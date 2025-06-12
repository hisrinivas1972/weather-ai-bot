# -*- coding: utf-8 -*-
import os
import re
import sys
import requests
from datetime import datetime
import google.generativeai as genai

# Load API keys from environment variables
openweather_api_key = os.environ.get('OPENWEATHER_API_KEY')
google_api_key = os.environ.get('GOOGLE_API_KEY')

# Configure Google Generative AI
genai.configure(api_key=google_api_key)
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Fetch current date
def get_current_date():
    now = datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."

# Check if input is weather-related
def is_weather_query(text):
    pattern = re.compile(r"\b(weather|temperature|forecast|rain|snow|sunny|cloudy)\b", re.IGNORECASE)
    return bool(pattern.search(text))

# Check if input is date-related
def is_date_query(text):
    pattern = re.compile(r"\b(today|date|day|time)\b", re.IGNORECASE)
    return bool(pattern.search(text))

# Extract city from the input
def extract_city(text):
    match = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)", text, re.IGNORECASE)
    if match:
        city = match.group(1).strip()
        city = re.sub(r"[?.!,]*$", "", city)
        return city
    else:
        tokens = text.strip().split()
        if tokens:
            city_candidate = tokens[-1]
            city_candidate = re.sub(r"[?.!,]*$", "", city_candidate)
            return city_candidate
    return None

# Fetch weather using OpenWeatherMap API
def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={openweather_api_key}&units=metric"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        temp = data['main']['temp']
        desc = data['weather'][0]['description']
        return f"The weather in {city} is {desc} with a temperature of {temp:.2f}°C."
    else:
        return f"Sorry, couldn't fetch weather for {city}."

# Query Google AI (Gemini)
def query_google_ai(prompt):
    context_prompt = f"""
You are a helpful assistant answering general knowledge questions. Assume today's date is {datetime.now().strftime('%A, %B %d, %Y')}.
Respond clearly and concisely.

User asked: "{prompt}"
"""
    response = model.generate_content(context_prompt)
    return response.text

# Chatbot dispatcher
def chatbot(user_input):
    if is_date_query(user_input):
        return get_current_date()
    elif is_weather_query(user_input):
        city = extract_city(user_input)
        if city:
            return get_weather(city)
        else:
            return "Please specify a city for the weather query."
    else:
        return query_google_ai(user_input)

# Entry point with command line support
if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
        response = chatbot(user_input)
        print(f"< Bot: {response}")
    else:
        print("🤖 Welcome to Weather + AI Bot! Type 'exit' or 'quit' to stop.")
        while True:
            try:
                user_input = input("> You: ")
            except EOFError:
                print("\n👋 Goodbye!")
                break
            if user_input.lower() in ['exit', 'quit']:
                print("👋 Goodbye!")
                break
            response = chatbot(user_input)
            print(f"< Bot: {response}\n")
