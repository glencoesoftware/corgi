# -*- coding: utf-8 -*-

"""

Copyright (c) 2013, Glencoe Software, Inc.
See LICENSE for details.

"""

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

from logging import StreamHandler
from logging.handlers import WatchedFileHandler

log = logging.getLogger('server')


# Global configuration properties
config = None


def create_tree_url(data):
    ref = data['pull_request']['head']['ref']
    url = data['pull_request']['head']['repo']['html_url'] + "/tree/" + ref
    return url


def create_issue_update(data):
    loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), 'templates'))
    template = loader.load('updated_pull_request.textile')
    return template.generate(
        data=data,
        tree_url=create_tree_url(data),
    )


def update_redmine_issues(issues, data):
    logging.info("Updating Redmine issues %s" % ", ".join(issues))
    c = Corgi(config['redmine.url'], config['redmine.auth_key'],
              config.get('user.mapping.%s' % data['sender']['login']))
    if c.connected:
        for issue in issues:
            if not config.get('dry-run'):
                c.updateIssue(issue, create_issue_update(data))
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
        pr = data['pull_request']
        number = pr['number']
        title = pr['title']
        body = pr['body']

        logging.info("Received event for PR %s" % number)

        # Update Redmine issues
        issues = set(re.findall(r'\bgs-(\d+)', title + ' ' + body))
        if issues:
            update_redmine_issues(issues, data)
        else:
            logging.info("No issue numbers found")

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
    # Load configuration
    from configobj import ConfigObj
    config = os.path.join(os.path.dirname(__file__), 'server.cfg')
    config = ConfigObj(config, interpolation=False, file_error=True)
    settings = {
    }

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
