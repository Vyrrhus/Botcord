""" Cette extension permet de modifier la configuration du bot :
"""
import discord
from discord.ext import commands
from discord import app_commands

from src.utils import Paginator
from config.config import SetupManager, GUILD
from src import check

class SetupPaginator(Paginator):
    """ Setup Paginator """
    def __init__(
            self,
            interaction: discord.Interaction,
            manager: SetupManager
    ) -> None:
        self.manager = manager
        self.buttonRole: discord.ui.Item
        self.buttonChannel: discord.ui.Item
        super().__init__(interaction, manager.navigate)

    #--------------------------------------------------------------------------
    async def start(self):
        self.buttonChannel = self.children[-1]
        self.buttonRole    = self.children[-2]
        self.remove_item(self.buttonChannel)
        self.remove_item(self.buttonRole)

        super().start(isEphemeral=False)

    def update_buttons(self):
        # Remove select Items
        self.remove_item(self.buttonChannel)
        self.remove_item(self.buttonRole)

        # Update Buttons
        super().update_buttons()
        
        # Add a single select Item
        if self.manager.currentGroup == "role":
            self.add_item(self.buttonRole)
        if self.manager.currentGroup == "channel":
            self.add_item(self.buttonChannel)

    #--------------------------------------------------------------------------
    @discord.ui.select(
        cls=discord.ui.RoleSelect,
        min_values=1,
        placeholder="Sélectionner le·s rôle·s...",
        row=0)
    async def selectRole(
        self,
        interaction: discord.Interaction,
        select: discord.ui.RoleSelect):
        """ Selecting roles Coroutine"""
        roles_id = [value.id for value in select.values]
        
        # Set new parameters
        group = self.manager.currentGroup
        param = self.manager.currentParam
        self.manager.config.set_params({f"{group}_{param}": roles_id})

        # Save
        self.manager.config.to_json()

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        min_values=1,
        placeholder="Sélectionner le·s canal·aux",
        row=0)
    async def selectChannel(
        self,
        interaction: discord.Interaction,
        select: discord.ui.ChannelSelect):
        """ Selecting channel Coroutine """
        channels_id = [value.id for value in select.values]
        
        # Set new parameters
        group = self.manager.currentGroup
        param = self.manager.currentParam
        self.manager.config.set_params({f"{group}_{param}": channels_id})

        # Save
        self.manager.config.to_json()

class SetupCog(commands.Cog):
    """ SetupCog Class """
    def __init__(self, bot: commands.Bot):
        """ SetupCog Constructor """
        print(f"Cog [{self.__cog_name__}] activé.")
        self.bot     = bot
        self.manager = SetupManager(self.bot)
        
    #--------------------------------------------------------------------------
    #   SLASH COMMANDS
    @app_commands.command(name="setup")
    @app_commands.guilds(GUILD)
    @check.is_staff()
    async def _setupCommand(
        self, 
        interaction: discord.Interaction
        ):
        """ Setup Manager
        """
        view = SetupPaginator(interaction, self.manager)
        await view.start()

async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))