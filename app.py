from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
import openai
import os
import random
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
print("GEMINI KEY:", os.getenv("GEMINI_API_KEY"))
print("OPENAI KEY:", os.getenv("OPENAI_API_KEY"))

# Access the API key from the environment variable
gemini_api_key = os.getenv("GEMINI_API_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

# Configure Gemini API
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    gemini_model = genai.GenerativeModel("gemini-1.5-pro")
else:
    print("Gemini API key is missing!")

# Configure OpenAI API
if openai_api_key:
    openai.api_key = openai_api_key
else:
    print("OpenAI API key is missing!")

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "your_secret_key")

# Handle browser favicon requests
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No Content

# Serve main HTML page
@app.route("/")
def index():
    return render_template("index.html")

@app.before_request
def init_conversation():
    if 'conversation_history' not in session:
        session['conversation_history'] = []

# Reset conversation in session
@app.route("/reset", methods=["POST"])
def reset():
    session['conversation_history'] = []
    return '', 204

# API endpoint for receiving a message
@app.route("/ask", methods=["POST"])
def ask():
    user_message = request.json.get("message")
    ai_choice = request.json.get("ai_choice", "gemini")

    if not user_message:
        return jsonify({"reply": "Please enter a message."})

    # Convert the user's message to lowercase for case-insensitive matching
    user_message_lower = user_message.lower()

    # Check if the message matches any of the predefined responses
    predefined_reply = predefined_responses.get(user_message_lower)

    if predefined_reply:
        # If the message matches a predefined response, return that
        return jsonify({"reply": predefined_reply})

    # Append user message to conversation
    session['conversation_history'].append({"role": "user", "content": user_message})

    personality_reply = random.choice([
        "Alright, here's a clear answer.",
        "Let me explain it simply.",
        "Here’s what you need to know:",
        "Of course, here’s the answer:"
    ])
    predefined_responses = {
    "hello": "Hi there! How can I help you today?",
    "how are you": "I'm just a bot, but I'm doing great! How about you?",
    "bye": "Goodbye! Take care!",
    "thanks": "You're welcome! Let me know if you need anything else.",
    "help": "Sure! How can I assist you with your health today?",
    "sickle cell": "Sickle cell disease is a genetic blood disorder. Would you like to know more about it?",
    "fever": "If you're experiencing a fever, it's important to monitor your temperature and consult a healthcare provider if it persists.",
    "headache": "A headache can be caused by many things. Drink plenty of water, and if it doesn't improve, consider consulting a doctor.",
}

    try:
        if ai_choice == "openai":
            # Use OpenAI Chat API with memory
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # or "gpt-4"
                messages=session['conversation_history'],
                max_tokens=200,
                temperature=0.7,
            )
            ai_reply = response.choices[0].message["content"]
            session['conversation_history'].append({"role": "assistant", "content": ai_reply})

        elif ai_choice == "gemini":
            # Simulate Gemini memory by stitching prompt
            chat_prompt = "\n".join(
                f"{'User' if m['role']=='user' else 'MediCare'}: {m['content']}"
                for m in session['conversation_history']
            )
            response = gemini_model.generate_content(chat_prompt)
            ai_reply = response.text.strip()
            session['conversation_history'].append({"role": "assistant", "content": ai_reply})

        else:
            ai_reply = "Invalid AI choice."

    except Exception as e:
        if "429" in str(e):
            ai_reply = "I'm currently handling too many requests. Please try again shortly."
        else:
            ai_reply = f"Sorry, I encountered an error: {str(e)}"

    # Combine personality-driven message with the real answer
    bot_reply = f"{personality_reply} {ai_reply}"

    # Return the final reply
    return jsonify({"reply": bot_reply})

@app.route("/check_symptoms", methods=["POST"])
def check_symptoms():
    symptoms = request.json.get("symptoms")
    if not symptoms:
        return jsonify({"diagnosis": "Please provide some symptoms to check."})

    # Dummy logic for symptom checking (replace with real logic or external API)
    diagnosis = "You might have a cold. Please consult a healthcare professional."
    
    return jsonify({"diagnosis": diagnosis})

if __name__ == "__main__":
    app.run(debug=True)
