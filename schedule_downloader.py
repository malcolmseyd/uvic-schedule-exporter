import json
import requests
from datetime import date, datetime
from icalendar import Calendar, Event, vRecur
from datetime import datetime
from getpass import getpass
from bs4 import BeautifulSoup
from os import remove

"""
Your Netlink ID is never stored and is only sent to UVic's servers.
Please see the link below for documentation:
https://documenter.getpostman.com/view/9187076/SVtZwmUP
"""

# Cache page so that we're not spamming UVic's API while testing
CACHE_PAGE = False


# For these four get_XXXX() functions, see the documentation above

def get_execution():
    url = "https://www.uvic.ca/cas/login"

    response = requests.get(url)
    page = BeautifulSoup(response.text, 'html.parser')

    for i in page.find_all('input'):
        if i['name'] == 'execution':
            return i['value']


def get_TGC(username, password, execution):
    url = "https://www.uvic.ca/cas/login"

    data = f"username={username}&password={password}&execution={execution}&_eventId=submit"
    headers = {'Content-Type': "application/x-www-form-urlencoded"}
    querystring = {"service": "https://www.uvic.ca/home/tools/index.php"}

    response = requests.request(
        "POST", url, data=data, headers=headers, params=querystring, allow_redirects=False)
    return response.cookies.get("TGC")


def get_SESSID(TGC):
    url = "https://www.uvic.ca/cas/login"

    querystring = {
        "service": "https://www.uvic.ca/BAN1P/banuvic.gzcaslib.P_Service_Ticket?target=bwskflib.P_SelDefTerm"}
    headers = {'Cookie': f"TGC={TGC}"}
    response = requests.request(
        "GET", url, headers=headers, params=querystring)

    return response.cookies.get("SESSID")


def get_detailed_courses(SESSID, term):
    url = "https://www.uvic.ca/BAN1P/bwskfshd.P_CrseSchdDetl"

    data = f"term_in={term}"
    headers = {
        'Content-Type': "application/x-www-form-urlencoded",
        'Cookie': f"SESSID={SESSID}"
    }
    response = requests.request("POST", url, data=data, headers=headers)

    return(response)


# we parse (almost) everything for completeness but not all values are used.
def read_course_values(page):

    if "You are not currently registered for the term." in str(page):
        print("You're not registered for this term!")
        exit(1)

    course_dict = {}
    current_course = None

    for t in page.select("table.datadisplaytable"):
        caption = t.select("caption.captiontext")[0].text
        # print(caption)

        if caption == "Scheduled Meeting Times":
            scheduleArray = []

            for row in t.select("tr")[1:]:

                schedule = {}

                # all of the values are in this array
                fields = row.select("td.dddefault")

                schedule["Type"] = fields[0].text.strip()
                schedule["Time"] = fields[1].text.strip()
                schedule["Days"] = fields[2].text.strip()
                schedule["Where"] = fields[3].text.strip()
                schedule["Date Range"] = fields[4].text.strip()
                schedule["Schedule Type"] = fields[5].text.strip()
                # ignore instructors because we already have them

                scheduleArray.append(schedule)

            # finally update the dictionary
            course_dict[current_course]["Schedule"] = scheduleArray

        else:
            course_values = {}
            current_course = caption

            fields = t.select("td.dddefault")
            course_values["Term"] = fields[0].text.strip()
            course_values["CRN"] = fields[1].text.strip()
            course_values["Status"] = fields[2].text.strip()
            course_values["Instructors"] = fields[3].text.strip().split(",")
            course_values["Grade Mode"] = fields[4].text.strip()
            course_values["Credits"] = fields[5].text.strip()
            course_values["Level"] = fields[6].text.strip()
            course_values["Campus"] = fields[7].text.strip()

            # try removing empty profs
            try:
                course_values["Instructors"].remove("")
            except ValueError:
                pass

            for i in range(len(course_values["Instructors"])):
                course_values["Instructors"][i] = course_values["Instructors"][i].strip(
                )

            course_dict[current_course] = course_values

    return course_dict


def parse_course_dict(course_dict):
    parsed_dict = {}

    for course_name in course_dict:
        course = course_dict[course_name]
        parsed_course = {}

        parsed_course["title"] = course_name.split(" - ")[0]
        parsed_course["code"] = course_name.split(" - ")[1]
        parsed_course["section"] = course_name.split(" - ")[2]

        parsed_course["schedule"] = []

        for sched in course["Schedule"]:
            new_schedule = {}

            if sched["Time"] == "TBA":
                continue

            new_schedule["start_time"] = sched["Time"].split(" - ")[0]
            new_schedule["end_time"] = sched["Time"].split(" - ")[1]

            new_schedule["start_date"] = sched["Date Range"].split(" - ")[0]
            new_schedule["end_date"] = sched["Date Range"].split(" - ")[1]

            new_schedule["location"] = sched["Where"]

            new_schedule["days"] = days_to_ics(sched["Days"])

            parsed_course["schedule"].append(new_schedule)

        # Append our parsed course, using the CRN as a key.
        parsed_dict[course["CRN"]] = parsed_course

    return parsed_dict


def days_to_ics(day_string):
    # This function lookS at the letters "MTWRFS" and converts them to weekdays
    # This won't support Sunday classes as I've never encountered them.
    # I could probably do this as a map
    days = []
    for c in day_string:
        if c == "M":
            days.append("MO")
        elif c == "T":
            days.append("TU")
        elif c == "W":
            days.append("WE")
        elif c == "R":
            days.append("TH")
        elif c == "F":
            days.append("FR")
        elif c == "S":
            days.append("SA")
    return days


def ics_day_to_number(day):
    # all days, including sunday
    # i suppose this could be a dict, idk how performance compares though
    if day == "MO":
        return 0
    elif day == "TU":
        return 1
    elif day == "WE":
        return 2
    elif day == "TH":
        return 3
    elif day == "FR":
        return 4
    elif day == "SA":
        return 5
    elif day == "SU":
        return 6


def create_ics(courses, filename):
    # Unix "date" style format string for datetime importing
    # Example:
    #   "Jan 01, 2021 12:59 PM -0700"
    tformat = "%b %d, %Y %I:%M %p"

    cal = Calendar()
    for c in courses:
        course = courses[c]

        # create a new calender event for each lecture time (for classes like ENGR 120)
        for schedule in course["schedule"]:
            event = Event()

            # Time formatting is similar to unix "date" command
            start_time = datetime.strptime(
                f'{schedule["start_date"]} {schedule["start_time"]}', tformat)

            end_time = datetime.strptime(
                f'{schedule["start_date"]} {schedule["end_time"]}', tformat)

            end_date = datetime.strptime(
                f'{schedule["end_date"]  } {schedule["end_time"]}', tformat)

            days = schedule["days"]

            numeric_days = []
            for d in days:
                numeric_days.append(ics_day_to_number(d))

            # fix if the start date is not an included day
            while start_time.weekday() not in numeric_days:
                try:
                    start_time = start_time.replace(day=start_time.day+1)
                except ValueError:
                    if start_time.month == 12:
                        start_time = start_time.replace(
                            day=1, month=1, year=start_time.year+1)
                    else:
                        start_time = start_time.replace(
                            day=1, month=start_time.month+1)
            else:
                # update end time accordingly
                end_time = datetime.combine(
                    date=start_time.date(), time=end_time.time())

            event.add("summary", f"{course['code']} {course['section']}")

            event.add("dtstart", start_time, parameters={
                      'TZID': 'America/Vancouver'})
            event.add("dtend", end_time, parameters={
                      'TZID': 'America/Vancouver'})
            event.add("dtstamp", datetime.now())

            event.add("location", schedule["location"])

            event.add('rrule', vRecur({
                "freq": "WEEKLY",
                "interval": 1,
                "until": end_date,
                "byday": days
            }))

            cal.add_component(event)

    with open(f"{filename}.ics", "wb") as f:
        f.write(cal.to_ical())


def getTerm():
    terms = {
        1: "Spring",
        5: "Summer",
        9: "Fall"
    }

    today = date.today()
    thisYear = today.year
    thisMonth = today.month
    # restrict to 1, 5, 9
    thisTerm = ((thisMonth - 1) // 4 * 4) + 1

    year = input(f"Year [{thisYear}]: ")
    if year == '':
        year = thisYear

    term = input(f"Term [{terms[thisTerm]}]: ")
    if term == '':
        term = terms[thisTerm]

    if term[0:2].lower() == "sp":
        return f"{year}01"
    elif term[0:2].lower() == "su":
        return f"{year}05"
    elif term[0].lower() == "f":
        return f"{year}09"
    else:
        print("Invalid term. Options are (sp)ring, (su)mmer, (f)all")
        exit(1)


def fetch_page():
    try:
        term = getTerm()
        print("Log in to UVic")
        username = input("Username: ")
        password = getpass("Password: ")
    except KeyboardInterrupt:
        print("\nQuitting.")
        exit(0)

    print("Downloading...")

    execution = get_execution()
    # print(execution)
    TGC = get_TGC(username, password, execution)

    if (TGC == None):
        print("Error: Failed to log in.")
        exit(1)

    # print(TGC)
    SESSID = get_SESSID(TGC)
    # print(SESSID)

    detailed_courses = get_detailed_courses(SESSID, term)

    # print(json.dumps(detailed_courses.headers.__dict__, indent=4, sort_keys=True))

    page = BeautifulSoup(detailed_courses.content, 'html.parser')

    if CACHE_PAGE:
        open("page.html", "wb").write(detailed_courses.content)

    return (page, term)


def main():
    try:
        with open("page.html") as in_file:
            if CACHE_PAGE != True:
                remove("page.html")
                raise FileNotFoundError
            else:
                page = BeautifulSoup(in_file.read(), 'html.parser')
                in_file.close()
        term = "testing"

    except FileNotFoundError:
        page, term = fetch_page()

    print("Parsing...")
    course_dict_raw = read_course_values(page)

    if course_dict_raw == {}:
        print("Error fetching course data")

    # print(json.dumps(course_dict_raw, indent=4, sort_keys=False))

    parsed_courses = parse_course_dict(course_dict_raw)

    # print(json.dumps(parsed_courses, indent=4, sort_keys=False))

    filename = "schedule"
    create_ics(parsed_courses, f"{filename}-{term}")

    print(f"Done. Wrote to {filename}-{term}.ics")


if __name__ == "__main__":
    main()
