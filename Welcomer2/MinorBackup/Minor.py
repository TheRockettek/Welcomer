from DataIO import dataIO
from discord.ext import commands
from datetime import datetime
import asyncio
import discord
import discord.abc
import discord.utils
import datetime
import json
import math
import os
import psutil
import rethinkdb as r
import requests
import sys
import time
import traceback

r.set_loop_type("asyncio")


global bot
global data
global connection
global loadedmodules

loadedmodules = dict()
data = dataIO.load_json("data.json")
token = dataIO.load_json("token.json")['token']
uptime = datetime.now()
handler_ready = False

# Enable affinity
p = psutil.Process()
all_cpus = list(range(psutil.cpu_count()))
p.cpu_affinity(all_cpus)
print(p.cpu_affinity())


# Arguments
args = sys.argv
if len(args) < 4:
    print(f"{args[0]} <shard count> <cluster count> <cluster id> <test mode>")
    sys.exit()


# Argument Handling
usesharding = True
if len(args) > 4:
    if args[4] == "True":
        usesharding = False
        token = dataIO.load_json("token.json")['debug_token']
        print("Debug Mode Enabled :)")


shard_count = int(sys.argv[1])
cluster_count = int(sys.argv[2])
cluster_id = int(sys.argv[3])

if (shard_count % cluster_count) != 0:
    while (shard_count % cluster_count) != 0:
        shard_count += 1
    print(f"Changed shard count to {str(shard_count)}")


step = shard_count/cluster_count
cluster_id -= 1
start = step * cluster_id
end = start + step

ushards = list(range(int(start), int(end)))

# Bot Initialization
if usesharding:
    bot = commands.AutoShardedBot(command_prefix="^^", pm_help=True, shard_ids=ushards,
                                  shard_count=shard_count, activity=discord.Game(name="Starting up bot..."))
else:
    print("No Sharding Activated")
    bot = commands.AutoShardedBot(command_prefix="^^")

setattr(bot, "GGL_KEY", "")

setattr(bot, "data", data)
setattr(bot, "loaded_modules", loadedmodules)

setattr(bot, "TEST_MODE", not usesharding)
setattr(bot, "CLUSTER_COUNT", cluster_count)
setattr(bot, "CLUSTER_ID", cluster_id)
setattr(bot, "SHARD_COUNT", shard_count)
setattr(bot, "SHARD_ID", ushards)

setattr(bot, "SyncHandler_Errors", 0)
setattr(bot, "HookActive", False)


def merge(sets):
    new = dict()
    for index, dicts in sets.items():
        for i, k in dicts.items():
            new[i] = k
    return new


def sendWebhookMessage(message, webhookurl=""):
    return requests.post(webhookurl, headers={'Content-Type': 'application/json'}, data=json.dumps({"content": message}))


# Custom LIB

class ModuleManager():

    def __init__(self, bot):
        self.bot = bot

    def load(self, module):
        ts = datetime.now()
        try:
            self.bot.load_extension(f"Modules.{module}")
            te = datetime.now()
            tl = te - ts
            self.bot.loaded_modules[module] = True
            return True, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            return False, str(e)

    def unload(self, module):
        ts = datetime.now()
        try:
            self.bot.unload_extension(f"Modules.{module}")
            te = datetime.now()
            tl = te - ts
            if module in self.bot.loaded_modules:
                del self.bot.loaded_modules[module]
            return True, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            return False, str(e)

    def reload(self, module):
        ts = datetime.now()

        try:
            compile(open("Modules/" + module + ".py", "r").read() +
                    "\n", module + ".py", "exec")

            self.bot.unload_extension(f"Modules.{module}")
            self.bot.load_extension(f"Modules.{module}")

            self.bot.loaded_modules[module] = True
            te = datetime.now()
            tl = te - ts
            return True, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            self.bot.loaded_modules[module] = False
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
            return False, str(e)
        te = datetime.now()
        tl = te - ts
        return False, (tl.seconds * 1000000 + tl.microseconds)/1000

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
                        if work == True:
                            print(f"Loaded {ext} in {str(ttl)}ms")
                            wm += 1
                        else:
                            print(f"Failed to load {ext}: {str(ttl)}")
                            bm += 1
            te = datetime.now()
            tl = te - ts
            print(
                f"Loaded {wm+bm} modules in {(tl.seconds * 1000000 + tl.microseconds)/1000}ms")
            return True, wm, bm, (tl.seconds * 1000000 + tl.microseconds)/1000
        except Exception as e:
            print(str(e))
            return False, str(e), 0, 0


setattr(bot, "modules", ModuleManager(bot))
bot.modules.load("Modules.Init")


@bot.event
async def on_message(message):

    if message.author.bot:
        return
    if not bot.is_ready():
        return

    await bot.process_commands(message)

setattr(bot, "queue", dict())
setattr(bot, "skips", dict())
setattr(bot, "active", list())
setattr(bot, "modules", ModuleManager(bot))
setattr(bot, "uptime", uptime)
setattr(bot, "mention", "143090142360371200")

bot.modules.reloadall()

if not bot.TEST_MODE:
    sendWebhookMessage(message=f":white_small_square: | Restarting cluster **{str(bot.CLUSTER_ID)}**...",
                       webhookurl="")

print(f"Wait time: {str(5*start)}")
time.sleep(5*start)


@bot.event
async def on_ready():
    if bot.HookActive == False:
        setattr(bot, "HookActive", True)
        i = True
        while True:
            try:
                i = not i
                await bot.cogs['SyncHandler'].cpre(i)
            except Exception as e:
                bot.SyncHandler_Errors += 1
                if bot.SyncHandler_Errors >= 300:
                    bot.modules.reload("Init")
                print(e)
            await asyncio.sleep(30)
bot.run(token)
