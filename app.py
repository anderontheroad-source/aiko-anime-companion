import os
import json
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Aiko - Anime Companion</title>
<style>
body {
    background: #21152f;
    color: white;
    font-family: Arial, sans-serif;
    text-align: center;
    padding: 20px;
}
h1 { color: #ff9bd2; }
.avatar { font-size: 90px; }
#chat {
    background: #392447;
    padding: 15px;
    border-radius: 15px;
    min-height: 200px;
    text-align: left;
    overflow-wrap: anywhere;
}
input {
    padding: 12px;
    width: 60%;
    border-radius: 10px;
    border: none;
}
button {
    padding: 12px;
    background: #ff9bd2;
    border: 0;
    border-radius: 10px;
}
p { white-space: pre-wrap; }
</style>
</head>
<body>
<div class="avatar">🌸🎀</div>
<h1>My Anime Companion</h1>
<div id="chat">
<p style="color:#ff9bd2">Aiko: Hiii! 💗 Main Aiko hoon!</p>
</div>
<br>
<form id="form">
<input id="msg" placeholder="Message likho..." required>
<button id="send">Send</button>
</form>
<script>
const form = document.getElementById('form');
const input = document.getElementById('msg');
const chat = document.getElementById('chat');
const send = document.getElementById('send');

function addMessage(name, text, color) {
    const p = document.createElement('p');
    p.style.color = color;
    p.textContent = name + ': ' + text;
    chat.appendChild(p);
}

form.addEventListener('submit', async function(e) {
    e.preventDefault();
    const message = input.value.trim();
    if (!message) return;

    addMessage('You', message, 'white');
    input.value = '';
    send.disabled = true;
    send.textContent = 'Thinking...';

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({message: message})
        });
        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }

        addMessage('Aiko 💗', data.reply, '#ff9bd2');
const audioResponse = await fetch('/tts', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({text: data.reply})
});

if (audioResponse.ok) {
    const audioBlob = await audioResponse.blob();
    const audioUrl = URL.createObjectURL(audioBlob);
    const audio = new Audio(audioUrl);
    audio.onended = () => URL.revokeObjectURL(audioUrl);
    audio.play();
}   
 } catch (err) {
        addMessage('Aiko', 'Error: ' + err.message, '#ffaaaa');
    } finally {
        send.disabled = false;
        send.textContent = 'Send';
    }
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Message khaali hai"}), 400

    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return jsonify({"error": "Groq API key set nahi hai"}), 500

    url = "https://api.groq.com/openai/v1/chat/completions"

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Your name is Aiko. You are a friendly anime companion. "
                    "Reply naturally in casual Hinglish using Roman letters only. "
                    "Never use Devanagari. Keep replies warm and concise."
                )
            },
            {"role": "user", "content": message}
        ],
        "temperature": 0.7
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "User-Agent": "AikoAnimeCompanion/1.0"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))

        reply = result["choices"][0]["message"]["content"]
        return jsonify({"reply": reply})

    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        print("Groq error:", error.code, details)
        return jsonify({"error": "Groq API error " + str(error.code)}), 502

    except Exception as error:
        print("Connection error:", repr(error))
        return jsonify({"error": "AI connection nahi ho paya. Dobara try karo."}), 502

@app.route("/tts", methods=["POST"])
def tts():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()

        if not text:
            return jsonify({"error": "Text missing"}), 400

        api_key = os.getenv("SARVAM_API_KEY")
        if not api_key:
            return jsonify({"error": "Sarvam API key missing"}), 500

        payload = {
            "text": text,
            "target_language_code": "hi-IN",
            "speaker": "aparna_hi_kyc",
            "model": "bulbul:v4-flash",
            "speech_sample_rate": 24000,
            "output_audio_codec": "mp3"
        }

        req = urllib.request.Request(
            "https://api.sarvam.ai/text-to-speech/stream",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "api-subscription-key": api_key,
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(req, timeout=60) as response:
            audio = response.read()

        from flask import Response
        return Response(audio, mimetype="audio/mpeg")

    except Exception as error:
        print("Sarvam TTS error:", repr(error))
        return jsonify({"error": "Voice generate nahi hui"}), 502
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
