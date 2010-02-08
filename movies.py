from BeautifulSoup import BeautifulSoup, NavigableString
import urllib2
from pprint import pprint
import re
import logging
import datetime

def theater_html(theater_id, theater_name):
    url = "http://www.cineplex.com/Theatres/TheatreDetails/%s/%s.aspx" % (theater_id, theater_name)
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    result = response.read()
    # f = open("testdata3.html", "w")
    # f.write(result)
    # f.close()
    return result
    
def cached_html(theater_id, theater_name):
    f = open("data/testdata.html", "r")
    result = f.read()
    f.close()
    return result
    
def get_showtimes(theater_id, theater_name):
    soup = BeautifulSoup(theater_html(theater_id, theater_name))
    movielist = soup.findAll('div', "MovieList")
    movies = {}
    pat = re.compile("\d+:\d+\wm")
    current_year = datetime.date.today().year
    for movie_div in movielist:
        try:
            title = movie_div.div.h1.a.string
            movie_date_text_html = movie_div.div.findNextSibling('div').find('p', 'filmenhancement').contents[0].strip()
            movie_date_text = "".join(movie_date_text_html.partition(str(current_year))[:2])
            movie_date = datetime.datetime.strptime(movie_date_text, "%B %d, %Y").date()
            showtimes = movie_div.div.findNextSibling('div').find('p', 'showtimes')
            movies[title] = {"available":[], "soldout":[]}
            times = []
            for thing in showtimes.contents:
                if isinstance(thing, NavigableString):
                    if pat.search(thing):
                        for token in thing.split("|"):
                            if token.strip() != "":
                                times.append(token.strip())
                else:
                    times.append(thing.string)
            for time in times:
                if "SOLD OUT" in time:
                    time = time.split(" ")[0]
                    availability = "soldout"
                else:
                    availability = "available"
                movie_time = datetime.datetime.strptime(time, "%I:%M%p")
                movie_time = movie_time.replace(movie_date.year, movie_date.month, movie_date.day)
                movies[title][availability].append(movie_time)
        except Exception, e:
            logging.exception("Exception while parsing a movie")
    return movies
        
    
if __name__ == "__main__":
    pprint(get_showtimes("3ED25043", "SilverCity_Riverport"))