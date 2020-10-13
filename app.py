from flask import Flask, redirect, render_template, request
from MaplewoodScraper import MaplewoodScraper
import requests

username = ""
password = ""

app = Flask(__name__)

@app.route("/")
def index():
    return redirect("/signin")

@app.route("/loading", methods=["POST"])
def loading():
    global username
    global password
    username = request.form["inputUsername"]
    password = request.form["inputPassword"]
    return render_template("loading.html")

@app.route("/signin")
def signin():
    return render_template("signin.html")


@app.route("/marks")
def marks():
    # username = request.form["username"]
    # password = request.form["password"]
    scrape = MaplewoodScraper(username, password)
    scrape.start(notify=False)
    return render_template("index.html", courses=scrape.courses, aliases=scrape.aliases)


if __name__ == "__main__":
    app.run()


# TODO: highlight percentage/row when a mark is below a certain perctentage
# TODO: signin page
# TODO: show num assignments that are 100, mediocre and bad
# TODO: show course average
# TODO: deploy to heroku
# TODO: verify login by making a new method in class
# TODO: loading page
