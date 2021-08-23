# UVic Schedule Exporter

## Usage

Install the dependencies.
```shell
$ pip install -r requirements.txt
```

Run the program.
```shell
$ # Some example output of the interactive prompt
$ python schedule_downloader.py
Year [2021]: 2022
Term [Summer]: Spring
Log in to UVic
Username: malcolmseyd
Password: 
Downloading...
Parsing...
Done. Wrote to schedule-202201.ics
```

## FAQ

**Q.** Why does it need my Netlink ID?  
**A.** It uses it to [get your schedule](https://documenter.getpostman.com/view/9187076/SVtZwmUP). If you don't trust it, read the code.

**Q.** I can't see my password when I type it? What's happening?  
**A.** Don't worry, it's just being hidden. The program will still read it

**Q.** What are those square brackets for the year an term?  
**A.** Those are default options. If you put nothing, then the option in the square bracket will be chosen by default.

**Q.** What options are there for the term?  
**A.** `spring`, `summer`, and `fall`, case insensitive. `sp`, `su`, and `f` also work as abbreviations.

## About

What started out as a simple web scraping project eventually turned into a useful tool that can integrate with common calendar software. Let's see how it works.

On UVic's website, they support viewing your schecule as a list of courses. The first part of my script logs into the website and downloads the date. [I've documented the API calls here.](https://documenter.getpostman.com/view/9187076/SVtZwmUP)

Next, we use BeautifulSoup to parse the html to get text-based data from it. We push the data through a few functions until it's ready to be exported.

Finally, we write the data to an iCalendar file. This filetype supports recurring events, so your schedule will look the same as the one on UVic's website.

We can now import the file into Google Calendar and voila, no more manually entering your courses every term.

### My schedule on UVic's website (before)
![UVic's website](https://i.imgur.com/S6EF8iE.png)

### My schedule imported to Google Calendar (after)
![Google Calendar](https://i.imgur.com/4RdAeS5.png)
