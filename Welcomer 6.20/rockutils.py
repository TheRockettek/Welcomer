import aiohttp
import base64
import csv
import discord
import gettext
import os
import io
import re
import math
import time
import random
import unicodedata
import hashlib
import logging
import traceback
import sys
import functools

from aiofile import AIOFile as aiofile
from discord.ext import commands
from datetime import datetime

# import valve.source.a2s
# import mcstatus

if "nt" in os.name:
    try:
        from colorama import init
        init()
    except BaseException:
        pass

try:
    import ujson as json
except BaseException:
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

    def canint(self, value):
        try:
            return True, int(value)
        except BaseException:
            return False, value

    def canfloat(self, value):
        try:
            return True, float(value)
        except BaseException:
            return False, value

    def hasvalue(self, ref, _dict):
        ref_tree = ref.split(".")
        table = _dict
        for value, branch in enumerate(ref_tree):
            if value == len(ref_tree) - 1:
                return True
            elif branch in table:
                table = table[branch]
            else:
                return False

    def getvalue(self, ref, _dict, _fallback=None):
        ref_tree = ref.split(".")
        table = _dict
        for value, branch in enumerate(ref_tree):
            if value == len(ref_tree) - 1:
                return table[branch]
            elif branch in table:
                table = table[branch]
            else:
                return _fallback
        return _fallback

    def setvalue(self, ref, _dict, _value):
        ref_tree = ref.split(".")
        table = _dict
        for value, branch in enumerate(ref_tree):
            if value == len(ref_tree) - 1:
                table[branch] = _value
            else:
                if branch not in table:
                    table[branch] = {}
                table = table[branch]

    def encodeid(self, i):
        return base64.b32encode(
            i.to_bytes(
                (i.bit_length() + 8) // 8,
                'big',
                signed=True)).decode("ascii")

    def decodeid(self, i):
        return int.from_bytes(base64.b32decode(i.encode()), 'big', signed=True)

    def markmessage(self, _string, guild):
        # converts special message mentions such as
        # channel mentions #
        # emojis <a?:...:0>
        # to normalised messages

        _string = str(_string)
        found_channels = set(
            re.findall(
                r"#([a-zA-Z-]+)",
                _string) +
            re.findall(
                r"\{#([a-zA-Z- ]+)\}",
                _string))
        # found_emotes = set(re.findall(r":(\S+):", _string))

        # for emote in found_emotes:
        #     _emote = discord.utils.get(guild.emojis, name=emote)
        #     if _emote:
        #         _string = _string.replace(f":{emote}:", str(_emote))

        # for channel in found_channels:
        #     _channel = discord.utils.get(guild.channels, name=channel)
        #     if _channel:
        #         _string = _string.replace(f"#{channel}", _channel.mention)
        found_emotes = set(re.findall(r"(<?):([^:]+):", _string))

        for before, emote in sorted(found_emotes, key=lambda o: len(o), reverse=True):
            ignore = False
            raw = emote
            if before in ["<", "a"]:
                ignore = True

            if not ignore:
                _emote = discord.utils.get(guild.emojis, name=emote)
                if _emote:
                    # _string = _string.replace(f":{emote}:", str(_emote))
                    _string = _string.replace(f"{before}:{raw}:", f"{before}{_emote}")

        for channel in found_channels:
            _channel = discord.utils.get(guild.channels, name=channel)
            if _channel:
                _string = _string.replace(f"#{channel}", _channel.mention)

        return _string

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

    def retrieve_time_emoji(self, _t=None):
        if not _t:
            _t = time.time()
        a = int((_t / 900 - 3) / 2 % 24)
        return chr(128336 + a // 2 + a % 2 * 12)

    def text_format(self, message, formatting, encapsulation=["{", "}"]):
        for _key, _value in formatting.items():
            message = message.replace(encapsulation[0] + str(_key) + encapsulation[1], str(_value))
        return message

    def parse_unix(self, unix):
        if not unix:
            return 0, 0, 0, 0, 0
        _y = math.floor(unix / 31536000)
        unix = unix - (_y * 31536000)
        _d = math.floor(unix / 86400)
        unix = unix - (_d * 86400)
        _h = math.floor(unix / 3600)
        unix = unix - (_h * 3600)
        _m = math.floor(unix / 60)
        unix = unix - (_m * 60)
        _s = math.ceil(unix)

        return _y, _d, _h, _m, _s

    # async def incr_db(self, connection, db, table, key, count=1, keyname="count"):
    #     return await r.db(db).table(table).get(key).update({keyname: r.row[keyname] + count}).run(connection)

    # def incr_db_noasync(
    #         self, connection,
    #         db, table,
    #         key, count=1,
    #         keyname="count"):
    #     return r.db(db).table(table).get(key).update(
    #         {keyname: r.row[keyname] + count}).run(connection)

    def produce_human_timestamp(
            self,
            seconds,
            include_years=False,
            include_days=True,
            include_seconds=True):
        # converts seconds to timestamp: 63 to 0d,  0 h, 1 m, 3 s
        _y, _d, _h, _m, _s = self.parse_unix(seconds)
        message = ""

        if include_years:
            if _y > 0:
                message += f"{_y} y, "
        else:
            _d += (365 * _y)

        if include_days and _d > 0:
            message += f"{_d} d, "
        else:
            _h += _d * 24
        message += f"{_h} h, {_m} m"
        if include_seconds:
            message += f", {_s} s"

        return message

    def produce_timestamp(
            self,
            seconds,
            include_years=False,
            include_days=True,
            include_seconds=True):
        # converts seconds to timestamp: 63 to 0D - 0H - 1M - 3S
        _y, _d, _h, _m, _s = self.parse_unix(seconds)
        message = ""

        if include_years:
            if _y > 0:
                message += f"{_y} Y - "
        else:
            _d += (365 * _y)

        if include_days and _d > 0:
            message += f"{_d} D - "
        else:
            _h += _d * 24
        message += f"{_h} H - {_m} M"
        if include_seconds:
            message += f" - {_s} S"

        return message

    def since_seconds_str(self, seconds, allow_secs=False, include_ago=True):
        _y, _d, _h, _m, _s = self.parse_unix(seconds)
        message = ""

        if _y > 0:
            message += f"{_y} year{'s' if _y != 1 else ''}"
        if _d > 0:
            if _h < 0:
                message += " and "
            elif len(message) > 1:
                message += ", "
            message += f"{_d} day{'s' if _d != 1 else ''}"
        if _h > 0:
            if _m < 0:
                message += " and "
            elif len(message) > 1:
                message += ", "
            message += f"{_h} hour{'s' if _h != 1 else ''}"
        if _m > 0:
            if _s < 0 if allow_secs else (_h > 0 or _d > 0):
                message += " and "
            elif len(message) > 1:
                message += ", "
            message += f"{_m} minute{'s' if _m != 1 else ''}"
        if allow_secs:
            if _h > 0 or _d > 0 or _m > 0:
                message += " and "
            message += f"{_s} second{'s' if _s != 1 else ''}"
        if include_ago:
            message += " ago"

        return message

    def since_unix_str(
            self,
            unix,
            lang=[
                "second",
                "minute",
                "hour",
                "day",
                "and",
                "ago",
                "year"],
            allow_secs=False,
            include_ago=True):
        if not unix:
            unix = time.time()
        _y, _d, _h, _m, _s = self.parse_unix(time.time() - unix)

        # message = ""
        # if _y > 0:
        #     message += f"{str(_y)} {lang[6]}{'s' if _y > 1 else ''} "
        # if _d > 0:
        #     if _h < 0:
        #         message += f"{lang[4]} "
        #     elif len(message) > 1:
        #         message += ", "
        #     message += f"{str(_d)} {lang[3]}{'s' if _d > 1 else ''} "
        # if _h > 0:
        #     if _m < 0:
        #         message += f"{lang[4]} "
        #     elif len(message) > 1:
        #         message += ", "
        #     message += f"{str(_h)} {lang[2]}{'s' if _h > 1 else ''} "
        # # if we dont allow seconds, round the minutes up
        # if not allow_secs and _s > 0:
        #     _m += 1
        # if _m > 0:
        #     if _h > 0 or _d > 0:
        #         message += f"{lang[4]} "
        #     message += f"{str(_m)} {lang[1]}{'s' if _m > 1 else ''} "
        # if allow_secs:
        #     if _h > 0 or _d > 0 or _m > 0:
        #         message += f"{lang[4]} "
        #     message += f"{str(_s)} {lang[0]}{'s' if _s > 1 else ''} "
        # if include_ago:
        #     message += lang[5]
        # return message

        message = ""

        if _y > 0:
            message += f"{_y} year{'s' if _y != 1 else ''}"
        if _d > 0:
            if _h < 0:
                message += " and "
            elif len(message) > 1:
                message += ", "
            message += f"{_d} day{'s' if _d != 1 else ''}"
        if _h > 0:
            if _m < 0:
                message += " and "
            elif len(message) > 1:
                message += ", "
            message += f"{_h} hour{'s' if _h != 1 else ''}"
        if _m > 0:
            if _s < 0 if allow_secs else (_h > 0 or _d > 0):
                message += " and "
            elif len(message) > 1:
                message += ", "
            message += f"{_m} minute{'s' if _m != 1 else ''}"
        if allow_secs:
            if _h > 0 or _d > 0 or _m > 0:
                message += " and "
            message += f"{_s} second{'s' if _s != 1 else ''}"
        if include_ago:
            message += " ago"

        return message

    def retrieve_gmt(self, format="%d %b %Y %H:%M:%S"):
        return time.strftime(format, time.gmtime(time.time()))

    def gmt(self):
        return time.strftime("%d %b %Y %H:%M:%S", time.gmtime(time.time()))

    def get_selection(self, text, fallback):
        text = text.lower()
        if text in [
            'yes',
            'y',
            'true',
            't',
            'enable',
            'on',
            'active',
                'activate']:
            return True
        if text in [
            'no',
            'n',
            'false',
            'f',
            'disable',
            'off',
            'inactive',
                'deactivate']:
            return False
        return not fallback

    def prefix_print(
            self,
            text,
            prefix="Welcomer",
            text_colour="default",
            prefix_colour="light blue"):
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

    def merge_results_lists(self, _dict, key="results"):
        results = []
        for cluster in _dict.values():
            if cluster.get("success"):
                results += cluster.get(key, [])
        return results

    def normalize(self, _string, normal_format="NFKC", encode_format="ascii"):
        try:
            return unicodedata.normalize(
                normal_format, _string).encode(
                encode_format, "ignore").decode()
        except BaseException:
            return _string

    async def send_webhook(self, url, text, **kwargs):
        if not isinstance(url, list):
            url = [url]
        for url in url:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    url, adapter=discord.AsyncWebhookAdapter(session))
                await webhook.send(content=text, **kwargs)

    def save_json(self, filename, data):
        path, _ = os.path.splitext(filename)
        tmp_file = f"{path}-{random.randint(1000, 9999)}.tmp"
        self._save_json(tmp_file, data)
        try:
            self._read_json(tmp_file)
        except json.decoder.JSONDecodeError:
            return False
        os.replace(tmp_file, filename)
        return True

    def load_json(self, filename, default=None):
        try:
            return self._read_json(filename)
        except BaseException:
            return default

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
            self.prefix_print(
                f"Loading language: {language}",
                prefix="gettext")
            _language = gettext.translation(
                'base', 'locale', languages=[language])
            _language.install()
            self.langs[language] = _language
            return True
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            self.prefix_print(
                f"Failed to load language: {e}",
                prefix="gettext",
                prefix_colour="light red")
            return False

    def regex_text(self, _string, dlist, return_string=False):
        normalized_name = rockutils.normalize(_string.lower())
        stripped_name = re.sub(r'\s+', '', normalized_name)
        bare_name = re.sub(r"[^0-9a-zA-Z]+", '', stripped_name)
        rlist = []
        for dom in dlist:
            rlist.append(dom)
            rlist.append(re.sub(r"[^0-9a-zA-Z]+", '', dom))
        for dom in rlist:
            if dom in stripped_name or dom in normalized_name or dom in _string or dom in bare_name:
                if return_string:
                    return True, dom
                else:
                    return True
        if return_string:
            return False, ""
        else:
            return False

    def _(self, text, lang=None):
        if isinstance(lang, commands.Context) and hasattr(lang, "userinfo"):
            pass
        if isinstance(lang, dict):
            try:
                lang = lang['g']['b']['l']
            except BaseException:
                pass

        if isinstance(lang, str) and lang not in self.langs:
            self.add_lang(lang)

        if lang not in self.langs:
            return text
        else:
            return self.langs[lang].gettext(text)

    async def logcsv(self, data, file_name, directory="logs"):
        # print(data, file_name, directory)
        # try:
        #     async with aiofile(os.path.join(directory, file_name), mode="a+") as file:
        #         _sio = io.StringIO()
        #         csv.writer(_sio).writerow(data)
        #         _sio.seek(0)
        #         await file.write(_sio.read())
        #         await file.fsync()
        #     return True
        # except Exception as e:
        #     exc_info = sys.exc_info()
        #     traceback.print_exception(*exc_info)
        #     self.prefix_print(
        #         f"Failed to log csv: {e}",
        #         prefix="logcsv",
        #         prefix_colour="light red")
        #     return False
        return True

    def randstr(self):
        return base64.b64encode(
            bytes(str(time.time() * 100000),
                  "ascii")).decode().replace(
            "=", "").lower()

    def create_poll_embed(self, pollinfo):
        options_chosen = {}
        total_votes = 0

        for i in range(len(pollinfo['o'])):
            options_chosen[i] = 0

        usersvoted = []
        for user, vote in pollinfo.items():
            if user not in usersvoted:
                usersvoted.append(user)
                if vote in options_chosen:
                    options_chosen[vote] += 1
                    total_votes += 1

        max_value = max(options_chosen.values())

        embed = discord.Embed(
            colour=3553599,
            description=f"**__POLL__**\nReact to this message with a number such as :zero: to vote\n\nTotal Votes: **{total_votes}**",
            timestamp=datetime.datetime.utcfromtimestamp(
                time.time()))
        for option_value, option in enumerate(pollinfo['o']):
            voted_for = options_chosen[option_value]

            char_length = 10
            length = round(
                ((voted_for * (100 / max_value)) / 100) * char_length)
            percent = round((voted_for / total_votes) * 1000)

            embed.add_field(
                name=f"**{option_value}**) {'█'*length}",
                value=f"{option}\n**{voted_for}** votes - (**{percent}%**)")
        embed.set_footer(text=f"Poll id: {pollinfo['id']}")

        return embed


rockutils = RockUtils()


class GameRetriever():

    def __init__(self, rockutils):
        self.http_cache = {}
        self.rockutils = rockutils

        self.config = self.rockutils.load_json("cfg/config.json")
        self.youtube_key = self.config['keys']['youtube']

    async def retrieve_url(self, url, retrieval="json", cache_time=30):
        _time = time.time()
        _dkeys = []
        for _key, _value in self.http_cache.items():
            if _time >= _value['time']:
                _dkeys.append(_key)
        for _key in _dkeys:
            del self.http_cache[_key]

        _url_signature = hashlib.sha256(url.encode("utf8")).hexdigest()[-16:]
        if _url_signature in self.http_cache and "handler" in self.http_cache[_url_signature]:
            print("Using cached data")
            return self.http_cache[_url_signature]['handler']

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if retrieval == "json":
                    try:
                        resp = await response.json()
                    except Exception as e:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)
                        resp = e
                else:
                    resp = await response.text()

                self.http_cache[_url_signature] = {
                    "handler": resp,
                    "time": _time + cache_time
                }
                return self.http_cache[_url_signature]['handler']

    async def youtube(self, channel_id):
        try:
            url = f"https://www.googleapis.com/youtube/v3/channels?part=statistics&id={channel_id}&key={self.youtube_key}&alt=json"
            payload = await self.retrieve_url(url, retrieval="json", cache_time=30)

            if payload['pageInfo']['totalResults'] > 0:
                return True, payload['items'][0]
        except Exception:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return False, None

    async def twitter(self, display_name):
        response = await self.retrieve_url(f"https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={display_name}")
        if isinstance(response, aiohttp.client_exceptions.ContentTypeError):
            return False, {}

        if len(response) > 0:
            return True, response[0]
        else:
            return False, response

    async def steam_group(self, group_id):
        response = await self.retrieve_url(f"https://steamcommunity.com/groups/{group_id}", retrieval="text")
        data = {}
        info = re.findall('count ">[0-9,]+</div>', response)
        if len(info) == 0:
            data['ingame'] = 0
            data['online'] = 0
            data['members'] = 0
            data['display'] = "-"
            return False, data
        else:
            data['ingame'] = info[0][8:-6]
            data['online'] = info[1][8:-6]
            data['members'] = re.findall(
                'count">[0-9,]+</span>', response)[0][7:-7]
            data['display'] = re.findall(
                'grouppage_header_abbrev" >.+</span>', response)[0][26:-7]
            return True, data

    async def factorio(self, game_id):
        response = await self.retrieve_url(f"https://multiplayer.factorio.com/get-game-details/{game_id}")
        if isinstance(response, aiohttp.client_exceptions.ContentTypeError):
            return False, {}

        if "no game" in response.get("message", ""):
            return False, response
        return True, response

    # async def a2s(self, ip):
    #     _split = ip.split(":")
    #     try:
    #         _split[1] = int(_split[1])
    #     except BaseException:
    #         exc_info = sys.exc_info()
    #         traceback.print_exception(*exc_info)
    #         return False, None

    #     if len(_split) == 2:
    #         server = valve.source.a2s.ServerQuerier(_split, timeout=1)
    #         _query = functools.partial(server.info)
    #         _values = await self.bot.loop.run_in_executor(None, _query)

    #         try:
    #             return True, _values.values
    #         except BaseException:
    #             return False, None
    #     else:
    #         return False, None

    # async def minecraft(self, ip):
    #     try:
    #         server = mcstatus.MinecraftServer.lookup(ip)
    #         return True, server.status()
    #     except BaseException:
    #         exc_info = sys.exc_info()
    #         traceback.print_exception(*exc_info)
    #         return False, None

    async def checkip(self, ip):
        response = await self.retrieve_url(f"https://check.getipintel.net/check.php?ip={ip}&contact=[removed]", retrieval="text", cache_time=600)
        try:
            a = float(response)
            if a >= 0:
                return True, a
            else:
                return False, 0
        except BaseException:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return False, 0


class CustomChecks():

    def requires_guild(self, return_predicate=False, return_message=True):
        async def _predicate(ctx):
            if not (hasattr(ctx, "guild") and ctx.guild is not None):
                if return_message:
                    message = rockutils._(
                        "This command can only be ran in a server", ctx)

                    try:
                        await ctx.send(f"{ctx.bot.get_emote('alert')}  | " + message)
                    except BaseException:
                        pass
                return False
            return True
        if return_predicate:
            return _predicate
        else:
            return commands.check(_predicate)

    def requires_membership(
            self,
            donation=True,
            partner=True,
            return_predicate=False,
            return_message=True):
        async def _predicate(ctx):
            can_donate = await ctx.bot.has_guild_donated(ctx.guild, ctx.guildinfo, donation, partner)
            has_bot_elevation = await ctx.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True)
            if not can_donate and not has_bot_elevation:
                if return_message:
                    message = rockutils._(
                        "This command is for donators only. Do {command} to find out more",
                        ctx).format(
                        command="+membership")

                    try:
                        await ctx.send(f"{ctx.bot.get_emote('alert')}  | " + message)
                    except BaseException:
                        pass
            return has_bot_elevation or can_donate
        if return_predicate:
            return _predicate
        else:
            return commands.check(_predicate)

    def requires_special_elevation(
            self,
            support=False,
            developer=False,
            admin=False,
            trusted=False,
            return_predicate=False,
            return_message=True):
        async def _predicate(ctx):
            has_bot_elevation = await ctx.bot.has_special_permission(ctx.author, support, developer, admin, trusted)
            if not has_bot_elevation:
                if return_message:
                    message = rockutils._(
                        "You do not have permission to use this command", ctx)

                    try:
                        await ctx.send(f"{ctx.bot.get_emote('alert')}  | " + message)
                    except BaseException:
                        pass
            return has_bot_elevation
        if return_predicate:
            return _predicate
        else:
            return commands.check(_predicate)

    def requires_elevation(
            self,
            staffbypass=True,
            return_predicate=False,
            return_message=True):
        async def _predicate(ctx):
            elevated = await ctx.bot.has_elevation(ctx.guild, ctx.guildinfo, ctx.author)
            if not elevated and staffbypass:
                has_bot_elevation = await ctx.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True)
                if has_bot_elevation:
                    return True

            if not elevated:
                if return_message:
                    message = rockutils._(
                        "You do not have permission to use this command", ctx)

                    try:
                        await ctx.send(f"{ctx.bot.get_emote('alert')}  | " + message)
                    except BaseException:
                        pass
            return elevated
        if return_predicate:
            return _predicate
        else:
            return commands.check(_predicate)

    def requires_permission(
            self,
            permissions=[],
            return_predicate=False,
            return_message=True):
        async def _predicate(ctx):
            _permissions = list(map(lambda v: v.upper(), permissions))
            bot_permissions = await ctx.bot.has_permission_node(target=ctx.guild.me, return_has=True)

            for permission in bot_permissions:
                if permission == "ADMINISTRATOR":
                    return True
                if permission in bot_permissions:
                    return True

            if return_message:
                message = rockutils._(
                    "The bot is unable to run this command as it is missing permissions: `{permissions}`",
                    ctx).format(
                        permissions=",".join(_permissions))

                try:
                    await ctx.send(f"{ctx.bot.get_emote('alert')}  | " + message)
                except BaseException:
                    pass

            return False
        if return_predicate:
            return _predicate
        else:
            return commands.check(_predicate)

    # @customchecks.requires_special_elevation(developer=True)
    # @commands.bot_has_permissions(manage_messages=True)


gameretriever = GameRetriever(rockutils)
customchecks = CustomChecks()
