from flask import Flask, render_template

app = Flask(__name__, template_folder="../public/templates")

@app.route("/")
def home():
    return render_template("index.html")

# Netlify Lambda requires a handler
def handler(event, context):
    from flask_lambda import FlaskLambda
    app_lambda = FlaskLambda(app)
    return app_lambda(event, context)