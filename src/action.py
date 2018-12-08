import datetime
import src.tool as tool
from src.config.settings import GUILD_ID

class ACTION:
	"""Représente une action de modération (kick, warn, ban, log).
	
	Attributs
	---------
	lib : str
		Libellé de l'action
	user : int
		ID de la cible
	author: int
		ID de l'auteur
	time : datetime.datetime
		date de création (UTC local)
	reason : None | str
		auditlog associé
	message : None | str
		message à destination de la cible
	log_id : None | int
		si LOG, ID du message associé
	log_channel : None | int
		si LOG, ID du TextChannel associé
	log_content : None | str
		si LOG, contenu du message
	num : int
		numéro attribué à l'objet
		
	Méthodes
	--------
	embed() :
		retourne une classe embed
	"""
	 
	__slots__ = ['lib', 'user', 'author', 'time', 'reason', 'message', 'log_id', 'log_channel', 'log_content', 'num']
	
	def __init__(self, lib, user, author, time, reason=None, message=None, log=None):
		
		# Attributs déclarés
		self.lib = lib
		self.user = user.id
		self.author = author.id
		self.time = time
		self.reason = reason
		self.message = message
		if not log:
			self.log_id = None
			self.log_channel = None
			self.log_content = None
		else:
			self.log_id = log.id
			self.log_channel = log.channel.id
			self.log_content = log.content
		
		# Num
		with open('src/config/moderation/num.txt', 'r+') as file:
			num = int(file.read()) + 1
			file.seek(0)
			file.truncate()
			file.write(str(num))
			print('----- {} N°{} créée !'.format(self.lib, str(num)))
		self.num = num
		
	def userinfo(self, client, user):
		guild = client.get_guild(GUILD_ID)
		# Member
		if guild.get_member(user):
			user = guild.get_member(user)
		elif client.get_user(user):
			user = client.get_user(user)
		else:
			user, user_mention = "#deleted_user"
		# Mention
		try:
			user_mention = user.mention
		except:
			user_mention = str(user)
		# Icon
		try:
			user_icon = user.avatar_url
		except:
			user_icon = None
			
		return user, user_mention, user_icon
		
	def embed(self, client, embed_color):
		"""Retourne un message embed
		"""
		# USER & AUTHOR
		user, user_mention, user_icon = self.userinfo(client, self.user)
		author, author_mention, author_icon = self.userinfo(client, self.author)
		
		# FIELDS
		field_list = []
		field_list.append(tool.set_field(name='Utilisateur :', value=user_mention, inline=False))
		field_list.append(tool.set_field(name='\nModerateur :', value=author_mention))

		# Warn, Kick & Ban
		if self.reason:
			field_list.append(tool.set_field(name='\nRaison :', value=self.reason, inline=False))
		if self.message:
			field_list.append(tool.set_field(name='\nMessage envoyé :', value=self.message, inline=False))
		
		# Log field
		if self.log_id:
			textchannel = client.get_channel(self.log_channel)
			if textchannel:
				field_list.append(tool.set_field(name='\nDans #{} :'.format(channel.name), value=self.log_content, inline=False))
			else:
				field_list.append(tool.set_field(name='\n Dans #deleted_channel :', value=self.log_content, inline=False))
		
		# EMBED
		EMB = tool.set_embed(color=embed_color,
							 author='{} - N°{} | {}'.format(self.lib, str(self.num), str(user)),
							 author_icon=user_icon,
							 thumbnail=user_icon,
							 footer_text='ID : {}'.format(str(self.user)),
							 timestamp=self.time,
							 fields=field_list)
		
		return EMB
