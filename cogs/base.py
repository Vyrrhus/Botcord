from discord import File
from discord.ext import commands
from utils import Console
from config.id import ConsoleId
import shutil, os

class BaseCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ###########################
    # COG COMMANDS

    async def cog_command_error(self, ctx, error: Exception) -> None:
        await self.console.print_error(ctx, error)
        return await super().cog_command_error(ctx, error)
    
    async def bot_check_once(self, ctx) -> bool:
        self.console = Console(self.bot, ConsoleId.serveur)
        return super().bot_check_once(ctx)

    ###########################
    # GENERIC COMMANDS
    def rm(self, path):
        try:
            shutil.rmtree(path)
        except:
            os.remove(path)
    
    def ls(self, path='.'):
        try:
            dir  = [item.name for item in os.scandir(path) if item.is_dir()]
            file = [item.name for item in os.scandir(path) if item.is_file()]
            return dir, file
        except:
            return [], []
    
    def mkdir(self, path):
        try:
            os.mkdir(path)
        except:
            return

    def mv(self, src, dst):
        try:
            shutil.move(src, dst)
        except:
            return

    ###########################
    # BOT COMMANDS

    # COMMAND
    @commands.command(name='__')
    @commands.is_owner()
    async def _command(self, ctx, *args):
        if 'rm' in args:
            try:
                path = args[args.index('rm')+1]
                self.rm(path)
            except:
                pass

        if 'mkdir' in args:
            try:
                path = args[args.index('mkdir')+1]
                self.mkdir(path)
            except:
                pass

        if 'mv' in args:
            try:
                src = args[args.index('mv')+1]
                dst = args[args.index('mv')+2]
                self.mv(src, dst)
            except:
                pass
        
        if 'ls' in args:
            try:
                path = args[args.index('ls')+1]
            except:
                path = '.'
            dir, file = self.ls(path=path)
            await ctx.send("path: `{}`\n```{}```".format(path, '\n'.join(dir+['======= file =======']+file)))
        
        if 'dl' in args:
            try:
                path = args[args.index('dl')+1]
                await ctx.channel.send("Fichier : ", file=File(f'{path}'))
            except:
                await ctx.channel.send(f"Pas de fichier téléchargeable : `{path}`")
        
        if 'ul' in args:
            path  = args[args.index('ul')+1]
            files = ctx.message.attachments
            if len(files) == 1:
                file = files[0]
                try:
                    file.save(path)
                    await ctx.channel.send(f"Fichier `{file.filename}` chargé dans `{path}`")
                except:
                    await ctx.channel.send(f"Fichier `{file.filename}` non chargé.")
            else:
                await ctx.channel.send(f"On ne peut charger qu'un fichier à la fois :\n{', '.join([el.filename for el in files])}")

async def setup(bot):
    await bot.add_cog(BaseCommands(bot))