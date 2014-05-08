#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Imports
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref

Base = declarative_base()

# init
def get_session():
	DATABASE = 'mysql://ess:secret@localhost/ess?charset=utf8'
	engine = create_engine(DATABASE)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	return Session()


#############################################################################
## Database Schema Definition                                              ##
#############################################################################

class Artist(Base):
	__tablename__ = 'music_artist'

	id   = Column('id', Integer(unsigned=True), autoincrement='ignore_fk',
			primary_key=True)
	name = Column('name', String(255), nullable=False)

	def __repr__(self):
		return '<Artist(id=%i, name="%s")>' % (self.id, self.name)


class Album(Base):
	__tablename__ = 'music_album'

	id        = Column('id', Integer, autoincrement='ignore_fk',
			primary_key=True)
	name      = Column('name', String(255), nullable=False)
	artist_id = Column('artist_id', None, ForeignKey('music_artist.id'))

	artist = relationship("Artist", backref=backref('album', order_by=name))

	def __repr__(self):
		return '<Album(id=%i, name="%s", artist_id=%i)>' % \
				(self.id, self.name, self.artist_id)


class Song(Base):
	__tablename__ = 'music_song'

	id           = Column('id', Integer(unsigned=True), primary_key=True, autoincrement=True)
	title        = Column('name', String(255), nullable=False)
	date         = Column('date', String(255))
	tracknumber  = Column('tracknumber', Integer(unsigned=True))
	times_played = Column('times_played', Integer(unsigned=True))
	uri          = Column('uri', String(2**16), nullable=False)
	genre        = Column('genre', String(255))
	artist_id    = Column('artist_id', None, ForeignKey('music_artist.id'))
	album_id     = Column('album_id', None, ForeignKey('music_album.id'))

	artist = relationship("Artist", backref=backref('song', order_by=title))
	album  = relationship("Album",  backref=backref('song', order_by=title))

	def __repr__(self):
		return '<Song(id=%i, title="%s", artist_id=%i)>' % \
			(self.id, self.title, self.artist_id)

