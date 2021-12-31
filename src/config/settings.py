# -*- coding: utf-8 -*-
import json
import sys
import traceback
import discord
from discord.ext.commands import Bot
intents = discord.Intents.all()

try:
	with open('src/config/auth.json', encoding="utf-8") as auth_file:
		auth_data = json.load(auth_file)
except:
	traceback.print_exc()

TOKEN = auth_data["TOKEN"]
PREFIX = auth_data["PREFIX"]

MONITOR_MAIN = auth_data["MONITOR"]["MAIN"]
MONITOR_TWITTER = auth_data["MONITOR"]["TWITTER"]
MONITOR_MODERATION = auth_data["MONITOR"]["MODERATION"]
# MONITOR_SPACE = auth_data["MONITOR"]["SPACE"]

GUILD_ID = auth_data["GUILD"]

try:
	client = Bot(command_prefix=PREFIX, intents=intents)
except:
	traceback.print_exc()
	sys.exit()