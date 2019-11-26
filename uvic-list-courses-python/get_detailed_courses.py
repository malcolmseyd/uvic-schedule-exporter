import json
import requests
from getpass import getpass
from bs4 import BeautifulSoup

"""
"What the heck is this, you want my Netlink ID?!"
Please see the link below for documentation:
https://documenter.getpostman.com/view/9187076/SVtZwmUP
"""

#main_session = requests.session()

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

				# If the instructor is TBA, or if it is your instructor, or if there is some
				# strange middle-name business check the first and last names
				# This data is un-parsed so we have some inconsistencies to account for
				if (course_dict[caption]["Instructor"] == "" and "TBA" in v[6].text \
						#or course_dict[caption]["Instructor"] in ' '.join(v[6].text.split()) \
						or  ' '.join(course_dict[caption]["Instructor"].split()[0]) == ' '.join(v[6].text.split()[0]) \
						and ' '.join(course_dict[caption]["Instructor"].split()[2]) == ' '.join(v[6].text.split()[2]) \
						):
					course_values["Type"]          = v[0].text.strip()
					course_values["Time"]          = v[1].text.strip()
					course_values["Days"]          = v[2].text.strip()
					course_values["Where"]         = v[3].text.strip()
					course_values["Data Range"]    = v[4].text.strip()
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

def main():
	print("Log in to UVic")
	username = input("Username: ")
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

	#print(json.dumps(detailed_courses.headers.__dict__, indent=4, sort_keys=True))

	page = BeautifulSoup(detailed_courses.content, 'html.parser')

	#print(page.prettify())

	"""
	f=open("page.html", "w")
	f.write(page.prettify())
	f.close()
	"""

	course_dict_raw = read_course_values(page)

	print(json.dumps(course_dict_raw, indent=4, sort_keys=False))

	# TODO Parse the json and get useable values

if __name__ == "__main__":
	main()