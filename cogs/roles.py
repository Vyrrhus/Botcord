""" Cette extension s'occupe de la gestion des roles :
    ▫️ `/role` : lorsqu'un membre obtient ou perd l'un des rôles 
    sélectionnés, une notification se fait dans le canal où la
    commande a été faite.
"""
from typing import Dict, List
import discord
from discord.ext import commands
from discord import app_commands
import json

from config.config import GUILD
import src.check as check

class RolesManager:
    """ Roles Manager Class """
    def __init__(
            self, 
            bot: commands.Bot, 
            rolesFilename='data/roles.json'
        ) -> None:
        """ Roles Manager Constructor """
        self.bot = bot
        self.filename = rolesFilename

    #--------------------------------------------------------------------------
    #   METHODS
    def append(self, role_id: int, channel_id: int) -> None:
        """ Add a new channel associated to the role for notification. 
        """
        data = self.data
        if role_id not in data.keys():         data[role_id] = [channel_id]
        elif channel_id not in data[role_id]:  data[role_id].append(channel_id)

        with open(self.filename, 'w') as file:
            json.dump(data, file, indent=4)
        
    def remove(self, role_id: int, channel_id: int) -> None:
        """ Remove a channel for a given role. """
        data = self.data

        if role_id in data.keys():
            if channel_id in data[role_id]:
                
                # Clear role : no channels anymore
                if len(data[role_id] == 1):
                    self.clear_role(role_id, self.filename)
                
                # Remove channel
                else:
                    data[role_id].remove(channel_id)
            
                with open(self.filename, 'w') as file:
                    json.dump(data, file, indent=4)

    def clear_role(self, role_id: int) -> None:
        """ Remove a role from notification in every channel """
        data = self.data

        if role_id in data.keys():
            data.pop(role_id)
        
        with open(self.filename, 'w') as file:
            json.dump(data, file, indent=4)
    
    def clear_channel(self, channel_id: int) -> None:
        """ Clear all roles for a given channel """
        data = self.data

        new_data = {
            role_id: [
                ch_id
                for ch_id in channel_ids_list
                if ch_id != channel_id
            ]
            for role_id, channel_ids_list in data.items()
            if channel_ids_list != [channel_id]
        }

        with open(self.filename, 'w') as file:
            json.dump(new_data, file, indent=4)

    def embed(self, interaction: discord.Interaction):
        """ Get embed associated with roles """
        embedDict = dict(
            title=f"Rôle·s suivi·s sur {interaction.channel.mention} 🕵️",
            footer={
                "text": (f"Utilisez le menu déroulant pour sélectionner"
                         f" les rôles à suivre.")
            }
        )
        
        # Retrieve role names
        role_names = []
        guild = self.bot.get_guild(GUILD)
        for role_id, channel_id_list in self.data.items():
            if interaction.channel_id in channel_id_list:
                role = guild.get_role(role_id)
                if role:
                    role_names.append(role.name)
        
        # Embed description
        if role_names:
            embedDict["description"] = "\n".join([
                "▫️ " + name
                for name in role_names
            ])
        
        # Embed description if nothing retrieved
        else:
            embedDict["description"] = "Aucun rôle n'est observé."

        return discord.Embed.from_dict(embedDict)
    
    #--------------------------------------------------------------------------
    #   PROPERTIES
    @property
    def roles(self):
        """ Get roles with notification activated """
        return self.data.keys()
    
    @property
    def data(self) -> Dict[int, List[int]]:
        """ Read external file to get data """
        with open(self.filename, 'r') as file:
            data: Dict[int, List[int]] = json.load(file)

        return {int(key): value for key, value in data.items()}

class RolesView(discord.ui.View):
    """ Roles View Class """
    def __init__(
            self,
            interaction: discord.Interaction,
            manager: RolesManager,
        ) -> None:
        """ Roles View Constructor """
        super().__init__(timeout=100)
        self.interaction = interaction
        self.manager     = manager

        self.response: discord.InteractionMessage = None

    #--------------------------------------------------------------------------
    #   ASYNC METHODS
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
                f"Seul l'auteur de la commande peut interagir ! "
                ),
                color=16711680
            )
            await interaction.response.send_message(
                embed=emb, 
                ephemeral=True)
            return False

    async def on_timeout(self) -> None:
        self.clear_items()
        embed = self.response.embeds[0]
        embed.set_footer(text="Éditez les rôles suivis avec `/cog`")
        await self.response.edit(view=self, embed=embed)
        self.stop()

    async def start(self):
        """ Start View """
        await self.interaction.response.send_message(
            embed=self.manager.embed(self.interaction),
            view=self
        )

        self.response = await self.interaction.original_response()

    #--------------------------------------------------------------------------
    #   DROPDOWN
    @discord.ui.select(
            cls=discord.ui.RoleSelect, 
            min_values=0, max_values=25,
            placeholder="Sélectionner le·s rôle·s à suivre")
    async def select_role(
        self, 
        interaction: discord.Interaction, 
        select:discord.ui.RoleSelect):
        """ Selecting roles Coroutine """
        # Remove all roles within this channel
        self.manager.clear_channel(interaction.channel_id)

        # Add each selected role
        for value in select.values:
            self.manager.append(value.id, interaction.channel_id)
        
        # Edit response
        await interaction.response.edit_message(
            embed=self.manager.embed(interaction),
            view=self
        )
        
        self.response = await interaction.original_response()

class RolesCog(commands.Cog):
    """ RolesCog Class """
    def __init__(self, bot: commands.Bot):
        """ RolesCog Constructor """
        print(f"Cog [{self.__cog_name__}] activé.")
        self.bot     = bot
        self.manager = RolesManager(self.bot)
        
    #--------------------------------------------------------------------------
    #   SLASH COMMANDS
    @app_commands.command(name="role")
    @app_commands.guilds(GUILD)
    @check.is_staff()
    async def _roleCommand(
        self, 
        interaction: discord.Interaction
        ):
        """ Gérer les rôles suivis dans ce canal """
        view = RolesView(interaction, self.manager)
        await view.start()

    #--------------------------------------------------------------------------
    #   EVENT LISTENERS
    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):
        """ Listen change in roles """
        rolesRemoved = [el for el in before.roles if el not in after.roles]
        rolesAdded   = [el for el in after.roles if el not in before.roles]

        # No role has been updated
        if len(rolesRemoved) == 0 and len(rolesAdded) == 0:
            return
        
        # Check if role is tracked
        role = rolesRemoved[0] if len(rolesRemoved) > 0 else rolesAdded[0]
        if role.id not in self.manager.roles:
            return
        
        # Notification
        isRemoved = True if len(rolesRemoved) > 0 else False

        for channel_id in self.manager.data[role.id]:
            channel = after.guild.get_channel_or_thread(channel_id)

            # Send message
            try:
                await channel.send(
                    content=(
                    f":{'red' if isRemoved else 'green'}_circle: "
                    f"{after.mention} a "
                    f"{'perdu' if isRemoved else 'obtenu'} "
                    f"le rôle **{role.name}**"
                    )
                )
            
            # The channel or thread can't be found
            except AttributeError:
                print(f"Channel or thread with ID {channel.id} not found")
                self.manager.remove(role.id, channel_id)

async def setup(bot: commands.Bot):
    await bot.add_cog(RolesCog(bot))