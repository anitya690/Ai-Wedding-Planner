from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import traceback

def api_request(method, url, **kwargs):
    """Make external API calls without inheriting broken local proxy settings."""
    with requests.Session() as session:
        session.trust_env = False
        return session.request(method, url, **kwargs)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Check API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

print(f"\n🔑 GROQ_API_KEY: {'✅ Found' if GROQ_API_KEY else '❌ Missing'}")
print(f"🔑 PEXELS_API_KEY: {'✅ Found' if PEXELS_API_KEY else '⚠️ Optional'}")

def get_wedding_image(query):
    """Fetch wedding images from Pexels"""
    if not PEXELS_API_KEY:
        return None
    try:
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": PEXELS_API_KEY}
        params = {"query": f"wedding {query}", "per_page": 5, "orientation": "landscape"}
        response = api_request("GET", url, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("photos"):
                return data["photos"][0]["src"]["large2x"]
        return "https://images.pexels.com/photos/1024993/pexels-photo-1024993.jpeg"
    except:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'success': False, 'error': 'Please enter a message!'}), 400
        
        print(f"\n💬 User: {user_message}")
        if not GROQ_API_KEY:
            return jsonify({'success': False, 'error': 'GROQ_API_KEY is missing in .env'}), 500

        # Direct API call to Groq (without groq library)
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "llama-3.3-70b-versatile",
            "messages": [
                {
                    "role": "system",
                    "content": """You are 'WeddingWise AI' - a friendly wedding planning assistant. 
Help users with wedding budgets, venues, decorations, rituals, vendors, timeline, and honeymoon plans.
Be warm and supportive. Use emojis occasionally. Keep responses concise (4-5 sentences)."""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        response = api_request("POST", url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            ai_reply = result['choices'][0]['message']['content']
            print(f"✨ AI: {ai_reply[:100]}...")
            
            # Get image
            image_url = get_wedding_image(user_message[:20])
            
            return jsonify({
                'success': True,
                'reply': ai_reply,
                'image_url': image_url
            })
        else:
            print(f"❌ Groq API error: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'error': 'AI service error'}), 500
            
    except Exception as e:
        print(f"❌ Error: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/suggestions', methods=['GET'])
def get_suggestions():
    suggestions = [
        "How to plan a wedding under ₹10 lakhs?",
        "What are the key rituals in an Indian wedding?",
        "Best time of year for a destination wedding",
        "How to choose the perfect wedding venue?",
        "Wedding decoration ideas on a budget",
        "What questions to ask a wedding photographer?",
        "Sample wedding day timeline",
        "Mehendi ceremony planning ideas"
    ]
    return jsonify({'success': True, 'suggestions': suggestions})

if __name__ == '__main__':
    print("\n" + "="*50)
    print("💍 AI Wedding Planner - Starting...")
    print("="*50)
    print(f"🌐 Server: http://localhost:8080")
    print("="*50 + "\n")
    app.run(debug=True, host='0.0.0.0', port=8080)