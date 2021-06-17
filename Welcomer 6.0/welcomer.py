import aiohttp
import asyncio
import discord
import os
import math
import psutil
import gettext
import sys
import time
import traceback
import logging

logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger('discord')
# logger.setLevel(logging.DEBUG)
# handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
# handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
# logger.addHandler(handler)

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLookPolicy())
except:
    pass

import rethinkdb as r
import ujson as json

from datetime import datetime
from discord.ext import commands
from rockutils import gameretriever, rockutils

_arg = sys.argv

# rockutils.prefix_print("test", prefix="test 123")
# rockutils.add_lang("en")
# print(rockutils._("Test file %s","en"))
# print(rockutils._("Test file %s"))

if len(_arg) == 1:
    rockutils.prefix_print(f"{_arg[0]} <cluster id>")
    exit()

r.set_loop_type("asyncio")

config = rockutils.load_json("cfg/config.json")

rockutils.prefix_print(f"IPC address: {config['ipc']['host']}:{config['ipc']['port']}")
rockutils.prefix_print(f"CDN address: {config['cdn']['host']}:{config['cdn']['port']}")

cluster_count = config['bot']['clusters']
cluster_id = _arg[1]

if cluster_id.lower() == "debug":
    shard_count = 1
    raw_cluster_id = 0

    shard_range = [1]
    debug = True
    rockutils.prefix_print("Using debug mode", text_colour="light blue")
elif cluster_id.lower() == "donator":
    shard_count = 1
    raw_cluster_id = 0

    shard_range = [1]
    debug = False
else:
    shard_count = config['bot']['shards']
    try:
        raw_cluster_id = int(cluster_id)
    except:
        rockutils.prefix_print(f"Invalid cluster id specified. Expected number, donator, debug. Got {cluster_id}", prefix_colour="light red", text_colour="red")
        exit()

    _step = step = int(shard_count/cluster_count)

    if math.ceil(_step) != _step:
        rockutils.prefix_print(f"The shard count ({shard_count}) is not divisiable by the cluster count ({cluster_count})")
        exit()

    shard_range = list(range(raw_cluster_id * step, ((raw_cluster_id * step) + step)))
    debug = False

rockutils.prefix_print(f"Cluster Count: {cluster_count}")
rockutils.prefix_print(f"Cluster: {cluster_id} ({raw_cluster_id})")
rockutils.prefix_print(f"Shard Count: {shard_count}")
rockutils.prefix_print(f"Shard Range: {','.join(map(str,shard_range))} ({len(shard_range)})")
rockutils.prefix_print(f"Maximum Guilds: {2500 * len(shard_range)}")

core_count = psutil.cpu_count()

if core_count > cluster_count*2:
    affinity = [(core_count-(cluster_count*2)+(raw_cluster_id*2))+1,(core_count-(cluster_count*2)+(raw_cluster_id*2))+2]
elif core_count >= cluster_count:
    affinity = [(core_count - cluster_count) + raw_cluster_id, (core_count - raw_cluster_id) + cluster_id + 1]
else:
    affinity = list(range(psutil.cpu_count()))

rockutils.prefix_print(f"Affinity: {','.join(map(str,affinity))}")
process = psutil.Process()
process.cpu_affinity(affinity)

async def connect(_debug, _config):
    global rethink
    host = config['db']['host']
    port = config['db']['port']
    db = config['db']['table']

    if _debug:
        db += "debug"

    rockutils.prefix_print(f"Connecting to DB {host}:{port}@{db}")
    try:
        rethink = await r.connect(host=host, port=port, db=db)
    except Exception as e:
        rockutils.prefix_print(f"Failed to connect to DB: {e}.", prefix_colour="light red", text_colour="red")
        exit()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([asyncio.ensure_future(connect(debug, config))]))

class Welcomer(commands.AutoShardedBot):

    def __init__(self, *args, **kwargs):
        rockutils.prefix_print("Init", text_colour="light blue")

        self.connection = kwargs.get("connection")

        self.affinity = kwargs.get("affinity")
        self.shard_range = kwargs.get("shard_range")
        self.shard_count = kwargs.get("shard_count")
        self.cluster_id = kwargs.get("cluster_id")
        self.cluster_count = kwargs.get("cluster_count")

        self.donator = kwargs.get("donator", False)
        self.debug = kwargs.get("testing", False)

        self.ipc_ws = None
        self.ipc_queue = []
        self.cache = {}
        self.jobs = []
        self.config = config
        self.init_time = time.time()

        self.integrated_sync = True
        # if true will process jobs in sync handler

        kwargs['command_prefix'] = "+"
        super().__init__(*args, **kwargs)

        self.load_extension("modules.core")
        setattr(self, "command_prefix", self.get_prefix)


        self.load_extension("modules.worker")
        self.sync_handle = self.loop.create_task(self.sync_task())
        self.worker_handle = self.loop.create_task(self.worker_task())

        # self.job_handle = self.loop.create_task(self.job_task())
        
        @self.event
        async def on_message(message):
            return

class ModuleManager:

    def __init__(self, bot):
        self.bot = bot

    def load(self, module):
        ts = datetime.now()
        try:
            self.bot.load_extension(f"modules.{module}")
            te = datetime.now()
            tl = te - ts
            rockutils.prefix_print(f"Loaded {module} in {str((tl.seconds * 1000000 + tl.microseconds) / 1000)}ms", prefix="Modules", prefix_colour="yellow")
            return True, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except Exception as e:
            return False, str(e)

    def unload(self, module):
        ts = datetime.now()
        if module.lower() == 'core':
            return False, "This module is protected"
        try:
            self.bot.unload_extension(f"modules.{module}")
            te = datetime.now()
            tl = te - ts
            rockutils.prefix_print(f"Loaded {module} in {str((tl.seconds * 1000000 + tl.microseconds) / 1000)}ms", prefix="Modules", prefix_colour="yellow")
            return True, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except Exception as e:
            return False, str(e)

    def reload(self, module):
        ts = datetime.now()

        try:
            f = open("modules/" + module + ".py", "r")
            file_content = f.read()
            f.close()
            compile(file_content + "\n", module + ".py", "exec")

            self.bot.unload_extension(f"modules.{module}")
            self.bot.load_extension(f"modules.{module}")

            te = datetime.now()
            tl = te - ts
            return True, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            del exc_info
            return False, str(e)

    def reloadall(self):
        ts = datetime.now()
        wm = []
        bm = []
        try:
            for ext in os.listdir("modules"):
                if os.path.isfile("modules/" + ext):
                    if ext[-3:] == ".py":
                        module = ext[:-3]
                        work, ttl = self.reload(module)
                        if work:
                            wm.append(module)
                        else:
                            bm.append(module)
            te = datetime.now()
            tl = te - ts
            rockutils.prefix_print(f"Loaded {len(wm+bm)} modules in {(tl.seconds * 1000000 + tl.microseconds)/1000}ms", prefix="Modules", prefix_colour="yellow")
            return True, wm, bm, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except Exception as e:
            print(str(e))
            return False, str(e), 0, 0

bot = Welcomer(
    connection = rethink,
    affinity = affinity,
    shard_range = shard_range,
    shard_count = shard_count,
    cluster_id = cluster_id,
    cluster_count = cluster_count,
    donator = cluster_id.lower() == "donator",
    debug = cluster_id.lower() == "debug",

    pm_help=True,
    activity = discord.Game(name = "Getting ready 👌")
)

@bot.event
async def on_message(message):
    if message.author.bot and bot.is_ready():
        return
    class PseudoSelf:
        def __init__(self, bot):
            self.bot = bot
    self = PseudoSelf(bot)
    return await self.bot.process_message(message)


setattr(bot, "modules", ModuleManager(bot))

bot.modules.load("Core")
bot.modules.reloadall()

bot.run(config['tokens'].get(cluster_id.lower(),config['tokens']['main']))