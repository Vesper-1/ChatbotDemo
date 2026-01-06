"""
Flask Chat App Demo
A simple chat application with multiple AI model support.
No JavaScript, No Database - uses in-memory storage and sessions.
"""

import os
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# In-memory user storage (demo purposes only - not for production!)
users = {}

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')


# ============== Helper Functions ==============

def get_ai_response(message: str, model: str, chat_history: list) -> str:
    """
    Get response from the selected AI model.
    Supports: deepseek, gemini, gpt4
    """
    try:
        if model == 'gpt4':
            return call_openai_api(message, chat_history)
        elif model == 'gemini':
            return call_gemini_api(message, chat_history)
        elif model == 'deepseek':
            return call_deepseek_api(message, chat_history)
        else:
            return "Unknown model selected."
    except Exception as e:
        return f"Error: {str(e)}"


def call_openai_api(message: str, chat_history: list) -> str:
    """Call OpenAI GPT-4 API"""
    if not OPENAI_API_KEY or OPENAI_API_KEY == 'your-openai-api-key-here':
        return "[Demo Mode] GPT-4 API key not configured. This is a placeholder response."

    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}',
        'Content-Type': 'application/json'
    }

    # Build messages for context
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for msg in chat_history[-10:]:  # Last 10 messages for context
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })
    messages.append({"role": "user", "content": message})

    data = {
        "model": "gpt-4",
        "messages": messages,
        "max_tokens": 1000
    }

    response = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


def call_gemini_api(message: str, chat_history: list) -> str:
    """Call Google Gemini API"""
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'your-google-api-key-here':
        return "[Demo Mode] Gemini API key not configured. This is a placeholder response."

    url = f'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GOOGLE_API_KEY}'

    # Build conversation context
    context = "Previous conversation:\n"
    for msg in chat_history[-10:]:
        role = "User" if msg['role'] == 'user' else "Assistant"
        context += f"{role}: {msg['content']}\n"
    context += f"\nUser: {message}\n\nAssistant:"

    data = {
        "contents": [{
            "parts": [{"text": context}]
        }]
    }

    response = requests.post(url, json=data, timeout=30)
    response.raise_for_status()
    result = response.json()

    if 'candidates' in result and len(result['candidates']) > 0:
        return result['candidates'][0]['content']['parts'][0]['text']
    return "No response from Gemini."


def call_deepseek_api(message: str, chat_history: list) -> str:
    """Call DeepSeek API"""
    if not DEEPSEEK_API_KEY or DEEPSEEK_API_KEY == 'your-deepseek-api-key-here':
        return "[Demo Mode] DeepSeek API key not configured. This is a placeholder response."

    headers = {
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
        'Content-Type': 'application/json'
    }

    # Build messages for context
    messages = [{"role": "system", "content": "You are a helpful assistant."}]
    for msg in chat_history[-10:]:
        messages.append({
            "role": msg['role'],
            "content": msg['content']
        })
    messages.append({"role": "user", "content": message})

    data = {
        "model": "deepseek-chat",
        "messages": messages,
        "max_tokens": 1000
    }

    response = requests.post(
        'https://api.deepseek.com/chat/completions',
        headers=headers,
        json=data,
        timeout=30
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']


# ============== Routes ==============

@app.route('/')
def index():
    """Redirect to chat if logged in, otherwise to login"""
    if 'username' in session:
        return redirect(url_for('chat'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handle login and registration"""
    if 'username' in session:
        return redirect(url_for('chat'))

    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please fill in all fields.', 'error')
            return redirect(url_for('login'))

        if action == 'register':
            # Register new user
            if username in users:
                flash('Username already exists. Please choose another.', 'error')
            else:
                users[username] = password
                flash('Registration successful! Please login.', 'success')

        elif action == 'login':
            # Login existing user
            if username in users and users[username] == password:
                session['username'] = username
                session['chat_history'] = []
                session['current_model'] = 'deepseek'
                flash(f'Welcome back, {username}!', 'success')
                return redirect(url_for('chat'))
            else:
                flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Logout user and clear session"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/chat')
def chat():
    """Display chat interface"""
    if 'username' not in session:
        flash('Please login to access chat.', 'error')
        return redirect(url_for('login'))

    return render_template(
        'chat.html',
        username=session['username'],
        chat_history=session.get('chat_history', []),
        current_model=session.get('current_model', 'deepseek')
    )


@app.route('/select-model', methods=['POST'])
def select_model():
    """Change the selected AI model"""
    if 'username' not in session:
        return redirect(url_for('login'))

    model = request.form.get('model', 'deepseek')
    session['current_model'] = model
    flash(f'Switched to {model.upper()} model.', 'info')
    return redirect(url_for('chat'))


@app.route('/send', methods=['POST'])
def send_message():
    """Send message to AI and get response"""
    if 'username' not in session:
        return redirect(url_for('login'))

    message = request.form.get('message', '').strip()
    if not message:
        return redirect(url_for('chat'))

    # Initialize chat history if needed
    if 'chat_history' not in session:
        session['chat_history'] = []

    current_model = session.get('current_model', 'deepseek')

    # Add user message to history
    chat_history = session['chat_history']
    chat_history.append({
        'role': 'user',
        'content': message
    })

    # Get AI response
    ai_response = get_ai_response(message, current_model, chat_history)

    # Add AI response to history
    chat_history.append({
        'role': 'assistant',
        'content': ai_response,
        'model': current_model.upper()
    })

    # Update session
    session['chat_history'] = chat_history

    return redirect(url_for('chat'))


@app.route('/clear', methods=['POST'])
def clear_chat():
    """Clear chat history"""
    if 'username' not in session:
        return redirect(url_for('login'))

    session['chat_history'] = []
    flash('Chat history cleared.', 'info')
    return redirect(url_for('chat'))


# ============== Main ==============

if __name__ == '__main__':
    # Create a demo user for easy testing
    users['demo'] = 'demo'
    print("=" * 50)
    print("Flask Chat App Demo")
    print("=" * 50)
    print("Demo user created: username='demo', password='demo'")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)
