import asyncio
import logging
import math
import os
import sys
import time
import traceback
import hashlib
from datetime import datetime

import aiohttp
import discord
import psutil
import asyncpg
from discord.ext import commands
from rockutils import rockutils

logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, filename='discord.log', filemode='a',
                    format='%(asctime)s:%(levelname)s:%(name)s: %(message)s')

logging.getLogger().addHandler(logging.StreamHandler())
# logger.addHandler(handler)


_arg = sys.argv

if len(_arg) == 1:
    rockutils.prefix_print(f"{_arg[0]} <cluster id>")
    exit()

logging.basicConfig(level=logging.DEBUG)

rockutils.prefix_print(
    " _       __     __                              ",
    text_colour="cyan")
rockutils.prefix_print(
    "| |     / /__  / /________  ____ ___  ___  _____",
    text_colour="cyan")
rockutils.prefix_print(
    r"| | /| / / _ \/ / ___/ __ \/ __ `__ \/ _ \/ ___/",
    text_colour="cyan")
rockutils.prefix_print(
    "| |/ |/ /  __/ / /__/ /_/ / / / / / /  __/ /    ",
    text_colour="cyan")
rockutils.prefix_print(
    r"|__/|__/\___/_/\___/\____/_/ /_/ /_/\___/_/     ",
    text_colour="cyan")
rockutils.prefix_print(
    "Made by ImRock#0001 - Ver. 09/05/2021",
    text_colour="light blue")

config = rockutils.load_json("cfg/config.json")
cluster_count = config['bot']['clusters']
cluster_id = _arg[1]

rockutils.prefix_print(
    f"IPC address: {config['ipc']['host']}:{config['ipc']['port']}")
rockutils.prefix_print(
    f"CDN address: {config['cdn']['host']}:{config['cdn']['port']}")

if cluster_id.lower() == "b":
    shard_count = 1
    raw_cluster_id = -1
    cluster_id = "b"

    shard_ids = [0]
    debug = False
elif cluster_id.lower() == "debug":
    shard_count = 1
    raw_cluster_id = -1

    shard_ids = [0]
    debug = True
    rockutils.prefix_print("Using debug mode", text_colour="light blue")
elif cluster_id.lower() == "donator":
    shard_count = 2
    raw_cluster_id = -1
    cluster_id = "donator"

    shard_ids = [0,1]
    debug = False
else:
    shard_count = config['bot']['shards']
    try:
        raw_cluster_id = int(cluster_id)
    except BaseException:
        rockutils.prefix_print(
            f"Invalid cluster id specified. Expected number, donator, debug. Got {cluster_id}",
            prefix_colour="light red",
            text_colour="red")
        exit()

    _step = step = int(shard_count / cluster_count)

    if math.ceil(_step) != _step:
        rockutils.prefix_print(
            f"The shard count ({shard_count}) is not divisiable by the cluster count ({cluster_count})")
        exit()

    shard_ids = list(
        range(
            raw_cluster_id * step,
            ((raw_cluster_id * step) + step)))

    debug = False

rockutils.prefix_print(f"Cluster Count: {cluster_count}")
rockutils.prefix_print(f"Cluster: {cluster_id} ({raw_cluster_id})")
rockutils.prefix_print(f"Shard Count: {shard_count}")
rockutils.prefix_print(
    f"Shard Range: {','.join(map(str,shard_ids))} ({len(shard_ids)})")
rockutils.prefix_print(f"Maximum Guilds: {2500 * len(shard_ids)}")

core_count = psutil.cpu_count()

affinity = [
    (core_count - (cluster_count - raw_cluster_id)) % core_count,
    ((core_count - (cluster_count - raw_cluster_id) - 1) % core_count),
]

# if core_count > cluster_count * 2:
#     affinity = [
#         (core_count - (cluster_count * 2) + (raw_cluster_id * 2)) + 1,
#         (core_count - (cluster_count * 2) + (raw_cluster_id * 2)) + 2]
# elif core_count >= cluster_count:
#     affinity = [(core_count - cluster_count) + raw_cluster_id,
#                 (core_count - raw_cluster_id) + cluster_id + 1]
# else:
#     affinity = list(range(psutil.cpu_count()))

rockutils.prefix_print(f"Affinity: {','.join(map(str,affinity))}")
process = psutil.Process()
process.cpu_affinity(affinity)


async def connect(_debug, _config):
    global connection
    host = config['db']['host']
    db = config['db']['db']
    password = config['db']['password']
    user = config['db']['user']

    rockutils.prefix_print(f"Connecting to DB {user}@{host}")
    try:
        connection = await asyncpg.create_pool(user=user, password=password,
                                               database=db, host=host, max_size=20, command_timeout=30)
    except Exception as e:
        rockutils.prefix_print(
            f"Failed to connect to DB: {e}.",
            prefix_colour="light red",
            text_colour="red")
        exit()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(
    [asyncio.ensure_future(connect(debug, config))]))


class Welcomer(commands.AutoShardedBot):

    def __init__(self, *args, **kwargs):
        kwargs['command_prefix'] = "+"
        super().__init__(*args, **kwargs)

        rockutils.prefix_print("Init", text_colour="light blue")

        self.connection = kwargs.get("connection")
        self.affinity = kwargs.get("affinity")

        self.cluster_id = kwargs.get("cluster_id")
        self.cluster_count = kwargs.get("cluster_count")

        print("shard_ids", self.shard_ids)
        print("shard_count", self.shard_count)

        self.donator = kwargs.get("donator", False)
        self.debug = kwargs.get("testing", False)

        self.ipc_ws = None
        self.ipc_queue = []
        self.cache = {}
        self.jobs = []
        self.config = config
        self.version = config['bot']['version']
        self.init_time = time.time()

        # self.integrated_sync = True
        # if true will process jobs in sync handler

        self.load_extension("modules.core")
        setattr(self, "command_prefix", self.get_prefix)

        try:
            self.load_extension("modules.worker")
        except Exception:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)

        self.sync_handle = self.loop.create_task(self.sync_task())
        self.worker_handle = self.loop.create_task(self.worker_task())

        # self.job_handle = self.loop.create_task(self.job_task())

    async def before_identify_hook(self, shard_id, initial):
        identify_key = f"{hashlib.md5(self.http.token.encode()).hexdigest()}:{shard_id % self.config['bot']['max_concurrency']}:{self.shard_count}"
        domain = f"http://{self.config['ipc']['host']}:{self.config['ipc']['port']}/api/ipc_identify/{identify_key}/{self.cluster_id}/{self.config['ipc']['auth_key']}"
        start = time.time()
    
        rockutils.prefix_print(f"Retrieving identify lock for shard {shard_id}", prefix="IdentifyHook")
        async with aiohttp.ClientSession() as session:
            while True:
                async with session.post(domain) as resp:
                    data = await resp.json()
                    if data['available']:
                        rockutils.prefix_print(f"Retireved identify lock for shard {shard_id} in {math.ceil((time.time()-start)*1000)} ms", prefix="IdentifyHook")
                        break
                    else:
                        rockutils.prefix_print(f"Waiting {data['sleep']} seconds for identify lock for shard {shard_id}", prefix="IdentifyHook")
                        await asyncio.sleep(data['sleep'])


class ModuleManager:

    def __init__(self, bot):
        self.bot = bot

    def load(self, module):
        ts = datetime.now()
        try:
            if f"modules.{module}" not in self.bot.extensions:
                self.bot.load_extension(f"modules.{module}")
            else:
                self.bot.reload_extension(f"modules.{module}")
            te = datetime.now()
            tl = te - ts
            rockutils.prefix_print(
                f"Loaded {module} in {str((tl.seconds * 1000000 + tl.microseconds) / 1000)}ms",
                prefix="Modules", prefix_colour="yellow")
            return True, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except discord.ext.commands.errors.ExtensionNotLoaded:
            return False, ""
        except ModuleNotFoundError:
            return False, ""
        except Exception as e:
            return False, str(e)

    def unload(self, module):
        ts = datetime.now()
        try:
            if f"modules.{module}" in self.bot.extensions:
                self.bot.unload_extension(f"modules.{module}")
            te = datetime.now()
            tl = te - ts
            rockutils.prefix_print(
                f"Loaded {module} in {str((tl.seconds * 1000000 + tl.microseconds) / 1000)}ms",
                prefix="Modules", prefix_colour="yellow")
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

            try:
                self.bot.reload_extension(f"modules.{module}")
            except BaseException:
                try:
                    self.bot.unload_extension(f"modules.{module}")
                except BaseException:
                    pass
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
                        work, _ = self.reload(module)
                        if work:
                            wm.append(module)
                        else:
                            bm.append(module)
            te = datetime.now()
            tl = te - ts
            rockutils.prefix_print(
                f"Loaded {len(wm+bm)} modules in {(tl.seconds * 1000000 + tl.microseconds)/1000}ms",
                prefix="Modules",
                prefix_colour="yellow")
            return True, wm, bm, (tl.seconds * 1000000 +
                                  tl.microseconds) / 1000
        except Exception as e:
            print(str(e))
            return False, str(e), 0, 0


intents = discord.Intents().default()
intents.members = True
intents.typing = False


bot = Welcomer(
    intents=intents,
    chunk_guilds_at_startup=False,

    connection=connection,
    affinity=affinity,
    shard_ids=shard_ids,
    shard_count=shard_count,
    cluster_id=cluster_id,
    cluster_count=cluster_count,
    donator="donator" in cluster_id.lower(),
    debug=cluster_id.lower() == "debug",
    status=discord.Status.online,
    loop=loop,
    pm_help=True,
    heartbeat_timeout=120,  # danny recommends
    max_messages=50
)


@bot.event
async def on_message(message):
    if message.author.bot or not bot.is_ready():
        return

    return await bot.process_message(message)

setattr(bot, "modules", ModuleManager(bot))
bot.modules.load("core")
bot.modules.load("developer")
bot.modules.reloadall()

rockutils.prefix_print(f"Running bot")
bot.run(config['tokens'].get(
    (''.join(i for i in cluster_id if not i.isdigit())).lower(), config['tokens']["main"]))
