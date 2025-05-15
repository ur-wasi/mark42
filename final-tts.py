import openai
import json
import os
import datetime
import requests
import speech_recognition as sr
from langdetect import detect
import random
import time
from google.cloud import texttospeech

# Set API keyss
openai.api_key = "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"
WEATHER_API_KEY = "64f71b95aec8db14e72121d04e040220"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "mark42-457319-77579cd6f7ff.json"

recognizer = sr.Recognizer()

# Load memory
if os.path.exists("chat_memory.json"):
    with open("chat_memory.json", "r", encoding="utf-8") as f:
        memory = json.load(f)
else:
    memory = {}

# Custom responses
custom_responses = {
    "wake_jarvis": {
        "triggers": ["hello jarvis", "wake up jarvis", "jarvis suno", "uth jao jarvis"],
        "responses_en": ["Yes sir, I'm up.", "At your service."],
        "responses_hi": ["Haan sir, main jag gaya hoon.", "Main seva mein hoon."]
    },
    "how_are_you": {
        "triggers": ["how are you", "kya haal", "kaisa hai", "kaise ho"],
        "responses_en": ["Running fine sir!", "All good here."],
        "responses_hi": ["Main bilkul theek hoon sir.", "Sab sahi hai idhar."]
    }
}

fallback_responses = {
    "en": ["Sorry, I don't understand.", "I'm not sure about that."],
    "hi": ["Maaf kijiye, main samjha nahi.", "Mujhe ye nahi pata."]
}

def speak(text, lang="en"):
    try:
        client = texttospeech.TextToSpeechClient()

        voice_params = {
            "en": {"language_code": "en-US", "name": "en-US-Wavenet-D"},
            "hi": {"language_code": "hi-IN", "name": "hi-IN-Wavenet-B"}
        }

        voice_config = voice_params.get(lang, voice_params["en"])

        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code=voice_config["language_code"],
            name=voice_config["name"]
        )
        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )

        with open("response.mp3", "wb") as out:
            out.write(response.audio_content)

        os.system("mpg321 response.mp3 > /dev/null 2>&1")
    except Exception as e:
        print("TTS Error:", e)

def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"

def play_intro():
    os.system("mpg321 jarvis-intro.mp3")
    time.sleep(1)
    os.system("mpg321 jarvis-intro-2.mp3")

def listen_command():
    with sr.Microphone() as source:
        print("🎤 Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=8, phrase_time_limit=10)
            query = recognizer.recognize_google(audio, language='hi-IN')
            print("You said:", query)
            return query
        except:
            return ""

def get_weather_data():
    try:
        location_data = requests.get("https://ipinfo.io/json").json()
        city = location_data["city"]
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()

        weather = {
            "city": city,
            "temp": data["main"]["temp"],
            "temp_max": data["main"]["temp_max"],
            "temp_min": data["main"]["temp_min"],
            "wind_speed": data["wind"]["speed"] * 3.6,
            "description": data["weather"][0]["description"],
            "sunrise": datetime.datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p"),
            "sunset": datetime.datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p")
        }
        return weather
    except:
        return None

def check_custom_responses(command, lang):
    cmd = command.lower()
    for data in custom_responses.values():
        if any(trigger in cmd for trigger in data["triggers"]):
            return random.choice(data["responses_hi" if lang == "hi" else "responses_en"])
    return None

def get_day_and_time_response(command, lang):
    now = datetime.datetime.now()
    if "day" in command or "din" in command:
        return now.strftime("Today is %A." if lang == "en" else "Aaj %A hai.")
    elif "time" in command or "samay" in command:
        return now.strftime("The time is %I:%M %p." if lang == "en" else "Abhi ka samay hai %I:%M %p.")
    return None

def get_weather_response(command, lang, weather):
    if not weather:
        return "Weather information is not available." if lang == "en" else "Mausam ki jankari uplabdh nahi hai."

    if "current temperature" in command or "taapmaan" in command:
        return (f"The current temperature in {weather['city']} is {weather['temp']:.1f}°C." if lang == "en"
                else f"{weather['city']} mein vartamaan taapmaan hai {weather['temp']:.1f}°C.")
    elif "high" in command or "maximum" in command:
        return (f"Today's high is {weather['temp_max']:.1f}°C." if lang == "en"
                else f"Aaj ka adhiktam taapmaan hai {weather['temp_max']:.1f}°C.")
    elif "low" in command or "minimum" in command:
        return (f"Today's low is {weather['temp_min']:.1f}°C." if lang == "en"
                else f"Aaj ka niyuntam taapmaan hai {weather['temp_min']:.1f}°C.")
    elif "wind" in command or "hawa" in command:
        return (f"Wind speed is {weather['wind_speed']:.1f} km/h." if lang == "en"
                else f"Hawa ki gati hai {weather['wind_speed']:.1f} km/h.")
    elif "sunrise" in command or "surya" in command:
        return f"Sunrise was at {weather['sunrise']}." if lang == "en" else f"Surya uday hua tha {weather['sunrise']} baje."
    elif "sunset" in command or "ast" in command:
        return f"Sunset will be at {weather['sunset']}." if lang == "en" else f"Surya ast hoga {weather['sunset']} baje."
    return None

def ask_openai(question):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": question}]
        )
        return response['choices'][0]['message']['content'].strip()
    except:
        return None

def main_loop():
    while True:
        command = listen_command()
        if not command:
            continue

        lang = detect_language(command)
        memory_key = f"{lang}:{command}"

        if command.lower() in ['exit', 'bye', 'quit', 'band karo jarvis']:
            speak("Goodbye!" if lang == "en" else "Alvida!", lang)
            break

        if memory_key in memory:
            response = memory[memory_key]
        else:
            response = check_custom_responses(command, lang)

            if not response:
                weather = get_weather_data()
                response = get_day_and_time_response(command.lower(), lang)
                if not response:
                    response = get_weather_response(command.lower(), lang, weather)

            if not response:
                response = ask_openai(command)
                if response:
                    memory[memory_key] = response
                    with open("chat_memory.json", "w", encoding="utf-8") as f:
                        json.dump(memory, f, indent=4, ensure_ascii=False)

        if not response:
            response = random.choice(fallback_responses.get(lang, fallback_responses["en"]))

        speak(response, lang)

if __name__ == "__main__":
    time.sleep(2)
    play_intro()
    time.sleep(5)
    speak("Jarvis aapki khidtmat main hazir hai sir!", lang="hi")
    main_loop()