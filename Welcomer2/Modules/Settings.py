from DataIO import dataIO
import json, discord, asyncio, psutil, math, requests, traceback
from datetime import datetime, timezone
from discord.ext import commands

def isint(string):
    try:
        int(string)
        return True
    except:
        return False

def between(string, highereql, lowereql):
    if isint(string):
        intager = int(string)
        if intager >= highereql and intager <= lowereql:
            return True
        else:
            return False
    else:
        return False

def validuserid(members, id):
    for member in members:
        if str(member.id) == str(id):
            return True
    return False

def validusername(members, name):
    for member in members:
        if str(member.name) == str(name):
            return True
    return False

def validchannelid(channels, id):
    for channel in channels:
        if str(channel.id) == str(id):
            return True
    return False

def validchannelname(channels, name):
    for channel in channels:
        if str(channel.name) == str(name):
            return True
    return False

class Settings():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def guildlookup(self, ctx):
        """View information on new and banned users on your server"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            embed = discord.Embed(title=":clock1:")
            m = await ctx.send(embed=embed)
            b = 0
            y = 0
            bannedt = ""
            for member in ctx.message.guild.members:
                if str(member.id) in self.bot.dbanslist:
                    b += 1
                    bannedt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td></tr>"
            strb = "<!DOCTYPE html><html><body><link href=\"https://fonts.googleapis.com/css?family=Open+Sans\" rel=\"stylesheet\"><style>*{font-family:'Open Sans',sans-serif}th,td{border-bottom:1px solid #ddd;text-align:center}}</style><h1>Server Lookup: " + str(ctx.guild.name) + " (" + str(ctx.guild.id) + ")</h1><h4>This page will be deleted once you exit +settings</h4><br><br><table style=\"width:100%\">\n<h1>&#128683; Banned users (" + str(b) + ")</h1><tr><th>User#Discriminator</th><th>User ID</th></tr>" + bannedt
            youngt = ""
            for member in ctx.message.guild.members:
                try:
                    joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
                except:
                    joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
                currentDate = datetime.now(timezone.utc)
                currentDate = currentDate.replace(tzinfo=None)
                timeSinceJoining = currentDate - joinDate
                if timeSinceJoining.days < 7:
                    y += 1
                    if timeSinceJoining.days < 1:
                        youngt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td><td><1 day ago</td></tr>"
                    else:
                        if timeSinceJoining.days == 1:
                            youngt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td><td>1 day ago</td></tr>"
                        else:
                            youngt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td><td>" + str(timeSinceJoining.days) + " days ago</td></tr>"
            strb += "</table></br></br><h1>&#9888; New accounts (" + str(y) + ")</h1><table style=\"width:100%\"><tr><th>User#Discriminator</th><th>User ID</th><th>Days old</th></tr>" + youngt
            strb += "</table><br><br>Requested by " + str(ctx.author.name) + "#" + str(ctx.author.discriminator) + " (" + str(ctx.author.id) + ") @ " + str(ctx.message.created_at) + "</body></html>"
            url = 'http://smaller.hol.es/welcomer.php'
            files = {'fileToUpload': ("serverlookup.html", strb)}
            responce = requests.post(url, files=files)
            url = responce.text
            #embed = discord.Embed(title="__Server Lookup__", description="**" + str(blockedc) + "** members on this server are on the [ban list](https://bans.discordlist.net)\n**" + str(youngc) + "** members are less than a week old.\n\n" + blocked + "\n" + young + "\n\n:one: **Back**")
            embed = discord.Embed(title="__Server Lookup__", description="**" + str(b) + "** members are on the [ban list](https://bans.discordlist.net)\n**" + str(y) + "** members are less than a week old.\n\n" + (("[View members](" + str(url) + ")") if "http" in str(url) else ("Sorry i broke whilst uploading :(\n\n```" + str(url) + "```")))
            await m.edit(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.command()
    async def settings(self, ctx):
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            try:
                embed = discord.Embed(title=":clock1: **Queuing lag on purpose, please wait...**")
                m = await ctx.send(embed=embed)
                while True:
                    embed = discord.Embed(title="__Main Menu__", description="\n**:one: General\n:two: Manage Staff Members\n:three: Manage Channel Limiting\n:four: Manage Message Autodeletes\n:five: Manage Logging [WIP]\n:six: Manage Image/Text Welcome Messages [WIP]\n:seven: Manage Leaving Messages [WIP]\n:eight: Manage Autorole [WIP]\n\n:zero: Apply Changes**")
                    await m.edit(embed=embed)
                    r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author) and isint(c.content) and between(c.content,0,9))
                    try:
                        await r.delete()
                    except:
                        0
                    n = int(r.content)
                    if n == 0:
                        await m.delete()
                        try:
                            await r.delete()
                        except:
                            0
                        dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
                        return
                    elif n == 9:
                        raise RandomError
                    elif n == 1:
                        # General
                        while True:
                            embed = discord.Embed(title="__General__", description="\nBot Prefix: " + self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['bot-prefix'] + "\nSupport Server: [invite](https://discord.gg/E6gnrgp)\nVersion: 2.1\n\n**:one: Change Bot Prefix\n:two: Export Server Config\n:three: Prune Invites\n:four: Bot Invite\n:five: Bot Info\n:six: See Text Formatting\n:seven: Server Lookup\n\n:zero: Return To Main Menu**")
                            await m.edit(embed=embed)
                            r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author) and isint(c.content) and between(c.content,0,7))
                            try:
                                await r.delete()
                            except:
                                0
                            n = int(r.content)
                            if n == 0:
                                break
                            elif n == 1:
                                # Change Bot Prefix
                                prefix = self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['bot-prefix']
                                newprefix = self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['bot-prefix']
                                while True:
                                    embed = discord.Embed(title="__Change Bot Prefix__", description="\nCurrent Bot Prefix: " + prefix + "\nNew Bot Prefix: " + newprefix + "\n:one: **Discard Changes\n:two: Save Changes**")
                                    await m.edit(embed=embed)
                                    r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author))
                                    try:
                                        await r.delete()
                                    except:
                                        0
                                    if r.content  == "1":
                                        break
                                    elif r.content == "2":
                                        self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['bot-prefix'] = newprefix
                                        break
                                    else:
                                        newprefix = r.content
                            elif n == 2:
                                # Export Config
                                embed = discord.Embed(title=":clock1:")
                                await m.edit(embed=embed)
                                await r.channel.send(file=discord.File("Servers/" + str(r.guild.id) + ".json",str(r.guild.id) + ".json"))
                                await asyncio.sleep(1)
                            elif n == 3:
                                # Prune Invites
                                while True:
                                    totalInvites = await ctx.message.guild.invites()
                                    message = ""
                                    willdelete = 0
                                    embed = discord.Embed(title=":clock1:")
                                    await m.edit(embed=embed)
                                    for invite in totalInvites:
                                        if invite.uses == 0:
                                            message += invite.id + "\n"
                                            willdelete += 1
                                    embed = discord.Embed(title="__Prune Unused Invites__", description="\nThis will delete " + str(willdelete) + " invite(s):\n" + message + "\n\n**:one: Continue\n:two: Cancel**")
                                    await m.edit(embed=embed)
                                    r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author and isint(c.content)) and between(c.content,1,2))
                                    try:
                                        await r.delete()
                                    except:
                                        0
                                    r = int(r.content)
                                    if r == 1:
                                        deletedinvites = 0
                                        embed = discord.Embed(title=":clock1:")
                                        await m.edit(embed=embed)
                                        for invite in totalInvites:
                                            try:
                                                if invite.uses == 0:
                                                    await invite.delete()
                                            except Exception as e:
                                                print(e)
                                            else:
                                                deletedinvites += 1
                                        embed = discord.Embed(title="__Prune Unused Invites__", description="\n**" + str(deletedinvites) + "** invite(s) have been deleted\n\n:one: Continue")
                                        await m.edit(embed=embed)
                                        r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author and c.content == "1"))
                                        try:
                                            await r.delete()
                                        except:
                                            0
                                        break
                                    elif r == 2:
                                        break
                            elif n == 4:
                                # Bot Invite
                                embed = discord.Embed(title="__Invite Links__", description="**[Bot Invite]()\n[Support Server Invite](FeYfR9b)\n\n:one: Back**")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: (c.content == "1" and c.author == ctx.author))
                                try:
                                    await r.delete()
                                except:
                                    0
                            elif n == 5:
                                #  Bot Info
                                while True:
                                    servers = 0
                                    channels = 0
                                    process = psutil.Process()
                                    now = datetime.now()
                                    shards = self.bot.shard_count
                                    members = list(self.bot.get_all_members())
                                    unique = set(m.id for m in members)
                                    uptime = (now - self.bot.uptime).total_seconds()
                                    for guild in self.bot.guilds:
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
                                    message += "**Adverage websocket protocol latency** " + str(math.ceil(self.bot.latency*1000)) + "ms\n"
                                    for shard in self.bot.latencies:
                                        message += "Shard " + str(shard[0]) + " - " + str(math.ceil(shard[1]*1000)) + "ms\n"
                                    message += "\n"
                                    message += "**Currently Bored ** True\n"
                                    message += "\n**:one: Back\n:two: Refresh**"
                                    embed = discord.Embed(title="__Bot Info__", description=message)
                                    embed.set_thumbnail(url=self.bot.user.avatar_url)
                                    await m.edit(embed=embed)
                                    r = await self.bot.wait_for("message", check=lambda c: ((c.content == "2" or c.content == "1") and c.author == ctx.author) and between(c.content,1,2))
                                    try:
                                        await r.delete()
                                    except:
                                        0
                                    if r.content == "1":
                                        break
                            elif n == 6:
                                # Formatting
                                embed = discord.Embed(title="__Text Formatting__", description="Can be used with Welcomer Image and Text Messages and Welcomer DM Messaging.\n\n**Syntax**\n\n**%SERVER_NAME%** Returns name of server (Discord Server)\n**%SERVER_MEMBER_COUNT%** Returns total users on server (100)\n**%SERVER_COUNT_SUFFIX%** Returns proper ending text for member count (th)\n**%SERVER_OWNER_NAME%** Returns name of owner (Im Rock)\n**%SERVER_OWNER%** Returns name of owner and discriminator (Im Rock#3779)\n**%SERVER_OWNER_ID%** Returns id of owner (143090142360371200)\n**%MEMBER_NAME%** Returns name of new member (iDerp)\n**%MEMBER%** Returns name and discriminator of new member (iDerp#3616)\n**%MEMBER_ID%** Returns id of new user (159074350350336000)\n\n**Tips**\n\nYou can put channel ids also in your message by using\n`<#channelId>`\n\nYou can mention users by using\n`<@memberId>`\n\nOr use in combination with **%MEMBER_ID%** to mention them when they join!\n`<@%MEMBER_ID%>`\n\nHowever mentioning channels or users in images will not display properly so just use their name.\n\n**Examples**\n\n`Welcome <@%MEMBER_ID> to **%SERVER_NAME%** :thumbsup:`\n`Hello there, **%MEMBER%** :wave:! You are the %SERVER_MEMBER_COUNT%%SERVER_COUNT_SUFFIX% user! :tada:`\n`Is it a bird? Is it a plane? No its %MEMBER_NAME% ¯\\_(ツ)_/¯`\n`Welcome to **%SERVER_NAME%**, %MEMBER_NAME%. If you need any assistance you can contact the owner, %SERVER_OWNER%.`\n\n:one: **Back**")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: (c.content == "1" and c.author == ctx.author))
                                try:
                                    await r.delete()
                                except:
                                    0
                            elif n == 7:
                                # Lookup
                                embed = discord.Embed(title=":clock1:")
                                await m.edit(embed=embed)
                                b = 0
                                y = 0
                                bannedt = ""
                                for member in ctx.message.guild.members:
                                    if str(member.id) in self.bot.dbanslist:
                                        b += 1
                                        bannedt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td></tr>"
                                strb = "<!DOCTYPE html><html><body><link href=\"https://fonts.googleapis.com/css?family=Open+Sans\" rel=\"stylesheet\"><style>*{font-family:'Open Sans',sans-serif}th,td{border-bottom:1px solid #ddd;text-align:center}}</style><h1>Server Lookup: " + str(ctx.guild.name) + " (" + str(ctx.guild.id) + ")</h1><h4>This page will be deleted once you exit +settings</h4><br><br><table style=\"width:100%\">\n<h1>&#128683; Banned users (" + str(b) + ")</h1><tr><th>User#Discriminator</th><th>User ID</th></tr>" + bannedt
                                youngt = ""
                                for member in ctx.message.guild.members:
                                    try:
                                        joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
                                    except:
                                        joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
                                    currentDate = datetime.now(timezone.utc)
                                    currentDate = currentDate.replace(tzinfo=None)
                                    timeSinceJoining = currentDate - joinDate
                                    if timeSinceJoining.days < 7:
                                        y += 1
                                        if timeSinceJoining.days < 1:
                                            youngt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td><td><1 day ago</td></tr>"
                                        else:
                                            if timeSinceJoining.days == 1:
                                                youngt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td><td>1 day ago</td></tr>"
                                            else:
                                                youngt += "<tr><td>" + str(member.name) + "#" + str(member.discriminator) + "</td><td>" + str(member.id) + "</td><td>" + str(timeSinceJoining.days) + " days ago</td></tr>"
                                strb += "</table></br></br><h1>&#9888; New accounts (" + str(y) + ")</h1><table style=\"width:100%\"><tr><th>User#Discriminator</th><th>User ID</th><th>Days old</th></tr>" + youngt
                                strb += "</table><br><br>Requested by " + str(ctx.author.name) + "#" + str(ctx.author.discriminator) + " (" + str(ctx.author.id) + ") @ " + str(ctx.message.created_at) + "</body></html>"
                                url = 'http://smaller.hol.es/welcomer.php'
                                files = {'fileToUpload': ("serverlookup.html", strb)}
                                responce = requests.post(url, files=files)
                                url = responce.text
                                #embed = discord.Embed(title="__Server Lookup__", description="**" + str(blockedc) + "** members on this server are on the [ban list](https://bans.discordlist.net)\n**" + str(youngc) + "** members are less than a week old.\n\n" + blocked + "\n" + young + "\n\n:one: **Back**")
                                embed = discord.Embed(title="__Server Lookup__", description="**" + str(b) + "** members are on the [ban list](https://bans.discordlist.net)\n**" + str(y) + "** members are less than a week old.\n\n" + (("[View members](" + str(url) + ")") if "http" in str(url) else ("Sorry i broke whilst uploading :(\n\n```" + str(url) + "```")) + "\n\n**:one: Exit and delete temporary file**")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: (c.content == "1" and c.author == ctx.author))
                                try:
                                    await r.delete()
                                except:
                                    0
                    elif n == 2:
                        message = ""
                        while True:
                            staff = ""
                            for member in guildInfo['staff-members']:
                                if len(staff) > 0:
                                    staff += " , "
                                staff += "<@" + str(member) + ">"
                            if len(staff) == "0":
                                staff = "No staff assigned"
                            embed = discord.Embed(title="__Staff Members__", description=message + staff + "\n\n**:one: Add Staff Member\n:two: Remove Staff Member\n\n:zero: Back**")
                            await m.edit(embed=embed)
                            message = ""
                            r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author and between(c.content, 0, 2))
                            try:
                                await r.delete()
                            except:
                                0
                            n = int(r.content)
                            if n == 0:
                                break
                            elif n == 1:
                                # Add
                                embed = discord.Embed(title="__Add Staff Member__", description="Provide their name, their user id or just mention them")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                try:
                                    await r.delete()
                                except:
                                    0
                                if len(r.mentions) >= 1:
                                    id = r.mentions[0].id
                                else:
                                    if isint(r.content):
                                        if validuserid(ctx.guild.members,int(r.content)):
                                            id = int(r.content)
                                        else:
                                            id = ""
                                    elif validusername(ctx.guild.members,r.content):
                                        for member in ctx.guild.members:
                                            if member.name == r.content:
                                                id = member.id
                                                break
                                    else:
                                        id = ""
                                if id != "":
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['staff-members'][str(id)] = True
                                    message = ":white_check_mark: Added <@" + str(id) + "> to staff members\n\n"
                                else:
                                    message = ":mag_right: Could not that user\n\n"
                            elif n == 2:
                                # Remove
                                embed = discord.Embed(title="__Remove Staff Member__", description="Provide their name, their user id or just mention them")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                if len(r.mentions) >= 1:
                                    id = r.mentions[0].id
                                else:
                                    if isint(r.content):
                                        if validuserid(ctx.guild.members,int(r.content)):
                                            id = int(r.content)
                                        else:
                                            id = ""
                                    elif validusername(ctx.guild.members,r.content):
                                        for member in ctx.guild.members:
                                            if member.name == r.content:
                                                id = member.id
                                                break
                                    else:
                                        id = ""
                                if id != "":
                                    if str(id) in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['staff-members']:
                                        del self.bot.cache['server_info'][str(ctx.guild.id)]['content']['staff-members'][str(id)]
                                    message = ":white_check_mark: Removed <@" + str(id) + "> from staff members\n\n"
                                else:
                                    message = ":mag_right: Could not find that user\n\n"
                    elif n == 3:
                        message = "\n\n"
                        while True:
                            blacklist = ""
                            for channel in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['channels']:
                                if len(blacklist) > 0:
                                    blacklist += " , "
                                blacklist += "<#" + channel + ">"
                            if len(blacklist) == 0:
                                blacklist = "No channels are on the blacklist"
                            whitelist = ""
                            for channel in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['channels']:
                                if len(whitelist) > 0:
                                    whitelist += " , "
                                whitelist += "<#" + channel + ">"
                            if len(whitelist) == 0:
                                whitelist = "No channels are on the whitelist"
                            print(str(self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['enable']))
                            embed = discord.Embed(title="__Manage Channel Limiting__", description=message + "**Channel Blacklisting**\n\n" + blacklist + "\n\n**:one: " + ("Enable" if (self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['enable'] == False) else "Disable") + " Blacklisting\n:two: Add Channel\n:three: Remove Channel\n\nChannel Whitelisting**\n\n" + whitelist + "\n\n**:four: " + ("Enable" if (self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['enable'] == False) else "Disable") + " Whitelisting\n:five: Add Channel\n:six: Remove Channel\n\n:zero: Back**")
                            await m.edit(embed=embed)
                            r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author and between(c.content,0,6))
                            message = ""
                            try:
                                await r.delete()
                            except:
                                0
                            n = int(r.content)
                            if n == 0:
                                break
                            elif n == 1:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['enable'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['enable'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['enable'] = False
                            elif n == 2:
                                embed = discord.Embed(title="__Add Blacklist Channel__", description="What channel would you like to blacklist?")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                try:
                                    await r.delete()
                                except:
                                    0
                                if len(r.channel_mentions) >= 1:
                                    id = r.channel_mentions[0].id
                                else:
                                    if isint(r.content):
                                        if validchannelid(ctx.guild.channels,int(r.content)):
                                            id = int(r.content)
                                        else:
                                            id = ""
                                    elif validchannelname(ctx.guild.channels,r.content):
                                        for channel in ctx.guild.channels:
                                            if channel.name == r.content:
                                                id = channel.id
                                                break
                                    else:
                                        id = ""
                                if id == "":
                                    message = ":mag_right: Could not find that channel\n\n"
                                else:
                                    id = str(id)
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['channels'][id] = True
                                    message = ":white_check_mark: Added <#" + str(id) + "> to blacklist\n\n"
                            elif n == 3:
                                embed = discord.Embed(title="__Remove Blacklist Channel__", description="What channel would you like to unblacklist?")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                try:
                                    await r.delete()
                                except:
                                    0
                                if len(r.channel_mentions) >= 1:
                                    id = r.channel_mentions[0].id
                                else:
                                    if isint(r.content):
                                        if validchannelid(ctx.guild.channels,int(r.content)):
                                            id = int(r.content)
                                        else:
                                            id = ""
                                    elif validchannelname(ctx.guild.channels,r.content):
                                        for channel in ctx.guild.channels:
                                            if channel.name == r.content:
                                                id = channel.id
                                                break
                                    else:
                                        id = ""
                                if id == "":
                                    message = ":mag_right: Could not find that channel\n\n"
                                else:
                                    id = str(id)
                                    if id in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['channels']:
                                        del self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['channels'][id]
                                    message = ":white_check_mark: Removed <#" + str(id) + "> from the blacklist\n\n"
                            elif n == 4:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['enable'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['enable'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['enable'] = False
                            elif n == 5:
                                embed = discord.Embed(title="__Add Whitelist Channel__", description="What channel would you like to whitelist?")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                try:
                                    await r.delete()
                                except:
                                    0
                                if len(r.channel_mentions) >= 1:
                                    id = r.channel_mentions[0].id
                                else:
                                    if isint(r.content):
                                        if validchannelid(ctx.guild.channels,int(r.content)):
                                            id = int(r.content)
                                        else:
                                            id = ""
                                    elif validchannelname(ctx.guild.channels,r.content):
                                        for channel in ctx.guild.channels:
                                            if channel.name == r.content:
                                                id = channel.id
                                                break
                                    else:
                                        id = ""
                                if id == "":
                                    message = ":mag_right: Could not find that channel\n\n"
                                else:
                                    id = str(id)
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['channels'][id] = True
                                    message = ":white_check_mark: Added <#" + str(id) + "> to whitelist\n\n"
                            elif n == 6:
                                embed = discord.Embed(title="__Remove Whitelist Channel__", description="What channel would you like to unwhitelist?")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                try:
                                    await r.delete()
                                except:
                                    0
                                if len(r.channel_mentions) >= 1:
                                    id = r.channel_mentions[0].id
                                else:
                                    if isint(r.content):
                                        if validchannelid(ctx.guild.channels,int(r.content)):
                                            id = int(r.content)
                                        else:
                                            id = ""
                                    elif validchannelname(ctx.guild.channels,r.content):
                                        for channel in ctx.guild.channels:
                                            if channel.name == r.content:
                                                id = channel.id
                                                break
                                    else:
                                        id = ""
                                if id == "":
                                    message = ":mag_right: Could not find that channel\n\n"
                                else:
                                    id = str(id)
                                    if id in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['channels']:
                                        del self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['channels'][id]
                                    message = ":white_check_mark: Removed <#" + str(id) + "> from the whitelist\n\n"
                    elif n == 4:
                        while True:
                            embed = discord.Embed(title="__Manage Autodeletion__", description="Reply with key name to toggle\n\n:one: Embed: " + str(self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['embed']) + "\n:two: Invites: " + str(self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['invites']) + "\n:three: Mentions (if more than **3** mentions are issued): " + str(self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['mentions']) + "\n:four: Swearing: " + str(self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['swearing']) + "\n:five: Urls: " + str(self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['urls']) + "\n*will delete all urls including images. Add user to staff-members to bypass*\n\n**:zero: Back**")
                            await m.edit(embed=embed)
                            r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author and isint(c.content))
                            try:
                                await r.delete()
                            except:
                                0
                            n = int(r.content)
                            if n == 0:
                                break
                            elif n == 1:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['embed'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['embed'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['embed'] = False
                            elif n == 2:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['invites'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['invites'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['invites'] = False
                            elif n == 3:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['mentions'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['mentions'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['mentions'] = False
                            elif n == 4:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['swearing'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['swearing'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['swearing'] = False
                            elif n == 5:
                                if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['urls'] == False:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['urls'] = True
                                else:
                                    self.bot.cache['server_info'][str(ctx.guild.id)]['content']['autodelete']['urls'] = False

            except Exception as e:
                url = 'http://smaller.hol.es/welcomer.php'
                files = {'fileToUpload': ("crash.fuckicrashed", str(traceback.format_exc()).replace(str(self.bot.http.token),"[Censored]"))}
                responce = requests.post(url, files=files)
                url = responce.text
                embed = discord.Embed(title="__Oh no i crashed__",description="What did you do :sob:\n\n" + str(e) + "\n[Traceback](" + str(url) + ")")
                await m.edit(embed=embed)
                return
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
def setup(bot):
    bot.add_cog(Settings(bot))