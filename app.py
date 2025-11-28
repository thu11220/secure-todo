from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "CHANGE_ME_SECRET_KEY"   

DB_NAME = "database.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            password TEXT
        )
    """)
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            text TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("todo"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        
        hashed = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return "Email already exists"
        conn.close()
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ? AND password = ?",
        (email, password))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            return redirect(url_for("todo"))
        else:
            return "Invalid email or password"
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/todo", methods=["GET", "POST"])
def todo():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        text = request.form["text"]
        cur.execute("INSERT INTO todos (user_id, text) VALUES (?, ?)", (session["user_id"], text))
        conn.commit()

    cur.execute("SELECT * FROM todos WHERE user_id = ?", (session["user_id"],))
    todos = cur.fetchall()
    conn.close()
    return render_template("todo.html", todos=todos)


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM todos WHERE id = ? AND user_id = ?", (todo_id, session["user_id"]))
    conn.commit()
    conn.close()
    return redirect(url_for("todo"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)