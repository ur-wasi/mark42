import openai
import json
import os
import datetime
import requests
import speech_recognition as sr
from gtts import gTTS
import threading

# Set your API keys here
openai.api_key = "API_KEY"
WEATHER_API_KEY = "API_KEY"

recognizer = sr.Recognizer()

# Memory handling
if os.path.exists("chat_memory.json"):
    with open("chat_memory.json", "r") as f:
        memory = json.load(f)
else:
    memory = {}

def get_weather():
    try:
        # IP-based location
        location_data = requests.get("https://ipinfo.io/json").json()
        city = location_data["city"]
        weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(weather_url).json()

        temp = data["main"]["temp"]
        temp_max = data["main"]["temp_max"]
        temp_min = data["main"]["temp_min"]
        speed = data["wind"]["speed"]
        sunrise_time = data["sys"]["sunrise"]
        sunset_time = data["sys"]["sunset"]
        description = data["weather"][0]["description"]
        sunrise = datetime.datetime.fromtimestamp(sunrise_time).strftime("%I:%M %p")
        sunset = datetime.datetime.fromtimestamp(sunset_time).strftime("%I:%M %p")

        return city, temp, temp_max, temp_min, speed, description, sunrise, sunset
    except Exception as e:
        print(f"Error: {e}")
        return "your area", "unknown", "unknown", "unknown", "unknown", "unknown"

def greet_user():
    now = datetime.datetime.now()
    hour = now.hour
    greeting = "Good morning sir" if hour < 12 else "Good afternoon sir" if hour < 18 else "Good evening sir"
    time_str = now.strftime("%I:%M %p")
    city, temp, temp_max, temp_min, speed, description, sunrise, sunset = get_weather()
    msg = f"{greeting}. The time is {time_str}. In your {city} the current temperature is {temp}°C. with a high of {temp_max}°C and a low of {temp_min}°C. Wind speed is approximately {speed} meters per second, conditions are described as {description} Sunrise was at {sunrise} and sunset is expected at {sunset} today."
    speak(msg)

def check_local_memory(question):
    return memory.get(question)

def ask_openai(question):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": question}]
    )
    answer = response['choices'][0]['message']['content'].strip()
    memory[question] = answer
    with open("chat_memory.json", "w") as f:
        json.dump(memory, f, indent=4)
    return answer

def listen_command():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            query = recognizer.recognize_google(audio, language='en-IN')
            print("You said:", query)
            return query
        except sr.WaitTimeoutError:
            return ""
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            print("Sorry, I can't connect right now.")
            return ""

def speak(text):
    speaker = gTTS(text=text, lang='en')
    speaker.save("response.mp3")
    os.system("mpg321 response.mp3")

def continuous_listen():
    while True:
        command = listen_command()
        if command:
            if command.lower() in ['exit', 'quit', 'bye']:
                speak("Goodbye!")
                break

            saved = check_local_memory(command)
            if saved:
                speak(saved)
            else:
                reply = ask_openai(command)
                speak(reply)

if __name__ == "__main__":
    greet_user()
    continuous_listen()