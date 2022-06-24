from discord.ext import commands

def check_category(category_id):
    def predicate(ctx):
        return ctx.channel.category_id == category_id

    return commands.check(predicate)

def check_channel(channel_id):
    def predicate(ctx):
        return ctx.channel.id == channel_id
    
    return commands.check(predicate)