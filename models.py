from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine
from sqlalchemy import Time, Date, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relation
import datetime
import config

Base = declarative_base()

class Movie(Base):
    __tablename__ = 'movies'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255))
    showtimes = relation("Showtime", backref="movie")
    
    def __init__(self, title):
        self.title = title
        
    def __unicode__(self):
        return self.title
        
    def __str__(self):
        try:
            s = self.title.decode('utf8')
            return s.encode('ascii', 'ignore')
        except:
            return ""
        
class Theater(Base):
    __tablename__ = 'theaters'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    showtimes = relation("Showtime", backref="theater")
    
    def __init__(self, name):
        self.name = name
        
    def __str__(self):
        return self.name
        
class Showtime(Base):
    __tablename__ = 'showtimes'
    
    id = Column(Integer, primary_key=True)
    movie_id = Column(Integer, ForeignKey('movies.id'))
    theater_id = Column(Integer, ForeignKey('theaters.id'))
    time = Column(Time)
    availabilities = relation("Availability", backref="showtime")
    
    def __init__(self, movie, theater, time):
        self.movie = movie
        self.theater = theater
        self.time = time
        
    def __str__(self):
        return "%s (%s) at %s" % (self.movie, self.time, self.theater)
    
class Availability(Base):
    __tablename__ = 'availabilities'
    
    id = Column(Integer, primary_key=True)
    showtime_id = Column(Integer, ForeignKey('showtimes.id'))
    date = Column(Date)
    timestamp = Column(DateTime)
    status = Column(Enum("Available", "Sold Out"))
    
    def __init__(self, showtime, date, status, timestamp = None):
        if timestamp is None:
            timestamp = datetime.datetime.now()
        self.showtime = showtime
        self.date = date
        if status:
            self.status = "Available"
        else:
            self.status = "Sold Out"
        self.timestamp = timestamp
        

def setup():
    engine = create_engine(config.database_url)
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=True)
    session = Session()
    Base.metadata.create_all(engine)
    return session