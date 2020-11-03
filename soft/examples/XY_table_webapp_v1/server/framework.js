var ws;
var ws_error;
var working;
var log;


//----------------------------------------
function fwk_show_section(btn) {       
  all_btn = document.querySelectorAll("main nav button");
  all_sect = document.querySelectorAll("main section");
  for (i=0; i<all_btn.length;i ++) {
    if (all_btn[i]===btn) {
      all_btn[i].className="sel";
      all_sect[i].className="sel";
      try { all_sect[i].onshow(); } catch(e){}
    } else {
      all_btn[i].className="";
      if (all_sect[i].className=="sel") try { all_sect[i].onblur(); } catch(e){}
      all_sect[i].className="";
    }
  }
}
      
//----------------------------------------
function fwk_init() {
  t0 = (new Date()).getTime();

//  var all_btn = document.querySelectorAll("button");
//  for (i=0; i<all_btn.length;i ++){
//    all_btn[i].style.backgroundImage="url(img/" + all_btn[i].id + ".svg)";
//    all_btn[i].onmousedown = function (event)
//      { data = {"evt":"mousedown","id":event.target.id};
//        ws.send(JSON.stringify(data));
//      };
//    all_btn[i].onclick = function (event)
//      { data = {"evt":"click","id":event.target.id};
//        ws.send(JSON.stringify(data));
//      };
//    };
    
  var all_nav_btn = document.querySelectorAll("main nav button");
  for (i=0; i<all_nav_btn.length;i ++){
    all_nav_btn[i].onclick = function (event)
      { fwk_show_section(event.target);
      };
    }
    
  fwk_show_section(all_nav_btn[0]);
  
  log = document.getElementById('log');
  
  // Install WebSocket
  ws = new WebSocket("ws://" + location.host + "/ws");
  ws_error = false;
  
  // Execute when socket opened
  ws.onopen = function () {
    ws.send(JSON.stringify({"cmd":"new_connection()"})); // Send the message to the server
  };

  // Execute received messages from the server
  ws.onmessage = function (e) {
    if (!working){
      working=true;
      in_msg = JSON.parse(e.data);
      // DEBUG log.textContent = 'Server: ' + e.data; // in_msg["log"] ;
      
      if (in_msg["msg_type"] > "") {
          disp_async_msg(in_msg);
        }
      else if (in_msg["cmd"]=="report") {
        eval(in_msg["report_action"]);
      }
      else {
          // Do nothing !
        }
      working=false;
      }
  };

  // Execute when error on socket
  ws.onerror = function (error) {
    ws_error = true;
    log.textContent = 'WebSocket Error ' + error;
  };
};
      
//----------------------------------------
function fwk_read_file(file, cb) {
  var xhttp, file_text;
  if (file) {
    xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
      if (this.readyState == 4) {
        if (this.status == 0) {file_text = this.statusText;}
        if (this.status == 200) {file_text = this.responseText;}
        if (this.status == 404) {file_text = "File not found.";}
        if (cb) cb(file_text);
      }
    }      
    xhttp.open("GET", file, true);
    xhttp.send();
    return;
  }
};
