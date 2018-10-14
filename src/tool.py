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
		
def replace_key(dictionnary, *keys):
	for element in keys:
		try:
			dictionnary[element[0]] = dictionnary.pop(element[1])
		except:
			pass
	return dictionnary

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
	# TITLE
	title = {k: v for k, v in kwargs.items() if k in ['color', 'title', 'description', 'title_url', 'timestamp']}
	title = replace_key(title, ['url', 'title_url'])
	
	# AUTHOR
	author = {k: v for k, v in kwargs.items() if k in ['author', 'author_url', 'author_icon']}
	author = replace_key(author, ['name', 'author'], ['url', 'author_url'], ['icon_url', 'author_icon'])
	
	# Footer
	footer = {k: v for k, v in kwargs.items() if k in ['footer_text', 'footer_icon']}
	footer = replace_key(footer, ['text', 'footer_text'], ['icon_url', 'footer_icon'])
	
	# IMAGE & THUMBNAIL
	img = kwargs.get('image', None)
	thumbnail = kwargs.get('thumbnail', None)
	
	# FIELDS
	fields = kwargs.get('fields', [])
	
	EMB = discord.Embed(**title)
	EMB.set_author(**author)
	EMB.set_footer(**footer)
	if img:
		EMB.set_image(url=img)
	if thumbnail:
		EMB.set_thumbnail(url=thumbnail)
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