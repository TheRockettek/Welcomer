from discord.ext import commands
from datetime import datetime
from DataIO import dataIO
import discord, shutil, asyncio

def exists(variable):
    try:
        variable
        return True
    except:
        return False

def is_int(string):
    try:
        int(string)
        return True
    except:
        return False

def is_bool(string):
    try:
        bool(string)
        return True
    except:
        False

def splitKey(string):
    a = string.find(".")
    b = string[:a]
    c = string[a+1:]
    return b, c

def set_attribute(self, server_info, key, value, id, guild):
    if key.find(".") != -1:
        key, indKey = splitKey(key)
        if key in server_info:
            if indKey in server_info[key]:
                if type(self.bot.cache['server_info'][id]['content'][key][indKey]) == str:
                    if "member" in indKey or "member" in key:
                        print(ismember(guild,value))
                        print("HA")
                        if ismember(guild,value):
                            self.bot.cache['server_info'][id]['content'][key][indKey] = value
                            return True,"SS"
                        else:
                            return False,"VNU"
                    elif "channel" in indKey or "channel" in key:
                        print(ischannel(guild,value))
                        if ischannel(guild,value):
                            self.bot.cache['server_info'][id]['content'][key][indKey] = value
                            return True,"SS"
                        else:
                            return False,"VNC"
                    else:
                        self.bot.cache['server_info'][id]['content'][key][indKey] = value
                        return True,"SS"
                elif type(self.bot.cache['server_info'][id]['content'][key][indKey]) == bool:
                    if is_bool(value):
                        self.bot.cache['server_info'][id]['content'][key][indKey] = (not value.lower() == "false")
                        print(self.bot.cache['server_info'][id]['content'][key][indKey])
                        print("Setting " + key + "." + indKey + " to " + str(value))
                        return True,"SS"
                    return False,"WTB"
                elif type(self.bot.cache['server_info'][id]['content'][key][indKey]) == int:
                    if is_int(value):
                        if "member" in indKey or "member" in key:
                            if ismember(guild,value):
                                self.bot.cache['server_info'][id]['content'][key][indKey] = int(value)
                                return True,"SS"
                            else:
                                return False,"VNU"
                        elif "channel" in indKey or "channel" in key:
                            print(ischannel(guild,value))
                            if ischannel(guild,value):
                                self.bot.cache['server_info'][id]['content'][key][indKey] = int(value)
                                return True,"SS"
                            else:
                                return False,"VNC"
                        else:
                            self.bot.cache['server_info'][id]['content'][key][indKey] = int(value)
                            return True,"SS"
                    return False,"WTI"
                elif type(self.bot.cache['server_info'][id]['content'][key][indKey]) == dict:
                    if not value in self.bot.cache['server_info'][id]['content'][key][indKey]:
                        if "member" in indKey or "member" in key:
                            if ismember(guild,value):
                                self.bot.cache['server_info'][id]['content'][key][indKey][value] = True
                                return True,"SSD"
                        elif "channel" in indKey or "channel" in key:
                            if ischannel(guild,value):
                                self.bot.cache['server_info'][id]['content'][key][indKey][value] = True
                                return True,"SSD"
                        else:
                            self.bot.cache['server_info'][id]['content'][key][indKey][value] = True
                            return True,"SSD"
                    return False,"VIS"
            else:
                return False,"DNE"
        else:
            return False,"DNE"
    else:
        if key in server_info:
            if "member" in key:
                if ismember(guild,value):
                    self.bot.cache['server_info'][id]['content'][key] = value
                    return True,"SS"
                else:
                    return False,"VNU"
            elif "guild" in key:
                if ismember(guild,value):
                    self.bot.cache['server_info'][id]['content'][key] = value
                    return True,"SS"
                else:
                    return False,"VNC"
                if type(self.bot.cache['server_info'][id]['content'][key]) == str:
                    if "member" in key:
                        if ismember(guild,value):
                            self.bot.cache['server_info'][id]['content'][key] = value
                            return True,"SS"
                        else:
                            return False,"VNU"
                    elif "channel" in key:
                        if ischannel(guild,value):
                            self.bot.cache['server_info'][id]['content'][key] = value
                            return True,"SS"
                        else:
                            return False,"VNC"
            elif type(self.bot.cache['server_info'][id]['content'][key]) == bool:
                if is_bool(value):
                    self.bot.cache['server_info'][id]['content'][key] = bool(value)
                    return True,"SS"
                return False,"WTB"
            elif type(self.bot.cache['server_info'][id]['content'][key]) == int:
                if is_int(string):
                    self.bot.cache['server_info'][id]['content'][key] = int(value)
                    return True,"SS"
                return False,"WTI"
            elif type(self.bot.cache['server_info'][id]['content'][key]) == dict:
                if not value in self.bot.cache['server_info'][id]['content'][key]:
                    if "member" in key:
                        if ismember(guild,value):
                            self.bot.cache['server_info'][id]['content'][key] = value
                            return True,"SSD"
                        else:
                            return False,"VNU"
                    elif "channel" in key:
                        if ischannel(guild,value):
                            self.bot.cache['server_info'][id]['content'][key] = value
                            return True,"SSD"
                        else:
                            return False,"VNC"
                return False,"VIS"
        else:
            return False,"DNE"

def ischannel(guild, channelName):
    for channel in guild.channels:
        if str(channel.id) == str(channelName):
            return True
    return False

def ismember(guild, memberName):
    for member in guild.members:
        if member.id == memberName:
            return True
    return False

def isrole(guild, roleName):
    for role in guild.roles:
        if str(role.id) == str(roleName):
            return True
    for role in guild.roles:
        if role.name == roleName:
            return True
    return False

def getSuffix(num):
    num = str(num)
    last = num[len(num)-1:len(num)]
    if num == "1":
        return "st"
    elif last == "2":
        return "nd"
    elif last == "3":
        return "rd"
    else:
        return "th"

def replace(text, guild, member):
    text = text.replace("%SERVER_NAME%",guild.name)
    text = text.replace("%SERVER_MEMBER_COUNT%",len(guild.members))
    text = text.replace("%SERVER_COUNT_SUFFIX%",getSuffix(len(guild.members)))
    text = text.replace("%SERVER_ICON_URL%",guild.icon_url)
    text = text.replace("%SERVER_OWNER_NAME%",guild.owner.name)
    text = text.replace("%SERVER_OWNER%",guild.owner.name + "#" + guild.owner.discriminator)
    text = text.replace("%SERVER_OWNER_ID%",guild.owner.id)
    text = text.replace("%MEMBER_NAME%",member.name)
    text = text.replace("%MEMBER%",member.name + "#" + member.discriminator)
    text = text.replace("%MEMBER_ID%",member.id)
    return text

class Management():

    def __init__(self, bot):
        self.bot = bot

    @asyncio.coroutine
    async def on_message(self, message):
        0

    @commands.group(pass_context=True)
    async def config(self, ctx):
        """Advanced config features (advanced users only)"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if ctx.invoked_subcommand is None:
                embed = discord.Embed(description=guildInfo['bot-prefix'] + "config <set/unset/get/apply/reload>")
                embed.add_field(name="get <key>", value="Get the value of a key", inline=True)
                embed.add_field(name="set <key> <value>", value="Assigns/Adds a value to a key", inline=True)
                embed.add_field(name="unset <key> <value>", value="Removes a value from a key. Only works with tables", inline=True)
                embed.add_field(name="apply", value="Saves current settings")
                embed.add_field(name="reload", value="Reloads settings (reverts changes to last apply)", inline=True)
                embed.add_field(name="reset", value="Resets entire config", inline=True)
                await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @config.command(pass_context=True)
    async def reset(self, ctx):
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            embed = discord.Embed(description="Are you sure you want to do this?\n\nDo `+settings > 1 > Export server config` to backup your old config.\n\nDo `+confirm` to reset config, enter anything else to cancel.")
            m = await ctx.send(embed=embed)
            r = await self.bot.wait_for("message", check=lambda c: (c.author == ctx.author))
            if r.content.lower() == "+confirm":
                taskStart = datetime.now()
                shutil.copy("default_server_config.json","Servers/" + str(ctx.guild.id) + ".json")
                taskEnd = datetime.now()
                taskLength = taskEnd - taskStart
                embed = discord.Embed(description="Completed reset in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
                await m.edit(embed=embed)
            else:
                await m.edit(embed=discord.Embed(description="Canceled reset"))
                return
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @config.command(pass_context=True)
    async def get(self, ctx, key : str):
        """Get a key's value"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if key.find(".") != -1:
                key, indKey = splitKey(key)
                if exists(guildInfo[key][indKey]):
                    embed = discord.Embed(description=str(guildInfo[key][indKey]))
                else:
                    embed = discord.Embed(description="This key does not exist")
            else:
                if exists(guildInfo[key]):
                    embed = discord.Embed(description=str(guildInfo[key][indKey]))
                else:
                    embed = discord.Embed(description="This key does not exist")
            await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @config.command(pass_context=True)
    async def set(self, ctx, key : str, value : str):
        """Assigns a value to a key"""
        """try:
            value = ctx.message.mentions[0].id
        except:
            0
        try:
            value = ctx.message.channel_mentions[0].id
        except:
            0"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            work,errorCode = set_attribute(self,guildInfo,key,value,str(ctx.message.guild.id),ctx.message.guild)
            print(str(work),errorCode)
            if work == False:
                if errorCode == "DNE":
                    embed = discord.Embed(description=key + " is not a valid key")
                    await ctx.send(embed=embed)
                elif errorCode == "WTB":
                    embed = discord.Embed(description=key + " requires a boolean and could not recognise " + key + " as one.")
                    await ctx.send(embed=embed)
                elif errorCode == "WTI":
                    embed = discord.Embed(description=key + " requires a intager and could not recognise " + key + " as one.")
                    await ctx.send(embed=embed)
                elif errorCode == "VIS":
                    embed = discord.Embed(description=value + " is already in " + key)
                    await ctx.send(embed=embed)
                elif errorCode == "VNU":
                    embed = discord.Embed(description="Could not find anyone on this guild with the id " + value)
                    await ctx.send(embed=embed)
                elif errorCode == "VNC":
                    embed = discord.Embed(description="Could not find a channel on this guild with the id " + value)
                    await ctx.send(embed=embed)
            else:
                if errorCode == "SSD":
                    embed = discord.Embed(description=key + " has been added to " + value + ". Dont forget to " + guildInfo['bot-prefix'] + "config apply to save your config")
                    await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description=key + " has been changed to " + value + ". Dont forget to " + guildInfo['bot-prefix'] + "config apply to save your config")
                    await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @config.command(pass_context=True)
    async def unset(self,ctx,key : str,value : str):
        """Remove a user from a key"""
        try:
            value = ctx.message.mentions[0].id
        except:
            0
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if key.find(".") != -1:
                key, indKey = splitKey(key)
                if type(self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'][key][indKey]) == dict:
                    if value in self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'][key][indKey]:
                        del self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'][key][indKey][value]
                        embed = discord.Embed(description="Removed " + value + " from " + key + "." + indKey)
                        await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(description=value + " is not in " + key + "." + indKey)
                        await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description="Cannot use " + guildInfo['bot-prefix'] + "unset with " + key)
                    await ctx.send(embed=embed)
            else:
                if type(self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'][key]) == dict:
                    if value in self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'][key]:
                        del self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'][key][value]
                        embed = discord.Embed(description="Removed " + value + " from " + key)
                        await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(description=value + " is not in " + key)
                        await ctx.send(embed=embed)
                else:
                    embed = discord.Embed(description="Cannot use " + guildInfo['bot-prefix'] + "unset with " + key)
                    await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @config.command(pass_context=True)
    async def apply(self,ctx):
        """Save current config details"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            taskStart = datetime.now()
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
            taskEnd = datetime.now()
            taskLength = taskEnd - taskStart
            embed = discord.Embed(description="Task completed in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
            await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @config.command(pass_context=True)
    async def reload(self,ctx):
        """Reload config from file"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            taskStart = datetime.now()
            self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'] = dataIO.load_json("Servers/" + str(ctx.message.guild.id) + ".json")
            taskEnd = datetime.now()
            taskLength = taskEnd - taskStart
            embed = discord.Embed(description="Task completed in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/1000) + "ms.")
            await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.group(pass_context=True)
    async def logging(self,ctx):
        """Manage logging functionality"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if ctx.invoked_subcommand is None:
                embed = discord.Embed(description=guildInfo['bot-prefix'] + "logging <enable/disable/setchannel>")
                embed.add_field(name=guildInfo['bot-prefix'] + "logging enable", value="Enables logging of guild information", inline=True)
                embed.add_field(name=guildInfo['bot-prefix'] + "logging disable", value="Disables logging of guild information", inline=True)
                embed.add_field(name=guildInfo['bot-prefix'] + "logging setchannel [#channel]", value="Tells welcomer to use the channel this command is ran in as the logging channel")
                await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @logging.command(name="enable",pass_context=True)
    async def loggingenable(self,ctx):
        """Enables logging on the guild"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['logging']['enable'] = True
            embed = discord.Embed(description="Logging has been enabled.")
            await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @logging.command(name="disable",pass_context=True)
    async def loggingdisable(self,ctx):
        """Disables logging on the guild"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['logging']['enable'] = False
            embed = discord.Embed(description="Logging has been disabled.")
            await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @logging.command(pass_context=True)
    async def setchannel(self,ctx,*args):
        """Sets channel to send logging info"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            print(args)
            channelid = ""
            if len(args) > 0:
                if is_int(args[0]):
                    if ischannel(ctx.message.guild,args[0]):
                        channelid = args[0]
                else:
                    for channel in ctx.message.guild.channels:
                        if channel.name == args[0]:
                            channelid = channel.id
                            break
            else:
                channelid = ctx.message.channel.id
            try:
                channelid = ctx.message.channel_mentions[0].id
            except:
                0
            self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['logging']['channel'] = str(channelid)
            embed = discord.Embed(description="Logging has set to use <#" + str(channelid) + ">")
            await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.group(pass_context=True)
    async def autorole(self,ctx):
        """Manages autorole features"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if ctx.invoked_subcommand is None:
                embed = discord.Embed(description="+autorole <enable/disable/setrole>")
                embed.add_field(name=guildInfo['bot-prefix'] + "autorole enable", value="Enables autorole for a new member to be assigned to", inline=True)
                embed.add_field(name=guildInfo['bot-prefix'] + "autorole disable", value="Disables autorole for when a new member joined", inline=True)
                embed.add_field(name=guildInfo['bot-prefix'] + "autorole setrole rolename", value="Sets a role that new users will be assigned when members join")
                await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @autorole.command(name="enable",pass_context=True)
    async def autoroleenable(self,ctx):
        """Enable autorole in member join"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if isrole(ctx.message.guild,guildInfo['autorole']['roleid']):
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['autorole']['enable'] = True
                embed = discord.Embed(description="Autorole has been enabled.")
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description="A role has not been assigned yet. Do `" + guildInfo['bot-prefix'] + "autorole setrole rolename` to do this.")
                await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @autorole.command(name="disable",pass_context=True)
    async def autoroledisable(self,ctx):
        """Disable autorole on member join"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['autorole']['enable'] = False
            embed = discord.Embed(description="Autorole has been disabled.")
            await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @autorole.command(pass_context=True)
    async def setrole(self,ctx,roleid : str):
        """Set autorole role"""
        try:
            roleid = ctx.message.role_mentions[0].id
        except:
            0
        print(roleid)
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if isrole(ctx.message.guild,roleid):
                if not is_int(roleid):
                    for role in ctx.message.guild.roles:
                        if role.name == roleid:
                            roleid = str(role.id)
                            break
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['autorole']['roleid'] = str(roleid)
                embed = discord.Embed(description="Autorole role id has been set to <@" + str(roleid) + ">")
                await ctx.send(embed=embed)
                dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
            else:
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['autorole']['roleid'] = str(roleid)
                embed = discord.Embed(description="Could not find the role you specified")
                await ctx.send(embed=embed)
                dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

def setup(bot):
    bot.add_cog(Management(bot))