import discord
from discord.ext import commands

from playwright.async_api import async_playwright

from src.config.settings import MONITOR_MAIN as MNT
from src.tool import log

class Laec(commands.Cog):
	def __init__(self, client):
		self.client	= client
		self.url    = "https://laec.fr/"
		self.search = "https://laec.fr/recherche/?q={}"
		self.no_result = "Ta recherche ne renvoie aucun résultat ¯\_(ツ)_/¯"

	###########################################
	#                COMMANDS                 #
	###########################################

	@commands.command(name='laec', pass_context=True)
	async def laec(self, ctx, *search):
		""" Fait une recherche sur laec.fr
		"""
		url = self.search.format("+".join(("+".join(el.split()) for el in search)))
		await log('Recherche !laec par {} sur {}:\n<{}>'.format(ctx.author.mention, ctx.channel.mention, url), MNT)

		async with async_playwright() as p:
			browser = await p.chromium.launch(headless=True)
			page    = await browser.new_page()
			await page.goto(url)

			await page.wait_for_selector("id=contenu")
			resultats = await page.query_selector("id=resultats")
			links = await resultats.query_selector_all("cite")
			try:
				link = await links[0].inner_text()
				await ctx.message.reply(link)
			except Exception as e:
				await ctx.message.reply(self.no_result)
				print(e)

			await browser.close()
		return
		
	###########################################
	#                  EVENTS                 #
	###########################################
    
    # # ON MESSAGE
	# @commands.Cog.listener()
	# async def on_message(self, message):

	# # ON MEMBER JOIN
	# @commands.Cog.listener()
	# async def on_member_join(self, member):

def setup(client):
	client.add_cog(Laec(client))