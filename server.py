import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class EventHandler(tornado.web.RequestHandler):
    def post(self):
        print self.request.body


application = tornado.web.Application([
    (r"/", MainHandler),
    (r"/event", EventHandler),
])

if __name__ == "__main__":
    application.listen(19090)
    tornado.ioloop.IOLoop.instance().start()
