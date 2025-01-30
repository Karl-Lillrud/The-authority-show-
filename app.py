from flask import Flask, render_template

app = Flask(__name__, template_folder='templates')

app.route('/')
def index():
    return render_template('index.html')

app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)