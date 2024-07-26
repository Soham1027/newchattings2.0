from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

app = FastAPI()

html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Chat</title>
</head>
<body>
    <div id="usernameSection">
        <h1>WebSocket Chat</h1>
        <hr>
        <form onsubmit="submitUsername(event)">
            <label for="username"><b>Username:</b></label>
            <input type="text" id="usernameInput" autocomplete="off" required/>
            <br><br>
            <button type="submit">Submit</button>
        </form>
    </div>
    
    <div id="messagesSection" style="display: none;">
        <h1>WebSocket Chat</h1>
        <hr>
        <p><b>Username:</b> <span id="displayUsername"></span></p>
        <hr>
        <form action="" onsubmit="sendMessage(event)">
            <label><b>Messages:</b></label>
            <input type="text" id="messageText" autocomplete="off"/>
            <br><br>
            <label for="file"><b>Upload file:</b></label>
            <input type="file" id="file" enctype="multipart/form-data" autocomplete="off"/>
            <br><br>
            <button type="submit">Send</button>
        </form>
        <hr>
        <ul id='messages'></ul>
    </div>

    <script>
        var username = '';
        var ws;

        function submitUsername(event) {
            event.preventDefault();
            username = document.getElementById("usernameInput").value;
           
            ws = new WebSocket(`ws://192.168.29.158:8000/ws/${username}`);
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('li');
                
                if (event.data.startsWith("file:")) {
                    var parts = event.data.split(":");
                    var fileType = parts[1];
                    var fileContent = parts.slice(2).join(":");

                    if (fileType.startsWith("image")) {
                        var img = document.createElement("img");
                        img.src = fileContent;
                        // Set maximum width for images
                        img.style.maxWidth = "200px"; // Adjust as needed
                        message.appendChild(img);
                    } else if (fileType.startsWith("video")) {
                        var video = document.createElement("video");
                        video.src = fileContent;
                        video.controls = true;
                        // Set maximum width for videos
                        video.style.maxWidth = "200px"; // Adjust as needed
                        message.appendChild(video);
                    } else if (fileType.startsWith("audio")) {
                        var audio = document.createElement("audio");
                        audio.src = fileContent;
                        audio.controls = true;
                        message.appendChild(audio);
                    }
                } else {
                    var content = document.createTextNode(event.data);
                    message.appendChild(content);
                }
                
                messages.appendChild(message);
            };
            document.getElementById("displayUsername").innerText = username;
            document.getElementById("usernameSection").style.display = "none";
            document.getElementById("messagesSection").style.display = "block";
        }

        function sendMessage(event) {
            event.preventDefault();
            var input = document.getElementById("messageText");
            var file = document.getElementById("file").files[0];
            
            if (input.value) {
                ws.send(`${username}: ${input.value}`);
                input.value = '';
            }

            if (file) {
                var reader = new FileReader();
                reader.onload = function() {
                    var fileContent = reader.result;
                    ws.send(`file:${file.type}:${fileContent}`);
                };
                reader.readAsDataURL(file);
            }
        }
    </script>
</body>
</html>
"""

class ConnectionManager:
    def __init__(self):
        self.active_connections = []

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections.append((websocket, username))

    def disconnect(self, websocket: WebSocket):
        for conn, user in self.active_connections:
            if conn == websocket:
                self.active_connections.remove((conn, user))
                break

    async def broadcast(self, message: str):
        for conn, _ in self.active_connections:
            await conn.send_text(message)

manager = ConnectionManager()

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {username} left the chat")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app)