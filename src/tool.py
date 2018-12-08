import discord
from datetime import datetime
import json
import asyncio
from src.config.settings import client

# PRINT EQUIVALENT (consola purposes)
async def log(text, monitor, time=False, file=None):
	await asyncio.sleep(0)
	if time:
		msg = '{} - {}'.format(str(datetime.today())[:-4], text)
	else:
		msg = text

	channel = client.get_channel(monitor)
	await channel.send(msg)
	return

# CONVERTER
def str_to_date(str_time):
	return datetime.strptime(str_time, '%Y-%m-%d %H:%M:%S.%f')

# HANDLING FILES
def get_data(outfile, default={}):
	try:
		with open(outfile) as outfile:
			data_file = json.load(outfile)
	except:
		# File doesn't exist yet
		data_file = default
		set_data(data_file, outfile)
	return data_file

def set_data(data_file, outfile):
	with open(outfile, 'w') as outfile:
		json.dump(data_file, outfile, indent=4)
		
# TWITTER MODULE FUNCTIONS
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
	
	# EMBED ELEMENTS
	EMB = discord.Embed(**title)
	try:
		EMB.set_author(**author)
	except:
		pass
	try:
		EMB.set_footer(**footer)
	except:
		pass
	
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

async def enhance_embed(ctx, embed, confirm=False, message=None, name='Default name', values=[], **kwargs):
	"""Dynamic embed messages
	
	OUTPUT
	------
	> message (with the embed, for editing purpose)
	> result (str or None) -> value confirmed by a tick, if it exists
	
	"""
	# Get pages length
	max_page = len(values)
	if max_page == 0:
		print('No values stored into the list')
		return message, None
	current_page = 1
	index = kwargs.get('index', None)
	left = u"\U00002B05"
	right = u"\U000027A1"
	tick = u"\U00002611"
	
	# Add field
	if index is not None:
		print('Index : {}'.format(index))
		embed.set_field_at(index, name=name, value=values[current_page-1], inline=kwargs.get('inline', True))
	else:
		index = len(embed.fields)
		embed.add_field(name=name, value=values[current_page-1], inline=kwargs.get('inline', True))
	
	# Edit or send message
	if not message:
		message = await ctx.channel.send(content=kwargs.get('content', None), 
									 	embed=embed.set_footer(text='Mettez une réaction pour changer de page. Page {} / {}'.format(current_page, max_page)))
	else:
		await message.edit(content=kwargs.get('content', None),
						   embed=embed.set_footer(text='Mettez une réaction pour changer de page. Page {} / {}'.format(current_page, max_page)))
	if max_page <= 1:
		return message, None
	
	# Init reactions
	for emoji in [left, tick, right]:
		if emoji == tick and not confirm:
			continue
		await message.add_reaction(emoji)
		
	# Wait for reaction replies
	def check(reaction: discord.Reaction, adder: discord.User):
		return adder == ctx.message.author and reaction.message.id == message.id and reaction.emoji in [left, right, tick]
	while True:
		try:
			reaction, adder = await client.wait_for('reaction_add', check=check, timeout=30)
			if reaction.emoji == left and current_page > 1:
				current_page -= 1
			elif reaction.emoji == right and current_page < max_page:
				current_page += 1
			elif reaction.emoji == tick and confirm:
				result = values[current_page-1]
				return message, result
			try:
				await message.remove_reaction(reaction.emoji, adder)
			except:
				print('Cannot delete reactions from other users')
			embed.set_field_at(index, name=name, value=values[current_page-1], inline=kwargs.get('inline', True))
			await message.edit(content=kwargs.get('content', None), 
							   embed=embed.set_footer(text='Mettez une réaction pour changer de page. Page {} / {}'.format(current_page, max_page)))
		except:
			return message, None
		
def extract_text(text):
	if text.find('[') == -1:
		inner_brack = None
		outer_brack = text
	else:
		inner_brack = text[text.find('[')+1:text.find(']')]
		outer_brack = text[text.find(']')+1::]
		if outer_brack == '':
			outer_brack = None
			
	return inner_brack, outer_brack