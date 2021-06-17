import asyncio, discord, time, os, shutil, requests
from datetime import datetime
from discord.ext import commands
from DataIO import dataIO

global bot
bot = commands.AutoShardedBot(command_prefix="+")
global blockedusers
blockedusers = dataIO.load_json("blacklist.json")
global botStart
botStart = datetime.now()

setattr(bot, "uptime", botStart)
setattr(bot, "get_user", bot.get_user_info)

def is_owner(ctx):
    return ctx.message.author.id == 143090142360371200



global cache
cache = dict()
cache['server_info'] = dict()
cache['user_info'] = dict()
setattr(bot,"cache",cache)

data = {"token":""}
url = "https://bans.discordlist.net/api"
dbanslist = requests.post(url,data=data).text
setattr(bot,"dbanslist",dbanslist)

def exists(variable):
    try:
        variable
        return True
    except:
        return False

def get_server_info(id):
    id = str(id)
    if id in bot.cache['server_info']:
        if int(time.time()) < bot.cache['server_info'][id]['timeout']:
            bot.cache['server_info'][id]['timeout'] = int(time.time()) + 600 # Resets timer so it doesnt unload every 5 minutes, but only if not used in 5 minutes
            return bot.cache['server_info'][id]['content']
    bot.cache['server_info'][id] = dict()
    if not os.path.exists("Servers/" + str(id) + ".json"):
        shutil.copy("default_server_config.json","Servers/" + str(id) + ".json")
        print("Added server " + str(id) + " to database")
    bot.cache['server_info'][id]['content'] = dataIO.load_json("Servers/" + str(id) + ".json")
    bot.cache['server_info'][id]['timeout'] = int(time.time()) + 600
    return bot.cache['server_info'][id]['content']
setattr(bot,"get_guild_info",get_server_info)

def get_user_info(id):
    id = str(id)
    if id in bot.cache['user_info']:
        if int(time.time()) < bot.cache['user_info'][id]['timeout']:
            bot.cache['user_info'][id]['timeout'] = int(time.time()) + 300 # Resets timer so it doesnt unload every 5 minutes, but only if not used in 5 minutes
            return bot.cache['user_info'][id]['content']
    bot.cache['user_info'][id] = dict()
    if not os.path.exists("Members/" + str(id) + ".json"):
        shutil.copy("default_member_config.json","Members/" + str(id) + ".json")
        print("Added user " + str(id) + " to database")
    bot.cache['user_info'][id]['content'] = dataIO.load_json("Members/" + str(id) + ".json")
    bot.cache['user_info'][id]['timeout'] = int(time.time()) + 300
    return bot.cache['user_info'][id]['content']
setattr(bot,"get_user_info",get_user_info)

def get_guild_user_info(ctx):
    guildInfo = get_server_info(str(ctx.message.guild.id))
    userInfo = get_user_info(str(ctx.message.author.id))
    return userInfo,guildInfo
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
    data = {"token":""}
    url = "https://bans.discordlist.net/api"
    bot.dbanslist = requests.post(url,data=data).text

customemotes = dict()
setattr(bot,"customemotes",customemotes)

@asyncio.coroutine
async def get_emote_list(id):
    emojilist = bot.get_guild(id).emojis
    for emoji in emojilist:
        bot.customemotes[emoji.name] = str(emoji.id)

@bot.event
async def on_ready():
    taskEnd = datetime.now()
    cache_clean()
    get_bans_list()
    await get_emote_list(341685098468343822)
    taskLength = taskEnd - botStart
    print("Loaded in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
    await bot.change_presence(game=discord.Game(name="Bot is broke atm"))
    while True:
        await asyncio.sleep(60)
        cache_clean()
        get_bans_list()

@bot.event
async def on_message(message):
    if str(message.author.id) in blockedusers:
        return
    try:
        guildInfo = get_server_info(str(message.guild.id))
        if guildInfo['channel-blacklist']['enable'] == True:
            if not str(message.channel.id) in guildInfo['channel-blacklist']['channels']:
                return
        if guildInfo['channel-whitelist']['enable'] == True:
            if str(message.channel.id) in guildInfo['channel-blacklist']['channels']:
                return
        prefix = guildInfo['bot-prefix']
        if message.content[0:len(prefix)] == prefix:
            message.content = "+" + message.content[len(prefix):]
            print(message.guild.name + " | " + message.author.name + " | " + message.content)
    except:
        0
    await bot.process_commands(message)

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

    @commands.group(pass_context=True)
    async def modules(self,ctx):
        guildInfo = get_server_info(str(ctx.message.guild.id))
        if is_owner(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(guildInfo['bot-prefix'] + "modules <load/unload/reload/reloadall/list> [moduleName]")

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
            except Exception as e:
                embed = discord.Embed(description="Task failed.\n``` " + str(e) + " ```")
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