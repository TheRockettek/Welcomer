import asyncio
import copy
import csv
import io
import math
from math import inf
import os
import sys
import time
import traceback
import logging
from importlib import reload
from datetime import datetime
import logging

import aiohttp
import discord
import requests
import json
import ujson
from discord.ext import commands
from rockutils import rockutils
import uuid
import handling


def canint(val):
    try:
        int(val)
        return True
    except BaseException:
        return False


class NoPermission(Exception):
    pass


class NoDonator(Exception):
    pass


class WelcomerCore(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def maketimestamp(
            self,
            timestamp=0,
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
        if not timestamp:
            timestamp = 0
        _y, _d, _h, _m, _s = rockutils.parse_unix(
            datetime.utcnow().timestamp() - timestamp)

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

    async def get_value(self, table, key, default=None):
        # print("FETCH", table, key)

        async with self.bot.connection.acquire() as connection:
            value = await connection.fetchrow(
                f"SELECT * FROM {table} WHERE id = $1",
                key
            )

        if value:
            print("FETCH", table, key, "OK")

            try:
                return ujson.loads(value["value"])
            except ValueError:
                return json.loads(value["value"])
        else:
            print("FETCH", table, key, "FAIL")
            return default

    async def set_value(self, table, key, value):
        if key is None:
            key = str(uuid.uuid4())

        print("SET", table, key)

        try:
            async with self.bot.connection.acquire() as connection:
                await connection.execute(
                    f"INSERT INTO {table}(id, value) VALUES($1, $2) ON CONFLICT (id) DO UPDATE SET value = $2",
                    key, ujson.dumps(value)
                )
        except Exception as e:
            print("Failed to set value", table, ":", key, e)
            # return False
        else:
            # return True
            return {
                "generated_keys": [key],
                "inserted": 1
            }

    async def get_guild_info(self, id, refer="", reload_data=True, create_cache=True, direct=False, request_invites=True):
        # rockutils.prefix_print(
        #     f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for G:{id}",
        #     prefix="Guild Info:Get",
        #     prefix_colour="light green")

        guild_info = await self.get_value("guilds", str(id))
        # guild_info = await r.table("guilds").get(str(id)).run(self.bot.connection)

        if not direct:
            new_data = True if not isinstance(
                guild_info, dict) else not bool(guild_info)
            has_updated = True if new_data else False

            guild = self.bot.get_guild(int(id))
            _guild_info = self.bot.serialiser.guild(guild)
            _time = time.time()

            default_data = copy.deepcopy(self.bot.default_guild)

            latest_version = default_data['d']['dv']

            if new_data and guild:
                # try:
                #     old_info = await r.db("welcomer5").table("guilds").get(str(id)).run(self.bot.connection)
                #     if old_info:
                #         default_data['a']['e'] = old_info['analytics']['enabled']

                #         default_data['ar']['e'] = old_info['autorole']['enabled']
                #         default_data['ar']['r'] = list(
                #             map(str, old_info['autorole']['role_ids']))

                #         for donation in old_info['donations']:
                #             default_data['d']['de'].append(donation['id'])
                #             default_data['d']['b']['hb'] = True

                #         default_data['l']['e'] = old_info['leaver']['enabled']
                #         if isinstance(old_info['leaver']['channel'], str):
                #             default_data['l']['c'] = old_info['leaver']['channel']
                #         default_data['l']['t'] = old_info['leaver']['text']

                #         if "prefix" in old_info:
                #             default_data['d']['b']['p'] = old_info['prefix']

                #         default_data['r']['e'] = old_info['rules']['enabled']
                #         default_data['r']['r'] = old_info['rules']['rules']

                #         default_data['d']['b']['ai'] = old_info['settings']['allow_invite']
                #         default_data['d']['b']['d'] = old_info['settings']['description']
                #         default_data['d']['b']['ss'] = old_info['settings']['show_staff']

                #         default_data['st']['ap'] = old_info['staff']['allow_ping']
                #         for staff_id, allow_ping in old_info['staff']['staff_ids'].items():
                #             default_data['st']['u'].append(
                #                 [staff_id, allow_ping])

                #         # for channel_id, stat in old_info['stats']['channels']:
                #         #     stats = {}
                #         #     stats['c'] = channel_id
                #         #     stats['t'] = stat['type']
                #         #     stats['t'] = stat['text']
                #         #     default_data['s']['c'].append(stat)

                #         default_data['s']['c'] = old_info['stats']['channels']
                #         if isinstance(old_info['stats']['enabled'], str):
                #             default_data['s']['e'] = old_info['stats']['enabled']
                #         default_data['s']['ca'] = old_info['stats']['category']

                #         default_data['tc']['e'] = old_info['tempchannels']['enabled']
                #         if isinstance(old_info['tempchannels']['category'], str):
                #             default_data['tc']['c'] = old_info['tempchannels']['category']
                #         default_data['tc']['ap'] = old_info['tempchannels']['autopurge']

                #         if isinstance(old_info['welcomer']['channel'], str):
                #             default_data['w']['c'] = old_info['welcomer']['channel']
                #         default_data['w']['e'] = old_info['welcomer']['enable_embed']
                #         default_data['w']['b'] = old_info['welcomer']['text']['badges']
                #         default_data['w']['iv'] = old_info['welcomer']['text']['invited']
                #         default_data['w']['i']['e'] = old_info['welcomer']['images']['enabled']
                #         default_data['w']['i']['bg'] = old_info['welcomer']['images']['background']
                #         # default_data['w']['i']['c']['bo'] = old_info['welcomer']['images']['colour']['border']
                #         # default_data['w']['i']['c']['b'] = old_info['welcomer']['images']['colour']['text']
                #         # default_data['w']['i']['c']['pb'] = old_info['welcomer']['images']['colour']['profile']
                #         default_data['w']['i']['m'] = old_info['welcomer']['images']['message']
                #         default_data['w']['t']['e'] = old_info['welcomer']['text']['enabled']
                #         default_data['w']['t']['m'] = old_info['welcomer']['text']['message']
                #         default_data['w']['dm']['e'] = old_info['welcomer']['dm']['enabled']
                #         default_data['w']['dm']['m'] = old_info['welcomer']['text']['message']

                #         if "namepurge" in old_info['welcomer']:
                #             default_data['np']['e'] = old_info['welcomer']['namepurge']['enabled']
                #             default_data['np']['f'] = list(map(lambda o: o.replace(
                #                 "\n", ""), old_info['welcomer']['namepurge']['filter']))
                # except BaseException:
                #     exc_info = sys.exc_info()
                #     traceback.print_exception(*exc_info)

                guild_info = default_data

            origional_guild_info = copy.deepcopy(guild_info)

            guild_info['d']['b']['c'] = self.bot.cluster_id
            guild_info['id'] = str(id)

            if self.bot.donator:
                guild_info['d']['b']['hd'] = True
            elif guild:
                if not guild.get_member(498519480985583636):
                    guild_info['d']['b']['hd'] = False

            if guild:
                if new_data:
                    guild_info['d']['g']['ga'] = math.ceil(_time)
                    guild_info['d']['g']['gc'] = math.ceil(
                        guild.created_at.timestamp())

                    if request_invites:
                        try:
                            guild_info['d']['i'] = await self.bot.serialiser.invites(guild)
                        except BaseException:
                            pass

                guild_info['d']['g']['i'] = _guild_info['icons']
                guild_info['d']['g']['ic'] = _guild_info['icon']
                guild_info['d']['g']['n'] = _guild_info['name']
                guild_info['d']['b']['r'] = _guild_info['region']
                guild_info['d']['b']['sh'] = guild.shard_id

                if guild.owner or guild.owner_id:
                    try:
                        owner_id = guild.owner.id
                    except:
                        owner_id = guild.owner_id
                    user = self.bot.get_user(owner_id)
                    if user:
                        guild_info['d']['g']['o'] = self.bot.serialiser.user(
                            user)

                    if _time - guild_info['d']['m']['u'] > 600:
                        guild_info['d']['m'] = {
                            "b": _guild_info['bots'],
                            "m": _guild_info['users'] - _guild_info['bots'],
                            "a": _guild_info['users'],
                            "u": _time
                        }

                    # if _time - guild_info['d']['d']['u'] > 600:
                    #     _guild_detailed = self.bot.serialiser.guild_detailed(
                    #         guild)
                    #     guild_info['d']['d'] = {
                    #         "s": _guild_detailed['streaming'],
                    #         "o": _guild_detailed['online'],
                    #         "i": _guild_detailed['idle'],
                    #         "d": _guild_detailed['dnd'],
                    #         "of": _guild_detailed['offline'],
                    #         "u": _time
                    #     }

                    if _time - guild_info['d']['c']['u'] > 600:
                        _channels = self.bot.serialiser.channels(guild)
                        guild_info['d']['c'] = {
                            "c": _channels['categories'],
                            "v": _channels['voice'],
                            "t": _channels['text'],
                            "u": _time
                        }

                    if "r" not in guild_info['d'] or (
                            _time - guild_info['d']['r']['u'] > 600):
                        _roles = self.bot.serialiser.roles(guild)
                        guild_info['d']['r'] = {
                            "r": _roles,
                            "u": _time
                        }

            has_updated = True if guild_info != origional_guild_info else has_updated

            if latest_version != guild_info['d']['dv']:
                default_data.update(guild_info)
                guild_info = default_data
                _version = guild_info['d']['dv']

                if _version == 0:
                    # example hardcoded data overwrite
                    pass

                if "sw" not in guild_info['d']['b']:
                    guild_info['d']['b']['sw'] = True

                guild_info['d']['dv'] = default_data['d']['dv']
                has_updated = True

            if not isinstance(guild_info['s']['c'], list):
                print("Emptying channel list")
                guild_info['s']['c'] = []

            def normalize_colour(string):
                if string.startswith("RGBA|"):
                    return string
                elif string.startswith("RGB|"):
                    return string
                else:
                    try:
                        _hex = str(hex(int(string)))[2:]
                        if len(_hex) >= 8:
                            return f"RGBA|{str(hex(string))[:8]}"
                        elif len(_hex) >= 6:
                            return f"RGB|{str(hex(string))[:6]}"
                    except BaseException:
                        pass
                    return f"RGB|FFFFFF"

            keys = ['w.i.c.b', 'w.i.c.b', 'w.i.c.pb', 'w.i.c.ib']
            for key in keys:
                value = rockutils.getvalue(key, guild_info)
                value = str(value)
                if not value.startswith("R"):
                    newvalue = normalize_colour(value)
                    rockutils.setvalue(key, guild_info, newvalue)

            # print("create cache", create_cache)
            if create_cache:
                guild = self.bot.get_guild(int(id))
                if guild:
                    await self.create_guild_cache(guild_info, guild, force=True)
                else:
                    rockutils.prefix_print(
                        f"Wanted to make cache for {id} but no guild object", prefix="createcache", prefix_colour="red", text_colour="light red")
            create_cache = False

            if has_updated or new_data:
                if new_data:
                    # rockutils.prefix_print(
                    #     f"{f'[Refer: {refer}] ' if refer != '' else ''}Creating information for G:{id}",
                    #     prefix="Guild Info:Get",
                    #     prefix_colour="light green")

                    # await r.table("guilds").insert(guild_info).run(self.bot.connection)
                    await self.set_value("guilds", guild_info["id"], guild_info)
                else:
                    await self.update_guild_info(id, guild_info, refer="getguildinfo:" + (refer or "?"))

        # print("create cache", create_cache)
        if create_cache:
            guild = self.bot.get_guild(int(id))
            if guild:
                await self.create_guild_cache(guild_info, guild, force=True)
            else:
                rockutils.prefix_print(
                    f"Wanted to make cache for {id} but no guild object", prefix="createcache", prefix_colour="red", text_colour="light red")

        return guild_info

    async def update_info(self, ctx, data):
        guilddata = copy.copy(ctx.guildinfo)
        if data:
            if isinstance(data[0], list):
                for key, value in data:
                    if rockutils.hasvalue(key, guilddata):
                        rockutils.setvalue(key, guilddata, value)
                    else:
                        rockutils.prefix_print(
                            f"Could not find key {key} in guildinfo",
                            prefix="Update Info",
                            prefix_colour="red",
                            text_colour="light red")
            else:
                # Table not nested (only one key value pair)
                key, value = data[0], data[1]
                if rockutils.hasvalue(key, guilddata):
                    rockutils.setvalue(key, guilddata, value)
                else:
                    rockutils.prefix_print(
                        f"Could not find key {key} in guildinfo",
                        prefix="Update Info",
                        prefix_colour="red",
                        text_colour="light red")

        await self.bot.create_guild_cache(guilddata, guild=ctx.guild, force=True)
        return await self.update_guild_info(ctx.guild.id, guilddata, refer="updateinfo")

    async def update_info_key(self, guildinfo, data, refer=""):
        if isinstance(guildinfo, int):
            guildinfo = await self.bot.get_guild_info(guildinfo, refer=f"Update Info Key:{refer}")

        if len(data) > 0:
            if isinstance(data[0], list):
                # print(list(map(lambda o: o[0], data)))
                for key, value in data:
                    if rockutils.hasvalue(key, guildinfo):
                        rockutils.setvalue(key, guildinfo, value)
                    else:
                        rockutils.prefix_print(
                            f"Could not find key {key} in guildinfo",
                            prefix="Update Info",
                            prefix_colour="red",
                            text_colour="light red")
            else:
                # print(data[0])
                # Table not nested (only one key value pair)
                key, value = data[0], data[1]
                if rockutils.hasvalue(key, guildinfo):
                    rockutils.setvalue(key, guildinfo, value)
                else:
                    rockutils.prefix_print(
                        f"Could not find key {key} in guildinfo",
                        prefix="Update Info",
                        prefix_colour="red",
                        text_colour="light red")

        guild = self.bot.get_guild(int(guildinfo['id']))
        await self.bot.create_guild_cache(guildinfo, guild=guild, force=True)
        return await self.update_guild_info(guildinfo['id'], guildinfo, refer=f"Update Info Key:{refer}")

    async def update_guild_info(self, id, data, forceupdate=False, refer=""):
        try:
            # rockutils.prefix_print(
            #     f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for G:{id}",
            #     prefix="Guild Info:Update",
            #     prefix_colour="light green")
            t = time.time()

            res = await self.set_value("guilds", str(id), data)
            # if forceupdate:
            #     res = await r.table("guilds").get(str(id)).update(data).run(self.bot.connection)
            # else:
            #     res = await r.table("guilds").get(str(id)).replace(data).run(self.bot.connection)

            te = time.time()
            if te - t > 1:
                rockutils.prefix_print(
                    f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating guild info took {math.floor((te-t)*1000)}ms",
                    prefix="Guild Info:Update",
                    prefix_colour="red",
                    text_colour="light red")
            return res
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            rockutils.prefix_print(
                f"{f'[Refer: {refer}] ' if refer != '' else ''}Error occured whilst updating info for G:{id}. {e}",
                prefix="Guild Info:Update",
                prefix_colour="red",
                text_colour="light red")
            return False

    async def get_user_info(self, id, refer="", reload_data=True, direct=False):
        # rockutils.prefix_print(
        # f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for U:{id}",
        # prefix="User Info:Get",
        # prefix_colour="light green")

        # user_info = await r.table("users").get(str(id)).run(self.bot.connection)
        user_info = await self.get_value("users", str(id))

        if not direct:
            new_data = True if not isinstance(
                user_info, dict) else not bool(user_info)
            has_updated = True if new_data else False

            user = self.bot.get_user(int(id))
            _user_info = self.bot.serialiser.user(user)
            _time = time.time()

            default_data = copy.deepcopy(self.bot.default_user)

            latest_version = default_data['g']['dv']

            if new_data and user:
                #     try:
                #         old_info = await r.db("welcomer5").table("guilds").get(str(id)).run(self.bot.connection)
                #         if old_info:
                #             if (old_info['membership']['exte'] or
                #                     old_info['membership']['plus'] or
                #                     old_info['membership']['pro']):
                #                 default_data['m']['5']['h'] = True
                #             default_data['m']['5']['p'] = (old_info['membership']['exte_patr'] or
                #                                            old_info['membership']['plus_patr'] or
                #                                            old_info['membership']['pro_patr'])
                #             default_data['m']['5']['u'] = max(
                #                 old_info['membership']['exte_since'],
                #                 old_info['membership']['plus_since'],
                #                 old_info['membership']['pro_since']) + 2592000
                #             default_data['m']['p'] = old_info['membership']['partner']
                #             default_data['m']['s'] = list(
                #                 map(lambda o: o['id'], old_info['membership']['servers']))
                #             default_data['r']['r'] = old_info['reputation']
                #             default_data['r']['l'] = old_info['last_reputation']
                #             default_data['g']['b']['pd'] = old_info['prefer_dms']
                #     except BaseException:
                #         exc_info = sys.exc_info()
                #         traceback.print_exception(*exc_info)

                user_info = default_data

            origional_user_info = copy.deepcopy(user_info)

            user_info['id'] = str(id)

            if user:
                if new_data:
                    user_info['g']['g']['ua'] = math.ceil(_time)
                    user_info['g']['g']['uc'] = math.ceil(
                        user.created_at.timestamp())
                if "avatar" in _user_info:
                    user_info['g']['g']['a'] = _user_info['avatar']
                user_info['g']['g']['n'] = _user_info['name']
                user_info['g']['g']['d'] = _user_info['discriminator']
                user_info['g']['g']['u'] = _time

                # if _time - user_info['g']['g']['m']['u'].get(
                #         self.bot.cluster_id, 0) > 900 and not user.bot:
                #     user_info['g']['g']['m']['c'][
                #         self.bot.cluster_id] = self.bot.serialiser.mutualguilds(user)
                #     user_info['g']['g']['m']['u'][self.bot.cluster_id] = _time

                expired = []
                renewed = []
                changes = []
                for membership_type, v in user_info['m'].items():
                    if isinstance(v, dict):
                        # print(_time, user_info['m'][membership_type]['u'])
                        # print(user_info['m'][membership_type]['u'])
                        if user_info['m'][membership_type]['h'] and user_info['m'][membership_type]['u'] and ((_time > user_info['m'][membership_type]['u'])):
                            user_info['m'][membership_type]['h'] = False
                            if user_info['m'][membership_type]['p']:
                                user_info['m'][membership_type]['h'] = True
                                user_info['m'][membership_type]['u'] = _time + 2592000
                                renewed.append("Welcomer x" + membership_type)
                            else:
                                expired.append("Welcomer x" + membership_type)

                if len(expired) > 0 or len(renewed) > 0:
                    url = "https://[removed]"
                    await rockutils.send_webhook(url, f"User: `{id}` <@{id}> membership expired. Expired: `{expired}` Renewed: `{renewed}`")

                    message = rockutils._(
                        "Some of your memberships have expired and may have renewed if you have paid using patreon.\n\n__Expired memberships:__**\n{expired}**\n__Renewed memberships:__\n**{renewed}**\n\nYou are able to renew memberships automatically by donating with patreon. Find out more at **{url}**",
                        user_info).format(
                        expired=", ".join(expired),
                        renewed=", ".join(renewed),
                        url="https://welcomer.gg/donate")
                    try:
                        await user.send(message)
                    except BaseException:
                        pass

                if not user.bot:
                    user_info['b'] = sorted(
                        self.bot.serialiser.badges(
                            user, user_info), key=lambda o: o[0])

            has_updated = True if user_info != origional_user_info else has_updated

            if latest_version != user_info['g']['dv']:
                user_info = default_data.update(user_info)
                _version = user_info['g']['dv']

                if _version == 0:
                    # example hardcoded data overwrite
                    pass

                user_info['g']['dv'] = default_data['g']['dv']
                has_updated = True

            if has_updated or new_data:
                if new_data:
                    rockutils.prefix_print(
                        f"{f'[Refer: {refer}] ' if refer != '' else ''}Creating information for G:{id}",
                        prefix="User Info:Get",
                        prefix_colour="light green")
                    # await r.table("users").insert(user_info).run(self.bot.connection)
                    await self.set_value("users", user_info["id"], user_info)
                else:
                    await self.update_user_info(id, user_info)

        return user_info

    async def update_user_info(self, id, data, forceupdate=False, refer=""):
        try:
            # rockutils.prefix_print(
            # f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for U:{id}",
            # prefix="User Info:Update",
            # prefix_colour="light green")
            t = time.time()

            await self.set_value("users", str(id), data)
            # if forceupdate:
            #     await r.table("users").get(str(id)).update(data).run(self.bot.connection)
            # else:
            #     await r.table("users").get(str(id)).replace(data).run(self.bot.connection)
            te = time.time()
            if te - t > 1:
                rockutils.prefix_print(
                    f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating guild info took {math.floor((te-t)*1000)}ms",
                    prefix="User Info:Update",
                    prefix_colour="red",
                    text_colour="light red")
            return True
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            rockutils.prefix_print(
                f"Error occured whilst updating info for U:{id}. {e}",
                prefix="User Info:Update",
                prefix_colour="red",
                text_colour="light red")
            return False

    @ commands.Cog.listener()
    async def on_shard_connect(self, shard_id):
        await self.push_ipc({"o": "SHARD_UPDATE", "d": [0, shard_id]})

    @ commands.Cog.listener()
    async def on_shard_ready(self, shard_id):
        await self.push_ipc({"o": "SHARD_UPDATE", "d": [1, shard_id]})

    @ commands.Cog.listener()
    async def on_shard_resumed(self, shard_id):
        await self.push_ipc({"o": "SHARD_UPDATE", "d": [4, shard_id]})

    @ commands.Cog.listener()
    async def on_connect(self):
        if self.bot.ranonconnect:
            return
        self.bot.ranonconnect = True

        rockutils.prefix_print("Bot is now connecting", prefix_colour="green")
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 0})

        game = discord.Game("Getting Ready...")
        await self.bot.change_presence(status=discord.Status.idle, activity=game)

    @ commands.Cog.listener()
    async def on_ready(self):
        rockutils.prefix_print("Bot is fully ready", prefix_colour="green")
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 1})

        game = discord.Game("welcomer.gg | +help")
        await self.bot.change_presence(status=discord.Status.online, activity=game)

    @ commands.Cog.listener()
    async def on_resume(self):
        rockutils.prefix_print("Bot is now resuming", prefix_colour="green")
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 4})

    async def sync_task(self):
        # ws = self.bot.ipc_ws
        rockutils.prefix_print("Starting sync task", prefix="Sync Task")
        while True:
            try:
                await self.sync_handle()
            except asyncio.CancelledError:
                raise asyncio.CancelledError
            except Exception as e:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                rockutils.prefix_print(
                    f"{type(e)} {str(e)}",
                    prefix="Sync Task",
                    prefix_colour="light red",
                    text_colour="red")
            await asyncio.sleep(1)

    async def sync_receiver(self):
        ws = self.bot.ipc_ws
        rockutils.prefix_print("Yielding sync receiver", prefix="Sync Handler")
        while not self.bot.is_ready():
            await asyncio.sleep(1)
        rockutils.prefix_print("Starting sync receiver", prefix="Sync Handler")
        while True:
            try:
                print("Waiting for json")
                jobs = await ws.receive_json(loads=ujson.loads)
            except ValueError:
                pass
            except asyncio.CancelledError:
                raise asyncio.CancelledError
            else:
                if len(jobs) > 0:
                    try:
                        f = open("handling.py", "r")
                        file_content = f.read()
                        f.close()
                        compile(file_content + "\n", "handling.py", "exec")
                    except Exception as e:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)
                        rockutils.prefix_print(
                            f"Could not update handling: {str(e)}",
                            prefix="Sync Handler",
                            prefix_colour="light red",
                            text_colour="red")

                for job in jobs:
                    print(f"Running job {job} in task")
                    self.bot.loop.create_task(self.process_job(job))

    async def process_job(self, job):
        try:
            opcode = job['o'].lower()
            try:
                args = ujson.loads(job['a'])
            except BaseException:
                args = job['a']
            key = job['k']

            if canint(args):
                args = int(args)

            if hasattr(handling, opcode):
                try:
                    result = await asyncio.wait_for(getattr(handling, opcode)(self, opcode, args), timeout=60)
                except Exception as e:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
                    result = result = {
                        "success": False, "error": "Exception",
                        "exception": str(type(e))}
                    rockutils.prefix_print(
                        f"Could not process job. {opcode}:{args}. {str(e)}",
                        prefix="Sync Handler",
                        prefix_colour="light red",
                        text_colour="red")
            else:
                result = {
                    "success": False, "error": "InvalidOPCode"}

            _payload = {
                "o": "SUBMIT",
                "k": key,
                "r": self.bot.cluster_id,
                "d": result
            }

            domain = f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/ipc_submit/{self.bot.cluster_id}/{self.bot.config['ipc']['auth_key']}"
            async with aiohttp.ClientSession() as _session:
                await _session.post(domain, json=_payload)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            rockutils.prefix_print(
                f"Could not process jobs: {str(e)}",
                prefix="Sync Handler",
                prefix_colour="light red",
                text_colour="red")

    async def sync_send(self, _payload):
        try:
            _payload['o'] = _payload['o'].upper()
            await self.bot.ipc_ws.send_json(_payload, dumps=ujson.dumps)
        except asyncio.CancelledError:
            raise asyncio.CancelledError
        except OverflowError:
            # If we have overflowed in a ping, and more than half the
            # shards are broken, kill the bot.
            if _payload["o"] == "SUBMIT" and "ping" in _payload["k"]:
                total = round(len(_payload["d"]["latencies"])/2)
                tinf = 0
                for i in _payload["d"]["latencies"]:
                    if i[1] == inf:
                        tinf += 1
                if tinf >= total:
                    self.bot.logout()
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            rockutils.prefix_print(
                f"Could not send payload. {_payload}. {str(e)}",
                prefix="Sync Handler",
                prefix_colour="light red",
                text_colour="red")

    async def sync_handle(self):
        rockutils.prefix_print("Starting sync handler", prefix="Sync Handler")
        try:
            domain = f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/ipc/{self.bot.cluster_id}/{self.bot.config['ipc']['auth_key']}"
            rockutils.prefix_print(f"Connecting to WS via {domain}")
            session = aiohttp.ClientSession()
            self.bot.ipc_ws = await session.ws_connect(domain)

            rockutils.prefix_print(
                "Connected to websocket",
                prefix="Sync Handler")
            self.bot.sync_receiver_task = self.bot.loop.create_task(
                self.sync_receiver())

            while True:
                await asyncio.sleep(1)
                if self.bot.sync_receiver_task.done():
                    rockutils.prefix_print(
                        "Closing sync", prefix="Sync Handler", text_colour="red")

                    try:
                        self.bot.sync_receiver_task.cancel()
                    except asyncio.CancelledError:
                        raise asyncio.CancelledError
                    except BaseException:
                        pass

                    await session.close()
                    return

        except aiohttp.client_exceptions.ClientConnectionError:
            await session.close()
            rockutils.prefix_print(
                "Encountered connection error with IPC",
                prefix="Sync Handler",
                prefix_colour="light red",
                text_colour="red")
            await asyncio.sleep(2)
        except asyncio.CancelledError:
            raise asyncio.CancelledError
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            rockutils.prefix_print(
                f"{type(e)} {str(e)}",
                prefix="Sync Handler",
                prefix_colour="light red",
                text_colour="red")

    async def push_ipc(self, _payload):
        if _payload.get("o", "") != "":
            await self.bot.sync_send(_payload)
            return True
        else:
            return False

    async def has_guild_donated(self, guild, guild_info, donation=False,
                                partner=True):
        if guild and isinstance(guild, discord.Guild):
            _time = time.time()

            if partner:
                try:
                    owner_id = guild.owner.id
                except:
                    owner_id = guild.owner_id

                _userinfo = await self.bot.get_user_info(owner_id)
                if _userinfo and _userinfo['m']['p']:
                    return True

            for id in guild_info['d']['de']:
                id = int(id)
                try:
                    _user = self.bot.get_user(id)
                    if _user:
                        if await self.bot.has_special_permission(_user, support=True, developer=True, admin=True, trusted=True):
                            return True
                    _userinfo = await self.bot.get_user_info(id)
                    if _userinfo:
                        if donation:
                            if _userinfo['m']['1']['h'] and (
                                    _time < (_userinfo['m']['1'].get('u', 0) or 0) or
                                    _userinfo['m']['1']['p']):
                                return True
                            if _userinfo['m']['3']['h'] and (
                                    _time < (_userinfo['m']['3'].get('u', 0) or 0) or
                                    _userinfo['m']['3']['p']):
                                return True
                            if _userinfo['m']['5']['h'] and (
                                    _time < (_userinfo['m']['5'].get('u', 0) or 0) or
                                    _userinfo['m']['5']['p']):
                                return True
                except BaseException:
                    pass

        return False

    async def has_special_permission(self, user, support=False,
                                     developer=False, admin=False,
                                     trusted=False):
        _config = rockutils.load_json("cfg/config.json")

        if _config != self.bot.config:
            self.bot.config = copy.deepcopy(_config)

        if user and type(user) in [discord.User, discord.Member]:
            if support and user.id in _config['roles']['support']:
                return True

            if developer and user.id in _config['roles']['developer']:
                return True

            if admin and user.id in _config['roles']['admins']:
                return True

            if trusted and user.id in _config['roles']['trusted']:
                return True

        return False

    async def walk_help(self, ctx, group):
        message = ""
        command_list = []

        briefs = {}
        for command in group.commands:
            key = command.description.split('|')[0]
            if key not in briefs:
                briefs[key] = []
            briefs[key].append(command)

        for key, value in briefs.items():
            _sorted = sorted(value, key=lambda o: o.name)
            briefs[key] = _sorted

        for key in sorted(briefs.keys()):
            for command in briefs[key]:
                command_list.append(command)

        for command in command_list:
            sub_message = f"**{command.full_parent_name} {command.name} {command.description.split('|')[0]}** | {command.description.split('|')[1]}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, title=f"{ctx.command.name[0].upper()}{ctx.command.name[1:].lower()} usage")
                message = ""
            message += sub_message
        await self.bot.send_data(ctx, message, ctx.userinfo, title=f"{ctx.command.name[0].upper()}{ctx.command.name[1:].lower()} usage")

    async def send_user_data(self, user, message,
                             title="", footer="", raw=False):
        message_kwargs = {}
        extra = ""

        if raw:
            message_kwargs['content'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
        else:
            embed_kwargs = {}
            embed_kwargs['description'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
            embed_kwargs['timestamp'] = datetime.utcfromtimestamp(
                math.ceil(time.time()))
            if title:
                embed_kwargs['title'] = title
            embed = discord.Embed(colour=3553599, **embed_kwargs)
            embed.set_footer(text=footer)
            message_kwargs['embed'] = embed

        try:
            await user.send(**message_kwargs)
        except BaseException:
            try:
                await user.send(message[:2048])
            except BaseException:
                return

        if len(extra) > 0:
            return await self.send_user_data(user, message, title, footer, raw)

    async def send_data(self, ctx, message, userinfo={}, prefer_dms=False,
                        force_guild=False, force_dm=False, alert=True,
                        title="", footer="", raw=False):
        if force_dm and force_guild:
            force_dm, force_guild = False, False
        if userinfo.get("g"):
            use_guild = not userinfo['g']['b']['pd']
        if force_dm:
            use_guild = False
        if force_guild:
            use_guild = True
        if not getattr(ctx, "guild", False):
            use_guild = False

        message_kwargs = {}
        extra = ""

        if raw:
            message_kwargs['content'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
        else:
            embed_kwargs = {}
            embed_kwargs['description'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
            embed_kwargs['timestamp'] = datetime.utcfromtimestamp(
                math.ceil(time.time()))
            if title:
                embed_kwargs['title'] = title
            embed = discord.Embed(colour=3553599, **embed_kwargs)
            embed.set_footer(text=footer)
            message_kwargs['embed'] = embed

        if use_guild:
            try:
                await ctx.send(**message_kwargs)
            except BaseException:
                try:
                    await ctx.send(message[:2048])
                except BaseException:
                    return
        else:
            try:
                await ctx.author.send(**message_kwargs)
                if alert and getattr(ctx, "guild", False):
                    try:
                        _message = rockutils._(
                            "Help has been sent to your direct messages", ctx)
                        await ctx.send(":mailbox_with_mail:  | " + _message)
                    except BaseException:
                        pass
            except BaseException:
                try:
                    await ctx.send(**message_kwargs)
                except BaseException:
                    try:
                        await ctx.send(message[:2048])
                    except BaseException:
                        return

        if len(extra) > 0:
            return await self.send_data(ctx, extra, userinfo, prefer_dms,
                                        force_guild, force_dm, alert,
                                        title, footer, raw)

    def reload_data(self, filename, key=None):
        if not key:
            _, key = os.path.split(filename)
            key = key[:key.find(".")]

        if os.path.exists(filename):
            data = rockutils.load_json(filename)
            setattr(self.bot, key, data)
            return True, key
        else:
            return False, key

    def should_cache(self, guildinfo):
        return guildinfo['a']['e'] or len(
            guildinfo['rr']) > 0 or guildinfo['tr']['e'] or guildinfo['am'][
            'e'] or guildinfo['s']['e']

    async def create_guild_cache(self, guildinfo, guild=None, cache_filter=[],
                                 force=False):
        cached = False
        force = True
        if not guild:
            guild = await self.bot.get_guild(int(guildinfo['id']))

        _id = None
        if guild:
            _id = guild.id
        else:
            _id = int(guildinfo['id'])
        if guildinfo and _id:
            c = self.bot.cache
            # print(f"Creating cache for {_id}")

            if (_id not in c['prefix'] or force) and (
                    "prefix" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['prefix'][_id] = guildinfo['d']['b']['p']

            if (_id not in c['guilddetails'] or force) and (
                    "guilddetails" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['guilddetails'][_id] = guildinfo['d']['b']

            if (_id not in c['rules'] or force) and (
                    "rules" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['rules'][_id] = guildinfo['r']

            # if (_id not in c['channels'] or force) and (
            #         "channels" in cache_filter if len(cache_filter) > 0 else True):
            #     c['channels'][_id] = guildinfo['ch']

            # if (_id not in c['serverlock'] or force) and (
            #         "serverlock" in cache_filter if len(cache_filter) > 0 else True):
            #     c['serverlock'][_id] = guildinfo['sl']

            if (_id not in c['staff'] or force) and (
                    "staff" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['staff'][_id] = guildinfo['st']

            if (_id not in c['tempchannel'] or force) and (
                    "tempchannel" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['tempchannel'][_id] = guildinfo['tc']

            if (_id not in c['autorole'] or force) and (
                    "autorole" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['autorole'][_id] = guildinfo['ar']

            # if (_id not in c['rolereact'] or force) and (
            #         "rolereact" in cache_filter if len(cache_filter) > 0 else True):
            #     c['rolereact'][_id] = guildinfo['rr']

            if (_id not in c['leaver'] or force) and (
                    "leaver" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['leaver'][_id] = guildinfo['l']

            if (_id not in c['freerole'] or force) and (
                    "freerole" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['freerole'][_id] = guildinfo['fr']

            if (_id not in c['timeroles'] or force) and (
                    "timeroles" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['timeroles'][_id] = guildinfo['tr']

            if (_id not in c['namepurge'] or force) and (
                    "namepurge" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['namepurge'][_id] = guildinfo['np']

            if (_id not in c['welcomer'] or force) and (
                    "welcomer" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['welcomer'][_id] = guildinfo['w']

            if (_id not in c['stats'] or force) and (
                    "stats" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['stats'][_id] = guildinfo['s']

            if (_id not in c['automod'] or force) and (
                    "automod" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['automod'][_id] = guildinfo['am']

            if (_id not in c['borderwall'] or force) and (
                    "borderwall" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['borderwall'][_id] = guildinfo['bw']

            # if (_id not in c['customcommands'] or force) and (
            #         "customcommands" in cache_filter if len(cache_filter) > 0 else True):
            #     c['customcommands'][_id] = guildinfo['cc']

            # if (_id not in c['music'] or force) and (
            #         "music" in cache_filter if len(cache_filter) > 0 else True):
            #     c['music'][_id] = guildinfo['m']

            # if (_id not in c['polls'] or force) and (
            #         "polls" in cache_filter if len(cache_filter) > 0 else True):
            #     c['polls'][_id] = guildinfo['p']

            # if (_id not in c['logging'] or force) and (
            #         "logging" in cache_filter if len(cache_filter) > 0 else True):
            #     c['logging'][_id] = guildinfo['lo']

            if (_id not in c['moderation'] or force) and (
                    "moderation" in cache_filter if len(cache_filter) > 0 else True):
                self.bot.cache['moderation'][_id] = guildinfo['m']

            if (_id not in c['activepunishments'] or force) and (
                    "activepunishments" in cache_filter if len(cache_filter) > 0 else True):
                punishments = []

                if os.path.exists(f"punishments/{_id}.csv"):
                    with open(f"punishments/{_id}.csv") as csv_file:
                        csv_reader = csv.reader(csv_file)
                        for row in csv_reader:
                            if row[8].lower() == "false":
                                punishments.append({
                                    "userid": int(row[0]),
                                    "type": row[4],
                                    "endtime": int(row[6]) + int(row[7])
                                })

                self.bot.cache['activepunishments'][_id] = punishments

            # "analytics",
        else:
            print(f"Skipped cache as missing arg")

        return cached

    async def has_elevation(self, guild, guildinfo, user):
        if await self.bot.has_special_permission(user, developer=True):
            return True

        if hasattr(guild, "owner") or hasattr(guild, "owner_id"):
            try:
                owner_id = guild.owner.id
            except:
                owner_id = guild.owner_id

            if owner_id == user.id:
                return True

        if guildinfo:
            if guildinfo.get("st"):
                for staff in guildinfo['st']['u']:
                    if str(user.id) == staff[0]:
                        return True

        if guild:
            member = guild.get_member(user.id)
            if member and await self.bot.has_permission_node(member, ["manage_guild", "ban_members"]):
                return True

        return False

    async def get_prefix(self, message, return_prefixes=False):
        if message.guild:
            if message.guild.id not in self.bot.cache['prefix']:
                guild_info = await self.bot.get_guild_info(message.guild.id, refer="get_prefix")
                self.bot.cache['prefix'][
                    message.guild.id] = guild_info['d']['b']['p'] or "+"
            prefix = self.bot.cache['prefix'][message.guild.id]
        else:
            prefix = "+"

        prefix = prefix

        if type(prefix) != str:
            print(message.guild.id, "does not have string prefix!!!",
                  type(prefix), prefix)

        if return_prefixes:
            return prefix
        else:
            return commands.when_mentioned_or(prefix)(self.bot, message)

    async def has_permission_node(self, target, check_for=[], return_has=False):
        permissions = discord.Permissions.all()
        my_permissions = {}
        for key in list(
            node.upper() for node in dir(permissions) if isinstance(
                getattr(
                    permissions,
                    node),
                bool)):
            my_permissions[key] = False

        for role in target.roles:
            for node in my_permissions:
                if getattr(role.permissions, node.lower()):
                    my_permissions[node] = True

        if len(check_for) > 0:
            my_permissions = list(
                node for node,
                val in my_permissions.items() if val)
            if "ADMINISTRATOR" in my_permissions:
                return True

            for node in check_for:
                if node.upper() in my_permissions:
                    return True, my_permissions
            return False
        elif return_has:
            return list(node for node, val in my_permissions.items() if val)
        else:
            return False

    def get_emote(self, name, fallback=":grey_question:"):
        if getattr(self.bot, "emotes", None) is None:
            try:
                data = rockutils.load_json("cfg/emotes.json")
            except Exception as e:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                rockutils.prefix_print(
                    f"Failed to retrieve emotes.json: {e}",
                    prefix_colour="light red")

            if not data:
                guild = self.bot.get_guild(
                    self.bot.config['bot']['emote_server'])

                if guild:
                    emotes = self.bot.serialiser.emotes(guild)
                    if emotes[0]:
                        emotelist = {}

                        for emote in emotes:
                            emotelist[emote['name']] = emote['str']
                        rockutils.save_json("cfg/emotes.json", emotelist)
                else:
                    self.bot.blocking_broadcast(
                        "emotesdump", "*", args="", timeout=10)
                    while not os.path.exists("cfg/emotes.json"):
                        try:
                            data = rockutils.load_json("cfg/emotes.json")
                        except BaseException:
                            pass

                setattr(self.bot, "emotes", emotelist)
            else:
                setattr(self.bot, "emotes", data)

        # # sometimes will save it as a list with a table inside, precaution
        # if type(self.bot.emotes) == list:
        #     setattr(self.bot, "emotes", self.bot.emotes[0])

        return self.bot.emotes.get(name, fallback)

    async def broadcast(self, opcode, recepients, args="", timeout=10):
        payload = {
            "op": opcode,
            "args": ujson.dumps(args),
            "recep": recepients,
            "timeout": str(timeout),
        }

        domain = f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/job/{self.bot.config['ipc']['auth_key']}"
        timeout = aiohttp.ClientTimeout(total=timeout + 2)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(domain, headers=payload) as resp:
                return await resp.json()

    def blocking_broadcast(self, opcode, recepients, args="", timeout=10):
        payload = {
            "op": opcode,
            "args": ujson.dumps(args),
            "recep": recepients,
            "timeout": str(timeout),
        }

        domain = f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/job/{self.bot.config['ipc']['auth_key']}"
        timeout = timeout + 2
        with requests.post(domain, headers=payload, timeout=timeout) as resp:
            return resp.json()

    @ commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        # if isinstance(error, self.NoPermission):
        #     message = rockutils._("You do not have permission to use this command")
        # return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        # if isinstance(error, self.NoDonator):
        #     message = rockutils._("This command is for donators only. Do +membership to find out more")
        # return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if isinstance(error, discord.ext.commands.NoPrivateMessage):
            message = rockutils._(
                "This command cannot be ran in a private message", ctx)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if isinstance(error, (discord.ext.commands.UnexpectedQuoteError,
                              discord.ext.commands.InvalidEndOfQuotedStringError)):
            message = rockutils._(
                "Your message provided has an unexpected quotations and could not be executed", ctx)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if isinstance(error, discord.ext.commands.BotMissingPermissions):
            message = rockutils._(
                "The bot is unable to run this command as it is missing permissions: {permissions}",
                ctx).format(
                    permissions=",".join(map(lambda o: o.upper(), error.missing_perms)))
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
        if isinstance(error, discord.errors.Forbidden):
            return

        if isinstance(error, discord.ext.commands.CheckFailure):
            return

        _traceback = traceback.format_exception(
            type(error), error, error.__traceback__)
        _error = {
            "name": str(error),
            "type": str(type(error)),
            "tb": _traceback,
            "status": "not handled",
            "occurance": str(datetime.now()),
            "timestamp": str(time.time()),
            "version": ctx.bot.version,
            "gname": getattr(ctx.guild, "name", "Direct Message"),
            "gid": str(getattr(ctx.guild, "id", "Direct Message")),
            "aname": str(ctx.author),
            "aid": str(ctx.author.id),
            "mc": getattr(ctx.message, "content", ""),
            "command": str(ctx.command),
            "cog": str(getattr(ctx.command, "cog", ""))
        }
        try:
            # response = await r.table("errors").insert(_error).run(self.bot.connection)
            response = await self.set_value("errors", None, _error)
        except BaseException:
            response = {"inserted": 0}

        if response['inserted'] > 0:
            _id = response['generated_keys'][0]
            embed = discord.Embed(
                title="Uh oh, something bad just happened",
                description=f"We tried executing your command but something very unexpected happened. Either a bug or a tiger escaped the zoo but im pretty sure it was a bug. I have alerted my higher ups that this has occured and it should be fixed soon. [Track Issue](https://welcomer.fun/errors/{_id})\n\n`{_error['name']}`")
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Uh oh, something bad just happened",
                description=f"We tried executing your command but something extremely unexpected happened. I was unable to contact my higher ups at this moment in time and this could be very bad. Please head to the support server and give them my memo")
            await ctx.send(embed=embed, file=discord.File(io.StringIO(ujson.dumps(_error)), "memo.json"))

    @ commands.command(
        name="help",
        description="|Returns list of all commands with their usage and description")
    async def custom_help(self, ctx, module=""):
        message = ""
        modules = dict()
        modules['misc'] = []

        is_developer = await ctx.bot.has_special_permission(ctx.author,
                                                            developer=True)
        is_admin = await ctx.bot.has_special_permission(ctx.author,
                                                        developer=True,
                                                        admin=True)
        is_support = await ctx.bot.has_special_permission(ctx.author,
                                                          developer=True,
                                                          admin=True,
                                                          support=True)
        for command in self.bot.commands:
            if isinstance(command, discord.ext.commands.core.Group):
                if (
                    is_developer if "developer" in (
                        command.brief or "") else True) and (
                    is_support if "support" in (
                        command.brief or "") else True) and (
                    is_admin if "admin" in (
                        command.brief or "") else True):
                    modules[command.name.lower()] = command
            else:
                modules['misc'].append(command)

        if module == "":
            message = rockutils._(
                "Please specify a module that you would like to look up",
                ctx) + "\n\n"
            for k in sorted(modules.keys()):
                if k == "misc":
                    message += f"{self.bot.get_emote('dotshorizontal')} **MISC** - `Helpful commands for general use`\n"
                c = self.bot.get_command(k)
                if c:
                    message += f"{self.bot.get_emote(c.description.split('|')[0])} **{c.name.upper()}** - "
                    message += f"`{c.description.split('|')[1]}`\n"
            return await self.send_data(ctx, message, ctx.userinfo,
                                        prefer_dms=True, raw=False,
                                        force_guild=False, force_dm=False,
                                        alert=True)

        if module != "":
            if module.lower() in modules.keys():
                modules = {
                    module.lower(): modules[module.lower()]
                }
            else:
                message = rockutils._(
                    "Could not find a module with the name: **{modulename}**",
                    ctx).format(
                    modulename=module)
                message += "\n\n" + rockutils._("Modules", ctx) + ":\n\n"
                message += ", ".join(f"**{k}**" for k in modules.keys())
                return await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)

        for cog, cog_obj in modules.items():
            if cog.lower() in ['misc']:
                message = ""
                message += f"\n**{self.bot.get_emote('dotshorizontal')}  MISC**\n\n"
                for command in sorted(
                        cog_obj, key=lambda o: f"{o.full_parent_name} {o.name}"):
                    if len(command.description.split("|")) >= 2:
                        sub_message = f"**{command.full_parent_name} {command.name} {command.description.split('|')[0]}** | {command.description.split('|')[1]}\n"
                    else:
                        sub_message = f"**{command.full_parent_name} {command.name}** | {command.description}\n"
                    if len(message) + len(sub_message) > 2048:
                        await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)
                        message = ""
                    message += sub_message
            else:
                message = ""
                message += f"\n**{self.bot.get_emote(cog_obj.description.split('|')[0])}  {cog.upper()}**\n\n"
                for command in sorted(
                        cog_obj.commands,
                        key=lambda o: f"{o.full_parent_name} {o.name}"):
                    if len(command.description.split("|")) >= 2:
                        sub_message = f"**{command.full_parent_name} {command.name} {command.description.split('|')[0]}** | {command.description.split('|')[1]}\n"
                    else:
                        sub_message = f"**{command.full_parent_name} {command.name}** | {command.description}\n"
                    if len(message) + len(sub_message) > 2048:
                        await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)
                        message = ""
                        sub_message = ""
                    message += sub_message

        await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)

    async def chunk_guild(self, guild):
        if guild.chunked:
            return

        a = time.time()
        await guild.chunk(cache=True)
        if math.ceil((time.time()-a)*1000) >= 10000:
            await rockutils.send_webhook(
                "https://discord.com/api/webhooks/8[removed]",
                f"{'<@143090142360371200>' if math.ceil((time.time()-a)*1000) > 60000 else ''}Chunked {guild.id} in {math.ceil((time.time()-a)*1000)}ms Shard: {self.bot.shard_id} Cluster: {self.bot.cluster_id}")
        rockutils.prefix_print(
            f"Chunked {guild.id} in {math.ceil((time.time()-a)*1000)}ms", prefix_colour="light yellow", prefix="Core:ProcessMessage")

        # try:
        #     a = time.time()
        #     since = self.bot.chunkcache.get(guild.id, 0)

        #     cond = self.bot.lockcache.get(guild.id)
        #     if not cond:
        #         self.bot.lockcache[guild.id] = asyncio.Condition()
        #         cond = self.bot.lockcache[guild.id]

        #     if type(since) != float:
        #         self.bot.chunkcache[guild.id] = 0
        #         since = 0

        #     if a-since > 60:
        #         rockutils.prefix_print(
        #             f"Chunking {guild.id}", prefix_colour="light yellow", prefix="Core:ProcessMessage")
        #         self.bot.chunkcache[guild.id] = a

        #         await cond.acquire()
        #         await guild.chunk(cache=True)
        #         cond.notify_all()

        #         if math.ceil((time.time()-a)*1000) >= 1000:
        #             await rockutils.send_webhook(
        #                 "https://discord.com/api/webhooks/[removed]",
        #                 f"{'<@143090142360371200>' if math.ceil((time.time()-a)*1000) > 60000 else ''}Chunked {guild.id} in {math.ceil((time.time()-a)*1000)}ms Shard: {self.bot.shard_id} Cluster: {self.bot.cluster_id}")
        #         rockutils.prefix_print(
        #             f"Chunked {guild.id} in {math.ceil((time.time()-a)*1000)}ms", prefix_colour="light yellow", prefix="Core:ProcessMessage")
        #     elif cond:
        #         rockutils.prefix_print(
        #             f"Waiting for chunk lock on {guild.id}", prefix_colour="light yellow", prefix="Core:ProcessMessage")
        #         await cond.wait()
        #         rockutils.prefix_print(
        #             f"Finished waiting for chunk lock for {guild.id}", prefix_colour="light yellow", prefix="Core:ProcessMessage")
        #         # wait on lock
        # except Exception as e:
        #     rockutils.prefix_print(
        #         f"Failed to chunk guild: {e.id}", prefix_colour="red", prefix="Core:ProcessMessage")

    async def process_message(self, message):
        prefixes = (await self.get_prefix(message, return_prefixes=True), f"<@{self.bot.user.id}>", f"<@!{self.bot.user.id}>")
        if not message.content.startswith(prefixes):
            return

        ctx = await self.bot.get_context(message)

        if ctx.command is None:
            if ctx.guild.me in ctx.message.mentions:
                message.content = f"{prefixes[0]}prefix"
                ctx = await self.bot.get_context(message)
            else:
                return

        if ctx.guild:
            try:
                await asyncio.wait_for(self.bot.chunk_guild(ctx.guild), timeout=10)
            except asyncio.TimeoutError:
                await rockutils.send_webhook(
                    "https://discord.com/api/webhooks/[removed]",
                    f"Failed to chunk guild `{ctx.guild}` ID: {ctx.guild.id} Shard: {self.bot.shard_id} Cluster: {self.bot.cluster_id}")
                return await ctx.send(f"{self.bot.get_emote('alert')}  | " + "I am having problems chunking this guild. Try again later. Keep getting this issue? Try the other bot: http://welcomer.gg/invitebot/fallback")

        ctx.userinfo = await self.bot.get_user_info(ctx.author.id, refer="process_commands")

        if isinstance(message.guild, discord.guild.Guild):
            ctx.guildinfo = await self.bot.get_guild_info(ctx.guild.id, refer="process_commands")
        else:
            ctx.guildinfo = copy.deepcopy(
                rockutils.load_json("cfg/default_guild.json"))

        ctx.prefix = ctx.guildinfo['d']['b']['p']

        rockutils.prefix_print(
            ctx.message.content,
            prefix=ctx.author.__str__())

        # black and whitelist

        if self.bot.donator:
            if ctx.guild:
                has_donated = await self.bot.has_guild_donated(ctx.guild, ctx.guildinfo, donation=True, partner=True)
                if not has_donated:
                    if ctx.command.name not in [
                            'help', 'donate', 'prefix', 'membership']:
                        message = rockutils._(
                            "A membership is required to use the donator bot. You can find out more at **{website}** or by doing `{donatecommand}`. If you have donated, do `{membershipcommand}` to be able to manage servers you have a membership on".format(
                                website="https://welcomer.fun/donate",
                                donatecommand="+donate",
                                membershipcommand="+membership"))
                        try:
                            await ctx.send(
                                f"{self.bot.get_emote('cross')}  | " + message)
                        except BaseException:
                            pass
            elif ctx.guild:
                if ctx.command.name not in [
                        'help', 'donate', 'prefix', 'membership']:
                    message = rockutils._(
                        "A membership is required to use the donator bot. You can find out more at **{website}** or by doing `{donatecommand}`. If you have donated, do `{membershipcommand}` to be able to manage servers you have a membership on".format(
                            website="https://welcomer.fun/donate",
                            donatecommand="+donate",
                            membershipcommand="+membership"))
                    try:
                        await ctx.send(
                            f"{self.bot.get_emote('cross')}  | " + message)
                    except BaseException:
                        pass
        else:
            if ctx.guild and ctx.guild.get_member(
                    498519480985583636) and not self.bot.debug:
                # If this is normal bot and sees donator welcomer, do not
                # respond to messages
                return

        if self.bot.user == 330416853971107840 and ctx.guild.get_member(824435160593727518):
            # Do not process commands if i am the main bot and see bcomer
            return

        await self.bot.invoke(ctx)


class DataSerialiser:

    def __init__(self, bot):
        self.bot = bot

    # def guild_detailed(self, guild):
    #     detailed = {
    #         "streaming": 0,
    #         "online": 0,
    #         "idle": 0,
    #         "dnd": 0,
    #         "offline": 0,
    #         "bots": 0,
    #         "members": 0,
    #     }

    #     if guild and isinstance(guild, discord.Guild):
    #         for member in guild.members:
    #             detailed["bots" if member.bot else "members"] += 1

    #             if hasattr(member, "status"):
    #                 detailed[str(member.status)] += 1

    #             if hasattr(member, "activities"):
    #                 for activity in member.activities:
    #                     if isinstance(
    #                             activity, discord.Streaming):
    #                         detailed['streaming'] += 1
    #             elif hasattr(member, "activity") and isinstance(member.activity, discord.Streaming):
    #                 detailed['streaming'] += 1

    #     return detailed

    def guild(self, guild):
        guild_info = {}

        if guild and isinstance(guild, discord.Guild):
            guild_info = {
                "name": guild.name,
                "id": str(guild.id),
                "owner": {
                    "id": "0",
                    "name": "?"
                },
                "region": str(guild.region),
                "users": guild.member_count,
                "bots": sum(1 for m in guild.members if m.bot),
                "creation": guild.created_at.timestamp(),
                "icon": str(guild.icon),
                "icons": [
                    str(guild.icon_url_as(format="jpeg", size=64)),
                    str(guild.icon_url_as(format="png", size=256))
                ]
            }

            if guild.owner or guild.owner_id:
                try:
                    owner_id = guild.owner.id
                except:
                    owner_id = guild.owner_id

                guild_info["owner"]["id"] = str(guild.owner_id)
                guild_info["owner"]["name"] = str(guild.owner)

        return guild_info

    async def guildelevation(self, guild, guildinfo=None, member=None):
        guildinfo = {}

        if guild and isinstance(guild, discord.Guild):
            guild_info = {
                "name": guild.name,
                "id": str(guild.id),
                "owner": {
                    "id": str(getattr(guild.owner, "id", guild.owner_id)),
                    "name": str(guild.owner),
                },
                "users": guild.member_count,
                "bots": sum(1 for m in guild.members if m.bot),
                "icon": str(guild.icon),
                "icons": [
                    str(guild.icon_url_as(format="jpeg", size=64)),
                    str(guild.icon_url_as(format="png", size=256))
                ]
            }

            if member and guildinfo:
                member = guild.get_member(member.id)
                if member:
                    guild_info['elevated'] = await self.bot.has_elevation(guild, guildinfo, member)

        return guild_info

    def roles(self, guild):
        roles = []

        for role in guild.roles:
            roles.append({
                "name": role.name,
                "id": str(role.id),
                "position": str(role.position),
                "higher": role > guild.me.top_role,
            })

        return roles

    def channels(self, guild):
        channels = {
            "categories": [],
            "voice": [],
            "text": []
        }

        if guild and isinstance(guild, discord.Guild):
            for channel in guild.channels:
                if isinstance(channel, discord.TextChannel):
                    channels['text'].append({
                        "name": channel.name,
                        "id": str(channel.id),
                        "position": channel.position,
                        "category": str(getattr(channel, "category_id")),
                        "topic": channel.topic,
                        "nsfw": channel.is_nsfw()
                    })
                if isinstance(channel, discord.VoiceChannel):
                    channels['voice'].append({
                        "name": channel.name,
                        "id": str(channel.id),
                        "position": channel.position,
                        "category": str(getattr(channel, "category_id")),
                        "bitrate": channel.bitrate,
                        "user_limit": channel.user_limit
                    })
                if isinstance(channel, discord.CategoryChannel):
                    channels['categories'].append({
                        "name": channel.name,
                        "id": str(channel.id),
                        "position": channel.position,
                        "nsfw": channel.is_nsfw()
                    })
        return channels

    def emotes(self, guild):
        emotes = []
        if guild and isinstance(guild, discord.Guild):
            for emote in guild.emojis:
                emotes.append({
                    "str": str(emote),
                    "id": str(emote.id),
                    "name": emote.name,
                    "gif": emote.animated,
                    "url": str(emote.url)
                })
        return emotes

    async def invites(self, guild):
        ginvites = []
        if guild and isinstance(guild, discord.Guild):
            try:
                for invite in await guild.invites():
                    try:
                        ginvites.append(
                            {"code": invite.code, "created_at": math.ceil(
                                invite.created_at.timestamp()),
                            "temp": invite.temporary, "uses": invite.uses,
                            "max": invite.max_uses,
                            "inviter": str(invite.inviter.id)
                            if invite.inviter else "Unknown",
                            "inviter_str": str(invite.inviter)
                            if invite.inviter else "Unknown",
                            "channel": str(invite.channel.id),
                            "channel_str": str(invite.channel),
                            "duration": str(invite.max_age), })
                    except AttributeError as e:
                        print("Issue when handling invite", invite.code, "on guild", guild.id, e)
                    except Exception as e:
                        raise e
            except Exception as e:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                rockutils.prefix_print(
                    f"Failed to retrieve invites: {e}",
                    prefix_colour="light red")
                return []

        return ginvites

    def user(self, user):
        userinfo = {}
        if user and type(user) in [discord.User, discord.ClientUser]:
            userinfo = {
                "name": user.name,
                "bot": user.bot,
                "id": str(user.id),
                "discriminator": user.discriminator,
                "display": str(user.name),
                "icon": str(user.avatar),
                "creation": user.created_at.timestamp(),
                "avatar": [
                    str(user.default_avatar_url),
                    str(user.avatar_url_as(format="jpeg", size=64)),
                    str(user.avatar_url_as(format="png", size=256))
                ]
            }
        return userinfo

    def mutualguildsid(self, _id):
        guilds = []
        for guild in self.bot.guilds:
            member = guild.get_member(_id)
            if member.bot:
                return []
            if member:
                guilds.append(self.guild(guild))
        return guilds

    def mutualguilds(self, user):
        guilds = []
        if user.bot:
            return guilds
        for guild in self.bot.guilds:
            if guild.get_member(user.id):
                guilds.append(self.guild(guild))
        return guilds

    def badges(self, user, userinfo):
        _time = time.time()
        badges = []
        if (userinfo['m']['1']['h'] and (
            _time < (userinfo['m']['1'].get('u', 0) or 0) or userinfo['m']['1']['p'])) or \
            (userinfo['m']['3']['h'] and (
                _time < (userinfo['m']['3'].get('u', 0) or 0) or userinfo['m']['3']['p'])) or \
            (userinfo['m']['5']['h'] and (
                _time < (userinfo['m']['5'].get('u', 0) or 0) or userinfo['m']['5']['p'])):
            badges.append([
                self.bot.get_emote("gift"),
                "Donator",
                "This user supports welcomer",
                "202225"
            ])
        if userinfo['m']['p']:
            badges.append([
                self.bot.get_emote("starbox"),
                "Welcomer Partner",
                "Currently a Welcomer partner",
                "2D103F"
            ])
        all_guilds = rockutils.merge_embeded_lists(
            userinfo['g']['g']['m']['c'])
        tops = {}
        for guild in all_guilds:
            if guild['owner']['id'] == str(user.id):
                if guild['users'] > 250:
                    if not guild['id'] in tops:
                        tops[guild['id']] = guild
                    if guild['users'] > tops[guild['id']]['users']:
                        tops[guild['id']] = guild
        for guild in tops.values():
            badges.append([
                self.bot.get_emote("packagevariantclosed"),
                "Server Owner",
                f"Owner of server with {guild['users']} members",
                "202225"
            ])

        if user.id in self.bot.config['roles']['support']:
            badges.append([
                self.bot.get_emote("gavel"),
                "Welcomer Support",
                "Official Welcomer support member",
                "202225"
            ])

        if user.id in self.bot.config['roles']['trusted']:
            badges.append([
                self.bot.get_emote("accountstar"),
                "Trusted user",
                "User that Welcomer recognises as trustworthy",
                "202225"
            ])

        if user.id in self.bot.config['roles']['admins']:
            badges.append([
                self.bot.get_emote("wrench"),
                "Welcomer Administrator",
                "Official Welcomer administrator",
                "202225"
            ])

        if user.id in self.bot.config['roles']['developer']:
            badges.append([
                self.bot.get_emote("cogs"),
                "Welcomer Developer",
                "These people made the bot :)",
                "202225"
            ])

        return badges


def setup(bot):

    def existingdict(subject, key, data):
        if not subject.get(key):
            subject[key] = data

    caches = [
        "prefix",
        "guilddetails",
        "rules",
        "analytics",
        "channels",
        "serverlock",
        "staff",
        "tempchannel",
        "autorole",
        "rolereact",
        "leaver",
        "freerole",
        "timeroles",
        "namepurge",
        "welcomer",
        "stats",
        "automod",
        "borderwall",
        "customcommands",
        "music",
        "polls",
        "logging",
        "moderation",
        "activepunishments"
    ]

    for name in caches:
        existingdict(bot.cache, name, {})

    core = WelcomerCore(bot)
    for key in dir(core):
        if not ("on_" in key[:3] and key != "on_message_handle"):
            value = getattr(core, key)
            if callable(value) and "_" not in key[0]:
                setattr(bot, key, value)
                if not hasattr(bot, key):
                    print(f"I called set for {key} but its not set now")

    bot.remove_command("help")
    bot.add_cog(core)

    if not hasattr(bot, "chunkcache"):
        setattr(bot, "chunkcache", {})
    if not hasattr(bot, "lockcache"):
        setattr(bot, "lockcache", {})

    setattr(bot, "ranonconnect", False)

    setattr(bot, "cachemutex", False)
    setattr(bot, "serialiser", DataSerialiser(bot))
    setattr(bot, "emotes", rockutils.load_json("cfg/emotes.json"))

    default_data = rockutils.load_json("cfg/default_user.json")
    setattr(bot, "default_user", default_data)

    default_data = rockutils.load_json("cfg/default_guild.json")
    setattr(bot, "default_guild", default_data)

    bot.reload_data("cfg/config.json", "config")
    reload(handling)
