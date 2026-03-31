from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "supersecretkey"

# --- Database setup ---
def init_db():
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT,
                    receiver TEXT,
                    content TEXT)""")
    conn.commit()
    conn.close()

init_db()

# --- Routes ---
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("chat"))
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        conn = sqlite3.connect("chat.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
        except:
            return "Username already exists!"
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("chat.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session["user"] = username
            return redirect(url_for("chat"))
        return "Invalid credentials!"
    return render_template("login.html")

@app.route("/chat")
def chat():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("chat.html", user=session["user"])

@app.route("/send", methods=["POST"])
def send():
    if "user" not in session:
        return "Unauthorized", 403
    receiver = request.form["receiver"]
    content = request.form["content"]
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, content) VALUES (?, ?, ?)",
              (session["user"], receiver, content))
    conn.commit()
    conn.close()
    return "Message sent!"

@app.route("/messages/<receiver>")
def messages(receiver):
    if "user" not in session:
        return "Unauthorized", 403
    conn = sqlite3.connect("chat.db")
    c = conn.cursor()
    c.execute("SELECT sender, content FROM messages WHERE receiver=? ORDER BY id DESC", (receiver,))
    msgs = c.fetchall()
    conn.close()
    return jsonify(msgs)

if __name__ == "__main__":
    app.run(debug=True)