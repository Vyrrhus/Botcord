import discord
import sys
from src import check
from discord.ext import commands

from src.config.settings import MONITOR_MAIN as MNT

class Cmd(commands.Cog):
    def __init__(self, client):
        self.client  = client

    ###########################################
	#                  CHECKS                 #
	###########################################
	
	# COG LOCAL CHECK
    async def cog_check(self, ctx):
        """ Test : modérateur only in right channel
		"""
        try:
            return check.check_is_me(ctx)
        except:
            return False
    
    ###########################################
	#                COMMANDS                 #
	###########################################
	# COMMAND: ?version
    @commands.command(name='ver', pass_context=True)
    async def ver(self, ctx, *text):
        await ctx.channel.send("Version python en cours : {}".format(sys.version))

def setup(client):
	client.add_cog(Cmd(client))