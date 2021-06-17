import aiohttp
import asyncio
import discord
import math
import os
import psutil
import sys
import socket
import time
import traceback

import rethinkdb as r
import ujson as json

from datetime import datetime
from discord.ext import commands
from rockutils import rockutils


print("""dddddddddddddddddddddddd[33m[43mhsss/++-//-//:o+oys[0mddddddddddddddddddddddddddd
ddddddddddddddddddd[33m[43mho//..-.--`--`--`-..-..-.://y[0mhddddddddddddddddddddd
dddddddddddddddd[33m[43mhs-.-..-`--`--`-..-..-.--`--`--.::sh[0mdddddddddddddddddd
dddddddddddddd[33m[43ms/..-`--`--`--.-..-..-`--`--`-..-..-`-/y[0mdddddddddddddddd
dddddddddddd[33m[43my:.--`--`--`-..-..-`--`--`-..-..-`--`--`--:h[0mdddddddddddddd
ddddddddddd[33m[43m+`--`-/+[30m[40myddhh+[33m[43m:`--`--`--.-..-.--`--`--`-..-.-o[0mddddddddddddd
ddddddddd[33m[43ms.::.::[30m[40msdddo/yhddo[33m[43m`--`-..-/+[30m[40mhdhds+:[33m[43m`-..-..-`--`-:y[0mddddddddddd
dddddddd[33m[43mo+:-/--[30m[40mohd+[33m[43m`--`[30m[40m:ody[33m[43m-.-..--[30m[40myddhoohhdds[33m[43m.-.--`-+y/[33m[43m-`--y[0mdddddddddd
ddddddd[33m[43my::+::/.::`--`-..-..-`--`-[30m[40m-/s:[33m[43m.-..:[30m[40msddo[33m[43m--`::/hds-..-.h[0mddddddddd
dddddd[33m[43ms:+:/+-//.:--:..-.--`--`--`-..-/+ydhyhdhhyddy+[33m[43m:d+--`--.[0mddddddddd
dddddd[33m[43m/-//-//-/:[31m[41m+yoos[33m[43m:/-`--`-..-..-/hs:`      [31m[41m     -[33m[43mdd/`--`-./[0mdddddddd
ddddd[33m[43m/::./:-/--[31m[41ms+sy+ss+[33m[43myo/o:/+-/+:sh-.:/oo+o/[31m[41m/:-/oyds[33m[43m-:-.-..-.s[0mddddddd
dddd[33m[43mh-.:-.:.-:.[31m[41mss+yo+yooyooy+ss+ssdhhdhsdhoho+hoyh/:/[33m[43m--:.--`--.[0mddddddd
dddd[33m[43m+-.--`--`--/[31m[41myooyooy+ss+ss+yooyydhooy+ss/::-/::/[33m[43m-::.--`--`-.o[0mdddddd
ddd[33m[43mh.--`--`-..--+[31m[41my+oy+ss+yoohdydddhhhhddddhy//--/[33m[43m.::.--`-..-..-:[0mdddddd
ddd[33m[43my-`--.-..-.--.[31m[41mos+ys+yoohd[30m[40mho:--:+o/oo/+::+sdd[33m[43m+::`--.-..-..-`-:h[0mddddd
ddd[33m[43m+-..-..-`--`--`/+[31m[41moyooddy[30m[40m-`+[37m[47mhddddddddddddo.`:[30m[40myhs[33m[43m/:/..-`--`--`-y[0mddddd
ddd[33m[43m:.-`--`--`-..-..--/[31m[41msh[30m[40mds  [37m[47mydddddddddddddddd``[37m[47m:o[30m[40mhd/[33m[43mydy+/.--.-..o[0mddddd
ddd[33m[43m:`--`--`-..-..-`--`-[30m[40mdd[37m[47m-  :hdddddddddddddd/:h+ohd[30m[40md//::s+ys[33m[43m---`+[0mddddd
ddh[33m[43m:-`-..-..-`--`--`-..[30m[40mdd[37m[47m-   `:oshdhddhdy+:. :h::::[30m[40ms+[33m[43mhyhs:.[30m[40mod.[33m[43m---[0mddddd
ddh[33m[43m--..-`--`--`--.-..-.[30m[40msdo[37m[47m          `          :h[30m[40mo.-[33m[43m:.-:.:[30m[40m:-d:[33m[43m.-/[0mddddd
ddd[33m[43ms--`--`--`-..-..-`--.[30m[40mdd[37m[47m-                    od[30m[40m/:[33m[43m.::.:-[30m[40m.::d[33m[43m/.-h[0mddddd
dddd[33m[43my/-`-..-..-`--`--`---[30m[40mhd/[37m[47m                   -[30m[40mh/[33m[43m::.:-[30m[40m.:--[33m[43myy:s[0mddddddd
dddddd[33m[43mhs::.--`--`--`-..-.-[30m[40mohy:[37m[47m              .[30m[40m+yyhyyos/o/[33m[43m/y[0mdddddddddddd
dddddddddd[33m[43mho+/.-..-..-`--`-:+[30m[40mhds+:-.`.`-[30m[40m:++yhhs[33m[43m-.-.-::ohh[0mddddddddddddd
ddddddddddddddd[33m[43mhys+o:::.--.-..::[30m[40mssydyddyhy+[33m[43m::-:o++yyh[0mddddddddddddddddd
ddddddddddddddddddddddddd[33m[43mhdyhhshsshsshyydhh[0mddddddddddddddddddddddddddd""")

arguments = sys.argv

global bot
global config
global connection

try:
    import handling
except Exception as e:
    rockutils.pprint(f"Unable to load Welcomer due to invalid handling with error {str(e)}")

if len(arguments) == 1:
    rockutils.pprint(f"{arguments[0]} <cluster id>")
    os._exit(2)

r.set_loop_type("asyncio")
config = rockutils.load_json("data/bot_data.json")
config['ipc_host'] = socket.gethostbyname(socket.gethostname())
rockutils.pprint(f"IPC Host is {config['ipc_host']}")

if not "sharding" in config:
    rockutils.pprint("Unable to load Welcomer due to invalid config file loated at data/bot_data.json")
    os._exit(2)

cluster_id = int(arguments[1])
cluster_count = config['sharding']['clusters']
shard_count = config['sharding']['shards']

core_count = psutil.cpu_count()
if core_count > cluster_count*2:
    affinity = [(core_count-cluster_count*2+cluster_id*2)+1,(core_count-cluster_count*2+cluster_id*2)+2]
elif core_count > cluster_count:
    affinity = [core_count-cluster_count+cluster_id,core_count-cluster_count+cluster_id+1]
else:
    affinity = list(range(psutil.cpu_count()))
process = psutil.Process()
process.cpu_affinity(affinity)
rockutils.pprint(f"Affinity: {affinity}", prefix="Init", prefix_colour="green", text_colour="light green")

step = int(shard_count/cluster_count)
shards = list(range(cluster_id*step,(cluster_id*step)+10))

rockutils.pprint(f"Total Clusters: {cluster_count}", prefix="Init", prefix_colour="green", text_colour="light green")
rockutils.pprint(f"Cluster: {cluster_id}", prefix="Init", prefix_colour="green", text_colour="light green")
rockutils.pprint(f"Own Shards: {shards[0]}-{shards[-1]}", prefix="Init", prefix_colour="green", text_colour="light green")
rockutils.pprint(f"Own shard count: {len(shards)}", prefix="Init", prefix_colour="green", text_colour="light green")
rockutils.pprint(f"Shard count: {shard_count}", prefix="Init", prefix_colour="green", text_colour="light green")

debug = bool(arguments[2]) if len(arguments) >= 3 else False
if debug:
    rockutils.pprint(f"Using debug mode")

class Welcomer(commands.AutoShardedBot):

    async def on_connect(self):
        async with aiohttp.ClientSession() as session:
            await session.post(f"http://{self.config['ipc_host']}:{self.config['ipc_port']}/api/pushstatus/{self.cluster_id}/3")

    async def on_ready(self):
        async with aiohttp.ClientSession() as session:
            await session.post(f"http://{self.config['ipc_host']}:{self.config['ipc_port']}/api/pushstatus/{self.cluster_id}/2")
    
    async def on_message(self, message):
        print(f"{message.author} {message.guild} {message.content}")

    async def on_shard_ready(self, shard_id):
        pass
    async def sync_task(self):
        rockutils.pprint("Starting sync task", prefix="IPC-Sync")
        while True:
            try:
                session = aiohttp.ClientSession()
                rockutils.pprint("Connecting to websocket", prefix="IPC-Sync")
                async with session.ws_connect(f"http://{self.config['ipc_host']}:{self.config['ipc_port']}/api/slave/{self.cluster_id}") as ws:
                    rockutils.pprint("Connected to websocket", prefix="IPC-Sync")
                    while True:
                        try:
                            jobs = await ws.receive_json(loads=json.loads)
                        except ValueError:
                            pass
                        else:
                            for job in jobs:
                                self.jobs.append(job)
                        await asyncio.sleep(0.05)
            except aiohttp.client_exceptions.ClientConnectionError:
                await session.close()
                rockutils.pprint(f"Unable to connect to IPC on port {self.config['ipc_port']}", prefix="IPC-Sync", prefix_colour="red", text_colour="light red")
                await asyncio.sleep(5)
            except Exception as e:
                await session.close()
                rockutils.pprint(str(e), prefix="IPC-Sync", prefix_colour="red", text_colour="light red")

    async def job_task(self):
        rockutils.pprint("Initializing job handle")
        upd = time.time()
        import handling
        rockutils.pprint("Starting job handle")
        while True:
            async with aiohttp.ClientSession() as session:
                try:
                    if time.time()-upd > 60:
                        try:
                            f = open("handling.py", "r")
                            file_content = f.read()
                            f.close()
                            compile(file_content + "\n", "handling.py", "exec")

                            import handling
                        except:
                            pass

                    donejobs = []
                    for job in self.jobs:
                        rockutils.pprint(job, prefix="IPC-Sync")

                        opcode = job['op']
                        args = job['args']
                        key = job['key']
                        
                        try:
                            if hasattr(handling, opcode):
                                func = getattr(handling,opcode)
                                if func:
                                    result = await func(self, opcode, args)
                            else:
                                rockutils.pprint(f"No such opcode: {opcode}", prefix=">", prefix_colour="red", text_colour="light red")
                                result = "InvalidOpCode"
                        except Exception as e:
                            rockutils.pprint(str(e))
                            result = str(type(e))
                        await session.post(f"http://{self.config['host']}:{self.config['ipc_port']}/api/submit/{key}/{str(self.cluster_id)}", json=result)
                        donejobs.append(job)

                        for job in donejobs:
                            self.jobs.remove(job)

                    await asyncio.sleep(0.05)
                except Exception as e:
                    rockutils.pprint(str(e), prefix="IPC-Job", prefix_colour="red", text_colour="light red")
            await session.close()

    # {
    # "op": "STR",
    # "args": "JSON",
    # "key": "STR",
    # }

    # {
    # "cluster": "INT->STR"
    # }
    # key in url
    # responce in json kwarg

    def __init__(self, *args, **kwargs):
        rockutils.pprint("Init")
        super().__init__(*args, **kwargs)

        # websocket job adding
        self.sync_handle = self.loop.create_task(self.sync_task())
        self.job_handle = self.loop.create_task(self.job_task())

        self.cache = {}
        self.jobs = []
        self.config = config
        self.init_time = time.time()

        self.testing = kwargs.get("testing", False)
        self.affinity = kwargs.get("affinity")
        self.shard_range = kwargs.get("shard_range")
        self.cluster_id = kwargs.get("cluster_id")

if debug:
    bot = Welcomer(
        command_prefix=config['default_prefix'],
        pm_help=True,
        cluster_id=cluster_id,
        shard_range=shard_count,
        affinity=affinity,
        testing=debug,
        activity=discord.Game(name="Starting up bot...")
    )
else:
    bot = Welcomer(
        command_prefix=config['default_prefix'],
        pm_help=True,
        cluster_id=cluster_id,
        shard_ids=shards,
        shard_count=shard_count,
        shard_range=shard_count,
        affinity=affinity,
        testing=debug,
        activity=discord.Game(name="Starting up bot...")
    )

async def connect():
    rethonk = await r.connect(host="localhost", port=28015, db="welcomer4")
    setattr(bot, "connection", rethonk)

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait([asyncio.ensure_future(connect())]))

class ModuleManager:

    def __init__(self, bot):
        self.bot = bot

    def load(self, module):
        ts = datetime.now()
        try:
            self.bot.load_extension(f"modules.{module}")
            te = datetime.now()
            tl = te - ts
            rockutils.pprint(f"Loaded {module} in {str((tl.seconds * 1000000 + tl.microseconds) / 1000)}ms", prefix="Modules-Load", prefix_colour="yellow")
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
            rockutils.pprint(f"Loaded {module} in {str((tl.seconds * 1000000 + tl.microseconds) / 1000)}ms", prefix="Modules-Unload", prefix_colour="yellow")
            return True, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except Exception as e:
            return False, str(e)

    def reload(self, module):
        ts = datetime.now()

        try:
            f = open("Modules/" + module + ".py", "r")
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
        wm = 0
        bm = 0
        try:
            for ext in os.listdir("Modules"):
                if os.path.isfile("Modules/" + ext):
                    if ext[-3:] == ".py":
                        module = ext[:-3]
                        work, ttl = self.reload(module)
                        if work:
                            wm += 1
                        else:
                            bm += 1
            te = datetime.now()
            tl = te - ts
            rockutils.pprint(f"Loaded {wm+bm} modules in {(tl.seconds * 1000000 + tl.microseconds)/1000}ms", prefix="Modules-Reloadall", prefix_colour="yellow")
            return True, wm, bm, (tl.seconds * 1000000 + tl.microseconds) / 1000
        except Exception as e:
            print(str(e))
            return False, str(e), 0, 0

setattr(bot, "modules", ModuleManager(bot))

bot.modules.load("Core")
bot.modules.reloadall()

# @bot.event
# async def on_message(message):
#     pass

tokens = rockutils.load_json("data/tokens.json")
if bot.testing:
    bot.run(tokens['testing'])
else:
    bot.run(tokens['bot'])
