import asyncio, random, discord, json, requests, re, aiohttp, math
from discord.ext import commands
from urllib.parse import urlparse
from time import time
import html2text

CustomMessages = dict()

opstaff = {"Melonz","RyJamsCastle","jamatosaurex","SumoSnorlax","VoxaDub"}

CustomMessages['349893105543151616'] = dict()
file_content = open('349893105543151616.custom')
file_content = file_content.readlines()
for lines in file_content[0:]:
    CustomMessages['349893105543151616'][len(CustomMessages['349893105543151616'])] = lines

@asyncio.coroutine
async def get_emote_list(self, id):
    emojilist = self.bot.get_guild(id).emojis
    for emoji in emojilist:
        self.bot.customemotes[emoji.name] = str(emoji.id)

def allowed(url):
    url = url.lower()
    url = urlparse(url).netloc
    for blocked in blockednames:
        if blocked in url:
            return False, blocked
    return True, ""


def extractURLS(string):
    return re.findall(r'(https?://[^\s]+)', string)

def nicify(i,t,stri):
    if i == 0:
        stri = ""
    for key, value in t.items():
        if type(value) == dict:
            stri += "║"*i + "╠" + key + ":\n"
            i += 1
            stri = nicify(i+1,value,stri)
        else:
            stri += "║"*i + "╠" + key + ": " + str(value) + "\n"
    return stri

def getrole(roles,name):
    for role in roles:
        if role.name == name:
            return role
    return False

class CustomStuff():

    def __init__(self,bot):
        self.bot = bot

    @commands.command()
    async def dcheck(self, ctx):
        print(dir(ctx))
        user = ctx.mentions[0]
        await ctx.send(nicify(0,user,""))

    @commands.command()
    async def gsay(self, ctx, message="Hello World"):
        await get_emote_list(self, 341685098468343822)
        s = message
        n = ""
        for i in range(1,len(s)+1):
            if "r"+s[i-1].lower() in self.bot.customemotes:
                n += "<a:r" + s[i-1].lower() + ":" + str(self.bot.customemotes["r"+s[i-1].lower()]) + ">"
            else:
                n += s[i-1]
        print(n)
        await ctx.send("`" + n + "`")

    @commands.command(aliases=['boobs'])
    async def porn(self, ctx):
        embed = discord.Embed(title="Hey there! Did you know running discord bots arent cheap?", colour=discord.Colour(0x2c363e), description="Thanks to the wonderful people at Boobbot we are able to keep welcomer and its kohorts up and running 24/7! If it wasnt for them this bot would of never even been existant in the first place and it wouldnt make sence to not add their discord bot and credit them for the wonderful things they have done <a:blubbounce:402658918020677635>")
        embed.set_thumbnail(url="https://cdn.discordapp.com/app-icons/285480424904327179/3b0ddd147a565307705b6735c45ef448.png?size=128")
        embed.add_field(name="Invite Boobbot to your server", value="[Invite bot](https://bot.boobbot.us/)", inline=True)
        embed.add_field(name="Credits", value="**Tails™#0420**\nfor graciously hosting the bot on their lovely vps and supplying help when needed to make the bot more friendly.\n\n**Waspy#0669**\nfor being nice sometimes and waking me up with a million pings")
        await ctx.send(embed=embed)

    @commands.command()
    async def gag(self, ctx, user : discord.Member, reason="Unspecified"):
        guildInfo = self.bot.get_guild_info(ctx.guild.id)
        if (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            try:
                await user.edit(mute=True)
                await ctx.send("**" + str(user) + "** has been gagged")
                await user.send("You have been gagged in **" + str(ctx.guild) + "** by **" + str(ctx.author) + "** for **" + reason + "**")
            except Exception as e:
                await ctx.send("I couldnt gag this user\n```" + str(e) + "```")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.command()
    async def giverole(self, ctx, role : str, member : discord.Member):
        guildInfo = self.bot.get_guild_info(ctx.guild.id)
        pos = ctx.author.roles[-1].position
        if (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            print(type(member))
            if not type(member) == discord.Member:
                member = ctx.author
            arole = getrole(ctx.guild.roles,role)
            if ctx.author.id != 143090142360371200:
                if arole.position > pos:
                    await ctx.send("You cannot assign a role higher than you. (" + str(arole.position) + " > " + str(pos) + ")")
                    return
            if arole != False:
                try:
                    await member.add_roles(arole)
                    await ctx.send("You have assigned the `" + str(arole.name) + "`")
                except Exception as e:
                    await ctx.send("Couldnt assign role \n```" + str(e) + "```")
            else:
                await ctx.send("This role doesnt exist")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.command()
    async def ungag(self, ctx, user : discord.Member, reason="Unspecified"):
        guildInfo = self.bot.get_guild_info(ctx.guild.id)
        if (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            try:
                await user.edit(mute=False)
                await ctx.send("**" + str(user) + "** has been ungagged")
                await user.send("You have been ungagged in **" + str(ctx.guild) + "** by **" + str(ctx.author) + "** for **" + reason + "**")
            except Exception as e:
                await ctx.send("I couldnt ungag this user\n```" + str(e) + "```")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.command()
    async def server(self, ctx, ip="opmines.net"):
        """
        async with aiohttp.ClientSession() as session:
        async with session.get("https://api.mcsrvstat.us/1/opmines.net", headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36"}) as resp:
        st = await resp.read()"""
        st = requests.get("https://api.mcsrvstat.us/1/" + ip)
        print(st)
        st = st.text
        print(st)
        serverdata = json.loads(st)
        players = ""
        p = 0
        hasp = False
        if "players" in serverdata:
            if "list" in serverdata['players']:
                hasp = True
                for member in serverdata['players']['list']:
                    p += 1
                    if len(players) != 0:
                        players += " , "
                    if member.lower() in opstaff:
                        players += "**"+member+"** :star:"
                    else:
                        players += member
        embed = discord.Embed(title="Server Status")
        if ip == "opmines.net":
            embed.set_thumbnail(url="http://files.enjin.com/780854/opmines%20logo%20222.png")
        embed.add_field(name="Status", value="Online" if not "offline" in serverdata else "Offline")
        if hasp == True:
            per = math.floor((serverdata['players']['online']/serverdata['players']['max'])*1000)/10
            embed.add_field(name="Members Online", value=str(serverdata['players']['online']) + " / " + str(serverdata['players']['max']) + " (" + str(per) + "%)")
        try:
            embed.add_field(name="Connection Stats", value=serverdata['ip'] + ":" + str(serverdata['port']) + " / " + serverdata['version'], inline=True)
        except:
            embed.add_field(name="Connection Stats", value=serverdata['ip'] + ":" + str(serverdata['port']) + " / ?", inline=True)
        try:
            embed.add_field(name="MOTD", value=html2text.html2text(serverdata['motd']['html'][0]).replace("\\","").replace("</span>","").replace("\n","").replace("*","\\*").replace("_","\\_").replace("~","\\~"))
        except:
            embed.add_field(name="MOTD", value="?")
        try:
            embed.add_field(name="Player List (" + str(p) + ")", value=players)
        except:
            embed.add_field(name="Player List (unable to retrieve)", value="This server may be offline")
        await ctx.send(embed=embed)

    """
        @commands.command()
        async def boot(self, ctx, id:str, reason="Unspecified"):
            guildInfo = self.bot.get_guild_info(ctx.guild.id)
            if (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
                id = str(id)
                await ctx.send(":warning: ***Do not use this command without permission. If you use this for malacious reasons you will be immediately demoted and gbanned. All uses of this command is logged.***\nPlease type \'yes\' to continue")
                if str(id) in self.bot.globalbans:
                    msg = await self.bot.wait_for('message', check=lambda u: u.author.id == ctx.message.author.id)
                    if msg.content == "yes":
                        await ctx.send("Ok")
                        for s in self.bot.guilds:
                            for m in s.members:
                                if str(m.id) == id:
                                    try:
                                        await s.ban(m,reason="Banned by " + ctx.author + ": " + reason)
                                        await ctx.send("Removed from " + str(s))
                                    except Exception as e:
                                        await ctx.send("Could not remove from " + str(s) + " `" + e + "`")
                        await ctx.send("Ive done it.")
                    else:
                        await ctx.send("Aborted")
                        return
                else:
                    await ctx.send("Dont you dare do that.")
                    return
            else:  
                m = await ctx.send("Yeah you shouldnt try run this.")
                await asyncio.sleep(3)
                await m.delete()
"""

    @asyncio.coroutine
    async def on_member_join(self,member):
        if member.guild.id == "349893105543151616":
            message = random.randint(1,len(CustomMessages['349893105543151616']))
            message = CustomMessages['349893105543151616'][message]
            message = message.replace("%","<@" + member.id + ">")
            await self.bot.send_message(self.bot.get_channel(self.bot.cache['guild_info'][member.guild.id]['content']['welcomer']['channel']),message)

    @commands.command()
    async def purify(self, ctx):
        embed = discord.Embed(title="Purify thou thot!", description=":cross: I have purified your body and removed all " + str(random.randint(2,50)) + " sins from you!")
        embed.set_image(url="http://s.storage.akamai.coub.com/get/b85/p/coub/simple/cw_timeline_pic/7f1478f535a/dd4559060b12730cf9230/big_1473918436_image.jpg")
        await bot.say(embed=embed)

    @commands.command()
    async def scrape(self, ctx):
        leave = 0
        d = 0
        n = 0
        s = ""
        o = False
        for guild in self.bot.guilds:
            try:
                bots = 0
                total = 0
                for member in guild.members:
                    total += 1
                    if member.id == 143090142360371200:
                        o = True
                    if member.bot == True:
                        bots += 1
                PercentageBots = bots/total
                if PercentageBots > 0.75:
                    d += 1
                    if not "bot" in guild.name.lower() and o == False:
                        leave += 1
                        n += 1
                        s += "[bot] Left " + str(guild.name) + "\n"
                        if n == 10:
                            await ctx.send(s)
                            n = 0
                            s = ""
                        await guild.leave()
                if total < 5:
                    leave += 1
                    n += 1
                    s += "[sml] Left " + str(guild.name) + "\n"
                    if n == 10:
                        await ctx.send(s)
                        n = 0
                        s = ""
                    await guild.leave()
                o = False
            except Exception as e:
                print(e)
        await ctx.send(str(leave))
    @commands.command()
    async def channellisttest(self, ctx):
        clist = dict()
        for category in ctx.guild.categories:
            id = category.position
            clist[id] = dict()
            clist[id]['name'] = category.name
            clist[id]['c'] = dict()
            for channel in category.channels:
                clist[id]['c'][channel.position] = dict()
                clist[id]['c'][channel.position]['id'] = str(channel.id)
                clist[id]['c'][channel.position]['n'] = channel.name
        s = "<select>"
        for category in pairs(clist):
            print(category)
            s += "<option disabled=\"test\"> -- " + category['name'].upper() + " -- </option>"
            for channel in pairs(category['c']):
                print(channel)
                s += "<option value=\"" + str(channel['id']) + "\"> #" + channel['n'] + " (" + str(channel['id']) + ")</option>"
        s += "</select>"
        await ctx.send(clist)
        await ctx.send(file=discord.File(s,"test.html"))

    @commands.command()
    async def biggest(self, ctx):
        biggestservers = dict()
        for server in self.bot.guilds:
            if len(server.members) > 1000:
                biggestservers[server.name] = server.member_count
        s = "```"
        print(biggestservers)
        o = 1
        def f(e):
            print(biggestservers[e])
            return biggestservers[e]
        sortd = sorted(biggestservers, key=f, reverse=True)
        print(sortd)
        for item in sortd:
            s += str(o) + ") " + item + ": " + str(biggestservers[item]) + "\n"
            o += 1
            if o == 11:
                break
        s += "```"
        await ctx.send(s)

    @commands.command()
    async def noods(self, ctx):
        embed = discord.Embed()
        embed.set_image(url="https://pics.me.me/high-quality-noods-23273452.png")
        m = await ctx.send(embed=embed)
        await asyncio.sleep(60)
        await m.delete()

    @commands.command()
    async def dicklength(self, ctx):
        if len(ctx.message.mentions) > 0:
            random.seed(ctx.message.mentions[0].id)
        else:
            random.seed(ctx.author.id)
        length = random.randint(1,30)
        cm = length * 2.54
        await ctx.send("8" + "="*length + "D\nNow thats a long one! " + str(length) + " inches (" + str(cm) + "cm). The ladies will be impressed with that.")

    @commands.command()
    async def ratewaifu(self, ctx):
        if len(ctx.message.mentions) > 0:
            random.seed(ctx.author.id * ctx.message.mentions[0].id)
        else:
            await ctx.send(":broken_heart: No waifu? No laifu. (Please tag your waifu)")
        if ctx.message.mentions[0].id == ctx.author.id:
            await ctx.send(":eyes: Woah are you like a trap or something? You cant be your own waifu!")
            return
        if ctx.author.id == 143090142360371200 and ctx.message.mentions[0].id == ctx.me.id:
            await ctx.send(":star: Rock-chan we will never be separated! わたしは、あなたを愛しています")
            return
        length = random.randint(1,100)
        if length < 40:
            s = ":broken_heart: "
        elif length > 80:
            s = ":sparkling_heart: "
        else:
            s = ":heart: "
        await ctx.send(s + " Yeah, i would give you two a rate of atleast **" + str(length) + "%** (In terms of seduction obviously)")

    @commands.command()
    async def harem(self, ctx):
        if len(ctx.message.mentions) > 0:
            menother = True
            random.seed(ctx.message.mentions[0].id)
        else:
            menother = False
            random.seed(ctx.author.id)
        length = random.randint(1,50)
        if length == 1:
            await ctx.send("Sorry but you wont ever have a harem. #4everLonely <3")
            return
        loli = 0
        trap = 0
        normal = 0
        furries = 0
        nekos = 0
        other = 0
        for wife in range(0,length):
            t = random.randint(1,6)
            if t == 1:
                loli += 1
            elif t == 2:
                trap += 1
            elif t == 3:
                normal += 1
            elif t == 4:
                furries += 1
            elif t == 5:
                nekos += 1
            else:
                other += 1
        if menother == True:
            text = ctx.message.mentions[0].name + " has " + str(length) + " wives in their harem. Makeup:\n```"
        else:
            text = "You have " + str(length) + " wives in your harem. Makeup:\n```"
        if loli > 0:
            text += "Loli: " + str(loli) + "\n"
        if trap > 0:
            text += "Trap: " + str(trap) + "\n"
        if normal > 0:
            text += "Normal: " + str(normal) + "\n"
        if furries > 0:
            text += "Furrie: " + str(furries) + "\n"
        if nekos > 0:
            text += "Neko: " + str(nekos) + "\n"
        if other > 0:
            text += "Other: " + str(other) + "\n" 
        text += "```"
        await ctx.send(text)

    @commands.command()
    async def neko(self,ctx):
        url = json.loads(requests.get("http://nekos.life/api/neko").text)['neko']
        embed = discord.Embed()
        embed.set_image(url=url)
        m = await ctx.send(embed=embed)
        await asyncio.sleep(60)
        await m.delete()

    @commands.command()
    async def lewd(self,ctx):
        if not ctx.channel.is_nsfw():
            embed = discord.Embed(title="Don't let your kids see this!", description=":warning: This command can only be ran on channels marked **NSFW**.")
            embed.set_image(url="https://i.ytimg.com/vi/44flbwqefJA/maxresdefault.jpg")
            m = await ctx.send(embed=embed)
            await asyncio.sleep(30)
            await m.delete()
        else:
            url = json.loads(requests.get("http://nekos.life/api/lewd/neko").text)['neko']
            embed = discord.Embed()
            embed.set_image(url=url)
            m = await ctx.send(embed=embed)
            await asyncio.sleep(60)
            await m.delete()

    @commands.command()
    async def ban(self, ctx, nil=None, reason="Unspecified"):
        guildInfo = self.bot.get_guild_info(ctx.guild.id)
        if ctx.message.mentions[0].roles[-1].position > ctx.author.roles[-1].position:
            await ctx.send("You cannot do this to people higher up than you (" + ctx.message.mentions[0].roles[-1].position + " > " + ctx.author.roles[-1].position + ")")
            return
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            print("Can use")
            if len(ctx.message.mentions) == 0:
                await ctx.send("Please mention a user")
                return
            print("Ban mofo")
            for user in ctx.message.mentions:
                try:
                    await user.send(":hammer_pick: You have been banned from **" + str(ctx.guild) + "** by" + str(ctx.author) + "** for **" + reason + "**")
                except:
                    0
                try:
                    await ctx.guild.ban(user, reason="Banned by " + str(ctx.author) + ": " + reason)
                except Exception as e:
                    await ctx.send("Could not ban " + str(user) + "\n```" + str(e) + "```")
                await ctx.send(":hammer_pick: **" + str(user) + "** has been banned")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.command()
    async def unban(self, ctx, id=None, reason="Unspecified"):
        guildInfo = self.bot.get_guild_info(ctx.guild.id)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            print("Can use")
            if id == None:
                await ctx.send("Please provide a user id")
                return
            user = await self.bot.get_user(id)
            try:
                await user.send(":hammer_pick: You have been unbanned from **" + str(ctx.guild) + "** by " + str(ctx.author) + "** for **" + reason + "**")
            except:
                0
            try:
                await ctx.guild.unban(user, reason="Unbanned by " + ctx.author + ": " + reason)
            except Exception as e:
                await ctx.send("Could not unban " + str(user) + "\n```" + str(e) + "```")
            await ctx.send(":trumpet: **" + str(user) + "** has been unbanned")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @commands.command()
    async def kick(self, ctx, nil=None, reason="Unspecified"):
        guildInfo = self.bot.get_guild_info(ctx.guild.id)
        if ctx.message.mentions[0].roles[-1].position > ctx.author.roles[-1].position:
            await ctx.send("You cannot do this to people higher up than you (" + ctx.message.mentions[0].roles[-1].position + " > " + ctx.author.roles[-1].position + ")")
            return
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if len(ctx.message.mentions) == 0:
                await ctx.send("Please mention a user")
                return
            else:
                for user in ctx.message.mentions:
                    if ctx.author > user:
                        try:
                            await ctx.guild.kick(user,"Kicked by " + ctx.author + ": " + reason)
                            try:
                                await user.send(":boot: You have been kicked from **" + str(ctx.guild) + "** by **" + str(ctx.author) + "** for **" + reason + "**")
                            except:
                                0
                            await ctx.send(":boot: **" + str(user) + "** has been kicked")
                        except Exception as e:
                            await ctx.send("Could not kick " + str(user) + "\n```" + str(e) + "```")
                    await ctx.send("You cannot ban this user as they are higher than you.")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

def setup(bot):
    bot.add_cog(CustomStuff(bot))