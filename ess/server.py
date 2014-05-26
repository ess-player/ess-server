#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Imports
from flask import Flask, request, redirect, url_for, render_template, jsonify, stream_with_context, Response
from sqlalchemy import or_, and_, desc
import json
from ess.db import get_session, Song, Artist, Album, Player, Playlist
import os.path
# Create aplication
app = Flask(__name__)
app.config.from_object(__name__)

_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']

# View method for entries
@app.route('/', methods = ['GET', 'POST'])
def list ():
	# Method POST
	if request.method == 'POST':
		searchword = request.form['search']

		# Redirect to list with searchword
		if searchword:
			return redirect('%s/?s=%s' % (url_for('list'), request.form['search'] ))

		# Searching with an empty string redirect to list
		return redirect(url_for('list'))

	# Method GET
	# Get searchword from URL
	s = request.args.get('s', '')
	if s:
		hs = '%' + s + '%'
		entries = get_session().query(Song)\
				.outerjoin(Album)\
				.outerjoin(Artist)\
				.filter(or_(Song.title.like(hs),
							Song.genre.like(hs),
							Song.date.like(hs),
							Album.name.like(hs),
							Artist.name.like(hs)))\
				.order_by(Song.title)\
				.all()

	else:
		entries = get_session().query(Song).order_by(Song.title).all()

	# Return the list of data
	return render_template('database.html', entries=entries, searchword=s)


@app.route('/search', methods = ['POST'])
def song_search():

	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data
	try:
		data = json.loads(data)
	except Exception as e:
		return e.message, 400

	search = data.get('search')
	if not search:
		entries = get_session().query(Song)\
					.outerjoin(Album)\
					.outerjoin(Artist)
	else:
		searchlist = search.split()
		if not searchlist:
			entries = get_session().query(Song)\
					.outerjoin(Album)\
					.outerjoin(Artist)
		else:
			hs = '%' + searchlist[0]  + '%'
			entries = get_session().query(Song)\
						.outerjoin(Album)\
						.outerjoin(Artist)\
						.filter(or_(Song.title.like(hs),
									Song.genre.like(hs),
									Song.date.like(hs),
									Album.name.like(hs),
									Artist.name.like(hs)))

			for s in searchlist[1:]:
				hs = '%' + s + '%'
				entries  = entries\
						.filter(or_(Song.title.like(hs),
									Song.genre.like(hs),
									Song.date.like(hs),
									Album.name.like(hs),
									Artist.name.like(hs)))

	entries = entries.order_by(Artist.name)
	songs = []
	for entry in entries:
		if entry.artist:
			artist_name = entry.artist.name
		else:
			artist_name = None
		if entry.album:
			album_name = entry.album.name
		else:
			album_name = None
		songs.append({
			'id'           : entry.id,
			'title'        : entry.title,
			'artist'       : artist_name,
			'album'        : album_name,
			'date'         : entry.date,
			'genre'        : entry.genre,
			'tracknumber'  : entry.tracknumber,
			'times_played' : entry.times_played
			})

	return jsonify({'songs': songs})


# Deliver Songs to player
@app.route('/song/<int:song_id>')
def deliver_song(song_id):

	song = get_session().query(Song).filter(Song.id ==
			song_id).first()

	if not song:
		return '', 404

	def generate():
		with open(song.uri,'rb') as f:
			part = f.read(1024)
			while part:
				yield part
				part = f.read(128*1024)
 	response = Response(stream_with_context(generate()), mimetype='application/octet-stream')
	response.headers['content-length'] = os.path.getsize(song.uri)
	return response


@app.route('/player', methods = ['POST'])
def player_register():
	'''Register a player. The data have to be JSON encoded.
	Example::

		{"name":"player01", "description":"The first player"}

	'''
	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data
	try:
		data = json.loads(data)
	except Exception as e:
		return e.message, 400

	# Get the name of the player. It may not be empty.
	playername = data.get('name')
	if not playername:
		return 'playername is missing', 400

	# Get an optional description
	description = data.get('description')

	# Check if the player already exists
	session = get_session()
	player = session.query(Player).filter(Player.playername==playername).first()
	if player:
		return '', 204
	player = Player(
			playername=playername,
			description=description)
	session.add(player)
	print('>>> Create new player: %s' % playername)
	session.commit()
	return '', 201


@app.route('/player', methods = ['GET'])
def player_list_all():
	'''List all players.
	'''
	playerlist = []
	for player in get_session().query(Player):
		playerlist.append({
			'name'        : player.playername,
			'description' : player.description,
			'current'     : player.current.id if player.current else None})

	return  jsonify(player=playerlist)


@app.route('/player/<name>', methods = ['GET'])
def player_list(name):
	'''List player *name*.
	'''
	player = get_session().query(Player).filter(Player.playername==name).first()
	return jsonify({
			'name'        : player.playername,
			'description' : player.description,
			'current'     : player.current.id if player.current else None} \
					if player else {})


@app.route('/player/<name>', methods = ['DELETE'])
def player_delete(name):
	'''Delete player.
	'''
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	# Get playlist and delete it
	playlist = session.query(Playlist).filter(Playlist.playername==name)
	for entry in playlist:
		session.delete(entry)
	session.commit()
	session.delete(player)
	session.commit()
	return '', 204

@app.route('/playlist', methods = ['GET'])
def playlist_list_all():
	''' List playlists of all players
	'''

	all = {}

	session = get_session()
	for player in session.query(Player):

		# Get Current
		if player.current:
			current = player.current.id
		else:
			current = None

		# Get Songs
		playlist = session.query(Playlist)\
				.filter(Playlist.playername==player.playername)

		list = []
		for entry in playlist:
			list.append(entry.song_id)

		all[player.playername] = {'list' : list, 'current' : current}

	return jsonify(all)


@app.route('/playlist', methods = ['DELETE'])
def playlist_delete_all():
	''' Delete playlists of all players
	'''
	session = get_session()

	# Change current of alle player to None
	for player in session.query(Player):
		if player.current:
			player.current = None

	# Get all playlistentries and delete them
	for entry in session.query(Playlist):
		session.delete(entry)
	session.commit()
	return '', 204


@app.route('/playlist/<name>', methods = ['GET'])
def playlist_list(name):
	'''List playlist from player *name*.
	'''
	session = get_session()

	# Get Player and Current
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	if player.current:
		current = player.current.id
	else:
		current = None

	# Get Songs
	playlist = session.query(Playlist).filter(Playlist.playername==name)

	list = []
	for entry in playlist:
		list.append(entry.song_id)

	return jsonify({
			'list'        : list,
			'current'     : current})


@app.route('/playlist/<name>', methods = ['POST'])
def playlist_post(name):
	'''Post a playerlist for the player *name*.
	'''
	session = get_session()

	# Check if player exists
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data
	try:
		data = json.loads(data)
	except Exception as e:
		return e.message, 400

	# Get list of song_ids.
	list = data.get('list')
	if not list:
		return 'list is missing', 400

	# Get optionally current.
	current = data.get('current')
	if current and current not in list:
		return 'Playlist does not contain Song', 400

	# Check if the playlist already exists
	playlist = session.query(Playlist).filter(Playlist.playername==name).all()
	if len(playlist)!=0:
		return 'playlist exists', 400
	# Create playlist
	for index in range(len(list)):
		session.add(Playlist(order=index+1,
			playername=name,
			song_id = list[index]))

	# Set Current
	song = session.query(Song).filter(Song.id==current).first()
	if not song:
		return 'Database does not contain song', 400
	player.current = song

	print('>>> Create new playlist for %s' % name)
	session.commit()
	return '', 201


@app.route('/playlist/<name>', methods = ['DELETE'])
def playlist_delete(name):
	'''Delete playlist.
	'''
	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	# Change current to None
	if player.current:
		player.current = None

	# Get playlist and delete it
	playlist = session.query(Playlist).filter(Playlist.playername==name)
	for entry in playlist:
		session.delete(entry)
	session.commit()
	return '', 204

@app.route('/playlist/<name>/<int:place>/up')
def playlist_entry_up(name,place):
	'''Change playlistentry from playlist playlist on place place with
	playlistentry on place place+1'''

	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'player not found', 404

	# Get playlist and entries
	playlist = session.query(Playlist).filter(Playlist.playername==name)
	if not playlist.count():
		return 'playlist not found', 404
	entry1   = playlist.filter(Playlist.order==place).first()
	if not entry1:
		return 'entry not found', 404
	entry2   = playlist.filter(Playlist.order==place+1).first()
	if not entry2:
		return '', 204

	h = entry1.song_id
	entry1.song_id = entry2.song_id
	entry2.song_id = h
	session.commit()
	return '', 204


@app.route('/playlist/<name>/<int:place>/down')
def playlist_entry_down(name,place):
	'''Change playlistentry from playlist playlist on place place with
	playlistentry on place place-1'''

	if place == 1:
		return '204'

	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'player not found', 404

	# Get playlist and entries
	playlist = session.query(Playlist).filter(Playlist.playername==name)
	if not playlist.count():
		return 'playlist not found', 404
	entry1   = playlist.filter(Playlist.order==place).first()
	if not entry1:
		return 'entry not found', 404
	entry2   = playlist.filter(Playlist.order==place-1).first()

	h = entry1.song_id
	entry1.song_id = entry2.song_id
	entry2.song_id = h
	session.commit()
	return '', 204


@app.route('/playlist/<name>/<int:place>', methods = ['DELETE'])
def playlist_entry_delete(name,place):
	'''Delete playlistentry from playlist on place place'''

	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'player not found', 404

	# Get playlist and entries
	playlist =	session.query(Playlist).filter(and_(Playlist.playername==name,
			Playlist.order>=place))

	for entry in playlist.order_by(Playlist.order):
		hentry = playlist.filter(Playlist.order==entry.order+1).first()
		if hentry:
			entry.song_id = hentry.song_id
		else:
			session.delete(entry)
	session.commit()
	return '', 204


@app.route('/playlist/<name>/<int:place>', methods = ['PUT'])
def playlist_entry_add(name,place):
	'''Add playlistentry to playlist to place place'''
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/json']:
		return 'Invalid data type: %s' % type, 400
	try:
		data = json.loads(data)
	except Exception as e:
		return e.message, 400

	id  = data.get('id')
	if not id:
		return 'Song id is missing', 400

	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'player not found', 404

	# Get playlist and add entry
	playlist =	session.query(Playlist).filter(Playlist.playername==name)
	size = playlist.count()
	if place > size+1:
		return 'place too big', 400

	session.add(Playlist(order=playlist.count()+1,
		playername=name))

	# Get size of playlist (changed)
	size = playlist.count()
	# Shift entries of playlist
	for entry in playlist.filter(Playlist.order>=place).order_by(desc(Playlist.order)):
		if entry.order != place:
			entry.song_id = playlist.filter(Playlist.order==entry.order-1)\
					.first().song_id
		else:
			entry.song_id = id
	session.commit()

	return '', 204


# Handle current from a player's playlist
@app.route('/playlist/<playername>/current', methods = ['GET'])
def current_playing_get(playername):
	player = get_session().query(Player).filter(Player.playername==playername).first()
	if player:
		return json.dumps({'id' : player.current.id if player.current else None})
	return 'Do not exist', 404


@app.route('/playlist/<playername>/current', methods = ['POST'])
def current_playing_set(playername):
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/json']:
		return 'Invalid data type: %s' % type, 400
	try:
		data = json.loads(data)
	except Exception as e:
		return e.message, 400

	id  = data.get('id')
	if not id:
		return 'Song id is missing', 400

	session = get_session()
	player = session.query(Player).filter(Player.playername==playername).first()
	if not player:
		return 'Player does not exist', 404

	entry = session.query(Playlist).filter(Playlist.playername==playername,
			Playlist.song_id==id).first()
	if not entry:
		return 'Playlist does not contain song', 400

	player.current = entry.song
	session.commit()
	return 'Change current', 200
