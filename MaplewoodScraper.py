import requests
from bs4 import BeautifulSoup
import dateparser
from datetime import datetime
import pytz
import json


class MaplewoodScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password

        self.mainPage = None
        self.markPages = []
        self.allMarks = []
        self.courses = []
        self.activeCourses = []
        self.inactiveCourses = []
        self.programmingCourses = []
        self.roboticsCourses = []
        self.coursesOld = None
        self.additions = None
        self.removals = None
        self.markChanges = None
        self.formattedChanges = ""
        self.GPA = None
        self.waterlooGPA = None
        self.comments = []

        self.aliases = {
            "English Language Arts 20-1 (AP Lang.)": "English 20 AP Lang.",
            "Mathematics 30-1 Pre-AP": "Math 30 Pre-AP",
            "Physics 20 AP": "Physics 20 AP",
            "Applied Science Project": "Applied Science Project",
            "Social Studies 20-1": "GH 20",
            "Chemistry 20": "Chemistry 20",
            "CAD1": "CAD 1",
            "Electro Assembly 1": "Electro Assembly 1",
            "Robotics applications": "Robotics Applications",
            "Introductory Robotics": "Introductory Robotics",
            "Computer Programming 25": "Programming 25",
            "Computer Science 2": "Computer Science 2",
            "Files & File Structures 1": "File Structures 1",
            "Second Language Programming 1": "C++ Language",
            "Iterative Algorithms 1": "Algorithms 1",
            "Object­oriented Programming 1": "OOP 1"
        }
        self.mwURL = "https://hosting.maplewood.com/AB/Private/WA/WA/Maplewood"
        self.programmingCourseNames = [
            "Computer Science 2",
            "Files & File Structures 1",
            "Second Language Programming 1",
            "Iterative Algorithms 1",
            "Object­oriented Programming 1",
            "Computer Programming 25"
        ]
        self.roboticsCourseNames = [
            "CAD1",
            "Electro Assembly 1",
            "Robotics applications",
            "Introductory Robotics"
        ]

    def start(self, notify=True, test=False):
        if test:
            with open("test.json", "r") as f:
                self.courses = json.load(f)
                self.sortCourses()
                self.calculateGPA()
                self.getTodayUpdates()
            return True
        self.startSession()
        if not self.login():
            return False
        self.getMainPage()
        self.getCourses()
        self.getMarkPages()
        self.addMarkDetails()
        self.parseMarks()
        self.sortCourses()
        self.calculateGPA()
        if self.username.lower() == "xu3628":
            self.calculatewaterlooGPA()
        self.getTodayUpdates()
        return True

    def startSession(self):
        self.session = requests.Session()
        self.session.get(
            self.mwURL+"/connectEd/viewer/login/login.aspx?logintype=S"
        )

    def login(self):
        userInfo = f"EntryType=StudentParent&username={self.username}&pwd={self.password}"
        response = self.session.post(
            self.mwURL+"/connectEd/viewer/login/VerUser.aspx",
            data=userInfo,
            headers={"Content-type": "application/x-www-form-urlencoded"}
        )
        return True if response.history[0].headers.get('location').endswith('SvrMsg.aspx') else False

    def getMainPage(self):
        self.mainPage = self.session.get(
            self.mwURL + "/connectEd/viewer/Viewer/main.aspx"
        ).text

    def getCourses(self):
        mainPage = BeautifulSoup(self.mainPage, features="lxml")
        table = str(mainPage.find(id="TableSecondaryClasses"))
        table = BeautifulSoup(table, features="lxml")
        courseList = [str(c) for c in table.find_all("tr")[3:]]

        for course in courseList:
            course = BeautifulSoup(course, features="lxml")
            cols = [str(col.string) for col in course.find_all("td")]
            markbook = course.find("a")
            if markbook:
                attributes = markbook.attrs["onclick"][13:-2].split(",")
            else:
                attributes = None

            self.courses.append(
                {
                    "code": "".join(cols[0].split(" - ")[0].split(" ")),
                    "name": cols[0].split(" - ")[1],
                    "teacher": cols[1],
                    "updated": cols[2] if cols[2] != "n.a." else None,
                    "absent": int(cols[3]) if cols[3] != "NA" else None,
                    "excused": int(cols[4]) if cols[3] != "NA" else None,
                    "late": int(cols[5]) if cols[3] != "NA" else None,
                    "studentID": int(attributes[0]) if markbook else None,
                    "classID": int(attributes[1]) if markbook else None,
                    "termID": int(attributes[2]) if markbook else None,
                    "topicID": int(attributes[3]) if markbook else None,
                    "active": True if cols[2] != "n.a." else False,
                    "units": []
                }
            )
        for course in self.courses:
            if course["active"]:
                self.activeCourses.append(course)

    def getMarkPages(self):
        for course in self.courses:
            if course in self.activeCourses:
                courseInfo = {
                    "studentID": course["studentID"],
                    "classID": course["classID"],
                    "termID": course["termID"],
                    "topicID": course["topicID"],
                    "fromDate": "1/1/2000",
                    "toDate": "1/1/3000",
                    "relPath": "../../../",
                    "stuLetters": "",
                    "orgID": -1
                }
                markPage = self.session.post(
                    self.mwURL+"/connectEd/viewer/Achieve/TopicBas/StuMrks.aspx/GetMarkbook",
                    json=courseInfo
                ).json()["d"]
                self.markPages.append(BeautifulSoup(markPage, features="lxml"))
            else:
                self.markPages.append(None)

    def addMarkDetails(self):
        for i, markPage in enumerate(self.markPages):
            if markPage:
                termMark = markPage.find(
                    "div", attrs={"style": "font-weight: bold; margin-bottom: 3px;"}).string[11:]
                self.courses[i]["mark"] = float(
                    termMark) if termMark != " " else None
            else:
                self.courses[i]["mark"] = None

            if markPage:
                rows = markPage.find_all("tr")

                course = []
                for row in rows:
                    splitRows = [str(col.string) for col in row.find_all("td")]
                    commentLink = row.find("img", attrs={
                                           "onclick": "loadComment($(this).attr('commid'), $(this).attr('commtitle'), true);"
                                           })
                    if commentLink:
                        commentInfo = {
                            "commentID": commentLink.attrs["commid"],
                            "isMarkbook": True
                        }
                        commentContent = self.session.post(
                            self.mwURL+"/connectEd/viewer/Achieve/TopicBas/StuMrks.aspx/GetComment",
                            json=commentInfo
                        ).json()["d"]
                        comment = {
                            "commentID": commentLink.attrs["commid"],
                            "commentTitle": commentLink.attrs["commtitle"],
                            "commentContent": commentContent
                        }
                        splitRows.append(comment)
                        self.comments.append(comment)
                    else:
                        splitRows.append(None)
                    rowName = row.find("span")
                    if rowName:
                        splitRows[0] = str(rowName.string)
                        style = rowName.attrs["style"]
                        if style == "margin-left: 0px":
                            splitRows.append("unit")
                        elif style == "margin-left: 20px":
                            splitRows.append("section")
                        elif style == "margin-left: 40px":
                            splitRows.append("assignment")
                    else:
                        splitRows.append("header")
                    course.append(splitRows)
                self.allMarks.append(course)
            else:
                self.allMarks.append([])

    def newUnit(self, course, row):
        unit = {
            "name": row[0],
            "denominator": float(row[4]) if row[4] != "None" else None,
            "weight": float(row[3]) if row[3] != "None" else None,
            "comment": row[5],
            "course": course["name"],
            "has sections": False,
            "assignments": [],
            "sections": [],
            "updated today": False
        }
        if row[1] == "None":
            unit["mark"] = None
        elif row[1] == "EXC" or row[1] == "NHI" or row[1] == "ABS":
            unit["mark"] = row[1]
        else:
            unit["mark"] = float(row[1])
        return unit

    def newSection(self, course, unit, row):
        section = {
            "name": row[0],
            "denominator": float(row[4]) if row[4] != "None" else None,
            "weight": float(row[3]) if row[3] != "None" else None,
            "comment": row[5],
            "course": course["name"],
            "unit": unit["name"],
            "assignments": [],
            "updated today": False
        }
        if row[1] == "None":
            section["mark"] = None
        elif row[1] == "EXC" or row[1] == "NHI" or row[1] == "ABS":
            section["mark"] = row[1]
        else:
            section["mark"] = float(row[1])
        return section

    def newAssignment(self, course, unit, row):
        assignment = {
            "name": row[0],
            "denominator": float(row[4]) if row[4] != "None" else None,
            "weight": float(row[3]) if row[3] != "None" else None,
            "comment": row[5],
            "date": row[2],
            "course": course["name"],
            "unit": unit["name"],
            "updated today": False
        }
        if row[1] == "None":
            assignment["mark"] = None
        elif row[1] == "EXC" or row[1] == "NHI" or row[1] == "ABS":
            assignment["mark"] = row[1]
        else:
            assignment["mark"] = float(row[1])
        return assignment

    def parseMarks(self):
        section = None
        assignment = None
        for course, marks in zip(self.courses, self.allMarks):
            if course["active"]:
                row = marks[1]
                unit = self.newUnit(course, row)
                last = "unit"

                for row in marks[2:]:
                    if row[-1] == "unit":
                        if last == "unit":
                            course["units"].append(unit)
                        if last == "section":
                            unit["sections"].append(section)
                            course["units"].append(unit)
                        if last == "assignment" and unit["has sections"]:
                            section["assignments"].append(assignment)
                            unit["sections"].append(section)
                            course["units"].append(unit)
                        elif last == "assignment":
                            unit["assignments"].append(assignment)
                            course["units"].append(unit)
                        unit = self.newUnit(course, row)
                        last = "unit"

                    if row[-1] == "section":
                        if last == "unit":
                            unit["has sections"] = True
                        if last == "section":
                            unit["sections"].append(section)
                        if last == "assignment":
                            section["assignments"].append(assignment)
                            unit["sections"].append(section)
                        section = self.newSection(course, unit, row)
                        last = "section"

                    if row[-1] == "assignment":
                        if last == "unit":
                            pass
                        if last == "section":
                            pass
                        if last == "assignment" and unit["has sections"]:
                            section["assignments"].append(assignment)
                        elif last == "assignment":
                            unit["assignments"].append(assignment)
                        assignment = self.newAssignment(course, unit, row)
                        if unit["has sections"]:
                            assignment["section"] = section["name"]
                        last = "assignment"

                if last == "unit":
                    course["units"].append(unit)
                if last == "section":
                    unit["sections"].append(section)
                    course["units"].append(unit)
                if last == "assignment" and unit["has sections"]:
                    section["assignments"].append(assignment)
                    unit["sections"].append(section)
                    course["units"].append(unit)
                elif last == "assignment":
                    unit["assignments"].append(assignment)
                    course["units"].append(unit)

    def compActive(self):
        pass

    def sortCourses(self):
        for course in [course for course in self.courses if course["name"] in self.programmingCourseNames]:
            self.courses.remove(course)
            if course["active"]:
                self.programmingCourses.insert(0, course)
            else:
                self.programmingCourses.append(course)

        for course in [course for course in self.courses if course["name"] in self.roboticsCourseNames]:
            self.courses.remove(course)
            if course["active"]:
                self.roboticsCourses.insert(0, course)
            else:
                self.roboticsCourses.append(course)

        self.inactiveCourses = [
            course for course in self.courses if not course["active"]]
        for course in self.inactiveCourses:
            self.courses.remove(course)

        self.courses += self.programmingCourses + \
            self.roboticsCourses + self.inactiveCourses

    def calculateGPA(self):
        marks = []
        programmingMarks = []
        roboticsMarks = []
        for course in self.courses:
            if course["mark"]:
                if course["name"] in self.programmingCourseNames:
                    programmingMarks.append(course["mark"])
                elif course["name"] in self.roboticsCourseNames:
                    roboticsMarks.append(course["mark"])
                else:
                    marks.append(course["mark"])
        if len(programmingMarks) > 0:
            marks.append(sum(programmingMarks) / len(programmingMarks))
        if len(roboticsMarks) > 0:
            marks.append(sum(roboticsMarks) / len(roboticsMarks))
        self.GPA = sum(marks) / len(marks)

    def calculatewaterlooGPA(self):
        waterlooSECourses = [
            "English Language Arts 20-1 (AP Lang.)",
            "Mathematics 30-1 Pre-AP",
            "Physics 20 AP",
            "Chemistry 20"
        ]
        marks = [course["mark"] for course in self.courses if course["mark"]
                 and course["name"] in waterlooSECourses]
        self.waterlooGPA = sum(marks) / len(marks)

    def getTodayUpdates(self):
        dateToday = str(datetime.now(
            pytz.timezone("America/Denver"))).split()[0]
        for course in self.courses:
            if not course["updated"]:
                continue
            dateUpdated = str(dateparser.parse(course["updated"])).split()[0]
            if dateUpdated != dateToday:
                continue
            course["updated today"] = True
            for unit in course["units"]:
                if unit["has sections"]:
                    for section in unit["sections"]:
                        for assignment in section["assignments"]:
                            dateUpdated = str(dateparser.parse(
                                assignment["date"])).split()[0]
                            if dateUpdated == dateToday:
                                assignment["updated today"] = True
                                section["updated today"] = True
                                unit["updated today"] = True
                else:
                    for assignment in unit["assignments"]:
                        dateUpdated = str(dateparser.parse(
                            assignment["date"])).split()[0]
                        if dateUpdated == dateToday:
                            assignment["updated today"] = True
                            unit["updated today"] = True


if __name__ == "__main__":
    username = "xu3628"  # input("Username: ")
    password = "Lego1211"  # input("Password: ")
    scraper = MaplewoodScraper(username, password)
    scraper.start()
