import discord
import pandas as pd
from config.id import ConsoleId
import traceback

class Data:
    path = 'data/moderation.dat'

    def __init__(self, title, target, author, time, reason=None, dm=None, message=None):
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
            content = self.message.content.replace('\\n', '%newline%')
        else:
            id, channel_id, content = None, None, None
        
        if self.dm:
            dm = self.dm.replace('\\n', '%newline%')
        else:
            dm = None
        
        if self.reason:
            reason = self.reason.replace('\\n', '%newline%')
        else:
            reason = None

        df.loc[len(df)] = [self.type, self.target.id, self.author.id, str(self.time), reason, dm, id, channel_id, content]
        df.to_csv(self.path, index=False)

class Console:
    def __init__(self, bot, id=None):
        if not id:
            id = ConsoleId.default
        self.channel = bot.get_channel(id)

    async def print_command(self, ctx):
        await self.print(f"{ctx.author.display_name} : `{ctx.prefix}{ctx.command}` in `#{ctx.channel.name}`\n{ctx.message.content}")
    
    async def print_error(self, error):
        await self.print(f":x: Une erreur est survenue :x: \n{str(error)}")

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