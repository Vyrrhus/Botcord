import discord
import asyncio
import random
from datetime import datetime
from datetime import timedelta

import src.check as check
import src.tool as tool
from src.tool import log

from discord.ext import commands
from src.config.settings import data
from src.action import ACTION
#from src.note import NOTE

class Moderation:
	def __init__(self, client):
		self.client = client
		self.exit_lock = False
		
	###########################################
	#            COROUTINE TASK               #
	###########################################	
	
	"""No task in this module"""
	
	
	###########################################
	#                  CHECKS                 #
	###########################################
	
	# LOCAL CHECK
	async def __local_check(self, ctx):
		"""	Les commandes de ce cog ne peuvent être utilisées que par un staff ou un modérateur.
			En outre, elles ne sont utilisables que dans le salon de modération
		"""
		try:
			return check.is_moderator(ctx.author) and check.in_moderation_channel(ctx.channel)
		except:
			await log('moderation local check failed')
			return False
		
	###########################################
	#                COMMANDS                 #
	###########################################
	
	# BEFORE HOOK
	async def __before_invoke(self, ctx):
		""" BEFORE HOOK FUNC
		"""
		return

	# WARN COMMAND
	@commands.command(name='warn', pass_context=True)
	async def warn(self, ctx, target:discord.Member, *, text):
		""" Envoie un warn à l'user
		"""
		# Checks
		if check.is_moderator(target):
			await log('WARN - target role invalide')
			return
		
		# Action
		action = ACTION('Warn', target, ctx.message.author, ctx.message.created_at, message=text)
		EMB = action.embed(self.client, 0xaa8800)
		
		# Notification aux modérateurs
		await self.client.get_channel(data['ID']['SALON_LOG']).send(content=None, embed=EMB)
		await ctx.channel.send('{} a reçu un warn :telephone:'.format(target.mention))
		
		# Envoi du warn
		await target.send(data['TEXT']['WARN'].format(text))
		
		# Sauvegarde du log
		pass
	
	# KICK COMMAND
	@commands.command(name='kick', pass_context=True)
	async def kick(self, ctx, target: discord.Member, *, text):
		""" Kick un user (message optionnel)
		"""
		# Checks
		if check.is_moderator(target):
			await log('KICK - target role onvalide')
			return
		if not check.kick_allowed(target, ctx.message.author) or not check.kick_allowed(target, ctx.guild.me):
			await log('KICK - permission de kick refusée')
			return
		
		# Séparation du text en message + auditlog
		message, auditlog = tool.extract_text(text)
		if not auditlog:
			await log('KICK - auditlog not given')
			return await ctx.channel.send("Auditlog manquant : ?kick [message envoyé] auditlog")
		if len(auditlog) > 512:
			await log('KICK - auditlog too long (512 char max)')
			return await ctx.channel.send("Auditlog trop long *({}/512 caractères max)*".format(len(auditlog)))
		
		# ACTION
		action = ACTION('Kick', target, ctx.message.author, ctx.message.created_at, message=message, reason=auditlog)
		EMB = action.embed(self.client, 0x995500)
		
		# Notification aux modérateurs
		await self.client.get_channel(data['ID']['SALON_LOG']).send(content=None, embed=EMB)
		await ctx.channel.send('{} a été kick du serveur :hammer:'.format(target.mention))
		
		# Kick
		if message:
			await target.send(data['TEXT']['KICK']['with_msg'].format(message))
		else:
			await target.send(data['TEXT']['KICK']['with_no_msg'])
		await target.kick(reason=auditlog)
		
		# Sauvegarde du log
		pass
		
	@commands.command(name='libre', pass_context=True)
	async def libre(self, ctx):
		await ctx.channel.send('```LIBRE```')
		
	###########################################
	#                 EVENTS                  #
	###########################################
		
	# ON MEMBER JOIN
	async def on_member_join(self, member):
		""" Vérifie les logs des nouveaux arrivants
		"""
		await log('{} a rejoint le serveur'.format(member.name), time=True)
				
	# ON MEMBER REMOVE	
	async def on_member_remove(self, member):
		""" Notifie les kicks / bans si ceux-ci ne sont pas dûs à une commande.
			Notifie aussi les fuites de SDD (quelqu'un quitte de lui-même le serveur avec un rôle SDD)
		
		NOTE
		----
		> L'accès à l'auditlog est défaillant et peut parfois poser problèmes (léger lag entre le kick/ban et l'entrée correspondante dans l'auditlog).
		  Pour y palier, on a mis un délai de 5s avant lecture de l'auditlog, puis on récupère les 20 dernières entrées (en supposant en cas de raid jusqu'à 20 kick / bans en 5s) pour vérifier si l'une d'entre elle correspond.
		  C'est à dire si l'entrée a été faite il y a moins de 5s, correspond à un kick / ban et concerne l'utilisateur souhaité.
		"""
		await log('{} a quitté le serveur'.format(member.name), time=True)
		
		# Commande utilisée:
		if self.exit_lock:
			self.exit_lock = False
			return await log('verrou actif: commande')
		
		guild = self.client.get_guild(data['ID']['GUILD'])
		if not check.auditlog_allowed(guild.me):
			return await log("HAL 9000 n'a pas accès à l'auditlog")
		await asyncio.sleep(5)
		
		# Kick
		async for entry in guild.audit_logs(action=discord.AuditLogAction.kick, limit=20):
			await log('KICK : auditlog timer')
			await log(str(datetime.utcnow()-entry.created_at))
			if datetime.utcnow() - entry.created_at < timedelta(0,10):
				break
			if entry.target == member:
				await log("KICK manuel")
				action = ACTION('Kick', entry.target, entry.user, entry.created_at, reason=entry.reason)
				EMB = action.embed(self.client, 0x995500)
				await self.client.get_channel(data['ID']['SALON_LOG']).send(content=None, embed=EMB)
				await self.client.get_channel(data['ID']['SALON_MODERATION']).send(':hammer: {} a été kick du serveur.'.format(str(entry.target)))
				
				# Check SDD
				if check.is_sdd(member):
					for role in member.roles:
						if role.id == data['ID']['ROLE_DISCUSSION'] and not role.members:
							channel = self.client.get_channel(data['ID']['SALON_DISCUSSION'])
							await channel.send('```LIBRE```')
						if role.id == data['ID']['ROLE_DIALOGUE'] and not role.members:
							channel = self.client.get_channel(data['ID']['SALON_DIALOGUE'])
							await channel.send('```LIBRE```')
				return
		
		# Ban
		async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=20):
			if datetime.utcnow() - entry.created_at < timedelta(0,10):
				break
			if entry.target == member:
				await log('BAN manuel')
				action = ACTION('Ban', entry.target, entry.user, entry.created_at, reason=entry.reason)
				EMB = action.embed(self.client, 0x550000)
				await self.client.get_channel(data['ID']['SALON_LOG']).send(content=None, embed=EMB)
				await self.client.get_channel(data['ID']['SALON_MODERATION']).send(':skull_crossbones: {} a été ban du serveur.'.format(str(entry.target)))
				
				# Check SDD
				if check.is_sdd(member):
					for role in member.roles:
						if role.id == data['ID']['ROLE_DISCUSSION'] and not role.members:
							channel = self.client.get_channel(data['ID']['SALON_DISCUSSION'])
							await channel.send('```LIBRE```')
						if role.id == data['ID']['ROLE_DIALOGUE'] and not role.members:
							channel = self.client.get_channel(data['ID']['SALON_DIALOGUE'])
							await channel.send('```LIBRE```')
				return
		
		# Départ volontaire
		if check.is_sdd(member):
			for role in member.roles:
				if role.id == data['ID']['ROLE_DISCUSSION'] and not role.members:
					channel = self.client.get_channel(data['ID']['SALON_DISCUSSION'])
					await channel.send('```LIBRE```')
				if role.id == data['ID']['ROLE_DIALOGUE'] and not role.members:
					channel = self.client.get_channel(data['ID']['SALON_DIALOGUE'])
					await channel.send('```LIBRE```')
			await self.client.get_channel(data['ID']['SALON_MODERATION']).send(':no_pedestrians: {} a pris la fuite de la SDD !'.format(member.mention))
		
		
	# ON RAW REACTION ADD
	async def on_raw_reaction_add(self, payload):
		""" Log ou supprime un message via un emoji mis en réaction.
			Donne un rôle SDD en fonction de la place libre avec un troisième emoji
			
		NOTE
		----
		> Pour la SDD, on vérifie le nombre de personnes ayant déjà l'un des deux rôles. Si d'autres personnes ont déjà ce rôle, les nouveaux arrivants iront par défaut dans la seconde salle.
		"""
		return
	
	# ON MEMBER BAN
	async def on_member_ban(self, guild, user):
		""" Notifie les bans uniquement s'ils sont réalisés sur des non-membres du serveur (pour éviter les doublons)"""
		return
			
	# ON MEMBER UPDATE
	async def on_member_update(self, before, after):
		""" Notifie les mises en SDD si celles-ci ne sont pas le fait d'une commande.
			"Libère" la SDD lorsqu'il n'y a plus personne dedans (laisse un message)
		"""
		
		# Mise en SDD
		if not check.is_sdd(before) and check.is_sdd(after):
			await log('{} a été mis en SDD'.format(before.name), time=True)
			return
		elif check.is_sdd(before) and not check.is_sdd(after):
			lost_role = [role for role in before.roles if role not in set(after.roles)]
			await log('{} a perdu le rôle {}'.format(after.name, lost_role[0].name))
			if lost_role[0].id == data['ID']['ROLE_DIALOGUE']:
				channel = self.client.get_channel(data['ID']['SALON_DIALOGUE'])
			else:
				channel = self.client.get_channel(data['ID']['SALON_DISCUSSION'])
			if not lost_role[0].members:
				return await channel.send('```LIBRE```')
		else:
			return
		
def setup(client):
	client.add_cog(Moderation(client))