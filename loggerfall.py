#!/usr/bin/env python
# Modified work by Michael Gugino
# Original work Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
"""Simplified chat demo for websockets.

Authentication, error handling, etc are left as an exercise for the reader :)
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import os.path
import uuid
from tornado.httpserver import HTTPServer
from tornado.options import define, options
import redis
import ast


#define("port", default=8888, help="run on the given port", type=int)
pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
redcon = redis.Redis(connection_pool=pool)

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", MainHandler),
            (r"/chatsocket", ChatSocketHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        hostchannel = str(self.get_argument("HOST", default='none', strip=False))
        appchannel = str(self.get_argument("APP", default='none', strip=False))
        cache = str(hostchannel + '::' + appchannel)
        if cache in ChatSocketHandler.channelcache:
           cache = ChatSocketHandler.channelcache[cache]
        else:
           cache = []
        
        self.render("index.html", messages=cache)

class ChatSocketHandler(tornado.websocket.WebSocketHandler):
#    waiters = set()
#    cache = []
    channelcache = dict()
    channels = dict()
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    def open(self):
        hostchannel = str(self.get_argument("HOST", default='none', strip=False))
        appchannel = str(self.get_argument("APP", default='none', strip=False))
        hostappchan = hostchannel + '::' + appchannel
        if (hostchannel == 'none' or appchannel == 'none'):
          return none
        self.subscribe = hostappchan
        if str(hostappchan) in ChatSocketHandler.channels:
          ChatSocketHandler.channels[hostappchan].add(self)
        else:
          ChatSocketHandler.channels[hostappchan] = set()
          ChatSocketHandler.channels[hostappchan].add(self)
    def on_close(self):
        hostchannel = str(self.get_argument("HOST", default='none', strip=False))
        appchannel = str(self.get_argument("APP", default='none', strip=False))
        hostappchan = hostchannel + '::' + appchannel
        ChatSocketHandler.channels[hostappchan].remove(self)
 
    @classmethod
    def update_cache(cls,channel,chat):
        #cls.cache.append(chat)
        if channel in cls.channelcache:
          cls.channelcache[channel].append(chat)
        else:
          cls.channelcache[channel] = []
          cls.channelcache[channel].append(chat)
        if len(cls.channelcache) > cls.cache_size:
            cls.channelcache = cls.channelcache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, channel, chat):
            logging.info("sending message to %d waiters", len(cls.channels[channel]))
            for waiter in cls.channels[channel]:
              print "waiters", waiter
              #logging.info("sending message to %d waiters", len())
              try:
                  print "send_updates: ", type(chat)
                  waiter.write_message(chat)
              except:
                  logging.error("Error sending message", exc_info=True)
                  cls.channels[channel].remove(waiter)
    @classmethod
    def send_updates2(cls, channel, chat):
      logging.info("sending message to %d waiters", len(cls.channels[channel]))
      for waiter in cls.channels[channel]:
        print channel
        print "chat: ", chat
        print "waiters", waiter
        try:
          for msg in redcon.lrange(channel,-200,-1):
            #print "msg: ", type(msg)
            waiter.write_message(ast.literal_eval(msg))
          #waiter.write_message(chat)
        except:
          logging.error("Error sending message", exc_info=True)
          cls.channels[channel].remove(waiter)

    def on_message(self, message):
        pass


def push_to_redis(app,message):
  parsed = tornado.escape.json_decode(message)
  chat = {
    "id": str(uuid.uuid4()),
    "body": parsed["body"],
    }
  
  if ChatSocketHandler.channels:
    removals = list()
    for channel in ChatSocketHandler.channels:
      if len(ChatSocketHandler.channels[channel]) == 0:
        removals.append(ChatSocketHandler.channels[channel])
      else:
        chat["id"] = str(uuid.uuid4())
        chat["html"] = """<div class="message" id="#m%s">%s : %s</div>""" % (chat['id'], channel, str(parsed['body'] + chat["id"]))
        print "push_to_redis", chat
        redcon.rpush(channel,chat)
        ChatSocketHandler.send_updates2(channel,chat)
    for chan in removals:
      del ChatSocketHandler.channels[channel]

def main_on_message(app,message):
        parsed = tornado.escape.json_decode(message)
        chat = {
            "id": str(uuid.uuid4()),
            "body": parsed["body"],
            }
        #chat["html"] = """<div class="message" id="0">%s</div>""" % parsed['body']
        
        if ChatSocketHandler.channels:
          for channel in ChatSocketHandler.channels:
            #check if there are no subscribers
            if len(ChatSocketHandler.channels[channel]) == 0:
              #no subscribers = remove channel
              del ChatSocketHandler.channels[channel]
            else:
              #this is where we'll pull data from redis
              print "channel: ",channel
              chat["html"] = """<div class="message" id="0">%s : %s</div>""" % (channel, parsed['body'])
              print "main_on_message: ", chat
              ChatSocketHandler.update_cache(channel,chat)
              #should change this method to only send new info
              ChatSocketHandler.send_updates(channel,chat)
def main(**kwargs):
    import socket
    define("port", default=0, help="run on the given port", type=int)
    define("path", default="/tmp/test", help="run on the given port", type=str)
    define("fd", default=8888, help="run on the given port", type=int)
    tornado.options.parse_command_line()
    app = Application()
    if options.port > 0:
      app.listen(options.port)
    else:
      sock = socket.fromfd(options.fd, socket.AF_INET, socket.SOCK_STREAM)
      server = HTTPServer(app, **kwargs)
      server.add_socket(sock)

    goer = tornado.ioloop.IOLoop.instance() 
    def t2():
      #print app.handlers[0][1][4].handler_class.cache
      #print ChatSocketHandler.cache
      main_on_message(app,u'{"body":"test","_xsrf":"2|7f1e46b3|f4ea7f3d2aeef31b4aabb4af00886db3|1426865952"}')
    def t3():
      push_to_redis(app,u'{"body":"test","_xsrf":"2|7f1e46b3|f4ea7f3d2aeef31b4aabb4af00886db3|1426865952"}')
    pcall = tornado.ioloop.PeriodicCallback(t3, 2000)
    pcall.start()
    goer.start()


if __name__ == "__main__":
    main()
