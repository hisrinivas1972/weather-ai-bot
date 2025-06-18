import os
import re
import requests
from datetime import datetime
import google.generativeai as genai
from google.colab import userdata

# Load API keys securely from Colab Secrets
openweather_api_key = userdata.get('OPENWEATHER_API_KEY')
google_api_key = userdata.get('GOOGLE_API_KEY')

# Set environment variables (optional)
os.environ['OPENWEATHER_API_KEY'] = openweather_api_key
os.environ['GOOGLE_API_KEY'] = google_api_key

# Configure Gemini
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# -------- INTENT DETECTORS --------

def is_date_query(text):
    pattern = re.compile(
        r"\b(what(?:'s| is)?\s+(today|date|day)|current\s+(date|day)|today['s]*\s+date|what\s+time\s+is\s+it)\b",
        re.IGNORECASE
    )
    return bool(pattern.search(text))

def is_weather_query(text):
    pattern = re.compile(r"\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b", re.IGNORECASE)
    return bool(pattern.search(text))

# -------- CITY EXTRACTION (IMPROVED) --------

def extract_city(text):
    noise_words = {"today", "now", "please", "right", "currently", "tomorrow", "this", "week", "tonight"}

    # Try extracting city after "in" or "for"
    match = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)", text, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
    else:
        # Fallback: last word
        tokens = text.strip().split()
        city = tokens[-1]

    # Clean punctuation
    city = re.sub(r"[?.!,]*$", "", city)

    # Remove any noise words from the end
    words = city.lower().split()
    filtered = [word for word in words if word not in noise_words]

    if not filtered:
        return None

    return ' '.join(filtered).title()

# -------- WEATHER AGENT --------

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"The weather in {city} is {desc} with a temperature of {temp:.2f}°C."
    else:
        print(f"[Debug] Weather API error: {response.status_code} | {response.json()}")
        return f"Sorry, couldn't fetch weather for {city}."

# -------- DATE AGENT --------

def get_current_date():
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."

# -------- GENERAL AI AGENT --------

def query_google_ai(prompt):
    context_prompt = f"""
You are a helpful assistant answering general knowledge questions. Assume today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
Respond clearly and concisely.

User asked: "{prompt}"
"""
    response = model.generate_content(context_prompt)
    return response.text.strip()

# -------- DISPATCHER --------

def chatbot(user_input):
    if is_date_query(user_input):
        print("[Debug] Routed to Date Agent")
        return get_current_date()
    elif is_weather_query(user_input):
        print("[Debug] Routed to Weather Agent")
        city = extract_city(user_input)
        if city:
            return get_weather(city)
        else:
            return "Please specify a city for the weather query."
    else:
        print("[Debug] Routed to Gemini AI Agent")
        return query_google_ai(user_input)

# -------- INTERACTIVE LOOP --------

print("🤖 Welcome to Weather + AI Bot! Type 'exit' or 'quit' to stop.\n")

while True:
    user_input = input("> You: ")
    if user_input.lower() in ['exit', 'quit']:
        print("👋 Goodbye!")
        break
    response = chatbot(user_input)
    print(f"< Bot: {response}\n")
