#!/opt/Botcord/.pyenv/bin/python
# @author : Vyrrhus
"""
BOT DE MODÉRATION DU DISCORD INSOUMIS
- voir https://discordpy.readthedocs.io/en/rewrite/ -

FILE MAP
--------
MAIN >>>>>>>>>> main.py 		: 	gère les extensions & commandes de staff
				twitter.py		:	task pour suivre des tweets & commandes pour interagir
				
SRC >>>>>>>>>>> src/check.py	:	fonctions renvoyant un boolean pour vérifier certaines conditions
				src/tool.py		:	fonctions utilitaires pour réaliser des conversions, sérialiser, etc.
				src/tweetool.py	:	fonctions utilitaires spécifiques au module twitter.py
				
	CONFIG >>>>>>>>>>> src/config/settings.py : charge les fichiers json dans les variables associées
				
WIP
---
- vérifier qu'on ne peut pas modérer un autre bot (comment?)
- changer !help commande (decorators ?)
- assert toutes les fonctions?

"""
import discord
import datetime
import asyncio
import random
import src.check as check
import src.tool as tool
from src.tool import log
from src.config.settings import data, client

# GLOBAL SETTINGS
TOKEN = data['TOKEN']
VERSION = '1.0c'

# EXTENSIONS : loaded by default
extensions = ['twitter']

# STARTING EVENT
@client.event
async def on_ready():
	"""Preparation done"""
	await client.wait_until_ready()
	await log('HAL 9000 is ready', time=True)

@client.event
async def on_resumed():
	"""Client has resumed session"""
	await log('HAL 9000 has resumed session', time=True)
	
@client.before_invoke
async def before_any_command(ctx):
	"""Global hook pour interrompre les commandes (bot capricieux)
		>>> Désactivé for now
	"""
	if True:
		return
	ctx.global_lock = False
	probability = 0.01
	if random.random() > probability:
		return
	else:
		ctx.global_lock = True
		print('HAL TRIGGERED')

@client.command()
async def version(ctx):
	"""Return version"""
	await ctx.channel.send('HAL 9000 - version {}'.format(VERSION))
	
@client.command()
async def connexion(ctx):
	"""Return connection info"""
	await ctx.channel.send('Latency: {}\nIs_ready: {}'.format(client.latency, client.is_ready()))
	
@client.command()
async def evl(ctx, module: str):
	evl = {t for t in asyncio.Task.all_tasks() if module in repr(t)}
	print(evl)
	
@client.command()
async def close(ctx):
	"""Owner can log off"""
	if ctx.message.author.id == 246321888693977088:
		print('logout')
		await log('HAL 9000 logging out', time=True)
		await client.close()
	else:
		pass
	
###########################################
#            LOAD AND UNLOAD              #
###########################################
	
@client.command(name='load')
async def load(ctx, extension):
	"""Charge une extension : ?load <extension>
	
	Extensions accessibles :
	- 'twitter'
	"""
	if not check.is_staff(ctx.author):
		return
	try:
		client.load_extension(extension.lower())
		await log('Loaded {}'.format(extension.lower()))
	except Exception as error:
		await log('{} cannot be loaded. [{}]'.format(extension.lower(), error))
		
@client.command(name='unload')
async def unload(ctx, extension):
	"""Retire l'extension : ?unload <extension>
	
	Extensions accessibles :
	- 'twitter'
	"""
	if not check.is_staff(ctx.author):
		return
	try:
		client.unload_extension(extension.lower())
		await log('Unloaded {}'.format(extension.lower()))
	except Exception as error:
		await log('{} cannot be unloaded. [{}]'.format(extension.lower(), error))
	

###########################################
#                 ERROR                   #
###########################################

@client.event
async def on_command_error(ctx, Exception):
	try:
		channel = ctx.channel.name
	except:
		channel = 'DMChannel'
	await log('Command raised in {} by {} (invoke : {} - {})'.format(channel, ctx.author.name, ctx.message.content, ctx.prefix))
	await log('Error : raised Exception : {}'.format(Exception))
	
###########################################
#                  RUN                    #
###########################################

if __name__ == '__main__':
	for extension in extensions:
		try:
			client.load_extension(extension)
			print('{} loaded successfully'.format(extension))
		except Exception as error:
			print('{} cannot be loaded. [{}]'.format(extension, error))
			
client.run(TOKEN, reconnect=False)
