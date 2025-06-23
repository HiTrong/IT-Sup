import os
import uuid
import speech_recognition as sr
from flask import Flask, request, jsonify, send_file, session
from flask_session import Session
from flask_cors import CORS
from gtts import gTTS
import av
import numpy as np
import soundfile as sf
import requests


MODEL_OPTION = "qwen"
# LLM_SERVER_URL = "http://127.0.0.1:5005/{}"
LLM_SERVER_URL = "https://af6d-34-74-192-43.ngrok-free.app/{}"


app = Flask(__name__)
CORS(app, supports_credentials=True)
UPLOAD_FOLDER = "uploads"
PROCESSED_FOLDER = "processed"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"
Session(app) # Initialize Flask-Session

def get_state():
    if not session.get("question"):
        session["question"] = "Xin chào"
    if not session.get("state"):
        session["state"] = "normal"
    if not session.get("top_k"):
        session["top_k"] = 5
    if not session.get("unknown_question"):
        session["unknown_question"] = []
    if not session.get("phone_number"):
        session["phone_number"] = ""
    if not session.get("history"):
        session["history"] = []
    return {
        "question": session["question"],
        "state": session["state"],
        "top_k": session["top_k"],
        "history": session["history"],
        "unknown_question": session["unknown_question"],
        "phone_number": session["phone_number"]
    }

def convert_m4a_to_wav(input_path, output_path):
    container = av.open(input_path)
    audio_stream = next(s for s in container.streams if s.type == 'audio')

    # Đặt output là mono 1 kênh, 16bit signed, 44100Hz
    resampler = av.audio.resampler.AudioResampler(format='s16', layout='mono', rate=44100)

    audio_frames = []

    for frame in container.decode(audio_stream):
        resampled_frames = resampler.resample(frame)

        if not isinstance(resampled_frames, list):
            resampled_frames = [resampled_frames]

        for resampled_frame in resampled_frames:
            samples = resampled_frame.to_ndarray()
            # Đảm bảo là mono
            if samples.ndim > 1:
                samples = samples.mean(axis=0).astype(np.int16)
            audio_frames.append(samples)

    audio_data = np.concatenate(audio_frames)
    sf.write(output_path, audio_data, 44100)

@app.route("/process-audio", methods=["POST"])
def process_audio():
    print(request)
    if "audio" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["audio"]
    filename = f"{uuid.uuid4().hex}.m4a"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    # # Chuyển file M4A thành WAV (do SpeechRecognition không hỗ trợ MP3)
    wav_path = os.path.join(UPLOAD_FOLDER, f"{uuid.uuid4().hex}.wav")
    convert_m4a_to_wav(filepath, wav_path)

    # # Dùng Google STT để chuyển thành văn bản (offline)
    recognizer = sr.Recognizer()
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            text = recognizer.recognize_google(audio_data, language="vi-VN")
        except sr.UnknownValueError:
            text = "Tôi không thể nghe thấy bạn! Vui lòng điều chỉnh micro và hỏi lại rõ ràng hơn!"
            # Chuyển văn bản thành giọng nói bằng gTTS
            ai_audio_path = os.path.join(PROCESSED_FOLDER, f"{uuid.uuid4().hex}.mp3")
            tts = gTTS(text, lang="vi")
            tts.save(ai_audio_path)

            return send_file(ai_audio_path, mimetype="audio/mp3", as_attachment=True)
        except sr.RequestError:
            text = "Dịch vụ giọng nói đã có vấn đề xảy ra! Vui lòng thử lại sau!"
            # Chuyển văn bản thành giọng nói bằng gTTS
            ai_audio_path = os.path.join(PROCESSED_FOLDER, f"{uuid.uuid4().hex}.mp3")
            tts = gTTS(text, lang="vi")
            tts.save(ai_audio_path)

            return send_file(ai_audio_path, mimetype="audio/mp3", as_attachment=True)

    
    
    payload = get_state()
    payload['question'] = text
    payload['model'] = MODEL_OPTION
    session['question'] = text
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            LLM_SERVER_URL.format("chat/get_response"), 
            json=payload, 
            headers=headers, 
            timeout=200
        )
        response.raise_for_status()     
        result = response.json()
        
        # Lấy dữ liệu an toàn
        response = result.get("response", "Đã có lỗi xảy ra!")
        state = result.get("state", "normal")
        unknown_question = result.get("unknown_question", [])
        phone_number = result.get("phone_number", "")
        url = result.get("url", [])
        speak = result.get("response_speak", "Đã có lỗi xảy ra!")
        url_dict = {}
        for i in range(0, len(url)):
            if url[i] != "Internet" and url[i] != "Tham khảo từ chuyên gia":
                url_dict[f'Tài liệu {i+1}'] = url[i]
                
        # Cập nhật Session
        session["state"] = state
        session["unknown_question"] = unknown_question
        session["phone_number"] = phone_number
        print(session)
    
    except requests.exceptions.RequestException as e:
        speak = "Có lỗi xảy ra! Không thể kết nối đến Server!"
        print(f"Lỗi khi gọi API: {e}")  # Debug lỗi
    
    
    # Chuyển văn bản thành giọng nói bằng gTTS
    ai_audio_path = os.path.join(PROCESSED_FOLDER, f"{uuid.uuid4().hex}.mp3")
    tts = gTTS(speak, lang="vi")
    tts.save(ai_audio_path)
    return send_file(ai_audio_path, mimetype="audio/mp3", as_attachment=True)

@app.route("/get-audio", methods=["POST"])
def get_audio():
    try:
        data = request.get_json()
        speak = data.get("text", "Xin chào, tôi là chát bót ai ti súp")
        ai_audio_path = os.path.join(PROCESSED_FOLDER, f"{uuid.uuid4().hex}.mp3")
        tts = gTTS(speak, lang="vi")
        tts.save(ai_audio_path)
        return send_file(ai_audio_path, mimetype="audio/mp3", as_attachment=True)
    except:
        return {"error": "No text provided"}, 400
        

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
