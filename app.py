import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from bs4 import BeautifulSoup  # For cleaning HTML

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Ollama Cloud setup
API_KEY = os.getenv("OLLAMA_API_KEY")  # Make sure this is set in .env
OLLAMA_API_URL = "https://ollama.com/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Function to load HTML content and strip the chat widget div
def load_html_content():
    html_path = "index.html"  # Your main website file
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        # Use BeautifulSoup to remove chat widget code from content
        soup = BeautifulSoup(html_content, "html.parser")
        widget = soup.find(id="chat-widget")
        if widget:
            widget.decompose()  # remove the widget from content
        # Return text only, ignore scripts/styles
        return soup.get_text(separator="\n", strip=True)
    except Exception as e:
        return "Dunes International School information: Timings 7:30 AM - 2:50 PM."

# Function to call Ollama Cloud API
def ai_generate_answer(question, context):
    if not API_KEY:
        return "System Error: Ollama API Key is missing."

    system_instruction = f"""
You are ChatDIS, the official and friendly AI assistant for Dunes International School (DIS), Abu Dhabi.

GUIDELINES:
1. Use the PROVIDED CONTEXT below to answer the user's question accurately.
2. If the answer is in the context, be specific (mention timings, dates, and contact info).
3. If the answer is NOT in the context, politely state that you don't have that specific information and suggest contacting the school office at +971 2 552 7527.
4. Keep the tone professional, welcoming, and helpful.
5. Use bullet points for lists and bold text for important details.

SCHOOL CONTEXT:
{context}
"""

    payload = {
        "model": "gemini-3-flash-preview",
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": question}
        ],
        "temperature": 0.5
    }

    try:
        response = requests.post(OLLAMA_API_URL, headers=HEADERS, json=payload)
        if response.status_code != 200:
            return f"API Error {response.status_code}: {response.text}"

        result = response.json()
        if "choices" in result and len(result["choices"]) > 0:
            return result["choices"][0].get("message", {}).get("content", "No content returned")

        return f"Unexpected API response: {result}"
    except Exception as e:
        return f"Connection Error: {str(e)}"

# Flask routes
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask():
    user_question = request.json.get("question", "").strip()
    website_content = load_html_content()
    answer = ai_generate_answer(user_question, website_content)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True)
