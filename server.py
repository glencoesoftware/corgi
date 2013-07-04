import simplejson
import logging
import sys
import re
import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.template

from jenkinsapi.jenkins import Jenkins

from corgi import Corgi
from corgit import update_pr_description, get_issues_from_pr, get_pullrequest
from config import config

from logging import StreamHandler
from logging.handlers import WatchedFileHandler

log = logging.getLogger('server')


def create_tree_url(data):
    ref = data['pull_request']['head']['ref']
    url = data['pull_request']['head']['repo']['html_url'] + "/tree/" + ref
    return url


def create_issue_update(data):

    def make_past_tense(verb):
        if not verb.endswith('d'):
            return verb + 'd'
        return verb

    loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), 'templates'))
    template = loader.load('updated_pull_request.textile')
    return template.generate(
        data=data,
        tree_url=create_tree_url(data),
        make_past_tense=make_past_tense,
    )


def update_redmine_issues(pullrequest, data):
    issues = get_issues_from_pr(pullrequest)
    if not issues:
        logging.info("No issues found")
        return

    logging.info("Updating Redmine issues %s" % ", ".join(map(str, issues)))
    c = Corgi(config['redmine.url'], config['redmine.auth_key'],
              config.get('user.mapping.%s' % data['sender']['login']))
    if c.connected:
        for issue in issues:
            if not config.get('dry-run'):
                status = config.get('redmine.status.on-pr-%s' % data['action'])
                c.updateIssue(issue, create_issue_update(data), status)
            logging.info("Added comment to issue %s" % issue)
    else:
        logging.error("Connection to Redmine failed")


def run_jenkins_job(job):
    jenkins = Jenkins(config['jenkins.url'],
                      username=config['jenkins.username'],
                      password=config['jenkins.password'])
    if job in jenkins:
        logging.debug('Invoking Jenkins job %s' % job)
        if not config.get('dry-run'):
            jenkins[job].invoke()
    else:
        logging.error('Jenkins job %s not found' % job)
        logging.debug('Available Jenkins jobs: %s' % ', ' % jenkins.keys())


class EventHandler(tornado.web.RequestHandler):

    def post(self):
        data = simplejson.loads(self.request.body)
        logging.info("Received event for PR %s" % data['pull_request']['number'])
        pullrequest = get_pullrequest(data['repository']['full_name'],
                          data['pull_request']['number'])

        # Update Redmine issues
        update_redmine_issues(pullrequest, data)

        # Update PR description
        update_pr_description(pullrequest)

        # Trigger jenkins jobs
        jobs = config.get('repository.mapping.%s' %
                data['repository']['full_name'].replace('/', '.')
        )
        if jobs:
            if isinstance(jobs, list):
                for job in jobs:
                    run_jenkins_job(job)
            else:
                run_jenkins_job(jobs)
        else:
            logging.info("No Jenkins job mappings found")


if __name__ == "__main__":
    # Set up our log level
    try:
        filename = config['server.logging_filename']
        handler = WatchedFileHandler(filename)
    except KeyError:
        handler = StreamHandler()
    handler.setFormatter(logging.Formatter(config['server.logging_format']))
    root_logger = logging.getLogger('')
    root_logger.setLevel(int(config['server.logging_level']))
    root_logger.addHandler(handler)

    settings = {
    }

    if 'debug' in config:
        log.info('Enabling Tornado Web debug mode')
        settings['debug'] = config['debug']

    host = config['server.socket_host']
    port = int(config['server.socket_port'])

    application = tornado.web.Application([
        (r"/event", EventHandler),
    ], **settings)

    if config.get('dry-run'):
        log.info('In dry-run mode')

    log.info('Starting corgi server http://%s:%d/' % (host, port))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port, host)
    tornado.ioloop.IOLoop.instance().start()
