%%writefile multi_chatbot.py


import os
import re
import requests
from datetime import datetime
import google.generativeai as genai
import streamlit as st

# --- Load API keys from environment variables or other secure storage ---
openweather_api_key = os.getenv('OPENWEATHER_API_KEY')
google_api_key = os.getenv('GOOGLE_API_KEY')

# --- Set environment variables (optional) ---
os.environ['OPENWEATHER_API_KEY'] = openweather_api_key or ""
os.environ['GOOGLE_API_KEY'] = google_api_key or ""

# --- Configure Gemini ---
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# --- INTENT DETECTORS ---

def is_date_query(text):
    pattern = re.compile(
        r"\b(what(?:'s| is)?\s+(today|date|day)|current\s+(date|day)|today['s]*\s+date|what\s+time\s+is\s+it)\b",
        re.IGNORECASE
    )
    return bool(pattern.search(text))

def is_weather_query(text):
    pattern = re.compile(r"\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b", re.IGNORECASE)
    return bool(pattern.search(text))

# --- CITY EXTRACTION ---

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

# --- WEATHER AGENT ---

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"The weather in {city} is {desc} with a temperature of {temp:.2f}°C."
    else:
        st.write(f"[Debug] Weather API error: {response.status_code} | {response.json()}")
        return f"Sorry, couldn't fetch weather for {city}."

# --- DATE AGENT ---

def get_current_date():
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."

# --- GENERAL AI AGENT ---

def query_google_ai(prompt):
    context_prompt = f"""
You are a helpful assistant answering general knowledge questions. Assume today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
Respond clearly and concisely.

User asked: "{prompt}"
"""
    response = model.generate_content(context_prompt)
    return response.text.strip()

# --- DISPATCHER ---

def chatbot(user_input, debug=False):
    if is_date_query(user_input):
        if debug:
            st.write("[Debug] Routed to Date Agent")
        return get_current_date()
    elif is_weather_query(user_input):
        if debug:
            st.write("[Debug] Routed to Weather Agent")
        city = extract_city(user_input)
        if city:
            return get_weather(city)
        else:
            return "Please specify a city for the weather query."
    else:
        if debug:
            st.write("[Debug] Routed to Gemini AI Agent")
        return query_google_ai(user_input)

# --- STREAMLIT UI ---

st.title("🤖 Weather + AI Bot")
st.markdown("Ask about weather, dates, travel plans, or general AI questions.")

debug_mode = st.checkbox("Show debug info")

user_input = st.text_input("Enter your message:")

if user_input:
    response = chatbot(user_input, debug=debug_mode)
    st.markdown(f"**Bot:** {response}")
