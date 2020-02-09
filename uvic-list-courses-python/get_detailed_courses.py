import json
import requests
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
	url = "https://www.uvic.ca/home/tools/index.php"
	
	response = requests.get(url)
	page = BeautifulSoup(response.text, 'html.parser')

	for i in page.find_all('input'):
		if i['name'] == 'execution':
			return i['value']


def get_TGC(username, password, execution):
	url = "https://www.uvic.ca/cas/login"

	data = f"username={username}&password={password}&execution={execution}&_eventId=submit"
	headers = {'Content-Type': "application/x-www-form-urlencoded"}
	querystring = {"service":"https://www.uvic.ca/home/tools/index.php"}

	response = requests.request("POST", url, data=data, headers=headers, params=querystring, allow_redirects=False)
	return response.cookies.get("TGC")



def get_SESSID(TGC):
	url = "https://www.uvic.ca/cas/login"

	querystring = {"service":"https://www.uvic.ca/BAN1P/banuvic.gzcaslib.P_Service_Ticket?target=bwskflib.P_SelDefTerm"}
	headers = {'Cookie': f"TGC={TGC}"}
	response = requests.request("GET", url, headers=headers, params=querystring)

	return response.cookies.get("SESSID")


def get_detailed_courses(SESSID):
	url = "https://www.uvic.ca/BAN1P/bwskfshd.P_CrseSchdDetl"

	# TODO Allow user to select term
	data = "term_in=202001"
	headers = {
		'Content-Type': "application/x-www-form-urlencoded",
		'Cookie': f"SESSID={SESSID}"
	}
	response = requests.request("POST", url, data=data, headers=headers )

	return(response)


def read_course_values(page):
	course_dict = {}
	prev_course = None

	for t in page.select("table.datadisplaytable"):
		caption = t.select("caption.captiontext")[0].text
		#print(caption)

		# temporary dict to store our things
		course_values = {}

		if caption == "Scheduled Meeting Times":
			# If it's the schedule, set the name to the respective course
			caption = prev_course

			for row in t.select("tr")[1:]:
				v = row.select("td.dddefault")
				##print(caption + v[])

				# TODO Add support for multi-row schedules like ENGR 110 with plenary lectures

				# Match the schedule to your instructor and exclude midterm exams
				if ((
						course_dict[caption]["Instructor"] == "" and "TBA" in v[6].text \
						or course_dict[caption]["Instructor"] in ' '.join(v[6].text.split()) \
						or  ' '.join(course_dict[caption]["Instructor"].split()[0]) == ' '.join(v[6].text.split()[0])  \
						and ' '.join(course_dict[caption]["Instructor"].split()[2]) == ' '.join(v[6].text.split()[2]))  \
						and v[0].text.strip().lower() != "Midterm Exam".lower()
						):
					course_values["Type"]          = v[0].text.strip()
					course_values["Time"]          = v[1].text.strip()
					course_values["Days"]          = v[2].text.strip()
					course_values["Where"]         = v[3].text.strip()
					course_values["Date Range"]    = v[4].text.strip()
					course_values["Schedule Type"] = v[5].text.strip()
				#else:
				#	print("'{}' doesn't contain {}".format(v[6].text, course_dict[caption]['Instructor']))

			course_dict[caption].update(course_values)

			#course_dict[caption] = course_values
		else:
			v = t.select("td.dddefault")
			course_values["Term"]       = v[0].text.strip()
			course_values["CRN"]        = v[1].text.strip()
			course_values["Status"]     = v[2].text.strip()
			course_values["Instructor"] = v[3].text.strip().split(",")[0]
			course_values["Grade Mode"] = v[4].text.strip()
			course_values["Credits"]    = v[5].text.strip()
			course_values["Level"]      = v[6].text.strip()
			course_values["Campus"]     = v[7].text.strip()

			course_dict[caption] = course_values

		prev_course = caption

	return course_dict


def parse_course_dict(course_dict):
	parsed_dict = {}

	for course_name in course_dict:
		course = course_dict[course_name]
		parsed_course = {}
		
		parsed_course["title"]   = course_name.split(" - ")[0]
		parsed_course["code"]    = course_name.split(" - ")[1]
		parsed_course["section"] = course_name.split(" - ")[2]

		parsed_course["start_time"] = course["Time"].split(" - ")[0]
		parsed_course["end_time"]   = course["Time"].split(" - ")[1]

		parsed_course["start_date"] = course["Date Range"].split(" - ")[0]
		parsed_course["end_date"]   = course["Date Range"].split(" - ")[1]

		parsed_course["location"] = course["Where"]
		
		parsed_course["days"] = parse_days(course["Days"])

		# Append our parsed course, using the CRN as a key.
		parsed_dict[course["CRN"]] = parsed_course

	return parsed_dict

def parse_days(day_string):
	# This function lookS at the letters "MTWRFS" and converts them to weekdays
	# This won't support Sunday classes as I've never encountered them.
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


def create_ics(courses):
	cal = Calendar()
	for c in courses:
		course = courses[c]
		event = Event()

		# Time formatting is similar to unix "date" command
		start_time = datetime.strptime(f'{course["start_date"]} {course["start_time"]}', '%b %d, %Y %I:%M %p')
		end_time   = datetime.strptime(f'{course["start_date"]} {course["end_time"]  }', '%b %d, %Y %I:%M %p')
		end_date   = datetime.strptime(f'{course["end_date"]  } {course["end_time"]  }', '%b %d, %Y %I:%M %p')
		days = course["days"]

		event.add("summary", f"{course['code']} {course['section']}")

		event.add("dtstart", start_time)
		event.add("dtend", end_time)
		event.add("dtstamp", datetime.now())

		event.add("location", course["location"])

		event.add('rrule', vRecur({
			"freq": "WEEKLY",
			"interval": 1,
			"until": end_date,
			"byday": days
		}))
		
		cal.add_component(event)
	
	# TODO confirm file overwrite
	open("output.ics", "wb").write(cal.to_ical())


def fetch_page():
	print("Log in to UVic")
	username = input("Username: ") or "malcolmseyd"
	password = getpass("Password: ")

	execution = get_execution()
	#print(execution)
	TGC = get_TGC(username, password, execution)
	
	if (TGC == None):
		print("Error: Failed to log in.")
		exit(1)

	#print(TGC)
	SESSID = get_SESSID(TGC)
	#print(SESSID)

	detailed_courses = get_detailed_courses(SESSID)

	# print(json.dumps(detailed_courses.headers.__dict__, indent=4, sort_keys=True))

	page = BeautifulSoup(detailed_courses.content, 'html.parser')

	if CACHE_PAGE:
		open("page.html", "wb").write(detailed_courses.content)
	
	return page


def main():
	try:
		with open("page.html") as in_file:
			if CACHE_PAGE != True:
				remove("page.html")
				raise FileNotFoundError
			else:
				page = BeautifulSoup(in_file.read(), 'html.parser')
				in_file.close()
				
	except FileNotFoundError:
		page = fetch_page()	
		
	course_dict_raw = read_course_values(page)

	#print(json.dumps(course_dict_raw, indent=4, sort_keys=False))

	parsed_courses = parse_course_dict(course_dict_raw)

	#print(json.dumps(parsed_courses, indent=4, sort_keys=False))

	create_ics(parsed_courses)


if __name__ == "__main__":
	main()