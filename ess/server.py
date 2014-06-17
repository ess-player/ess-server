# -*- coding: utf-8 -*-
'''
	ess.server
	~~~~~~~~~~

	This is the ess-server.

	:license: FreeBSD, see license file for more details.
'''

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Imports
from flask import Flask, request, redirect, url_for, render_template, jsonify, stream_with_context, Response
from sqlalchemy import or_, and_, desc, func
import json
from ess.db import get_session, Media, Artist, Album, Player, PlaylistEntry
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


@app.route('/')
def render():
	''' Render sites'''
	return render_template('layout.html')


@app.route('/search', methods = ['POST'])
def media_search():
	'''Full text search for media files.

	This method exposes an easy to use method for searching through the media
	library. It should be convenient to use for UIs wanting to have a general
	search interface.

	HTTP return codes:

		====  =====================  ======================
		Code  Status                 Meaning
		====  =====================  ======================
		200   OK                     Returned search result
		400   Bad Request            Review your request
		500   Internal Server Error  Please report this
		====  =====================  ======================

	cURL command to search for term “pathetic”::

		curl -f --request POST 'http://localhost:5001/search' \\
				-H 'Content-Type: application/json' --data '{"search":"pathetic"}'

	Search result::

		{
		  "media": [
			 {
				"album": {
				  "artist": 1,
				  "id": 1,
				  "name": "Lightning"
				},
				"artist": {
				  "id": 1,
				  "name": "Tamara Laurel"
				},
				"date": "2014",
				"duration": null,
				"genre": "(255)",
				"path": "/home/lars/music/sorted/Tamara Laurel - Lightning/05 - Tamara Laurel - Pathetic.mp3",
				"times_played": null,
				"title": "Pathetic",
				"tracknumber": 5
			 }
		  ]
		}

	Sending the data:

		The data have to be JSON encoded and should fill the whole request body.
		The content type of the request should be “application/json”. If
		necessary, the content type can also be “multipart/form-data” or
		“application/x-www-form-urlencoded” with the JSON data in the field
		called “data”. However, we very much like to discourage you from using
		the later method. While it should work in theory we are only using and
		testing the first method.

	'''
	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data
	try:
		data = json.loads(data)
	except Exception as e:
		return e.message, 400

	search = data.get('search')
	if not search:
		entries = get_session().query(Media)\
					.outerjoin(Album)\
					.outerjoin(Artist)
	else:
		searchlist = search.split()
		if not searchlist:
			entries = get_session().query(Media)\
					.outerjoin(Album)\
					.outerjoin(Artist)
		else:
			hs = '%' + searchlist[0]  + '%'
			entries = get_session().query(Media)\
						.outerjoin(Album)\
						.outerjoin(Artist)\
						.filter(or_(Media.title.like(hs),
									Media.genre.like(hs),
									Media.date.like(hs),
									Album.name.like(hs),
									Artist.name.like(hs)))

			for s in searchlist[1:]:
				hs = '%' + s + '%'
				entries  = entries\
						.filter(or_(Media.title.like(hs),
									Media.genre.like(hs),
									Media.date.like(hs),
									Album.name.like(hs),
									Artist.name.like(hs)))

	entries = entries.order_by(Artist.name)
	return jsonify({'media': [e.serialize(1) for e in entries]})


@app.route('/media/<int:media_id>')
def deliver_media(media_id):
	''' Deliver media to player '''

	media = get_session().query(Media).filter(Media.id ==
			media_id).first()

	if not media:
		return '', 404

	def generate():
		with open(media.path,'rb') as f:
			part = f.read(1024)
			while part:
				yield part
				part = f.read(128*1024)
 	response = Response(stream_with_context(generate()), mimetype='application/octet-stream')
	response.headers['content-length'] = os.path.getsize(media.path)
	return response


@app.route('/player', methods = ['POST'])
def player_register():
	'''Register a player. The data have to be JSON encoded.

	Example data to register a player “player01”::

		{"name":"player01", "description":"The first player"}

	cURL commend to register a player player01::

		curl -i --request POST -H 'Content-Type: application/json' \\
				--data '{"name":"player01"}'  "http://127.0.0.1:5001/player"

	Sending the data:

		The data have to be JSON encoded and should fill the whole request body.
		The content type of the request should be “application/json”. If
		necessary, the content type can also be “multipart/form-data” or
		“application/x-www-form-urlencoded” with the JSON data in the field
		called “data”. However, we very much like to discourage you from using
		the later method. While it should work in theory we are only using and
		testing the first method.

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

	session.query(PlaylistEntry).filter(PlaylistEntry.playername==name).delete()
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
	playlist = session.query(PlaylistEntry).order_by(PlaylistEntry.order)

	# Collect Media of playlist
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
	session.query(PlaylistEntry).delete()

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

	# Get media
	playlist = session.query(PlaylistEntry)\
			.filter(PlaylistEntry.playername==name)\
			.order_by(PlaylistEntry.order)

	# Collect media of playlist
	items = [e.serialize(expand) for e in playlist]

	return jsonify({name:items})


@app.route('/playlist/<name>', methods = ['PUT'])
def playlist_put(name):
	'''Post a playlist for the player *name*.
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

	# Get list of media_ids.
	media = data.get('list')
	if not media:
		return 'List of media is missing', 400

	# Delete old entries
	playlist = session.query(PlaylistEntry).filter(PlaylistEntry.playername==name).delete()

	# Create playlist
	for i in xrange(len(media)):
		session.add(PlaylistEntry(order=i, playername=name, media_id=media[i]))

	session.commit()
	return '', 201


@app.route('/playlist/<name>', methods = ['POST'])
def playlist_entry_add(name):
	'''Post a playerlist for the player *name*.
	'''
	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data

	try:
		data = json.loads(data)
	except:
		return 'Invalid data', 400

	session = get_session()
	try:
		(maximum_order,) = session.query(func.max(PlaylistEntry.order))\
				.filter(PlaylistEntry.playername==name).first()
		print maximum_order
		session.add(PlaylistEntry(order=maximum_order+1, playername=name,
			media_id=data['media']))
	except:
		return '', 400

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
	session.query(PlaylistEntry).filter(PlaylistEntry.playername==name).delete()
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
	playlist = session.query(PlaylistEntry).filter(PlaylistEntry.playername==name)
	entry1   = playlist.filter(PlaylistEntry.order==place).first()
	entry2   = playlist.filter(PlaylistEntry.order==place + direction).first()
	if not (entry1 and entry2):
		return 'entry not found', 404
	if player.current_idx == place:
		player.current_idx = player.current_idx + direction
	entry1.media_id, entry2.media_id = entry2.media_id, entry1.media_id
	session.commit()
	return '', 204


@app.route('/playlist/<name>/<int:place>', methods = ['DELETE'])
def playlist_entry_delete(name,place):
	'''Delete playlistentry from playlist on place place'''

	session = get_session()
	player = session.query(Player).filter_by(playername=name).first()
	if player.current_idx == place:
		player.current_idx = None
	session.query(PlaylistEntry).filter(and_(PlaylistEntry.playername==name,
			PlaylistEntry.order==place)).delete()

	# New order
	if player.current_idx > place:
		player.current_idx = player.current_idx - 1
	for e in	session.query(PlaylistEntry).filter(and_(PlaylistEntry.playername==name,
		PlaylistEntry.order>place)).order_by(PlaylistEntry.order):
		e.order = e.order-1
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
	return jsonify({'current':player.current.serialize(expand) if player.current else None})


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
		return 'You have to specify a media', 400

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

@app.route('/playlist/<name>/current/done', methods = ['GET'])
def current_done(name):
	expand  = get_expand()
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404
	if not player.current:
		return 'Current was not set', 400
	player.current.media.times_played = + 1
	if session.query(PlaylistEntry).filter(PlaylistEntry.playername==name,
			PlaylistEntry.order==player.current_idx + 1).first():
		player.current_idx += 1
	else:
		player.current_idx = None
	session.commit()
	return '', 200

