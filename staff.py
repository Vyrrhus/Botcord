import discord
import asyncio
from discord.ext import commands

import src.check as check
import src.tool as tool
from src.tool import log

from src.config.settings import MONITOR_MAIN as MNT

class Staff(commands.Cog):
	def __init__(self, client):
		self.client = client
		asyncio.get_event_loop().create_task(self.update_claim())
		
	###########################################
	#            COROUTINE TASK               #
	###########################################
	async def update_claim(self):
		await self.client.wait_until_ready()
		await asyncio.sleep(1)
		
		while True:
			# Get all claims
			claim_data = tool.get_data('src/config/staff/claim.json')
			for channel_ID in claim_data:
				# Get claims of each Textchannel
				update = []
				for claim in claim_data[channel_ID]:
					claim['next'] -= 1
					# Trigger claims that must be fired
					if claim['next'] <= 0:
						claim['next'] = claim['delay']
						try:
							await self.client.get_channel(int(channel_ID)).send(claim['text'])
						except:
							await log('ALERTE : accès restreint au salon ID: {}'.format(int(channel_ID)), MNT)
					update.append(claim)
				claim_data[channel_ID] = update
			# Task executes every minute
			tool.set_data(claim_data, 'src/config/staff/claim.json')
			await asyncio.sleep(60)
			
	###########################################
	#                  CHECKS                 #
	###########################################
	async def cog_check(self, ctx):
		"""Les commandes de ce cog ne peuvent être utilisées que par un staff.
		"""
		data_ID = tool.get_data('src/config/id.json')
		try:
			return check.is_role(ctx.author, data_ID['ROLE']['STAFF'])
		except:
			await log('STAFF COG local check failed', MNT)
			return False
		
	###########################################
	#                COMMANDS                 #
	###########################################
	# COMMAND: ?claim
	@commands.command(name='claim', pass_context=True)
	async def claim(self, ctx, *text):
		""" Messages automatiques du bot
		
		EXEMPLE
		-------
		> ?claim <delay> <text> : génère un message automatique tous les <delay> minutes dans le salon courant.
		> ?claim		: affiche la liste des messages autos du salon courant
		> ?claim .clear : supprime tous les messages autos du salon courant.
		"""
		claim_data = tool.get_data('src/config/staff/claim.json')
		
		# Liste des annonces du salon courant
		if not text:
			await log('?claim list : [#{}], {}'.format(ctx.channel.name, str(ctx.author)), MNT)
			try:
				claim_list = claim_data[str(ctx.channel.id)]
				EMB = tool.set_embed(color=0xaa6622,
								 	author='Messages automatiques sur : #{}'.format(ctx.channel.name))
				claim_text = [claim_list[n]['text'] + '\n\n :alarm_clock: - {}mn'.format(claim_list[n]['delay']) for n in range(0, len(claim_list))]
				message, result = await tool.enhance_embed(ctx, EMB, name='Texte [délai]', values=claim_text)
						
			except Exception as e:
				# Pas de claim dans ce salon
				await ctx.channel.send('Aucun message automatique trouvé :shrug:')

		# Ajout d'un claim dans le salon courant
		else:
			text = list(text)
			if text[0] == '.clear':
				await log('?claim clear : [#{}], {}'.format(ctx.channel.name, str(ctx.author)), MNT)
				claim_data.pop(str(ctx.channel.id), None)
				await ctx.channel.send('Messages automatiques effacés :put_litter_in_its_place:')
				tool.set_data(claim_data, 'src/config/staff/claim.json')
				return
			
			await log('?claim ajout : [#{}], {}'.format(ctx.channel.name, str(ctx.author)), MNT)
				
			claim = {'text': ' '.join(text[1::]),
					 'delay': int(text[0]),
					 'next': int(text[0])}
			try:
				channel_list = claim_data[str(ctx.channel.id)]
				channel_list.append(claim)
			except:
				channel_list = [claim]
			claim_data[str(ctx.channel.id)] = channel_list
			await ctx.channel.send('Message automatique enregistré :memo:')
			tool.set_data(claim_data, 'src/config/staff/claim.json')
	
	###########################################
	#                 EVENTS                  #
	###########################################
	
async def setup(client):
	await client.add_cog(Staff(client))