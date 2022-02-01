import discord
import asyncio
from numpy import random as rand
from discord.ext import commands

from src.config.settings import MONITOR_MAIN as MNT

class Melanchon(commands.Cog):
    def __init__(self, client):
        self.client  = client
        self.msgList = ['melanchon', 'mélanchon']
    
    ####################
	#   EVENTS
	###
    
    # ON MESSAGE
    @commands.Cog.listener()
    async def on_message(self, message):
        """
            Corrige les Mélanchon en Mélenchon
        """
        content = message.content.lower()
        check = [el in content for el in self.msgList]

        if True in check:
            tweet = ['https://twitter.com/T_Bouhafs/status/1468982780264693763',
                     'https://twitter.com/T_Bouhafs/status/1488492002165542912']
            await message.channel.send('{} : {}'.format(message.author.mention, tweet[rand.randint(2)]))            

def setup(client):
	client.add_cog(Melanchon(client))