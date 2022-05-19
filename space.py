import discord
from discord.ext import commands

import asyncio
import os
from datetime import time, timedelta
from datetime import datetime
from playwright.async_api import async_playwright

import src.check as check
import src.tool as tool
from src.tool import log
from src.config.settings import MONITOR_MODERATION as MONITOR

class Space(commands.Cog):
	def __init__(self, client):
		self.client	= client
		self.config = "src/space/config.json"
		self.src = "src/space/url.json"
		config = tool.get_data(self.config)
		self.spaceChannel = config["CHANNEL"]
		try:
			self.invite = config["INVITATION"]
		except:
			self.invite = {}
		self.hasFound = False
		
		self.dataUrl = []
		self.newUrl = []
		self.catch = {}
		try:
			self.msgID = config["MSG"]
		except:
			self.msgID = None
		self.timedelta = 600
		self.topic = "Space en cours : {}"
		self.message    = "\n:small_blue_diamond: \"{}\" ({} participants)\n  >> <{}>"
		self.endMessage = ":x: Le Space Twitter **{}** est maintenant terminé.\n{} personnes ont participé !"
		asyncio.get_event_loop().create_task(self.update())

	###########################################
	#            COROUTINE TASK               #
	###########################################

	#######
	# FUNC

	async def scraper(self, response):
		# Response scraper : only AudioSpaceById
		if ("AudioSpaceById" in response.url and not self.hasFound):
			responseData = await response.json()
			self.hasFound = True
			audioSpace = responseData['data']['audioSpace']
			url  = ""
			meta = {}

			if "errors" in responseData.keys() or not "metadata" in audioSpace.keys():
				# URL invalide
				pass

			else:
				# Clean url and avoid copies
				url = "https://twitter.com/i/spaces/{}".format(audioSpace['metadata']['rest_id'])
				meta["title"] = audioSpace['metadata']['title']
				meta["state"] = audioSpace['metadata']['state']

				if meta["state"] == 'Ended' or meta["state"] == 'TimedOut':
					meta["total_nb"] = audioSpace['metadata']['total_live_listeners']
				
				elif meta["state"] == 'Running':
					meta["nb"] = audioSpace['participants']['total']
				else:
					meta["nb"] = 0
			
			self.catch[url] = meta
			return

	async def update(self):
		"""
			TO DO :
			- classer les Space par popularité ?
			- Virer l'épingle
		"""
		await self.client.wait_until_ready()
		await asyncio.sleep(1)

		async with async_playwright() as p:
			browser = await p.chromium.launch()
			page    = await browser.new_page()
			page.on("response", self.scraper)

			while True:
				# Get all Space url
				self.dataUrl = tool.get_data(self.src)
				totalSpace = self.dataUrl + self.newUrl
				self.newUrl = []
				for space in (totalSpace):
					if (datetime.utcnow() - tool.str_to_date(space["timestamp"])).seconds < self.timedelta:
						continue
					try:
						await page.goto(space["url"])
					except Exception as e:
						print(e)
						pass
					self.hasFound = False
					for i in range(5000):
						await page.wait_for_timeout(5)
						if self.hasFound:
							break

				# Wait to ensure every response has been catched
				await asyncio.sleep(10)

				self.catch.pop('', None)
				if self.catch:
					channel = self.client.get_channel(self.spaceChannel)
					for url in self.catch:
						matchingSpace = [space for space in self.dataUrl if space["url"] == url]
						if matchingSpace:
							self.dataUrl = [item for item in self.dataUrl if item not in matchingSpace]
						space = self.catch[url]
						# Space ending
						if space["state"] == "Ended" or space["state"] == "TimedOut":
							await channel.send(self.endMessage.format(space["title"], space["total_nb"]))
						else:
							self.dataUrl.append({"state": space["state"], "url": url, "title": space["title"], "nb": space["nb"], "timestamp": str(datetime.utcnow())})
					# Suppression du message précédent
					self.catch = {}
					if self.msgID:
						try:
							message = await channel.fetch_message(self.msgID)
							await message.delete()
						except Exception as e:
							print(e)

					# Nouveau message pour les Space en cours
					if self.dataUrl:
						msgContent = "" 
						nbRunning = 0
						for space in self.dataUrl:
							if space["state"] == "Running":
								nbRunning += 1
								msgContent += "{}".format(self.message.format(space["title"], space["nb"], space["url"]))
						if nbRunning:
							msg = await channel.send(":microphone2: **SPACE TWITTER EN COURS**\n```python\n\"N'hésitez pas à partager le lien d'un Space Twitter dans ce salon !\"```:o: **DIRECT** - **{}** Space en cours :{}".format(nbRunning, msgContent))
							await msg.pin()
							self.msgID = msg.id
							config = tool.get_data(self.config)
							config["MSG"] = self.msgID
							tool.set_data(config, self.config)
					tool.set_data(self.dataUrl, self.src)

				await page.wait_for_timeout(5000)
				await asyncio.sleep(10)

				
	###########################################
	#                  CHECKS                 #
	###########################################
	
	# COG LOCAL CHECK
	async def cog_check(self, ctx):
		""" Test : modérateur only in right channel
		"""
		try:
			return check.check_is_me(ctx)
		except:
			return False

	###########################################
	#                COMMANDS                 #
	###########################################

	@commands.command(name='pin', pass_context=True)
	async def pin(self, ctx):
		""" Initialize le message pin
		"""
		if self.pinnedMessage is not None:
			return
		
		content = ":microphone2: **SPACE TWITTER EN COURS**\n```python\n\"N'hésitez pas à partager le lien d'un Space Twitter dans ce salon !\"```\n:white_small_square: Actuellement **0** Space en cours"
		configPath = "src/space/config.json"

		msg = await ctx.channel.send(content)
		await msg.pin()
		self.pinnedMessage = msg.id
		config = tool.get_data(configPath)
		config["PINNED"] = msg.id
		tool.set_data(config, configPath)
		
	###########################################
	#                  EVENTS                 #
	###########################################
    
    # ON MESSAGE
	@commands.Cog.listener()
	async def on_message(self, message):
		"""
			Search for Space Twitter
		"""
		# Only space channel...
		if (message.channel.id != self.spaceChannel):
			return
		
		# Avoid bot messages
		if (message.author.bot):
			if message.type == discord.MessageType.pins_add:
				await message.delete()
			return

		content   = message.content
		spaceUrls = [el for el in content.replace("\n", " ").split(" ") if "twitter.com/i/spaces/" in el]
		#... with space link within
		if not spaceUrls:
			return
		for i in range(len(spaceUrls)):
			if spaceUrls[i].endswith(".") or spaceUrls[i].endswith(","):
				spaceUrls[i] = spaceUrls[i][:-1]

		spaceUrls = list(set(spaceUrls))
		for url in spaceUrls:
			self.newUrl.append({"url": url, "timestamp": str(datetime.utcnow() - timedelta(seconds=self.timedelta)), "id": None})
			print("ADD URL : {}".format(url))

	# ON MEMBER JOIN
	@commands.Cog.listener()
	async def on_member_join(self, member):
		"""
			Check if Member has been invited with a link redirecting on the specific space channel

			get current invites, store

			on member join:
			get and store new invites
				check invites to see if one has incremented
				if one has, that's your invite, return

				else:
					if an invite is missing, it might be it was a limited use one or expired- add it to a list of things to return
					check vanity invite to see if it incremented
						if it did, return that
					poll audit log to see if any invites were created recently
						if one was, add that to things to return, return
			
			else :mystery: 
		
		"""
		channel 	= self.client.get_channel(self.spaceChannel)
		listInvites = await channel.invites()

		# Try except to ensure it works
		try:
			# Check for every invite url directing towards this channel
			for invite in listInvites:
				await log("Invitation sur le channel #{} : [{}] ({})".format(channel.name, invite.id, invite.uses), MONITOR)
				if invite.id in self.invite:
					# Check if number of uses changed
					if self.invite[invite.id] == invite.uses:
						continue
					# Log and update uses
					await log("{} used a link towards Space Twitter channel".format(member.name), MONITOR)

				# Update invite id / uses and save it
				self.invite[invite.id] = invite.uses
				config = tool.get_data(self.config)
				config["INVITE_ID"] = self.invite
				tool.set_data(config, self.config)
		except:
			pass

async def setup(client):
	await client.add_cog(Space(client))