import discord
import asyncio
from discord.ext import commands

import src.check as check
import src.tool as tool
from src.tool import log
from src.config.settings import MONITOR_MAIN as MNT

import os

class File(commands.Cog):
	"""All files commands : remove & add directories, files. Upload and download them."""
	def __init__(self, client):
		self.client = client
	
	###########################################
	#                  CHECKS                 #
	###########################################
	
	# LOCAL CHECK
	async def cog_check(self, ctx):
		""" Les commands de ce cog ne peuvent être utilisées que par l'owner
		"""
		try:
			return check.is_owner(ctx.author)
		except:
			await log('File local check failed', MNT)
			return False
		
	###########################################
	#                COMMANDS                 #
	###########################################

	@commands.command(name='command_test', pass_context=True)
	@commands.is_owner()
	async def _command(ctx, *command):
		await log(f"Commande exécutée : {' '.join(command)}", MNT)
		os.system(' '.join(command))

	
	# LIST FILES IN DIRECTORY
	@commands.command(name='ls', pass_context=True)
	async def listdir(self, ctx, path):
		""" Repository list
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
		""" Download file
		"""
		try:
			await ctx.channel.send("Fichier : ", file=discord.File('{}'.format(file_path)))
		except:
			await ctx.channel.send("L'envoi du fichier a échoué")
		return
	
	@commands.command(name='upload', pass_context=True)
	async def upload(self, ctx, path):
		""" Upload file
		"""
		file = ctx.message.attachments
		for element in file:
			try:
				await element.save(path)
			except:
				await log('Something went wrong while uploading the file', MNT)
				pass
		return
	
	@commands.command(name='rm', pass_context=True)
	async def remove(self, ctx, path):
		""" Remove file
		"""
		try:
			os.remove(path)
		except:
			pass
		
		return
	
	@commands.command(name='mkdir', pass_context=True)
	async def mkdir(self, ctx, path):
		""" Create new dir
		"""
		try:
			os.mkdir(path)
		except:
			await log('Something went wrong while creating the directory', MNT)
			
		return
	
	@commands.command(name='rmdir', pass_context=True)
	async def rmdir(self, ctx, path):
		""" Remove empty dir
		"""
		try:
			os.rmdir(path)
		except:
			pass
		
		return
	
async def setup(client):
	await client.add_cog(File(client))