#!/usr/bin/python

"""Receiving json-like data via 0mq, and putting it in redis
"""

import zmq
import sys
import ast
import redis

def msgToDict(msg):
  try:
     dmsg = ast.literal_eval(msg)
     return dmsg
  except:
     print "bad json, ignoring message", msg
     return False

def main():
    pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
    redcon = redis.Redis(connection_pool=pool)
    pipe = redcon.pipeline()
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    socket.connect("tcp://0.0.0.0:5555")
    while True:
      message = socket.recv()
      dmsg = msgToDict(message)

      if dmsg:
          host =  dmsg['host']
          app = dmsg['tag'][:-1]
          pipe.sadd('hosts',host)
          pipe.sadd('apps',app)
          pipe.sadd('apps::' + host, app)
          pipe.sadd('hosts::' + app, host)
          pipe.rpush(host + "::" + app, dmsg['message'])
          response = pipe.execute()

if __name__ == "__main__":
    main()
