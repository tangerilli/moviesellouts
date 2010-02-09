import urllib2
from pprint import pprint
import re
import logging
import datetime
import itertools

from BeautifulSoup import BeautifulSoup, NavigableString

import models
from models import Movie, Theater, Showtime, Availability

def theater_html(theater_id, theater_name):
    url = "http://www.cineplex.com/Theatres/TheatreDetails/%s/%s.aspx" % (theater_id, theater_name)
    logging.debug("Fetching %s" % url)
    request = urllib2.Request(url)
    response = urllib2.urlopen(request)
    result = response.read()
    # f = open("testdata4.html", "w")
    # f.write(result)
    # f.close()
    return result
    
def cached_html(theater_id, theater_name):
    f = open("data/testdata.html", "r")
    result = f.read()
    f.close()
    return result

def get_newstyle_showtimes(soup):
    """
    Deals with the new cineplex layout
    """
    movies = {}
    pat = re.compile("\d+:\d+\wm")
    current_year = datetime.date.today().year
    movielist = soup.findAll('div', 'Listing') + soup.findAll('div', 'Listing ListingAlt')
    for movie_div in movielist:
        try:
            title = movie_div.a.h3.string.strip()
            movie_date_text = movie_div.find('div', 'Times').div.string.split("-")[0].strip()
            
            movie_date = datetime.datetime.strptime(movie_date_text, "%B %d, %Y").date()
            showtimes = movie_div.find('div', 'Times').div.findNextSibling('div')
            movies[title] = {"available":[], "soldout":[], "date":movie_date}
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
                movie_time = datetime.datetime.strptime(time, "%I:%M%p").time()
                movies[title][availability].append(movie_time)
            
        except Exception, e:
            logging.exception("Exception while parsing a movie")
    return movies
    
def get_showtimes(theater_id, theater_name):
    soup = BeautifulSoup(theater_html(theater_id, theater_name))
    movielist = soup.findAll('div', "MovieList")
    if len(movielist) == 0:
        logging.debug("New style page")
        return get_newstyle_showtimes(soup)
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
            movies[title] = {"available":[], "soldout":[], "date":movie_date}
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
                movie_time = datetime.datetime.strptime(time, "%I:%M%p").time()
                movies[title][availability].append(movie_time)
        except Exception, e:
            logging.exception("Exception while parsing a movie")
    return movies
        
def update_database(session, showtimes, theater_name):
    # First get the associated theater object (creating it if necessary)
    theater = session.query(Theater).filter(Theater.name == theater_name).first()
    if theater is None:
        theater = Theater(theater_name)
        session.add(theater)
    logging.debug("Processing theater: %s", theater)
    for movie_name, times in showtimes.items():
        # Then get each movie
        movie = session.query(Movie).filter(Movie.title==movie_name).first()
        if movie is None:
            movie = Movie(movie_name)
            session.add(movie)
        try:
            logging.debug("Processing movie: %s", movie)
        except:
            pass
        for time in itertools.chain(times["soldout"], times["available"]):
            # For each movie, get the various showtimes
            showtime = session.query(Showtime).filter(Showtime.movie == movie).filter(Showtime.theater == theater).\
                                               filter(Showtime.time == time).first()
            if showtime is None:
                showtime = Showtime(movie, theater, time)
                session.add(showtime)
            # And then make a record of whether that showtime is available right now or not
            status = time in times["available"]
            availability = Availability(showtime, times["date"], status)
            session.add(availability)
        
    
if __name__ == "__main__":
    logging.basicConfig()
    for handler in logging.getLogger().handlers:
        handler.setFormatter(logging.Formatter("%(name)s: %(message)s"))
    logging.getLogger().setLevel(logging.DEBUG)
        
    logging.debug("Starting")
    db_session = models.setup()
    
    showtimes = get_showtimes("3ED25043", "SilverCity_Riverport")
    #pprint(showtimes)
    update_database(db_session, showtimes, "Silvercity Riverport")
    db_session.commit()