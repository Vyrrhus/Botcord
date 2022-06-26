from config.id import ConsoleId
import traceback

class Console:
    def __init__(self, bot, id=None):
        if not id:
            id = ConsoleId.default
        self.channel = bot.get_channel(id)

    async def print_command(self, ctx):
        await self.print(f"{ctx.author.display_name} : `{ctx.prefix}{ctx.command}` in `#{ctx.channel.name}`\n{ctx.message.content}")
    
    async def print_error(self, ctx, error):
        await self.print(f":x: Exception dans la commande {ctx.command} : {type(error)}\n```{error}```")
        await self.print(f"Traceback: ```{error.__traceback__}```")

    async def print(self, content, embed=None, view=None, file=None, files=None):
        try:
            await self.channel.send(content, embed=embed, view=view, file=file, files=files)
        except:
            print("La console est inaccessible !")
            traceback.print_exc()

# File handlers
def read(path, split=False):
    with open(path, 'r') as file:
        data = file.read()
    
    if split:
        data = data.split(',')
        data = [el for el in data if el != '']

    return data

def write_append(path, data):
    dataFile = read(path, split=True)
    for el in data:
        if el.lower() not in dataFile:
            dataFile.append(el.lower())
    
    with open(path, 'w') as file:
        file.write(','.join(dataFile))

def write_remove(path, data):
    dataFile = read(path, split=True)
    dataRemoved = []
    for el in data:
        if el.lower() in dataFile:
            dataFile.remove(el.lower())
            dataRemoved.append(el.lower())
    
    with open(path, 'w') as file:
        file.write(','.join(dataFile))
    
    return dataRemoved