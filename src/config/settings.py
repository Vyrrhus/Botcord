# -*- coding: utf-8 -*-
import json

data = {}

if __name__ == 'src.config.settings':
	try:
		with open('src/config/settings.json', encoding="utf-8") as file:
			data = json.load(file)
	except Exception as error:
		print('settings.json ne peut pas être lu. [{}]'.format(error))