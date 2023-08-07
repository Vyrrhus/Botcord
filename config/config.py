""" Config Classes
"""
from __future__ import annotations
from typing import Dict, List, Any
import json
from inspect import cleandoc

import discord
from discord.ext import commands

###############################################################################
#   PRIVATE FUNCTIONS
def _read(filename: str, isInteger=False) -> str:
    """ Private function : read .config file"""
    with open(filename, 'r') as file:
        data = file.read()
    
    if isInteger:       return int(data)
    else:               return data

###############################################################################
#   CLASS

class SetupBase:
    prefix = ""

    """ Setup Base class """
    def set_params(self, **data:Dict[str, Any]) -> None:
        """ Add attributes to class, given a prefix """
        for key, value in data.items():
            if self.prefix in key:
                setattr(self, key.split(self.prefix)[1], value)
    
    #--------------------------------------------------------------------------
    #   PROPERTIES
    @property
    def params(self) -> List[str]:
        """ List of attributes """
        return [key for key in self.__dict__.keys() if key != "prefix"]
    
    @property
    def size(self) -> int:
        """ Number of attributes """
        return len(self.params)

    @property
    def to_dict(self) -> Dict:
        """ Convert class attributes to a dictionnary """
        return {
            key: value 
            for key, value in self.__dict__.items()
        }

    @property
    def buttonType(self) -> str:
        pass

    #--------------------------------------------------------------------------
    #   METHODS
    def embed(
            self, 
            bot: commands.Bot, 
            guild_id: int,
            key:str,
            title: str = ""
        ) -> discord.Embed:
        """ Override this method with subclasses """
        pass

class SetupRole(SetupBase):
    """ Setup Role Class """
    description = {
        "staff":    """ Les rôles sélectionnés sont ceux qui peuvent
                        utiliser les commandes /cogs et /role. \n
                        ▫️ /cogs : activate ou désactivation des groupes
                        de commandes. \n
                        ▫️ / role : notifie les changements de rôles
                        choisis dans le canal où se fait la commande.
                    """,
        "quarantine":   """ Les rôles sélectionnés sont ceux qui peuvent
                            déclencher le log "Mise en quarantaine".
                        """
    }

    def __init__(self, prefix="role_", **data) -> None:
        """ Setup Role Constructor """
        self.prefix = prefix

        # Roles
        self.staff:      List[int]
        self.quarantine: List[int]

        self.set_params(**data)

    def embed(
            self, 
            bot: commands.Bot,
            key:str,
            title: str = ""
        ) -> discord.Embed:
        """ discord.Embed associated to a given attribute key """
        description = self.description[key]
        guild = bot.get_guild(GUILD)
        embed = discord.Embed.from_dict(
            {
                "title":  title if title else None,
                "description": cleandoc(description),
                "fields": [{
                    "value": cleandoc("\n ".join([
                        "▫️ " + guild.get_role(role_id).name
                        for role_id in self.__dict__[key]
                    ])),
                    "name": "Rôles actuels :" 
                }]
            }
        )

        return embed

class SetupChannel(SetupBase):
    """ Setup Channel | Category Class """
    description = {
        "moderation":   """ Le canal sélectionné est celui où le bot
                            va envoyer une notification pour : \n
                            ▫️ l'interruption d'un time-out \n
                            ▫️ le mute / unmute en vocal \n
                            ▫️ l'arrivée de quelqu'un sur le serveur avec
                            déjà au moins un log.
                        """,
        "logs":         """ Le canal sélectionné est celui où le bot
                            va publier un log : \n
                            Kick, Ban, time-out, mise en quarantaine, 
                            logs 👀 et logs ❌.
                        """
    }
    
    def __init__(self, prefix="channel_", **data) -> None:
        self.prefix = prefix

        """ Setup Channel | Category Constructor """
        # Channel
        self.moderation: int
        self.logs:       int

        self.set_params(**data)

    def embed(
            self, 
            bot: commands.Bot,
            key:str,
            title: str = ""
        ) -> discord.Embed:
        """ discord.Embed associated to a given attribute key """
        description = self.description[key]
        embed = discord.Embed.from_dict(
            {
                "title":  title if title else None,
                "description": cleandoc(description),
                "fields": [{
                    "value": cleandoc("\n ".join([
                        "▫️ " + bot.get_channel(channel_id).name
                        for channel_id in [self.__dict__[key]]
                    ])),
                    "name": "Canal textuel actuel : "
                }]
            }
        )

        return embed

class SetupManager:
    """ Setup Manager Class """
    def __init__(self, bot: commands.Bot, config: ConfigBot) -> None:
        """ Setup Manager Constructor """
        self.config = config
        self.bot    = bot

        # Select type
        self.currentGroup: str = None
        self.currentParam: str = None

    #--------------------------------------------------------------------------
    #   PROPERTIES
    @property
    def setupGroups(self) -> List[str]:
        """ List of SetupBase attributes """
        return [
            key 
            for key, value in self.config.__dict__.items() 
            if isinstance(value, SetupBase)
        ]

    @property
    def setupParams(self) -> Dict[str, List[str]]:
        """ Dict of attributes within SetupBase instances """
        params = {}
        for key in self.setupGroups:
            setupGroup: SetupBase = self.config.__dict__[key]
            params[key] = setupGroup.params

        return params
    
    @property
    def setupSize(self) -> int:
        """ Number of parameters in SetupBases instances """
        number = 0
        for key in self.setupGroups:
            setupGroup: SetupBase = self.config.__dict__[key]
            number += len(setupGroup.params)

        return number
    
    #--------------------------------------------------------------------------
    #   METHODS
    async def navigate(self, page: int):
        """ Coroutine for Paginator (called by navigation buttons) """
        n = self.setupSize
        groupName = [
            key 
            for key, value in self.setupParams.items() 
            for _ in range(len(value))
        ]
        paramName = [
            param 
            for sublist in self.setupParams.values() 
            for param in sublist
        ]
        self.currentGroup = groupName[page - 1]
        self.currentParam = paramName[page - 1]

        group: SetupBase = self.config.__dict__[self.currentGroup]
        embed : discord.Embed = group.embed(
            self.bot,
            self.currentParam,
            title="🔧 Configuration des commandes 🔧"
        )

        return embed, n

class ConfigBot:
    """ Config Bot Class """
    def __init__(self, filename: str = "config/id/id.json"):
        """ Config Bot Constructor """
        self.filename = filename

        # Setup parameters
        self.role: SetupRole
        self.channel: SetupChannel

        self.set_params(**self.data)

    #--------------------------------------------------------------------------
    #   PROPERTIES
    @property
    def data(self) -> Dict:
        """ Read external file to get data as a dictionnary """
        with open(self.filename, "r") as file:
            data = json.load(file)
        
        return data
    
    #--------------------------------------------------------------------------
    #   METHODS
    def set_params(self, **params):
        """ Set parameters in the config file """
        if not hasattr(self, "role"):
            self.role = SetupRole(**params)
            for key in self.role.__dict__.keys():
                params.pop(f"{self.role.prefix}{key}", None)
        else:
            self.role.set_params(**params)

        if not hasattr(self, "channel"):
            self.channel = SetupChannel(**params)
            for key in self.channel.__dict__.keys():
                params.pop(f"{self.channel.prefix}{key}", None)
        else:
            self.channel.set_params(**params)
        
        for key, value in params.items():
            setattr(self, key, value)

    def to_json(self) -> None:
        """ Store attributes into .json file """
        data = {}
        for key, value in self.__dict__.items():
            if key == "filename":   continue

            if not isinstance(value, SetupBase):
                data[key] = value

            else:
                for keySetupBase, valueSetupBase in value.__dict__.items():
                    if keySetupBase == "prefix":     continue
                    data[f"{value.prefix}{keySetupBase}"] = valueSetupBase

        with open(self.filename, "w") as file:
            json.dump(data, file, indent=4)

###############################################################################
#   TOKEN, PREFIX, EXTENSIONS

TOKEN  = _read('config/token.config')
PREFIX = _read('config/prefix.config')
GUILD  = _read('config/id/guild.config', isInteger=True)
OWNER  = _read('config/id/owner.config', isInteger=True) 