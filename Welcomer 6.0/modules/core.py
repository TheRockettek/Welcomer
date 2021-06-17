from discord.ext import commands
from rockutils import rockutils
from datetime import datetime

import aiohttp
import asyncio
import copy
import discord
import math
import time
import os
import functools

import rethinkdb as r
import ujson as json

def canint(val):
    try:
        int(val)
        return True
    except ValueError:
        return False

    class NoPermission(Exception):
        pass
    
    class NoDonator(Exception):
        pass


class WelcomerCore:

    def __init__(self, bot):
        self.bot = bot

    async def get_guild_info(self, id, refer="", reload_data=True):
        rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for G:{id}", prefix="Guild Info:Get", prefix_colour="light green")
        guild_info = await r.table("guilds").get(str(id)).run(self.bot.connection)

        new_data = True if type(guild_info) != dict else not bool(guild_info)
        has_updated = True if new_data else False

        guild = self.bot.get_guild(int(id))
        _guild_info = self.bot.serialiser.guild(guild)
        _time = time.time()
        
        default_data = rockutils.load_json("cfg/default_guild.json")
        latest_version = default_data['d']['dv']

        if new_data and guild:
            guild_info = default_data

        origional_guild_info = copy.deepcopy(guild_info)

        guild_info['d']['b']['c'] = self.bot.cluster_id
        guild_info['id'] = str(id)

        if guild:
            if new_data:
                guild_info['d']['g']['ga'] = math.ceil(_time)
                guild_info['d']['g']['gc'] = math.ceil(guild.created_at.timestamp())
            guild_info['d']['g']['i'] = _guild_info['icons']
            guild_info['d']['g']['n'] = _guild_info['name']
            guild_info['d']['b']['sh'] = guild.shard_id

            user = self.bot.get_user(guild.owner.id)
            if user:
                guild_info['d']['g']['o'] = self.bot.serialiser.user(user)
            
            if _time - guild_info['d']['m']['u'] > 600:
                guild_info['d']['m'] = {
                    "b": _guild_info['bots'],
                    "m": _guild_info['users'] - _guild_info['bots'],
                    "a": _guild_info['users'],
                    "u": _time
                }
            
            if _time - guild_info['d']['d']['u'] > 600:
                _guild_detailed = self.bot.serialiser.guild_detailed(guild)
                guild_info['d']['d'] = {
                    "s": _guild_detailed['streaming'],
                    "o": _guild_detailed['online'],
                    "i": _guild_detailed['idle'],
                    "d": _guild_detailed['dnd'],
                    "of": _guild_detailed['offline'],
                    "u": _time
                }

            if _time - guild_info['d']['c']['u'] > 600:
                _channels = self.bot.serialiser.channels(guild)
                guild_info['d']['c'] = {
                    "c": _channels['categories'],
                    "v": _channels['voice'],
                    "t": _channels['text'],
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

            guild_info['d']['dv'] = default_data['d']['dv']
            has_updated = True

        if has_updated or new_data:
            if new_data:
                rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Creating information for G:{id}", prefix="Guild Info:Get", prefix_colour="light green")
                await r.table("guilds").insert(guild_info).run(self.bot.connection)
            else:
                await self.update_guild_info(id, guild_info)

        await self.create_guild_cache(guild_info, guild)
        return guild_info

    async def update_guild_info(self, id, data, forceupdate=False, refer=""):
        try:
            rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for G:{id}", prefix="Guild Info:Update", prefix_colour="light green")
            t = time.time()
            if forceupdate:
                await r.table("guilds").get(str(id)).update(data).run(self.bot.connection)
            else:
                await r.table("guilds").get(str(id)).replace(data).run(self.bot.connection)
            te = time.time()
            if te-t > 1:             
                rockutils.prefix_print(f"Updating guild info took {math.floor((te-t)*1000)}ms", prefix="Guild Info:Update", prefix_colour="red", text_colour="light red")
            return True
        except Exception as e:
            rockutils.prefix_print(f"Error occured whilst updating info for G:{id}. {e}", prefix="Guild Info:Update", prefix_colour="red", text_colour="light red")
            return False



    async def get_user_info(self, id, refer="", reload_data=True):
        rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for U:{id}", prefix="User Info:Get", prefix_colour="light green")
        user_info = await r.table("users").get(str(id)).run(self.bot.connection)

        new_data = True if type(user_info) != dict else not bool(user_info)
        has_updated = True if new_data else False

        user = self.bot.get_user(int(id))
        _user_info = self.bot.serialiser.user(user)
        _time = time.time()
        
        default_data = rockutils.load_json("cfg/default_user.json")
        latest_version = default_data['g']['dv']

        if new_data and user:
            user_info = default_data

        origional_user_info = copy.deepcopy(user_info)

        user_info['id'] = str(id)

        if user:
            if new_data:
                user_info['g']['g']['ua'] = math.ceil(_time)
                user_info['g']['g']['uc'] = math.ceil(user.created_at.timestamp())
            user_info['g']['g']['a'] = _user_info['avatar']
            user_info['g']['g']['n'] = _user_info['name']
            user_info['g']['g']['d'] = _user_info['discriminator']
            user_info['g']['g']['u'] = _time

            if _time - user_info['g']['g']['m']['u'].get(self.bot.cluster_id, 0) > 900:
                user_info['g']['g']['m']['c'][self.bot.cluster_id] = self.bot.serialiser.mutualguilds(user)
                user_info['g']['g']['m']['u'][self.bot.cluster_id] = _time
            
            expired = []
            renew = []
            for membership_type,v in user_info['m'].items():
                if type(v) == dict:
                    if user_info['m'][membership_type]['h'] and _time - user_info['m'][membership_type]['u'] > 0:
                        user_info['m'][membership_type]['h'] = False
                        expired.append(membership_type)
                        if user_info['m'][membership_type]['p']:
                            user_info['m'][membership_type]['h'] = True
                            renew.append(membership_type)

            if len(expired) > 0 or len(renew) > 0:
                message = rockutils._("Some of your memberships have expired and may have renewed if you have payed using patreon.\n\n__Expired memberships:__\n{}\n\n__Renewed memberships:__\n{}\n\nYou are able to renew memberships automatically by donating with patreon. Find out more at **{}**".format("https://welcomer.fun/donate"), guild_info)
                try:
                    await user.send(message)
                except:
                    pass

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
                rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Creating information for G:{id}", prefix="User Info:Get", prefix_colour="light green")
                await r.table("users").insert(user_info).run(self.bot.connection)
            else:
                await self.update_user_info(id, user_info)

        return user_info


    async def update_user_info(self, id, data, forceupdate=False, refer=""):
        try:
            rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for U:{id}", prefix="User Info:Update", prefix_colour="light green")
            t = time.time()
            if forceupdate:
                await r.table("users").get(str(id)).update(data).run(self.bot.connection)
            else:
                await r.table("users").get(str(id)).replace(data).run(self.bot.connection)
            te = time.time()
            if te-t > 1:             
                rockutils.prefix_print(f"Updating guild info took {math.floor((te-t)*1000)}ms", prefix="User Info:Update", prefix_colour="red", text_colour="light red")
            return True
        except Exception as e:
            rockutils.prefix_print(f"Error occured whilst updating info for U:{id}. {e}", prefix="User Info:Update", prefix_colour="red", text_colour="light red")
            return False

    async def on_connect(self):
        rockutils.prefix_print("Bot is now connecting", prefix_colour="green")
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 0})

    async def on_ready(self):
        rockutils.prefix_print("Bot is fully ready", prefix_colour="green")
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 1})

    async def on_resume(self):
        rockutils.prefix_print("Bot is now resuming", prefix_colour="green")
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 4})

    async def on_shard_ready(self, shard):
        rockutils.prefix_print(f"Shard {shard} is ready", prefix_colour="green")

    async def sync_task(self):
        ws = self.bot.ipc_ws
        rockutils.prefix_print("Starting sync task", prefix="Sync Task")
        while True:
            try:
                await self.sync_handle()
            except Exception as e:
                rockutils.prefix_print(str(e), prefix="Sync Task", prefix_colour="light red", text_colour="red")
            await asyncio.sleep(1)

    async def sync_receiver(self):
        ws = self.bot.ipc_ws
        rockutils.prefix_print("Yielding sync receiver", prefix="Sync Handler")
        while not self.bot.is_ready():
            await asyncio.sleep(1)
        rockutils.prefix_print("Starting sync receiver", prefix="Sync Handler")
        while True:
            try:
                jobs = await ws.receive_json(loads=json.loads)
                print(jobs)
            except ValueError:
                pass
            else:
                _sub = []
                if len(jobs) > 0:
                    try:
                        f = open("handling.py", "r")
                        file_content = f.read()
                        f.close()
                        compile(file_content + "\n", "handling.py", "exec")
                        import handling
                    except Exception as e:
                        rockutils.prefix_print(f"Could not update handling: {str(e)}", prefix="Sync Handler", prefix_colour="light red", text_colour="red")
                for job in jobs:
                    try:
                        opcode = job['o'].lower()
                        try:
                            args = json.loads(job['a'])
                        except:
                            args = job['a']
                        key = job['k']

                        if canint(args):
                            args = int(args)

                        if hasattr(handling, opcode):
                            try:
                                result = await getattr(handling, opcode)(self, opcode, args)
                            except Exception as e:
                                result = result = {"success": False, "error": "Exception", "exception": str(type(e))}
                                rockutils.prefix_print(f"Could not process job. {opcode}:{args}. {str(e)}", prefix="Sync Handler", prefix_colour="light red", text_colour="red")
                        else:
                            result = {"success": False, "error": "InvalidOPCode"}

                        _payload = {
                            "o": "SUBMIT",
                            "k": key,
                            "r": self.bot.cluster_id,
                            "d": result
                        }
                        self.bot.ipc_queue.append(_payload)
                    except Exception as e:
                        rockutils.prefix_print(f"Could not process jobs: {str(e)}", prefix="Sync Handler", prefix_colour="light red", text_colour="red")
            await asyncio.sleep(0.05)

    async def sync_sender(self):
        ws = self.bot.ipc_ws
        rockutils.prefix_print("Starting sync sender", prefix="Sync Handler")
        while True:
            for _payload in self.bot.ipc_queue:
                try:
                    _payload['o'] = _payload['o'].upper()
                    await ws.send_json(_payload, dumps=json.dumps)
                except Exception as e:
                    rockutils.prefix_print(f"Could not send payload. {_payload}. {str(e)}", prefix="Sync Handler", prefix_colour="light red", text_colour="red")
                self.bot.ipc_queue.remove(_payload) if _payload in self.bot.ipc_queue else 0
            await asyncio.sleep(0.05)

    async def sync_handle(self):
        rockutils.prefix_print("Starting sync handler", prefix="Sync Handler")
        try:
            domain = f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/ipc/{self.bot.cluster_id}/{self.bot.config['ipc']['auth_key']}"
            rockutils.prefix_print(f"Connecting to WS via {domain}")
            session = aiohttp.ClientSession()
            self.bot.ipc_ws = await session.ws_connect(domain)

            rockutils.prefix_print("Connected to websocket", prefix="Sync Handler")
            self.bot.sync_sender_task = self.bot.loop.create_task(self.sync_sender())
            self.bot.sync_receiver_task = self.bot.loop.create_task(self.sync_receiver())

            while True:
                await asyncio.sleep(1)
                if self.bot.sync_receiver_task.done() or self.bot.sync_sender_task.done():
                    rockutils.prefix_print("Closing sync", prefix="Sync Handler", text_colour="red")

                    try:
                        self.bot.sync_receiver_task.cancel()
                    except:
                        pass
                    try:
                        self.bot.sync_sender_task.cancel()
                    except:
                        pass

                    await session.close()
                    return

        except aiohttp.client_exceptions.ClientConnectionError:
            await session.close()
            rockutils.prefix_print("Encountered connection error with IPC", prefix="Sync Handler", prefix_colour="light red", text_colour="red")
            await asyncio.sleep(2)
        except Exception as e:
            rockutils.prefix_print(str(e), prefix="Sync Handler", prefix_colour="light red", text_colour="red")

    async def push_ipc(self, _payload):
        if _payload.get("o","") != "":
            self.bot.ipc_queue.append(_payload)
            return True
        else:
            return False

    async def has_guild_donated(self, guild, guild_info, plus=True, pro=True, extended=True, partner=True):
        if guild and type(guild) == discord.Guild:
            _time = time.time()

            if partner:
                _userinfo = await self.bot.get_user_info(guild.owner.id)
                if _userinfo and _userinfo['m']['p']:
                    return True

            for id in guild_info['d']['de']:
                _userinfo = await self.bot.get_user_info(id)
                if _userinfo:
                    if extended:
                        if _userinfo['m']['extended']['h'] and (_time - _userinfo['m']['extended']['u'] > 0 or _userinfo['m']['extended']['p']):
                            return True
                    if pro:
                        if _userinfo['m']['pro']['h'] and (_time - _userinfo['m']['pro']['u'] > 0 or _userinfo['m']['pro']['p']):
                            return True
                    if plus:
                        if _userinfo['m']['plus']['h'] and (_time - _userinfo['m']['plus']['u'] > 0 or _userinfo['m']['plus']['p']):
                            return True

        return False

    async def has_special_permission(self, user, support=False, developer=False, admin=False, trusted=False):
        _config = rockutils.load_json("cfg/config.json")

        if user and type(user) in [discord.User, discord.Member]:
            if support and user.id in _config['roles']['support']:
                return True

            if developer and user.id in _config['roles']['developer']:
                return True

            if admin and user.id in _config['roles']['admins']:
                return True

            if trusted and user.id in _config['roles']['trusted']:
                return True

        if _config != self.bot.config:
            self.bot.config = copy.deepcopy(_config)

        return False


    async def send_data(self, ctx, message, userinfo={}, prefer_dms=False, force_guild=False, force_dm=False, alert=True, title="", footer="", raw=False):
        if force_dm and force_guild:
            force_dm, force_guild = False, False
        if userinfo.get("g"):
            use_guild = userinfo['g']['b']['pd']
        if force_dm:
            use_guild = False
        if force_guild:
            use_guild = True
        if not getattr(ctx, "guild", False):
            use_guild = False
        
        message_kwargs = {}

        if raw:
            message_kwargs['content'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
        else:
            embed_kwargs = {}
            embed_kwargs['description'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
            embed_kwargs['timestamp'] = datetime.utcfromtimestamp(math.ceil(time.time()))
            if title:
                embed_kwargs['title'] = title
            embed = discord.Embed(colour=3553599, **embed_kwargs)
            embed.set_footer(text=footer)
            message_kwargs['embed'] = embed

        if use_guild:
            try:
                await ctx.send(**message_kwargs)
            except:
                try:
                    await ctx.send(message[:2048])
                except:
                    return
        else:
            try:
                await ctx.author.send(**message_kwargs)
                if alert and getattr(ctx, "guild", False):
                    try:
                        _message = rockutils._("Help has been sent to your direct messages", ctx)
                        await ctx.send(":mailbox_with_mail:  | " + _message)
                    except:
                        pass
            except:
                try:
                    await ctx.send(**message_kwargs)
                except:
                    try:
                        await ctx.send(message[:2048])
                    except:
                        return
            


    def reload_data(self, filename, key=None):
        if not key:
            head, key = os.path.split(filename)
            key = key[:key.find(".")]

        if os.path.exists(filename):
            data = rockutils.load_json(filename)
            if not key:
                head, key = os.path.split(filename)
                key = key[:key.find(".")]
            setattr(self.bot, key, data)
            return True, key
        else:
            return False, key
    
    def should_cache(self, guildinfo):
        return guildinfo['a']['e'] or len(guildinfo['rr']) > 0 or guildinfo['tr']['e'] or guildinfo['am']['e'] or guildinfo['s']['e']

    async def create_guild_cache(self, guildinfo, guild=None, cache_filter=[], force=False):
        cached = False
        if not guild:
            guild = await self.bot.get_guild(int(guildinfo['id']))
        if guildinfo and guild:
            c = self.bot.cache
            id = guild.id

            if (not id in c['prefix'] or force) and ("prefix" in cache_filter if len(cache_filter) > 0 else True):
                c['prefix'][id] = guildinfo['d']['b']['p']

            if (not id in c['prefix'] or force) and ("prefix" in cache_filter if len(cache_filter) > 0 else True):
                c['prefix'][id] = guildinfo['d']['b']['p']

            if (not id in c['guilddetails'] or force) and ("guilddetails" in cache_filter if len(cache_filter) > 0 else True):
                c['guilddetails'][id] = guildinfo['d']['b']

            if (not id in c['rules'] or force) and ("rules" in cache_filter if len(cache_filter) > 0 else True):
                c['rules'][id] = guildinfo['r']

            if (not id in c['channels'] or force) and ("channels" in cache_filter if len(cache_filter) > 0 else True):
                c['channels'][id] = guildinfo['ch']

            if (not id in c['serverlock'] or force) and ("serverlock" in cache_filter if len(cache_filter) > 0 else True):
                c['serverlock'][id] = guildinfo['sl']

            if (not id in c['staff'] or force) and ("staff" in cache_filter if len(cache_filter) > 0 else True):
                c['staff'][id] = guildinfo['st']

            if (not id in c['tempchannel'] or force) and ("tempchannel" in cache_filter if len(cache_filter) > 0 else True):
                c['tempchannel'][id] = guildinfo['tc']

            if (not id in c['autorole'] or force) and ("autorole" in cache_filter if len(cache_filter) > 0 else True):
                c['autorole'][id] = guildinfo['ar']

            if (not id in c['rolereact'] or force) and ("rolereact" in cache_filter if len(cache_filter) > 0 else True):
                c['rolereact'][id] = guildinfo['rr']

            if (not id in c['leaver'] or force) and ("leaver" in cache_filter if len(cache_filter) > 0 else True):
                c['leaver'][id] = guildinfo['l']

            if (not id in c['freerole'] or force) and ("freerole" in cache_filter if len(cache_filter) > 0 else True):
                c['freerole'][id] = guildinfo['fr']

            if (not id in c['timeroles'] or force) and ("timeroles" in cache_filter if len(cache_filter) > 0 else True):
                c['timeroles'][id] = guildinfo['tr']

            if (not id in c['namepurge'] or force) and ("namepurge" in cache_filter if len(cache_filter) > 0 else True):
                c['namepurge'][id] = guildinfo['np']

            if (not id in c['welcomer'] or force) and ("welcomer" in cache_filter if len(cache_filter) > 0 else True):
                c['welcomer'][id] = guildinfo['w']

            if (not id in c['stats'] or force) and ("stats" in cache_filter if len(cache_filter) > 0 else True):
                c['stats'][id] = guildinfo['s']

            if (not id in c['automod'] or force) and ("automod" in cache_filter if len(cache_filter) > 0 else True):
                c['automod'][id] = guildinfo['am']

            if (not id in c['borderwall'] or force) and ("borderwall" in cache_filter if len(cache_filter) > 0 else True):
                c['borderwall'][id] = guildinfo['bw']

            if (not id in c['customcommands'] or force) and ("customcommands" in cache_filter if len(cache_filter) > 0 else True):
                c['customcommands'][id] = guildinfo['cc']
            
            if (not id in c['music'] or force) and ("music" in cache_filter if len(cache_filter) > 0 else True):
                c['music'][id] = guildinfo['m']
            
            if (not id in c['polls'] or force) and ("polls" in cache_filter if len(cache_filter) > 0 else True):
                c['polls'][id] = guildinfo['p']
            
            if (not id in c['logs'] or force) and ("logs" in cache_filter if len(cache_filter) > 0 else True):
                c['logs'][id] = guildinfo['lo']
            
            # "analytics",

        return cached

    async def has_elevation(self, guild, guildinfo, user):
        if await self.bot.has_special_permission(user, donator=True):
            return True
        
        if hasattr(guild, "owner"):
            if guild.owner.id == user.id:
                return True
        
        if guildinfo:
            if guildinfo.get("st"):
                if str(user.id) in guildinfo['st']['u'].keys():
                    return True
        
        member = guild.get_member(user.id)
        if member and await self.bot.has_permission_node(member, ["manage_guild","ban_members"]):
            return True

        return False

    async def get_prefix(self, message):
        if message.guild:
            if not message.guild.id in self.bot.cache['prefix']:
                guild_info = await self.bot.get_guild_info(message.guild.id, refer="get_prefix")
                self.bot.cache['prefix'][message.guild.id] = guild_info['d']['b']['p'] or "+"
            prefix = self.bot.cache['prefix'][message.guild.id]
        else:
            prefix = "+"
        return commands.when_mentioned_or(prefix)(self.bot, message)

    async def has_permission_node(self, target, check_for, return_has=False):
        permissions = discord.Permissions.all()
        my_permissions = {}
        for key in list(node.upper() for node in dir(permissions) if type(getattr(permissions, node)) == bool):
            my_permissions[key] = False

        for role in target.roles:
            for node in my_permissions:
                if getattr(role.permissions, node.lower()) == True:
                    my_permissions[node] = True

        if len(check_for) > 0:
            my_permissions = list(node for node,val in my_permissions.items() if val)
            if "ADMINISTRATOR" in my_permissions:
                return True

            for node in check_for:
                if node.upper() in my_permissions:
                    return True, my_permissions
            return False
        elif return_has:
            return list(node for node,val in my_permissions.items() if val)
        else:
            return False

    def get_emote(self, name, fallback=":grey_question:"):
        if not hasattr(self.bot, "emotes"):
            setattr(self.bot, "emotes", rockutils.load_json("cfg/emotes.json"))
        return self.bot.emotes.get(name, fallback)

    async def broadcast(self, opcode, recepients, args="", timeout=10):
        payload = {
            "op": opcode,
            "args": json.dumps(args),
            "recep": recepients,
            "timeout": str(timeout),
        }

        domain = f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/job/{self.bot.config['ipc']['auth_key']}"
        timeout = aiohttp.ClientTimeout(total=timeout+2)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(domain, headers=payload) as resp:
                print(await resp.text())
                return await resp.json()

    async def on_command_error(self, ctx, error):
        # if isinstance(error, self.NoPermission):
        #     message = rockutils._("You do not have permission to use this command")
        #     return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        # if isinstance(error, self.NoDonator):
        #     message = rockutils._("This command is for donators only. Do +membership to find out more")
        #     return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if isinstance(error, discord.ext.commands.NoPrivateMessage):
            message = rockutils._("This command cannot be ran in a private message")
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if isinstance(error, discord.ext.commands.BotMissingPermissions):
            message = rockutils._("The bot is unable to run this command as it is missing permissions: {0}")
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message.format(",".join(map(lambda o: o.upper(), error.missing_perms))))


    def requires_membership(plus=True, pro=True, extended=True, partner=True):
        async def _predicate(ctx):
            can_donate = await ctx.bot.has_guild_donated(ctx.guild, ctx.guildinfo, plus, pro, extended, partner)
            has_bot_elevation = await ctx.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True)
            if not can_donate and not has_bot_elevation:
                message = rockutils._("This command is for donators only. Do +membership to find out more")
                try:
                    await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
                except:
                    pass
            return has_bot_elevation or can_donate
        return commands.check(_predicate)

    def requires_special_elevation(support=True, developer=True, admin=True, trusted=True):
        async def _predicate(ctx):
            has_bot_elevation = await ctx.bot.has_special_permission(ctx.author, support, developer, admin, trusted)
            if not has_bot_elevation:
                message = rockutils._("You do not have permission to use this command")
                try:
                    await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
                except:
                    pass
            return has_bot_elevation
        return commands.check(_predicate)

    def requires_elevation(staffbypass=True):
        async def _predicate(ctx):
            elevated = await ctx.bot.has_elevation(self, ctx.guild, ctx.guildinfo, ctx.author)
            if not elevated:
                has_bot_elevation = await ctx.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True)
                if has_bot_elevation:
                    return True
            
            if not elevated:
                message = rockutils._("You do not have permission to use this command")
                try:
                    await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
                except:
                    pass
            return elevated
        return commands.check(_predicate)

    @commands.command()
    @requires_special_elevation(developer=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def test(self, ctx):
        await ctx.send("Passed")

    # on_error
    # on_command_error

    @commands.command(name="help", description="|Returns list of all commands with their usage and description")
    async def custom_help(self, ctx, module=""):
        message = ""
        modules = dict()
        modules['misc'] = []
        for command in self.bot.commands:
            if type(command) is discord.ext.commands.core.Group:
                modules[command.name.lower()] = command
            else:
                modules['misc'].append(command)
            # name = self.bot.cogs[command.cog_name].name
            # if not name in modules:
            #     modules[name] = []
            # modules[name].append(command)

        if module == "":
            message = rockutils._("Please specify a module that you would like to look up", ctx) + "\n\n"
            for k in sorted(modules.keys()):
                if k == "misc":
                    message += f":game_die: **MISC** - `List of commands not grouped`\n\n"
                c = self.bot.get_command(k)
                if c:
                    message += f"{c.description} **{c.name.upper()}** - `{getattr(self.bot.cogs[c.cog_name],'desc','No description found')}`\n\n"
            return await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)

        if module != "":
            if module.lower() in modules.keys():
                modules = {module.lower(): modules[module.lower()]}
            else:
                message = rockutils._("Could not find a module with the name: **{}**",ctx)
                message += "\n\n" + rockutils._("Modules",ctx) + ":\n\n"
                message += ", ".join(f"**{k}**" for k in modules.keys())#
                return await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)

        for cog, cog_obj in modules.items():
            if cog.lower() in ['misc']:
                sub_message = ""
                sub_message += f"\n**:game_die:  MISCELLANEOUS**\n\n"
                for command in sorted(cog_obj, key=lambda o: f"{o.full_parent_name} {o.name}"):
                    if len(command.description.split("|")) >= 2:
                        sub_message += f"**{command.full_parent_name} {command.name} {command.description.split('|')[0]}** | {command.brief or command.description.split('|')[1]}\n"
                    else:
                        sub_message += f"**{command.full_parent_name} {command.name}** | {command.brief or command.description}\n"
                if len(message) + len(sub_message) > 2048:
                    await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)
                    message = ""
            else:
                sub_message = ""
                sub_message += f"\n**{cog_obj.description}  {cog.upper()}**\n\n"
                for command in sorted(cog_obj.commands, key=lambda o: f"{o.full_parent_name} {o.name}"):
                    if len(command.description.split("|")) >= 2:
                        sub_message += f"**{command.full_parent_name} {command.name} {command.description.split('|')[0]}** | {command.brief or command.description.split('|')[1]}\n"
                    else:
                        sub_message += f"**{command.full_parent_name} {command.name}** | {command.brief or command.description}\n"
                if len(message) + len(sub_message) > 2048:
                    await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)
                    message = ""
            message += sub_message

        await self.send_data(ctx, message, ctx.userinfo, prefer_dms=True, raw=False, force_guild=False, force_dm=False, alert=True)


    async def process_message(self, message):
        if not message.content.startswith(tuple(await self.get_prefix(message))):
            return

        ctx = await self.bot.get_context(message)

        if ctx.command is None:
            if self.bot.user in ctx.message.mentions:
                c = self.bot.get_command("prefix")
                if c:
                    await c.invoke(ctx)
            return

        ctx.userinfo = await self.bot.get_user_info(ctx.author.id, refer="process_commands")

        if type(message.guild) == discord.guild.Guild:
            ctx.guildinfo = await self.bot.get_guild_info(ctx.guild.id, refer="process_commands")
        else:
            ctx.guildinfo = copy.deepcopy(rockutils.load_json("cfg/default_guild.json"))

        rockutils.prefix_print(ctx.message.content, prefix=ctx.author.__str__())

        if self.bot.donator:
            if ctx.guild:
                has_donated = await self.bot.has_guild_donated(ctx.guild, ctx.guildinfo, plus=True, pro=True, extended=True, partner=True)
                if not has_donated:
                    if not ctx.command.name in ['help','donate','prefix','membership']:
                        message = rockutils._("A membership is required to use the donator bot. You can find out more at **{}** or by doing `{}`. If you have donated, do `{}` to be able to manage servers you have a membership on".format("https://welcomer.fun/donate","+donate","+membership"))
                        try:
                            ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
                        except:
                            pass
            else:
                if not ctx.command.name in ['help','donate','prefix','membership']:
                    message = rockutils._("A membership is required to use the donator bot. You can find out more at **{}** or by doing `{}`. If you have donated, do `{}` to be able to manage servers you have a membership on".format("https://welcomer.fun/donate","+donate","+membership"))
                    try:
                        ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
                    except:
                        pass
        else:
            if ctx.guild and ctx.guild.get_member(498519480985583636) and not self.bot.debug:
                # If this is donator bot and sees normal welcomer, do not respond to messages
                return

        await self.bot.invoke(ctx)

class DataSerialiser:

    def __init__(self, bot):
        self.bot = bot

    def guild_detailed(self, guild):
        detailed = {
            "streaming": 0,
            "online": 0,
            "idle": 0,
            "dnd": 0,
            "offline": 0,
            "bots": 0,
            "members": 0,
        }

        if guild and type(guild) == discord.Guild:
            for member in guild.members:
                detailed["bots" if member.bot else "members"] += 1
                
                if hasattr(member, "status"):
                    detailed[str(member.status)] += 1
                
                if hasattr(member, "activity") and type(member.activity) == discord.ActivityType.streaming:
                    detailed['streaming'] += 1

        return detailed

    def guild(self, guild):
        guildinfo = {}

        if guild and type(guild) == discord.Guild:
            guild_info = {
                "name": guild.name,
                "id": str(guild.id),
                "owner": {
                    "id": str(guild.owner.id),
                    "name": str(guild.owner)
                },
                "users": guild.member_count,
                "bots": sum(1 for m in guild.members if m.bot),
                "icons": [
                    guild.icon_url_as(format="jpeg",size=64),
                    guild.icon_url_as(format="png",size=256)
                ]
            }

        return guild_info

    async def guildelevation(self, guild, guildinfo=None, member=None):
        guildinfo = {}

        if guild and type(guild) == discord.Guild:
            guild_info = {
                "name": guild.name,
                "id": str(guild.id),
                "owner": {
                    "id": str(guild.owner.id),
                    "name": str(guild.owner)
                },
                "users": guild.member_count,
                "bots": sum(1 for m in guild.members if m.bot),
                "icons": [
                    guild.icon_url_as(format="jpeg",size=64),
                    guild.icon_url_as(format="png",size=256)
                ]
            }

            if member and guildinfo:
                member = guild.get_member(member.id)
                if member:
                    guild_info['elevated'] = await self.bot.has_elevation(guild, guildinfo, member)

        return guild_info

    def channels(self, guild):
        channels = {
            "categories": [],
            "voice": [],
            "text": []
        }

        if guild and type(guild) == discord.Guild:
            for channel in guild.channels:
                if type(channel) == discord.TextChannel:
                    channels['text'].append({
                        "name": channel.name,
                        "id": str(channel.id),
                        "position": channel.position,
                        "category": str(getattr(channel,"category_id")),
                        "topic": channel.topic,
                        "nsfw": channel.is_nsfw()
                    })
                if type(channel) == discord.VoiceChannel:
                    channels['voice'].append({
                        "name": channel.name,
                        "id": str(channel.id),
                        "position": channel.position,
                        "category": str(getattr(channel,"category_id")),
                        "bitrate": channel.bitrate,
                        "user_limit": channel.user_limit
                    })
                if type(channel) == discord.CategoryChannel:
                    channels['categories'].append({
                        "name": channel.name,
                        "id": str(channel.id),
                        "position": channel.position,
                        "nsfw": channel.is_nsfw()
                    })
        return channels

    def emotes(self, guild):
        emotes = []
        if guild and type(guild) == discord.Guild:
            for emote in guild.emojis:
                emotes.append({
                    "str": str(emote),
                    "id": str(emote.id),
                    "name": emote.name,
                    "gif": emote.animated,
                    "url": emote.url
                })
        return emotes

    async def invites(self, guild):
        ginvites = []
        if guild and type(guild) == discord.Guild:
            try:
                for invite in await guild.invites():
                    ginvites.append({
                        "code": invite.code,
                        "created_at": math.ceil(invite.created_at.timestamp()),
                        "temp": invite.temporary,
                        "uses": invite.uses,
                        "max": invite.max_uses,
                        "inviter": str(invite.inviter.id) if invite.inviter else "Unknown",
                        "inviter_str": str(invite.inviter) if invite.inviter else "Unknown"
                    })
            except Exception as e:
                rockutils.prefix_print(f"Failed to retrieve invites: {e}", prefix_colour="light red")
                return [False, str(e)]

        return ginvites

    def user(self, user):
        userinfo = {}
        if user and type(user) == discord.User:
            userinfo = {
                "name": user.name,
                "bot": user.bot,
                "id": str(user.id),
                "discriminator": user.discriminator,
                "avatar": [
                    user.default_avatar_url,
                    user.avatar_url_as(format="jpeg",size=64),
                    user.avatar_url_as(format="png",size=256)
                ]
            }
        return userinfo

    def mutualguilds(self, user):
        guilds = []
        for guild in self.bot.guilds:
            if guild.get_member(user.id):
                guilds.append(self.guild(guild))
        return guilds

    def badges(self, user, userinfo):
        badges = []
        if userinfo['m']['plus']['h']:
            badges.append([
                self.bot.get_emote("welcomerplus"),
                "Welcomer Plus",
                "Has a welcomer plus subscription",
                "3182BC"
            ])
        if userinfo['m']['pro']['h']:
            badges.append([
                self.bot.get_emote("welcomerpro"),
                "Welcomer Pro",
                "Has a welcomer pro subscription",
                "FF4507"
            ])
        if userinfo['m']['extended']['h']:
            badges.append([
                self.bot.get_emote("welcomerextended"),
                "Welcomer Extended",
                "Has a welcomer extended subscription",
                "202225"
            ])
        if userinfo['m']['partner']:
            badges.append([
                self.bot.get_emote("welcomerpartner"),
                "Welcomer Partner",
                "Currently a Welcomer partner",
                "2D103F"
            ])
        all_guilds = rockutils.merge(userinfo['g']['g']['m']['c'])
        for guild in all_guilds:
            if guild['owner']['id'] == str(user.id):
                if guild['users'] > 250:
                    badges.append([
                        ":globe_with_meridians:"
                        "Server Owner",
                        f"Owner of server with {guild['users']} members",
                        "202225"
                    ])

        if user.id in self.bot.config['roles']['support']:
            badges.append([
                ":hammer:"
                "Welcomer Support",
                "Official Welcomer support member",
                "202225"
            ])

        if user.id in self.bot.config['roles']['trusted']:
            badges.append([
                ":shield:"
                "Trusted user",
                "User that Welcomer recognises as trustworthy",
                "202225"
            ])

        if user.id in self.bot.config['roles']['admins']:
            badges.append([
                ":wrench:"
                "Welcomer Administrator",
                "Official Welcomer administrator",
                "202225"
            ])

        if user.id in self.bot.config['roles']['developer']:
            badges.append([
                ":gear:"
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
        "logs"
    ]

    for name in caches:
        existingdict(bot.cache, name, {})

    core = WelcomerCore(bot)
    for key in dir(core):
        if not ("on_" in key and key != "on_message_handle"):
            value = getattr(core, key)
            if callable(value) and not "_" in key[0]:
                setattr(bot, key, value)

    bot.remove_command("help")
    bot.add_cog(core)
    setattr(bot, "serialiser", DataSerialiser(bot))
    setattr(bot, "emotes", rockutils.load_json("cfg/emotes.json"))
