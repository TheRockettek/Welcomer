import datadog, psutil, datetime, asyncio, requests, json
from datadog import statsd

def updateServers(self):
    content = {"Authorization" : "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjE0MzA5MDE0MjM2MDM3MTIwMCIsImlhdCI6MTUwMDEzNTQzN30.FgI45a92nCctayr6Wi7YtfIINX97f8Q2yvcLHKNqL1I","Content-Type" : "application/json"}
    data = {"server_count" : len(self.bot.guilds)}
    url = "https://discordbots.org/api/bots/330416853971107840/stats"
    requests.post(url,data=json.dumps(data),headers=content)

class DataDog:
    def __init__(self, bot):
        self.bot = bot
        self.tags = []
        self.task = self.bot.loop.create_task(self.loop_task())
        datadog.initialize(api_key="7067aba41e88ceee45f3b9a79a1ddc57",interval=5)

    def __unload(self):
        self.task.cancel()

    def send_all(self):
        self.send_guilds()
        self.send_channels()
        self.send_members()
        self.send_uptime()
        self.send_shards()
        self.send_cpu()
        self.send_ram()

    def send_cpu(self):
        cpu_p = psutil.cpu_percent(interval=None, percpu=True)
        cpu_usage = sum(cpu_p) / len(cpu_p)
        statsd.gauge('bot.cpu', cpu_usage, tags=self.tags)

    def send_ram(self):
        mem_v = psutil.virtual_memory()
        statsd.gauge('bot.ram', mem_v, tags=self.tags)

    def send_uptime(self):
        now = datetime.datetime.now()
        uptime = (now - self.bot.uptime).total_seconds()
        statsd.gauge('bot.uptime', uptime, tags=self.tags)

    def send_shards(self):
        shards = self.bot.shard_count
        statsd.gauge('bot.shards', shards, tags=self.tags)

    def send_guilds(self):
        guilds = len(self.bot.guilds)
        statsd.gauge('bot.guilds', guilds, tags=self.tags)
        updateServers(self)

    def send_channels(self):
        text_channel = 0
        for guild in self.bot.guilds:
            for channel in guild.channels:
                text_channel += 1
        text_channels = text_channel
        statsd.gauge('bot.channels', text_channels,
                    tags=[*self.tags, 'channel_type:text'])

    def send_members(self):
        members = list(self.bot.get_all_members())
        unique = set(m.id for m in members)
        statsd.gauge('bot.members', len(members), tags=self.tags)
        statsd.gauge('bot.unique_members', len(unique), tags=self.tags)

    def notbot(self, channel):
        return sum(m != self.bot.user for m in channel.voice_members)

    async def loop_task(self):
        await self.bot.wait_until_ready()
        self.tags = ['application:welcomer',
                    'bot_id:' + str(self.bot.user.id),
                    'bot_name:' + self.bot.user.name]
        self.send_all()
        await asyncio.sleep(5)
        if self is self.bot.get_cog('DataDog'):
            self.task = self.bot.loop.create_task(self.loop_task())


    async def on_channel_create(self, channel):
        self.send_channels()

    async def on_channel_delete(self, channel):
        self.send_channels()

    async def on_member_join(self, member):
        self.send_members()

    async def on_member_remove(self, member):
        self.send_members()

    async def on_guild_join(self, guild):
        statsd.event(tags=self.tags, title='Joined ' + guild.name,text="Server has " + str(len(guild.members)) + " users")
        self.send_guilds()

    async def on_guild_remove(self,guild):
        statsd.event(tags=self.tags, title='Left ' + guild.name,text="Server had " + str(len(guild.members)) + " users")
        self.send_guilds()

    async def on_ready(self):
        self.send_all()

    async def on_resume(self):
        self.send_all()

    async def on_message(self, message):
        statsd.increment('bot.messages', tags=self.tags)

    async def on_command(self,ctx):
        statsd.increment('bot.commands',tags=[*self.tags,'command_name:' + str(ctx.command),'cog_name:' + type(ctx.cog).__name__])

def setup(bot):
    bot.add_cog(DataDog(bot))