# -*- coding: utf-8 -*-
'''
	ess.db
	~~~~~~

	Database specification for the ess player project.

	:license: FreeBSD, see license file for more details.
'''

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from ess import config
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy.schema import ForeignKeyConstraint
Base = declarative_base()

def init():
	'''Initialize connection to database. Additionally the basic database
	structure will be created if nonexistent.
	'''
	global engine
	engine = create_engine(config.DATABASE)
	Base.metadata.create_all(engine)


def get_session():
	'''Get a session for database communication. If necessary a new connection
	to the database will be established.

	:return:  Database session
	'''
	if not 'engine' in globals():
		init()
	Session = sessionmaker(bind=engine)
	return Session()


# Database Schema Definition
class Artist(Base):
	'''Database definition of an artist.'''

	__tablename__ = 'artist'

	id   = Column('id', Integer(unsigned=True), autoincrement='ignore_fk',
			primary_key=True)
	'''Unique identifier of an artist'''
	name = Column('name', String(255), nullable=False)
	'''Name of an artist'''


	def __repr__(self):
		'''Return a string representation of an artist object.

		:return: String representation of object.
		'''
		return '<Artist(id=%i, name="%s")>' % (self.id, self.name)

	def serialize(self, expand=0):
		'''Serialize this object as dictionary usable for conversion to JSON.

		:param expand: Defines if sub objects shall be serialized as well.
		:return: Dictionary representing this object.
		'''
		return {'id':self.id, 'name':self.name}


class Album(Base):
	'''Database definition of an album.'''

	__tablename__ = 'album'

	id        = Column('id', Integer, autoincrement='ignore_fk',
			primary_key=True)
	'''Unique identifier of an album'''
	name      = Column('name', String(255), nullable=False)
	'''Name of an album'''
	artist_id = Column('artist_id', ForeignKey('artist.id'))
	'''Id of the Artist of an Album'''

	artist    = relationship("Artist", backref=backref('album'))
	'''Artist of an Album'''

	def __repr__(self):
		'''Return a string representation of an album object.

		:return: String representation of object.
		'''
		return '<Album(id=%i, name="%s", artist_id=%i)>' % \
				(self.id, self.name, self.artist_id)


	def serialize(self, expand=0):
		'''Serialize this object as dictionary usable for conversion to JSON.

		:param expand: Defines if sub objects shall be serialized as well.
		:return: Dictionary representing this object.
		'''
		if expand:
			return {'id':self.id, 'name':self.name,
					'artist':self.artist.serialize(expand-1)}
		return {'id':self.id, 'name':self.name, 'artist':self.artist_id}


class Media(Base):
	'''Database definition of a mediafile.'''
	__tablename__ = 'media'

	id           = Column('id', Integer(unsigned=True), primary_key=True,
			autoincrement=True)
	'''Unique identifier of a mediafile'''
	title        = Column('title', String(255), nullable=False)
	'''Title of a mediafile'''
	date         = Column('date', String(255))
	'''Date of a mediafile'''
	tracknumber  = Column('tracknumber', Integer(unsigned=True))
	'''Tracknumber of a mediafile in an album'''
	times_played = Column('times_played', Integer(unsigned=True), default=0)
	'''Times the mediafile was played'''
	path         = Column('path', String(2**16), nullable=False)
	'''Path of a mediafile'''
	genre        = Column('genre', String(255))
	'''Genre of a mediafile'''
	duration     = Column('duration', Integer(unsigned=True), nullable=True)
	'''Duration of a mediafile'''
	artist_id    = Column('artist_id', ForeignKey('artist.id'))
	'''Id of the Artist of a mediafile'''
	album_id     = Column('album_id', ForeignKey('album.id'))
	'''Id of the Album of a mediafile'''
	artist       = relationship("Artist", backref=backref('media'))
	'''Artist of a mediafile'''
	album        = relationship("Album",  backref=backref('media'))
	'''Album of a mediafile'''
	def __repr__(self):
		'''Return a string representation of a media object.

		:return: String representation of object.
		'''
		return '<Media(id=%i, title="%s", artist_id=%i)>' % \
			(self.id, self.title, self.artist_id)


	def serialize(self, expand=0):
		'''Serialize this object as dictionary usable for conversion to JSON.

		:param expand: Defines if sub objects shall be serialized as well.
		:return: Dictionary representing this object.
		'''
		result = {
				'id'           : self.id,
				'title'        : self.title,
				'date'         : self.date,
				'tracknumber'  : self.tracknumber,
				'times_played' : self.times_played,
				'path'         : self.path,
				'genre'        : self.genre,
				'duration'     : self.duration,
				'artist'       : self.artist_id,
				'album'        : self.album_id}
		if expand:
			result['artist'] = self.artist.serialize(expand - 1)
			result['album']  = self.album.serialize(expand - 1)
		return result


class Player(Base):
	'''Database definition of a player.'''
	__tablename__ = 'player'

	playername  = Column('playername', String(255), primary_key=True)
	'''Name of a player (This is unique)'''
	description = Column('description', String(255))
	'''Optional description of a player'''
	current_idx = Column('current', Integer(unsigned=True), default=None)
	'''Id of the mediafile that is currently played'''
	current     = relationship("PlaylistEntry",
			foreign_keys=[playername, current_idx])
	'''Mediafile that is currenty played'''

	__table_args__ = (
			ForeignKeyConstraint(
				[playername, current_idx],
				['playlist_entry.playername', 'playlist_entry.order'],
				use_alter=True,
				name='fk_current_media'),
			{})

	def __repr__(self):
		'''Return a string representation of a player object.

		:return: String representation of object.
		'''
		return '<Player(playername=%s, description=%s, current_idx=%i)>' % \
			(self.playername, self.description, self.current_idx)


	def serialize(self, expand=0):
		'''Serialize this object as dictionary usable for conversion to JSON.

		:param expand: Defines if sub objects shall be serialized as well.
		:return: Dictionary representing this object.
		'''
		return {
				'playername'  : self.playername,
				'description' : self.description,
				'current'     : self.current.serialize(expand-1) \
						if expand and self.current else self.current_idx }


class PlaylistEntry(Base):
	__tablename__ = 'playlist_entry'
	'''Database definition of a playlistentry'''

	playername  = Column('playername', ForeignKey('player.playername'), primary_key=True)
	'''Name of the player to which the playlist belongs'''
	order       = Column('order', Integer(unsigned=True), primary_key=True, autoincrement=False)
	'''The position of a playlistentry in the playlist'''
	media_id    = Column('media_id', ForeignKey('media.id'), nullable=False)
	'''Id of the mediafile corresponding to the playlistentry'''
	media       = relationship("Media",  backref=backref('playlist_entry'))
	'''Mediafile corresponding to the playlistentry'''
	player      = relationship("Player", foreign_keys=[playername])
	'''Player to which the playlist belongs'''

	def __repr__(self):
		'''Return a string representation of a playlistentry object.

		:return: String representation of object.
		'''
		return '<(playername=%s, order=%i, media_id=%i)>' % \
			(self.playername, self.order, self.media_id)


	def serialize(self, expand=0):
		'''Serialize this object as dictionary usable for conversion to JSON.

		:param expand: Defines if sub objects shall be serialized as well.
		:return: Dictionary representing this object.
		'''
		return {
				'player' : self.player.serialize(expand-1) if expand else self.playername,
				'order'  : self.order,
				'media'  : self.media.serialize(expand-1) if expand else self.media_id}
