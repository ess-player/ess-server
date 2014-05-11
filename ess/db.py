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
from sqlalchemy.schema import PrimaryKeyConstraint
Base = declarative_base()

# Init
def get_session():
	DATABASE = 'mysql://ess:secret@localhost/ess?charset=utf8'
	engine = create_engine(DATABASE)
	Base.metadata.create_all(engine)
	Session = sessionmaker(bind=engine)
	return Session()


# Database Schema Definition
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

	artist    = relationship("Artist", backref=backref('music_album'))

	def __repr__(self):
		return '<Album(id=%i, name="%s", artist_id=%i)>' % \
				(self.id, self.name, self.artist_id)


class Song(Base):
	__tablename__ = 'music_song'

	id           = Column('id', Integer(unsigned=True), primary_key=True,
			autoincrement=True)
	title        = Column('title', String(255), nullable=False)
	date         = Column('date', String(255))
	tracknumber  = Column('tracknumber', Integer(unsigned=True))
	times_played = Column('times_played', Integer(unsigned=True))
	uri          = Column('uri', String(2**16), nullable=False)
	genre        = Column('genre', String(255))
	artist_id    = Column('artist_id', None, ForeignKey('music_artist.id'))
	album_id     = Column('album_id', None, ForeignKey('music_album.id'))

	artist       = relationship("Artist", backref=backref('music_song'))
	album        = relationship("Album",  backref=backref('music_song'))

	def __repr__(self):
		return '<Song(id=%i, title="%s", artist_id=%i)>' % \
			(self.id, self.title, self.artist_id)

class Player(Base):
	__tablename__ = 'player'

	playername  = Column('playername', String(255), primary_key=True)
	description = Column('description', String(255))
	song_id     = Column('song_id', None, ForeignKey('music_song.id'))

	current     = relationship("Song", backref=backref('player'))

	def __repr__(self):
		return '<Player(playername=%s, description="%s", song_id=%i)>' % \
			(self.playername, self.description, self.song_id)

class Playlist(Base):
	__tablename__ = 'playlist'

	order      = Column('order', Integer(unsigned=True), primary_key=True)
	playername = Column('playername', None, ForeignKey('player.playername'),
			primary_key=True)
	song_id    = Column('song_id', None, ForeignKey('music_song.id'))

	song       = relationship("Song",  backref=backref('playlist'))
	player     = relationship("Player", backref=backref('playerlist'),
			uselist=False)

	def __repr__(self):
		return '<(playername=%s, order="%i", song_id=%i)>' % \
			(self.playername, self.order, self.song_id)

