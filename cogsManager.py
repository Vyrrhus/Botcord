""" Cogs Manager Class
"""
import os
import traceback
import importlib
import inspect
from typing import List

import discord
from discord.ext import commands
from src.utils import Paginator

class CogsManager:
    """ Cogs Manager Class """
    def __init__(self, bot: commands.Bot, cogDir: str = "cogs"):
        """ Cogs Manager Constructor """
        self.bot = bot
        self.cogsDir = cogDir
        self.cogs_available = [
            cog[:-3]
            for cog in os.listdir(cogDir)
            if (cog.endswith('.py') and '__init__' not in cog)
        ]

    #--------------------------------------------------------------------------
    @property
    def cogs(self) -> List[str]:
        """ List of active cogs """
        return self._read()
    
    #--------------------------------------------------------------------------
    def docstring(self, cog:str) -> str:
        """ Returns main docstring of the given cog"""
        module = importlib.import_module(f"{self.cogsDir}.{cog}")
        return inspect.getdoc(module)
    
    async def load(self, cog:str):
        """ Load Cog """
        await self.bot.load_extension(f"{self.cogsDir}.{cog}")
        self._append(cog)

    async def unload(self, cog:str):
        """ Unoad Cog """
        await self.bot.unload_extension(f"{self.cogsDir}.{cog}")
        self._remove(cog)

    # Paginator
    async def navigate(self, page: int):
        """ Coroutine for Paginator """
        emb = discord.Embed(title="Gestion des cogs", description="")
        offset = page - 1
        for cog in self.cogs_available[offset:offset+1]:
            docstring = self.docstring(cog)
            emb.description += f"**{cog.capitalize()}**\n{docstring}\n"
        
        n = Paginator.compute_total_pages(len(self.cogs_available), 1)
        emb.set_footer(text=f"Page {page} / {n}")
        return emb, n
    
    #--------------------------------------------------------------------------
    def _read(self, filename='config/extension.config') -> List[str]:
        """ Private function to read extension.config"""
        with open(filename, 'r') as file:
            data = file.read()
        
        if data:    return data.split(',')
        else:       return []

    def _append(
            self, 
            cog: str, 
            filename='config/extension.config') -> None:
        """ Add a new cog to the extension.config file"""
        cogs = self._read()
        if cog not in cogs:
            cogs.append(cog)
        
            with open(filename, 'w') as file:
                file.write(','.join(cogs))
    
    def _remove(
            self,
            cog: str,
            filename='config/extension.config') -> None:
        """ Remove a cog from the extension.config file"""
        cogs = self._read()
        if cog in cogs:
            cogs.remove(cog)

            with open(filename, 'w') as file:
                file.write(','.join(cogs))

class CogsPaginator(Paginator):
    """ Paginator extended for Cogs Manager """
    activeCog   = {
        "style": discord.ButtonStyle.red,
        "label": f"{'Désactiver cog':^15}"
        }
    inactiveCog = {
        "style": discord.ButtonStyle.green,
        "label": f"{'Activer cog':^15}"
        }
    
    def __init__(
            self,
            interaction: discord.Interaction,
            manager: CogsManager
            ) -> None:
        """ Cogs Paginator Constructor"""
        self.manager = manager
        super().__init__(interaction, manager.navigate, withFastButtons=False)

    #--------------------------------------------------------------------------
    
    async def start(self):
        """ Start View """
        buttons = self.children

        for button in self.children:
            self.remove_item(button)

        idx = len(buttons) // 2
        buttons[idx:idx] = [buttons.pop()]

        for button in buttons:
            self.add_item(button)
        
        await super().start()
    
    def update_buttons(self):
        """ Update buttons"""
        super().update_buttons()

        idxToggle = len(self.children) // 2
        # Set active or inactive style for toggle button
        print(self.manager.cogs_available)
        print(self.manager.cogs)
        if self.manager.cogs_available[self.index - 1] in self.manager.cogs:
            self.children[idxToggle].style = self.activeCog["style"]
            self.children[idxToggle].label = self.activeCog["label"]
        else:
            self.children[idxToggle].style = self.inactiveCog["style"]
            self.children[idxToggle].label = self.inactiveCog["label"]

    #--------------------------------------------------------------------------
    @discord.ui.button(label="Button")
    async def toggle(
        self,
        interaction: discord.Interaction,
        button: discord.Button):
        """ Toggle Cogs """
        cog = self.manager.cogs_available[self.index - 1]

        # Disable
        if cog in self.manager.cogs:
            await self.manager.unload(cog)
            button.style = self.activeCog["style"]
            button.label = self.activeCog["label"]

        # Enable
        else:
            await self.manager.load(cog)
            button.style = self.inactiveCog["style"]
            button.label = self.inactiveCog["label"]
