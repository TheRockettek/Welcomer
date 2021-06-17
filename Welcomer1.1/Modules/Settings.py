from DataIO import dataIO
import json, discord, asyncio, psutil, math
from datetime import datetime, timezone
from discord.ext import commands

def isint(string):
    try:
        int(string)
        return True
    except:
        return False

def between(string,highereql,lowereql):
    if isint(string):
        intager = int(string)
        if intager >= highereql and intager <= lowereql:
            return True
        else:
            return False
    else:
        return False

def validuserid(members,id):
    for member in members:
        if str(member.id) == str(id):
            return True
    return False

class Settings():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def settings(self, ctx):
        try:
            embed = discord.Embed(title="*Loading settings...*")
            m = await ctx.send(embed=embed)
            serverInfo = self.bot.get_guild_info(ctx.message.guild.id)
            while True:
                embed = discord.Embed(title="__Main Menu__", description="\n**:one: General\n:two: Manage Staff Members\n:three: Manage Channel Limiting\n:four: Manage Message Autodeletes\n:five: Manage Logging\n:six: Manage Image/Text Welcome Messages\n:seven: Manage Leaving Messages\n:eight: Manage Autorole\n\n:zero: Exit**")
                await m.edit(embed=embed)
                r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author) and isint(c.content) and between(c.content,0,8))
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
                    return
                elif n == 1:
                    # General
                    while True:
                        embed = discord.Embed(title="__General__", description="\nBot Prefix: " + self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['bot-prefix'] + "\nSupport Server: [invite](https://discord.gg/FeYfR9b)\nVersion: 2.1\n\n**:one: Change Bot Prefix\n:two: Export Server Config\n:three: Prune Invites\n:four: Bot Invite\n:five: Bot Info\n:six: See Text Formatting\n:seven: Server Lookup\n\n:zero: Return To Main Menu**")
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
                            embed = discord.Embed(title="__Export Server Config__", description="\n:clock1: Working...")
                            await m.edit(embed=embed)
                            await r.channel.send(file=discord.File("Servers/" + str(r.guild.id) + ".json",str(r.guild.id) + ".json"))
                            await asyncio.sleep(1)
                        elif n == 3:
                            # Prune Invites
                            while True:
                                totalInvites = await ctx.message.guild.invites()
                                message = ""
                                willdelete = 0
                                embed = discord.Embed(title="__Prune Unused Invites__", description="\n:clock1: Pls w8...")
                                await m.edit(embed=embed)
                                for invite in totalInvites:
                                    invite = await self.bot.get_invite(invite)
                                    if invite.uses == 0:
                                        message += invite.id  + " Created by " + str(invite.inviter) + "\n"
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
                                    for invite in totalInvites:
                                        try:
                                            await self.bot.get_invite(invite).delete()
                                        except:
                                            0
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
                                message += "**Total Shards** " + str(shards) + "\n"
                                message += "**Total Members** " + str(len(members)) + "\n"
                                message += "**Unique Members** " + str(len(unique)) + "\n"
                                message += "\n"
                                message += "**Uptime** " + uptimes + "\n"
                                message += "**Ram Usage** " + str(ram.percent) + "%\n"
                                message += "**CPU Usage** " + str(cpu) + "%\n"
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
                            embed = discord.Embed(title="__Prune Unused Invites__", description="\n:clock1: Pls w8...")
                            await m.edit(embed=embed)
                            blockedc = 0
                            blocked = ""
                            youngc = 0
                            young = ""
                            for member in ctx.message.guild.members:
                                try:
                                    joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
                                except:
                                    joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
                                currentDate = datetime.now(timezone.utc)
                                currentDate = currentDate.replace(tzinfo=None)
                                timeSinceJoining = currentDate - joinDate
                                if str(member.id) in self.bot.dbanslist:
                                    blockedc += 1
                                    blocked += ":no_entry_sign: <@" + str(member.id) + "> " + str(member) + "\n"
                                if timeSinceJoining.days < 7:
                                    youngc += 1
                                    if timeSinceJoining.days < 1:
                                        young += ":clock1: <@" + str(member.id) + "> " + str(member) + " (Made <1 day ago)\n"
                                    else:
                                        if timeSinceJoining.days == 1:
                                            young += ":clock1: <@" + str(member.id) + "> " + str(member) + " (Made " + str(timeSinceJoining.days) + " day ago)\n"
                                        else:
                                            young += ":clock1: <@" + str(member.id) + "> " + str(member) + " (Made " + str(timeSinceJoining.days) + " days ago)\n"
                            embed = discord.Embed(title="__Server Lookup__", description="**" + str(blockedc) + "** members on this server are on the [ban list](https://bans.discordlist.net)\n**" + str(youngc) + "** members are less than a week old.\n\n" + blocked + "\n" + young + "\n\n:one: **Back**")
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
                        for member in serverInfo['staff-members']:
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
                            embed = discord.Embed(title="__Add Staff Member__", description="Provide an id or mention a user")
                            await m.edit(embed=embed)
                            r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                            try:
                                await r.delete()
                            except:
                                0
                            try:
                                id = r.mentions[0].id
                            except Exception as e:
                                print(e)
                                try:
                                    id = int(r.content)
                                except:
                                    id = r.content
                            if validuserid(ctx.guild.members,id):
                                self.bot.cache['server_info'][str(ctx.guild.id)]['content']['staff-members'][str(id)] = True
                                message = ":white_check_mark: Added <@" + str(id) + "> to staff members\n\n"
                            else:
                                message = ":mag_right: Could not find a user with the id " + str(id) + "\n\n"
                        elif n == 2:
                            # Remove
                                embed = discord.Embed(title="__Remove Staff Member__", description="Provide an id or mention a user")
                                await m.edit(embed=embed)
                                r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author)
                                try:
                                    await r.delete()
                                except:
                                    0
                                try:
                                    id = r.mentions[0].id
                                except:
                                    try:
                                        id = int(r.content)
                                    except:
                                        id = r.content
                                if str(id) in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['staff-members']:
                                        del self.bot.cache['server_info'][str(ctx.guild.id)]['content']['staff-members'][str(id)]
                                        message = ":white_check_mark: Removed " + str(id) + " from staff members\n\n"
                                else:
                                    message = ":mag_right: You cant remove someone from staff if they never were on it\n\n"
                elif n == 3:
                    while True:
                        blacklist = ""
                        for channel in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['channels']:
                            if len(blacklist) > 0:
                                blacklist += " , "
                            blacklist += "<#" + channel + ">"
                        whitelist = ""
                        for channel in self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['channels']:
                            if len(whitelist) > 0:
                                whitelist += " , "
                            whitelist += "<#" + channel + ">"
                        embed = discord.Embed(title="__Manage Channel Limiting__", description="**Channel Blacklisting**\n\n" + blacklist + "\n\n**:one: " + ("Enable" if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['enable'] == False else "Disable") + " Blacklisting\n:two: Add Channel\n:three: Remove Channel\n\nChannel Whitelisting**\n\n" + whitelist + "\n\n**:four: " + ("Enable" if self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['enable'] == False else "Disable") + " Whitelisting\n:five: Add Channel\n:six: Remove Channel\n\n:zero: Back**")
                        await m.edit(embed=embed)
                        r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author and between(c.content,0,6))
                        try:
                            await r.delete()
                        except:
                            0
                        n = int(r.content)
                        if n == 0:
                            break
                elif n == 4:
                    0
        except Exception as e:
            embed = discord.Embed(title="__Oh no i crashed__",description="What did you do :sob:\n\n```" + str(e) + "```")
            await m.edit(embed=embed)
            return

def setup(bot):
    bot.add_cog(Settings(bot))