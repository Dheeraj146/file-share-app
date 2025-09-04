import os
import sqlite3
import datetime
from flask import Flask, request, render_template, send_from_directory

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Database setup
def init_db():
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS files (
                 code TEXT PRIMARY KEY,
                 filename TEXT,
                 expiry TEXT)""")
    conn.commit()
    conn.close()

init_db()

# Home Page (index.html with Upload/Download tabs)
@app.route("/")
def home():
    return render_template("index.html")

# Upload route
@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files or request.files["file"].filename == "":
        return "❌ No file selected!"

    file = request.files["file"]
    code = request.form["code"].strip()

    if not code:
        return "❌ Code is required!"

    # Save file
    filename = file.filename
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Expiry = 24 hours
    expiry = datetime.datetime.now() + datetime.timedelta(hours=24)

    # Save metadata
    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("REPLACE INTO files (code, filename, expiry) VALUES (?, ?, ?)",
              (code, filename, expiry.isoformat()))
    conn.commit()
    conn.close()

    return f"""
    <div style="text-align:center; margin-top:50px; font-family:Arial;">
        <h2>✅ File Uploaded Successfully!</h2>
        <p>Your file is locked with the code:</p>
        <h1 style="color:blue;">{code}</h1>
        <p>Expiry: 24 hours</p>
        <p>Share this code with the recipient.<br>
        They can unlock the file using the <a href='/'>Access Page</a>.</p>
    </div>
    """

# Download route
@app.route("/download", methods=["POST"])
def download():
    code = request.form["code"].strip()

    conn = sqlite3.connect("files.db")
    c = conn.cursor()
    c.execute("SELECT filename, expiry FROM files WHERE code=?", (code,))
    row = c.fetchone()
    conn.close()

    if row:
        filename, expiry = row
        expiry = datetime.datetime.fromisoformat(expiry)

        if datetime.datetime.now() > expiry:
            return "❌ This file has expired!"

        return send_from_directory(app.config["UPLOAD_FOLDER"], filename, as_attachment=True)
    else:
        return "❌ Invalid code!"

if __name__ == "__main__":
    # host=0.0.0.0 makes it accessible on LAN/WAN
    app.run(host="0.0.0.0", port=5000, debug=True)
