from flask import Flask, render_template, jsonify, request
import datetime
import requests
from gtts import gTTS
import os
import feedparser
import re
import time
import random
from setuptools import Command

app = Flask(__name__)

WEATHER_API_KEY = "64f71b95aec8db14e72121d04e040220"

def clean_news_text(text):
    return re.sub(r'\s?(- \d+|quote|: source:.*|[\(\[].*?[\)\]])\s?', '', text, flags=re.IGNORECASE).strip()

def get_greeting():
    current_hour = datetime.datetime.now().hour
    if 6 <= current_hour < 12:
        return "गुड मॉर्निंग!"
    elif 12 <= current_hour < 16:
        return "गुड आफ्टरनून!"
    else:
        return "गुड ईवनिंग!"


def get_weather_data(city=None, lat=None, lon=None):
    try:
        if lat and lon:
            url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_API_KEY}&units=metric&lang=hi"
        elif city:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=hi"
        else:
            # fallback default location
            url = f"http://api.openweathermap.org/data/2.5/weather?q=Siwan,Bihar&appid={WEATHER_API_KEY}&units=metric&lang=hi"

        data = requests.get(url).json()

        return {
            "city": data["name"],
            "temp": round(data["main"]["temp"]),
            "temp_max": round(data["main"]["temp_max"]),
            "temp_min": round(data["main"]["temp_min"]),
            "wind_speed": round(data["wind"]["speed"] * 3.6),
            "description": data["weather"][0]["description"],
            "sunrise": datetime.datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p"),
            "sunset": datetime.datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p")
        }

    except Exception as e:
        print("Weather Error:", e)
        return None

def get_top_news():
    try:
        feed = feedparser.parse("https://www.amarujala.com/rss/breaking-news.xml")
        entries = feed.entries
        if not entries:
            return "माफ़ कीजिए, मैं आज की खबरें प्राप्त नहीं कर सका।"
        news_summary = "आज की मुख्य ख़बरें इस प्रकार हैं: "
        for entry in entries[:5]:
            news_summary += f"{clean_news_text(entry.title)}. "
        return news_summary
    except Exception as e:
        print("News Error:", e)
        return "माफ़ कीजिए, आज खबरें लाने में समस्या आ गई है।"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/start_alarm', methods=['POST'])
def start_alarm():
    data = request.get_json()
    lat = data.get("lat")
    lon = data.get("lon")
    weather = get_weather_data(lat=lat, lon=lon)
    news = get_top_news()
    time_str = datetime.datetime.now().strftime("%I:%M %p")
    greeting = get_greeting()

    if weather:
        weather_speech = (
            f"{greeting} इस वक़्त {time_str} बजे हैं. {weather['city']} में वर्तमान तापमान {weather['temp']} डिग्री सेल्सियस है. "
            f"अधिकतम तापमान {weather['temp_max']} और न्यूनतम तापमान {weather['temp_min']} डिग्री सेल्सियस रहेगा. "
            f"हवा की रफ़्तार लगभग {weather['wind_speed']} किलोमीटर प्रति घंटा है. "
            f"आज का मौसम {weather['description']} है. "
            f"सूर्योदय {weather['sunrise']} बजे हुआ था और सूर्यास्त {weather['sunset']} बजे होगा. "
        )
    else:
        weather_speech = "माफ़ कीजिए, मौसम की जानकारी प्राप्त नहीं हो सकी। "

    final_speech = weather_speech + news

    # Generate unique filename using timestamp
    filename = f"morning_{int(time.time())}.mp3"
    audio_path = os.path.join("static", filename)

    try:
        tts = gTTS(text=final_speech, lang="hi")
        tts.save(audio_path)
        print(f"[INFO] Audio saved at {audio_path}")
    except Exception as e:
        print("TTS Error:", e)
        return jsonify({"error": "Failed to generate audio."}), 500

    return jsonify({
        "audio_url": f"/static/{filename}",
        "message": "Weather and News Audio ready!"
    })

@app.route('/process-command', methods=['POST'])
def process_command():
    data = request.get_json()
    command = data.get("command", "").lower()
    print(f"User Command Received: {command}")

    # --- Define keyword sets ---
    time_keywords = ["समय", "time", "कितना बजे", "टाइम", "kitna baja", "abhi kya samay hai"]
    wind_keywords = ["रफ़्तार", "wind speed", "हवा", "hawa ki speed", "हवा की गति"]
    weather_keywords = ["मौसम", "weather", "आज का मौसम", "mausam", "सूर्यास्त", "सूर्योदय", "sunrise", "sunset"]
    temp_keywords = ["तापमान", "temperature", "टेंपरेचर", "गर्मी", "ठंड", "kitna degree"]
    date_keywords = ["तारीख", "date", "aaj ki tareekh", "आज कौन सी तारीख"]
    news_keywords = ["समाचार", "news", "ताजा खबर", "खबरें"]
    joke_keywords = ["joke", "जोक", "मजाक", "हँसी", "funny"]
    day_keywords = ["दिन", "कौन सा दिन", "today is", "day", "वार है", "क्या दिन", "आज कौन सा दिन", "आज क्या है"]

    # --- Intent Matching Function ---
    def matches_any(keywords):
        return any(kw in command for kw in keywords)

    # --- Respond accordingly ---
    if matches_any(time_keywords):
        now = datetime.datetime.now().strftime('%I:%M %p')
        response_text = f"अभी समय है {now}"
    
    elif matches_any(date_keywords):
        hindi_months = {
        "January": "जनवरी", "February": "फ़रवरी", "March": "मार्च", "April": "अप्रैल",
        "May": "मई", "June": "जून", "July": "जुलाई", "August": "अगस्त",
        "September": "सितंबर", "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर"
        }
        today = datetime.datetime.now().strftime('%d %B %Y')
        day, month_en, year = today.split()
        month_hi = hindi_months.get(month_en, month_en)
        response_text = f"आज की तारीख है {int(day)} {month_hi} {year}"

    elif matches_any(day_keywords):
        hindi_days = {
        "Monday": "सोमवार",
        "Tuesday": "मंगलवार",
        "Wednesday": "बुधवार",
        "Thursday": "गुरुवार",
        "Friday": "शुक्रवार",
        "Saturday": "शनिवार",
        "Sunday": "रविवार"
        }

        day_en = datetime.datetime.now().strftime('%A')
        day_hi = hindi_days.get(day_en, day_en)
        response_text = f"आज दिन है {day_hi}"    

    elif matches_any(wind_keywords):
        data = request.get_json()
        lat = data.get("lat")
        lon = data.get("lon")
        weather = get_weather_data(lat=lat, lon=lon)
        if weather:
            response_text = f"हवा की रफ़्तार {weather['wind_speed']} किलोमीटर प्रति घंटा है।"
        else:
            response_text = "माफ़ कीजिए, हवा की रफ़्तार जानकारी प्राप्त नहीं हो सकी।"

    elif matches_any(temp_keywords):
        data = request.get_json()
        lat = data.get("lat")
        lon = data.get("lon")
        weather = get_weather_data(lat=lat, lon=lon)
        if weather:
            response_text = f"इस समय तापमान {weather['temp_max']} डिग्री सेल्सियस है।"
        else:
            response_text = "माफ़ कीजिए, तापमान की जानकारी प्राप्त नहीं हो सकी।"

    elif matches_any(weather_keywords):
        data = request.get_json()
        lat = data.get("lat")
        lon = data.get("lon")
        weather = get_weather_data(lat=lat, lon=lon)
        if weather:
            response_text = f" सर {weather['city']} मे आज अधिकतम तापमान {weather['temp_max']}°C है। आज {weather['description']} रहेगा और हवा की रफ्तार {weather['wind_speed']} km प्रति घंटा है। आज का सूर्योदय का समय है {weather['sunrise']} बजे और सूर्यास्त {weather[ 'sunset']} बजे होगा"
        else:
            response_text = "माफ़ कीजिए, मौसम की जानकारी नहीं मिल सकी।"

    elif matches_any(news_keywords):
        news = get_top_news()
        response_text = news

    elif matches_any(joke_keywords):
        jokes = [
            "टीचर: बताओ पृथ्वी से चाँद कितनी दूर है? छात्र: सर एक कदम! क्योंकि टीवी में रोज़ कहते हैं 'चाँद तक क्या जाना, एक कदम और बढ़ाना!'",
            "डॉक्टर: आप रोज़ एक्सरसाइज करते हैं? मरीज़: हां, रोज़ सुबह अलार्म बंद करके दौड़कर सोने जाता हूं।"
        ]
        response_text = random.choice(jokes)

    else:
        response_text = f"आपने कहा: {command}. यह आदेश समझ में नहीं आया।"

    # --- Text to Speech ---
    filename = f"response_{int(time.time())}.mp3"
    response_audio = os.path.join("static", filename)

    try:
        tts = gTTS(text=response_text, lang="hi")
        tts.save(response_audio)
        print(f"[INFO] Response audio saved at {response_audio}")
    except Exception as e:
        print("TTS Error:", e)
        return jsonify({"error": "Failed to generate response."}), 500

    return jsonify({
        "reply": response_text,
        "audio_url": f"/static/{filename}"
    })

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000, threaded=True)