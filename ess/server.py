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


def get_expand():
	try:
		return int(request.args.get('expand', 0))
	except:
		return 0


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
	''' Search for songs '''
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


@app.route('/song/<int:song_id>')
def deliver_song(song_id):
	''' Deliver Songs to player '''

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
	session = get_session()
	expand  = get_expand()
	playerlist = [p.serialize(expand) for p in session.query(Player)]
	return  jsonify(player=playerlist)


@app.route('/player/<name>', methods = ['GET'])
def player_list(name):
	'''List player *name*.
	'''
	session = get_session()
	expand  = get_expand()

	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404
	return jsonify(player.serialize(expand))


@app.route('/player/<name>', methods = ['DELETE'])
def player_delete(name):
	'''Delete player.
	'''
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	session.query(Playlist).filter(Playlist.playername==name).delete()
	session.delete(player)
	session.commit()
	return '', 204


@app.route('/playlist', methods = ['GET'])
def playlist_list_all():
	''' List playlists of all players
	'''
	result = {}

	expand  = get_expand()
	session = get_session()
	playlist = session.query(Playlist).order_by(Playlist.order)

	# Collect songs of playlist
	for entry in playlist:
		if not result.get(entry.playername):
			result[entry.playername] = []
		result[entry.playername].append(entry.serialize(expand))

	return jsonify(result)


@app.route('/playlist', methods = ['DELETE'])
def playlist_delete_all():
	''' Delete playlists of all players
	'''
	session = get_session()

	# Delete currents
	for player in session.query(Player):
		player.current_idx = None

	# Delete playlists
	session.query(Playlist).delete()

	session.commit()
	return '', 204


@app.route('/playlist/<name>', methods = ['GET'])
def playlist_list(name):
	'''List playlist from player *name*.
	'''
	expand  = get_expand()
	session = get_session()

	# Get Player and Current
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	# Get Songs
	playlist = session.query(Playlist)\
			.filter(Playlist.playername==name)\
			.order_by(Playlist.order)

	# Collect songs of playlist
	items = [e.serialize(expand) for e in playlist]

	return jsonify({name:items})


@app.route('/playlist/<name>', methods = ['PUT'])
def playlist_put(name):
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
	except:
		return 'Invalid data', 400

	# Get list of song_ids.
	songs = data.get('list')
	if not songs:
		return 'List of songs is missing', 400

	# Delete old entries
	playlist = session.query(Playlist).filter(Playlist.playername==name).delete()

	# Create playlist
	for i in xrange(len(songs)):
		session.add(Playlist(order=i, playername=name, song_id=songs[i]))

	print('>>> Create new playlist for %s' % name)
	session.commit()
	return '', 201


@app.route('/playlist/<name>', methods = ['DELETE'])
def playlist_delete(name):
	'''Delete playlist.
	'''
	session = get_session()
	# Unset current
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'player not found', 404
	player.current_idx = None
	# Delete playlists
	session.query(Playlist).filter(Playlist.playername==name).delete()
	session.commit()

	return '', 204


@app.route('/playlist/<name>/<int:place>/up')
@app.route('/playlist/<name>/<int:place>/down')
def playlist_entry_down(name,place):
	'''Change playlistentry from playlist playlist on place place with
	playlistentry on place place-1'''

	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'player not found', 404

	direction = 1 if request.path.endswith('/down') else -1

	# Get playlist and entries
	playlist = session.query(Playlist).filter(Playlist.playername==name)
	entry1   = playlist.filter(Playlist.order==place).first()
	entry2   = playlist.filter(Playlist.order==place + direction).first()
	if not (entry1 and entry2):
		return 'entry not found', 404
	if player.current_idx == place:
		player.current_idx = player.current_idx + direction
	entry1.song_id, entry2.song_id = entry2.song_id, entry1.song_id
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

	# Delete entry on place
	entry = session.query(Playlist).filter(and_(Playlist.playername==name,
			Playlist.order==place)).first()
	if entry:
		session.delete(entry)
	else:
		return '', 404

	# New order
	playlist =	session.query(Playlist).filter(and_(Playlist.playername==name,
			Playlist.order>place))
	for entry in playlist.order_by(Playlist.order):
		entry.order = entry.order-1
	session.commit()
	return '', 204


@app.route('/playlist/<name>/current', methods = ['DELETE'])
def current_playing_delete(name):
	'''Handle current from a player's playlist'''
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404
	player.current_idx = None
	session.commit()


@app.route('/playlist/<name>/current', methods = ['GET'])
def current_playing_get(name):
	'''Handle current from a player's playlist'''
	expand  = get_expand()
	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404
	return jsonify({'current':player.current.serialize(expand)})


@app.route('/playlist/<name>/current', methods = ['PUT'])
def current_playing_set(name):
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

	current = data.get('current')
	if current is None:
		return 'You have to specify a song', 400

	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Player does not exist', 404

	try:
		player.current_idx = current
		session.commit()
	except:
		return 'Invalid data', 400
	return '', 201
