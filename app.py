from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from flask_socketio import SocketIO, emit
from deep_translator import GoogleTranslator     
import uuid
import os

app = Flask(__name__)
socketio=SocketIO(app,cors_allowed_origins="*")

# DATABASE
client = MongoClient("mongodb://localhost:27017/")
db = client["translator_db"]

translations = db["translations"]

# STATIC FOLDER
if not os.path.exists("static"):
    os.makedirs("static")



# HOME
@app.route("/")
def home():
    return render_template("index.html")

# SOCKET CONNECT EVENT
@socketio.on('connect')
def handle_connect():
    print("Client Connected")
    emit('message', {'msg': 'Connected Successfully'})
    


# SEND MESSAGE
@app.route("/translate", methods=["POST"])
def translate():

    try:

        data = request.json

        text = data.get("text")

        

        # translate

        english = GoogleTranslator(
            source="auto",
            target="en"
        ).translate(text)

        hindi = GoogleTranslator(
            source="auto",
            target="hi"
        ).translate(text)

        gujarati = GoogleTranslator(
            source="auto",
            target="gu"
        ).translate(text)

        # audio

        # save db
        translations.insert_one({
           "original_text": text,
           "en": english,
           "hi": hindi,
           "gu": gujarati,
           "source_lang": "auto"
})

        socketio.emit(
        "new_message",
        {
            "original": text,
            "en": english,
            "hi": hindi,
            "gu": gujarati
        }
    )
        
        
        return jsonify({
            "original": text,
            "en": english,
            "hi": hindi,
            "gu": gujarati
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        })


# RECEIVER GET MESSAGE
@app.route("/target_lang")
def target_lang():

    try:

        lang = request.args.get("lang", "en")

        latest = translations.find_one(
            sort=[("_id", -1)]
        )

        if not latest:
            return jsonify([])

        translated = latest.get(lang, "")   

        return jsonify([
            {
                "translated_text": translated,
            }
        ])

    except Exception as e:

        return jsonify({
            "error": str(e)
        })
  

if __name__ == "__main__":  

    port = int(os.environ.get("PORT", 5000))
    
    socketio.run(app,
                 host="127.0.0.1",
                 port=port,
                 debug=True)
