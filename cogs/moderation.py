""" Cette extension ajoute des outils spécifiques à la modération :
    ▫️ ban temporaire
    ▫️ gestion des logs avec la commande **/logs**
    ▫️ suppression et log de messages par emoji en réaction
"""
from __future__ import annotations
from typing import List
import pandas as pd
import datetime

import discord
from discord.ext import commands
from discord import app_commands
from src.utils import Paginator
from config.config import ConfigBot, GUILD
import src.check as check

###############################################################################
#   LOGS CLASS

class Logs:
    """ Logs Class """
    def __init__(
            self,
            type: str,
            target_id: int,
            author_id: int,
            time: str,
            reason: str | None = None,
            content: str | None = None,
            content_id: int | None = None,
            channel_id: int | None = None
        ) -> None:
        """ Logs Constructor """
        self.type       = type
        self.target_id  = target_id
        self.author_id  = author_id
        self.time       = time
        self.reason     = reason
        self.content    = content
        self.content_id = content_id
        self.channel_id = channel_id
    
    #--------------------------------------------------------------------------
    #   PROPERTIES
    @property
    def to_dict(self):
        """ Convert from Logs to dict type """
        return {
            "type":         self.type,
            "target_id":    self.target_id,
            "author_id":    self.author_id,
            "time":         self.time,
            "reason":       self.reason if self.reason else "",
            "content":      self.content if self.content else "",
            "content_id":   self.content_id if self.content_id else "",
            "channel_id":   self.channel_id if self.channel_id else ""
        }

    #--------------------------------------------------------------------------
    #   METHODS
    def to_embed(self, bot: commands.Bot) -> discord.Embed:
        """ Convert Log to a discord.Embed"""
        target  = bot.get_user(self.target_id)
        author  = bot.get_user(self.author_id)
        channel = bot.get_channel(self.channel_id) if self.channel_id else None
        fields = []

        if target:
            fields.append({
                "name":     "Utilisateur",
                "value":    target.mention \
                            if hasattr(target, "mention") \
                            else str(target),
                "inline":   True
            })

        if author:          
            fields.append({
                "name":     "Modérateur",
                "value":    author.mention \
                            if hasattr(author, "mention") \
                            else str(author),
                "inline":   True
            })
        if self.channel_id:         
            fields.append({
                "name":     "Canal",
                "value":    channel.mention \
                            if channel is not None \
                            else "#deleted",
                "inline":   True
            })
        if self.content:    
            fields.append({
                "name":     "Message",
                "value":    self.content
            })
        if self.reason:     
            fields.append({
                "name":     "Raison",
                "value":    self.reason
            })

        embedDict = {
            "type": "rich",
            "author": {
                "name": f"{self.type} | {str(target)}",
                "icon_url": target.display_avatar.url if target else None
            },
            "footer": {
                "text": f"ID : {self.target_id}"
            },
            "fields": fields,
            "timestamp": self.time
        }

        # Colors
        if "Ban" in self.type:              embedDict["color"] = 0xcc3e2e
        elif "Kick" in self.type:           embedDict["color"] = 0xe6cd5e
        elif "👀" in self.type:             embedDict["color"] = 0x4b8262
        elif "❌" in self.type:             embedDict["color"] = 0x4b8262
        elif "QUARANTAINE" in self.type:    embedDict["color"] = 0xd17038
        
        return discord.Embed.from_dict(embedDict)

    #--------------------------------------------------------------------------
    #   STATIC METHODS
    @staticmethod
    def from_serie(serie: pd.Series) -> Logs:
        data = serie.to_dict()
        return Logs(
            data['type'], 
            data['target_id'], 
            data['author_id'], 
            data['time'],
            **{
                key: value 
                for key, value in data.items()
                if key not in ['type', 'target_id', 'author_id', 'time']
            })
    
class LogsManager:
    """ LogsManager Class """
    def __init__(
            self, 
            bot: commands.Bot, 
            logsFilename='data/moderation.json'
        ) -> None:
        """ LogsManager Constructor """
        self.bot       = bot
        self.filename  = logsFilename
        self.embed     = None
        self.options   = {}
        self.log: Logs = None
    
    #--------------------------------------------------------------------------
    #   PROPERTIES
    @property
    def data(self) -> pd.DataFrame:
        """ Read external file to get data as pandas.DataFrame object """
        return pd.read_json(
            self.filename, 
            orient="records", 
            dtype=False, 
            encoding="utf-8")
    
    #--------------------------------------------------------------------------
    #   METHODS
    def append(self, log: Logs) -> None:
        """ Add a new log to the LogsManager file """
        data = pd.concat(
            [self.data, pd.DataFrame([log.to_dict])],
            ignore_index=True
            ).drop_duplicates()
        
        data.to_json(
            self.filename, 
            indent=4, 
            orient="records", 
            force_ascii=False)

    def remove(self, log: Logs) -> None:
        """ Remove a log from the LogsManager file """
        data = self.data
        idx_to_remove = data[data.eq(log.to_dict).all(axis=1)].index

        data = data.drop(idx_to_remove)
        data.to_json(
            self.filename, 
            indent=4, 
            orient="records", 
            force_ascii=False)

    def filter(self, **options) -> pd.DataFrame:
        """ Filter the data with the options provided """
        filtered = self.data

        for column_name, value in {**self.options, **options}.items():
            filtered = filtered[filtered[column_name] == value]
        
        return filtered
    
    #--------------------------------------------------------------------------
    #   PAGINATOR NAVIGATION
    async def navigate(self, page: int):
        """ Coroutine for Paginator (called by navigation buttons) """
        dataLogs = self.filter()
        n        = Paginator.compute_total_pages(len(dataLogs), 1)

        # No log found
        if n == 0:
            self.embed = discord.Embed(description="Plus aucun log !")
            self.log   = None
        
        else:
            self.log = Logs.from_serie(dataLogs.iloc[page - 1])
            self.embed = self.log.to_embed(self.bot)
            self.embed.set_footer(text=f"Log {page} / {n}")

        return self.embed, n

    #--------------------------------------------------------------------------
    #   TO DELETE => convert old .dat file into .json file
    @staticmethod
    def read_old(filename: str):
        """ Convert old file to .json """
        # Convert floats to integers
        def convert_to_int(value):
            try:
                return int(float(value))
            except (ValueError, TypeError):
                return value
        
        # Read csv => pd.DataFrame
        data = pd.read_csv(
            filename,
            index_col=False,
            converters={
                column: convert_to_int 
                for column in ['user', 'moderateur', 'id', 'channel_id']
                })
        
        # Merge two columns
        data['content'] = data['message'].fillna(data['contenu'])
        data.drop(columns=['message', 'contenu'], inplace=True)

        # Rename columns
        data.rename(
            columns={
                "user": "target_id", 
                "moderateur": "author_id", 
                "raison": "reason",
                "message": "content",
                "id": "content_id"
                }, 
            inplace=True
            )
        
        data.fillna('', inplace=True)

        # pd.DataFrame => .json
        data.to_json(
            "data/old_moderation.json",
            indent=4,
            orient="records",
            force_ascii=False)

class LogsView(discord.ui.View):
    """ Logs View """
    def __init__(
            self,
            interaction: discord.Interaction,
            manager: LogsManager
        ) -> None:
        """ Logs View Constructor """
        self.interaction    = interaction
        self.manager        = manager
        super().__init__(timeout=100)
    
    #--------------------------------------------------------------------------
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

    async def start_paginator(
            self, 
            interaction: discord.Interaction,
            member: discord.Member):
        """ Handle Paginator View """
        embed, total_pages = await self.manager.navigate(1) 
        
        # No log found
        if total_pages == 0:
            embed.description = f"Aucun log trouvé pour : {member.mention}"
            await interaction.response.edit_message(
                embed=embed,
                view=self
            )
        
        # Logs found => starting Paginator View
        else:
            await LogsPaginator(interaction, self.manager, self).start()

    #--------------------------------------------------------------------------
    @discord.ui.select(
        cls=discord.ui.UserSelect,
        min_values=1, max_values=1,
        placeholder="Recherche des logs...",
        row=0)
    async def select_user(
        self,
        interaction: discord.Interaction,
        select: discord.ui.UserSelect):
        """ Selecting User Coroutine """
        if select.values:
            self.manager.options["target_id"] = select.values[0].id
        
        await self.start_paginator(interaction, select.values[0])

class LogsPaginator(Paginator):
    """ Logs Paginator """
    def __init__(
            self, 
            interaction: discord.Interaction, 
            manager: LogsManager,
            selectView: LogsView
        ) -> None:
        """ Logs Paginator Constructor """
        self.manager    = manager
        self.selectView = selectView
        super().__init__(interaction, manager.navigate)

    #--------------------------------------------------------------------------
    async def start(self):
        """ Start View """
        buttons = self.children
        self.clear_items()

        idx = len(buttons) // 2
        buttons[idx:idx] = [buttons.pop()]

        for button in buttons:
            self.add_item(button)
        
        # Recompute embed & total pages (duplicate)
        emb, self.total_pages = await self.get_page(self.index)

        # Fast Buttons Removed
        if not self.withFastButtons:
            fastprevious = self.children[0]
            fastnext     = self.children[-1]
            self.remove_item(fastprevious)
            self.remove_item(fastnext)
            pass
        
        self.add_item(self.selectView.children[0])
        self.update_buttons()

        await self.interaction.response.edit_message(
            embed=emb,
            view=self)

    async def edit_page(self, interaction: discord.Interaction):
        """ Navigate through pages when on_click event """
        emb, self.total_pages = await self.get_page(self.index)

        # No more log : back to selectView
        if self.total_pages == 0:
            await interaction.response.edit_message(
                embed=emb, 
                view=self.selectView)

        # Still logs : Paginator continues
        else:
            self.update_buttons()
            await interaction.response.edit_message(embed=emb, view=self)

    def update_buttons(self):
        """ Update buttons """
        # Disable buttons whenever useful
        self.children[0].disabled  = self.index == 1
        self.children[-2].disabled = self.index == self.total_pages

        if self.withFastButtons:
            self.children[1].disabled  = self.index == 1
            self.children[-3].disabled = self.index == self.total_pages

    #--------------------------------------------------------------------------
    @discord.ui.button(
        label="Supprimer log", 
        style=discord.ButtonStyle.red,
        row=4)
    async def deleteLog(
        self,
        interaction: discord.Interaction,
        button: discord.Button):
        """ Delete Log """
        self.manager.remove(self.manager.log)
        self.manager.log = None

        if self.index == self.total_pages:
            self.index -= 1
        
        await self.edit_page(interaction)

###############################################################################
#   MODERATION COG

class ModerationCog(commands.Cog):
    """ ModerationCog Class """
    def __init__(self, bot: commands.Bot):
        """ ModerationCog Constructor """
        print(f"Cog [{self.__cog_name__}] activé.")
        self.bot     = bot
        self.manager = LogsManager(self.bot)
        self.config  = ConfigBot()
    
    #--------------------------------------------------------------------------
    #   SLASH COMMANDS
    @app_commands.command(name="logs")
    @app_commands.guilds(GUILD)
    @check.can_kick()
    async def _logsCommand(
        self,
        interaction: discord.Interaction
        ):
        """ Gérer les logs """
        view = LogsView(interaction, self.manager)
        await interaction.response.send_message(
            view=view,
            ephemeral=False
        )

    #--------------------------------------------------------------------------
    #   EVENT LISTENERS
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """ Check if a new Member triggers a flag from logs """
        logs = LogsManager(self.bot).filter(target_id=member.id)
        if len(logs) > 0:
            channel = member.guild.get_channel(
                self.config.channel.moderation
                )
            await channel.send(embed=discord.Embed(description=(
                f":star: {str(member)} a rejoint le serveur "
                f"avec {len(logs)} logs."
                )))

    @commands.Cog.listener()
    async def on_voice_state_update(
        self, 
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
        ):
        """ Notification for mute & unmute """
        if after.mute and not before.mute:
            embed = discord.Embed(
                description=(
                    f":mute: {member.mention} a été mute dans "
                    f"{after.channel.mention}"
                    ), 
                color=0xfe0000
                )
        elif before.mute and not after.mute:
            embed = discord.Embed(
                description=f":loud_sound: {member.mention} n'est plus mute !",
                color=0x6eaa5e
            )
        else:
            return
        
        channel = member.guild.get_channel(self.config.channel.moderation)
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """ Check if a Member has been kicked, banned or timed out """
        # Kick
        if entry.action == discord.AuditLogAction.kick:
            log = Logs(
                f"Kick", 
                entry.target.id, entry.user_id, 
                entry.created_at.isoformat(), 
                reason=entry.reason
            )
            self.manager.append(log)
            channel = entry.guild.get_channel(self.config.channel.logs)
            await channel.send(embed=log.to_embed(self.bot))
        
        # Ban
        if entry.action == discord.AuditLogAction.ban:
            log = Logs(
                f"Ban",
                entry.target.id, entry.user_id, 
                entry.created_at.isoformat(),
                reason=entry.reason
            )
            self.manager.append(log)
            channel = entry.guild.get_channel(self.config.channel.logs)
            await channel.send(embed=log.to_embed(self.bot))

        # Timeout
        if entry.action == discord.AuditLogAction.member_update:
            # Beginning of timeout
            if hasattr(entry.after, 'timed_out_until') \
            and entry.target.is_timed_out():
                # Length of timeout
                timedelta: datetime.timedelta 
                timedelta = entry.target.timed_out_until - entry.created_at
                days, hours, mins = (
                    timedelta.days,
                    (timedelta.seconds // 3600),
                    (timedelta.seconds // 60)
                    )
                if days > 1:        length = "7j"
                elif hours > 1:     length = "1j"
                elif mins > 10:     length = "1h"
                elif mins > 5:      length = "10mn"
                elif mins > 1:      length = "5mn"
                else:               length = "1mn"

                log = Logs(
                    f"TIMEOUT - {length}",
                    entry.target.id, entry.user_id, 
                    entry.created_at.isoformat(),
                    reason=entry.reason
                )
                self.manager.append(log)
                channel = entry.guild.get_channel(self.config.channel.logs)
                await channel.send(embed=log.to_embed(self.bot))
            
            # Timeout interrupted
            elif hasattr(entry.after, 'timed_out_until') \
            and not entry.target.is_timed_out():
                channel = entry.guild.get_channel(self.config.channel.logs)
                await channel.send(embed=discord.Embed(
                    description=(
                    f"⏰ Interruption du time-out de {entry.target.name} !"
                )))
        
        # Quarantine
        if entry.action == discord.AuditLogAction.member_role_update:
            roles: List[discord.Role] = entry.after.roles

            if roles and roles[0].id in self.config.role.quarantine:
                log = Logs(
                    f"MISE EN QUARANTAINE",
                    entry.target.id, entry.user_id, 
                    entry.created_at.isoformat()
                )
                self.manager.append(log)
                channel = entry.guild.get_channel(self.config.channel.logs)
                await channel.send(embed=log.to_embed(self.bot))

    @commands.Cog.listener()
    async def on_raw_reaction_add(
        self, 
        payload: discord.RawReactionActionEvent
        ):
        """ Log or delete messages with emoji reactions """
        # Check if Member can manage messages
        if not payload.member.guild_permissions.manage_messages:
            return
        
        # LOG 👀
        if str(payload.emoji) == "\U0001f440":
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            # Avoid to log admins
            if isinstance(message.author, discord.Member) \
            and message.author.guild_permissions.kick_members:
                return
            
            await message.remove_reaction(payload.emoji, payload.member)
            log = Logs(
                f"LOG {payload.emoji}",
                message.author.id, payload.member.id, 
                message.created_at.isoformat(),
                content=message.content, 
                content_id=message.id, 
                channel_id=channel.id
            )
            self.manager.append(log)
            channel_logs = message.guild.get_channel(self.config.channel.logs)
            await channel_logs.send(embed=log.to_embed(self.bot))

        # LOG ❌
        if str(payload.emoji) == '\U0000274c':
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)

            # Avoid to log admins
            if isinstance(message.author, discord.Member) \
            and message.author.guild_permissions.kick_members:
                return
            
            await message.delete()
            log = Logs(
                f"LOG {payload.emoji}",
                message.author.id, payload.member.id, 
                message.created_at.isoformat(),
                content=message.content, 
                content_id=message.id, 
                channel_id=channel.id
            )
            self.manager.append(log)
            channel_logs = message.guild.get_channel(self.config.channel.logs)
            await channel_logs.send(embed=log.to_embed(self.bot))

async def setup(bot: commands.Bot):
    await bot.add_cog(ModerationCog(bot))