import tornado.ioloop
import tornado.web

import simplejson
import re
import logging
import sys

from corgi import Corgi
from config import REDMINE_AUTH_KEY, REDMINE_URL


class EventHandler(tornado.web.RequestHandler):

    def post(self):
        data = simplejson.loads(self.request.body)
        pr = data['pull_request']
        number = pr['number']
        title = pr['title']
        body = pr['body']
        url = pr['url']
        sender = data['sender']['login']

        logging.info("Received event for PR %s" % number)

        cases = set(re.findall(r'\bgs-(\d+)', title + ' ' + body))

        if cases:
            logging.info("Case numbers %s" % ",".join(cases))
            c = Corgi(REDMINE_URL, REDMINE_AUTH_KEY)
            if c.connected:
                for case in cases:
                    c.updateIssue(case, "PR %s was updated by %s" % (number, sender))
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
    application.listen(19090)
    tornado.ioloop.IOLoop.instance().start()
