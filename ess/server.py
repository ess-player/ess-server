# -*- coding: utf-8 -*-
'''
	ess.server
	~~~~~~~~~~

	This is the ess-server.

	:license: FreeBSD, see license file for more details.
'''


# Imports
# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')
from flask import Flask, request, redirect, url_for, render_template, jsonify, stream_with_context, Response
from sqlalchemy import or_, and_, desc, func
import json
from ess.db import get_session, Media, Artist, Album, Player, PlaylistEntry
import os.path
from time import sleep


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

	URL parameters:

		=========  =======  ====================  ================================
		Parameter  Default  Possible values       Meaning
		=========  =======  ====================  ================================
		limit      20       Positive Integer      Number of returned media entries
		offset     0        Positive Integer      Offset of Result
		order      artist   artist, album, title  Order of Result
		order_dir  asc      asc, desc             Ascending or descending order
		=========  =======  ====================  ================================

	HTTP return codes:

		====  =====================  ======================
		Code  Status                 Meaning
		====  =====================  ======================
		200   OK                     Returned search result
		400   Bad Request            Review your request
		500   Internal Server Error  Please report this
		====  =====================  ======================

	cURL command to search for term “pathetic” with limit=1, offset=0,
	order=title and order_dir=asc::

		curl -f --request POST 'http://localhost:5001/search?limit=1&order=title' \\
				-H 'Content-Type: application/json' --data '{"search":"pathetic"}'

	Search result::

		{
		  "count": 12,
		  "limit": 1,
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
		  ],
		  "offset":0,
		  "order":"title",
		  "order_dir":"asc"
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

	try:
		limit = int(request.args.get('limit', 20))
	except:
		limit = 20
	try:
		offset = int(request.args.get('offset', 0))
	except:
		offset = 0
	order = request.args.get('order', 'artist')
	if not order in ['artist', 'album', 'title']:
		order = 'artist'
	order_dir = request.args.get('order_dir', 'asc')
	if not order_dir in ['asc', 'desc']:
		order_dir = 'asc'

	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data
	try:
		data = json.loads(data)
	except Exception as e:
		return '', 400

	search = data.get('search')
	searchlist = (search or '').split()
	entries = get_session().query(Media)\
			.outerjoin(Album)\
			.outerjoin(Artist)
	for s in searchlist:
		hs = '%' + s + '%'
		entries  = entries\
				.filter(or_(Media.title.like(hs),
							Media.genre.like(hs),
							Media.date.like(hs),
							Album.name.like(hs),
							Artist.name.like(hs)))

	count = entries.count()

	if order_dir == 'desc':
		if order == 'album':
			entries = entries.order_by(Album.name.desc())
		elif order == 'title':
			entries = entries.order_by(Media.title.desc())
		else:
			entries = entries.order_by(Artist.name.desc())
	else:
		if order == 'album':
			entries = entries.order_by(Album.name)
		elif order == 'title':
			entries = entries.order_by(Media.title)
		else:
			entries = entries.order_by(Artist.name)

	entries = entries.offset(offset)
	if limit:
		entries = entries.limit(limit)

	return jsonify({'media'     : [e.serialize(1) for e in entries],
						 'offset'    : offset,
						 'count'     : count,
						 'limit'     : limit,
						 'order'     : order,
						 'order_dir' : order_dir})


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

	This method exposes an easy to use method for register a new player. It
	should be called when a new player is initialize.

	HTTP return codes:

		====  =====================  =============================
		Code  Status                 Meaning
		====  =====================  =============================
		201   Created                Registered Player
		204   No Content             Player was already registered
		400   Bad Request            Review your request
		500   Internal Server Error  Please report this
		====  =====================  =============================

	Example data to register a player “player01”::

		{"name":"player01", "description":"The first player"}

	cURL command to register a player player01::

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
		return '', 400

	# Get the name of the player. It may not be empty.
	playername = data.get('name')
	if not playername:
		return '', 400

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
	session.commit()
	return '', 201


@app.route('/player', methods = ['GET'])
def player_list_all():
	'''List all registered players. The output is JSON encoded.

	This method exposes an easy to use method for listing all registered
	players. It should be convenient to use for UIs wanting to know all
	registered players.

	HTTP return codes:

		====  =====================  ===================================
		Code  Status                 Meaning
		====  =====================  ===================================
		200   OK                     Returned list of registered players
		500   Internal Server Error  Please report this
		====  =====================  ===================================

	cURL command to list all players::

		curl -i http://127.0.0.1:5001/player

	Example for a result::

		{
			"player": [
				{
					"current": 3,
					"description": "The first player",
					"playername": "player01"
				},
				{
					"current": null,
					"description": "The second player",
					"playername": "player02"
				}
			]
		}
	'''
	session = get_session()
	expand  = get_expand()
	playerlist = [p.serialize(expand) for p in session.query(Player)]
	return  jsonify(player=playerlist)


@app.route('/player/<name>', methods = ['GET'])
def player_list(name):
	'''List player *name*. The Output is JSON encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		200   OK                     Return playered
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to list player01::

		curl -i http://127.0.0.1:5001/player/player01

	Example of a result::

		{
			"current": 3,
			"description": "The first player",
			"playername": "player01"
		}
	'''
	session = get_session()
	expand  = get_expand()

	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404
	return jsonify(player.serialize(expand))


@app.route('/player/<name>', methods = ['DELETE'])
def player_delete(name):
	'''Delete player *name*.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		204   No Content             Player deleted
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to delete “player01“::

		curl --request DELETE http://127.0.0.1:5001/player/player01
	'''
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	session.query(PlaylistEntry).filter(PlaylistEntry.playername==name).delete()
	session.delete(player)
	session.commit()
	return '', 204


@app.route('/playlist', methods = ['GET'])
def playlist_list_all():
	'''List the playlist of all registered players. The output is JSON encoded.

	HTTP return codes:

		====  =====================  ==================
		Code  Status                 Meaning
		====  =====================  ==================
		200   OK                     Returned playlists
		500   Internal Server Error  Please report this
		====  =====================  ==================

	cURL command to list all playlists::

		curl -i http://127.0.0.1:5001/playlist

	Example of a result::

		{
			"player01": [
				{
					"media": 2,
					"order": 0,
					"player": "player01"
				},
				{
					"media": 4,
					"order": 1,
					"player": "player01"
				},
				{
					"media": 6,
					"order": 2,
					"player": "player01"
				}
			],
			"player02": [
				{
					"media": 3,
					"order": 0,
					"player": "player02"
				},
				{
					"media": 4,
					"order": 1,
					"player": "player02"
				}
			]
		}
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
	'''Delete all playlists.

	HTTP return codes:

		====  =====================  ==================
		Code  Status                 Meaning
		====  =====================  ==================
		204   No Content             Playlists deleted
		500   Internal Server Error  Please report this
		====  =====================  ==================

	cURL command to delete all playlists::

		curl --request DELETE http://127.0.0.1:5001/playlist
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
	'''List the playlist of player *name*. The output is JSON encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		200   OK                     Returned playlist
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to list playlist of “player01“::

		curl -i http://127.0.0.1:5001/playlist/player01

	Example of a result::

		{
			"player01": [
				{
					"media": 2,
					"order": 0,
					"player": "player01"
				},
				{
					"media": 4,
					"order": 1,
					"player": "player01"
				},
				{
					"media": 6,
					"order": 2,
					"player": "player01"
				}
			]
		}
	'''
	expand  = get_expand()
	session = get_session()

	# Get Player and Current
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	# Get media
	playlist = session.query(PlaylistEntry)\
			.filter(PlaylistEntry.playername==name)\
			.order_by(PlaylistEntry.order)

	# Collect media of playlist
	items = [e.serialize(expand) for e in playlist]

	return jsonify({name:items})


@app.route('/playlist/<name>', methods = ['PUT'])
def playlist_put(name):
	'''Put a playlist for the player *name*. The data have to be
	JSON encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		201   Created                Created playlist
		400   Bad Request            Review your request
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	Example data to put a playlist::

		{"media":[3,5,7,1]}

	cURL command to put a playlist for “player01“::

		curl -i --request PUT -H 'Content-Type: application/json' \\
				--data '{"media":[3,5,7,1]}' "http://127.0.0.1:5001/playlist/player01"

	Sending the data:

		The data have to be JSON encoded and should fill the whole request body.
		The content type of the request should be “application/json”. If
		necessary, the content type can also be “multipart/form-data” or
		“application/x-www-form-urlencoded” with the JSON data in the field
		called “data”. However, we very much like to discourage you from using
		the later method. While it should work in theory we are only using and
		testing the first method.
	'''
	session = get_session()

	# Check if player exists
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	data = request.form.get('data') \
			if request.content_type in _formdata \
			else request.data

	try:
		data = json.loads(data)
	except:
		return '', 400

	# Get list of media_ids.
	media = data.get('list')
	if not media:
		return '', 400

	# Delete old entries
	playlist = session.query(PlaylistEntry).filter(PlaylistEntry.playername==name).delete()

	# Create playlist
	for i in xrange(len(media)):
		session.add(PlaylistEntry(order=i, playername=name, media_id=media[i]))

	session.commit()
	return '', 201


@app.route('/playlist/<name>', methods = ['POST'])
def playlist_entry_add(name):
	'''Add an entry to the playlist of the player *name*. The data have to be
	JSON encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		201   Created                Created playlist
		400   Bad Request            Review your request
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	Example data to post an entry::

		{"media":3}

	cURL command to post an entry to the playlist of “player01“::

		curl -i --request POST -H 'Content-Type: application/json' \\
				--data '{"media":3}' "http://127.0.0.1:5001/playlist/player01"

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
	except:
		return '', 400

	session = get_session()

	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	try:
		(maximum_order,) = session.query(func.max(PlaylistEntry.order))\
				.filter(PlaylistEntry.playername==name).first()
		session.add(PlaylistEntry(order=maximum_order+1, playername=name,
			media_id=data['media']))
	except:
		return '', 400

	session.commit()
	return '', 201


@app.route('/playlist/<name>', methods = ['DELETE'])
def playlist_delete(name):
	'''Delete playlist of player *name*.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		204   No Content             Playlist deleted
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to delete playlist of “player01“::

		curl --request DELETE http://127.0.0.1:5001/playlist/player01
	'''
	session = get_session()
	# Unset current
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404
	player.current_idx = None
	# Delete playlists
	session.query(PlaylistEntry).filter(PlaylistEntry.playername==name).delete()
	session.commit()

	return '', 204


@app.route('/playlist/<name>/<int:place>/up')
@app.route('/playlist/<name>/<int:place>/down')
def playlist_entry_move(name,place):
	'''Move entry on order *place* up or down in the playlist of player *name*

	HTTP return codes:

		====  =====================  ==============================
		Code  Status                 Meaning
		====  =====================  ==============================
		204   No Content             Changed order
		404   Not Found              Player or entries do not exist
		500   Internal Server Error  Please report this
		====  =====================  ==============================

	cURL command to move entry “1“ of the playlist of “player01“ up and down::

		curl http://127.0.0.1:5001/playlist/player01/1/up

		curl http://127.0.0.1:5001/playlist/player01/1/down
'''

	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	direction = 1 if request.path.endswith('/down') else -1

	# Get playlist and entries
	playlist = session.query(PlaylistEntry).filter(PlaylistEntry.playername==name)
	entry1   = playlist.filter(PlaylistEntry.order==place).first()
	entry2   = playlist.filter(PlaylistEntry.order==place + direction).first()
	if not (entry1 and entry2):
		return '', 404
	if player.current_idx == place:
		player.current_idx = player.current_idx + direction
	entry1.media_id, entry2.media_id = entry2.media_id, entry1.media_id
	session.commit()
	return '', 204


@app.route('/playlist/<name>/<int:place>', methods = ['DELETE'])
def playlist_entry_delete(name,place):
	'''Delete entry on order *place* of player *name*'s playlist.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		204   No Content             Deleted entry
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to delete entry “3“ of “player01“::

		curl --request DELETE http://127.0.0.1:5001/playlist/player01/3
	'''

	session = get_session()
	player = session.query(Player).filter_by(playername=name).first()
	if not player:
		return '', 404
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
	'''Unset current played sing from the player *name*.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		200   OK                     Deleted current
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to unset current of “player01“::

		curl --request DELETE http://127.0.0.1:5001/playlist/player01/current
	'''
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404
	player.current_idx = None
	session.commit()


@app.route('/playlist/<name>/current', methods = ['GET'])
def current_playing_get(name):
	'''Get current played song from the player *name*. The Output is JSON
	encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		200   OK                     Returned current
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to get current of “player01“::

		curl -i http://127.0.0.1:5001/playlist/player01/current

	Example of a result::

		{
			"current": {
				"media": 7,
				"order": 3,
				"player": "player01"
			}
		}
'''
	expand  = get_expand()
	session = get_session()
	# Get player
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404
	return jsonify({'current':player.current.serialize(expand) if player.current else None})


@app.route('/playlist/<name>/current', methods = ['PUT'])
def current_playing_set(name):
	''' Set current played song from the player *name*. The data have to be JSON encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		201   Created                Set current
		400   Bad Request            Review your request
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	Example data to set current to the entry “3“::

		{"current":3}

	cURL command to set current to the entry “3“ from “player01”'s playlist::

		curl -i --request PUT -H 'Content-Type: application/json' \\
				--data '{"current":3}' "http://127.0.0.1:5001/playlist/player01/current"

	Sending the data:

		The data have to be JSON encoded and should fill the whole request body.
		The content type of the request should be “application/json”. If
		necessary, the content type can also be “multipart/form-data” or
		“application/x-www-form-urlencoded” with the JSON data in the field
		called “data”. However, we very much like to discourage you from using
		the later method. While it should work in theory we are only using and
		testing the first method.
	'''
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/json']:
		return '' % type, 400
	try:
		data = json.loads(data)
	except Exception as e:
		return '', 400

	current = data.get('current')
	if current is None:
		return '', 400

	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	try:
		player.current_idx = current
		session.commit()
	except:
		return '', 400
	return '', 201


@app.route('/playlist/<name>/current/done', methods = ['GET'])
def current_done(name):
	'''Let the server know, that the current song was played successful.

	HTTP return codes:

		====  =====================  ==========================================
		Code  Status                 Meaning
		====  =====================  ==========================================
		204   No Content             Server knows current was played successful
		400   Bad Request            Review your request
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  ==========================================

	cURL command to inform server about current played song of “player01“::

		curl http://127.0.0.1:5001/playlist/player01/current/done
	'''
	expand  = get_expand()
	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404
	if not player.current:
		return '', 400
	player.current.media.times_played = + 1
	if session.query(PlaylistEntry).filter(PlaylistEntry.playername==name,
			PlaylistEntry.order==player.current_idx + 1).first():
		player.current_idx += 1
	else:
		player.current_idx = None
	session.commit()
	return '', 204



@app.route('/command/<name>', methods = ['GET'])
def command_get(name):
	'''Get command for the player *name*. The Output is JSON
	encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		200   OK                     Returned command
		200   No Content             No Command set
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	cURL command to get current of “player01“::

		curl -i http://127.0.0.1:5001/command/player01

	Example of a result::

		{"command": "next"}
	'''
	for i in range(300):
		session = get_session()
		player = session.query(Player).filter(Player.playername==name).first()
		if not player:
			return '', 404
		if	player.command:
			command = player.command
			player.command = None
			session.commit()
			return jsonify({'command':command}), 200
		session.close()
		sleep(0.1)
	return '', 204


@app.route('/command/<name>', methods = ['PUT'])
def command_set(name):
	'''Set command for the player *name*. The data have to be JSON encoded.

	HTTP return codes:

		====  =====================  =====================
		Code  Status                 Meaning
		====  =====================  =====================
		201   Created                Set command
		400   Bad Request            Review your request
		404   Not Found              Player does not exist
		500   Internal Server Error  Please report this
		====  =====================  =====================

	Example data to set command “pause“::

		{"command":"pause"}

	cURL command to set command “pause“ for “player01”::

		curl -i --request PUT -H 'Content-Type: application/json' \\
				--data '{"command":"pause"}' "http://127.0.0.1:5001/command/player01"

	Sending the data:

		The data have to be JSON encoded and should fill the whole request body.
		The content type of the request should be “application/json”. If
		necessary, the content type can also be “multipart/form-data” or
		“application/x-www-form-urlencoded” with the JSON data in the field
		called “data”. However, we very much like to discourage you from using
		the later method. While it should work in theory we are only using and
		testing the first method.
	'''
	if request.content_type in _formdata:
		data = request.form['data']
		type = request.form['type']
	else:
		data = request.data
		type = request.content_type
	if not type in ['application/json']:
		return '' % type, 400
	try:
		data = json.loads(data)
	except Exception as e:
		return '', 400

	command = data.get('command')
	if command is None:
		return '', 400

	session = get_session()
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return '', 404

	player.command = command
	session.commit()
	return '', 204
