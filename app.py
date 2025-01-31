from flask import Flask, render_template
import os
app = Flask(__name__, template_folder='templates')

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/register')
def register():
    return render_template('register/register.html')

@app.route('/forgotpassword/forgot-password')
def forgot_password():
    return render_template('forgotpassword/forgot-password.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Netlify assigns a port dynamically
    app.run(host="0.0.0.0", port=port)