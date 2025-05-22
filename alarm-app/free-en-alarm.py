import datetime
import requests
import os
import time
import pygame
import subprocess
import feedparser
import re
import speech_recognition as sr
import threading
from gtts import gTTS

WEATHER_API_KEY = "API_KEY"
stop_requested = False  # global flaggg

# Speak text
def speak(text, lang="en", speed=0.98):
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
def get_weather_data():
    try:
        city = "Siwan, Bihar"
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

# Get news
def get_top_news():
    try:
        feed = feedparser.parse("https://feeds.feedburner.com/ndtvnews-top-stories")
        entries = feed.entries
        if not entries:
            return "Sorry, I couldn't get the news today."
        news_summary = "Here are today's top stories: "
        for entry in entries[:5]:
            news_summary += f"{clean_news_text(entry.title)}. "
        return news_summary
    except:
        return "Sorry, there was an issue fetching the news."

# Background command listener
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
                command = recognizer.recognize_google(audio)
                print(f"Command received: {command.lower()}")

                if "stop the alarm" in command.lower() or "jarvis stop" in command.lower():
                    print("Command recognized. Stopping.")
                    stop_requested = True
                    stop_music()
                    subprocess.Popen(["python3", "test.py"])
                    os._exit(0)

            except:
                continue

# Main function
def main():
    global stop_requested

    # Start background listener
    command_thread = threading.Thread(target=listen_for_commands)
    command_thread.daemon = True
    command_thread.start()

    play_music()

    weather = get_weather_data()
    time_str = datetime.datetime.now().strftime("%I:%M %p")

    if not stop_requested and weather:
        phrase = (
            f"Good morning! It's {time_str}. The weather in Siwan is {weather['temp']} degrees Celsius with {weather['description']}. "
            f"The maximum temperature today will be {weather['temp_max']} and the minimum will be {weather['temp_min']} degrees Celsius. "
            f"The wind speed is {weather['wind_speed']} kilometers per hour. "
            f"Sunrise was at {weather['sunrise']} and the sunset will be at {weather['sunset']}. "
            f"Sir, I would make sure your day stays calm."
        )
        speak(phrase, lang="en")
    else:
        speak("Sorry, I couldn't fetch the weather information.", lang="en")

    stop_music()

    if not stop_requested:
        play_music()
        news = get_top_news()
        speak(news, lang="en")

    stop_music()

    print("News completed. Waiting 10 seconds for any stop command...")
    wait_time = 10
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