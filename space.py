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
# from src.config.settings import MONITOR_SPACE as MONITOR

class Space(commands.Cog):
	def __init__(self, client):
		id = tool.get_data("src/space/config.json")
		self.client	= client
		self.src = "src/space/url.json"
		self.hasFound = False
		self.spaceChannel = id["CHANNEL"]
		self.pinnedMessage = id["PINNED"]
		self.dataUrlIni = []
		self.dataUrlEnd = []
		self.addUrl = []
		self.timedelta = 300
		self.timestampReached = False
		self.topic = "Space en cours : {}"
		self.message    = ":o: **DIRECT**   :  **{}**\nSuivez le Space twitter avec {} autres personnes\n:fast_forward: {}"
		self.endMessage = ":x: Le Space Twitter **{}** est maintenant terminé.\n{} personnes ont participé !"
		asyncio.get_event_loop().create_task(self.update())

	###########################################
	#            COROUTINE TASK               #
	###########################################

	#######
	# FUNC

	async def scraper(self, response):
		"""
			TO DO:
			- handle errors if space doesn't exist
		"""
		# Response scraper : only AudioSpaceById
		if ("AudioSpaceById" in response.url and not self.hasFound):
			responseData = await response.json()
			self.hasFound = True
			audioSpace = responseData['data']['audioSpace']

			if "errors" in responseData.keys() or not "metadata" in audioSpace.keys():
				# URL invalide
				print('Space url invalide')
				return

			# Evite les doublons
			cleanUrl = "https://twitter.com/i/spaces/{}".format(audioSpace['metadata']['rest_id'])
			if cleanUrl in [el["url"] for el in self.dataUrlEnd]:
				return

			# Fin du Space, update le fichier initial (else "Running")
			if audioSpace['metadata']['state'] == 'Ended':
				print("Space ended")
				metadata = {"title": audioSpace['metadata']['title'], "nb": audioSpace['metadata']['total_participated']}
				await self.client.get_channel(self.spaceChannel).send(self.endMessage.format(metadata["title"], metadata["nb"]))
				await self.client.get_channel(self.spaceChannel).edit(topic=None)

			# Space en cours
			else:
				print("Space running")
				self.dataUrlEnd.append({"url": cleanUrl, "timestamp": str(datetime.utcnow())})
				metadata = {"title": audioSpace['metadata']['title'], "nb": audioSpace['participants']['total']}
				await self.client.get_channel(self.spaceChannel).send(self.message.format(metadata["title"], metadata["nb"], cleanUrl))
				await self.client.get_channel(self.spaceChannel).edit(topic=self.topic.format(cleanUrl))

	async def update(self):
		await self.client.wait_until_ready()
		await asyncio.sleep(1)

		async with async_playwright() as p:
			browser = await p.chromium.launch()
			page    = await browser.new_page()
			page.on("response", self.scraper)

			while True:
				# Get all Space url
				self.dataUrlIni = tool.get_data(self.src)
				self.dataUrlEnd = []
				for space in (self.dataUrlIni + self.addUrl):
					if (datetime.utcnow() - tool.str_to_date(space["timestamp"])).seconds < self.timedelta:
						self.dataUrlEnd.append(space)
						continue

					self.timestampReached = True
					self.hasFound = False
					await page.goto(space["url"])
					for i in range(5000):
						await page.wait_for_timeout(1)
						if self.hasFound:
							break
				
				self.addUrl = []

				if self.timestampReached:
					self.timestampReached = False
					tool.set_data(self.dataUrlEnd, self.src)

					if self.pinnedMessage:
						urlContent = ""
						if len(self.dataUrlEnd):
							urlContent = "".join(["\n>{}".format(el["url"]) for el in self.dataUrlEnd])
						content = ":microphone2: **SPACE TWITTER EN COURS**\n```python\n\"N'hésitez pas à partager le lien d'un Space Twitter dans ce salon !\"```\n:white_small_square: Actuellement **{}** Space en cours : {}".format(len(self.dataUrlEnd), urlContent)
						channel = self.client.get_channel(self.spaceChannel)
						message = await channel.fetch_message(self.pinnedMessage)
						await message.edit(content=content)
				await page.wait_for_timeout(5)

				
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
			self.addUrl.append({"url": url, "timestamp": str(datetime.utcnow() - timedelta(seconds=self.timedelta))})

def setup(client):
	client.add_cog(Space(client))