import discord
import asyncio
from discord.ext import commands

import src.check as check
import src.tool as tool
from src.tool import log
from src.config.settings import MONITOR_MAIN as MNT

import os

class File:
	def __init__(self, client):
		self.client = client
	
	
	###########################################
	#                  CHECKS                 #
	###########################################
	
	# LOCAL CHECK
	async def __local_check(self, ctx):
		""" Les commands de ce cog ne peuvent être utilisées que par un staff ou l'owner
		"""
		try:
			staff_role = tool.get_data('src/config/id.json')['ROLE']['STAFF']
			if check.is_owner(ctx.author):
				return True
			return check.is_role(ctx.author, staff_role)
		except:
			await log('File local check failed', MNT)
			return False
		
	###########################################
	#                COMMANDS                 #
	###########################################
	
	# LIST FILES IN DIRECTORY
	@commands.command(name='listdir', pass_context=True)
	async def listdir(self, ctx, path):
		""" Give all files within directory and sub-directories
		"""
		try:
			files = os.scandir(path)
		except:
			await log('os.scandir() failed', MNT)
			return
		result = ''
		for element in files:
			if element.is_dir():
				result += ':file_folder: `{}/{}`\n'.format(path, element.name)
			else:
				result += ':page_facing_up: `{}/{}`\n'.format(path, element.name)
				
		await log(result, MNT)
		return
	
	@commands.command(name='download', pass_context=True)
	async def download(self, ctx, file_path):
		""" Send the file specified to the current channel
		"""
		try:
			await ctx.channel.send("Fichier : ", file=discord.File('{}'.format(file_path)))
		except:
			await ctx.channel.send("L'envoi du fichier a échoué")
		return
	
	@commands.command(name='upload', pass_context=True)
	async def upload(self, ctx, path):
		""" Put the attached file to the specified path
		"""
		file = ctx.message.attachments
		for element in file:
			try:
				await element.save(path)
			except:
				await log('Something went wrong while uploading the file', MNT)
				pass
		return
	
	@commands.command(name='remove', pass_context=True)
	async def remove(self, ctx, path):
		""" Remove the file at the specified path
		"""
		try:
			os.remove(path)
		except:
			pass
		
		return
	
	@commands.command(name='mkdir', pass_context=True)
	async def mkdir(self, ctx, path):
		""" Create a new directory at the specified path
		"""
		try:
			os.mkdir(path)
		except:
			await log('Something went wrong while creating the directory', MNT)
			
		return
	
	@commands.command(name='rmdir', pass_context=True)
	async def rmdir(self, ctx, path):
		""" Remove an empty directory at specified path
		"""
		try:
			os.rmdir(path)
		except:
			pass
		
		return
	
def setup(client):
	client.add_cog(File(client))
