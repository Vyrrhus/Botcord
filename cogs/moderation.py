import discord
from discord.ext import commands
from check import check_category
from utils import Console
from config.id import RolesId, ChannelId, ConsoleId
import traceback
import asyncio
import numpy as np
import pandas as pd

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
        
        self.emDict = {"title": f"{target.display_name} ({str(target)})",
                       "type": "rich",
                       "color": 0x1db868,
                       "timestamp": discord.utils.utcnow().isoformat()}
        
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
        # Ajouter : timestamp (str to datetime.isoformat())
        # Ajouter : time-out durée restante si applicable
        log = self.logs.iloc[[self.num - 1]].replace({np.nan:None}).to_dict(orient='list')
        log = {key: log[key][0] for key in log}
        self.emDict["fields"] = [{"name": "Motif :", "value": log['type'], "inline": True}]

        moderateur = self.bot.get_user(log['moderateur'])
        if isinstance(moderateur, discord.User):
            self.emDict["fields"].append({"name": "Modérateur", "value": f"{self.bot.get_user(log['moderateur']).mention}"})
        if log['raison']:
            self.emDict["fields"].append({"name": "Raison", "value": log['raison']})
        if log['channel_id'] and log['contenu']:
            self.emDict["fields"].append({"name": "Salon", "value": f"Dans <#{log['channel_id']}>"})
            self.emDict["fields"].append({"name": "Message", "value": log["contenu"]})

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

# STRUCTURES
class Data:
    path = 'data/moderation.dat'

    def __init__(self, title, target, author, time, reason='', dm='', message=None):
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
                  "thumbnail": {"url": "https://cdn3.emoji.gg/emojis/9299-blurple-ban.png"},
                  "timestamp": self.time.isoformat(),
                  "fields": [{"name": "Utilisateur",
                              "value": self.target.mention,
                              "inline": True},
                              {"name": "Modérateur",
                              "value": self.author.mention,
                              "inline": True}]}
        
        # Modération d'un message
        if isLog and self.message:
            emDict["color"] = 0x0153f7
            emDict["fields"].append({"name": "Salon", "value": f"<#{self.message.channel.id}>"})
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
        
        emDict["title"] = f"[{self.type}] - {self.target.display_name} ({str(self.target)})"
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
            id = self.message.id
            channel_id = self.message.channel.id
        else:
            id, channel_id, content = None, None, ''
        
        df.loc[len(df)] = [self.type, self.target.id, self.author.id, self.time.isoformat(), self.reason.replace('\n', '\\n'), self.dm.replace('\n', '\\n'), id, channel_id, content.replace('\n', '\\n')]
        df.to_csv(self.path, index=False)

# COG CLASS
class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
    # COMMANDS

    # LIBRE
    @commands.command(name='libre', pass_context=True)
    @commands.has_guild_permissions(kick_members=True)
    @check_category(ChannelId.category_moderation)
    async def _libre(self, ctx):
        await ctx.message.delete()
        await ctx.send('```LIBRE```')

    # LOG VIEW : SEE AND CLEAR LOGS
    @commands.command(name='log', pass_context=True)
    @commands.has_guild_permissions(kick_members=True)
    @check_category(ChannelId.category_moderation)
    async def _log(self, ctx, target:discord.Member):
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
    @commands.command(name='sram', pass_context=True, hidden=True)
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
            await channel.send(f':star: {str(member)} a rejoint le serveur avec {user_logs.shape[0]} logs')

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
        if not self.bot.get_guild(member.guild.id).me.guild_permissions.view_audit_log:
            return

        await asyncio.sleep(5)
        guild = self.bot.get_guild(member.guild.id)
        entries = [entry async for entry in guild.audit_logs(limit=20) if entry.action in (discord.AuditLogAction.kick, discord.AuditLogAction.ban) and entry.target.id == member.id]
        if len(entries) == 0:
            return
        
        # Check the last entry only
        entry = entries[0]
        if entry.action == discord.AuditLogAction.kick:
            # NOT VERIFIED YET
            log = Data(f"KICK", member, entry.user, entry.created_at, reason=entry.reason)
            em  = log.embed(isSanction=True)
            try:
                await guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
            except:
                traceback.print_exc()
            log.to_dataframe()

        if entry.action == discord.AuditLogAction.ban:
            # NOT VERIFIED YET
            log = Data(f"BAN", member, entry.user, entry.created_at, reason=entry.reason)
            em  = log.embed(isSanction=True)
            try:
                await guild.get_channel(ChannelId.channel_log).send(content=None, embed=em)
            except:
                traceback.print_exc()
            log.to_dataframe()        

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
                await after.guild.get_channel(ChannelId.channel_moderation).send(content=f':alarm_clock: {after.mention} a terminé son time-out !')

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

async def setup(bot):
    await bot.add_cog(Moderation(bot))