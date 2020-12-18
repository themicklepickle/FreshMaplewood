from flask import Flask, redirect, render_template, request, session, escape
from MaplewoodScraper import MaplewoodScraper
import requests

app = Flask(__name__)
app.secret_key = "asdfkjh2i3u98@#%$#%@!#7ufiusjfdkjqwopr!@#$!$!@#$%@!"


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
    return render_template(
        "signin.html",
        error=True if "error" in session else False,
        errorMessage=session["errorMessage"] if "errorMessage" in session else ""
    )


@app.route("/marks")
def marks():
    scrape = MaplewoodScraper(session["username"], session["password"])
    if scrape.start(test=1):
        if "error" in session:
            session.pop("error")
            session.pop("errorMessage")
        return render_template(
            "index.html",
            courses=scrape.courses,
            aliases=scrape.aliases,
            GPA=scrape.GPA,
            waterlooGPA=scrape.waterlooGPA,
            courseCodes=scrape.courseCodes
        )
    session["error"] = True
    session["errorMessage"] = scrape.errorMessage
    return redirect("/signin")


if __name__ == "__main__":
    app.run()


# TODO: highlight percentage/row when a mark is below a certain perctentage
# TODO: show num assignments that are 100, mediocre and bad
# TODO: photos and personal details
# TODO: dynamic modification of marks
