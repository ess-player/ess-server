#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from ess import config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.schema import PrimaryKeyConstraint, ForeignKeyConstraint
Base = declarative_base()

# Init
def init():
	global engine
	engine = create_engine(config.DATABASE)
	Base.metadata.create_all(engine)


def get_session():
	if not 'engine' in globals():
		init()
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
	artist_id = Column('artist_id', ForeignKey('music_artist.id'))

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
	artist_id    = Column('artist_id', ForeignKey('music_artist.id'))
	album_id     = Column('album_id', ForeignKey('music_album.id'))

	artist       = relationship("Artist", backref=backref('music_song'))
	album        = relationship("Album",  backref=backref('music_song'))

	def __repr__(self):
		return '<Song(id=%i, title="%s", artist_id=%i)>' % \
			(self.id, self.title, self.artist_id)

	def serialize(self, expand=0):
		return {k:v for k,v in self.__dict__.items() if not k.startswith('_')}


class Player(Base):
	__tablename__ = 'player'

	playername  = Column('playername', String(255), primary_key=True)
	description = Column('description', String(255))
	current_idx = Column('current', Integer(unsigned=True), default=None)

	current     = relationship("Playlist", foreign_keys=[playername, current_idx])

	__table_args__ = (
			ForeignKeyConstraint(
				[playername, current_idx],
				['playlist.playername', 'playlist.order'],
				use_alter=True,
				name='fk_current_song'),
			{})

	def __repr__(self):
		return '<Player(playername=%s, description=%s, current_idx=%i)>' % \
			(self.playername, self.description, self.current_idx)

	def serialize(self, expand=0):
		if expand:
			return {'playername':self.playername, 'description':self.description,
					'current_idx':self.current_idx, 'current':self.current.serialize(expand-1)}
		return {'playername':self.playername, 'description':self.description,
				'current_idx':self.current_idx}


class Playlist(Base):
	__tablename__ = 'playlist'

	playername  = Column('playername', ForeignKey('player.playername'), primary_key=True)
	order       = Column('order', Integer(unsigned=True), primary_key=True, autoincrement=False)
	song_id     = Column('song_id', ForeignKey('music_song.id'), nullable=False)

	song        = relationship("Song",  backref=backref('playlist'))
	player      = relationship("Player", foreign_keys=[playername])

	def __repr__(self):
		return '<(playername=%s, order=%i, song_id=%i)>' % \
			(self.playername, self.order, self.song_id)

	def serialize(self, expand=0):
		if expand:
			return {'playername':self.playername,
					'player':self.player.serialize(expand-1), 'order':self.order,
					'song_id':self.song_id, 'song':self.song.serialize(expand-1)}
		return {'playername':self.playername, 'order':self.order,
				'song_id':self.song_id}
