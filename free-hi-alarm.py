import datetime
import requests
import os
import time
import pygame
import subprocess
import feedparser
import re
import threading
from gtts import gTTS
from deep_translator import GoogleTranslator
import speech_recognition as sr

WEATHER_API_KEY = "API_KEY"
stop_requested = False  # Global flag

# Translate text
def translate_to_language(text, target_lang="hi"):
    return GoogleTranslator(source='auto', target=target_lang).translate(text)

# Speak text
def speak(text, lang="hi"):
    tts = gTTS(text=text, lang=lang, slow=False)
    tts.save("morning_response.mp3")
    os.system("mpg321 morning_response.mp3 > /dev/null 2>&1")

# Play music
def play_music():
    pygame.mixer.init()
    pygame.mixer.music.load("intro-music.mp3")
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play()

# Stop music
def stop_music():
    if pygame.mixer.get_init():
        pygame.mixer.music.stop()

# Clean news
def clean_news_text(text):
    return re.sub(r'\s?(- \d+|quote|: source:.*|[\(\[].*?[\)\]])\s?', '', text, flags=re.IGNORECASE).strip()

# Get weather
def get_weather_data(city="Siwan, Bihar"):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        data = requests.get(url).json()
        return {
            "city": city,
            "temp": round(data["main"]["temp"]),
            "temp_max": round(data["main"]["temp_max"]),
            "temp_min": round(data["main"]["temp_min"]),
            "wind_speed": round(data["wind"]["speed"] * 3.6),
            "description": data["weather"][0]["description"],
            "sunrise": datetime.datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p"),
            "sunset": datetime.datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p")
        }
    except:
        return None

# Get top news
def get_top_news():
    try:
        feed = feedparser.parse("https://www.amarujala.com/rss/breaking-news.xml")
        entries = feed.entries
        if not entries:
            return "माफ़ कीजिए, मैं आज की खबरें प्राप्त नहीं कर सका।"
        news_summary = "आज की मुख्य ख़बरों पर एक नज़र। "
        for entry in entries[:5]:
            news_summary += f"{clean_news_text(entry.title)}. "
        return news_summary
    except:
        return "माफ़ कीजिए, आज खबरें लाने में समस्या आ गई है।"

# Background listener
def listen_for_commands():
    global stop_requested
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Listening for command...")

        while not stop_requested:
            try:
                audio = recognizer.listen(source, timeout=5)
                command = recognizer.recognize_google(audio, language='hi-IN')
                print(f"User said: {command}")

                if any(k in command.lower() for k in ["बंद करो", "alarm बंद", "जाग गया हूँ", "jarvis बंद"]):
                    print("Stop command detected.")
                    stop_music()
                    stop_requested = True
                    subprocess.Popen(["python3", "test.py"])
                    os._exit(0)
            except:
                continue

# Main function
def main():
    global stop_requested
    city_name = "Siwan, Bihar"

    # Start background listener
    listener_thread = threading.Thread(target=listen_for_commands)
    listener_thread.daemon = True
    listener_thread.start()

    play_music()

    weather = get_weather_data(city=city_name)
    time_str = datetime.datetime.now().strftime("%I:%M %p")

    if not stop_requested and weather:
        phrase = (
            f"गुड मॉर्निंग! इस वक़्त सुबह के {time_str} बजे हैं. {weather['city']} में वर्तमान तापमान {weather['temp']} डिग्री सेल्सियस है. "
            f"अधिकतम तापमान {weather['temp_max']} और न्यूनतम तापमान {weather['temp_min']} डिग्री सेल्सियस रहेगा. "
            f"हवा की रफ़्तार लगभग {weather['wind_speed']} किलोमीटर प्रति घंटा है. "
            f"आज का मौसम {weather['description']} है. "
            f"सूर्योदय {weather['sunrise']} बजे हुआ था और सूर्यास्त {weather['sunset']} बजे होगा."
        )
        speak(phrase, lang="hi")
    else:
        speak("माफ़ कीजिए, मौसम की जानकारी प्राप्त नहीं हो सकी।", lang="hi")

    stop_music()

    if not stop_requested:
        play_music()
        news = get_top_news()
        news_in_hindi = translate_to_language(news, target_lang="hi")
        speak(news_in_hindi, lang="hi")

    stop_music()

    # Wait briefly for any command
    print("News completed. Waiting 10 seconds for any stop command...")

    wait_time = 5
    for _ in range(wait_time):
        if stop_requested:
            break
        time.sleep(1)

    if not stop_requested:
        print("No command detected. Launching test.py...")
        subprocess.Popen(["python3", "test.py"])
        os._exit(0)

if __name__ == "__main__":
    main()