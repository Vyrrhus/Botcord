# @author : Vyrrhus
"""
BOT DE MODÉRATION DU DISCORD INSOUMIS
- voir https://discordpy.readthedocs.io/en/rewrite/ -
"""

import os
import sys
import traceback
import discord
import asyncio
import logging

import src.check as check
import src.tool as tool
from src.tool import log
from src.config.settings import client, TOKEN, MONITOR_MAIN
from src.config.version import VERSION

###########################################
#            LOGGING SNIPPET              #
###########################################
"""Generate a single file called 'discord.log' for debug purposes"""
try:
	os.remove('logfile.log')
	os.rename('discord.log', 'logfile.log')
except:
	pass
# Logger
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

###########################################
#            	  CLIENT                  #
###########################################
# SETTINGS & EXTENSIONS

EXTENSIONS = ['moderation','file']

# EVENTS
@client.event
async def on_ready():
	"""Preparation done"""
	await log('HAL 9000 is ready\nv{}'.format(VERSION), MONITOR_MAIN, time=True)
	
@client.event
async def on_command_error(ctx, Exception):
	try:
		channel = ctx.channel.name
	except:
		channel = 'DMChannel'
	await log('Command raised in {} by {} (invoke : {} - {})'.format(channel, ctx.author.name, ctx.message.content, ctx.prefix), MONITOR_MAIN)
	await log('Error : raised Exception : {}'.format(Exception), MONITOR_MAIN)

# HOOKS
@client.before_invoke
async def before_any_command(ctx):
	"""Global hook before any command
		>>> Désactivé for now
	"""
	if True:
		return

# COMMANDS
@client.command()
async def version(ctx):
	"""Return version"""
	await ctx.channel.send('HAL 9000 - version {}'.format(VERSION))
	
@client.command()
async def evl(ctx, module: str):
	await log({t for t in asyncio.Task.all_tasks() if module in repr(t)}, MONITOR_MAIN)
	
@client.command()
async def close(ctx):
	"""Owner can log off"""
	if check.is_owner(ctx.author):
#		await log('{}'.format(['{} - {}'.format(role.name, role.id) for role in ctx.author.roles]), MONITOR_MAIN)
		await log('HAL 9000 logging out', MONITOR_MAIN, time=True)
		await client.logout()
	else:
		pass
	
@client.command(name='load')
async def load(ctx, extension):
	"""Charge une extension : ?load <extension>
	
	Extensions accessibles :
	- 'twitter'
	"""
	if not check.is_owner(ctx.author):
		return
	try:
		client.load_extension(extension.lower())
		await log('Loaded {}'.format(extension.lower()), MONITOR_MAIN)
	except Exception as error:
		await log('{} cannot be loaded. [{}]'.format(extension.lower(), error), MONITOR_MAIN)
		
@client.command(name='unload')
async def unload(ctx, extension):
	"""Retire l'extension : ?unload <extension>
	
	Extensions accessibles :
	- 'twitter'
	"""
	if not check.is_owner(ctx.author):
		return
	try:
		client.unload_extension(extension.lower())
		await log('Unloaded {}'.format(extension.lower()), MONITOR_MAIN)
	except Exception as error:
		await log('{} cannot be unloaded. [{}]'.format(extension.lower(), error), MONITOR_MAIN)
	
###########################################
#                  RUN                    #
###########################################

if __name__ == '__main__':
	for extension in EXTENSIONS:
		try:
			client.load_extension(extension)
			print('{} loaded successfully'.format(extension))
		except:
			traceback.print_exc()

try:
	client.run(TOKEN, reconnect=False)
except:
	traceback.print_exc()
