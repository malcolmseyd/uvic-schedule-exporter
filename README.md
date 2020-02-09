# UVic Schedule Exporter

 What started out as a simple web scraping project eventually turned into a useful tool that can integrate with common calendar software. Let's see how it works.

On UVic's website, they support viewing your schecule as a list of courses. The first part of my script logs into the website and downloads the date. [I've documented the API calls here.](https://documenter.getpostman.com/view/9187076/SVtZwmUP)

Next, we use BeautifulSoup to parse the html to get text-based data from it. We push the data through a few functions until it's ready to be exported.

Finally, we write the data to an iCalendar file. This filetype supports recurring events, so your schedule will look the same as the one on UVic's website.

We can now import the file into Google Calendar and voila, no more manually entering your courses every term.

### My schedule on UVic's website (before)
![UVic's website](https://i.imgur.com/taWPzAp.png)

### My schedule imported to Google Calendar (after)
![Google Calendar](https://i.imgur.com/MlAJMfd.png)