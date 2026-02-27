const API_BASE = "http://127.0.0.1:8000";

async function sendMessage() {
    const inputField = document.getElementById("user-input");
    const chatBox = document.getElementById("chat-box");
    const text = inputField.value.trim();

    if (!text) return;

    appendMessage("You: " + text, "user");
    inputField.value = "";

    appendMessage("Jarvis is thinking...", "bot");

    try {
        const response = await fetch(`${API_BASE}/text`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ text: text })
        });

        chatBox.lastChild.remove(); // remove thinking message

        if (!response.ok) {
            const err = await response.json();
            appendMessage("Error: " + err.detail, "bot");
            return;
        }

        const data = await response.json();

        appendMessage("Jarvis: " + data.response, "bot");

    } catch (error) {
        chatBox.lastChild.remove();
        appendMessage("Connection error.", "bot");
    }
}

function appendMessage(message, className) {
    const chatBox = document.getElementById("chat-box");
    const div = document.createElement("div");
    div.className = "message " + className;
    div.textContent = message;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}