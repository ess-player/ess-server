#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Imports
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, abort, jsonify
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey, create_engine
from sqlalchemy.orm import sessionmaker, relationship, backref
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
import sys
import subprocess, json
from ess.db import get_session, Song, Artist, Album, Player, Playlist

# Create aplication
app = Flask(__name__)
app.config.from_object(__name__)

_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']

session = get_session()

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
		entries = session.query(Song)\
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
		entries = session.query(Song).order_by(Song.title).all()

	# Return the list of data
	return render_template('database.html', entries=entries, searchword=s)

# Deliver Songs to player
@app.route('/song/<int:song_id>')
def deliver_song(song_id):

	song = session.query(Song).filter(Song.id ==
			song_id).first()

	if song:
		[path,filename] = song.uri.rsplit('/' , 1)
		return send_from_directory(path, filename)

	abort(404)


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
	for player in session.query(Player):
		playerlist.append({
			'name'        : player.playername,
			'description' : player.description,
			'current'     : player.current})

	return  jsonify(player=playerlist)


@app.route('/player/<name>', methods = ['GET'])
def player_list(name):
	'''List player *name*.
	'''
	player = session.query(Player).filter(Player.playername==name).first()
	return jsonify({
			'name'        : player.playername,
			'description' : player.description,
			'current'     : player.current} \
					if player else {})


@app.route('/player/<name>', methods = ['DELETE'])
def player_delete(name):
	'''Delete player.
	'''
	player = session.query(Player).filter(Player.playername==name).first()
	if not player:
		return 'Do not exist', 404

	session.delete(player)
	session.commit()
	return '', 204

@app.route('/playlist/<name>', methods = ['GET'])
def playlist_list(name):
	'''List playlist from player *name*.
	'''

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



# Handle current from a player's playlist
@app.route('/playlist/<playername>/current', methods = ['GET'])
def current_playing_get(playername):
	player = session.query(Player).filter(Player.playername==playername).first()
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
