const socket = io();

const chatBox = document.getElementById("chatBox");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("chatSend");

const username = window.chatUsername;
const room = window.chatRoom;

/* stop if not chat page */

if(!chatBox) return;


/* join chat room */

socket.emit("join_chat", {
    room: room
});


/* send message */

function sendMessage(){

    const message = chatInput.value.trim();

    if(message === "") return;

    socket.emit("send_message",{
        room: room,
        username: username,
        message: message
    });

    chatInput.value = "";

    socket.emit("stop_typing",{
        room: room
    });
}


/* send button */

if(sendBtn){
sendBtn.addEventListener("click", sendMessage);
}


/* enter key */

if(chatInput){
chatInput.addEventListener("keypress", function(e){

    if(e.key === "Enter"){
        sendMessage();
    }

});
}


/* typing indicator */

let typingTimeout;

if(chatInput){

chatInput.addEventListener("input", function(){

    socket.emit("typing",{
        room: room,
        username: username
    });

    clearTimeout(typingTimeout);

    typingTimeout = setTimeout(function(){

        socket.emit("stop_typing",{
            room: room
        });

    },1000);

});
}


/* receive message */

socket.on("receive_message", function(data){

    const messageElement = document.createElement("div");

    messageElement.classList.add("chat-message");

    messageElement.innerHTML = `
        <strong>${data.username}</strong>: ${data.message}
    `;

    chatBox.appendChild(messageElement);

    chatBox.scrollTop = chatBox.scrollHeight;

});


/* typing indicator display */

socket.on("user_typing", function(data){

    const indicator = document.getElementById("typingIndicator");

    if(indicator){
        indicator.innerText = data.username + " is typing...";
    }

});


socket.on("user_stop_typing", function(){

    const indicator = document.getElementById("typingIndicator");

    if(indicator){
        indicator.innerText = "";
    }

});