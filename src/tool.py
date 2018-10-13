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

def set_twitter_embed(titleheader=None, fields=[], footer=None):
	"""Retourne un embed"""
	if color:
		EMB = discord.Embed(color=color)
	else:
		EMB = discord.Embed()
	EMB.type = 'rich'
	if header:
		EMB.set_author(name=header['name'], icon_url=header['icon'])
		if 'thumbnail' in header:
			EMB.set_thumbnail(url=header['thumbnail'])
	for e in fields:
		if not 'inline' in e:
			e['inline'] = False
		if 'name' in e:
			EMB.add_field(name=e['name'], value=e['value'], inline=e['inline'])
		else:
			EMB.add_field(name='Texte : ', value=e['value'], inline=e['inline'])
	if footer:
		EMB.set_footer(text=footer['text'])
		if footer['time']:
			EMB.timestamp = footer['time']
		
	return EMB