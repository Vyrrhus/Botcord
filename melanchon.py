import discord
import asyncio
from numpy import random as rand
from discord.ext import commands
import asyncio

from src.config.settings import MONITOR_MAIN as MNT

class Melanchon(commands.Cog):
    def __init__(self, client):
        self.client  = client
        self.msgList = ['melanchon', 'mélanchon']
        self.lepen = ['le pen', 'lepen']
        self.lepen_send = False
    
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

    
    # Ajoute un message pour Le Pen
        check_lepen = [el in content for el in self.lepen]
        check_vote  = [el in content for el in ["vote", "voter"]]

        if True in check_lepen and True in check_vote and not self.lepen_send:
            await message.channel.send('{}, :loudspeaker: **Il ne faut pas donner une seule voix à Madame Le Pen !** :loudspeaker:'.format(message.author.name))
            self.lepen_send = True
            await asyncio.sleep(1800)
            self.lepen_send = False


def setup(client):
	client.add_cog(Melanchon(client))