#!/opt/Botcord/.pyenv/bin/python
"""
@author: Vyrrhus

Documentation of discord.py is available at :
> https://discordpy.readthedocs.io/en/stable/# -
"""
import discord
from discord.ext import commands
import asyncio
from src import check
from cogsManager import *

###############################################################################
#   SETTINGS
from config.config import TOKEN, PREFIX, OWNER
from config.__version__ import VERSION

###############################################################################
#   BOT
BOTCORD = commands.Bot(
    command_prefix=PREFIX,
    owner_id=OWNER,
    intents=discord.Intents.all()
    )

#------------------------------------------------------------------------------
# SYNC COMMAND (to update slash commands to the command tree)
@BOTCORD.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context) -> None:
    """ Sync slash commands to the guild"""
    bot: commands.Bot = ctx.bot
    bot.tree.copy_global_to(guild=ctx.guild)
    synced = await bot.tree.sync(guild=ctx.guild)
    await ctx.send(
        f"Synchronisation de {len(synced)} commandes sur ce serveur.",
        ephemeral=True
    )

#------------------------------------------------------------------------------
# EVENT
@BOTCORD.event
async def on_ready():
    print(f"Logged in as {BOTCORD.user} (ID : {BOTCORD.user.id})")
    print(f"------")

    manager = CogsManager(BOTCORD)
    if manager.cogs:
        for cog in manager.cogs:
            try:
                await manager.load(cog)
            except commands.errors.ExtensionAlreadyLoaded:
                pass
    else:
        print("Aucun cog n'est activé.")


#------------------------------------------------------------------------------
# VERSION
@BOTCORD.tree.command(name='version')
@check.is_owner()
async def _version(interaction: discord.Interaction):
    """ Version du bot """
    await interaction.response.send_message(
        f"Version du bot : :robot: {VERSION}",
        ephemeral=False
        )

#------------------------------------------------------------------------------
# LOGOUT
@BOTCORD.tree.command(name='logout')
@check.is_owner()
async def _logout(interaction: discord.Interaction):
    """ Log out le bot """
    await interaction.response.send_message(f"Log out :zzz:")
    await BOTCORD.close()

#------------------------------------------------------------------------------
# COGS MANAGER
@BOTCORD.tree.command(name='cogs')
@check.is_staff()
async def _cogs(interaction: discord.Interaction):
    """ Cogs Manager """
    manager = CogsManager(BOTCORD)
    await CogsPaginator(interaction, manager).start()


###############################################################################
#   RUN

if __name__ == '__main__':
    # asyncio.run(start())
    BOTCORD.run(TOKEN)
