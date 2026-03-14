const socket = io();

const chatBox = document.getElementById("chatBox");
const chatInput = document.getElementById("chatInput");
const sendBtn = document.getElementById("chatSend");

const username = window.chatUsername;
const room = window.chatRoom;

/* join room */

socket.emit("join_room", {
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