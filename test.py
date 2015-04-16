#!/usr/bin/env python
# coding=utf-8
"""
streaming upload plugin for tornado. 
can upload the file from "multipart/form-data", 
save it into file system or mongodb, and set the metadata into request arguments.
"""
import tornado.ioloop
import tornado.web
from upload_mixin import FileUploadHandlerMixin, MongoUploadHandlerMixin
from pymongo import MongoClient
import gridfs

@tornado.web.stream_request_body
class FileHandler(FileUploadHandlerMixin, tornado.web.RequestHandler):

    def initialize(self, uploadpath='./'):
        self.uploadpath = uploadpath

    def post(self):
        print self.request.headers
        print self.request.arguments

@tornado.web.stream_request_body
class MongoHandler(MongoUploadHandlerMixin, tornado.web.RequestHandler):

    def initialize(self, filefs=None):
        self.filefs = filefs

    def post(self):
        print self.request.headers
        print self.request.arguments

client = MongoClient()
db = client['test']
filefs = gridfs.GridFS(db)

application = tornado.web.Application([
    (r"/", FileHandler, dict(uploadpath='/tmp/')),
    (r"/mongo", MongoHandler, dict(filefs=filefs)),
])
 
if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()


