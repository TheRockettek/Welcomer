import aiohttp
import discord
import os
import random
import time
import math
import psutil
from rockutils import rockutils

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
    return {
        "guilds": len(self.bot.guilds),
        "latency": self.bot.latency,
        "latencies": self.bot.latencies,
        "members": len(member_list),
        "unique": len(set(m.id for m in member_list)),
        "uptime": math.ceil(time.time() - self.bot.init_time),
        "time": time.time(),
        "mbused": math.ceil(memory.rss / 10000) / 100,
        "threads": process.num_threads()
    }

async def heartbeat(self, opcode, args):
    return {
        "latency": self.bot.latency,
        "latencies": self.bot.latencies,
        "time": time.time()
    }

async def ping(self, opcode, args):
    return {
        "latency": self.bot.latency,
        "latencies": self.bot.latencies,
        "guilds": len(self.bot.guilds),
        "time": time.time()
    }

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
        if emotes[0] != False:
            emotelist = {}

            for emote in emotes:
                emotelist[emote['name']] = emote['str']
            rockutils.save_json("cfg/emotes.json", emotes)

            await self.bot.push_ipc({"o": "PUSH_OPCODE", "d": ["reloademotes","","*"]})

            return {"success": True}
        else:
            return {"success": False, "error": emotes[1]}
    else:
        return {"success": False, "error": "NoGuild"}

async def cachereload(self, opcode, args):
    guild = self.bot.get_guild(args)
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
        user_serializer = self.bot.serialiser.user(user)
        return {"success": True, "data": user_serializer}
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

async def modulesreloadall(self, opcode, args):
    success, working, breaking, tte = self.bot.modules.reloadall()
    if success:
        return {"success": success, "loaded": working, "failed": breaking, "time": tte}
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
        threshold = 100

    if filter_type >= 0 and filter_type <= 2:
        filter_type = 2

    if filter_type == 0:
        guilds = sorted(self.bot.guilds, key=lambda g: g.member_count, reverse=not ascending)
    elif filter_type == 1:
        guilds = sorted(self.bot.guilds, key=lambda g: sum(1 if m.bot else 0 for m in g.members), reverse=not ascending)
    elif filter_type == 2:
        guilds = sorted(self.bot.guilds, key=lambda g: random.random(), reverse=not ascending)

    sorted_guilds = guilds[limit*(page-1):limit*(page)]
    processed_guilds = []
    for g in sorted_guilds:
        gi = self.bot.serialiser.guild(g)
        processed_guilds.append(gi)
    
    return {"success": True, "guilds": processed_guilds, "page": page, "limit": limit}

async def guildsfind(self, opcode, args):
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
                results.append(self.bot.serializer.guild(guild))
    
    return {"success": True, "results": results}

async def guilddetailed(self, opcode, args):
    guild = self.bot.get_guild(args)
    if guild:
        detailed = self.bot.serialiser.guild_detailed(guild)
        return {"success": True, "data": detailed}
    else:
        return {"success": False, "error": "NoSuchGuild"}

# GUILDSTAFF -- returns a list of staff statuses
# >> id
# << list[success, valid_staff_ids, data] / list[false, error]

async def guildinvite(self, opcode, args):
    guild = self.bot.get_guild(int(args))
    if guild:
        try:
            channels = sorted(list(c for c in guild.channels if type(c) == discord.TextChannel), key=lambda o: o.position)
            for channel in channels:
                code = await channel.create_invite(unique=False)
                if code:
                    response = {"success": True, "invite": code.id}
                    break
        except Exception as e:
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
        if type(invites) == list:
            return {"success": invites[0], "error": invites[1]}
        return {"success": True, "data": invites}
    else:
        return {"success": False, "error": "NoSuchGuild"}

async def userfind(self, opcode, args):
    search_type = args[0]
    term = args[1]
    results = []

    if search_type == 0:
        guild = self.bot.get_user(term)
        if guild:
            results = self.bot.serialiser.guild(guild)
    elif search_type == 1:
        for user in self.bot.users:
            if rockutils.regex_text(user.name, [term]):
                results.append(self.bot.serializer.user(user))

    return {"success": True, "results": results}

async def usermutual(self, opcode, args):
    user = self.bot.get_user(args)
    if user:
        mutual = self.bot.serialiser.mutualguilds(user)
        return {"success": True, "mutual": mutual}
    return {"success": False, "error": "NoUser"}