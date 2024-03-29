""" Decorators for checks
"""
from typing import List
import discord
from discord import app_commands
from config.config import OWNER, ConfigBot

###############################################################################
#   INTERACTIONS CHECK DECORATORS

#------------------------------------------------------------------------------
#   GENERAL CHECKS
def is_category(id: int):
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.channel.category_id == id
    return app_commands.check(predicate)

def is_channel(id: int):
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.channel_id == id
    return app_commands.check(predicate)

def is_role(id: List[int]):
    def predicate(interaction: discord.Interaction) -> bool:
        return any(
            item in [role.id for role in interaction.user.roles]
            for item in id)
    return app_commands.check(predicate)

#------------------------------------------------------------------------------
#   SPECIFIC CHECKS
def is_owner():
	def predicate(interaction: discord.Interaction) -> bool:
		return interaction.user.id == OWNER
	return app_commands.check(predicate)

def is_staff():
    return is_role(ConfigBot().role.staff)

def can_kick():
     def predicate(interaction: discord.Interaction) -> bool:
          return interaction.user.guild_permissions.kick_members
     return app_commands.check(predicate)