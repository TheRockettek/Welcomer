import asyncio
import aiohttp
import discord
import os
import string
import unicodedata

import ujson as json
from random import randint

if "nt" in os.name:
    try:
        from colorama import init
        init()
    except:
        pass

class RockUtils():
    class InvalidFileIO(Exception):
        pass

    colour_prefix = {"default": "39",
    "black": "30",
    "red": "31",
    "green": "32",
    "yellow": "33",
    "blue": "34",
    "magenta": "35",
    "cyan": "36",
    "light grey": "37",
    "dark grey": "90",
    "light red": "91",
    "light green": "92",
    "light yellow": "93",
    "light blue": "94",
    "light magenta": "95",
    "light cyan": "96",
    "white": "97"}

    def pprint(self, text, prefix="Welcomer", text_colour="default", prefix_colour="light blue"):
        text_colour = self.colour_prefix.get(text_colour.lower(), "97")
        prefix_colour = self.colour_prefix.get(prefix_colour.lower(), "39")
        print(f"[\033[{prefix_colour}m{prefix}\033[0m] \033[{text_colour}m{text}\033[0m")


    def merge(self, _dict):
        result = []
        for cluster in dictlist.values():
            results += cluster
        return result

    def normalize(self, string):
        return unicodedata.normalize("NFKC", string).encode("ascii", "ignore").decode()

    async def send_webhook(self, url, text, **kwargs):
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(content=text, **kwargs)

    def save_json(filename,data):
        path, ext = os.path.splitext(filename)
        tmp_file = f"{path}-{randint(1000, 9999)}.tmp"
        self._save_json(tmp_file, data)
        try:
            self._read_json(tmp_file)
        except json.decoder.JSONDecodeError:
            return False
        os.replace(tmp_file, filename)
        return True

    def load_json(self, filename):
        return self._read_json(filename)

    def is_valid_json(self, filename):
        try:
            self._read_json(filename)
            return True
        except FileNotFoundError:
            return False
        except json.decoder.JSONDecodeError:
            return False

    def _read_json(self, filename):
        with open(filename, encoding='utf-8', mode="r") as f:
            data = json.load(f)
        return data

    def _save_json(self, filename, data):
        with open(filename, encoding='utf-8', mode="w") as f:
            json.dump(data, f, indent=4,sort_keys=True,
                separators=(',',' : '))
        return data

rockutils = RockUtils()