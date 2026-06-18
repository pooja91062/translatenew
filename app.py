from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from deep_translator import GoogleTranslator     
import uuid
import os

app = Flask(__name__)
socketio=SocketIO(app,cors_allowed_origins="*")

# DATABASE
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///translator.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY']='secret!'

db = SQLAlchemy(app)

# STATIC FOLDER
if not os.path.exists("static"):
    os.makedirs("static")

# TABLE
class Translation(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    original_text = db.Column(db.Text)

    translated_text = db.Column(db.Text)

    source_lang = db.Column(db.String(10))

    target_lang = db.Column(db.String(10))

    audio_file = db.Column(db.String(200))


# HOME
@app.route("/")
def home():
    return render_template("index.html")


# SENDER PAGE
@app.route("/sender")
def sender():
    return render_template("sender.html")


# RECEIVER PAGE
@app.route("/receiver")
def receiver():
    return render_template("receiver.html")

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

        source_lang = data.get("source_lang", "auto")

        target_lang = data.get("target_lang", "en")

        # translate
        translated = GoogleTranslator(
            source=source_lang,
            target=target_lang
        ).translate(text)

        # audio

        # save db
        new_record = Translation(
            original_text=text,
            translated_text=translated,
            source_lang=source_lang,
            target_lang=target_lang,
            audio_file=""
        )

        db.session.add(new_record)

        db.session.commit()
        socketio.emit(
        "new_message",
        {
            "translated_text": translated,
        }
    )
        

        return jsonify({
            "translated_text": translated,
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

        latest = Translation.query.order_by(
            Translation.id.desc()
        ).first()

        if not latest:
            return jsonify([])

        translated = GoogleTranslator(
            source='auto',
            target=lang
        ).translate(latest.original_text)

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

    with app.app_context():
        db.create_all()

    port = int(os.environ.get("PORT", 5000))
    
    socketio.run(app,
                 host="127.0.0.1",
                 port=port,
                 debug=True)
