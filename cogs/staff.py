import discord
from discord.ext import commands
from datetime import datetime
from utils import Console
from config.id import *
import pandas as pd
import asyncio

class RemindModal(discord.ui.Modal, title='Note pour plus tard'):
    content = discord.ui.TextInput(
                label='Note',
                style=discord.TextStyle.long,
                placeholder='Ecrire...')
    date    = discord.ui.TextInput(
                label='Date',
                max_length=8)
    time    = discord.ui.TextInput(
                label='Heure',
                max_length=5)
    
    def save(self, time, user, content):
        df = pd.read_csv(RemindClass.path)
        df.loc[len(df)] = [time.isoformat(), user.id, content.replace('\n', '\\n')]
        df.to_csv(RemindClass.path, index=False)

    async def on_submit(self, interaction: discord.Interaction):
        # Check scheduled time
        scheduled_time = datetime.strptime(f"{self.date.value} {self.time.value}", "%d/%m/%y %Hh%M")
        if scheduled_time < datetime.today():
            await interaction.response.send_message(embed=discord.Embed(description="Erreur : impossible de briser la causalité de l'espace-temps !", color=0xfe0000), ephemeral=True)
            return

        # Save in file
        self.save(scheduled_time, interaction.user, self.content.value)

        # Response
        delta = scheduled_time - datetime.today()
        if delta.seconds // 3600 == 0:
            reste = f"{delta.seconds // 60}mn"
        else:
            reste = f"{delta.seconds // 3600}h"
        em = discord.Embed(color=0x6eaa5e, description=f"C'est bien noté, {interaction.user.name} ! Rappel dans {reste} :pencil:")
        await interaction.response.send_message(embed=em, ephemeral=True)

        # Start task
        await RemindClass.start_task(scheduled_time, interaction.user, self.content.value)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await RemindClass.print_error(self.console, interaction, error)

class RemindClass():
    path = "data/remind.dat"
    def __init__(self, bot, console):
        self.modal = RemindModal()
        self.modal.children[1].default = datetime.today().strftime("%d/%m/%y")
        self.modal.children[2].default = datetime.today().strftime("%Hh%M")
        self.modal.bot = bot
        self.modal.console = console

    @staticmethod
    async def remind(user: discord.Member, content: str):
        dm_channel = await user.create_dm()
        em = discord.Embed(title="**Rappel**", description=content)
        await dm_channel.send(embed=em)

    @staticmethod
    def clear(content):
        df = pd.read_csv(RemindClass.path)
        index = df.set_index('content').index.get_loc(content)
        df = df.drop(index)
        df.to_csv(RemindClass.path, index=False)
    
    @staticmethod
    async def start_task(scheduled, user, content):
        await discord.utils.sleep_until(scheduled)
        await RemindClass.remind(user, content.replace('\\n', '\n'))
        RemindClass.clear(content.replace('\n', '\\n'))
    
    @staticmethod
    async def print_error(console, interaction, error):
        await console.print_error(interaction, error)        

class Staff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        asyncio.get_event_loop().create_task(self.init_remind())

    async def init_remind(self):
        df_remind = pd.read_csv(RemindClass.path)
        await self.bot.wait_until_ready()
        self.console = Console(self.bot, ConsoleId.moderation)
        for ii in range(df_remind.shape[0]):
            remind_note = df_remind.iloc[ii]
            time    = datetime.fromisoformat(remind_note['time'])
            user    = self.bot.get_user(remind_note['user'])
            content = remind_note['content']
            await RemindClass.start_task(time, user, content)

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

    # Remind
    @discord.app_commands.command(name='remind', description="S'envoyer un message plus tard pour ne rien oublier")
    @discord.app_commands.guilds(discord.Object(GuildId.default))
    async def _remind(self, interaction: discord.Interaction):
        reminder = RemindClass(self.bot, self.console)
        await interaction.response.send_modal(reminder.modal)

async def setup(bot):
    await bot.add_cog(Staff(bot))