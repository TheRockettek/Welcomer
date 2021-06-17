from discord.ext import commands
import os.path

def isimage(imagename):
    return os.path.isfile("Images/" + imagename + ".png")

def exists(variable):
    try:
        variable
        return True
    except:
        return False

def validhex(hex):
    try:
        int(hex,16)
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

def ischannel(guild, channelName):
    for channel in guild.channels:
        if str(channel.id) == str(channelName):
            return True
    return False

def ismember(guild, memberName):
    for member in guild.members:
        if str(member.id) == str(memberName):
            return True
    return False

def isrole(guild, roleName):
    for role in guild.roles:
        if str(role.id) == str(roleName):
            return True
    for role in guild.roles:
        if str(role.name) == str(roleName):
            return True
    return False

class Troubleshooter():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def troubleshooter(self, ctx):
        guildinfo = self.bot.get_guild_info(str(ctx.guild.id))
        errors = ""

        errors += "__Autorole__ **" + ("Enabled" if guildinfo['autorole']['enable'] == True else "Disabled") + "**\n"
        if isrole(ctx.guild,guildinfo['autorole']['roleid']):
            errors += "*No errors found*\n"
        else:
            errors += "- The role specified for autorole is invalid (**" + str(guildinfo['autorole']['roleid']) + "**)\n"

        errors += "__Blacklist__ **" + ("Enabled" if guildinfo['channel-blacklist']['enable'] == True else "Disabled") + "**\n"
        deadchannels = 0
        d = dict()
        for channel in guildinfo['channel-blacklist']['channels']:
            if not ischannel(ctx.guild,channel):
                deadchannels += 1
                d[channel] = True
        for dead in d:
            del self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-blacklist']['channels'][d]
        if deadchannels > 0:
            errors += "- **" + str(deadchannels) + " channels on blacklist do not exist.\n"
        else:
            errors += "*No errors found*\n"

        errors += "__Whitelist__ **" + ("Enabled" if guildinfo['channel-whitelist']['enable'] == True else "Disabled") + "**\n"
        deadchannels = 0
        for channel in guildinfo['channel-whitelist']['channels']:
            if not ischannel(ctx.guild,channel):
                deadchannels += 1
                del self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['channels'][channel]
        broke = False
        if deadchannels > 0:
            errors += "- **" + str(deadchannels) + " channels on whitelist do not exist.\n"
            broke = True
        if guildinfo['channel-whitelist']['enable'] == True:
            self.bot.cache['server_info'][str(ctx.guild.id)]['content']['channel-whitelist']['enable'] = False
            errors += "- Whitelist was enabled but no channels were on whitelist.\n"
            broke = True
        if broke == False:
            errors += "*No errors found*\n"

        errors += "__GreetDM__ **" + ("Enabled" if guildinfo['greet-dm']['enable'] == True else "Disabled") + "**\n"
        if len(guildinfo['greet-dm']['text'].split("|")) != 2:
            errors += "- Text on greet dm is not formatted correctly.\n"
        else:
            errors += "*No errors found*\n"
        
        errors += "__Leaver__ **" + ("Enabled" if guildinfo['leaver']['enable'] == True else "Disabled") + "**\n"
        broke = False
        if guildinfo['leaver']['enable']:
            if not ischannel(ctx.guild,guildinfo['leaver']['channel']):
                errors += "- Specified channel no longer exists (**" + str(guildinfo['leaver']['channel']) + "**)\n"
                broke = True
        if len(guildinfo['leaver']['text']) > 2000:
            errors += "- Text set is too long (**" + str(len(guildinfo['leaver']['text'])) + " > 2000**)\n"
            broke = True
        if len(guildinfo['leaver']['text']) == 0:
            errors += "- Text has not been set.\n"
            broke = True
        if broke == False:
            errors += "*No errors found*\n"

        errors += "__Logging__ **" + ("Enabled" if guildinfo['logging']['enable'] == True else "Disabled") + "**\n"
        if not ischannel(ctx.guild,guildinfo['logging']['channel']):
            errors += "- Specified channel no longer exists (**" + str(guildinfo['logging']['channel']) + "**)\n"
        else:
            errors += "*No errors found*\n"

        errors += "__Welcomer__ **" + ("Enabled" if guildinfo['welcomer']['enable'] == True else "Disabled") + "**\n"
        broke = False
        if not ischannel(ctx.guild,guildinfo['logging']['channel']):
            errors += "- Specified channel no longer exists (**" + str(guildinfo['logging']['channel']) + "**)\n"
            broke = True
        if not isimage(guildinfo['welcomer']['background']):
            errors += "- **" + str(guildinfo['welcomer']['background']) + "** is not a valid background.\n"
            self.bot.cache['server_info'][str(ctx.guild.id)]['content']['welcomer']['background'] = "default"
        if len(guildinfo['greet-dm']['text'].split("|")) < 4:
            errors += "- Image text is not formatted correctly.\n"
            broke = True
        if not validhex(guildinfo['welcomer']['tclr']):
            errors += "- Text colour is not valid hex (**" + str(guildinfo['welcomer']['tclr']) + "**).\n"
            broke = True
        if not validhex(guildinfo['welcomer']['cclr']):
            errors += "- Circle colour is not valid hex (**" + str(guildinfo['welcomer']['cclr']) + "**).\n"
            broke = True
        errors += "\n\n"
        if guildinfo['welcomer']['enable'] == True:
            errors += ":information_source: Image greetings are **" + ("Enabled" if guildinfo['welcomer']['use-image'] == True else "Disabled") + "**\n"
            if guildinfo['welcomer']['use-image'] == False:
                errors += "To enable images do `+config set welcomer.use-image True`\n"
            errors += ":information_source: Text greetings are **" + ("Enabled" if guildinfo['welcomer']['use-text'] == True else "Disabled") + "**\n"
            if guildinfo['welcomer']['use-text'] == False:
                errors += "To enable text do `+config set welcomer.use-text True`\n"
            errors += ":information_source: DM greetings are **" + ("Enabled" if guildinfo['greet-dm']['enable'] == True else "Disabled") + "**\n"
            if guildinfo['greet-dm']['enable'] == False:
                errors += "To enable greet dms do `+config set greet-dm.enable True`\n"
            if guildinfo['welcomer']['use-text'] == False and guildinfo['welcomer']['use-text'] == False:
                errors += "- Welcomer is enabled but neither image or text is enabled.\n"
                broke = True
        if broke == False:
            errors += "*No errors found*\n"

        await ctx.send(errors)

def setup(bot):
    bot.add_cog(Troubleshooter(bot))