# >>> Import Libraries
from flask import (
    Flask, 
    redirect, 
    render_template,
    url_for,
    request,
    flash,
    jsonify,
    session
)
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from flask_session import Session
import requests

# >>> URL
# LLM_SERVER_URL = "http://127.0.0.1:5005/{}"
LLM_SERVER_URL = "https://af6d-34-74-192-43.ngrok-free.app/{}"


# >>> Initialize Flask App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'IT-Sup'

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"
Session(app) # Initialize Flask-Session


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False)

# >>> User Loader
@login_manager.user_loader
def loader_user(user_id):
    return User.query.get(user_id)

# >>> Home
# Route
@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    return render_template('home.html')

# >>> Introduction
# Route
@app.route('/introduction')
def introduction():
    return render_template('introduction.html')

# >>> Chatbot
# Get state
def get_state():
    if not session.get("question"):
        session["question"] = "Xin chào"
    if not session.get("state"):
        session["state"] = "normal"
    if not session.get("top_k"):
        session["top_k"] = 3
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
    
# Check connect function
def check_server(url, name):
    try:
        response = requests.get(url.format('check_connection'))
        # print(name,"Server:",response.json())
        if response.status_code == 200:
            print(f"✅ {name} Server is running!")
            return True
        else:
            print(f"⚠️ {name} Server responded with status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"❌ {name} Server is NOT running!")
    return False

# Route
@app.route('/chatbot')
def chatbot():
    return render_template('chatbot.html')

@app.route('/chatbot/qwen')
def chatbot_qwen():
    return render_template('chatbot-qwen.html')

@app.route('/chatbot/gemini')
def chatbot_gemini():
    return render_template('chatbot-gemini.html')

@app.route('/chatbot/qwen/get_response', methods=['GET', 'POST'])
def mistral_get_response():
    msg = request.form.get("msg", "")
    
    # Check connection
    if not check_server(LLM_SERVER_URL, "Qwen 2.5"):
        return jsonify(answer = "Không có kết nối đến Server!", url_dict = {}, speak="Đã có lỗi hệ thống xảy ra")
        
    # Connect LLM backend
    payload = get_state()
    payload['question'] = msg
    payload['model'] = 'qwen'
    session['question'] = msg
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
        source = result.get("source", [])
        speak = result.get("response_speak", "Đã có lỗi xảy ra!")
        url_dict = {}
        for i in range(0, min(len(url), len(source))):
            url_dict[source[i]] = url[i]
        
        # Cập nhật Session
        session["state"] = state
        session["unknown_question"] = unknown_question
        session["phone_number"] = phone_number
        print(session)

        return jsonify(answer=response, url_dict=url_dict, speak=speak) 

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")  # Debug lỗi
        return jsonify(answer="Đã có lỗi hệ thống xảy ra", url_dict={}, speak="Đã có lỗi hệ thống xảy ra") 
    
@app.route('/chatbot/gemini/get_response', methods=['GET', 'POST'])
def gemini_get_response():
    msg = request.form.get("msg", "")
    
    # Check connection
    if not check_server(LLM_SERVER_URL, "Gemini"):
        return jsonify(answer = "Không có kết nối đến Server!", url_dict = {}, speak="Đã có lỗi hệ thống xảy ra")
    
    # Connect LLM backend
    payload = get_state()
    payload['question'] = msg
    payload['model'] = 'gemini'
    session['question'] = msg
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
        source = result.get("source", [])
        speak = result.get("response_speak", "Đã có lỗi xảy ra!")
        url_dict = {}
        for i in range(0, min(len(url), len(source))):
            url_dict[source[i]] = url[i]
        
        # Cập nhật Session
        session["state"] = state
        session["unknown_question"] = unknown_question
        session["phone_number"] = phone_number
        print(session)
        return jsonify(answer=response, url_dict=url_dict, speak=speak) 

    except requests.exceptions.RequestException as e:
        print(f"Lỗi khi gọi API: {e}")  # Debug lỗi
        return jsonify(answer="Đã có lỗi hệ thống xảy ra", url_dict={}, speak="Đã có lỗi hệ thống xảy ra") 

# >>> Login
# Route
@app.route('/login', methods=["GET", "POST"])
def login():
    # If a post request was made, find the user by 
    # filtering for the username
    if request.method == "POST":
        user = User.query.filter_by(
            email=request.form.get("email")).first()
        if user is None:
            flash("Email không tồn tại!", "danger")
        # Check if the password entered is the 
        # same as the user's password
        elif user.password == request.form.get("password"):
            # Use the login_user method to log in the user
            login_user(user)
            return redirect(url_for("admin"))
        # Redirect the user back to the home
        # (we'll create the home route in a moment)
        else:
            flash("Mật khẩu không chính xác!", "danger")
    return render_template("login.html")

# >>> Logout
@app.route("/admin/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))

# >>> Admin Home
@app.route("/admin")
@login_required
def admin():
    if current_user.is_authenticated:
        return render_template("admin-home.html")
    else: 
        return redirect(url_for("home"))

# >>> Admin Question
def get_unknown_question():
    try:
        response = requests.get(LLM_SERVER_URL.format('manager/get_unknown_question'))
        if response.status_code == 200:
            print("✅  Server is running!")
            unknown_question = response.json()
            return unknown_question
        else:
            print(f"⚠️  Server responded with status code: {response.status_code}")
            unknown_question = {}
    except requests.exceptions.ConnectionError:
        print("❌  Server is NOT running!")
        unknown_question = {}
    return unknown_question

@app.route('/admin/submit_answer', methods=['POST'])
def submit_answer():
    try:
        question = request.form.get('question')
        answer = request.form.get('answer')

        headers = {
            'Content-Type': 'application/json',  # Chỉ định kiểu nội dung là JSON
        }
        
        payload = {
            "question": question,
            "answer": answer
        }

        response = requests.post(LLM_SERVER_URL.format("manager/update_unknown_question_state"), headers=headers, json=payload)
        print(response.json())
        if response.status_code == 200:
            return jsonify({"status": "success", "message": "Gửi thành công!"})
        else:
            status = response.json()
            return jsonify({"status": "error", "message": status['error']})
    except:
        return jsonify({"status": "error", "message": "Không kết nối được đến máy chủ"})

@app.route("/admin/question")
@login_required
def admin_question():
    if current_user.is_authenticated:
        unknown_question = get_unknown_question()
        return render_template("admin-question.html", unknown_question=unknown_question)
    else: 
        return redirect(url_for("home"))
    
    
# Admin Docs
    
# @app.route("/admin/docs")
# @login_required
# def admin_docs():
#     if current_user.is_authenticated:
#         return render_template("admin-docs.html")
#     else: 
#         return redirect(url_for("home"))

# Admin History SMS
def get_history_sms():
    try:
        response = requests.get(LLM_SERVER_URL.format('manager/get_history_sms'))
        if response.status_code == 200:
            print("✅  Server is running!")
            history_sms = response.json()
        else:
            print(f"⚠️  Server responded with status code: {response.status_code}")
            history_sms = {}
    except requests.exceptions.ConnectionError:
        print("❌  Server is NOT running!")
        history_sms = {}
    return history_sms
    
@app.route("/admin/historysms")
@login_required
def admin_historysms():
    if current_user.is_authenticated:
        history_sms = get_history_sms()
        return render_template("admin-historysms.html", history_sms=history_sms)
    else: 
        return redirect(url_for("home"))

# # >>> Register
# @app.route('/register', methods=["GET", "POST"])
# def register():
#     if request.method == "POST":
#         fullname = request.form.get("fullname")
#         email = request.form.get("email")
#         password = request.form.get("password")

#         # Kiểm tra xem người dùng đã nhập đầy đủ thông tin chưa
#         if not fullname or not email or not password:
#             flash("Vui lòng nhập đầy đủ thông tin!", "danger")
#             return redirect(url_for("register"))

#         # Kiểm tra xem email đã tồn tại chưa
#         existing_user = User.query.filter_by(email=email).first()
#         if existing_user:
#             flash("Email đã được sử dụng!", "danger")
#             return redirect(url_for("register"))

#         # Kiểm tra độ dài mật khẩu
#         if len(password) < 6:
#             flash("Mật khẩu phải có ít nhất 6 ký tự!", "danger")
#             return redirect(url_for("register"))

#         # Tạo người dùng mới
#         user = User(fullname=fullname, email=email, password=password, role="student")
#         db.session.add(user)
#         db.session.commit()

#         flash("Đăng ký thành công! Vui lòng đăng nhập.", "success")
#         return redirect(url_for("login"))

#     return render_template("register.html")

# >>> Run App
if __name__ == '__main__':
    app.run(debug=True, port=5001)