#!/usr/bin/env python
#
# Copyright 2009 Facebook
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

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)


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
        if (hostchannel == 'none' or appchannel == 'none'):
          return none
        self.subscribe = hostchannel+'::'+appchannel
        if str(hostchannel+'::'+appchannel) in ChatSocketHandler.channels:
          ChatSocketHandler.channels[hostchannel+'::'+appchannel].add(self)
        else:
          ChatSocketHandler.channels[hostchannel+'::'+appchannel] = set()
          ChatSocketHandler.channels[hostchannel+'::'+appchannel].add(self)
        #ChatSocketHandler.waiters.add(self)
    def on_close(self):
        #ChatSocketHandler.waiters.remove(self)
        ChatSocketHandler.channels[hostchannel+'::'+appchannel].remove(self)

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
                  waiter.write_message(chat)
              except:
                  logging.error("Error sending message", exc_info=True)
                  cls.channels[channel].remove(waiter)

    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        chat = {
            "id": str(uuid.uuid4()),
            "body": parsed["body"],
            }
        chat["html"] = tornado.escape.to_basestring(
            self.render_string("message.html", message=chat))

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)
def t1():
  print 't1'

def main_on_message(app,message):
        parsed = tornado.escape.json_decode(message)
        chat = {
            "id": str(uuid.uuid4()),
            "body": parsed["body"],
            }
        #chat["html"] = """<div class="message" id="0">%s</div>""" % parsed['body']
        
        if ChatSocketHandler.channels:
          for channel in ChatSocketHandler.channels:
            #this is where we'll pull data from redis
            print "channel: ",channel
            chat["html"] = """<div class="message" id="0">%s : %s</div>""" % (channel, parsed['body'])
            ChatSocketHandler.update_cache(channel,chat)

            ChatSocketHandler.send_updates(channel,chat)
def main():

    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    #tornado.ioloop.IOLoop.spawn_callback(t1)
    goer = tornado.ioloop.IOLoop.instance() 
    #tornado.ioloop.IOLoop.spawn_callback(t1)
    def t2():
      #print app.handlers[0][1][4].handler_class.cache
      #print ChatSocketHandler.cache
      main_on_message(app,u'{"body":"test","_xsrf":"2|7f1e46b3|f4ea7f3d2aeef31b4aabb4af00886db3|1426865952"}')
    pcall = tornado.ioloop.PeriodicCallback(t2, 2000)
    pcall.start()
    goer.start()


if __name__ == "__main__":
    main()
