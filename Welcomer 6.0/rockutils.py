import asyncio
import aiohttp
import base64
import discord
import gettext
import os
import re
import math
import string
import time
import random
import unicodedata

import rethinkdb as r
from discord.ext import commands
from urllib.parse import urlparse
from datetime import datetime

if "nt" in os.name:
    try:
        from colorama import init
        init()
    except:
        pass

try:
    import ujson as json
except:
    print("Could not import ujson, defaulting to built-in json library")
    import json

class RockUtils():

    def __init__(self):
        self.long_prefix = 0
        self.langs = {}

    class InvalidFileIO(Exception):
        pass

    colour_prefix = {
        "default": "39",
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
        "white": "97"
    }

    def markmessage(self, string, guild):
        # converts special message mentions such as
        # channel mentions #
        # emojis <a?:...:0>
        # to normalised messages

        found_channels = set(re.findall("\#([a-zA-Z-]+)",string))
        found_emotes = set(re.findall(":(\S+):", string))

        for emote in found_emotes:
            _emote = discord.utils.get(guild.emojis, name=emote)
            if _emote:
                string = string.replace(f":{emote}:", str(_emote))

        for channel in found_channels:
            _channel = discord.utils.get(guild.channels, name=channel)
            if _channel:
                string = string.replace(f"#{channel}",_channel.mention)

        return string

    def strip_emotes(self, message, emojis):
        # converts string with :emotes: to their valid counterparts
        _server_emojis = []
        for emoji in emojis:
            _server_emojis[emoji.name] = str(emoji)
        
        _message_emojis = re.findall(":.*?:", message)
        for emoji in _message_emojis:
            if emoji[1:-1] in _server_emojis:
                message = message.replace(emoji, _message_emojis[emoji[1:-1]])
        return message

    def getprefix(self, intager):
        strint = str(intager)
        if strint[-1] == "1" and strint[-2:] != "11":
            return "st"
        if strint[-1] == "2" and strint[-2:] != "12":
            return "nd"
        if strint[-1] == "3" and strint[-2:] != "13":
            return "rd"
        return "th"

    def retrieve_time_emoji(self):
        a = int((time.time()/900-3)/2%24)
        return chr(128336+a//2+a%2*12)

    def text_format(self, message, formatting, encapsulation=["{","}"]):
        for _key, _value in formatting.items():
            message = message.replace(encapsulation[0] + str(_key) + encapsulation[1], str(_valie))
        return message

    def parse_unix(self, unix):
        _d = math.floor(unix/86400)
        unix = unix - (_d*86400)
        _h = math.floor(unix/3600)
        unix = unix - (_h*3600)
        _m = math.floor(unix/60)
        unix = unix - (_m*60)
        _s = math.ceil(unix)

        return _d,_h,_m,_s

    async def incr_db(self, connection, db, table, key, count=1, keyname="count"):
        return await r.db(db).table(table).get(key).update({keyname: r.row[keyname]+count}).run(connection)

    def incr_db_noasync(self, connection, db, table, key, count=1, keyname="count"):
        return r.db(db).table(table).get(key).update({keyname: r.row[keyname]+count}).run(connection)

    def produce_timestamp(self, seconds, include_days=True, include_seconds=True):
        # converts seconds to timestamp: 63 to 0D - 0H - 1M - 3S
        _d,_h,_m,_s = self.parse_unix(seconds)

        message = ""
        if include_days and _d > 0:
            message += f"{_d} D - "
        else:
            h += _d*24
        message += f"{_h} H - {_m} M"
        if include_seconds:
            message += f" - {_s} S"
        return message

    def since_seconds_str(self, seconds, allow_secs=False, include_ago=True):
        _d, _h, _m, _s = self.parseUnix(seconds)

        message = ""
        if _d > 0:
            message += f"{str(_d)} day{'s' if _d > 1 else ''} "
        if _h > 0:
            if _m < 0:
                message += "and "
            elif len(message) > 1:
                message += ", "
            message += f"{str(_h)} hour{'s' if _h > 1 else ''} "
        if _m > 0:
            if _h > 0 or _d > 0:
                message += "and "
            message += f"{str(_m)} minute{'s' if _m > 1 else ''} "
        if allow_secs:
            if _h > 0 or _d > 0 or _m > 0:
                message += "and "
            message += f"{str(_s)} second{'s' if _s > 1 else ''} "
        if include_ago:
            message += "ago"
        return message

    def since_unix_str(self, unix, lang=["second","minute","hour","day","and","ago"], allow_secs=False, include_ago=True):
        _d, _h, _m, _s = self.parseUnix(time.time() - unix)

        message = ""
        if _d > 0:
            message += f"{str(_d)} {lang[3]}{'s' if _d > 1 else ''} "
        if _h > 0:
            if _m < 0:
                message += f"{lang[4]} "
            elif len(message) > 1:
                message += ", "
            message += f"{str(_h)} {lang[2]}{'s' if _h > 1 else ''} "
        if _m > 0:
            if _h > 0 or _d > 0:
                message += f"{lang[4]} "
            message += f"{str(_m)} {lang[1]}{'s' if _m > 1 else ''} "
        if allow_secs:
            if _h > 0 or _d > 0 or _m > 0:
                message += f"{lang[4]} "
            message += f"{str(_s)} {lang[0]}{'s' if _s > 1 else ''} "
        if include_ago:
            message += lang[5]
        return message

    def retrieve_gmt(self, format="%d %b %Y %H:%M:%S"):
        return time.strftime(format, time.gmtime(time.time()))

    def get_selection(self, text, fallback):
        text = text.lower()
        if text in ['yes','y','true','t','enable','on','active','activate']:
            return True
        if text in ['no','n','false','f','disable','off','inactive','deactivate']:
            return False
        return not fallback

    def prefix_print(self, text, prefix="Welcomer", text_colour="default", prefix_colour="light blue"):
        text_colour = self.colour_prefix.get(text_colour.lower(), "97")
        prefix_colour = self.colour_prefix.get(prefix_colour.lower(), "39")
        pre = f"[\033[{prefix_colour}m{prefix.rstrip()}\033[0m]"
        # if len(pre) > self.long_prefix:
        #     self.long_prefix = len(pre)
        # pre = f"{' '*(self.long_prefix-len(pre))}{pre}"
        print(f"{pre}\033[{text_colour}m {text}\033[0m")

    def merge_embeded_lists(self, _dict):
        results = []
        for cluster in _dict.values():
            results += cluster
        return results

    def normalize(self, string, normal_format="NFKC", encode_format="ascii"):
        try:
            return unicodedata.normalize(normal_format, string).encode(encode_format, "ignore").decode()
        except:
            return string

    async def send_webhook(self, url, text, **kwargs):
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(url, adapter=discord.AsyncWebhookAdapter(session))
            await webhook.send(content=text, **kwargs)

    def save_json(self, filename, data):
        path, ext = os.path.splitext(filename)
        tmp_file = f"{path}-{random.randint(1000, 9999)}.tmp"
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
            json.dump(data, f)
        return data

    def add_lang(self, language):
        try:
            self.prefix_print(f"Loading language: {language}", prefix="gettext")
            l = gettext.translation('base', 'locale', languages=[language])
            l.install()
            self.langs[language] = l
            return True
        except Exception as e:
            self.prefix_print(f"Failed to load language: {e}", prefix="gettext", prefix_colour="light red")
            return False

    def regex_text(self, string, dlist, return_string=False):
        normalized_name = rockutils.normalize(string.lower())
        stripped_name = re.sub(r'\s+', '', normalized_name)
        bare_name = re.sub(r"[^0-9a-zA-Z]+",'',stripped_name)
        rlist = []
        for dom in dlist:
            rlist.append(dom)
            rlist.append(re.sub(r"[^0-9a-zA-Z]+",'',dom))
        for dom in rlist:
            if dom in stripped_name or dom in normalized_name or dom in string or dom in bare_name:
                if return_string:
                    return True, dom
                else:
                    return True
        if return_string:
            return False, ""
        else:
            return False

    def _(self, text, lang=None):
        if type(lang) == commands.Context and hasattr(lang, "userinfo"):
            pass
        if type(lang) == dict:
            try:
                lang = lang['g']['b']['l']
            except:
                pass

        if not lang:
            self.add_lang(lang)

        if not lang in self.langs:
            return text
        else:
            return self.langs[lang].gettext(text)

    def randstr():
        return base64.b64encode(bytes(str(time.time()*100000),"ascii")).decode().replace("=","").lower()


rockutils = RockUtils()

class GameRetriever():

    def __init__(self):
        self.http_cache = {}

        try:
            import valve.source.a2s
            self.has_a2s = True
        except:
            rockutils.prefix_print("Could not import valve.source.a2s, retrieving valve server data will not be possible", prefix_colour="light red", text_colour="red")
            self.has_a2s = False

        try:
            from mcstatus import MinecraftServer
            self.has_mc = True
        except:
            rockutils.prefix_print("Could not import mcstatus, retrieving minecraft data will not be possible", prefix_colour="light red", text_colour="red")
            self.has_mc = False

    async def retrieve_url(self, url, cache_time=30):
        _time = time.time()
        for _key, _value in self.http_cache.keys():
            if _time >= _value['time']:
                del self.http_cache[_key]

        _url_signature = hashlib.sha256(url.encode("utf8")).hexdigest()[-16:]
        if _url_signature in self.http_cache and "handler" in self.http_cache[_url_signature]:
            return self.http_cache[_url_signature]['handler']

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                self.http_cache[_url_signature] = {
                    "handler": response,
                    "time": _time + cache_time
                }
                return self.http_cache[_url_signature]['handler']

    async def youtube(self, channel_id):
        async with retrieve_url(f"https://www.youtube.com/channel/{channel_id}") as response:
            _sub_regex = re.findall('[0-9,]+ subscribers',h)
            if len(_sub_regex) > 0:
                return True, _sub_regex[0][:-12]
            else:
                return False, None

    async def twitter(self, display_name):
        async with retrieve_url(f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={display_name}") as response:
            try:
                _json_data = await response.json()
            except:
                return False, {}

            if len(_json_data) > 0:
                return True, _json_data[0]
            else:
                return False, _json_data

    async def steam_group(self, group_id):
        async with retrieve_url(f"https://steamcommunity.com/groups/{group_id}") as response:
            h = await response.text()
            data = {}
            info = re.findall('count ">[0-9,]+</div>', b)
            if len(info) == 0:
                data['ingame'] = 0
                data['online'] = 0
                data['members'] = 0
                data['display'] = "-"
                return False, data 
            else:
                data['ingame'] = info[0][8:-6]
                data['online'] = info[1][8:-6]
                data['members'] = re.findall('count">[0-9,]+</span>', b)[0][7:-7]
                data['display'] = re.findall('grouppage_header_abbrev" >.+</span>', b)[0][26:-7]
                return True, data

    async def factorio(self, game_id):
        async with retrieve_url(f"https://multiplayer.factorio.com/get-game/details/{game_id}") as response:
            try:
                _json_data = await response.json()
            except:
                return False, {}
            
            if "no game" in j.get("message"):
                return False, _json_data
            return True, _json_data

    async def a2s(self, ip):
        if not self.has_a2s:
            return False, None
        _split = ip.split(":")
        if len(_split) == 2:
            server = valve.source.a2s.ServerQuerier(_split,timeout=1)
            try:
                return True, server.info().values
            except valve.source.NoResponseError:
                return True, None
        else:
            return False, None

    async def minecraft(self, ip):
        if not self.has_mc:
            return False, None

        try:
            server = MinecraftServer.lookup(ip)
            return True, server.status()
        except:
            return False, None

gameretriever = GameRetriever()