from BeautifulSoup import BeautifulSoup, NavigableString
import urllib2
from pprint import pprint
import re
import logging

def theater_html(theater_id, theater_name):
    url = "http://www.cineplex.com/Theatres/TheatreDetails/%s/%s.aspx?date=2010-1-28" % (theater_id, theater_name)
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    result = response.read()
    f = open("testdata2.html", "w")
    result = f.write(result)
    f.close()
    return result
    
def cached_html(theater_id, theater_name):
    f = open("testdata.html", "r")
    result = f.read()
    f.close()
    return result
    
def get_showtimes(theater_id, theater_name):
    soup = BeautifulSoup(cached_html(theater_id, theater_name))
    movielist = soup.findAll('div', "MovieList")
    movies = {}
    pat = re.compile("\d+:\d+\wm")
    for movie_div in movielist:
        try:
            title = movie_div.div.h1.a.string
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
                    movies[title]["soldout"].append(time.split(" ")[0])
                else:
                    movies[title]["available"].append(time)
        except Exception, e:
            logging.exception("Exception while parsing a movie")
    return movies
        
    
if __name__ == "__main__":
    pprint(get_showtimes("3ED25043", "SilverCity_Riverport"))