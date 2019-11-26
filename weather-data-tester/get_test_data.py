import http.client, urllib3, os
from bs4 import BeautifulSoup
from getpass import getpass
from pathlib import Path

""" 
No, I'm not trying to steal your NetLink ID. 
For more info, read here:
https://documenter.getpostman.com/view/9187076/SW7W7W9D
"""


def get_session(username, password):
	conn = http.client.HTTPSConnection("connex.csc.uvic.ca")
	
	# create format login info
	form_data = urllib3.request.urlencode({
		'eid': username,
		'pw': password,
		'submit': "Log+In"
	})
	headers = {'Content-Type': "application/x-www-form-urlencoded"}

	conn.request("POST", "/portal/relogin", body=form_data, headers=headers)
	
	# get the response and extract the header
	res = conn.getresponse()
	cookies = res.getheader("Set-Cookie")
	
	# search the header for our cookie
	cookie_start = cookies.index("JSESSIONID=") + len("JSESSIONID=")
	cookie_end = cookies.index(";")

	# got it!
	session_id = cookies[cookie_start:cookie_end]

	return session_id


def get_test_urls(session_id):
	conn = http.client.HTTPSConnection("connex.csc.uvic.ca")

	headers = {'Cookie': f"JSESSIONID={session_id}"}

	conn.request("GET", "/access/content/group/de96da00-2ff7-4e52-b309-fce15e3b8e7a/org/a6_test_data.html", headers=headers)

	res = conn.getresponse()
	data = res.read()

	# parse html for easy searching
	soup = BeautifulSoup(data.decode("utf-8"), "html.parser")

	urls = []

	# put each url in an array
	for a in soup.select("ul.org-ul li a"):
		urls.append(a['href'][15:])

	return urls


def mkdir_force(dir):
	try:
		os.mkdir(dir)
	except FileExistsError:
		pass


def create_dirs():
	data_dir = Path("data")

	mkdir_force(data_dir)
	mkdir_force(data_dir / "output")
	mkdir_force(data_dir / "output" / "daily_avg")
	mkdir_force(data_dir / "output" / "daily_min_max")
	mkdir_force(data_dir / "output" / "station_extremes")


def download_test_file(url_filename, session_id, data_index):
	# set up the connection
	conn = http.client.HTTPSConnection("connex.csc.uvic.ca")

	# create the header
	headers = {'Cookie': f"JSESSIONID={session_id}"}

	# send the request
	conn.request("GET", f"/access/content/group/de96da00-2ff7-4e52-b309-fce15e3b8e7a/Assignments/{url_filename}", headers=headers)
	
	# receive and decode the response
	res = conn.getresponse()
	data = res.read().decode("utf-8")
	
	# set up the output directory
	data_dir = Path("data")
	dest_dir = data_dir

	if (url_filename.count("daily_avg")):
		dest_dir = data_dir / "output" / "daily_avg"
		url_filename = f"output-{data_index}.txt"

	elif (url_filename.count("daily_min_max")):
		dest_dir = data_dir / "output" / "daily_min_max"
		url_filename = f"output-{data_index}.txt"

	elif (url_filename.count("station_extremes")):
		dest_dir = data_dir / "output" / "station_extremes"
		url_filename = f"output-{data_index}.txt"
	
	else:
		url_filename = f"data-{data_index}.txt"
	
	# write the file to disk
	f = open(dest_dir / url_filename, "w")
	f.write(data)
	f.close()
	

def main():
	print("Log in to conneX")
	username = input("Username: ")
	password = getpass("Password: ")

	print("\nLogging in...\n")	
	session_id = get_session(username, password)

	urls = get_test_urls(session_id)

	if (urls == []):
		print("Error: couldn't log in")
		exit(1)

	create_dirs()

	for u,i in zip(urls, range(0, len(urls))):
		print("\rDownloading files: {:.0%}".format((i+1) / len(urls)), end='')
		download_test_file(u, session_id, (i // 4) + 1)
	
	print('\n')

if __name__ == "__main__":
	main()
