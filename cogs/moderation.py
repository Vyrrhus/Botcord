import discord
from discord import app_commands
from discord.ext import commands
from check import check_category
from utils import Console
from config.id import *
import traceback
import asyncio
import numpy as np
import pandas as pd
import typing
from datetime import datetime, timedelta

# commande ?sram pour avoir un classement des meilleurs modérateurs

# UI & VIEW
class LogButton(discord.ui.Button):
    def __init__(self,id):
        if id < 0:
            super().__init__(row=0)
        else:
            super().__init__(row=1)
        self.id = id + 1
        self.emojis = ["\U000023ee", "\U000025c0", "", "\U000025b6", "\U000023ed"]

        if self.id == 0:
            self.style = discord.ButtonStyle.success
            self.label = "Voir logs"
        elif self.id == 3:
            self.style = discord.ButtonStyle.primary
            self.label = "Logs"
            self.disabled = True
        elif self.id == -1:
            self.style = discord.ButtonStyle.danger
            self.label = "Supprimer"
        else:
            self.style = discord.ButtonStyle.secondary
            self.label = self.emojis[id]
            
    
    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: LogView = self.view

        # Bouton initial
        if self.id == 0:
            view.start()

        # Navigation dans les logs
        if self.id == 1:
            view.num = 1
        if self.id == 2:
            view.num -= 1
        if self.id == 4:
            view.num += 1
        if self.id == 5:
            view.num = view.logs.shape[0]
        
        # Clear (seulement pour le propriétaire)
        if self.id == -1 and interaction.user == view.ctx.author:
            view.clear_log()

        # Update
        if view.nb > 0:
            view.update()
            em = discord.Embed.from_dict(view.emDict)
            await interaction.response.edit_message(content=None, embed=em, view=view)
        
        # Plus aucun log
        else:
            await interaction.response.edit_message(content=f':x: Plus aucun log pour {str(view.target)}', embed=None, view=None)
            view.stop()
        
class LogView(discord.ui.View):
    def __init__(self, bot, context, target, user_logs, timeout=180.0):
        super().__init__()
        self.bot    = bot
        self.ctx    = context
        self.target = target
        self.logs   = user_logs
        self.nb     = user_logs.shape[0]
        self.num    = 1
        self.timeout = timeout
        
        self.emDict =   {"type": "rich",
                         "author": {"name": f"{str(self.target)}",
                                    "icon_url": self.target.avatar.url},
                         "color": 0x1db868,
                         "footer": {"text": f"ID : {self.target.id}"}}
        
        # Ajouter un bouton pour clear et un select pour choisir entre les types de logs
        self.add_item(LogButton(-1))

    def clear_log(self):
        # Suppression du log
        index = self.logs.iloc[[self.num - 1]].index
        self.logs = self.logs.drop(index[0])
        self.nb = self.logs.shape[0]

        if self.num > self.nb:
            self.num = self.nb

        # Mise à jour Data
        Data.remove_index(index[0])

        # Plus aucun log
        if self.nb == 0:
            self.clear_items()
        return
    
    def get_log(self):
        log = self.logs.iloc[[self.num - 1]].replace({np.nan:None}).to_dict(orient='list')
        log = {key: log[key][0] for key in log}

        self.emDict["timestamp"] = log["time"]
        self.emDict["title"] = log["type"]
        self.emDict["fields"] = []

        moderateur = self.bot.get_user(log['moderateur'])
        if isinstance(moderateur, discord.User):
            self.emDict["fields"].append({"name": "Modérateur", "value": f"{moderateur.mention}", "inline": True})
        
        if log['channel_id'] and log['contenu']:
            self.emDict["fields"].append({"name": "Salon", "value": f"<#{log['channel_id']}>", "inline": True})
            self.emDict["fields"].append({"name": "Message", "value": log['contenu']})
        
        if log['raison']:
            self.emDict["fields"].append({"name": "Raison", "value": log['raison']})
        
        if log['message']:
            self.emDict["fields"].append({"name": "Message en DM", "value": log['message']})

    def update(self):
        # Update buttons
        for child in self.children:
            if child.id == 1 or child.id == 2:
                if self.num == 1:
                    child.disabled=True
                else:
                    child.disabled=False
            
            if child.id == 4 or child.id == 5:
                if self.num == self.nb:
                    child.disabled=True
                else:
                    child.disabled=False

            if child.id == 3:
                child.label = f'Log {self.num} / {self.nb}'

        # Update embed
        self.get_log()

    def start(self):
        self.clear_items()
        for i in range(5):
            self.add_item(LogButton(i))
        self.add_item(LogButton(-2))
    
    async def on_timeout(self) -> None:
        self.clear_items()
        await self.message.edit(content=f"{self.logs.shape[0]} logs trouvés pour {str(self.target)}", embed=None, view=None)
        self.stop()
        return await super().on_timeout()

class BanModal(discord.ui.Modal, title=''):
    path = "data/bantemp.dat"
    reason  = discord.ui.TextInput(
            label='Raison',
            style=discord.TextStyle.long,
            placeholder='Ban parce que...')
    message = discord.ui.TextInput(
            label='Message envoyé en DM (optionnel)',
            style=discord.TextStyle.long,
            required=False)
    
    @staticmethod
    def clear(user_id):
        df = pd.read_csv(BanModal.path)
        index = df.set_index('user').index.get_loc(user_id)
        df = df.drop(index)
        df.to_csv(BanModal.path, index=False)

    @staticmethod
    async def unban_task(time, target_id, guild, target=None, bot=None):
        if time > datetime.today():
            print(f'sleeping til {time.isoformat()}')
            await discord.utils.sleep_until(time)
        BanModal.clear(target_id)
        if not target and bot:
            target = await bot.fetch_user(target_id)
        if target:
            await guild.unban(target, reason=f"Fin du ban temporaire")
            await guild.get_channel(ChannelId.channel_moderation).send(embed=discord.Embed(color=0x6eaa5e, description=f"{str(target)} a été unban."))

    def store_data(self):
        # Datetime for unban
        delay = int(self.duree[0])   # Months
        unban = datetime.today() + timedelta(seconds=delay*30)

        df = pd.read_csv(self.path)
        df.loc[len(df)] = [self.target.id, unban.isoformat()]
        df.to_csv(self.path, index=False)

        return unban

    async def on_submit(self, interaction: discord.Interaction):
        # Send DM
        dm_channel = await self.target.create_dm()
        em = discord.Embed(
                    title=f"Tu as été banni de : {interaction.guild.name} pour une durée de {self.duree}.",
                    description=self.message.value,
                    color=0xfe0000)
        await dm_channel.send(embed=em)
        
        # Ban
        await self.target.ban(delete_message_days=0, reason=self.reason.value)
        
        # Log
        unban_datetime = self.store_data()
        log = Data(f"Ban temporaire {self.duree}", self.target, interaction.user, interaction.created_at, reason=self.reason.value, dm=self.message.value)
        em  = log.embed(isSanction=True)
        await interaction.guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
        log.to_dataframe()

        # Response
        await interaction.response.send_message(embed=discord.Embed(color=0x6eaa5e, description=f":hammer: {str(self.target)} a été banni du serveur pour une durée de {self.duree}"))

        # Task for unban
        await BanModal.unban_task(unban_datetime, self.target.id, interaction.guild, target=self.target)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await self.console.print_error(interaction, error)

# STRUCTURES
class Data:
    path = 'data/moderation.dat'

    def __init__(self, title, target, author, time, reason='', dm='', message=''):
        self.path    = Data.path
        self.type    = title.upper()
        self.target  = target
        self.author  = author
        self.time    = time
        self.reason  = reason
        self.dm      = dm
        self.message = message
    
    @staticmethod
    def get_logs(user):
        df = pd.read_csv(Data.path)
        df = df[df['user'] == user.id]
        return df

    @staticmethod
    def get_moderateur(user):
        df = pd.read_csv(Data.path)
        df = df[df['moderateur'] == user.id]
        return df

    @staticmethod
    def remove_index(index):
        df = pd.read_csv(Data.path)
        df = df.drop(index)
        df.to_csv(Data.path, index=False)

    def embed(self, isLog=False, isSanction=False):
        emDict = {"type": "rich",
                  "author": {"name": f"{self.type} | {str(self.target)}", 
                             "icon_url": self.target.avatar.url},
                  "timestamp": self.time.isoformat(),
                  "fields": [{"name": "Utilisateur",
                              "value": self.target.mention,
                              "inline": True},
                              {"name": "Modérateur",
                              "value": self.author.mention,
                              "inline": True}],
                   "footer": {"text": f"ID : {self.target.id}"}}
        
        # Modération d'un message
        if isLog and self.message:
            emDict["color"] = 0x0153f7
            emDict["fields"].append({"name": "Salon", "value": f"<#{self.message.channel.id}>", "inline": True})
            emDict["fields"].append({"name": "Message", "value": self.message.content})
        
        if isSanction:
            emDict["color"] = 0xfe0000
            if self.reason:
                emDict["fields"].append({"name": "Raison", "value": self.reason})
            if self.dm:
                emDict["fields"].append({"name": "Message en DM", "value": self.dm})
            if self.target.timed_out_until and self.type == "TIMEOUT":
                timedelta = self.target.timed_out_until - self.time
                days  = timedelta.days
                hours = (timedelta.seconds // 3600) % 24
                mins  = (timedelta.seconds // 60) % 60
                secs  = timedelta.seconds % 60
                if days > 1:
                    delay = "7j"
                elif hours > 1:
                    delay = "1j"
                elif mins > 10:
                    delay = "1h"
                elif mins > 5:
                    delay = "10mn"
                elif mins > 1:
                    delay = "5mn"
                else:
                    delay = "1mn"
                
                self.type += f' - {delay}'
                emDict["author"]["name"] = f"{self.type} | {str(self.target)}"

        em = discord.Embed.from_dict(emDict)

        return em

    def already_log(self):
        df = pd.read_csv(self.path)
        if self.message:
            df = df[df['id'] == self.message.id]
            if df.shape[0] > 0:
                return True
        return False

    def to_dataframe(self):
        df = pd.read_csv(self.path)
        if self.message:
            id         = self.message.id
            channel_id = self.message.channel.id
            content    = self.message.content
        else:
            id, channel_id, content = None, None, ''
        
        df.loc[len(df)] = [self.type, self.target.id, self.author.id, self.time.isoformat(), self.reason.replace('\n', '\\n'), self.dm.replace('\n', '\\n'), id, channel_id, content.replace('\n', '\\n')]
        df.to_csv(self.path, index=False)

# COG CLASS
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.get_event_loop().create_task(self.init_unban_task())

    async def init_unban_task(self):
        df = pd.read_csv(BanModal.path)
        await self.bot.wait_until_ready()
        self.console = Console(self.bot, ConsoleId.moderation)
        guild = self.bot.get_guild(GuildId.default)
        for ii in range(df.shape[0]):
            df_ban = df.iloc[ii]
            time   = datetime.fromisoformat(df_ban['time'])
            await BanModal.unban_task(time, df_ban['user'], guild, bot=self.bot)

    ###########################
    # COG COMMANDS
    async def cog_before_invoke(self, ctx) -> None:
        await self.console.print_command(ctx)
        return await super().cog_before_invoke(ctx)
    
    async def cog_command_error(self, ctx, error: Exception) -> None:

        await self.console.print_error(ctx, error)
        return await super().cog_command_error(ctx, error)
    
    async def bot_check_once(self, ctx) -> bool:
        self.console = Console(self.bot, ConsoleId.moderation)
        return super().bot_check_once(ctx)

    ###########################
    # SLASH COMMANDS

    # Check
    def check_ban_command():
        def predicate(interaction: discord.Interaction) -> bool:
            if interaction.channel.category.id == ChannelId.category_moderation:
                return interaction.user.guild_permissions.ban_members and interaction.guild.me.guild_permissions.ban_members
            else:
                return False
        return app_commands.check(predicate)

    # BAN TEMP
    @app_commands.command(name='bantemp', description="Ban temporairement un membre du serveur")
    @app_commands.guilds(discord.Object(GuildId.default))
    @app_commands.describe(cible="La personne à ban", duree="Durée du ban temporaire")
    @check_ban_command()
    async def _bantemp(self, interaction: discord.Interaction, cible: discord.Member, duree: typing.Literal['1 mois', '3 mois', '6 mois', '12 mois']):
        try:
            if interaction.user.roles[-1] <= cible.roles[-1]:
                await interaction.response.send_message(embed=discord.Embed(description=f"Impossible de bannir quelqu'un ayant un rôle supérieur ou égal au sien.", color=0xfe0000))
                return
            
            # Modal
            modal = BanModal()
            modal.title   = f"Ban {str(cible)} ({duree})"
            modal.bot     = self.bot
            modal.console = self.console
            modal.target  = cible
            modal.duree   = duree
        
            await interaction.response.send_modal(modal)
        except:
            self.console.print_error(interaction, traceback.print_exc())

    ###########################
    # COMMANDS

    # LIBRE
    @commands.command(name='libre')
    @commands.has_guild_permissions(kick_members=True)
    @check_category(ChannelId.category_moderation)
    async def _libre(self, ctx):
        await ctx.message.delete()
        await ctx.send('```LIBRE```')

    # WARN
    @commands.hybrid_command(name='warn', brief='Envoie un avertissement en privé à la personne ciblée')
    @app_commands.guilds(discord.Object(GuildId.default))
    @app_commands.describe(cible="La personne à avertir", message="contenu de l'avertissement envoyé en DM")
    @commands.has_guild_permissions(kick_members=True)
    @check_category(ChannelId.category_moderation)
    async def _warn(self, ctx: commands.Context, cible: discord.Member, *, message: str):
        if ctx.author.roles[-1] <= cible.roles[-1]:
            await ctx.send(content=None, embed=discord.Embed(description=f"Impossible d'envoyer un avertissement à quelqu'un ayant un rôle supérieur ou égal au sien.", color=0xfe0000))
            return

        # Send warn
        dm_channel = await cible.create_dm()
        em = discord.Embed(description=f"Tu as reçu un avertissement de **{ctx.guild.name}** : \n{message}", color=0xfe0000)
        await dm_channel.send(content=None, embed=em)

        # Log warn
        log = Data(f"Warn", cible, ctx.author, ctx.message.created_at, dm=message)
        em  = log.embed(isSanction=True)
        await ctx.guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
        log.to_dataframe()

        # Answer
        await ctx.send(content=None, embed=discord.Embed(color=0x6eaa5e, description=f"{str(cible)} a reçu un avertissement."))

    # LOG VIEW : SEE AND CLEAR LOGS
    @commands.command(name='log')
    @commands.has_guild_permissions(kick_members=True)
    @check_category(ChannelId.category_moderation)
    async def _log(self, ctx, target:discord.User):
        try:

            user_logs = Data.get_logs(target)
            if user_logs.shape[0] == 0:
                await ctx.channel.send(f':x: Aucun log trouvé pour {str(target)}')
                return

            user_logs['id'] = user_logs['id'].astype('Int64')
            user_logs['channel_id'] = user_logs['channel_id'].astype('Int64')
            view = LogView(self.bot, ctx, target, user_logs, timeout=120.0)
            view.message = await ctx.send(f"{user_logs.shape[0]} logs trouvés pour {str(target)}", embed=None, view=view)
        
        except:
            traceback.print_exc()

    # SRAM : classement
    @commands.command(name='sram', hidden=True)
    @commands.has_guild_permissions(kick_members=True)
    @check_category(ChannelId.category_moderation)
    async def _classement(self, ctx):
        return

    ###########################
    # EVENTS

    # MEMBER JOIN
    @commands.Cog.listener()
    async def on_member_join(self, member):
        # NOT VERIFIED YET
        user_logs = Data.get_logs(member)
        if user_logs.shape[0] > 0:
            channel = member.guild.get_channel(ChannelId.channel_moderation)
            await channel.send(embed=discord.Embed(description=f':star: {str(member)} a rejoint le serveur avec {user_logs.shape[0]} logs'))

    # EMOJI REACTIONS
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        try:

            guild = self.bot.get_guild(payload.guild_id)

            if payload.member.guild_permissions.manage_messages and guild.me.guild_permissions.manage_messages:

                # LOG
                if str(payload.emoji) == '\U0001f440':
                    channel = guild.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    if not isinstance(message.author, discord.User):
                        if message.author.guild_permissions.kick_members:
                            return
                    await message.remove_reaction(payload.emoji, payload.member)

                    log = Data(f"LOG {payload.emoji}", message.author, payload.member, message.created_at, message=message)
                    if log.already_log():
                        return
                    em  = log.embed(isLog=True)
                    try:
                        await guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
                    except:
                        traceback.print_exc()
                    log.to_dataframe()

                # DELETE
                elif str(payload.emoji) == '\U0000274c':
                    channel = guild.get_channel(payload.channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    if not isinstance(message.author, discord.User):
                        if message.author.guild_permissions.kick_members:
                            return
                    await message.delete()

                    log = Data(f"LOG {payload.emoji}", message.author, payload.member, message.created_at, message=message)
                    em  = log.embed(isLog=True)
                    try:
                        await guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
                    except:
                        traceback.print_exc()
                    log.to_dataframe()
        except:
            traceback.print_exc()

    # KICKS & BANS
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not member.guild.me.guild_permissions.view_audit_log:
            return

        await asyncio.sleep(5)
        guild = member.guild
        entries = [entry async for entry in guild.audit_logs(limit=20) if entry.action in (discord.AuditLogAction.kick, discord.AuditLogAction.ban) and entry.target.id == member.id]
        if len(entries) == 0:
            return
        
        # Check the last entry only
        entry = entries[0]
        if entry.action == discord.AuditLogAction.kick:
            log = Data(f"KICK", member, entry.user, entry.created_at, reason=entry.reason)
            em  = log.embed(isSanction=True)
            try:
                await guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
            except:
                traceback.print_exc()
            log.to_dataframe()

        if entry.action == discord.AuditLogAction.ban:
            log = Data(f"BAN", member, entry.user, entry.created_at, reason=entry.reason)
            if entry.user == member.guild.me:
                return
            em  = log.embed(isSanction=True)
            try:
                await guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
            except:
                traceback.print_exc()
            log.to_dataframe()
            await guild.get_channel(ChannelId.channel_moderation).send(content=None, embed=discord.Embed(color=0x6eaa5e, description=f":hammer: {str(member)} a été ban par {str(entry.user)}"))   

    # TIMEOUT & ROLE EDIT
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        try:
            # DEBUT TIMEOUT
            if after.is_timed_out() and not before.is_timed_out():
                if after.guild.me.guild_permissions.view_audit_log:
                    await asyncio.sleep(5)
                    entries = [entry async for entry in after.guild.audit_logs(limit=20) if entry.target.id == after.id and entry.after.timed_out_until and not entry.before.timed_out_until]
                    if len(entries) == 0:
                        return
                    
                    # Check the last entry
                    entry = entries[0]
                    log = Data(f"TIMEOUT", after, entry.user, entry.created_at, reason=entry.reason)
                
                else:
                    log = Data(f"TIMEOUT", after, after.guild.me, discord.utils.utcnow())

                em  = log.embed(isSanction=True)
                try:
                    await after.guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
                except:
                    traceback.print_exc()
                log.to_dataframe()

            # FIN TIMEOUT
            if not after.is_timed_out() and before.is_timed_out():
                await after.guild.get_channel(ChannelId.channel_moderation).send(embed=discord.Embed(description=f':alarm_clock: {after.mention} a terminé son time-out !'))

            # AJOUT ROLES
            roles_after  = [item for item in after.roles if item not in before.roles]
            roles_before = [item for item in before.roles if item not in after.roles]
            if len(roles_after) == 0 and len(roles_before) == 0:
                return
            
            # AUTOROLES
            # NOT VERIFIED YET
            for role in roles_after:
                if role.id in RolesId.autoroles_list:
                    await after.guild.get_channel(ChannelId.channel_autoroles).send(content=f":green_circle: {after.mention} a obtenu le rôle {role.name}")
            for role in roles_before:
                if role.id in RolesId.autoroles_list:
                    await after.guild.get_channel(ChannelId.channel_autoroles).send(content=f":red_circle: {after.mention} a perdu le rôle {role.name}")

            # QUARANTAINE
            # NOT VERIFIED YET
            for role in roles_after:
                if role.id in RolesId.quarantaine_list:
                    if after.guild.me.guild_permissions.view_audit_log:
                        await asyncio.sleep(5)
                        entries = [entry async for entry in after.guild.audit_logs(limit=20, action=discord.AuditLogAction.member_role_update) if entry.target.id == after.id and role in entry.after.roles]
                        if len(entries) != 0:
                            
                            # Check the last entry
                            entry = entries[0]
                            log = Data(f"MISE EN QUARANTAINE", after, entry.user, entry.created_at)
                            em  = log.embed(isSanction=True)
                            try:
                                await after.guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
                            except:
                                traceback.print_exc()
                            log.to_dataframe()
        except:
            traceback.print_exc()

    # MUTE
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if after.mute and not before.mute:
            channel = member.guild.get_channel(ChannelId.channel_moderation)
            await channel.send(embed=discord.Embed(description=f':mute: {str(member)} a été mute dans {after.channel.mention}', color=0xfe0000))
        if before.mute and not after.mute:
            channel = member.guild.get_channel(ChannelId.channel_moderation)
            await channel.send(embed=discord.Embed(description=f":loud_sound: {str(member)} n'est plus mute !", color=0x6eaa5e))
            
async def setup(bot):
    await bot.add_cog(Moderation(bot))