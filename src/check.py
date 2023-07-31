""" Decorators for checks
"""
import discord
from discord import app_commands
from config.config import ClassID

###############################################################################
#   INTERACTIONS CHECK DECORATORS

def is_owner(id: ClassID):
	def predicate(interaction: discord.Interaction) -> bool:
		return interaction.user.id == id.owner
	return app_commands.check(predicate)

def check_category(id: int):
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.channel.category_id == id
    return app_commands.check(predicate)

def check_channel(id: int):
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.channel_id == id
    return app_commands.check(predicate)
