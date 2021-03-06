import discord

def is_owner(member):
	"""True if is me
	"""
	return member.id == 246321888693977088

def check_is_me(ctx):
	return is_owner(ctx.author)

def in_channel(channel, channel_id):
	""" True if #moderation_animation
	"""
	return channel.id in channel_id

def is_role(member, roles_id):
	""" True if member has any of the roles in roles_id list
	"""
	if not is_member(member):
		return False
	return any(role.id in roles_id for role in member.roles)

def kick_allowed(target, author):
	""" True if author can kick target
	"""
	return author.guild_permissions.kick_members and target.top_role < author.top_role

def ban_allowed(target, author):
	""" True if author can ban target
	"""
	return author.guild_permissions.ban_members and target.top_role < author.top_role

def auditlog_allowed(member):
	""" True if member can access logs"""
	return member.guild_permissions.view_audit_log

def change_role_allowed(role, member):
	""" True if member can add this role
	"""
	return member.guild_permissions.manage_roles and member.top_role > role

def manage_messages_allowed(member):
	""" True if member can delete message
	"""
	return member.guild_permissions.manage_messages

def manage_emojis_allowed(member):
	""" True if member can delete emojis reactions
	"""
	return member.guild_permissions.manage_emojis

def mute_allowed(member):
	""" True if member can mute someone
	"""
	return member.guild_permissions.mute_members

def move_allowed(member):
	""" True if member can move someone
	"""
	return member.guild_permissions.move_members

def is_member(member):
	if isinstance(member, discord.Member):
		return True
	else:
		return False