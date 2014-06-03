#!/bin/env python
# -*- coding: utf-8 -*-

# Set default encoding to UTF-8
import sys
reload(sys)
sys.setdefaultencoding('utf8')

import subprocess, json
import os
import config
from ess.db import get_session, Media, Artist, Album

session = get_session()

def insert_media(path):
	# Use ffprobe to get ID3-Tags
	process = subprocess.Popen( [ 'ffprobe', '-show_format', '-show_streams',
		'-of', 'json', path ], stdout=subprocess.PIPE,
		stderr=subprocess.PIPE )
	[stdout, stderr] = process.communicate()
	if process.returncode:
		print ('>>> Warning: Could not read %s' % path)
		return 1
	try:
		data = json.loads(stdout)
	except UnicodeDecodeError:
		try:
			stdout = stdout.decode('latin-1')
			data = json.loads(stdout)
		except UnicodeDecodeError:
			try:
				import re
				stdout = re.sub(r'[^\w\s\d-.,;:!"§$]&"\'\{\}\[\]]', '_', stdout)
				data = json.loads(stdout)
			except:
				print 'Could not import %s' % path
				return

	tags = data['format'].get('tags') or {}

	if	data['format']['format_name'] not in config.FORMATS:
		print ('>>> Warning: Format not supported from %s' % path)
		return 1

	# Try to get the artist from db
	artist = None
	if tags.get('artist'):
		for a in session.query(Artist).filter(Artist.name==tags['artist']):
			artist = a
			break
		# Create new Artist if necessary
		if not artist:
			artist = Artist(name=tags['artist'])
			session.add(artist)

	# Try to get the album from db
	album = None
	if tags.get('album'):
		for a in session.query(Album).filter(Album.name==tags['album']).\
				filter(Album.artist==artist):
			album = a
			break
		# Create new album if necessary
		if not album:
			album = Album(name=tags['album'], artist=artist)
			session.add(album)

	media = Media(
			title=tags.get('title') or path.rsplit('/',1)[-1],
			date=tags.get('date'),
			tracknumber=tags.get('track'),
			path=path,
			genre=tags.get('genre'),
			duration=int(float(tags['duration'])) if tags.get('duration') else None,
			artist=artist,
			album=album
		)
	session.add(media)
	return media

def insert_files(path):
	for folder, subs, files in os.walk(path):
		for filename in files:
			insert_media(os.path.join(folder, filename))
	session.commit()
