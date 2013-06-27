import tornado.ioloop
import tornado.web

import simplejson
import re


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class EventHandler(tornado.web.RequestHandler):
    def post(self):
        data = simplejson.loads(self.request.body)
        pr = data['pull_request']
        title = pr['title']
        body = pr['body']
        url = pr['url']
        
        print title
        print body
        
        cases = set(re.findall(r'\bgs-(\d+)', title))
        cases = cases.union(re.findall(r'\bgs-(\d+)', body))

        print cases
        

application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/event", EventHandler),
])

if __name__ == "__main__":
    application.listen(19090)
    tornado.ioloop.IOLoop.instance().start()
