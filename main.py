# @author : Vyrrhus
"""
BOT DE MODÉRATION DU DISCORD INSOUMIS
- voir https://discordpy.readthedocs.io/en/rewrite/ -

FILE MAP
--------
MAIN >>>>>>>>>> bot.py 			 : 	gère les extensions & commandes de staff

EXTENSIONS >>>>	moderation.py 	 :	commandes & events pour la modération
				miscellaneous.py :	commandes utilitaires (principalement pour salons vocaux)
				pin.py			 :	commandes & events pour automatiser les unpin dans le temps
				twitter.py 		 :  commandes pour hook en continu certains tweets
				
CLASS >>>>>>>>> src/action.py	 :	classe ACTION (infos relatives à la modération)
				src/note.py		 :	classe NOTE (idem)
			
FUNCTION >>>>>>	src/check.py	 :	fonctions renvoyant un boolean pour vérifier certaines conditions
				src/tools.py	 :	fonctions utilitaires pour sérialiser / désérialiser des fichiers
				
FILES >>>>>>>>> src/config/settings.py	:	charge le fichier json associé dans une variable data
				src/config/settings.json:	contient les paramètres du bot (ID, tokens, texte, etc.)
				src/data/counter.txt	:	compteur du nombre d'objets de ACTION
				src/data/log			:	binary file contenant un dict des ACTION par numéro
				src/data/member			:	binary file contenant un dict des numéros d'actions & notes par ID

WIP
---
- supprimer !close
- rajouter les commandes staff pour modifier settings.json
- commande !clearnote
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

from discord.ext.commands import Bot
from src.config.settings import data
#from src.action import ACTION
#from src.note import NOTE

# GLOBAL SETTINGS
TOKEN = data['TOKEN']
BOT_PREFIX = (data['PREFIX'])
client = Bot(command_prefix = BOT_PREFIX)

# EXTENSIONS : loaded by default
extensions = ['twitter']

# STARTING EVENT
@client.event
async def on_ready():
	"""Bot fonctionnel"""
	print('HAL 9000 connecté on {}'.format(datetime.datetime.utcnow().strftime("%d-%m %H:%M:%S")))

@client.before_invoke
async def before_any_command(ctx):
	"""Global hook pour interrompre les commandes (bot capricieux)"""
	
	ctx.global_lock = False
	probability = 0.01
	if random.random() > probability:
		return
	else:
		ctx.global_lock = True
		print('HAL TRIGGERED')

	
@client.command()
async def close(ctx):
	if ctx.message.author.id == 246321888693977088:
		# Saving data
		tool.set_data(data, 'src/config/settings.json')
		print('logout')
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
	- 'moderation'
	- 'miscellaneous'
	- 'pin'
	- 'twitter'
	"""
	if not check.is_staff(ctx.author):
		return
	try:
		client.load_extension(extension.lower())
		print('Loaded {}'.format(extension.lower()))
	except Exception as error:
		print('{} cannot be loaded. [{}]'.format(extension.lower(), error))
		
@client.command(name='unload')
async def unload(ctx, extension):
	"""Retire l'extension : ?unload <extension>
	
	Extensions accessibles :
	- 'moderation'
	- 'miscellaneous'
	- 'pin'
	- 'twitter'
	"""
	if not check.is_staff(ctx.author):
		return
	try:
		client.unload_extension(extension.lower())
		print('Unloaded {}'.format(extension.lower()))
	except Exception as error:
		print('{} cannot be unloaded. [{}]'.format(extension.lower(), error))
	

###########################################
#                 ERROR                   #
###########################################

@client.event
async def on_command_error(ctx, Exception):
	try:
		channel = ctx.channel.name
	except:
		channel = 'DMChannel'
	print('Command raised in {} by {} (invoke : {} - {})'.format(channel, ctx.author.name, ctx.message.content, ctx.prefix))
	print('Error : raised Exception : {}'.format(Exception))
	
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
			
client.run(TOKEN)
