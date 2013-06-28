import tornado.ioloop
import tornado.web
import tornado.template

import simplejson
import re
import logging
import sys
import os

from corgi import Corgi
from config import REDMINE_AUTH_KEY, REDMINE_URL, PORT


def create_issue_update(data):
    loader = tornado.template.Loader(os.path.join(os.path.dirname(__file__), 'templates'))
    template = loader.load('updated_pull_request.textile')
    return template.generate(data=data)


class EventHandler(tornado.web.RequestHandler):

    def post(self):
        data = simplejson.loads(self.request.body)
        pr = data['pull_request']
        number = pr['number']
        title = pr['title']
        body = pr['body']

        logging.info("Received event for PR %s" % number)

        cases = set(re.findall(r'\bgs-(\d+)', title + ' ' + body))

        if cases:
            logging.info("Case numbers %s" % ",".join(cases))
            c = Corgi(REDMINE_URL, REDMINE_AUTH_KEY)
            if c.connected:
                for case in cases:
                    #c.updateIssue(case, create_issue_update(data))
                    print create_issue_update(data)
                    logging.info("Added comment to issue %s" % case)
            else:
                logging.error("Connection to Redmine failed")
        else:
            logging.info("No case numbers found")



application = tornado.web.Application([
    (r"/event", EventHandler),
])

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    logging.info('Starting corgi server')
    application.listen(PORT)
    tornado.ioloop.IOLoop.instance().start()
