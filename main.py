#!/opt/Botcord/.pyenv/bin/python
# @author : Vyrrhus
"""
BOT DE MODÉRATION DU DISCORD INSOUMIS
- voir https://discordpy.readthedocs.io/en/stable/# -
"""

import discord
from discord.ext import commands
import asyncio
import sys, traceback
from utils import *
from config.id import OWNER_ID

##################
# SETTINGS
##################

# TOKEN
try:
    TOKEN = read('config/token.config')
except:
    traceback.print_exc()
    sys.exit()

# PREFIX
try:
    PREFIX = read('config/prefix.config')
except:
    traceback.print_exc()
    PREFIX = '$'

# VERSION
try:
    VERSION = read('config/version.config')
except:
    traceback.print_exc()
    sys.exit()

# BOT
bot = commands.Bot(command_prefix=PREFIX, 
                   intents=discord.Intents.all(),
                   owner_id=OWNER_ID)

##################
# OWNER COMMANDS
##################

@bot.command(name='version', hidden=True)
@commands.is_owner()
async def _version(ctx):
    await ctx.send(f"Version du bot : {VERSION}", reference=ctx.message)

# LOGOUT
@bot.command(name='logout', aliases=['close'], hidden=True)
@commands.is_owner()
async def _logout(ctx):
    await Console(bot).print(f"Log out :zzz:")
    await bot.close()

# EXTENSIONS
@bot.command(name='extension', hidden=True)
@commands.is_owner()
async def _extension(ctx):
    extensions = read('config/extension.config', split=True)
    if extensions:
        await ctx.send(f":memo: {len(extensions)} extensions actives : {', '.join(extensions)}", reference=ctx.message)
    else:
        await ctx.send(f":x: Aucune extension active.", reference=ctx.message)

@bot.command(name='enable', aliases=['activate', 'load'], hidden=True)
async def _enable(ctx, extensions):
    extensions = extensions.split(',')
    
    active = []
    for ext in extensions:
        try:
            await bot.load_extension(f"cogs.{ext}")
            active.append(ext)
        except:
            traceback.print_exc()
    write_append('config/extension.config', active)
    if len(active) > 0:
        em = discord.Embed(color=ctx.author.color, description=f"Extension activée : **{', '.join(active)}**", timestamp=ctx.message.created_at)
        await ctx.send(embed=em, reference=ctx.message)
    else:
        await ctx.send(f"{', '.join(extensions)} n'a pas pu être chargée", reference=ctx.message)

@bot.command(name='disable', aliases=['desactivate', 'unload'], hidden=True)
async def _disable(ctx, extensions):
    if extensions == 'all' or extensions == '*':
        extensions = read('config/extension.config', split=True)
    else:
        extensions = extensions.split(',')

    inactive = []
    for ext in extensions:
        try:
            await bot.unload_extension(f"cogs.{ext}")
            inactive.append(ext)
        except:
            traceback.print_exc()
        
    write_remove('config/extension.config', inactive)
    if len(inactive) > 0:
        em = discord.Embed(color=ctx.author.color, description=f"Extension désactivée : **{', '.join(inactive)}**", timestamp=ctx.message.created_at)
        await ctx.send(embed=em, reference=ctx.message)
    else:
        await ctx.send(f"{', '.join(extensions)} n'a pas pu être enlevée", reference=ctx.message)

# COMMANDE
@bot.command(name='command', hidden=True)
@commands.is_owner()
async def _command(ctx, *command):
    print(f"Commande à exécuter : {' '.join(command)}")

##################
# MAIN EVENTS
##################

@bot.event
async def on_ready():
    await Console(bot).print(f"Bot ready : v{VERSION}")
    print(f"Bot ready : v{VERSION}")

##################
# RUN
##################

async def start():
    EXTENSIONS = read('config/extension.config', split=True)
    for ext in EXTENSIONS:
        try:
            await bot.load_extension(f"cogs.{ext}")
            print(f"Cog : [{ext}] actif")
        except:
            traceback.print_exc()
            pass
    
    try:
        await bot.start(TOKEN)
    except:
        traceback.print_exc()
        sys.exit()

if __name__ == '__main__':
    asyncio.run(start())