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
import os
from datetime import datetime
from datetime import timedelta
import tweepy
import src.check as check
import src.tool as tool
import src.tweetool as twool
from src.tool import log

from discord.ext import commands
from src.config.settings import data

import sys
import traceback

class Twitter:
	def __init__(self, client):
		self.client = client
		self.task1_lock = True
		self.task2_lock = False
		asyncio.get_event_loop().create_task(self.getting_tweets())
		asyncio.get_event_loop().create_task(self.checking_tags())
	
	###########################################
	#            COROUTINE TASK               #
	###########################################
	
	async def checking_tags(self):
		await self.client.wait_until_ready()
		await asyncio.sleep(1)
		await log('TAGS TASK - INIT', time=True)
		
		# PARAMETERS FOR THE WHOLE TASK
		# Login
		await log('TAGS TASK - LOGIN API', time=True)
		api = await twool.login()
		
		while True:
			await asyncio.sleep(0)
			
			# Sleeping time
			sleep_time = tool.get_data('src/config/tweetings.json')['TAG_SLEEP_TIME']
			max_time = tool.get_data('src/config/tweetings.json')['TAG_MAX_TIME']
			
			# Blocking
			while self.task1_lock:
				await log('TAGS TASK - tweets task running : lock', time=True)
				await asyncio.sleep(10)
				sleep_time -= 10
			self.task2_lock = True
			
			# Tags list
			data = tool.get_data('src/config/twitter/temp_tags.json')
			
			for account in data:
				await asyncio.sleep(0)
				print(account)
				
				# SEARCHING TARGET
				target = await twool.get_target(api, account)
				
				if not target:
					await log('TAGS TASK - {} unreachable'.format(account))
					continue
					
				since_id = data[account]['since_id']
					
				# GET RETWEETS & QUOTES
				while True:
					await asyncio.sleep(0)
					try:
						retweets, until_id = await twool.get_retweets(api, target, since_id=since_id, list_id=[tweet for tweet in data[account]["tweets"]])
						data[account]['since_id'] = until_id
						break
					except Exception as e:
						await log('TAGS TASK - Exception thrown in RT, QT: sleep [60]s\n{}'.format(e), time=True)
						await asyncio.sleep(60)
						sleep_time -= 60
						
				# GET FAVS
				favs = []
#				while True:
#					await asyncio.sleep(0)
#					try:
#						favs = await twool.get_fav(api, target, [tweet for tweet in data[account]["tweets"]])
#						break
#					except Exception as e:
#						await log('TAGS TASK - Exception thrown in FAV: SLEEP [60]s\n{}'.format(e), time=True)
#						traceback.print_exc()
#						await asyncio.sleep(60)
#						sleep_time -= 60
				
				# PROCESS TWEETS				
				for retweet in retweets:
					await asyncio.sleep(0)
					await log('{} a RT|QUOTE n°{}'.format(account, retweet))
					temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
					temp_data.append({'type': 'retweet',
									  'account': account,
									  'id': retweet
									 })
					tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
					
				for fav in favs:
					await asyncio.sleep(0)
					await log('{} a FAV n°{}'.format(account, fav))
					temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
					temp_data.append({'type': 'fav',
									  'account': account,
									  'id': fav
									 })
					tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
				
				for element in list(set(retweets + favs)):
					await asyncio.sleep(0)
					print(data[account])
					print(data[account]["tweets"])
					data[account]["tweets"].pop(element)
					
				list_to_del = []
				for element in data[account]["tweets"]:
					await asyncio.sleep(0)
					if datetime.utcnow() - tool.str_to_date(data[account]["tweets"][element]) >= timedelta(0, max_time):
						list_to_del.append(element)
				for element in list_to_del:
					await asyncio.sleep(0)
					try:
						data[account]["tweets"].pop(element)
					except Exception as e:
						await log('TAGS TASK - Exception thrown l.134 : {}'.format(e))
			
			list_to_del = []
			for account in data:
				await asyncio.sleep(0)
				if not data[account]["tweets"]:
					list_to_del.append(account)
			for element in list_to_del:
				data.pop(element)

			# SAVE DATA
			await asyncio.sleep(0)
			if not data:
				os.remove('src/config/twitter/temp_tags.json')
			else:
				tool.set_data(data, 'src/config/twitter/temp_tags.json')
			
			# SLEEPING
			await asyncio.sleep(0)
			if sleep_time <= 0:
				sleep_time = 0
			await log('TAGS TASK - sleeping [{}s]'.format(sleep_time), time=True)
			self.task2_lock = False
			await asyncio.sleep(sleep_time)
			await log('TAGS TASK - sleeping over', time=True)
				
	
	async def getting_tweets(self):
		await self.client.wait_until_ready()
		await asyncio.sleep(1)
		await log('TWEETS TASK - INIT', time=True)
		
		# PARAMETERS FOR THE WHOLE TASK
		# Login
		await log('TWEETS TASK - LOGIN API', time=True)
		api = await twool.login()
		self.task1_lock = True
		
		while True:
			await asyncio.sleep(0)
			
			# Sleeping time
			sleep_time = tool.get_data('src/config/tweetings.json')['TWEET_SLEEP_TIME']
			
			# Blocking
			while self.task2_lock:
				await log('TWEETS TASK - tags task running : lock', time=True)
				await asyncio.sleep(10)
				sleep_time -= 10
			self.task1_lock = True
			
			# Merging data
			data = tool.get_data('src/config/twitter/data.json')
			data_track = tool.get_data('src/config/twitter/tweet.json')
			try:
				temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
				for element in temp_data:
					await asyncio.sleep(0)
					# ADD
					if element['type'] == 'add':
						print('add {} - {}'.format(element['account'], element['channel']))
						if element['account'] not in data:
							print('create')
							data[element['account']] = {'channel': [element['channel']],
													    'since_id': None,
													    'created_since': str(datetime.utcnow())
													   }
						else:
							print('append')
							data[element['account']]['channel'] = list(set(data[element['account']]['channel'] + [element['channel']]))

					# REMOVE
					elif element['type'] == 'remove':
						print('remove {} - {}'.format(element['account'], element['channel']))
						if element['account'] in data:
							print('specific')
							try:
								data[element['account']]['channel'].remove(element['channel'])
								if not data[element['account']]['channel']:
									print('no channel anymore')
									data.pop(element['account'])
							except Exception as e:
								print('channel not found for this account')
								pass
						elif element['account'] == 'all':
							print('all')
							list_to_del = []
							for account in data:
								try:
									data[account]['channel'].remove(element['channel'])
									print('{} suppr'.format(account))
									if not data[account]['channel']:
										print('no channel anymore')
										list_to_del.append(account)
								except:
									continue
							for account in list_to_del:
								data.pop(account)
					# TRACK
					elif element['type'] == 'track':
						print('track {}'.format(element['account']))
						if element['account'] not in data_track:
							print('track ajouté')
							data_track[element['account']] = {}
					# UNTRACK
					elif element['type'] == 'untrack':
						print('untrack {}'.format(element['account']))
						if element['account'] in data_track:
							print('untracké')
							data_track.pop(element['account'])
					# RETWEET
					elif element['type'] == 'retweet':
						tweet_id = element['id']
						retweeter = element['account']
						for account in data_track:
							try:
								if 'tag_RT' in data_track[account][tweet_id]:
									data_track[account][tweet_id]['tag_RT'].append(retweeter)
								else:
									data_track[account][tweet_id]['tag_RT'] = [retweeter]
								break
							except Exception as e:
								continue
					# FAV
					elif element['type'] == 'fav':
						tweet_id = element['id']
						favish = element['account']
						for account in data_track:
							try:
								if 'tag_FAV' in data_track[account][tweet_id]:
									data_track[account][tweet_id]['tag_FAV'].append(favish)
								else:
									data_track[account][tweet_id]['tag_FAV'] = [favish]
								break
							except Exception as e:
								continue
			except Exception as e:
				print('no temp file'.format(e))
				traceback.print_exc()
				pass
			
			# List of accounts for the current iteration
			accounts = [element for element in data]
			
			for account in accounts:
				await asyncio.sleep(0)
				# SEARCHING TARGET
				target = await twool.get_target(api, account)
				
				if not target:
					await log('TWEETS TASK  - {} unreachable, check channels: {}'.format(account, ['{} '.format(element) for element in data[account]['channel']]))
					continue
					
				since_id = data[account]['since_id']
				if not since_id:
					created_since = tool.str_to_date(data[account]['created_since'])
				else:
					created_since = datetime.utcnow()
					
				# GET TWEETS
				while True:
					await asyncio.sleep(0)
					try:
						tweets, until_id = await twool.get_tweet(api, target, since_id=since_id, created_since=created_since)
						if tweets:
							await log('TWEETS TASK - {} : {} tweets found'.format(account, len(tweets)))
						data[account]['since_id'] = until_id
						break
					except Exception as e:
						await log('TWEETS TASK - Exception thrown ({}) : [60]s'.format(e), time=True)
						await asyncio.sleep(60)
						sleep_time -= 60
				
				# PROCESS TWEETS
				for tweet in tweets:
					await asyncio.sleep(0)
					# SET EMBED
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
					
					# TRACK TAGS IF NECESSARY
					if account in data_track:
						await asyncio.sleep(0)
						# APPEND DATA
						data_track[account][tweet.id_str] = {'date': str(tweet.created_at),
															 'link': 'https://twitter.com/{}/status/{}'.format(tweet.user.screen_name, tweet.id_str),
															 'text': tweet.full_text
															}
						try:
							tags = await twool.get_tags(tweet)
							data_track[account][tweet.id_str]['tags'] = tags
						except Exception as e:
							await log('TWEETS TASK - Exception thrown l. 299-300 ({})'.format(e), time=True)
							pass
						
						temp_tags = tool.get_data('src/config/twitter/temp_tags.json')
						if not temp_tags:
							os.remove('src/config/twitter/temp_tags.json')
						for tag in tags:
							await asyncio.sleep(0)
							if tag not in temp_tags:
								temp_tags[tag] = {"since_id": tweet.id,
												  "tweets": {tweet.id_str: str(datetime.utcnow())}
												 }
							else:
								temp_tags[tag]["tweets"][tweet.id_str] = str(datetime.utcnow())
							tool.set_data(temp_tags, 'src/config/twitter/temp_tags.json')
							
						# STORE DATA
						tool.set_data(data_track, 'src/config/twitter/tweet.json')
						
					
					# POST TO TEXTCHANNEL(S)
					textchannels = [self.client.get_channel(element) for element in data[account]['channel']]
					for textchannel in textchannels:
						await asyncio.sleep(0)
						if not textchannel:
#							await log('channel not found for {}'.format(account), time=True)
							continue
						await textchannel.send(content=None, embed=EMB)
		
			# Save data
			await asyncio.sleep(0)
			tool.set_data(data, 'src/config/twitter/data.json')
			tool.set_data(data_track, 'src/config/twitter/tweet.json')
			os.remove('src/config/twitter/temp_data.json')
			
			# Sleep & unlock self.task_lock
			await asyncio.sleep(0)
			if sleep_time <= 10:
				sleep_time = tool.get_data('src/config/tweetings.json')['TWEET_MIN_SLEEP_TIME']
			await log('TWEETS TASK - sleeping [{}s]'.format(sleep_time), time=True)
			self.task1_lock = False
			await asyncio.sleep(sleep_time)
			await log('TWEETS TASK - sleeping over', time=True)
					
				
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
			return True
			return False
	
	###########################################
	#                COMMANDES                #
	###########################################
	
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
			temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
			
			for compte in compte_twitter:
				compte = compte.lower()
				temp_data.append({'type': 'add',
								  'channel': ctx.channel.id,
								  'account': compte
								 })
			tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
				
					
		
	# REMOVE ACCOUNT
	@commands.command(name='unfollow', pass_context=True)
	async def remove_twitter(self, ctx, *compte_twitter):
		"""Retire le compte de la liste des comptes suivis dans ce salon
		"""
		await log('REMOVE')
		if not compte_twitter:
			return
		
		temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
		
		# UNFOLLOW ALL
		if compte_twitter[0] in ['all', '*']:
			temp_data.append({'type': 'remove',
							  'channel': ctx.channel.id,
							  'account': 'all'
							 })	
			tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
			return
		
		# UNFOLLOW SPECIFIC ACCOUNTS
		for account in compte_twitter:
			account = account.lower()
			temp_data.append({'type': 'remove',
							  'channel': ctx.channel.id,
							  'account': account
							 })
			
		tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
	
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
			temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
			
			for compte in compte_twitter:
				compte = compte.lower()
				temp_data.append({'type': 'track',
								  'account': compte
								 })
				temp_data.append({'type': 'add',
								  'channel': 'tracking',
								  'account': compte
								 })
			tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
			return
				
	# UNTRACK ACCOUNT
	@commands.command(name='untrack', pass_context=True)
	async def untrack(self, ctx, *compte_twitter):
		"""Retire le compte de la liste des comptes traqués
		"""
		await log('UNTRACK')
		if not compte_twitter:
			return
		
		temp_data = tool.get_data('src/config/twitter/temp_data.json', default=[])
		
		# UNTRACK ALL
		if compte_twitter[0] in ['all', '*']:
			temp_data.append({'type': 'untrack',
							  'account': 'all'
							 })
			tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
			return
		
		# UNTRACK SPECIFIC ACCOUNTS
		for account in compte_twitter:
			account = account.lower()
			temp_data.append({'type': 'untrack',
							  'account': account
							 })
			temp_data.append({'type': 'remove',
							  'channel': 'tracking',
							  'account': account
							 })
			
		tool.set_data(temp_data, 'src/config/twitter/temp_data.json')
	
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