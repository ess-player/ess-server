#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

# Imports
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, abort
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

# Handle players
@app.route('/player/', methods = ['GET', 'POST', 'DELETE'])
def handle_player():

	# Method POST
	if request.method == 'POST':
		_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']
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
		except ValueError as e:
			return e.message, 400

		playername  = data.get('playername')
		if not playername:
			return 'playername is missing', 400

		description = data.get('description')

		player = session.query(Player).filter(Player.playername==playername).first()
		if not player:
	 		player = Player(
					playername=playername,
					description=description)
			session.add(player)
			print('>>> Create new player: %s' % playername)
			session.commit()
			return 'Created', 201
		return 'Existed', 200

	if request.method == 'GET':
		playerlist = {}
		for player in session.query(Player):
			playerlist[player.playername] = {'description' : player.description,
					'current' : player.current}

		return  json.dumps(playerlist)

	if request.method == 'DELETE':
		_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']
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
		except ValueError as e:
			return e.message, 400

		playername  = data.get('playername')
		if not playername:
			return 'playername is missing', 400

		player = session.query(Player).filter(Player.playername==playername).first()
		if player:
			session.delete(player)
			session.commit()
			return 'Deleted', 200

		return 'Do not exist', 404

# Handle current from a player's playlist
@app.route('/playlist/<playername>/current', methods = ['GET', 'POST'])
def handle_current(playername):

	if request.method == 'GET':
		player = session.query(Player).filter(Player.playername==playername).first()
		if player:
			return json.dumps({'id' : player.current.id})
		return 'Do not exist', 404

	if request.method == 'POST':
		_formdata = ['application/x-www-form-urlencoded', 'multipart/form-data']
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
		except ValueError as e:
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
