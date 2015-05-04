from flask import Flask, flash, session, request, url_for, render_template

app = Flask(__name__)

@app.route("/")
@app.route("/home", methods = ["POST", "GET"])
def home():
    return render_template("home.html")

@app.route("/messages", methods = ["POST", "GET"])
def messages():
    return render_template("messages.html")

@app.route("/walls", methods = ["POST", "GET"])
def walls():
    return render_template("walls.html")


if __name__=="__main__":
    app.debug = True
    app.run()
