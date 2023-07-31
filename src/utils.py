""" Utilitary tools for Botcord
"""
import discord
from typing import Callable, Optional

class Paginator(discord.ui.View):
    def __init__(
            self, 
            interaction: discord.Interaction, 
            get_page: Callable,
            withFastButtons: bool = True
            ) -> None:
        """ Paginator Constructor """
        self.interaction     = interaction
        self.get_page        = get_page
        self.withFastButtons = withFastButtons

        self.total_pages: Optional[int] = None
        self.index = 1
        super().__init__(timeout=100)

    async def interaction_check(
            self, 
            interaction: discord.Interaction
            ) -> bool:
        """ Only author can interact """
        if interaction.user == self.interaction.user:
            return True
        else:
            emb = discord.Embed(
                description=(
                f"Only the author of the command can perform this "
                f"action."
                ),
                color=16711680
            )
            await interaction.response.send_message(
                embed=emb, 
                ephemeral=True)
            return False

    async def start(self):
        """ Start View """
        emb, self.total_pages = await self.get_page(self.index)

        # Single page
        if self.total_pages == 1:
            await self.interaction.response.send_message(
                embed=emb,
                ephemeral=True)

        # Multiple pages
        elif self.total_pages > 1:

            # Fast Buttons Removed
            if not self.withFastButtons:
                print(self.children)
                fastprevious = self.children[0]
                fastnext     = self.children[-1]
                self.remove_item(fastprevious)
                self.remove_item(fastnext)
                print(self.children)
                pass

            self.update_buttons()
            await self.interaction.response.send_message(
                embed=emb,
                ephemeral=True, 
                view=self)

    async def edit_page(self, interaction: discord.Interaction):
        """ Navigate through pages when on_click event """
        emb, self.total_pages = await self.get_page(self.index)
        self.update_buttons()
        await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        """ Update buttons """
        # Disable buttons whenever useful
        self.children[0].disabled  = self.index == 1
        self.children[-1].disabled = self.index == self.total_pages

        if self.withFastButtons:
            self.children[1].disabled  = self.index == 1
            self.children[-2].disabled = self.index == self.total_pages

    @discord.ui.button(label="\U000023ee")
    async def fastprevious(
        self, 
        interaction: discord.Interaction, 
        button: discord.Button):
        """ Go to first page """
        self.index = 1
        await self.edit_page(interaction)

    @discord.ui.button(label="\U000025c0")
    async def previous(
        self, 
        interaction: discord.Interaction, 
        button: discord.Button):
        """ Go to previous page """
        self.index -= 1
        await self.edit_page(interaction)
    
    @discord.ui.button(label="\U000025b6")
    async def next(
        self, 
        interaction: discord.Interaction, 
        button: discord.Button):
        """ Go to next page """
        self.index += 1
        await self.edit_page(interaction)
    
    @discord.ui.button(label="\U000023ed")
    async def fastnext(
        self,
        interaction: discord.Interaction,
        button: discord.Button):
        """ Go to last page """
        self.index = self.total_pages
        await self.edit_page(interaction)

    async def on_timeout(self):
        # remove buttons on timeout
        message = await self.interaction.original_message()
        await message.edit(view=None)

    @staticmethod
    def compute_total_pages(
        total_results: int, 
        results_per_page: int) -> int:
        return ((total_results - 1) // results_per_page) + 1