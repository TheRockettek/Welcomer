import asyncio
import discord
import os
import random
import time
import math
import sys
import psutil
import traceback
from datetime import datetime
from rockutils import rockutils
from collections import Counter


def canint(val):
    try:
        int(val)
        return True
    except ValueError:
        return False


async def exit(self, opcode, args):
    if args == 0:
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 5})
        rockutils.prefix_print("Received job to terminate")
        os._exit(100)
    elif args == 1:
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 3})
        rockutils.prefix_print("Received job to hang")
        os._exit(102)
    elif args == 2:
        await self.push_ipc({"o": "STATUS_UPDATE", "d": 4})
        rockutils.prefix_print("Received job to restart")
        os._exit(101)


async def botinfo(self, opcode, args):
    member_list = list(self.bot.get_all_members())
    process = psutil.Process(os.getpid())
    memory = process.memory_info()

    delta = datetime.utcnow() - self.bot.uptime
    minutes = delta.total_seconds() / 60
    total = sum(self.bot.socket_stats.values())
    cpm = total / minutes

    totalmembers = 0
    for guild in self.bot.guilds:
        if hasattr(guild, "member_count") and hasattr(guild, "_member_count"):
            totalmembers += guild.member_count

    return {
        "guilds": len(self.bot.guilds),
        "latency": self.bot.latency,
        "latencies": self.bot.latencies,
        "totalmembers": totalmembers,
        "members": len(member_list),
        "unique": len(set(m.id for m in member_list)),
        "uptime": math.ceil(time.time() - self.bot.init_time),
        "time": time.time(),
        "mbused": math.ceil(memory.rss / 10000) / 100,
        "threads": process.num_threads(),
        "socketstats": [
            dict(self.bot.socket_stats),
            str(total),
            str(int(math.ceil(cpm)))
        ],
        "tasks": len(asyncio.all_tasks()),
        "rl": [s.is_ws_ratelimited() for s in self.bot.shards.values()]
    }


async def datadump(self, opcode, args):
    return {
        "guilds": [
            self.bot.serialiser.guild(g) for g in self.bot.guilds
        ],
        "roles": [
            self.bot.serialiser.roles(g) for g in self.bot.guilds
        ],
        "emojis": [
            self.bot.serialiser.emotes(g) for g in self.bot.guilds
        ],
        "channels": [
            self.bot.serialiser.channels(g) for g in self.bot.guilds
        ],
    }


async def guildcount(self, opcode, args):
    return Counter([datetime.strftime(u.me.joined_at, '%b %Y') for u in self.bot.guilds])


async def heartbeat(self, opcode, args):
    return {
        "latency": self.bot.latency,
        "latencies": self.bot.latencies,
        "time": time.time()
    }


async def change_presence(self, opcode, args):
    try:
        await self.bot.change_presence(activity=discord.Game(args))
    except Exception as e:
        return str(e)
    else:
        return True


async def counters(self, opcode, args):
    return [[
        t.done(),
        t.cancelled(),
        [str(s) for s in t.get_stack()]
    ] for t in asyncio.all_tasks()]


async def ping(self, opcode, args):
    member_list = list(self.bot.get_all_members())

    delta = datetime.utcnow() - self.bot.uptime
    minutes = delta.total_seconds() / 60
    total = sum(self.bot.socket_stats.values())
    cpm = total / minutes

    task_count = len(asyncio.all_tasks())
    task_limit = 1500
    if task_count >= task_limit:
        await rockutils.send_webhook(
            "https://discord.com/api/webhooks/[removed]",
            f"Cluster {self.bot.cluster_id} | Restarting due to surpassing task limit ({task_count} >= {task_limit}) (ext: {len(self.bot.extra_events)})")
        os._exit(1)

    totalmembers = 0
    for guild in self.bot.guilds:
        if hasattr(guild, "member_count") and hasattr(guild, "_member_count"):
            totalmembers += guild.member_count

    return {
        "latency": self.bot.latency,
        "latencies": self.bot.latencies,
        "guilds": len(self.bot.guilds),
        "shards": list(self.bot.shards.keys()),
        "down": len(list(filter(lambda o: o.unavailable, self.bot.guilds))),
        "totalmembers": totalmembers,
        "members": len(member_list),
        "time": time.time(),
        "init": self.bot.init_time,
        "socketstats": [
            dict(self.bot.socket_stats),
            str(total),
            str(int(math.ceil(cpm)))
        ],
    }


async def searchemoji(self, opcode, args):
    emotes = []
    for guild in self.bot.guilds:
        for emoji in guild.emojis:
            if rockutils.regex_text(emoji.name, [args]):
                emotes.append([
                    str(emoji.guild_id),
                    str(emoji.id),
                    emoji.animated,
                    emoji.name
                ])
    return {"success": True, "data": emotes}


async def reloademotes(self, opcode, args):
    return self.bot.reload_data("cfg/emotes.json")


async def reloaddata(self, opcode, args):
    return self.bot.reload_data(args[0], args[1])


async def retrieveemotes(self, opcode, args):
    guild = self.bot.get_guild(args)
    if guild:
        emotes = self.bot.serialiser.emotes(guild)
        return {"success": True, "data": emotes}
    else:
        return {"success": False, "error": "NoSuchGuild"}


async def emotesdump(self, opcode, args):
    guild = self.bot.get_guild(self.bot.config['bot']['emote_server'])
    if guild:
        emotes = self.bot.serialiser.emotes(guild)
        if emotes[0]:
            emotelist = {}

            for emote in emotes:
                emotelist[emote['name']] = emote['str']
            rockutils.save_json("cfg/emotes.json", emotelist)

            await self.bot.push_ipc({"o": "PUSH_OPCODE", "d": ["reloademotes", "", "*"]})

            return {"success": True}
        else:
            return {"success": False, "error": emotes[1]}
    else:
        return {"success": False, "error": "NoGuild"}


async def cachereload(self, opcode, args):
    guild = self.bot.get_guild(int(args))
    if guild:
        guildinfo = await self.bot.get_guild_info(args)
        if guildinfo:
            await self.bot.create_guild_cache(guildinfo, guild=guild, force=True)
            return {"success": True, "cached": True}
        else:
            return {"success": True, "error": "NoGuildInfo"}
    return {"success": True, "error": "NoGuild"}


async def retrieveuser(self, opcode, args):
    user = self.bot.get_user(args)
    if user:
        user_serialiser = self.bot.serialiser.user(user)
        return {"success": True, "data": user_serialiser}
    return {"success": False, "error": "NoUser"}


async def createuser(self, opcode, args):
    user = self.bot.get_user(args)
    if user:
        userinfo = await self.bot.get_user_info(args)
        return {"success": True, "data": userinfo}
    return {"success": False, "error": "NoUser"}


async def reloadguilds(self, opcode, args):
    user = self.bot.get_user(args)
    if user:
        userinfo = await self.bot.get_user_info(args, refer="reloadguilds")
        if userinfo:
            mutual = self.bot.serialiser.mutualguilds(user)
            userinfo['g']['g']['m']['c'][self.bot.cluster_id] = mutual
            userinfo['g']['g']['m']['u'][self.bot.cluster_id] = time.time()
            await self.bot.update_guild_info(user.id, userinfo, refer="reloadguilds")
            return {"success": True, "data": mutual, "updated": True}
        return {"success": True, "data": mutual, "updated": False}
    return {"success": False, "error": "NoUser", "updated": False}

# DONATIONANNOUNCE --  used to send a donation to a user about their donation and also to add it to the donation json
# >> list [donation type, user id]
# << boolean


async def donationannounce(self, opcode, args):
    userid = int(args[0])
    donation = args[1]
    user = self.bot.get_user(userid)
    if user:
        try:
            await user.send(f""":tada: __***Guys, its here***__ :tada:

We have recieved intel that you have donated towards ***Welcomer {donation[0].upper()}{donation[1:]}*** :eyes:

Thank you for supporting the bot and i hope you can help contribute to the bot in the future. As you are a donator you are able to do many cool things such as the custom donator bot which you should be able to find on the page on **https://welcomer.fun/invitedonator**.\n\nDo not forget to **+membership add** your server :)\nIf you have donated for a custom background, please use **+membership addcustombackground** instead""")
        except Exception as e:
            print(e)
        return True
    else:
        return False


async def modulesreloadall(self, opcode, args):
    success, working, breaking, tte = self.bot.modules.reloadall()
    if success:
        return {
            "success": success,
            "loaded": working,
            "failed": breaking,
            "time": tte}
    else:
        return {"success": success, "error": working}


async def modulesreload(self, opcode, args):
    success, tte = self.bot.modules.reload(args)
    if success:
        return {"success": success, "time": tte}
    else:
        return {"success": success, "error": tte}


async def modulesload(self, opcode, args):
    success, tte = self.bot.modules.load(args)
    if success:
        return {"success": success, "time": tte}
    else:
        return {"success": success, "error": tte}


async def modulesunload(self, opcode, args):
    success, tte = self.bot.modules.unload(args)
    if success:
        return {"success": success, "time": tte}
    else:
        return {"success": success, "error": tte}


async def filterguilds(self, opcode, args):
    filter_type = args[0]
    ascending = args[1]
    limit = args[2]
    page = args[3]
    if len(args) > 4:
        threshold = args[4]
    else:
        threshold = 0

    if filter_type < 0 and filter_type > 2:
        filter_type = 2

    if filter_type == 0:
        guilds = sorted(
            self.bot.guilds,
            key=lambda g: g.member_count,
            reverse=not ascending)
    elif filter_type == 1:
        guilds = sorted(
            self.bot.guilds,
            key=lambda g: sum(
                1 if m.bot else 0 for m in g.members),
            reverse=not ascending)
    elif filter_type == 2:
        guilds = sorted(
            self.bot.guilds,
            key=lambda g: random.random(),
            reverse=not ascending)

    if threshold > 0:
        guilds = list(filter(lambda g: g.member_count >= threshold, guilds))

    sorted_guilds = guilds[limit * (page - 1):limit * (page)]
    processed_guilds = []
    for g in sorted_guilds:
        gi = self.bot.serialiser.guild(g)
        processed_guilds.append(gi)

    return {
        "success": True,
        "guilds": processed_guilds,
        "page": page,
        "limit": limit}


async def guildsfind(self, opcode, args):
    print(f"opcode: {opcode}")
    print(f"args: {args}")
    search_type = args[0]
    term = args[1]
    results = []

    if search_type == 0:
        guild = self.bot.get_guild(term)
        if guild:
            results = self.bot.serialiser.guild(guild)
    elif search_type == 1:
        for guild in self.bot.guilds:
            if rockutils.regex_text(guild.name, [term]):
                results.append(self.bot.serialiser.guild(guild))

    return {"success": True, "results": results}


async def guilddetailed(self, opcode, args):
    guild = self.bot.get_guild(args)
    if guild:
        detailed = self.bot.serialiser.guild_detailed(guild)
        return {"success": True, "data": detailed}
    else:
        return {"success": False, "error": "NoSuchGuild"}


async def guildstaff(self, opcode, args):
    guild = self.bot.get_guild(args)
    staff = []
    if guild:
        if guild.id not in self.bot.cache['staff']:
            guild_info = await self.bot.get_guild_info(guild.id, create_cache=False, direct=True)
            if guild_info:
                await self.bot.create_guild_cache(guild_info, guild)

        for staff_id, allow_ping in self.bot.cache['staff'][guild.id]['u']:
            user = self.bot.get_user(int(staff_id))
            if user:
                userinfo = self.bot.serialiser.user(user)
                userinfo['ap'] = allow_ping
            else:
                userinfo = {
                    "name": "",
                    "discriminator": "",
                    "id": str(staff_id),
                    "icon": None
                }
            staff.append(userinfo)
        return {"success": True, "data": staff}
    else:
        return {"success": False, "error": "NoSuchGuild"}


async def borderwallverify(self, opcode, args):
    _guildid = int(args[0])
    _id = args[2]
    guild = self.bot.get_guild(int(args[0]))
    if guild:
        member = guild.get_member(int(args[1]))
        if member:
            if not member.bot and guild.id in self.bot.cache['borderwall'] and \
                    self.bot.cache['borderwall'][guild.id]['e']:
                if self.bot.cache['borderwall'][guild.id]['c']:
                    _bw_channel = guild.get_channel(
                        int(self.bot.cache['borderwall'][guild.id]['c']))
                else:
                    _bw_channel = None

                roles = []
                for roleid in list(
                        self.bot.cache['borderwall'][_guildid]['r']):
                    role = member.guild.get_role(int(roleid))
                    if role:
                        roles.append(role)

                try:
                    if len(roles) > 0:
                        await member.add_roles(*roles)
                except BaseException:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)

                if not self.bot.donator:
                    if member.guild.get_member(498519480985583636):
                        return

                guildinfo = await self.bot.get_guild_info(guild.id)
                await self.bot.cogs['Worker'].execute_welcomer(member, guildinfo, True)

                try:
                    bw_information = await self.bot.get_value("borderwall", _id)
                    # bw_information = await r.table("borderwall").get(_id).run(self.bot.connection)
                    _borderwall_url = f"https://welcomer.fun/borderwall/{_id}"
                    user_ip = bw_information.get("ip", None)
                    message = self.bot.cogs['Worker'].format_message(
                        self.bot.cache['borderwall'][_guildid]['mv'],
                        guild=member.guild,
                        user=member,
                        include_user=True,
                        include_guild=True,
                        extras={
                            "link": _borderwall_url,
                            "ip": user_ip if user_ip else "?"})

                    embed = discord.Embed(
                        colour=self.bot.cache['guilddetails'][guild.id]['ec'],
                        description=message)

                    try:
                        await member.send(embed=embed)
                    except BaseException:
                        exc_info = sys.exc_info()
                        traceback.print_exception(*exc_info)

                    if _bw_channel:
                        try:
                            await _bw_channel.send(embed=embed)
                        except BaseException:
                            try:
                                await _bw_channel.send(message)
                            except BaseException:
                                exc_info = sys.exc_info()
                                traceback.print_exception(*exc_info)
                except BaseException:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)
            return True
    return False


async def guildinvite(self, opcode, args):
    guild = self.bot.get_guild(int(args))
    if guild:
        try:
            channels = sorted(
                list(
                    c for c in guild.channels
                    if isinstance(c, discord.TextChannel)),
                key=lambda o: o.position)
            for channel in channels:
                code = await channel.create_invite(unique=False)
                if code:
                    response = {"success": True, "invite": str(code.id)}
                    break
        except BaseException:
            response = {"success": False, "error": "MissingPermissions"}
    else:
        response = {"success": False, "error": "NoGuild"}
    return response


async def guildstructure(self, opcode, args):
    guild = self.bot.get_guild(args)
    if guild:
        structure = self.bot.serialiser.channels(guild)
        return {"success": True, "data": structure}
    else:
        return {"success": False, "error": "NoSuchGuild"}


async def guildinvites(self, opcode, args):
    guild = self.bot.get_guild(args)
    if guild:
        invites = await self.bot.serialiser.invites(guild)
        if isinstance(invites, list):
            return {"success": invites[0], "error": invites[1]}
        return {"success": True, "data": invites}
    else:
        return {"success": False, "error": "NoSuchGuild"}


async def userfind(self, opcode, args):
    search_type = args[0]
    term = args[1]
    results = []

    if search_type == 0:
        user = self.bot.get_user(term)
        if user:
            results = self.bot.serialiser.user(user)
    elif search_type == 1:
        for user in self.bot.users:
            if rockutils.regex_text(user.name, [term]):
                results.append(self.bot.serialiser.user(user))

    return {"success": True, "results": results}


async def getguildroles(self, opcode, args):
    guild = self.bot.get_guild(int(args))
    if not guild:
        return {"success": False, "error": "NoGuild"}
    roles = self.bot.serialiser.roles(guild)
    return {"success": True, "roles": roles}


async def getguildchannels(self, opcode, args):
    guild = self.bot.get_guild(int(args))
    if not guild:
        return {"success": False, "error": "NoGuild"}
    roles = self.bot.serialiser.channels(guild)
    return {"success": True, "channels": roles}


async def iselevated(self, opcode, args):
    user_id, guild_id = list(map(int, args))
    user = self.bot.get_user(user_id)
    if user:
        _guild = self.bot.get_guild(guild_id)
        if not _guild:
            return {"success": False, "error": "NoGuild"}

        if hasattr(_guild, "chunk"):
            await self.bot.chunk_guild(_guild)

        if not user:
            user = self.bot.get_user(user_id)

        guild_info = await self.bot.get_guild_info(_guild.id, refer="userelevated", direct=True)
        elevated = await self.bot.has_elevation(_guild, guild_info, user) or await self.bot.has_special_permission(user, developer=True, admin=True, support=True)
        return {"success": True, "elevated": elevated}
    return {"success": False, "error": "NoUser"}


async def userelevated(self, opcode, args):
    # [userid, [guilds...]]
    if type(args) == list:
        # print("Fetching user", args[0])
        # user = self.bot.get_user(int(args[0])) or await self.bot.fetch_user(int(args[0]))
        user_id = int(args[0])
        mutual = []
        for guildid in args[1]:
            guild = self.bot.get_guild(int(guildid))
            if guild:
                mutual.append(guild)
    else:
        # print("Fetching user", args)
        # user = self.bot.get_user(int(args)) or await self.bot.fetch_user(int(args))
        user_id = int(args)
        mutual = self.bot.serialiser.mutualguildsid(int(args))

    user = self.bot.get_user(user_id)
    if not user:
        return {"success": False, "error": "NoUser"}

    guilds = []
    nopes = []
    for _guild in mutual:
        elevated = False

        if hasattr(_guild, "chunk"):
            await self.bot.chunk_guild(_guild)

        # if hasattr(_guild, "chunk"):
        #     if not self.bot.chunkcache.get(_guild.id, False) and not _guild.chunked:
        #         rockutils.prefix_print(
        #             f"Chunking {_guild.id}", prefix_colour="light yellow", prefix="IPC:UserElevated")
        #         self.bot.chunkcache[_guild.id] = True
        #         a = time.time()
        #         await _guild.chunk(cache=True)
        #         rockutils.prefix_print(
        #             f"Chunked {_guild.id} in {math.ceil((time.time()-a)*1000)}ms", prefix_colour="light yellow", prefix="IPC:UserElevated")
        #         self.bot.chunkcache[_guild.id] = False

            # if not _guild.chunked:
            #     await _guild.chunk(cache=True)

        # has_elevation(self, guild, guildinfo, user):
        guild_info = await self.bot.get_guild_info(_guild.id, refer="userelevated", direct=True)
        elevated = await self.bot.has_elevation(_guild, guild_info, user) or await self.bot.has_special_permission(user, developer=True, admin=True, support=True)

        guild = self.bot.serialiser.guild(_guild)
        guild['has_elevation'] = elevated
        guilds.append(guild)

    return {"success": True, "mutual": guilds}


async def usermutual(self, opcode, args):
    user = self.bot.get_user(args)
    if user:
        mutual = self.bot.serialiser.mutualguilds(user)
        return {"success": True, "mutual": mutual}
    return {"success": False, "error": "NoUser"}
