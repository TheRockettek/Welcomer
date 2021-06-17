from discord.ext import commands
from datetime import datetime
from datetime import timezone
from DataIO import dataIO
import discord, asyncio, math, time

botLoggingChannel = 341855587669245957

def deformat(text):
    text = text.replace("`", "")
    text = text.replace("_", "")
    text = text.replace("*", "")
    text = text.replace("~", "")
    if text == "":
        return " "
    return text

def exists(variable):
    try:
        variable
        return True
    except:
        return False

def ischannel(channels, channelID):
    for channel in channels:
        if str(channel.id) == str(channelID):
            return True
    return False

def ismember(guild, memberID):
    for member in guild.members:
        if member.id == memberID:
            return True
    return False

def isrole(guild, roleID):
    for role in guild.roles:
        if role.id == roleID:
            return True
    return False

def getchannel(guild, channelID):
    for channel in guild.channels:
        if channel.id == channelID:
            return True
    return False

def getmember(guild, memberID):
    for member in guild.members:
        if member.id == memberID:
            return member
    return False

def getrole(guild, roleID):
    for role in guild.roles:
        if str(role.id) == roleID:
            return role
    return False

def get_guild_user_info(self, user, guild):
    guildInfo = self.bot.get_guild_info(guild)
    userInfo = self.bot.get_user_info(guild)
    return userInfo, guildInfo

def getSuffix(num):
    num = str(num)
    last = num[len(num)-1:len(num)]
    if num == "1":
        return "st"
    elif num == "2":
        return "nd"
    elif num == "3":
        return "rd"
    else:
        return "th"

def replace(text, guild, member):
    text = text.replace("%SERVER_NAME%",guild.name)
    text = text.replace("%SERVER_MEMBER_COUNT%",str(len(guild.members)))
    text = text.replace("%SERVER_COUNT_SUFFIX%",getSuffix(len(guild.members)))
    text = text.replace("%SERVER_ICON_URL%",guild.icon_url)
    text = text.replace("%SERVER_OWNER_NAME%",guild.owner.name)
    text = text.replace("%SERVER_OWNER%",guild.owner.name + "#" + guild.owner.discriminator)
    text = text.replace("%SERVER_OWNER_ID%",str(guild.owner.id))
    text = text.replace("%MEMBER_NAME%",member.name)
    text = text.replace("%MEMBER%",member.display_name + "#" + member.discriminator)
    text = text.replace("%MEMBER_ID%",str(member.id))
    return text

class EventHandler():

    def __init__(self, bot):
        self.bot = bot

    @asyncio.coroutine
    async def on_message_delete(self, message):
        if not message.guild is None:
            guildInfo = self.bot.get_guild_info(str(message.guild.id))
            loggingChannel = guildInfo['logging']['channel']
            if guildInfo['logging']['enable'] == True and ischannel(message.guild.channels,loggingChannel) and guildInfo['logging']['deleted-messages'] == True and (message.author.bot == False):
                responce = ""
                responce += ":date: **Created at** : " + str(message.created_at) + "\n"
                responce += ":file_folder: **Channel** : " + message.channel.name + " (" + str(message.channel.id) + ")\n"
                responce += ":mega: **Author** : " + message.author.name + "#" + message.author.discriminator + "(" + str(message.author.id) + ")\n"
                responce += ":speech_balloon: **Content** : ```" + deformat(message.content) + "```"
                embed = discord.Embed(title=message.author.name + "'s message has been deleted", description=responce, timestamp=datetime.utcfromtimestamp(time.time()))
                try:
                    await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
                except:
                    print("Unable to send message on " + message.guild.name + " (" + str(message.guild.id) + ")")

    @asyncio.coroutine
    async def on_message_edit(self, before, after):
        if not after.guild is None:
            guildInfo = self.bot.get_guild_info(str(after.guild.id))
            loggingChannel = guildInfo['logging']['channel']
            if guildInfo['logging']['enable'] == True and ischannel(after.guild.channels,loggingChannel) and guildInfo['logging']['edited-messages'] == True and (after.author.bot == False):
                if before.content != after.content:
                    message = ""
                    message += ":date: **Created at** : " + str(after.created_at) + "\n"
                    message += ":file_folder: **Channel** : " + after.channel.name + " (" + str(after.channel.id) + ")\n"
                    message += ":mega: **Author** : " + after.author.name + "#" + after.author.discriminator + "(" + str(after.author.id) + ")\n"
                    message += ":speech_balloon: **Content** : ```" + deformat(before.content) + "``````" + deformat(after.content) + "```"
                    embed = discord.Embed(title=after.author.name + "'s message has been edited", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
                    try:
                        await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
                    except:
                        print("Unable to send message on " + after.guild.name + " (" + str(after.guild.id) + ")")

    @asyncio.coroutine
    async def on_channel_delete(self, channel):
        guildInfo = self.bot.get_guild_info(str(channel.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(channel.guild.channels,loggingChannel) and guildInfo['logging']['deleted-channels'] == True:
            message = ""
            message += ":date: **Created at** : " + str(channel.created_at) + "\n"
            #message += ":spy: **Private Channel** : " + str(channel.is_private) + "\n"
            message += ":card_box: **Type** : " + str(channel.type) + "\n"
            if str(channel.type) == "voice":
                if channel.user_limit == 0:
                    channel.user_limit = "No limit"
                message += "\n"
                message += ":microphone2: **User Limit** : " + str(channel.user_limit) + "\n"
                message += ":signal_strength: **Bitrate** : " + str(math.floor(channel.bitrate/1000)) + " kbps"
            embed = discord.Embed(title="#" + channel.name + " (" + str(channel.id) + ") has been deleted", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + channel.guild.name + " (" + str(channel.guild.id) + ")")

    @asyncio.coroutine
    async def on_channel_create(self, channel):
        guildInfo = self.bot.get_guild_info(str(channel.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(channel.guild.channels,loggingChannel) and guildInfo['logging']['created-channels'] == True:
            message = ""
            message += ":clock1: **Created at** : " + str(channel.created_at) + "\n"
            message += ":spy: **Private Channel** : " + str(channel.is_private) + "\n"
            message += ":card_box: **Type** : " + str(channel.type) + "\n"
            message += "\n"
            if str(channel.type) == "voice":
                if channel.user_limit == 0:
                    channel.user_limit = "No limit"
                message += ":microphone2: **User Limit** : " + str(channel.user_limit) + "\n"
                message += ":signal_strength: **Bitrate** : " + str(math.floor(channel.bitrate/1000)) + " kbps\n"
            else:
                message += ":information_source: **Topic** : ```" + channel.topic + "```\n"
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + channel.guild.name + " (" + str(channel.guild.id) + ")")

    @asyncio.coroutine
    async def on_channel_update(self, before, after):
        guildInfo = self.bot.get_guild_info(str(after.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(after.guild.channels,loggingChannel) and guildInfo['logging']['edited-channels'] == True:
            change = False
            message = ""
            if before.name != after.name:
                message += ":paintbrush: **" + before.name + "** has been renamed to **" + after.name + "**\n"
                change = True
            #if before.is_private != after.is_private:
            #    if after.is_private:
            #        message += ":spy: The channel has been made private\n"
            #        change = True
            #    else:
            #        message += ":spy: The channel has been made public\n"
            #        change = True
            if str(after.type) == "voice":
                message += "\n"
                if before.user_limit == 0:
                    before.user_limit = "No limit"
                if after.user_limit == 0:
                    after.user_limit = "No limit"
                if before.bitrate != after.bitrate:
                    message += ":signal_strength: The bitrate has been changed from **" + str(math.floor(before.bitrate/1000)) + "** kbps to **" + str(math.floor(after.bitrate/1000)) + "** kbps\n"
                    change = True
                if before.user_limit != after.user_limit:
                    message += ":microphone2: The user limit has changed from **" + str(before.user_limit) + "** to **" + str(after.user_limit) + "**\n"
                    change = True
            else:
                if before.topic != after.topic:
                    message += ":information_source: The channel's topic has been changed\n"
                    change = True
            if change == True:
                embed = discord.Embed(title="#" + after.name + " (" + str(after.id) + ") has been edited", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
                try:
                    await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
                except:
                    print("Unable to send message on " + after.guild.name + " (" + str(after.guild.id) + ")")

    @asyncio.coroutine
    async def on_member_join(self, member):
        userInfo, guildInfo = get_guild_user_info(self,str(member.id),str(member.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        print("J | " + member.name + " | " + str(member.id) + " | " + member.guild.name + " (" + str(member.guild.id) + ")")

        welcomeChannel = guildInfo['welcomer']['channel']
        if guildInfo['welcomer']['use-text'] == True and ischannel(member.guild.channels,welcomeChannel):
            await self.bot.get_channel(int(welcomeChannel)).send(replace(guildInfo['welcomer']['text'], member.guild, member))

        if guildInfo['autorole']['enable'] == True:
            role = getrole(member.guild, guildInfo['autorole']['roleid'])
            if role != False:
                print("Gave " + member.name + " role " + role.name + " on " + member.guild.name)
                try:
                    await member.add_roles(role)
                except Exception as e:
                    print("Unable to assign role on " + member.guild.name + " (" + str(member.guild.id) + ")")
                    print(e)

        if guildInfo['logging']['enable'] == True and ischannel(member.guild.channels,loggingChannel) and guildInfo['logging']['member-join'] == True:
            message = ""
            try:
                joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
            except:
                joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
            currentDate = datetime.now(timezone.utc)
            currentDate = currentDate.replace(tzinfo=None)
            timeSinceJoining = currentDate - joinDate
            if timeSinceJoining.days < 1:
                message += ":date: **Join date** : " + str(member.created_at) + " (" + str(timeSinceJoining.hours) + " hours ago)\n"
            else:
                message += ":date: **Join date** : " + str(member.created_at) + " (" + str(timeSinceJoining.days) + " days ago)\n"
            message += ":robot: **Bot account** : " + str(member.bot) + "\n"
            message += "\n"
            for guild in self.bot.guilds:
                if len(guild.members) >= 100:
                    if member.id == guild.owner.id:
                        message += ":gear: **Server Owner (" + str(len(guild.members)) + " members)\n"
            if str(member.id) in self.bot.specialRoles['staff']:
                message += ":tools: **Welcome Support Staff**\n"
            if str(member.id) in self.bot.specialRoles['donators']:
                message += ":gem: **Donator**\n"
            if str(member.id) in self.bot.specialRoles['trusted']:
                message += ":shield: **Trusted user**\n"
            message += "\n"
            if timeSinceJoining.days < 7:
                message += ":warning: **Account is new**\n"
            if str(member.id) in self.bot.dbanslist:
                message += ":no_entry: **Banned on discord list**\n"
            verifiedReports = 0
            for report in userInfo['Records']:
                if report['isVerified'] == True:
                    verifiedReports += 1
            if verifiedReports > 0:
                message += ":dagger: **" + str(verifiedReports) + " verified reports**"
            message += "\n"
            if guildInfo['autorole']['enable'] == True:
                print("Giving role")
                role = getrole(member.guild, guildInfo['autorole']['roleid'])
                print(role.name + " | " + str(role.id) + " | " + member.guild, guildInfo['autorole']['roleid'])
                if role != False:
                    message += ":triangular_flag_on_post: Autoassigned " + role.name + " role"
            embed = discord.Embed(title=member.name + "#" + member.discriminator + " (" + str(member.id) + ") has joined", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
            avatar = member.avatar_url or member.default_avatar_url
            try:
                embed.set_thumbnail(url=avatar)
            except:
                0 
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + message.guild.name + " (" + message.guild.id + ")")

    @asyncio.coroutine
    async def on_member_remove(self, member):
        userInfo, guildInfo = get_guild_user_info(self,str(member.id),str(member.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        print("L | " + member.name + " | " + str(member.id) + " | " + member.guild.name + " (" + str(member.guild.id) + ")")
        if guildInfo['logging']['enable'] == True and ischannel(member.guild.channels,loggingChannel) and guildInfo['logging']['member-leave'] == True:
            message = ""
            try:
                joinDate = datetime.strptime(str(member.created_at),"%Y-%m-%d %H:%M:%S.%f")
            except:
                joinDate = datetime.strptime(str(member.created_at),"%Y-%m-%d %H:%M:%S")
            currentDate = datetime.now(timezone.utc)
            currentDate = currentDate.replace(tzinfo=None)
            timeSinceJoining = currentDate - joinDate
            if timeSinceJoining.days < 1:
                message += ":date: **Join date** : " + str(member.created_at) + " (" + str(timeSinceJoining.hours) + " hours ago)\n"
            else:
                message += ":date: **Join date** : " + str(member.created_at) + " (" + str(timeSinceJoining.days) + " days ago)\n"
            message += ":robot: **Bot account** : " + str(member.bot) + "\n"
            embed = discord.Embed(title=member.name + "#" + member.discriminator + " (" + str(member.id) + ") has left", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + message.guild.name + " (" + str(message.guild.id) + ")")

    @asyncio.coroutine
    async def on_member_update(self, before, after):
        if not after.guild is None:
            userInfo, guildInfo = get_guild_user_info(self,str(after.id),str(after.guild.id))
            loggingChannel = guildInfo['logging']['channel']
            if guildInfo['logging']['enable'] == True and ischannel(after.guild.channels,loggingChannel) and guildInfo['logging']['member-edit'] == True:
                change = False
                autoassign = ""
                if guildInfo['autorole']['enable'] == True:
                    role = getrole(after.guild, guildInfo['autorole']['roleid'])
                    if role != False:
                        autoassign = role.name
                message = ""
                if before.display_name != after.display_name:
                    message += ":pencil: Nickname changed from **" + before.display_name + "** to **" + after.display_name + "**\n"
                    change = True
                message += "\n"
                allroles = dict()
                for role in before.roles:
                    if role in after.roles and not role in before.roles:
                        if role.name != autoassign:
                            message += ":triangular_flag_on_post: Assigned **" + role.name + "** role\n"
                            change = True
                    elif not role in after.roles and role in before.roles:
                        message += ":triangular_flag_on_post: Deassigned **" + role.name + "** role\n"
                        change = True
                for role in after.roles:
                    if role in after.roles and not role in before.roles:
                        message += ":triangular_flag_on_post: Assigned **" + role.name + "** role\n"
                        change = True
                    elif not role in after.roles and role in before.roles:
                        message += ":triangular_flag_on_post: Deassigned **" + role.name + "** role\n"
                        change = True
                message += "\n"
                beforeperms = dict()
                afterperms = dict()
                for permission in after.guild_permissions:
                    afterperms[permission[0]] = permission[1]
                for permission in before.guild_permissions:
                    beforeperms[permission[0]] = permission[1]
                for permission in afterperms:
                    if afterperms[permission] != beforeperms[permission]:
                        if beforeperms[permission] == False and afterperms[permission] == True:
                            message += ":bookmark_tabs: Assigned **" + permission + "** permission\n"
                            change = True
                        elif beforeperms[permission] == True and afterperms[permission] == False:
                            message += ":bookmark_tabs: Deassigned **" + permission + "** permission\n"
                            change = True
                if change == True:
                    embed = discord.Embed(title=after.name + "#" + after.discriminator + " (" + str(after.id) + ") has been edited", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
                    try:
                        await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
                    except:
                        print("Unable to send message on " + after.guild.name + " (" + str(after.guild.id) + ")")

    @asyncio.coroutine
    async def on_guild_join(self, guild):
        await guild.owner.send(""":wave:

**__Welcomer by Im Rock#3779__**

Thank you for adding Welcomer to your guild :kissing_heart:

***Setup Welcomer***
- Do +welcomer setchannel in the channel you want or you can supply the channel id or mention the channel.
- After that is done do +welcomer enable

***Setup logging***
- Do +logging setchannel in the channel you would like it to use.
- After that do +logging enable

***Setup autorole***
- Do +autorole setrole then supply a role id, name or mention the role
- Do +autorole enable

***How do i change the prefix***
- Do +config set bot-prefix <prefix> (eg: +config set bot-prefix =)
- Do +config apply (but obviously + would be the new bot-prefix)

**Join the support guild : https://discord.gg/FeYfR9b**""")
        message = ""
        message += ":ticket: **Server Name** : " + guild.name + " (" + str(guild.id) + ")\n"
        users = 0
        bots = 0
        for user in guild.members:
            if user.bot:
                bots += 1
            else:
                users += 1
        percentage = math.ceil((bots/len(guild.members))*10000)/100
        message += ":page_facing_up: **User/Bots** : " + str(users) + " / " + str(bots) + " ( " + str(math.floor(percentage)) + "% )\n"
        if percentage >= 50:
            message += ":warning: **May be a bot farm**\n"
        message += "\n"
        message += ":crown: **Owner** : " + guild.owner.name + "#" + guild.owner.discriminator + " (" + str(guild.owner.id) + ")\n"
        message += "\n"
        for channel in guild.channels:
            invite = await channel.create_invite()
            break
        try:
            invite = "https://discord.gg/" + invite.id
            message += ":abc: **Invite Url** : " + invite  + "\n"
        except:
            message += ":abc: **Invite Url** : :grey_question:\n"
        message += ":hash: **Total Servers** : " + str(len(self.bot.guilds))
        embed = discord.Embed(title=guild.name + " (" + str(guild.id) + ") has added our bot :)", colour=discord.Colour(0x00ff00), description=message, timestamp=datetime.utcfromtimestamp(time.time()))
        try:
            embed.set_thumbnail(url=guild.icon_url)
        except:
            0
        await self.bot.get_channel(int(botLoggingChannel)).send(embed=embed)

    @asyncio.coroutine
    async def on_guild_remove(self, guild):
        message = ""
        message += ":ticket: **Server Name** : " + guild.name + " (" + str(guild.id) + ")\n"
        users = 0
        bots = 0
        for user in guild.members:
            if user.bot:
                bots += 1
            else:
                users += 1
        percentage = math.ceil((bots/len(guild.members))*10000)/100
        message += ":page_facing_up: **User/Bots** : " + str(users) + " / " + str(bots) + " ( " + str(math.floor(percentage)) + "% )\n"
        message += ":crown: **Owner** : " + guild.owner.name + "#" + guild.owner.discriminator + " (" + str(guild.owner.id) + ")\n"
        message += ":hash: **Total Servers** : " + str(len(self.bot.guilds))
        embed = discord.Embed(title=guild.name + " (" + str(guild.id) + ") has removed our bot :(", colour=discord.Colour(0xff0000), description=message, timestamp=datetime.utcfromtimestamp(time.time()))
        try:
            embed.set_thumbnail(url=guild.icon_url)
        except:
            0
        try:
            await self.bot.get_channel(int(botLoggingChannel)).send(embed=embed)
        except:
            print("Unable to send message on " + guild.name + " (" + str(guild.id) + ")")

    @asyncio.coroutine
    async def on_guild_role_create(self, role):
        guildInfo = self.bot.get_guild_info(str(role.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(role.guild.channels,loggingChannel) and guildInfo['logging']['server-role-create'] == True:
            message = ""
            message += "<:colour:" + self.bot.customemotes['colour'] + "> **Colour** : " + str(role.colour).upper() + "\n"
            message += "<:hoisted:" + self.bot.customemotes['hoisted'] + "> **Is hoisted** : " + str(role.hoist) + "\n"
            message += "<:twitch:" + self.bot.customemotes['twitch'] + "> **Is managed** : " + str(role.managed) + "\n"
            message += "<:at:" + self.bot.customemotes['at'] + "> **Is mentionable** : " + str(role.mentionable) + "\n"
            if role.mentionable == True:
                message += "<:at:" + self.bot.customemotes['at'] + "> **Is mentionable** : " + str(role.mentionable) + " (@" + role.mention + ")\n"
            else:
                message += "<:at:" + self.bot.customemotes['at'] + "> **Is mentionable** : " + str(role.mentionable) + "\n"
            message += "\n"
            for permission in role.permissions:
                if permission[1] == True:
                    message += ":bookmark_tabs: Given **" + permission[0] + "** permission\n"
            embed = discord.Embed(title="Role " + role.name + " (" + str(role.id) + ") has been created", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + role.guild.name + " (" + str(role.guild.id) + ")")

    @asyncio.coroutine
    async def on_guild_role_delete(self, role):
        guildInfo = self.bot.get_guild_info(str(role.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(role.guild.channels,loggingChannel) and guildInfo['logging']['server-role-delete'] == True:
            message = ""
            """
            message += "<:colour:" + self.bot.customemotes['colour'] + "> **Colour** : " + str(role.colour).upper() + "\n"
            message += "<:hoisted:" + self.bot.customemotes['hoisted'] + "> **Is hoisted** : " + str(role.hoist) + "\n"
            message += "<:twitch:" + self.bot.customemotes['twitch'] + "> **Is managed** : " + str(role.managed) + "\n"
            message += "<:at:" + self.bot.customemotes['at'] + "> **Is mentionable** : " + str(role.mentionable) + "\n"
            if role.mentionable == True:
                message += "<:at:" + self.bot.customemotes['at'] + "> **Is mentionable** : " + str(role.mentionable) + " (@" + role.mention + ")\n"
            else:
                message += "<:at:" + self.bot.customemotes['at'] + "> **Is mentionable** : " + str(role.mentionable) + "\n"
            """
            embed = discord.Embed(title="Role " + role.name + " (" + str(role.id) + ") has been deleted", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send file on " + role.guild.name + " (" + str(role.guild.id) + ")")

    @asyncio.coroutine
    async def on_guild_role_update(self, before, after):
        guildInfo = self.bot.get_guild_info(str(after.guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(after.guild.channels,loggingChannel) and guildInfo['logging']['server-role-edit'] == True:
            change = False
            message = ""
            if before.name != after.name:
                message += ":pencil: Role name changed from **" + before.name + "** to **" + after.name + "**\n"
                change = True
            if before.colour != after.colour:
                message += "<:colour:" + self.bot.customemotes['colour'] + "> Colour changed from **" + str(before.colour).upper() + "** to **" + str(after.colour).upper() + "**\n"
                change = True
            if before.hoist != after.hoist:
                if after.hoist == True:
                    message += "<:hoisted:" + self.bot.customemotes['hoisted'] + "> Role is now hoisted\n"
                    change = True
                else:
                    message += "<:hoisted:" + self.bot.customemotes['hoisted'] + "> Role is no longer hoisted\n"
                    change = True
            if before.mentionable != after.mentionable:
                if after.mentionable == True:
                    message += "<:at:" + self.bot.customemotes['at'] + "> Role is now able to be mentioned\n"
                    change = True
                else:
                    message += "<:at:" + self.bot.customemotes['at'] + "> Role can no longer be mentioned\n"
                    change = True
            if before.mention != after.mention and after.mentionable == True:
                message += "<:at:" + self.bot.customemotes['at'] + "> Role is now mentionable by doing @" + role.mention + "\n"
                change = True
            message += "\n"
            beforeperms = dict()
            afterperms = dict()
            for permission in after.permissions:
                afterperms[permission[0]] = permission[1]
            for permission in before.permissions:
                beforeperms[permission[0]] = permission[1]
            for permission in afterperms:
                if afterperms[permission] != beforeperms[permission]:
                    if beforeperms[permission] == False and afterperms[permission] == True:
                        message += ":bookmark_tabs: Assigned **" + permission + "** permission\n"
                        change = True
                    elif beforeperms[permission] == True and afterperms[permission] == False:
                        message += ":bookmark_tabs: Deassigned **" + permission + "** permission\n"
                        change = True
            if change == True:
                embed = discord.Embed(title="Role " + after.name + " (" + str(after.id) + ") has been edited", description=message, timestamp=datetime.utcfromtimestamp(time.time()))
                try:
                    await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
                except:
                    print("Unable to send message on " + after.guild.name + " (" + str(after.guild.id) + ")")

    @asyncio.coroutine
    async def on_guild_available(self, guild):
        0

    @asyncio.coroutine
    async def on_guild_unavailable(self, guild):
        0

    @asyncio.coroutine
    async def on_member_ban(self, guild, member):
        guildInfo = self.bot.get_guild_info(str(guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(guild.channels,loggingChannel) and guildInfo['logging']['member-ban'] == True:
            embed = discord.Embed(description="**" + member.name + "#" + member.discriminator + "** has been banned :hammer_pick:", timestamp=datetime.utcfromtimestamp(time.time()))
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + guild.name + " (" + str(guild.id) + ")")

    @asyncio.coroutine
    async def on_member_unban(self, guild, member):
        guildInfo = self.bot.get_guild_info(str(guild.id))
        loggingChannel = guildInfo['logging']['channel']
        if guildInfo['logging']['enable'] == True and ischannel(guild.channels,loggingChannel) and guildInfo['logging']['member-unban'] == True:
            embed = discord.Embed(description="**" + member.name + "#" + member.discriminator + "** has been unbanned :eyes:", timestamp=datetime.utcfromtimestamp(time.time()))
            try:
                await self.bot.get_channel(int(loggingChannel)).send(embed=embed)
            except:
                print("Unable to send message on " + guild.name + " (" + str(guild.id) + ")")



def setup(bot):
    bot.add_cog(EventHandler(bot))