#!/opt/Botcord/.pyenv/bin/python
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
import discord.ext.commands as commands

import src.check as check
import src.tool as tool
from src.tool import log
from src.config.settings import client, TOKEN, MONITOR_MAIN
from src.config.version import VERSION

###########################################
#            	  CLIENT                  #
###########################################
# EVENTS
@client.event
async def on_ready():
	"""Preparation done"""
	await log('HAL 9000 is ready\nv{}'.format(VERSION), MONITOR_MAIN, time=True)
	
#@client.event
#async def on_command_error(ctx, Exception):
#	try:
#		channel = ctx.channel.name
#	except:
#		channel = 'DMChannel'
#	await log('Command raised in {} by {} (invoke : {} - {})'.format(channel, ctx.author.name, ctx.message.content, ctx.prefix), MONITOR_MAIN)
#	await log('Error : raised Exception : {}'.format(Exception), MONITOR_MAIN)

# HOOKS
#@client.before_invoke
#async def before_any_command(ctx):
#	"""Global hook before any command
#		>>> Désactivé for now
#	"""
#	if True:
#		return

# COMMANDS
@client.command()
@commands.check(check.check_is_me)
async def version(ctx):
	"""Return version"""
	await ctx.channel.send('HAL 9000 - version {}'.format(VERSION))
	
#@client.command()
#async def evl(ctx, module: str):
#	await log({t for t in asyncio.Task.all_tasks() if module in repr(t)}, MONITOR_MAIN)
	
@client.command()
@commands.check(check.check_is_me)
async def logout(ctx):
	"""Bot logs out"""
	
#	await log('{}'.format(['{} - {}'.format(role.name, role.id) for role in ctx.author.roles]), MONITOR_MAIN)
	await log('HAL 9000 logging out', MONITOR_MAIN, time=True)
	await client.close()
	
@client.command(name='extension')
@commands.check(check.check_is_me)
async def extension(ctx):
	"""Liste des Cogs actifs"""

	try:
		exts = tool.get_data('src/config/extension.json')
		if 'LIST' in exts:
			await ctx.channel.send('Extensions chargées: {}.'.format(', '.join(exts['LIST'])))
		else:
			await ctx.channel.send('Extensions chargées: aucune.')
	except Exception as error:
		await log('Erreur: extension.json impossible à charger.', MONITOR_MAIN)

@client.command(name='load')
@commands.check(check.check_is_me)
async def load(ctx, extension):
	"""Charge un Cog
	
	Extensions accessibles :
	- 'twitter'
	- 'moderation'
	- 'file'
	"""
	try:
		await client.load_extension(extension.lower())
		
		try:
			exts = tool.get_data('src/config/extension.json')
			if 'LIST' in exts:
				exts['LIST'] += [extension.lower()]
			else:
				exts['LIST'] = [extension.lower()]
			tool.set_data(exts, 'src/config/extension.json')
			await log('Cog: [{}] successfully loaded.'.format(extension.lower()), MONITOR_MAIN)
		
		except Exception as error:
			await log('Erreur: extension.json impossible à charger.', MONITOR_MAIN)
			
	except Exception as error:
		await log('{} cannot be loaded. [{}]'.format(extension.lower(), error), MONITOR_MAIN)
		
@client.command(name='unload')
@commands.check(check.check_is_me)
async def unload(ctx, extension):
	"""Enlève un Cog
	
	Extensions accessibles :
	- 'twitter'
	- 'moderation'
	- 'file'
	"""
	try:
		await client.unload_extension(extension.lower())
		
		try:
			exts = tool.get_data('src/config/extension.json')
			try:
				exts['LIST'].remove(extension.lower())
				tool.set_data(exts, 'src/config/extension.json')
				await log('Cog: [{}] successfully unloaded.'.format(extension.lower()), MONITOR_MAIN)
			except Exception as error:
				await log('Cog: {} was not found in extension.json'.format(extension.lower()), MONITOR_MAIN)
			
		except Exception as error:
			await log('Erreur: extension.json impossible à charger.', MONITOR_MAIN)
			
	except Exception as error:
		await log('{} cannot be unloaded. [{}]'.format(extension.lower(), error), MONITOR_MAIN)
	
###########################################
#                  RUN                    #
###########################################

async def main():
	EXTENSIONS = tool.get_data('src/config/extension.json')
	for extension in EXTENSIONS['LIST']:
		try:
			await client.load_extension(extension)
			print(f'{extension} loaded successfully')
		except:
			traceback.print_exc()
	
	try:
		await client.start(TOKEN)
	except:
		traceback.print_exc()

if __name__ == '__main__':
	asyncio.run(main())