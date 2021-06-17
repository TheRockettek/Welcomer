import aiohttp, asyncio, discord, time, re, math
from urllib.parse import urlparse
from discord.ext import commands

def ischannel(channels, channelID):
    for channel in channels:
        if str(channel.id) == str(channelID):
            return True
    return False

blockednames = {"grabify","iplogger","blasze","whatstheirip","fuglekos","ipgrabber","ip-grabber","ip-","bit.ly","bmwforum.co","leancoding.co","quickmessage.io","spottyfly.com","spötify","stopify","yoütu","yoütübe","xda-developers.io","starbucks.bio","starbucksiswrong.com","starbucksisbadforyou.com","bucks","discörd","minecräft","shört","cyberh1"}
prophanity = {"2g1c", "2 girls 1 cup", "acrotomophilia", "alabama hot pocket", "alaskan pipeline", "anal", "anilingus", "anus", "apeshit", "arsehole", "ass", "asshole", "assmunch", "auto erotic", "autoerotic", "babeland", "baby batter", "baby juice", "ball gag", "ball gravy", "ball kicking", "ball licking", "ball sack", "ball sucking", "bangbros", "bareback", "barely legal", "barenaked", "bastard", "bastardo", "bastinado", "bbw", "bdsm", "beaner", "beaners", "beaver cleaver", "beaver lips", "bestiality", "big black", "big breasts", "big knockers", "big tits", "bimbos", "birdlock", "bitch", "bitches", "black cock", "blonde action", "blonde on blonde action", "blowjob", "blow job", "blow your load", "blue waffle", "blumpkin", "bollocks", "bondage", "boner", "boob", "boobs", "booty call", "brown showers", "brunette action", "bukkake", "bulldyke", "bullet vibe", "bullshit", "bung hole", "bunghole", "busty", "butt", "buttcheeks", "butthole", "camel toe", "camgirl", "camslut", "camwhore", "carpet muncher", "carpetmuncher", "chocolate rosebuds", "circlejerk", "cleveland steamer", "clit", "clitoris", "clover clamps", "clusterfuck", "cock", "cocks", "coprolagnia", "coprophilia", "cornhole", "coon", "coons", "creampie", "cum", "cumming", "cunnilingus", "cunt", "darkie", "date rape", "daterape", "deep throat", "deepthroat", "dendrophilia", "dick", "dildo", "dingleberry", "dingleberries", "dirty pillows", "dirty sanchez", "doggie style", "doggiestyle", "doggy style", "doggystyle", "dog style", "dolcett", "domination", "dominatrix", "dommes", "donkey punch", "double dong", "double penetration", "dp action", "dry hump", "dvda", "eat my ass", "ecchi", "ejaculation", "erotic", "erotism", "escort", "eunuch", "faggot", "fecal", "felch", "fellatio", "feltch", "female squirting", "femdom", "figging", "fingerbang", "fingering", "fisting", "foot fetish", "footjob", "frotting", "fuck", "fuck buttons", "fuckin", "fucking", "fucktards", "fudge packer", "fudgepacker", "futanari", "gang bang", "gay sex", "genitals", "giant cock", "girl on", "girl on top", "girls gone wild", "goatcx", "goatse", "god damn", "gokkun", "golden shower", "goodpoop", "goo girl", "goregasm", "grope", "group sex", "g-spot", "guro", "hand job", "handjob", "hard core", "hardcore", "hentai", "homoerotic", "honkey", "hooker", "hot carl", "hot chick", "how to kill", "how to murder", "huge fat", "humping", "incest", "intercourse", "jack off", "jail bait", "jailbait", "jelly donut", "jerk off", "jigaboo", "jiggaboo", "jiggerboo", "jizz", "juggs", "kike", "kinbaku", "kinkster", "kinky", "knobbing", "leather restraint", "leather straight jacket", "lemon party", "lolita", "lovemaking", "make me come", "male squirting", "masturbate", "menage a trois", "milf", "missionary position", "motherfucker", "mound of venus", "mr hands", "muff diver", "muffdiving", "nambla", "nawashi", "negro", "neonazi", "nigga", "nigger", "nig nog", "nimphomania", "nipple", "nipples", "nsfw images", "nude", "nudity", "nympho", "nymphomania", "octopussy", "omorashi", "one cup two girls", "one guy one jar", "orgasm", "orgy", "paedophile", "paki", "panties", "panty", "pedobear", "pedophile", "pegging", "penis", "phone sex", "piece of shit", "pissing", "piss pig", "pisspig", "playboy", "pleasure chest", "pole smoker", "ponyplay", "poof", "poon", "poontang", "punany", "poop chute", "poopchute", "porn", "porno", "pornography", "prince albert piercing", "pthc", "pubes", "pussy", "queaf", "queef", "quim", "raghead", "raging boner", "rape", "raping", "rapist", "rectum", "reverse cowgirl", "rimjob", "rimming", "rosy palm", "rosy palm and her 5 sisters", "rusty trombone", "sadism", "santorum", "scat", "schlong", "scissoring", "semen", "sex", "sexo", "sexy", "shaved beaver", "shaved pussy", "shemale", "shibari", "shit", "shitblimp", "shitty", "shota", "shrimping", "skeet", "slanteye", "slut", "s&m", "smut", "snatch", "snowballing", "sodomize", "sodomy", "spic", "splooge", "splooge moose", "spooge", "spread legs", "spunk", "strap on", "strapon", "strappado", "strip club", "style doggy", "suck", "sucks", "suicide girls", "sultry women", "swastika", "swinger", "tainted love", "taste my", "tea bagging", "threesome", "throating", "tied up", "tight white", "tit", "tits", "titties", "titty", "tongue in a", "topless", "tosser", "towelhead", "tranny", "tribadism", "tub girl", "tubgirl", "tushy", "twat", "twink", "twinkie", "two girls one cup", "undressing", "upskirt", "urethra play", "urophilia", "vagina", "venus mound", "vibrator", "violet wand", "vorarephilia", "voyeur", "vulva", "wank", "wetback", "wet dream", "white power", "wrapping men", "wrinkled starfish", "xx", "xxx", "yaoi", "yellow showers", "yiffy", "zoophilia", "🖕"}

def allowed(url):
    url = url.lower()
    url = urlparse(url).netloc
    for blocked in blockednames:
        if blocked in url:
            return False, blocked
    return True, ""

async def getFinal(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"user-agent": "WelcomerBoi/3.0"}) as resp:
            return str(resp.url)

def extractURLS(string):
    return re.findall(r'(https?://[^\s]+)', string)

def extractInvites(string):
    return re.findall(r'discord.gg/[a-zA-Z0-9]+', string)

def getrole(roles,name):
    for role in roles:
        if role.name == name:
            return role
    return False

automodcache = dict()
lastmsg = dict()

class AutoModHandler():

    def __init__(self, bot):
        self.bot = bot
        self.automodcache = dict()

    @commands.group()
    async def automod(self, ctx):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            if ctx.invoked_subcommand is None:
                guildinfo = await self.bot.get_guild_info(ctx.guild.id)
                possiblevalues = "`" + "` `".join(list(i for i,k in guildinfo['automod'].items() if i != "enable")) + "`"
                if guildinfo['automod']['enable'] == True:
                    enabled = "**Currently moderating**\n`" + ("` `".join(list(i for i,k in guildinfo['automod'].items() if i != "enable" and k == True))) + "`"
                else:
                    enabled = ":information_source: **Automod is currently disabled**"
                await ctx.send(f":nut_and_bolt: __**AutoMod commands usage**__\nautomod <enable/disable/moderate/unmoderate>\n- enable: Enables automod\n- disable: Disables automod\n- moderate <key>: Moderates <key>\n- unmoderate <key>: Stops moderating <key>\n\n{enabled}\n\n**Possible keys**\n{possiblevalues}\n\n")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @automod.command(name="enable")
    async def enableam(self, ctx, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            guildinfo['automod']['enable'] = True
            if str(message.guild.id) in self.bot.cogs['AutoModHandler'].automodcache:
                del self.bot.cogs['AutoModHandler'].automodcache[str(message.guild.id)]
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
            await ctx.send(f":nut_and_bolt: __**AutoMod**__: \nAutomod has been **enabled**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @automod.command(name="disable")
    async def disableam(self, ctx, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            guildinfo['automod']['enable'] = False
            if str(message.guild.id) in self.bot.cogs['AutoModHandler'].automodcache:
                del self.bot.cogs['AutoModHandler'].automodcache[str(message.guild.id)]
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
            await ctx.send(f":nut_and_bolt: __**AutoMod**__: \nAutomod has been **disabled**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @automod.command(name="moderate")
    async def moderateam(self, ctx, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            if key == "":
                possiblevalues = "`" + "` `".join(list(i for i,k in guildinfo['automod'].items() if i != "enable")) + "`"
                await ctx.send(f":nut_and_bolt: __**AutoMod**__: \nNo key was provided. Possible values:\n{possiblevalues}")
                return
            if not key in guildinfo['automod']:
                await ctx.send(f":nut_and_bolt: __**AutoMod**__: \n**{key}** is not a valid key")
                return
            if type(guildinfo['automod'][key]) != bool:
                await ctx.send(f":nut_and_bolt: __**AutoMod**__: \n**{key}** cannot be modified via moderate")
                return
            guildinfo['automod'][key] = True
            if str(message.guild.id) in self.bot.cogs['AutoModHandler'].automodcache:
                del self.bot.cogs['AutoModHandler'].automodcache[str(message.guild.id)]
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
            await ctx.send(f":nut_and_bolt: __**AutoMod**__: \nAutomod will now moderate **{key}**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @automod.command(name="unmoderate")
    async def unmoderateam(self, ctx, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            if key == "":
                possiblevalues = "`" + "` `".join(list(i for i,k in guildinfo['automod'].items() if i != "enable")) + "`"
                await ctx.send(f":nut_and_bolt: __**AutoMod**__: \nNo key was provided. Possible values:\n{possiblevalues}")
                return
            if not key in guildinfo['automod']:
                await ctx.send(f":nut_and_bolt: __**AutoMod**__: \n**{key}** is not a valid key")
                return
            if type(guildinfo['automod'][key]) != bool:
                await ctx.send(f":nut_and_bolt: __**AutoMod**__: \n**{key}** cannot be modified via unmoderate")
                return
            guildinfo['automod'][key] = False
            if str(message.guild.id) in self.bot.cogs['AutoModHandler'].automodcache:
                del self.bot.cogs['AutoModHandler'].automodcache[str(message.guild.id)]
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
            await ctx.send(f":nut_and_bolt: __**AutoMod**__: \nAutomod will no longer moderate **{key}**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @asyncio.coroutine
    async def on_message(self, message):
        if message.author.bot == True:
            return
        if str(message.guild.id) in automodcache:
            if time.time() > self.automodcache[str(message.guild.id)]['ttl']:
                d = (await self.bot.get_guild_info(message.guild.id))
                self.automodcache[str(message.guild.id)]['automod'] = d['automod']
                self.automodcache[str(message.guild.id)]['logging'] = d['logging']
                self.automodcache[str(message.guild.id)]['ttl'] = time.time() + 600
        else:
            d = (await self.bot.get_guild_info(message.guild.id))
            self.automodcache[str(message.guild.id)] = dict()
            self.automodcache[str(message.guild.id)]['automod'] = d['automod']
            self.automodcache[str(message.guild.id)]['logging'] = d['logging']
            self.automodcache[str(message.guild.id)]['ttl'] = time.time() + 600
        guilddata = self.automodcache[str(message.guild.id)]

        if self.automodcache[str(message.guild.id)]['automod']['enable'] == False:
            return

        """
        if not str(message.author.id) in lastmsg:
            lastmsg[str(message.author.id)] = {"t": time.time(), "v": 0, "w": 0, "wc": 0}
        if (time.time() - lastmsg[str(message.author.id)]['t']) < 1:
            lastmsg[str(message.author.id)]['t'] = time.time()
            lastmsg[str(message.author.id)]['wc'] += 1
            lastmsg[str(message.author.id)]['v'] += 1
            if lastmsg[str(message.author.id)]['v'] >= 12:
                # give muted role
                if guilddata['logging']['enable'] == True and guilddata['logging']['automod'] == True and ischannel(message.guild.channels, guilddata['logging']['channel']):
                    await self.bot.get_channel(guilddata['logging']['channel']).send("[**" + time.strftime(guilddata['logging']['timeformat'], time.gmtime()) + "**]:nut_and_bolt: Given **" + str(message.author) + "**'s mute due to spam. Reached spam violation threshold")
            lastmsg[str(message.author.id)]['t'] = time.time()
            if lastmsg[str(message.author.id)]['wc'] >= 5:
                lastmsg[str(message.author.id)]['wc'] = 0
                print("Pruned " + str(message.author.id))
                await message.channel.purge(limit=5, check=lambda m: m.author.id == message.author.id, bulk=True)
                #m = await message.channel.send("<@" + str(message.author.id) + "> Woah calm down there! (" + str(math.ceil(lastmsg[str(message.author.id)]['v']/12)) + "/4)")
            await asyncio.sleep(30)
            lastmsg[str(message.author.id)]['v'] -= 1
            return
        else:
            lastmsg[str(message.author.id)]['t'] = time.time()

        if not str(message.author.id) in lastmsg:
            lastmsg[str(message.author.id)] = {"v": 0, "t": time.time(), "w": 0}
        lastmsg[str(message.author.id)]['v'] += 1
        if lastmsg[str(message.author.id)]['v'] >= 3:
            print((time.time() - lastmsg[str(message.author.id)]['t']))
            msgs = lastmsg[str(message.author.id)]['v']
            if (time.time() - lastmsg[str(message.author.id)]['t']) < 2:
                print("Prune " + str(message.author.id))
                lastmsg[str(message.author.id)]['w'] += 1
                await message.channel.purge(limit=msgs, check=lambda m: m.author.id == message.author.id, bulk=True)
                await asyncio.sleep(30)
                lastmsg[str(message.author.id)]['w'] -= 1
                return
            lastmsg[str(message.author.id)]['v'] = 0
            lastmsg[str(message.author.id)]['t'] = time.time()
        """

        if guilddata['automod']['swearing'] == True:
            censor = False
            censorship = message.content
            for christianword in prophanity:
                if christianword in censorship:
                    censor = True
                    censorship = censorship.replace(christianword,christianword[0] + "*"*(len(christianword)-2) + christianword[-1])
            if censor == True:
                if await self.bot.is_elevated(message.author, message.guild):
                    return
                await message.delete()
                if guilddata['logging']['enable'] == True and guilddata['logging']['automod'] == True and ischannel(message.guild.channels, guilddata['logging']['channel']):
                    await self.bot.get_channel(guilddata['logging']['channel']).send(f"[**{time.strftime(guilddata['logging']['timeformat'], time.gmtime())}**]:nut_and_bolt: Removed **{str(message.author)}**'s mute due to swearing. Origional message: `{censorship}`")
                m = await message.channel.send(f"<@{str(message.author.id)}> Please do not use that type of language here")
                await asyncio.sleep(60)
                await m.delete()
                return
        if (len(message.mentions) >= guilddata['automod']['mentionthreshold']) and guilddata['automod']['mentions'] == True:
            if await self.bot.is_elevated(message.author, message.guild):
                return
            await message.delete()
            id = await self.bot.add_punishment({"t": 8, "gd": message.guild.id ,"ux": time.time(), "rs": f"Mentioning too many users ( {str(message.mentions)} > {str(guilddata['automod']['mentionthreshold'])} )", "mo": 330416853971107840, "p": str(message.author)})
            userdata = await self.bot.get_user_info(message.author.id)
            userdata['records'][id] = True
            await self.bot.update_user_info(message.author.id,userdata)
            if guilddata['logging']['enable'] == True and guilddata['logging']['automod'] == True and ischannel(message.guild.channels, guilddata['logging']['channel']):
                await self.bot.get_channel(guilddata['logging']['channel']).send(f"[**{time.strftime(guilddata['logging']['timeformat'], time.gmtime())}**]:nut_and_bolt: Removed **{str(message.author)}**'s message due to containing too many mentions ( {str(message.mentions)} > {str(guilddata['automod']['mentionthreshold'])} )")
            m = await message.channel.send(f"<@{str(message.author.id)}> Please do not mention too many users ( {str(len(message.mentions))} > {str(guilddata['automod']['mentionthreshold'])} )")
            await asyncio.sleep(60)
            await m.delete()
            return

        messageurls = extractURLS(message.content)
        fmessageurls = dict()
        if len(messageurls) > 0:
            for messageurl in messageurls:
                fmessageurls[len(fmessageurls)] = await getFinal(messageurl) # incase it redir
            if len(messageurls) > 0:
                if guilddata['automod']['url'] == True:
                    if await self.bot.is_elevated(message.author, message.guild):
                        return
                    await message.delete()
                    m = await message.channel.send(f"<@{str(message.author.id)}> URLs are not permitted in messages")
                    await asyncio.sleep(60)
                    await m.delete()
                    return
                for index, url in fmessageurls.items():
                    if "discordapp.com/invite" in url or "discord.gg/" in url or len(extractInvites(message.content)) > 0:
                        if guilddata['automod']['invites'] == False:
                            return
                        if await self.bot.is_elevated(message.author, message.guild):
                            return
                        await message.delete()
                        url = url.replace("https://discordapp.com/invite/","")
                        try:
                            invite = await self.bot.get_invite(url)
                            valid = True
                        except:
                            try:
                                invite = extractInvites(message.content)[0]
                                invite = await self.bot.get_invite(invite)
                                valid = True
                            except:
                                valid = False
                        userdata = await self.bot.get_user_info(message.author.id)
                        id = await self.bot.add_punishment({"t": 8, "gd": message.guild.id ,"ux": time.time(), "rs": f"Posting an Invite Link: {invite.id}", "mo": 330416853971107840, "p": str(message.author)})
                        userdata['records'][id] = True
                        await self.bot.update_user_info(message.author.id,userdata)
                        if guilddata['logging']['enable'] == True and guilddata['logging']['automod'] == True and ischannel(message.guild.channels, guilddata['logging']['channel']):
                            await self.bot.get_channel(guilddata['logging']['channel']).send(f"[**{time.strftime(guilddata['logging']['timeformat'], time.gmtime())}**]:nut_and_bolt: Removed **{str(message.author)}**'s message due to containing an invite link: `{invite.id}`")
                        m = await message.channel.send(f"<@{str(message.author.id)}> Your invite link has been removed")
                        await asyncio.sleep(60)
                        await m.delete()
                        return
                    goodurl, blockedname = allowed(messageurls[index])
                    if not goodurl:
                        if await self.bot.is_elevated(message.author, message.guild):
                            return
                        await message.delete()
                        userdata = await self.bot.get_user_info(message.author.id)
                        id = await self.bot.add_punishment({"t": 8, "gd": message.guild.id ,"ux": time.time(), "rs": f"Sending a blacklisted URL: {messageurls[index]} => {fmessageurls[index]}", "mo": 330416853971107840, "p": str(message.author)})
                        userdata['records'][id] = True
                        await self.bot.update_user_info(message.author.id,userdata)
                        if guilddata['logging']['enable'] == True and guilddata['logging']['automod'] == True and ischannel(message.guild.channels, guilddata['logging']['channel']):
                            await self.bot.get_channel(guilddata['logging']['channel']).send(f"[**{time.strftime(guilddata['logging']['timeformat'], time.gmtime())}**]:nut_and_bolt: Removed **{str(message.author)}**'s message due to containing a blacklisted link: `{messageurls[index]}`\nSafe url: `{fmessageurls[index]}`")
                        m = await message.channel.send(f"<@{str(message.author.id)}> This type of url is not permitted on discord ({blockedname}). Safe url: `{fmessageurls[index]}`")
                        await asyncio.sleep(60)
                        await m.delete()
                        return

                    if messageurls[index] != fmessageurls[index]:
                        await message.channel.send(f"A URL in this message redirects! Origional URL: `{messageurls[index]}` Final URL `{fmessageurls[index]}`")

                        
def setup(bot):
    bot.add_cog(AutoModHandler(bot))