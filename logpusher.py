#!/usr/bin/env python
# Written by Michael Gugino
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Consuming text (logs) from stdin and sending zeromq messages
to feeder.py
"""

import zmq
import sys
import fcntl
import os
import select
fcntl.fcntl(sys.stdin, fcntl.F_SETFL, os.O_NONBLOCK)
def setupZeroMQ(context):
    socket = context.socket(zmq.PUSH)
    socket.bind ("tcp://127.0.0.1:5555")
    return socket
def readFromStdin(socket) :
    for line in sys.stdin:
      socket.send(line)
      print "sent", line
      #yield line
def main(**kwargs):
  context = zmq.Context()
  poller = select.epoll()
  poller.register(sys.stdin, select.EPOLLIN | select.EPOLLET)
  socket = setupZeroMQ(context)
  #linestosend = readFromStdin()
  while True:
   try:
    poll = poller.poll(timeout=-1)
    if poll and poll[0][1] != select.EPOLLHUP:
       readFromStdin(socket)
  #for line in linestosend:
  #    socket.send(str(os.getpid()) + line)
    else:
      break
   except:
    pass
  socket.send('loop died')
if __name__ == "__main__":
    main()
