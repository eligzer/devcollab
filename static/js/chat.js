if (typeof io !== "undefined") {

    const chatBox = document.getElementById("chatBox")
    const input = document.getElementById("chatInput")
    const sendBtn = document.getElementById("chatSend")
    const typingIndicator = document.getElementById("typingIndicator")

    if (!chatBox || !input || !sendBtn) {
        console.log("Chat not active on this page")
    } else {

        const socket = io(location.origin)

        socket.on("connect", () => {
            console.log("Socket connected:", socket.id)
        })

        const username = window.chatUsername
        const userId = window.chatUserId
        const otherId = window.chatOtherId

        const room = "chat_" + [userId, otherId].sort().join("_")

        socket.emit("join_chat", { room: room })

        function sendMessage(){

            const message = input.value.trim()

            if(message === "") return

            socket.emit("send_message", {
                room: room,
                username: username,
                message: message
            })

            input.value = ""
        }

        sendBtn.onclick = sendMessage

        input.addEventListener("keypress", function(e){
            if(e.key === "Enter"){
                sendMessage()
            }
        })

        socket.on("receive_message", function(data){

            const msg = document.createElement("div")

            if(data.username === username){
                msg.className = "chat-message me"
            } else {
                msg.className = "chat-message them"
            }

            msg.innerHTML =
                '<div class="bubble">'+ data.message +'</div>'

            chatBox.appendChild(msg)

            chatBox.scrollTop = chatBox.scrollHeight
        })

        let typingTimeout

        input.addEventListener("input", function(){

            socket.emit("typing", {
                room: room,
                username: username
            })

            clearTimeout(typingTimeout)

            typingTimeout = setTimeout(function(){

                socket.emit("stop_typing", {
                    room: room
                })

            },1000)
        })

        socket.on("user_typing", function(data){
            typingIndicator.innerText = data.username + " is typing..."
        })

        socket.on("user_stop_typing", function(){
            typingIndicator.innerText = ""
        })

    }

}