from flask import Flask, redirect, render_template
from MaplewoodScraper import MaplewoodScraper

with open("loginInfo.txt") as f:
        username, password = [line.strip() for line in f.readlines()]
scrape = MaplewoodScraper(
    username=username,
    password=password
)
scrape.start(notify=False)

app = Flask(__name__)

@app.route("/")
def index():
    # return render_template("index.html")
    return render_template("index.html", courses=scrape.courses, aliases=scrape.aliases)

if __name__ == "__main__":
    app.run()


# TODO: highlight percentage/row when a mark is below a certain perctentage
# TODO: login page
# TODO: show num assignments that are 100, mediocre and bad
# TODO: show course average
# TODO: deploy to heroku
