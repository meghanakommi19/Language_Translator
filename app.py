from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
from deep_translator import GoogleTranslator
import speech_recognition as sr
from werkzeug.utils import secure_filename
import os
from gtts import gTTS
import io

app = Flask(__name__)
CORS(app)

# Upload folder for audio files
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Supported Languages
supported_languages = {
    'auto': 'Auto Detect',
    'ar': 'Arabic',
    'bn': 'Bengali',
    'zh-CN': 'Chinese',
    'en': 'English',
    'fr': 'French',
    'de': 'German',
    'el': 'Greek',
    'gu': 'Gujarati',
    'hi': 'Hindi',
    'it': 'Italian',
    'ja': 'Japanese',
    'kn': 'Kannada',
    'ko': 'Korean',
    'ml': 'Malayalam',
    'mr': 'Marathi',
    'ne': 'Nepali',
    'ta': 'Tamil',
    'te': 'Telugu'
}


# ---------------- HOME PAGE ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- SPEECH TO TEXT ----------------
@app.route("/transcribe", methods=["POST"])
def transcribe_audio():

    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    filename = secure_filename(audio_file.filename)

    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    audio_file.save(filepath)

    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(filepath) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio)

        os.remove(filepath)

        return jsonify({
            "success": True,
            "transcribed_text": text
        })

    except sr.UnknownValueError:
        os.remove(filepath)
        return jsonify({"error": "Could not understand audio"}), 400

    except sr.RequestError:
        os.remove(filepath)
        return jsonify({"error": "Speech service unavailable"}), 503


# ---------------- TEXT TRANSLATION ----------------
@app.route("/chat", methods=["POST"])
def chat():

    data = request.get_json()

    text = data.get("text", "")
    src_lang = data.get("src_lang", "auto")   # auto detect
    dest_lang = data.get("dest_lang", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        translator = GoogleTranslator(source=src_lang, target=dest_lang)
        translated_text = translator.translate(text)

        return jsonify({
            "translated": translated_text
        })

    except Exception as e:
        print("Translation Error:", e)
        return jsonify({"error": "Translation failed"}), 500


# ---------------- TEXT TO SPEECH ----------------
@app.route("/speak", methods=["POST"])
def speak():

    data = request.get_json()

    text = data.get("text", "")
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"error": "No text provided"}), 400

    try:
        tts = gTTS(text=text, lang=lang)

        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)

        return send_file(
            mp3_fp,
            mimetype="audio/mpeg",
            as_attachment=False,
            download_name="speech.mp3"
        )

    except Exception as e:
        print("TTS Error:", e)
        return jsonify({"error": "Text to Speech failed"}), 500


# ---------------- RUN SERVER ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)