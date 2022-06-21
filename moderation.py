import discord
import asyncio
from datetime import datetime
from datetime import timedelta

import src.check as check
import src.tool as tool
from src.tool import log

from src.config.settings import MONITOR_MODERATION as MNT
from src.config.settings import GUILD_ID
from discord.ext import commands
from src.action import ACTION
#from src.note import NOTE

class Moderation(commands.Cog):
	def __init__(self, client):
		self.client = client
		# Store id & text for events
		self.id = tool.get_data('src/config/id.json')
		self.text = tool.get_data('src/config/moderation/text.json')
		self.sdd_role = self.id['ROLE']['DISCU'] + self.id['ROLE']['DIALO']
		self.animation_role = self.id['ROLE']['ANIMATION']
		# Exit lock to block event triggered by command
		self.exit_lock = False
		self.sdd_lock = False
		self.log = client.get_channel(self.id['TEXTCHANNEL']['LOG'])
	
	###########################################
	#                  CHECKS                 #
	###########################################
	
	# LOCAL CHECK
	async def cog_check(self, ctx):
		"""	Les commandes de ce cog ne peuvent être utilisées que par un staff ou un modérateur.
			En outre, elles ne sont utilisables que dans le salon de modération
		"""
		print("MODERATION COG CHECK")
		if check.is_owner(ctx.author):
			await log('OWNER !', MNT)
			return True
		try:
			return check.is_role(ctx.author, self.id['ROLE']['MODER']) and check.in_channel(ctx.channel, self.id['TEXTCHANNEL']['CHECK_MODER'])
		except:
			await log('moderation local check failed', MNT)
			return False
		
	###########################################
	#                COMMANDS                 #
	###########################################

	# TEST
	@commands.command(name='test', pass_context=True)
	async def test(self, ctx):
		await log(f'COMMANDE TEST 1', MNT)
		await log(f'args: {ctx.message.author.id}, {ctx.message.created_at}')
		action = ACTION('TEST', ctx.message.author.id, ctx.message.author.id, ctx.message.created_at, message='Le test est concluant')
		await log(f'COMMANDE TEST 2', MNT)
		EMB = action.embed(self.client, 0xaa8800)
		await log(f'COMMANDE TEST 3', MNT)

		await log(f'Commande TEST - {self.log}\n{self.log.id} - {self.log.name} - {self.log.guild.name}\n{action}', MNT)
		await self.log.send(content=None, embed=EMB)

	# WARN COMMAND
	@commands.command(name='warn', pass_context=True)
	async def warn(self, ctx, target:discord.Member, *, text):
		""" Envoie un warn à l'user
		"""
		# Checks
		if check.is_role(target, self.id['ROLE']['MODER']):
			await log('WARN - target role invalide', MNT)
			return
		
		# Action
		action = ACTION('Warn', target.id, ctx.message.author.id, ctx.message.created_at, message=text)
		EMB = action.embed(self.client, 0xaa8800)
		
		# Notification aux modérateurs
		await self.log.send(content=None, embed=EMB)
		await ctx.channel.send(':warning: {} a reçu un warn'.format(target.mention))
		
		# Envoi du warn
		await target.send(self.text['WARN'].format(text))
		
		# Sauvegarde du log
		action.save('src/config/moderation/data.json')
	
	# KICK COMMAND
	@commands.command(name='kick', pass_context=True)
	async def kick(self, ctx, target: discord.Member, *, text):
		""" Kick un user (message optionnel)
		"""
		# Checks
		if check.is_role(target, self.id['ROLE']['MODER']):
			await log('KICK - target role invalide', MNT)
			return
		if not check.kick_allowed(target, ctx.message.author) or not check.kick_allowed(target, ctx.guild.me):
			await log('KICK - permission de kick refusée', MNT)
			return
		
		# Séparation du text en message + auditlog
		message, auditlog = tool.extract_text(text)
		if not auditlog:
			await log('KICK - auditlog not given', MNT)
			return await ctx.channel.send("Auditlog manquant : ?kick [message optionnel] auditlog")
		if len(auditlog) > 512:
			await log('KICK - auditlog too long (512 char max)', MNT)
			return await ctx.channel.send("Auditlog trop long (`{}/512` caractères max)".format(len(auditlog)))
		
		# ACTION
		action = ACTION('Kick', target.id, ctx.message.author.id, ctx.message.created_at, message=message, reason=auditlog)
		EMB = action.embed(self.client, 0x995500)
		
		# Notification aux modérateurs
		await self.log.send(content=None, embed=EMB)
		await ctx.channel.send(':hammer: {} a été kick du serveur.'.format(target.mention))
		
		# Kick
		if message:
			await target.send(self.text['KICK'].format(message))
		else:
			await target.send(self.text['KICK_w_msg'])
		self.exit_lock = True
		await target.kick(reason=auditlog)
		
		# Sauvegarde du log
		action.save('src/config/moderation/data.json')
		
	@commands.command(name='ban', pass_context=True)
	async def ban(self, ctx, target: discord.Member, *, text):
		""" Ban un user (message optionnel)
		"""
		# Checks
		if check.is_role(target, self.id['ROLE']['MODER']):
			await log('BAN - target role invalide', MNT)
			return
		if not check.ban_allowed(target, ctx.message.author) or not check.ban_allowed(target, ctx.guild.me):
			await log('BAN - permission de ban refusée', MNT)
			return
		
		# Séparation du text en message + auditlog
		message, auditlog = tool.extract_text(text)
		if not auditlog:
			await log('BAN - auditlog not given', MNT)
			return await ctx.channel.send('Auditlog manquant : ?ban [message optionnel] auditlog')
		if len(auditlog) > 512:
			await log('BAN - auditlog too long (512 char max)', MNT)
			return await ctx.channel.send("Auditlog trop long (`{}/512` caractères max)".format(len(auditlog)))
		
		# ACTION
		action = ACTION('Ban', target.id, ctx.message.author.id, ctx.message.created_at, message=message, reason=auditlog)
		EMB = action.embed(self.client, 0x550000)
		
		# Notification aux modérateurs
		await self.log.send(content=None, embed=EMB)
		await ctx.channel.send(':skull_crossbones: {} a été ban du serveur.'.format(target.mention))
		
		# Ban
		if message:
			await target.send(self.text['BAN'].format(message))
		else:
			await target.send(self.text['BAN_w_msg'])
		self.exit_lock = True
		await target.ban(reason=auditlog, delete_message_days=1)
		
		# Sauvegarde du log
		action.save('src/config/moderation/data.json')
		
	@commands.command(name='log', pass_context=True)
	async def log(self, ctx, target:discord.User):
		""" Récupère les logs d'un user
		"""
		# Checks
		if check.is_role(target, self.id['ROLE']['MODER']):
			await log('LOG - target role invalide', MNT)
			return
		
		# Obtention des logs
		logs = tool.get_data('src/config/moderation/data.json')
		list_log = []
		for e in logs:
			if logs[e]['user'] == target.id:
				log = ACTION(logs[e]['lib'], 
							 logs[e]['user'], 
							 logs[e]['author'], 
							 logs[e]['time'], 
							 reason=logs[e]['reason'], 
							 message=logs[e]['message'],
							 log_id=logs[e]['log_id'],
							 log_channel=logs[e]['log_channel'],
							 log_content=logs[e]['log_content'],
							 num=e)
				list_log.append(log)
		if not list_log:
			return await ctx.channel.send(':x: Aucun log trouvé pour {}.'.format(target.name))

		await ctx.channel.send(':pencil: {} logs trouvés pour {}.'.format(len(list_log), target.name))
		
		# Envoi des logs
		if len(list_log) > 5:
			for log in list_log:
				EMB = log.embed(self.client, log.color)
				await ctx.author.send(content=None, embed=EMB)
			await ctx.channel.send(':mailbox: Logs expédiés.')
		else:
			for log in list_log:
				EMB = log.embed(self.client, log.color)
				await self.client.get_channel(self.id['TEXTCHANNEL']['LOG']).send(content=None, embed=EMB)
				
	@commands.command(name='clearlog', pass_context=True)
	async def clear(self, ctx, numero_log: int):
		""" Supprime le log
		"""
		# Clear log
		logs = tool.get_data('src/config/moderation/data.json')
		try:
			logs.pop(str(numero_log))
			await ctx.channel.send(':outbox_tray: Log n°{} supprimé avec succès'.format(numero_log))
			tool.set_data(logs, 'src/config/moderation/data.json')
		except:
			await ctx.channel.send(':x: Log n°{} introuvable.'.format(numero_log))
				
	@commands.command(name='libre', pass_context=True)
	async def libre(self, ctx):
		await ctx.channel.send('```LIBRE```')
		
	###########################################
	#                 EVENTS                  #
	###########################################
		
	# ON MEMBER JOIN
	@commands.Cog.listener()
	async def on_member_join(self, member):
		""" Vérifie les logs des nouveaux arrivants
		"""
		await log('{} a rejoint le serveur'.format(member.name), MNT, time=True)
		
		channel_rem = self.client.get_channel(self.id['TEXTCHANNEL']['JOIN_REMOVE'])
		logs = tool.get_data('src/config/moderation/data.json')
		list_log = []
		for e in logs:
			if logs[e]['user'] == member.id:
				list_log.append(e)
		if not list_log:
			await channel_rem.send('{} a rejoint le serveur.'.format(member.mention))
			return
		await channel_rem.send(':star: {} a rejoint le serveur : {} logs.'.format(member.mention, len(list_log)))
				
	# ON MEMBER REMOVE
	@commands.Cog.listener()
	async def on_member_remove(self, member):
		""" Notifie les kicks / bans si ceux-ci ne sont pas dûs à une commande.
			Notifie aussi les fuites de SDD (quelqu'un quitte de lui-même le serveur avec un rôle SDD)
		
		NOTE
		----
		> L'accès à l'auditlog est défaillant et peut parfois poser problèmes (léger lag entre le kick/ban et l'entrée correspondante dans l'auditlog).
		  Pour y palier, on a mis un délai de 5s avant lecture de l'auditlog, puis on récupère les 20 dernières entrées (en supposant en cas de raid jusqu'à 20 kick / bans en 5s) pour vérifier si l'une d'entre elle correspond.
		  C'est à dire si l'entrée a été faite il y a moins de 5s, correspond à un kick / ban et concerne l'utilisateur souhaité.
		"""
		await log('{} a quitté le serveur'.format(member.name), MNT, time=True)
		
		# Commande utilisée:
		if self.exit_lock:
			self.exit_lock = False
			return await log('verrou actif: commande', MNT)
		
		guild = self.client.get_guild(GUILD_ID)
		if not check.auditlog_allowed(guild.me):
			return await log("HAL 9000 n'a pas accès à l'auditlog", MNT)
		await asyncio.sleep(5)
		
		# Kick
		async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=20):
			if datetime.utcnow() - entry.created_at > timedelta(0,10):
				break
			if entry.target == member:
				await log("KICK manuel", MNT)
				action = ACTION('Kick', entry.target.id, entry.user.id, entry.created_at, reason=entry.reason)
				EMB = action.embed(self.client, 0x995500)
				await self.log.send(content=None, embed=EMB)
				channel_mod = self.client.get_channel(self.id['TEXTCHANNEL']['MODER'])
				await channel_mod.send(':hammer: {} a été kick du serveur.'.format(str(entry.target)))
				action.save('src/config/moderation/data.json')
				
				# Check SDD
				if check.is_role(member, self.sdd_role):
					for role in member.roles:
						if role.id == self.id['ROLE']['DISCU'] and not role.members:
							channel = self.client.get_channel(self.id['TEXTCHANNEL']['DISCU'])
							await channel.send('```LIBRE```')
						if role.id == self.id['ROLE']['DIALO'] and not role.members:
							channel = self.client.get_channel(self.id['TEXTCHANNEL']['DIALO'])
							await channel.send('```LIBRE```')
			
				try:
					channel_rem = self.client.get_channel(self.id['TEXTCHANNEL']['JOIN_REMOVE'])
					await channel_rem.send('{}#{} a été kick du serveur. :hammer:'.format(member.name, member.discriminator))
				except:
					await log('ALERTE : accès restreint au salon JOIN_REMOVE')
					
				return
		
		# Ban
		async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=20):
			if datetime.utcnow() - entry.created_at > timedelta(0,10):
				break
			if entry.target == member:
				await log('BAN manuel', MNT)
				action = ACTION('Ban', entry.target.id, entry.user.id, entry.created_at, reason=entry.reason)
				EMB = action.embed(self.client, 0x550000)
				await self.log.send(content=None, embed=EMB)
				channel_mod = self.client.get_channel(self.id['TEXTCHANNEL']['MODER'])
				await channel_mod.send(':skull_crossbones: {} a été ban du serveur.'.format(str(entry.target)))
				action.save('src/config/moderation/data.json')
				
				# Check SDD
				if check.is_role(member, self.sdd_role):
					for role in member.roles:
						if role.id == self.id['ROLE']['DISCU'] and not role.members:
							channel = self.client.get_channel(self.id['TEXTCHANNEL']['DISCU'])
							await channel.send('```LIBRE```')
						if role.id == self.id['ROLE']['DIALO'] and not role.members:
							channel = self.client.get_channel(self.id['TEXTCHANNEL']['DIALO'])
							await channel.send('```LIBRE```')
			
				try:
					channel_rem = self.client.get_channel(self.id['TEXTCHANNEL']['JOIN_REMOVE'])
					await channel_rem.send('{}#{} a été ban du serveur. :skull_crossbones:'.format(member.name, member.discriminator))
				except:
					await log('ALERTE : accès restreint au salon JOIN_REMOVE')
				
				return
		
		# Départ volontaire
		await log('Départ volontaire', MNT)
		try:
			channel_rem = self.client.get_channel(self.id['TEXTCHANNEL']['JOIN_REMOVE'])
			await channel_rem.send('{}#{} a quitté le serveur.'.format(member.name, member.discriminator))
		except:
			await log('ALERTE : accès restreint au salon JOIN_REMOVE')
			
		if check.is_role(member, self.sdd_role):
			for role in member.roles:
				if role.id == self.id['ROLE']['DISCU'] and not role.members:
					channel = self.client.get_channel(self.id['TEXTCHANNEL']['DISCU'])
					await channel.send('```LIBRE```')
				if role.id == self.id['ROLE']['DIALO'] and not role.members:
					channel = self.client.get_channel(self.id['TEXTCHANNEL']['DIALO'])
					await channel.send('```LIBRE```')
			channel_mod = self.client.get_channel(self.id['TEXTCHANNEL']['MODER'])
			await channel_mod.send(':no_pedestrians: {} a pris la fuite de la SDD !'.format(member.mention))
		
		
	# ON RAW REACTION ADD
	@commands.Cog.listener()
	async def on_raw_reaction_add(self, payload):
		""" Log ou supprime un message via un emoji mis en réaction.
			Donne un rôle SDD en fonction de la place libre avec un troisième emoji
			
		NOTE
		----
		> Pour la SDD, on vérifie le nombre de personnes ayant déjà l'un des deux rôles. Si d'autres personnes ont déjà ce rôle, les nouveaux arrivants iront par défaut dans la seconde salle.
		"""
		guild = self.client.get_guild(GUILD_ID)
		author = guild.get_member(payload.user_id)
		channel = self.client.get_channel(payload.channel_id)
		msg = await channel.fetch_message(payload.message_id)

		# Checks
		if not check.is_role(author, self.id['ROLE']['MODER']):
			return
		if check.is_role(msg.author, self.id['ROLE']['MODER']):
			return
		
		# Emojis
		emoji = payload.emoji
		
		# LOG :eyes:
		if emoji.name == u"\U0001F440":
			if not check.manage_messages_allowed(guild.me) or not check.manage_messages_allowed(author):
				await log('Permission to remove emoji denied', MNT)
				return
			logs = tool.get_data('src/config/moderation/data.json')
			for e in logs:
				if logs[e]['user'] == msg.author.id and logs[e]['log_id'] == payload.message_id:
					return
			action = ACTION('LOG {}'.format(emoji), msg.author.id, author.id, msg.created_at, log_id=msg.id, log_channel=msg.channel.id, log_content=msg.content)
			await msg.remove_reaction(emoji, author)
			
		
		# DEL :x:
		elif emoji.name == u"\U0000274C":
			if not check.manage_messages_allowed(guild.me) or not check.manage_messages_allowed(author):
				await log('Permission to remove emoji denied', MNT)
				return
			action = ACTION('LOG {}'.format(emoji), msg.author.id, author.id, msg.created_at, log_id=msg.id, log_channel=msg.channel.id, log_content=msg.content)
			await msg.delete()
		
##		 SDD :hole:
#		elif emoji.name == u"\U0001F573":
#			print('hole')
#			role_dialo = guild.get_role(self.id['ROLE']['DIALO'])
#			role_discu = guild.get_role(self.id['ROLE']['DISCU'])
#			if (check.is_role(msg.author, role_discu)) or (check.is_role(msg.author, role_dialo)):
#				await log('SDD deja attribuee', MNT)
#				return
#			if not role_dialo.members:
#				if not check.change_role_allowed(role_dialo, guild.me) and not check.change_role_allowed(role_dialo, author):
#					await log('Permission to give role denied', MNT)
#					return
#				await msg.author.add_roles(role_dialo)
#				channel = self.client.get_channel(self.id['TEXTCHANNEL']['DIALO'])
#				if channel.permissions_for(guild.me).send_messages:
#					await channel.send('Bonjour {}'.format(msg.author.mention))
#				else:
#					await log('Permission to write in dialo forbidden', MNT)
#			else:
#				if not check.change_role_allowed(role_discu, guild.me) and not check.change_role_allowed(role_discu, author):
#					await log('Permission to give role denied', MNT)
#					return
#				await msg.author.add_roles(role_discu)
#				channel = self.client.get_channel(self.id['TEXTCHANNEL']['DISCU'])
#				if channel.permissions_for(guild.me).send_messages:
#					await channel.send('Bonjour {}'.format(msg.author.mention))
#				else:
#					await log('Permission to write in discu forbidden', MNT)
#			
#			await msg.remove_reaction(emoji,author)
#			action = ACTION('MISE EN SDD {}'.format(emoji), msg.author.id, author.id, msg.created_at)
#			self.sdd_lock = True
		else:
			return
		
		# Notification dans le salon de log
		EMB = action.embed(self.client, action.color)
		await self.log.send(content=None, embed=EMB)
		
		# Sauvegarde du log
		action.save('src/config/moderation/data.json')
				
	# ON MEMBER BAN
	@commands.Cog.listener()
	async def on_member_ban(self, guild, user):
		""" Notifie les bans uniquement s'ils sont réalisés sur des non-membres du serveur (pour éviter les doublons)"""
		return
			
	# ON MEMBER UPDATE
	@commands.Cog.listener()
	async def on_member_update(self, before, after):
		""" Notifie les mises en SDD si celles-ci ne sont pas le fait d'une commande.
			"Libère" la SDD lorsqu'il n'y a plus personne dedans (laisse un message)
		"""
		
		if after.roles == before.roles:
			return
		
		# CHANGEMENT DE ROLES
		if len(after.roles) > len(before.roles):
			add_role = True
			for item in after.roles:
				if item not in before.roles:
					role = item
					break
			notification = ':green_circle: {} a obtenu le rôle : {}'
		
		else:
			add_role = False
			for item in before.roles:
				if item not in after.roles:
					role = item
					break
			notification = ':red_circle: {} a perdu le rôle : {}'
		
		await log(notification.format(after.name, role.name), MNT)
		
		
		# ANIMATION (rôles spécifiques donnés sur autorole)
		if role.id in self.animation_role:
			log_anim = self.client.get_channel(self.id['TEXTCHANNEL']['LOG_ANIMATION'])
			await log_anim.send(notification.format(after.mention, role.name))
		
		# Mise en SDD
		if not check.is_role(before, self.sdd_role) and check.is_role(after, self.sdd_role):
			await log('{} a été mis en SDD'.format(before.name), MNT, time=True)
			if self.sdd_lock:
				await log('SDD by :hole:', MNT)
				self.sdd_lock = False
				return
			if not check.auditlog_allowed(after.guild.me):
				await log('Access to auditlog denied', MNT)
				return
			await asyncio.sleep(5)
			async for entry in after.guild.audit_logs(action=discord.AuditLogAction.member_role_update, limit=20):
				if entry.target == after and datetime.utcnow() - entry.created_at < timedelta(seconds=10):
					action = ACTION('MISE EN SDD', entry.target.id, entry.user.id, entry.created_at)
					EMB = action.embed(self.client, action.color)
					await self.log.send(content=None, embed=EMB)
					return
			return
		elif check.is_role(before, self.sdd_role) and not check.is_role(after, self.sdd_role):
			lost_role = [role for role in before.roles if role not in set(after.roles)]
			await log('{} a perdu le rôle {}'.format(after.name, lost_role[0].name), MNT)
			await log('{} - {}'.format(lost_role[0].id, self.id['ROLE']['DIALO']), MNT)
			if lost_role[0].id in self.id['ROLE']['DIALO']:
				channel = self.client.get_channel(self.id['TEXTCHANNEL']['DIALO'])
			else:
				channel = self.client.get_channel(self.id['TEXTCHANNEL']['DISCU'])
			await log('Channel : {} - {}'.format(channel.id, channel.name), MNT)
			await log('{} : {}'.format(lost_role[0].name, ['{} -'.format(user.name) for user in lost_role[0].members]), MNT)
			
			if not lost_role[0].members:
				return await channel.send('```LIBRE```')
		else:
			return
		
async def setup(client):
	await client.add_cog(Moderation(client))
