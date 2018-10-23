# -*- coding: utf-8 -*-
import json
import discord
from discord.ext.commands import Bot

data = {}
client = ''

if __name__ == 'src.config.settings':
	try:
		with open('src/config/settings.json', encoding="utf-8") as file:
			data = json.load(file)
	except Exception as error:
		print('settings.json ne peut pas être lu. [{}]'.format(error))
	try:
		BOT_PREFIX = (data['PREFIX'])
		client = Bot(command_prefix = BOT_PREFIX)
	except Exception as error:
		print('Something wrong in client init')