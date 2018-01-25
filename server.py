# -*- coding: utf-8 -*-

"""

Copyright (C) 2013 Glencoe Software, Inc.
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""

import simplejson
import logging
import re
import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.template

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.util.crumb_requester import CrumbRequester

import github

from corgi import Corgi
from config import config

from logging import StreamHandler
from logging.handlers import WatchedFileHandler

log = logging.getLogger('server')


HEADER = '### Referenced Issues:'


def create_tree_url(data, head_or_base='head'):
    ref = data['pull_request'][head_or_base]['ref']
    url = '%s/tree/%s' % (
        data['pull_request'][head_or_base]['repo']['html_url'],
        ref
    )
    return url


def create_issue_update(pullrequest, data):

    def make_past_tense(verb):
        if not verb.endswith('d'):
            return verb + 'd'
        return verb

    loader = tornado.template.Loader(
        os.path.join(os.path.dirname(__file__), 'templates')
    )
    template = loader.load('updated_pull_request.textile')
    return template.generate(
        data=data,
        head_url=create_tree_url(data, 'head'),
        base_url=create_tree_url(data, 'base'),
        make_past_tense=make_past_tense,
        commits=get_commits_from_pr(pullrequest),
    )


def update_redmine_issues(pullrequest, data):
    issues = get_issues_from_pr(pullrequest)
    if not issues:
        logging.info("No issues found")
    else:
        logging.info(
            "Updating Redmine issues %s" % ", ".join(map(str, issues))
        )

    if issues and not config.get('dry-run'):
        c = Corgi(
            config['redmine.url'], config['redmine.auth_key'],
            config.get('user.mapping.%s' % data['sender']['login'])
        )
        if not c.connected:
            logging.error("Connection to Redmine failed")
            return

    if data['action'] == 'closed' and data['pull_request']['merged']:
        data['action'] = 'merged'
    status = config.get('redmine.status.on-pr-%s' % data['action'])
    update_message = create_issue_update(pullrequest, data)
    logging.debug(update_message)

    if not config.get('dry-run'):
        for issue in issues:
            c.update_issue(issue, update_message, status)
            logging.info("Added comment to issue %s" % issue)


def run_jenkins_job(job):
    requester = CrumbRequester(config['jenkins.url'],
                               username=config['jenkins.username'],
                               password=config['jenkins.password'])
    jenkins = Jenkins(config['jenkins.url'],
                      username=config['jenkins.username'],
                      password=config['jenkins.password'],
                      requester=requester)
    if job in jenkins:
        logging.debug('Invoking Jenkins job %s' % job)
        if not config.get('dry-run'):
            jenkins[job].invoke()
    else:
        logging.error('Jenkins job %s not found' % job)
        logging.debug('Available Jenkins jobs: %s' % ', ' % jenkins.keys())


def get_pullrequest(repo_name, pr_number):
    gh = github.Github(config['git.token'])
    repo = gh.get_repo(repo_name)
    return repo.get_pull(pr_number)


def get_commits_from_pr(pullrequest):
    cached = getattr(pullrequest, '_cached_commits', None)
    if not cached:
        cached = pullrequest.get_commits()
        setattr(pullrequest, '_cached_commits', cached)
    return cached


def get_issues_from_pr(pullrequest):
    text = [pullrequest.title, pullrequest.body]
    for commit in get_commits_from_pr(pullrequest):
        text.append(commit.commit.message)
    return sorted(set(map(int, re.findall(r'\bgs-(\d+)', ' '.join(text)))))


def get_issue_titles(issues):
    corgi = Corgi(config['redmine.url'], config['redmine.auth_key'])
    titles = dict()
    if corgi.connected:
        for issue in issues:
            titles[issue] = corgi.get_issue_title(issue)
    return titles


def update_pr_description(pullrequest):
    log.info(
        'Updating PR description for %s PR %s' %
            (pullrequest.base.repo.full_name, pullrequest.number)
    )
    body = pullrequest.body
    issues = get_issues_from_pr(pullrequest)
    titles = get_issue_titles(issues)
    links = list()
    for issue in issues:
        link = '* [Issue %s: %s](%sissues/%s)' % (
            issue, titles[issue], config['redmine.url'], issue
        )
        links.append(link)
    links = '\n'.join(links)

    lines = [line.strip() for line in body.split('\n')]
    if HEADER in lines:
        log.info('Found existing list of issues, updating')
        # update existing list
        pos = lines.index(HEADER) + 1
        while pos < len(lines) and lines[pos].startswith('* '):
            del lines[pos]
        if links:
            lines.insert(pos, links)
        else:
            log.info('Removing existing list of issues')
            del lines[pos - 1]
    elif links:
        log.info('No existing list of issues found, creating')
        lines.append(HEADER)
        lines.append(links)

    updated_body = '\n'.join(lines)

    if updated_body != body:
        log.info('Committing new body')
        if not config.get('dry-run'):
            pullrequest.edit(body=updated_body)
    else:
        log.info('Body unchanged, skipping commit')

    return updated_body


class EventHandler(tornado.web.RequestHandler):

    def post(self):
        data = simplejson.loads(self.request.body)
        logging.info(
            "Received event for PR %s" % data['pull_request']['number']
        )

        try:
            pullrequest = get_pullrequest(
                data['repository']['full_name'],
                data['pull_request']['number']
            )

            # Update Redmine issues
            update_redmine_issues(pullrequest, data)

            # Update PR description
            update_pr_description(pullrequest)
        except:
            # Likely Github or Redmine connection problems, log and continue
            logging.exception("Exception updating cross-links")

        # Trigger jenkins jobs
        jobs = config.get(
            'repository.mapping.%s:%s' % (
                data['repository']['full_name'],
                data['pull_request']['base']['ref']
            )
        )

        if not jobs:
            jobs = config.get(
                'repository.mapping.%s' % data['repository']['full_name']
            )

        if jobs:
            if isinstance(jobs, list):
                for job in jobs:
                    run_jenkins_job(job)
            else:
                run_jenkins_job(jobs)
        else:
            logging.info("No Jenkins job mappings found")


def main():
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


if __name__ == "__main__":
    main()
