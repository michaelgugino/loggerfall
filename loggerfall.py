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
"""Streaming data (logs) via websockets.

Authentication, error handling, etc are not implemented yet
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
        #need to remove get/post data from first get.
        hostchannel = str(self.get_argument("HOST", default='none', strip=False))
        appchannel = str(self.get_argument("APP", default='none', strip=False))
        cache = []

        #Need to update the index.html
        self.render("index.html", messages=cache)

class ChatSocketHandler(tornado.websocket.WebSocketHandler):

    channelcache = dict()
    channels = dict()
    cache_size = 200

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    #client opens a connection to receive messages.
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
          #add our channel set to channels dictionary
          ChatSocketHandler.channels[hostappchan] = set()
          #create local cache for channel messages
          ChatSocketHandler.channelcache[hostappchan] = list()
          #add our client to our channel set
          ChatSocketHandler.channels[hostappchan].add(self)
        #Send full 2k messages on connect
        self.send_cache_on_connect(hostappchan)

    def send_cache_on_connect(self,channel):
        print "send_cache_on_connect: ", channel
        try:
          count = 0;
          res = redcon.lrange(channel,-2000,-1)
          reslen = len(res)
          for msg in res:
            if count > reslen - self.cache_size:
                local_cache_update(channel, msg, 0)
            count = count + 1
            self.write_message(ast.literal_eval(msg))
        except:
          logging.error("Error sending message", exc_info=True)
          ChatSocketHandler.channels[channel].remove(self)

    #Client has disconnected
    def on_close(self):
        hostchannel = str(self.get_argument("HOST", default='none', strip=False))
        appchannel = str(self.get_argument("APP", default='none', strip=False))
        hostappchan = hostchannel + '::' + appchannel
        ChatSocketHandler.channels[hostappchan].remove(self)

    @classmethod
    def send_updates3(cls, channel, msg):
        for waiter in cls.channels[channel]:
            try:
                waiter.write_message(ast.literal_eval(msg))
            except:
              logging.error("Error sending message", exc_info=True)
              cls.channels[channel].remove(waiter)

    def on_message(self, message):
        pass



def local_cache_update(channel, msg, cache_len):
    if cache_len > 200:
        ChatSocketHandler.channelcache[channel].pop(0)
    ChatSocketHandler.channelcache[channel].append(msg)
    pass


def local_cache_check(channel, cache_set, msg):
    if msg in cache_set:
        return True
    else:
        print "not in cache: ", msg
        return False

def check_redis():
      if ChatSocketHandler.channels:
        removals = list()
        for channel in ChatSocketHandler.channels:
          #check for any active listeners on this channel
          if len(ChatSocketHandler.channels[channel]) == 0:
            removals.append(ChatSocketHandler.channels[channel])
          else:
            messages_to_send = list()
            for msg in redcon.lrange(channel,-200,-1):
                #check if message in local cache.
                #append to local cache.
                #clear old entries from local cache.
                cache_set = set(ChatSocketHandler.channelcache[channel])
                cache_len = len(cache_set)
                if not local_cache_check(channel, cache_set, msg):
                    cache_len = cache_len+1
                    local_cache_update(channel, msg, cache_len)
                    messages_to_send.append(msg)

            for msg in messages_to_send:
                ChatSocketHandler.send_updates3(channel, msg)

        for chan in removals:
          del ChatSocketHandler.channels[channel]
          del ChatSocketHandler.channelcache[channel]


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

    pcall = tornado.ioloop.PeriodicCallback(check_redis, 1000)
    pcall.start()
    goer.start()


if __name__ == "__main__":
    main()
