""" Config Classes
"""
import json
from typing import Dict, List

###############################################################################
#   PRIVATE FUNCTIONS
def _read(filename: str) -> str:
    """ Private function : read .config file"""
    with open(filename, 'r') as file:
        return file.read()

###############################################################################
#   CLASS

class ClassID:
    """ ClassID Class """
    def __init__(self):
        """ ID Constructor """
        self.owner:                 int = None
        self.guild:                 int = None
        self.staff:                 int = None
        self.category_moderation:   int = None
        self.channel_moderation:    int = None
        self.channel_logs:          int = None
        self.quarantine:            List[int] = None

        # Set all attributes
        data = self._read()
        for key, value in data.items():
            setattr(self, key, value)

    def _read(self, filename: str ='config/id.json') -> Dict:
        """ Private method : read id stored in .json """
        with open(filename, 'r') as file:
            data = json.load(file)

        return data

###############################################################################
#   TOKEN, PREFIX, EXTENSIONS

TOKEN = _read('config/token.config')
PREFIX = _read('config/prefix.config')