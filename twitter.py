""" 
Rajouter d'autres trucs utiles pour remplacer le bot twitter : 
- suivre un compte en particulier (chaque paramètre doit pouvoir être modifié : salon, type de contenu (tweet natif, RT, RT + réponses, fav, etc), salon(s), personnes ayant les droits d'utiliser la commande, etc.
- suivre des mots-clefs dans une liste de comptes
- suivre des mots-clefs en restreignant au nombre d'abonnés / RT / fav (chaque settings personnalisé pour chaque keyword)

- account | compte | listen
- tag
- 
"""

import discord
import asyncio
import random
from datetime import datetime
from datetime import timedelta
import tweepy
import src.check as check
import src.tool as tool
import src.tweetool as twool
from src.tool import log

from discord.ext import commands
from src.config.settings import data

class Twitter:
	def __init__(self, client):
		self.client = client
		self.account = {}
		asyncio.get_event_loop().create_task(self.listen_accounts())
	
	###########################################
	#            COROUTINE TASK               #
	###########################################	
	async def listen_accounts(self):
		await self.client.wait_until_ready()
		await log('TASK INIT', time=True)
		# Login
		api = await twool.login()
		await log('twitter api logged in')
		
		# Parameters
		created_since = datetime.utcnow()
		
		# Loop
		while True:
			await log('TASK ITERATION', time=True)
			# Save data
			tool.set_data(data, 'src/config/settings.json')
			
			# Parameters
			sleep_time = 60 * 5 * data['TWITTER']['SLEEP_TIME_MN']
			
			# Listening for each account to retrieve their tweets and put it on the right channel.
			# If Listened, store the corresponding tags
			for element in data['TWITTER']['ACCOUNT']:
				target = await twool.get_target(api, element)
				if not target:
					"""AFFICHER UN MSG COMME QUOI LA TARGET EXISTE PLUS"""
					await log("{} cannot be found".format(element))
					continue
				
				# Get tweets
				since_id = data['TWITTER']['ACCOUNT'][element]['since_id']
				created_since = tool.str_to_date(data['TWITTER']['ACCOUNT'][element]['created_since'])
				tweets, last_tweet_id = await twool.get_tweet(api, target, since_id=since_id, created_since=created_since)
				data['TWITTER']['ACCOUNT'][element]['since_id'] = last_tweet_id
				if tweets:
					await log('{} : {} tweets found'.format(element, len(tweets)))
					
				# For each tweet :
				for tweet in tweets:
					try:
						img = tweet.entities['media'][0]['media_url']
					except:
						img = None
					EMB = tool.set_embed(color=0xffffff,
										 title='https://twitter.com/{}/status/{}'.format(tweet.user.screen_name, tweet.id_str),
										 title_url='https://twitter.com/{}/status/{}'.format(tweet.user.screen_name, tweet.id_str),
										 author='@{}'.format(tweet.user.screen_name),
										 author_url='https://twitter.com/{}'.format(tweet.user.screen_name),
										 author_icon=tweet.user.profile_image_url,
										 timestamp=tweet.created_at,
										 image=img,
										 fields=[tool.set_field(name='Nouveau tweet : ', value=tweet.full_text, inline=True)])
					
					# For each channel :
					remove_channels = []
					for channel_id in data['TWITTER']['ACCOUNT'][element]['channel']:
						channel = self.client.get_channel(channel_id)
						if channel:
							await channel.send(content=None, embed=EMB)
					
					# If account is listened:
					if element in data['TWITTER']['LISTEN']:
						# Get tweets' data file
						data_tweet = tool.get_data('src/config/data_tweet.json')
						if not element in data_tweet:
							data_tweet[element] = {}
						# Add tweet info
						data_tweet[element][tweet.id_str] = {'date': str(tweet.created_at),
															 'link': 'https://twitter.com/{}/status/{}'.format(tweet.user.screen_name, tweet.id_str),
															 'text': tweet.full_text}
						tags = await twool.get_tags(tweet)
						data_tweet[element][tweet.id_str]['tags'] = tags
						# Save tweets' data file
						tool.set_data(data_tweet, 'src/config/data_tweet.json')
						
						# Get tags' data file
						if not tags:
							continue
						data_tags = tool.get_data('src/config/data_tag.json')
						if not element in data_tags:
							data_tags[element] = {'in_progress': {}, 'completed': {}}
						for tag in tags:
							if not tag in data_tags[element]['in_progress']:
								data_tags[element]['in_progress'][tag] = []
							data_tags[element]['in_progress'][tag].append({'id': tweet.id,
																		   'since_id': tweet.id,
																		   'time': str(datetime.utcnow()),
																		   'RT': None,
																		   'FAV': None})
						# Save tags' data file
						tool.set_data(data_tags, 'src/config/data_tag.json')
						
			# Now check each account that has been tagged for each account listened
			data_tags = tool.get_data('src/config/data_tag.json')
			for element in data_tags:
				remove_accounts = []
				for account in data_tags[element]['in_progress']:
					target = await twool.get_target(api, account)
					if not target:
						"""AFFICHER UN MESSAGE COMME QUOI LA TARGET EXISTE PLUS"""
						continue
					since_id = min([tweet['since_id'] for tweet in data_tags[element]['in_progress'][account]])
					retweets, next_since_id = await twool.get_tweet(api, target, since_id=since_id, exclude_retweets=False, only_retweets=True)
					retweet_id = []
					for retweet in retweets:
						if hasattr(retweet, 'retweeted_status'):
							retweet_id.append(retweet.retweeted_status.id)
							continue
						if hasattr(retweet, 'quoted_status'):
							retweet_id.append(retweet.quoted_status.id)
							continue
					
					# Check for each tweet an account has been tagged on:
					for tweet in data_tags[element]['in_progress'][account]:
						# RT
						if tweet['id'] in retweet_id:
							tweet['RT'] = True
							await log('{} a RT {}'.format(account, tweet['id']))
						# FAV
						if tweet['id'] in await twool.get_fav(api, target, tweet['id']):
							tweet['FAV'] = True
							await log('{} a FAV {}'.format(account, tweet['id']))
						# Update time
						isOver = tool.str_to_date(tweet['time']) - datetime.utcnow() >= timedelta(hours=data['TWITTER']['MAX_TIMEDELTA_HOURS'])
						if isOver:
							await log('Temps écoulé pour {} sur le tweet {}'.format(account, tweet['id']))
						
						# Check if RT|FAV true or time over
						if tweet['RT'] or tweet['FAV'] or isOver:
							if account not in data_tags[element]['completed']:
								data_tags[element]['completed'][account] = []
							tweet.pop('time')
							tweet.pop('since_id')
							data_tags[element]['completed'][account].append(tweet)
							data_tags[element]['in_progress'][account].remove(tweet)
							if not data_tags[element]['in_progress'][account]:
								remove_accounts.append(account)
						else:
							if next_since_id:
								tweet['since_id'] = next_since_id
				for key in remove_accounts:
					data_tags[element]['in_progress'].pop(key)
			tool.set_data(data_tags, 'src/config/data_tag.json')
			await log('TASK SLEEPING [{}s]'.format(sleep_time), time=True)
			await asyncio.sleep(sleep_time)
		
		
	###########################################
	#                  CHECKS                 #
	###########################################
	
	# LOCAL CHECK
	async def __local_check(self, ctx):
		""" Les commandes de ce cog ne peuvent être utilisées que par un staff"""
		try:
			return check.is_staff(ctx.author)
		except:
			await log('twitter local check failed')
			return False
	
	###########################################
	#                COMMANDES                #
	###########################################
	
	# TEST
	@commands.command(name='test', pass_context=True)
	async def test(self, ctx):
		await ctx.channel.send('Channel : {}'.format(ctx.channel.id))
	
	# ADD ACCOUNT
	@commands.command(name='follow', pass_context=True)
	async def follow(self, ctx, *compte_twitter):
		"""Ajoute le compte à la liste des comptes suivis dans ce salon
		
		EXEMPLE
		-------
		> ?follow Action_Insoumis : ajoute [Action_Insoumis] à la liste des comptes suivis sur ce salon
		> ?follow : afficher la liste des comptes suivis sur ce salon
		"""
		await log('ADD')
		# Liste des comptes suivis sur ce salon :
		if not compte_twitter:
			accounts = []
			for element in data['TWITTER']['ACCOUNT']:
				if ctx.channel.id in data['TWITTER']['ACCOUNT'][element]['channel']:
					accounts.append(element)
			if not accounts:
				return await ctx.channel.send("Aucun compte twitter n'est suivi ici :shrug:")
			else:
				EMB = tool.set_embed(color=0x22aaaa,
									 author='Comptes twitters suivis',
									 author_icon='https://pbs.twimg.com/profile_images/1013798240683266048/zRim1x6M_400x400.jpg',
									 description='La liste ci-dessous est suivie sur ce salon, par ordre chronologique.\n?follow <nom_du_compte> : ajouter un compte\n?unfollow <nom_du_compte> : retirer un compte')
				list_accounts = ['\n'.join(accounts[n:n+10]) for n in range(0, len(accounts), 10)]
				
				message, result = await tool.enhance_embed(ctx, EMB, name='COMPTES', values=list_accounts)
			
		# Ajout des comptes à follow
		else:
			for compte in compte_twitter:
				compte = compte.lower()
				if not compte in data['TWITTER']['ACCOUNT']:
					data['TWITTER']['ACCOUNT'][compte] = {'channel': [],
														  'since_id': None,
														  'created_since': str(datetime.utcnow())}
				if not ctx.channel.id in data['TWITTER']['ACCOUNT'][compte]['channel']:
					data['TWITTER']['ACCOUNT'][compte]['channel'].append(ctx.channel.id)
		
	# REMOVE ACCOUNT
	@commands.command(name='unfollow', pass_context=True)
	async def remove_twitter(self, ctx, *compte_twitter):
		"""Retire le compte de la liste des comptes suivis dans ce salon
		"""
		await log('REMOVE')
		if not compte_twitter:
			return
		
		# UNFOLLOW ALL
		if compte_twitter[0] in ['all', '*']:
			del_list = []
			for account in data['TWITTER']['ACCOUNT']:
				try:
					data['TWITTER']['ACCOUNT'][account]['channel'].remove(ctx.channel.id)
					if not data['TWITTER']['ACCOUNT'][account]['channel']:
						del_list.append(account)
				except:
					continue
			for account in del_list:
				data['TWITTER']['ACCOUNT'].pop(account)
			return
		
		# UNFOLLOW SPECIFIC ACCOUNTS
		for account in compte_twitter:
			account = account.lower()
			try:
				data['TWITTER']['ACCOUNT'][account]['channel'].remove(ctx.channel.id)
				if not data['TWITTER']['ACCOUNT'][account]['channel']:
					data['TWITTER']['ACCOUNT'].pop(account)
			except:
				await log("{} n'est pas dans la liste".format(account))
				pass
	
	# TRACK ACCOUNT
	@commands.command(name='track', pass_context=True)
	async def track(self, ctx, *compte_twitter):
		"""Collecte des données sur le compte (chaque tweet + tags publiés)
		"""
		await log('TRACK')
		#Liste des comptes écoutés :
		if not compte_twitter:
			accounts = data['TWITTER']['LISTEN']
			if not accounts:
				return await ctx.channel.send("Aucun compte twitter n'est traqué.")
			EMB = tool.set_embed(color=0x006a6a,
								 author='Comptes twitters traqués',
								 author_icon='https://pbs.twimg.com/profile_images/1013798240683266048/zRim1x6M_400x400.jpg',
								 description='Les tweets des comptes ci-dessous sont sauvegardés et les tags de leurs publications surveillés, par ordre chronologique.\n?track <compte_twitter> : ajouter un compte\n?untrack <compte_twitter> : retirer un compte')
			list_accounts = ['\n'.join(accounts[n:n+10]) for n in range(0, len(accounts), 10)]
			message, result = await tool.enhance_embed(ctx, EMB, name='COMPTES', values=list_accounts)
			return
		
		 # Ajout de comptes à écouter
		else:
			for compte in compte_twitter:
				compte = compte.lower()
				if not compte in data['TWITTER']['LISTEN']:
					data['TWITTER']['LISTEN'].append(compte)
			return
				
	# UNTRACK ACCOUNT
	@commands.command(name='untrack', pass_context=True)
	async def untrack(self, ctx, *compte_twitter):
		"""Retire le compte de la liste des comptes traqués
		"""
		await log('UNTRACK')
		if not compte_twitter:
			return
		
		# UNTRACK ALL
		if compte_twitter[0] in ['all', '*']:
			data['TWITTER']['LISTEN'] = []
			return
		
		# UNTRACK SPECIFIC ACCOUNTS
		for account in compte_twitter:
			account = account.lower()
			try:
				data['TWITTER']['LISTEN'].remove(account)
			except:
				await log("{} n'est pas dans la liste.".format(account))
				pass
	
#	
#	# GET TAG LIST
#	@commands.command(name='tag', pass_context=True)
#	async def tag(self, ctx, *compte_twitter):
#		return
#		"""Récupère une liste des tags réalisés ou plus d'infos sur un compte en particulier
#		
#		EXEMPLE
#		-------
#		> ?tag Action_Insoumis : récupère la liste complète des tags du compte associé à LISTEN (on peut naviguer entre les pages)
#		"""
#		await log('TAG')
#		
#		# Check for the reaction add
#		def check_reaction(m):
#			return True
#		
#		# Getting data
#		
#		
#		# Embed of the tags
#		
#		
#		return
#	
#	# UPDATE PARAMETERS
#	@commands.command(name='settings', pass_context=True)
#	async def settings(self, ctx):
#		return
#		"""Modifier les settings de TWITTER"""
#		await log('SETTINGS')
#		
#		# Check for the replies
#		def check_reply(m):
#			return m.author == ctx.author and m.channel == ctx.channel
#		
#		# Embed of the settings
#		EMB = discord.Embed(color=0x840000)
#		EMB.set_author(name='Paramètres du module TWITTER', icon_url='https://pbs.twimg.com/profile_images/1035308510505062401/2YgRA4iz_400x400.jpg')
#		EMB.add_field(name='Paramètres :', value='1. SLEEP_TIME [{}mn]\nDélai entre deux checks de Twitter en minutes\n2. MAX_TIMEDELTA [{}h]\nDurée maximale pour RT | FAV un tweet identifié en heures'.format(data['TWITTER']['SLEEP_TIME_MN'], data['TWITTER']['MAX_TIMEDELTA_HOURS']))
#		EMB.set_footer(text='Indiquer le paramètre à modifier [num]')
#		msg_emb = await ctx.channel.send(content=None, embed=EMB)
#		
#		# Reply within 30s and edit
#		reply = await self.client.wait_for('message', check=check_reply, timeout=30)
#		num = reply.content
#		EMB = discord.Embed(color=0x840000)
#		EMB.set_author(name='Paramètres du module TWITTER', icon_url='https://pbs.twimg.com/profile_images/1035308510505062401/2YgRA4iz_400x400.jpg')
#		if num == '1':
#			EMB.add_field(name='SLEEP_TIME', value='{} minute(s)'.format(data['TWITTER']['SLEEP_TIME_MN']))
#		elif num == '2':
#			EMB.add_field(name='MAX_TIMEDELTA', value='{} heure(s)'.format(data['TWITTER']['MAX_TIMEDELTA_HOURS']))
#		else:
#			EMB.add_field(name='Erreur', value='Le numéro ne correspond à aucun paramètre.')
#			await msg_emb.edit(content=None, embed=EMB, delete_after=15)
#			try:
#				await reply.delete()
#			except:
#				# No permission to delete message
#				pass
#			return
#		EMB.set_footer(text='Indiquer la valeur du paramètre.')
#		try:
#			await reply.delete()
#		except:
#			# No permission to delete message
#			pass
#		await msg_emb.edit(content=None, embed=EMB)
#		
#		# Final reply
#		reply = await self.client.wait_for('message', check=check_reply, timeout=30)
#		try:
#			value = int(reply.content)
#		except:
#			value = None
#		
#		try:
#			await reply.delete()
#		except:
#			pass
#			
#		if not value:
#			await msg_emb.edit(content='Erreur : le paramètre ne peut pas prendre cette valeur', embed=None)
#			return
#		
#		if num == '1':
#			data['TWITTER']['SLEEP_TIME_MN'] = value
#			await msg_emb.edit(content='SLEEP_TIME a été mis à jour [{}mn]'.format(value), embed=None)
#			return
#		if num == '2':
#			data['TWITTER']['MAX_TIMEDELTA_HOURS'] = value
#			await msg_emb.edit(content='MAX_TIMEDELTA a été mis à jour [{}h]'.format(value), embed=None)
#			return
		
def setup(client):
	client.add_cog(Twitter(client))