from discord.ext import commands
from rockutils import rockutils, gameretriever
from datetime import datetime

import asyncio
import discord
import math
import time

class Worker:

    def __init__(self, bot):
        self.bot = bot
        self.delay = 10

    async def worker_task(self):
        rockutils.prefix_print(f"Awaiting ready", prefix="Worker Task")
        while not self.bot.is_ready():
            await asyncio.sleep(5)
        rockutils.prefix_print(f"Starting worker", prefix="Worker Task")

        _time = time.time()
        workdata = {}
        while True:
            try:
                workdata = await self.bot.execute_worker(workdata)
            except Exception as e:
                rockutils.prefix_print(str(e), prefix="Worker Task", prefix_colour="light red", text_colour="red")

            await asyncio.sleep(self.delay - workdata['processing'])

    async def handle_stats(self, data, channel=None):
        if not channel:
            channel = self.bot.get_channel(int(data.get('c',0)))
            if not channel:
                return False

        _type = data.get("t", None)
        _text = data.get("f", None)
        _args = data.get("d", None)

        _formatting = {}

        if not _type and not _text:
            return False
        
        if _type in ["mc", "a2s", "yt", "twitter", "steamgroup", "factorio"] and not _args:
            return False

        if _type == "time":
            pass

        if _type == "mc":
            success, data = await gameretriever.minecraft(_args)
            pass

        if _type == "a2s":
            success, data = await gameretriever.a2s(_args)
            pass

        if _type == "youtube":
            success, data = await gameretriever.youtube(_args)
            pass

        if _type == "guild":
            pass

        if _type == "twitter":
            success, data = await gameretriever.twitter(_args)
            pass

        if _type == "steamgroup":
            success, data = await gameretriever.steam_group(_args)
            pass

        if _type == "factorio":
            success, data = await gameretriever.factorio(_args)
            pass

        _text = rockutils.text_format(_text, _formatting, ["[","]"])

        if _text != channel.name:
            try:
                await channel.edit(name=_text)
            except:
                pass
        return True

    async def execute_worker(self, workdata):
        _tstart = time.time()
        
        # stats
        # timeroles
        # analytics saver
        # logs saver
        
        # stats format
        {
            "c": 0,
            "t": "minecraft",
            "d": none,
            "f": ">> {ip}"
        }


        workdata['processing'] = time.time() - _tstart
        if workdata['processing'] > self.delay/2:
            rockutils.prefix_print(f"Work job took {math.ceil(workdata['processing'] * 1000)}ms", prefix="Worker Task", prefix_colour="light red")
        return workdata

def setup(bot):
    worker = Worker(bot)
    setattr(bot, "execute_worker", worker.execute_worker)
    setattr(bot, "worker_task", worker.worker_task)

    bot.add_cog(worker)
