import simplejson
import logging
import sys
import re
import os

import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.template

from corgi import Corgi


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


from logging import StreamHandler
from logging.handlers import WatchedFileHandler

log = logging.getLogger('server')


# Global configuration properties
config = None


class EventHandler(tornado.web.RequestHandler):

    def post(self):
        data = simplejson.loads(self.request.body)
        pr = data['pull_request']
        number = pr['number']
        title = pr['title']
        body = pr['body']
        sender = data['sender']['login']

        logging.info("Received event for PR %s" % number)

        cases = set(re.findall(r'\bgs-(\d+)', title + ' ' + body))

        if cases:
            logging.info("Case numbers %s" % ",".join(cases))
            c = Corgi(config['redmine.url'], config['redmine.auth_key'],
                      config.get('user.mapping.%s' % sender))
            if c.connected:
                for case in cases:
                    c.updateIssue(case, create_issue_update(data))
                    logging.info("Added comment to issue %s" % case)
            else:
                logging.error("Connection to Redmine failed")
        else:
            logging.info("No case numbers found")



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

    log.info('Starting corgi server http://%s:%d/' % (host, port))
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port, host)
    tornado.ioloop.IOLoop.instance().start()
