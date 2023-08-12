""" Cogs Manager Class
"""
import os
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
        self.embed = discord.Embed(title="Gestion des cogs", description="")
        self.cogs_available = [
            cog[:-3]
            for cog in os.listdir(cogDir)
            if (cog.endswith('.py') and '__init__' not in cog)
        ]

    #--------------------------------------------------------------------------
    @property
    def cogs(self) -> List[str]:
        """ List of active cogs """
        return CogsManager.read()
    
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
        """ Unload Cog """
        await self.bot.unload_extension(f"{self.cogsDir}.{cog}")
        self._remove(cog)

    # Paginator
    async def navigate(self, page: int):
        """ Coroutine for Paginator """
        offset = page - 1
        for cog in self.cogs_available[offset:offset+1]:
            docstring = self.docstring(cog)
            self.embed.description = f"**{cog.capitalize()}**\n{docstring}\n"
        
        n = Paginator.compute_total_pages(len(self.cogs_available), 1)
        self.embed.set_footer(text=f"Page {page} / {n}")
        return self.embed, n
    
    #--------------------------------------------------------------------------
    def _append(
            self, 
            cog: str, 
            filename='config/extension.config') -> None:
        """ Add a new cog to the extension.config file"""
        cogs = CogsManager.read(filename)
        if cog not in cogs:
            cogs.append(cog)
        
            with open(filename, 'w') as file:
                file.write(','.join(cogs))
    
    def _remove(
            self,
            cog: str,
            filename='config/extension.config') -> None:
        """ Remove a cog from the extension.config file"""
        cogs = CogsManager.read(filename)
        if cog in cogs:
            cogs.remove(cog)

            with open(filename, 'w') as file:
                file.write(','.join(cogs))

    #--------------------------------------------------------------------------
    #   STATIC METHOD
    @staticmethod
    def read(filename='config/extension.config') -> List[str]:
        """ Read extension.config """
        with open(filename, 'r') as file:
            data = file.read()
        
        if data:    return data.split(',')
        else:       return []

    @staticmethod
    async def reload(bot: commands.Bot):
        """ Reload all cogs loaded """
        for cog in CogsManager.read():
            await bot.reload_extension(f"cogs.{cog}")

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
        self.clear_items()

        idx = len(buttons) // 2
        buttons[idx:idx] = [buttons.pop()]

        for button in buttons:
            self.add_item(button)
        
        await super().start(isEphemeral=False)
    
    def update_buttons(self):
        """ Update buttons"""
        super().update_buttons()

        idxToggle = len(self.children) // 2
        # Set active or inactive style for toggle button
        if self.manager.cogs_available[self.index - 1] in self.manager.cogs:
            self.children[idxToggle].style = self.activeCog["style"]
            self.children[idxToggle].label = self.activeCog["label"]
        else:
            self.children[idxToggle].style = self.inactiveCog["style"]
            self.children[idxToggle].label = self.inactiveCog["label"]

    #--------------------------------------------------------------------------
    @discord.ui.button(label="Button", row=4)
    async def toggle(
        self,
        interaction: discord.Interaction,
        button: discord.Button):
        """ Toggle Cogs """
        cog = self.manager.cogs_available[self.index - 1]

        # Disable
        if cog in self.manager.cogs:
            await self.manager.unload(cog)
            button.style = self.inactiveCog["style"]
            button.label = self.inactiveCog["label"]

        # Enable
        else:
            await self.manager.load(cog)
            button.style = self.activeCog["style"]
            button.label = self.activeCog["label"]
        
        await interaction.response.edit_message(
            embed=self.manager.embed, 
            view=self)
