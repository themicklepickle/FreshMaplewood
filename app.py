from flask import Flask, redirect, render_template, request, session
from MaplewoodScraper import MaplewoodScraper
import requests

app = Flask(__name__)
app.secret_key = "asdfkjh2i3u987ufiusjfdkjqwopr!@#$!@#%$#%@!#$!@#$%@!"

session["error"] = False


@app.route("/")
def index():
    return redirect("/signin")


@app.route("/loading", methods=["POST"])
def loading():
    session["username"] = request.form["inputUsername"]
    session["password"] = request.form["inputPassword"]
    return render_template("loading.html")


@app.route("/signin")
def signin():
    session["username"] = ""
    session["password"] = ""
    if session["error"]:
        return render_template("signin.html", error=True)
    return render_template("signin.html", error=False)


@app.route("/marks")
def marks():
    scrape = MaplewoodScraper(username, password)
    if scrape.start(notify=False):
        session["error"] = False
        return render_template("index.html", courses=scrape.courses, aliases=scrape.aliases)
    session["error"] = True
    return redirect("/signin")


if __name__ == "__main__":
    app.run()


# TODO: highlight percentage/row when a mark is below a certain perctentage
# TODO: show num assignments that are 100, mediocre and bad
# TODO: show course average
# TODO: deploy to heroku
# TODO: verify login by making a new method in class
# TODO: loading page
# TODO: photos and personal details
# TODO: dynamic modification of marks
