#et8NS4FCvw

import asyncio, discord, time, os, shutil, requests, json, psutil, math, sys, traceback
from datetime import datetime
from discord.ext import commands
from DataIO import dataIO
from PIL import Image
import logging

discord_logger = logging.getLogger('discord')
discord_logger.setLevel(logging.CRITICAL)
log = logging.getLogger("boobs")
log.setLevel(logging.INFO)

from pympler.tracker import SummaryTracker
tracker = SummaryTracker()

print(sys.argv)
ushards = list()
start = int(sys.argv[1])
end = int(sys.argv[2])
for i in range(start,end):
    ushards.append(i)
print(ushards)

global ready
ready = False


def sendWebhookMessage(webhookurl, message):
    print({"content": message})
    return requests.post(webhookurl, headers = {'Content-Type': 'application/json'}, data=json.dumps({"content": message}))

p = psutil.Process() 
all_cpus = list(range(psutil.cpu_count()))
p.cpu_affinity(all_cpus) 
print(p.cpu_affinity())
os.system("taskset -p 0xff %d" % os.getpid())

global bot
print("shards: " + str(ushards))
print("count: " + str(len(ushards)))
print("total: " + str(len(ushards)*int(sys.argv[4])))
bot = commands.AutoShardedBot(command_prefix="+",pm_help=True,shard_ids=ushards,shard_count=len(ushards)*int(sys.argv[4]))
global blockedusers
blockedusers = dataIO.load_json("blacklist.json")
global botStart
botStart = datetime.now()

sys.argv

print(sys.argv)
ttw = (int(sys.argv[2])-int(sys.argv[1])) *5*int(sys.argv[3])
print("Waiting " + str(ttw) + " seconds")
time.sleep(ttw)

setattr(bot, "uptime", botStart)
setattr(bot, "get_user", bot.get_user_info)

def is_owner(ctx):
    return ctx.message.author.id == 143090142360371200 or (str(ctx.message.author.id) in bot.specialRoles['staff'])

global cache
cache = dict()
cache['server_info'] = dict()
cache['user_info'] = dict()
cache['bg'] = dict()
setattr(bot,"ready",ready)
setattr(bot,"cache",cache)

data = {"token":"CTR2KCSRdN","version":3}
url = "https://bans.discordlist.net/api"
try:
    banslist = json.loads(requests.post(url,data=data).text)
    dbanslist = dict()
    for user in banslist:
        id = user[2]
        dbanslist[str(id)] = dict()
        dbanslist[str(id)]['r'] = user[3]
        dbanslist[str(id)]['p'] = user[4]
    setattr(bot,"dbanslist",dbanslist)
except:
    print("Could not retrieve ban list")

globalbans = dataIO.load_json("globalbans.json")
setattr(bot,"globalbans",globalbans)

def setplaying(string):
    nowplaying = string

def exists(variable):
    try:
        variable
        return True
    except:
        return False

def get_server_info(id):
    id = str(id)
    if id in bot.cache['server_info']:
        if "timeout" in bot.cache['server_info'][id]:
            if int(time.time()) < bot.cache['server_info'][id]['timeout']:
                bot.cache['server_info'][id]['timeout'] = int(time.time()) + 600 # Resets timer so it doesnt unload every 5 minutes, but only if not used in 5 minutes
                return bot.cache['server_info'][id]['content']
    bot.cache['server_info'][id] = dict()
    if not os.path.exists("Servers/" + str(id) + ".json"):
        shutil.copy("default_server_config.json","Servers/" + str(id) + ".json")
        print("Added server " + str(id) + " to database")
    try:
        bot.cache['server_info'][id]['content'] = dataIO.load_json("Servers/" + str(id) + ".json")
        bot.cache['server_info'][id]['timeout'] = int(time.time()) + 600
        return bot.cache['server_info'][id]['content']
    except:
        print("CANT LOAD SVR " + id)
setattr(bot,"get_guild_info",get_server_info)

"""
def get_bg(id):
    id = str(id)
    print("Retrieving " + id)
    if id in bot.cache['bg']:
        if "timeout" in bot.cache['bg'][id]:
            if int(time.time()) < bot.cache['bg'][id]['timeout']:
                bot.cache['bg'][id]['timeout'] = int(time.time()) + 600 # Resets timer so it doesnt unload every 5 minutes, but only if not used in 5 minutes
                return bot.cache['bg'][id]['content']
    bot.cache['bg'][id] = dict()
    if not os.path.exists("Images/" + str(id) + ".png"):
        print("/Images/" + id + ".png does not exist.")
        bot.cache['bg'][id]['content'] = Image.open("Images/default.png")
    try:
        bot.cache['bg'][id]['content'] = Image.open("Images/" + id + ".png")
        bot.cache['bg'][id]['timeout'] = int(time.time()) + 600
        print("Loaded /Images/" + id + ".png")
        return bot.cache['bg'][id]['content']
    except Exception as e:
        print("Could not load /Images/" + id + ".png")
        print(e)
        bot.cache['bg'][id]['content'] = Image.open("Images/default.png")
setattr(bot,"get_bg",get_bg)"""

def get_user_info(id):
    return {}
setattr(bot,"get_user_info",get_user_info)

def get_guild_user_info(ctx):
    try:
        guildInfo = get_server_info(str(ctx.message.guild.id))
        userInfo = get_user_info(str(ctx.message.author.id))
        return userInfo,guildInfo
    except:
        return dict(),dict()
setattr(bot,"get_guild_user_info",get_guild_user_info)

def cache_clean():
    t = int(time.time())
    pu = {}
    ps = {}
    pru = 0
    prs = 0
    for id in bot.cache['server_info']:
        try:
            if t >= bot.cache['server_info'][id]['timeout']:
                ps[len(ps)] = id
        except:
            0
    for id in cache['user_info']:
        try:
            if t >= bot.cache['user_info'][id]['timeout']:
                pu[len(pu)] = id
        except:
            0

    for id in ps.values():
        del bot.cache['server_info'][id]
        prs += 1
    for id in pu.values():
        del bot.cache['user_info'][id]
        pru += 1
    print("Pruned " + str(pru) + " users and "+ str(prs) + " guilds")
setattr(bot,"cache_clean",cache_clean)



def reload():
    loadFail = 0
    loadSucc = 0
    for ext in os.listdir("Modules"):
        try:
            bot.unload_extension("Modules." + ext[:-3])
        except:
            0
    for ext in os.listdir("Modules"):
        try:
            if os.path.isfile("Modules/" + ext):
                bot.load_extension("Modules." + ext[:-3])
                loadSucc += 1
        except Exception as e:
            print("Failed to load " + ext + ": " + str(e))
            loadFail += 1
    return loadSucc,loadFail
setattr(bot,"reload",reload)

specialRoles = dataIO.load_json("special_roles.json")
setattr(bot,"specialRoles",specialRoles)

def get_bans_list():
    print("Retrieving ban list")
    data = {"token":"CTR2KCSRdN","version":3}
    url = "https://bans.discordlist.net/api"
    banslist = json.loads(requests.post(url,data=data).text)
    dbanslist = dict()
    for user in banslist:
        id = user[2]
        dbanslist[str(id)] = dict()
        dbanslist[str(id)]['r'] = user[3]
        dbanslist[str(id)]['p'] = user[4]
    bot.dbanslist = dbanslist
    print("Done")

customemotes = dict()
setattr(bot,"customemotes",customemotes)

@asyncio.coroutine
async def get_emote_list(id):
    emojilist = bot.get_guild(id).emojis
    for emoji in emojilist:
        bot.customemotes[emoji.name] = str(emoji.id)

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
        for channel in guild.channels:
            channels += 1
    ram = psutil.virtual_memory()
    cpup = psutil.cpu_percent(interval=None, percpu=True)
    cpu = sum(cpup) / len(cpup)
    version = discord.__version__
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
setattr(bot,"botinfo",bot_info)

@bot.event
async def on_ready():
    globals()['ready'] = True
    bot.ready = True
    sendWebhookMessage("","Cluster **" + str(sys.argv[3]) + "**: Im ready!")
    taskEnd = datetime.now()
    try:
        await get_emote_list(341685098468343822)
    except:
        0
    try:
        taskLength = taskEnd - botStart
        print("Loaded in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
        sendWebhookMessage("","Cluster **" + str(sys.argv[3]) + "**: Loaded in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
        bot_info()
    except:
        0
    while True:
        try:
            get_bans_list()
        except:
            0
        for i in range(0,10):
            try:
                await bot.get_channel(364066649558745099).send(embed=bot_info())
            except:
                0
            await bot.change_presence(game=discord.Game(name="+help | With " + str(len(bot.guilds)) + " servers"))
            await asyncio.sleep(30)
            members = bot.get_all_members()
            await bot.change_presence(game=discord.Game(name="+settings | With " + str(len(set(m.id for m in members))) + " members"))
            await asyncio.sleep(30)
            cache_clean()

@bot.event
async def on_guild_join(server):
    setplaying("with " + str(len(bot.guilds)))

@bot.event
async def on_guild_remove(server):
    setplaying("with " + str(len(bot.guilds)))

@bot.event
async def on_message(message):
    if not bot.is_ready() or message.author.bot:
        return
    allow = True
    if str(message.author.id) in blockedusers:
        allow = False

    try:
        guildInfo = get_server_info(str(message.guild.id))
        prefix = guildInfo['bot-prefix']
        if len(message.mentions) > 0:
            if message.mentions[0].id == 143090142360371200:
                print("\"" + message.content + "\"")
            if message.content == "<@!330416853971107840>":
                await ctx.send("My prefix is " + str(prefix))
                return
        if message.content[0:len(prefix)] != prefix:
            allow = False
        else:
            message.content = "+" + message.content[len(prefix):]
        if message.content[0:len("<@330416853971107840> ")] == "<@330416853971107840> ":
            message.content = "+" + message.content[len("<@330416853971107840> "):]
            allow = True
    except:
        0
    if allow == False:
        return
    try:
        if guildInfo['channel-blacklist']['enable'] == True:
            if str(message.channel.id) in guildInfo['channel-blacklist']['channels']:
                print(message.channel.name + " is in blacklist")
                allow = False
        if guildInfo['channel-whitelist']['enable'] == True:
            if not str(message.channel.id) in guildInfo['channel-whitelist']['channels']:
                print(message.channel.name + " is not on whitelist")
                allow = False
    except:
        0

    if message.author.id == 143090142360371200:
        allow = True
        print("This is rock")

    if allow == True:
        try:
            print(message.guild.name + " | " + message.author.name + " | " + message.content)
        except:
            print("DM | " + message.author.name + " | " + message.content)
        if bot.is_ready():
            await bot.process_commands(message)
        return

"""
@bot.event
async def on_command_error(ctx, exception):
    0

@bot.event
async def on_error(err):
    print(err)"""

class Debug:

    def __init__(self,bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def botinfo(self,ctx):
        await ctx.send(embed=self.bot.botinfo())

    @commands.group(pass_context=True)
    async def modules(self,ctx):
        guildInfo = get_server_info(str(ctx.message.guild.id))
        if is_owner(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(guildInfo['bot-prefix'] + "modules <load/unload/reload/reloadall/list> [moduleName]")

    @commands.command()
    async def debug(self, ctx):
        tracker.print_diff()

    @modules.command(pass_context=True)
    async def load(self,ctx,moduleName : str):
        if is_owner(ctx):
            taskStart = datetime.now()
            try:
                bot.load_extension("Modules." + moduleName)
                taskEnd = datetime.now()
                taskLength = taskEnd - taskStart
                embed = discord.Embed(description="Task completed in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
                await ctx.send(embed=embed)
            except Exception as e:
                embed = discord.Embed(description="Task failed.\n``` " + str(e) + " ```")
                await ctx.send(embed=embed)

    @modules.command(pass_context=True)
    async def unload(self,ctx,moduleName : str):
        if is_owner(ctx):
            taskStart = datetime.now()
            try:
                bot.unload_extension("Modules." + moduleName)
                taskEnd = datetime.now()
                taskLength = taskEnd - taskStart
                embed = discord.Embed(description="Task completed in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
            except Exception as e:
                embed = discord.Embed(description="Task failed.\n``` " + str(e) + " ```")
                await ctx.send(embed=embed)

    @modules.command(pass_context=True)
    async def reload(self,ctx,moduleName : str):
        if is_owner(ctx):
            taskStart = datetime.now()
            try:
                bot.unload_extension("Modules." + moduleName)
            except:
                0
            try:
                bot.load_extension("Modules." + moduleName)
                taskEnd = datetime.now()
                taskLength = taskEnd - taskStart
                embed = discord.Embed(description="Task completed in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
                await ctx.send(embed=embed)
            except Exception as ex:
                embed = discord.Embed(description="Task failed.\n``` " + str(ex) + " ```")
                print(''.join(traceback.format_exception(etype=type(ex), value=ex, tb=ex.__traceback__)))
                await ctx.send(embed=embed)

    @modules.command(pass_context=True)
    async def reloadall(self,ctx):
        if is_owner(ctx):
            taskStart = datetime.now()
            loadSucc,loadFail = reload()
            taskEnd = datetime.now()
            taskLength = taskEnd - taskStart
            embed = discord.Embed(description="Task completed in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.\nLoaded succesfully: " + str(loadSucc) + "\nLoad failed: " + str(loadFail))
            await ctx.send(embed=embed)

    @modules.command(pass_context=True)
    async def list(self,ctx):
        if is_owner(ctx):
            list = ""
            modules = 0
            for ext in os.listdir("Modules"):
                if os.path.isfile("Modules/" + ext):
                    list = list + " - " + ext + "\n"
                    modules += 1
            embed = discord.Embed(description="Found " + str(modules) + " modules.\n" + list + "")
            await ctx.send(embed=embed)

    @commands.group(pass_context=True)
    async def blacklist(self,ctx):
        guildInfo = get_server_info(str(ctx.message.guild.id))
        if is_owner(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(guildInfo['bot-prefix'] + "blacklist <add/remove/check> <id>")

    @blacklist.command(pass_context=True)
    async def add(self,ctx,id : str):
        if is_owner(ctx):
            if not id in blockedusers:
                blockedusers[id] = True
                dataIO.save_json("blacklist.json",blockedusers)

    @blacklist.command(pass_context=True)
    async def remove(self,ctx,id : str):
        if is_owner(ctx):
            if id in blockedusers:
                del blockedusers[id]
                dataIO.save_json("blacklist.json",blockedusers)

    @commands.group(pass_context=True)
    async def specialroles(self,ctx):
        guildInfo = get_server_info(str(ctx.message.guild.id))
        if is_owner(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(guildInfo['bot-prefix'] + "specialroles <addsupport/removesupport/addtrusted/removetrusted/adddonators/removedonators/reload> <id>")

    @specialroles.command(pass_context=True)
    async def addsupport(self,ctx,id : str):
        if is_owner(ctx):
            if not id in bot.specialRoles['staff']:
                bot.specialRoles['staff'][id] = True
                dataIO.save_json("special_roles.json",bot.specialRoles)
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @specialroles.command(pass_context=True)
    async def removesupport(self,ctx,id : str):
        if is_owner(ctx):
            if id in bot.specialRoles['staff']:
                del bot.specialRoles['staff'][id]
                dataIO.save_json("special_roles.json",bot.specialRoles)
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @specialroles.command(pass_context=True)
    async def addtrusted(self,ctx,id : str):
        if is_owner(ctx):
            if not id in bot.specialRoles['trusted']:
                bot.specialRoles['trusted'][id] = True
                dataIO.save_json("special_roles.json",bot.specialRoles)
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @specialroles.command(pass_context=True)
    async def removetrusted(self,ctx,id : str):
        if is_owner(ctx):
            if id in bot.specialRoles['trusted']:
                del bot.specialRoles['trusted'][id]
                dataIO.save_json("special_roles.json",bot.specialRoles)
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @specialroles.command(pass_context=True)
    async def adddonators(self,ctx,id : str):
        if is_owner(ctx):
            if not id in bot.specialRoles['donators']:
                bot.specialRoles['donators'][id] = True
                dataIO.save_json("special_roles.json",bot.specialRoles)
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @specialroles.command(pass_context=True)
    async def removedonators(self,ctx,id : str):
        if is_owner(ctx):
            if id in bot.specialRoles['donators']:
                del bot.specialRoles['donators'][id]
                dataIO.save_json("special_roles.json",bot.specialRoles)
                await ctx.message.add_reaction("\N{WHITE HEAVY CHECK MARK}")

    @specialroles.command(name="reload",pass_context=True)
    async def specialrolesreload(self,ctx):
        if is_owner(ctx):
            bot.specialRoles = dataIO.load_json("special_roles.json")

bot.add_cog(Debug(bot))

for ext in os.listdir("Modules"):
    try:
        if os.path.isfile("Modules/" + ext):
            bot.load_extension("Modules." + ext[:-3])
            print("Loaded " + ext)
    except Exception as e:
        print("Failed to load " + ext + ": " + str(e))

print(sendWebhookMessage("","Cluster **" + str(sys.argv[3]) + "**: Restarting"))
print("Starting...")
bot.run("rockstoltoken")
