import discord
from datetime import datetime
import json

def str_to_date(str_time):
	return datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S.%f')

def get_data(outfile):
	try:
		with open(outfile) as outfile:
			data_file = json.load(outfile)
	except:
		# File doesn't exist yet
		data_file = {}
		set_data(data_file, outfile)
	return data_file

def set_data(data_file, outfile):
	with open(outfile, 'w') as outfile:
		json.dump(data_file, outfile, indent=4)

def set_field(**kwargs):
	return {k: v for k, v in kwargs.items() if k in ['name', 'value', 'inline']}
	
def set_embed(**kwargs):
	"""Retourne un EMBED
	
	Nb max de caractères par field : 1024
	Nb max de caractères : 6000
	
	KWARGS
	------
	- color
	- title
	- description
	- title_url
	- timestamp
	- author
	- author_url
	- author_icon
	- footer_text
	- footer_icon
	- image
	- thumbnail
	- fields : List
	"""
	title = {k: v for k, v in kwargs.items() if k in ['color', 'title', 'description', 'title_url', 'timestamp']}
	author = {k: v for k, v in kwargs.items() if k in ['author', 'author_url', 'author_icon']}
	footer = {k: v for k, v in kwargs.items() if k in ['footer_text', 'footer_icon']}
	img = kwargs.get('image', None)
	thumbnail = kwargs.get('thumbnail', None)
	fields = kwargs.get('fields', [])
	
	EMB = discord.Embed(**title)
	EMB.set_author(**author)
	EMB.set_footer(**footer)
	try:
		EMB.set_image(url=img)
	except:
		pass
	try:
		EMB.set_thumbnail(url=thumbnail)
	except:
		pass
	
	try:
		for element in fields:
			try:
				field = {k: v for k, v in element.items() if k in ['name', 'value', 'inline']}
				EMB.add_field(**field)
			except:
				continue
	except:
		pass
	return EMB

def 