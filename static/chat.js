// Original work Copyright 2009 FriendFeed
// Licensed under the Apache License, Version 2.0 (the "License"); you may
// not use this file except in compliance with the License. You may obtain
// a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
// WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
// License for the specific language governing permissions and limitations
// under the License.



$(document).ready(function() {
    if (!window.console) window.console = {};
    if (!window.console.log) window.console.log = function() {};

    $('.dragThis')
    .resizable({
      stop: function(event, ui) {
        var w = $(this).width();
        var h = $(this).height();
        console.log('StopEvent fired')
        console.log('Width:'+w);
        console.log('Height:'+h)
      }
    })
    .draggable({
      containment: $('body'),
      drag: function(){
        var offset = $(this).offset();
        var xPos = offset.left;
        var yPos = offset.top;
        $('#posX').text('x: ' + xPos);
        $('#posY').text('y: ' + yPos);
      },
      stop: function(){
        var finalOffset = $(this).offset();
        var finalxPos = finalOffset.left;
        var finalyPos = finalOffset.top;
        $('#finalX').text('Final X: ' + finalxPos);
        $('#finalY').text('Final X: ' + finalyPos);
      }
    });

    var myInbox = new multiupdater(location.host,purl().attr('query'),'#inbox');
    var myInbox2 = new multiupdater(location.host,'HOST=mikehost&APP=testapp','#inbox2');

    myInbox.updater.start(myInbox);
    myInbox2.updater.start(myInbox2);
});

function newMessage(form) {
    var message = form.formToDict();
    updater.socket.send(JSON.stringify(message));
    form.find("input[type=text]").val("").select();
}

jQuery.fn.formToDict = function() {
    var fields = this.serializeArray();
    var json = {}
    for (var i = 0; i < fields.length; i++) {
        json[fields[i].name] = fields[i].value;
    }
    if (json.next) delete json.next;
    return json;
};

function multiupdater(host, query, divid) {
  this.host = host;
  this.query = query;
  this.divid = divid;

  this.updater = {

    socket: null,
    divid: null,
    host: null,
    query: null,
    start: function(myobj) {
        var url = "ws://" + myobj.host + "/chatsocket?" + myobj.query;
        myobj.updater.socket = new WebSocket(url);
        myobj.updater.socket.onmessage = function(event) {
            myobj.updater.showMessage(myobj.divid, JSON.parse(event.data));
        }
    },
       showMessage: function(divid, message) {
        //var existing = $("#m" + message.id);
        //if (existing.length > 0) return;
        var node = $(message.html);
        node.hide();
        $(divid).append(node);
        node.slideDown();
        $(divid).animate({ scrollTop: $(divid)[0].scrollHeight}, 500);
    }

    };
};
