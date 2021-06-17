import asyncio
import discord
import datetime
import os
import sys
import rethinkdb as r
import traceback
import psutil
import math

r.set_loop_type("asyncio")

from datetime import datetime
from discord.ext import commands
from DataIO import dataIO

args = sys.argv

if len(args) < 4:
    print(args[0] + " <shard count> <cluster count> <cluster id> <test mode>")
    sys.exit()

shard_count = int(sys.argv[1])
cluster_count = int(sys.argv[2])
cluster_id = int(sys.argv[3])

p = psutil.Process() 
all_cpus = list(range(psutil.cpu_count()))
p.cpu_affinity(all_cpus) 
print(p.cpu_affinity())

def getCount(shardC,clusterC,clusterI):
    if shardC % clusterC != 0:
        while shardC % clusterC != 0:
            shardC += 1
        print("Changed shard count to " + str(shardC))
    step = shardC/clusterC
    clusterI -= 1
    start = step * clusterI
    end = start + step
    return start, end

# Config

usesharding = True # False for testing
if len(args) > 4:
    if args[4] == "True":
        usesharding = False

start, end = getCount(shard_count, cluster_count, cluster_id)

global bot
global data
global loadedmodules
global connection

loadedmodules = dict()
data = dataIO.load_json("data.json")

token = dataIO.load_json("token.json")['token']

async def connect():
    globals()['connection'] = await r.connect(host="localhost", port=28015, db="welcomer")

async def attempt():
    try:
        await r.db_create("welcomer").run(connection)
    except Exception as e:
        print(e)

    try:
        await r.db("welcomer").table_create("userinfo").run(connection)
    except Exception as e:
        print(e)

    try:
        await r.db("welcomer").table_create("guildinfo").run(connection)
    except Exception as e:
        print(e)

    try:
        await r.db("welcomer").table_create("punishments").run(connection)
    except Exception as e:
        print(e)

    try:
        await r.db("welcomer").table_create("crosscommunication").run(connection)
    except Exception as e:
        print(e)

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([asyncio.ensure_future(connect())]))
loop.run_until_complete(asyncio.wait([asyncio.ensure_future(attempt())]))

if usesharding == True:
    ushards = list(range(int(start),int(end)))
    print(ushards)
    bot = commands.AutoShardedBot(command_prefix=">",pm_help=True,shard_ids=ushards,shard_count=shard_count)
else:
    print("No Sharding Activated")
    bot = commands.AutoShardedBot(command_prefix="wb>")

botStart = datetime.now()
setattr(bot, "uptime", botStart)

def bot_info():
    servers = 0
    channels = 0
    process = psutil.Process()
    now = datetime.now()
    shards = bot.shard_count
    members = list(bot.get_all_members())
    unique = set(m.id for m in members)
    uptime = (now - bot.uptime).total_seconds()
    for guild in bot.guilds:
        servers += 1
        for _ in guild.channels:
            channels += 1
    ram = psutil.virtual_memory()
    cpup = psutil.cpu_percent(interval=None, percpu=True)
    cpu = sum(cpup) / len(cpup)
    uptime = datetime.utcfromtimestamp(uptime)
    uptimes = "**" + str(int(uptime.day)-1) + "D - " + str(int(uptime.hour)) + " H - " + str(int(uptime.minute)) + " M**"
    message = ""
    message += "**Total Servers** " + str(servers) + "\n"
    message += "**Total Channels** " + str(channels) + "\n"
    message += "**Total Members** " + str(len(members)) + "\n"
    message += "**Unique Members** " + str(len(unique)) + "\n"
    message += "\n"
    message += "**Uptime** " + uptimes + "\n"
    message += "**Total Shards** " + str(shards) + "\n"
    message += "**Ram Usage** " + str(ram.percent) + "%\n"
    message += "**CPU Usage** " + str(cpu) + "%\n"
    message += "**Threads** " + str(process.num_threads()) + "\n"
    message += "**Rewrite Version** " + str(discord.__version__) + "\n"
    message += "\n"
    message += "**Adverage websocket protocol latency** " + str(math.ceil(bot.latency*1000)) + "ms\n"
    for shard in bot.latencies:
        message += "Shard " + str(shard[0]) + " - " + str(math.ceil(shard[1]*1000)) + "ms\n"
    embed = discord.Embed(title="__Bot Info__", description=message)
    return embed

setattr(bot, "botinfo", bot_info)

async def create_user_info(id):
    id = str(id)
    print(f"\033[35m[CREATE] \033[37mCreating data for \033[36mu{id} \033[37m...")
    udata = bot.data['default_configs']['user']
    user_data = udata
    user_data['id'] = id
    await r.table("userinfo").insert(user_data).run(connection)
    data = await r.table("userinfo").get(id).run(connection)
    return data

async def create_guild_info(id):
    id = str(id)
    print(f"\033[35m[CREATE] \033[37mCreating data for \033[36mg{id} \033[37m...")
    sdata = bot.data['default_configs']['server']
    server_data = sdata
    server_data['id'] = id
    await r.table("guildinfo").insert(server_data).run(connection)
    data = await r.table("guildinfo").get(id).run(connection)
    return data

async def get_guild_info(id):
    id = str(id)
    ts = datetime.now()
    data = await r.table("guildinfo").get(id).run(connection)
    if not data:
        data = await create_guild_info(id)
    te = datetime.now()
    tl = te - ts
    if (tl.seconds * 1000000 + tl.microseconds)/1000 > 1000:
        print(f"\033[32m[GET] \033[37mRetrieved \033[36mg{id} \033[37minfo in \033[31m{(tl.seconds * 1000000 + tl.microseconds)/1000}\033[37mms")
    return data

async def get_user_info(id):
    id = str(id)
    ts = datetime.now()
    data = await r.table("userinfo").get(id).run(connection)
    if not data:
        data = await create_user_info(id)
    te = datetime.now()
    tl = te - ts
    if (tl.seconds * 1000000 + tl.microseconds)/1000 > 1000:
        print(f"\033[32m[GET] \033[37mRetrieved \033[36mu{id} \033[37minfo in \033[31m{(tl.seconds * 1000000 + tl.microseconds)/1000}\033[37mms")
    return data

async def get_guild_user_info(self, user, guild):
    guildInfo = self.bot.get_guild_info(guild)
    userInfo = self.bot.get_user_info(guild)
    return userInfo, guildInfo

async def update_guild_info(id,t):
    id = str(id)
    print(f"\033[34m[UPDATE] \033[37mUpdating data for \033[36mg{id} \033[37m...")
    data = await r.table("guildinfo").get(id).update(t).run(connection)
    return data

async def update_user_info(id,t):
    id = str(id)
    print(f"\033[34m[UPDATE] \033[37mUpdating data for \033[36mu{id} \033[37m...")
    data = await r.table("userinfo").get(id).update(t).run(connection)
    return data

async def is_elevated(member,server,super = True):
    serverDetails = await get_guild_info(server.id)
    if member.guild_permissions.manage_guild == True:
        return True
    if member.guild_permissions.ban_members == True:
        return True
    if str(member.id) in data['roles']['admin']:
        if data['roles']['admin'][str(member.id)] == True:
            return True
    if str(member.id) in data['roles']['support'] and super == False:
        if data['roles']['support'][str(member.id)] == True:
            return True
    if str(member.id) in serverDetails['staff']:
        return True
    return False

async def is_operator(member,super = True):
    if str(member.id) in data['roles']['admin']:
        if data['roles']['admin'][str(member.id)]:
            return True
    if str(member.id) in data['roles']['support'] and super == False:
        if data['roles']['support'][str(member.id)]:
            return True
    return False

def update_data():
    return dataIO.save_json("data.json", bot.data)

def reload_data():
    try:
        bot.data = dataIO.load_json("data.json")
        return True
    except:
        return False

async def add_punishment(table):
    await r.table("punishments").insert(table).run(connection)
    data = await r.table("punishments").max().run(connection)
    return data['id']

async def get_punishment(id):
    id
    return await r.table("punishments").get(id).run(connection)

async def has_elevated_roles(self, user, serverid):
    guild = self.bot.get_guild(int(serverid))
    for member in guild.members:
        if member.id == user.id:
            user = member
    for role in user.roles:
        if role.permissions.manage_guild:
            return True
    guildinfo = await self.bot.get_guild_info(serverid)
    if user.id in guildinfo['staff']:
        return True
    return False

setattr(bot, "has_elevated_roles", has_elevated_roles)
setattr(bot, "data", data)
setattr(bot, "loadedmodules", loadedmodules)
setattr(bot, "get_guild_info", get_guild_info)
setattr(bot, "get_user_info", get_user_info)
setattr(bot, "get_guild_user_info", get_guild_user_info)
setattr(bot, "update_guild_info", update_guild_info)
setattr(bot, "update_user_info", update_user_info)
setattr(bot, "is_elevated", is_elevated)
setattr(bot, "is_operator", is_operator)
setattr(bot, "update_data", update_data)
setattr(bot, "reload_data", reload_data)
setattr(bot, "connection", connection)
setattr(bot, "add_punishment", add_punishment)
setattr(bot, "get_punishment", get_punishment)

setattr(bot, "SHARD_COUNT", shard_count)
setattr(bot, "CLUSTER_COUNT", cluster_count)
setattr(bot, "CLUSTER_ID", cluster_id)
setattr(bot, "TEST_MODE", not usesharding)

class modules():

    def __init__(self, bot):
        self.bot = bot

    def load(self, module):
        ts = datetime.now()
        try:
            self.bot.load_extension(f"Modules.{module}")
            te = datetime.now()
            tl = te - ts
            loadedmodules[module] = True
            return True, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            return False, str(e)

    def unload(self, module):
        ts = datetime.now()
        try:
            self.bot.unload_extension(f"Modules.{module}")
            te = datetime.now()
            tl = te - ts
            del loadedmodules[module]
            return True, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            return False, str(e)

    def reload(self, module):
        ts = datetime.now()
        try:
            self.bot.unload_extension(f"Modules.{module}")
            self.bot.load_extension(f"Modules.{module}")
            loadedmodules[module] = True
            te = datetime.now()
            tl = te - ts
            return True, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            loadedmodules[module] = False
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
            return False, str(e)

    def reloadall(self):
        ts = datetime.now()
        wm = 0
        bm = 0
        try:
            for ext in os.listdir("Modules"):
                if os.path.isfile("Modules/" + ext):
                    if ext[-3:] == ".py":
                        module = ext[:-3]
                        work, ttl = self.reload(module)
                        if work:
                            print(f"Loaded {ext} in {str(ttl)}ms")
                            wm += 1
                        else:
                            print(f"Failed to load {ext}: {str(ttl)}")
                            bm += 1
            te = datetime.now()
            tl = te - ts
            print(f"Loaded {wm+bm} modules in {(tl.seconds * 1000000 + tl.microseconds)/1000}ms")
            return True, wm, bm, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            print(str(e))
            return False, str(e), 0, 0

setattr(bot, "modules", modules(bot))

bot.modules.reloadall()

bot.run(token)