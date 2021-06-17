from PIL import Image, ImageFont, ImageOps, ImageDraw
import asyncio, discord, os, PIL, urllib.request, time, requests, json, aiohttp, traceback
from datetime import datetime, timezone
from discord.ext import commands
from DataIO import dataIO
from io import BytesIO, StringIO
from urllib import parse

def clearbg(id):
    requests.post("http://localhost:1337/clear",{"id":id})

Images = dict()

authheader = {"Authorizationooh":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjE0MzA5MDE0MjM2MDM3MTIwMCIsImlhdCI6MTUwMDEzNTQzN30.FgI45a92nCctayr6Wi7YtfIINX97f8Q2yvcLHKNqL1I"}
upvote_time = 0
upvotes = dict()

def rgb_to_hex(rgb):
    return '%02x%02x%02x' % rgb

def unser(tag):
    beg = tag.find("\"")
    end = tag.find("\"",beg+1)
    return tag[beg+1:end].replace(" ","")

def has_upvoted(id):
    try:
        id = str(id)
        if int(time.time()) > upvote_time:
            upvote_request = requests.get("https://discordbots.org/api/bots/330416853971107840/votes?onlyids=True",headers=authheader)
            if upvote_request.ok:
                upvotes = json.loads(upvote_request.text)
                upvote_time = time.time() + 30
        return id in upvotes
    except:
        return True

"""
for ext in os.listdir("Images"):
    name = ext[:ext.find(".")]
    if not name in Images:
        Images[name] = Image.open("Images/" + ext)
"""

memeimage = Image.open("zucker.png")
memeimage2 = Image.open("cropthis.png")
memeimage3 = Image.open("amdry.png")
memeimage4 = Image.open("nicereligion.png")
memeimage5 = Image.open("betrayal.png")

def is_owner(ctx):
    return ctx.message.author.id == 143090142360371200 or (str(ctx.message.author.id) in bot.specialRoles['staff'])

def getSuffix(num):
    num = str(num)
    last = num[len(num)-1:len(num)]
    if last == "1" and num[len(num)-2:len(num)] != "11":
        return "st"
    elif last == "2" and num[len(num)-2:len(num)] != "12":
        return "nd"
    elif last == "3" and num[len(num)-2:len(num)] != "13":
        return "rd"
    else:
        return "th"

def ischannel(guild, channelName):
    for channel in guild.channels:
        if str(channel.id) == str(channelName):
            return True
    return False

@asyncio.coroutine
async def getImage(url, parse=False):
    if parse == True:
        url = parse.quote(url)
    print("Retrieving " + str(url))
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent":"urllib2/1.0"}) as resp:
            m = await resp.read()
            await session.close()
            return BytesIO(m)

def replace(text, guild, member):
    text = text.replace("%SERVER_NAME%",guild.name)
    text = text.replace("%SERVER_MEMBER_COUNT%",str(guild.member_count))
    text = text.replace("%SERVER_COUNT_SUFFIX%",getSuffix(guild.member_count))
    text = text.replace("%SERVER_COUNT%",str(guild.member_count))
    text = text.replace("%COUNT_SUFFIX%",getSuffix(guild.member_count))
    text = text.replace("%SERVER_ICON_URL%",guild.icon_url)
    text = text.replace("%SERVER_OWNER_NAME%",guild.owner.name)
    text = text.replace("%SERVER_OWNER%",guild.owner.name + "#" + guild.owner.discriminator)
    text = text.replace("%SERVER_OWNER_ID%",str(guild.owner.id))
    text = text.replace("%MEMBER_NAME%",member.name)
    text = text.replace("%NAME%",member.name)
    text = text.replace("%MEMBER%",member.name + "#" + member.discriminator)
    text = text.replace("%MEMBER_ID%",str(member.id))
    return text

@asyncio.coroutine
async def createMeme4(url):
    try:
        ProfilePicture = Image.open(await getImage(makeSmall(url)))
        ProfilePictureResized = ProfilePicture.resize((512,512),resample=PIL.Image.ANTIALIAS)
        Meme = memeimage4 # Import preloaded PIL file
        Meme.paste(ProfilePictureResized,(102,321))
        ImageObject = BytesIO()
        Meme.save(ImageObject, format="PNG")
        ImageObject.seek(0)
        return ImageObject, " "
    except Exception as e:
        return False, e

@asyncio.coroutine
async def createMeme3(urlt,urlb):
    try:
        ProfilePicture1 = Image.open(await getImage(makeSmall(urlt)))
        ProfilePicture1Resized = ProfilePicture1.resize((192,192),resample=PIL.Image.ANTIALIAS)
        ProfilePicture2 = Image.open(await getImage(makeSmall(urlb)))
        ProfilePicture2Resized = ProfilePicture2.resize((231,231),resample=PIL.Image.ANTIALIAS)
        Meme = memeimage3
        Meme.paste(ProfilePicture1Resized,(175,29))
        Meme.paste(ProfilePicture2Resized,(485,239))
        ImageObject = BytesIO()
        Meme.save(ImageObject, format="PNG")
        ImageObject.seek(0)
        return ImageObject
    except Exception as e:
        print(e)
        return False

@asyncio.coroutine
async def createMeme5(url):
    try:
        ProfilePicture = Image.open(await getImage(makeSmall(url)))
        ProfilePictureResized = ImageOps.fit(ProfilePicture,(1591,480),method=PIL.Image.ANTIALIAS,bleed=0)
        Meme = memeimage5 # Import preloaded PIL file
        Meme.paste(ProfilePictureResized,(29,30))
        ImageObject = BytesIO()
        Meme.save(ImageObject, format="PNG")
        ImageObject.seek(0)
        return ImageObject, ""
    except Exception as e:
        return False, str(e)

@asyncio.coroutine
async def createMeme2(url):
    try:
        ProfilePicture = Image.open(await getImage(makeSmall(url)))
        ProfilePictureResized = ProfilePicture.resize((258,258),resample=PIL.Image.ANTIALIAS)
        Meme = memeimage2 # Import preloaded PIL file
        Meme.paste(ProfilePictureResized,(65,63))
        ImageObject = BytesIO()
        Meme.save(ImageObject, format="PNG")
        ImageObject.seek(0)
        return ImageObject
    except:
        return False

@asyncio.coroutine
async def createMeme(url):
    try:
        ProfilePicture = Image.open(await getImage(makeSmall(url)))
        ProfilePictureResized = ProfilePicture.resize((356,356),resample=PIL.Image.ANTIALIAS)
        Meme = memeimage # Import preloaded PIL file
        Meme.paste(ProfilePictureResized,(73,63))
        ImageObject = BytesIO()
        Meme.save(ImageObject, format="PNG")
        ImageObject.seek(0)
        return ImageObject
    except:
        return False

def makeSmall(url):
    return url[:url.rfind(".")] + ".png?size=256"

@asyncio.coroutine
async def createWelcomeImage(backgroundImage,toptext,middletext,bottomtext,member,guild,circlecolour,textcolour,pfp):
    params = {"bg": backgroundImage, "tt": replace(toptext,guild,member), "mt": replace(middletext,guild,member), "bt": replace(bottomtext,guild,member), "cc": "#"+circlecolour, "tc": "#"+textcolour, "av": pfp}
    async with aiohttp.ClientSession() as session:
        async with session.post("http://127.0.0.1:1337/img.png", headers={"User-Agent":"urllib2/1.0"}, data=params) as resp:
            img = BytesIO(await resp.read())
    return img

def hextotupple(t):
    try:
        t = t.upper()
        r = int(t[0:2],16)
        g = int(t[2:4],16)
        b = int(t[4:6],16)
        return (r,g,b)
    except:
        (255,255,255)

class Greeter():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shards(self,ctx):
        await ctx.send(set(self.bot.shards.keys()))

    @commands.group(pass_context=True)
    async def gban(self,ctx):
        guildInfo = self.bot.get_guild_info(str(ctx.message.guild.id))
        if is_owner(ctx):
            if ctx.invoked_subcommand is None:
                await ctx.send(guildInfo['bot-prefix'] + "globalbans <add/remove/check> <id>")

    @gban.command(pass_context=True)
    async def add(self,ctx,id : str,reason : str):
        if is_owner(ctx):
            id = str(id)
            if not id in self.bot.globalbans:
                self.bot.globalbans[id] = True
                await ctx.send("<@" + str(id) + "> is gone forever.")
                await self.bot.get_channel(369382509244448778).send(" <@" + str(id) + "> has just been banned from " + str(len(self.bot.guilds)) + " servers :tada: GG\n`" + str(reason) + "`")
                dataIO.save_json("globalbans.json",self.bot.globalbans)

    @gban.command(pass_context=True)
    async def remove(self,ctx,id : str):
        if is_owner(ctx):
            if id in self.bot.globalbans:
                del self.bot.globalbans[id]
                dataIO.save_json("globalbans.json",self.bot.globalbans)


    @commands.command(pass_context=True)
    async def welcome(self,ctx):
        """Welcomes a user (tag them)"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        text = guildInfo['welcomer']['imagetext'].split("|")
        for member in ctx.message.mentions:
            try:
                pp = member.avatar_url
            except:
                pp = member.default_avatar_url
            try:
                ImageObject = await createWelcomeImage(guildInfo['welcomer']['background'],text[0],text[1],text[2],member,member.guild,guildInfo['welcomer']['cclr'] or "FFFFFF",guildInfo['welcomer']['tclr'] or "FFFFFF",pp) # Create Welcome Image                     try:
                await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
            except:
                print("Unable to send message on " + message.guild.name + " (" + str(message.guild.id) + ")")
            ImageObject.close()

    @commands.command(pass_context=True)
    async def welcomeimages(self,ctx):
        message = ""
        for imagename in Images:
            if not "custom" in imagename:
                message += imagename + "\n"
        embed = discord.Embed(description=message)
        await ctx.send(embed=embed)

    @commands.command(pass_context=True)
    async def previewimage(self,ctx,imagename : str):
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if not imagename in Images:
            embed = discord.Embed(description="This image does not exist.")
            await ctx.send(embed=embed)
        else:
            ImageObject = await self.bot.loop.run_in_executor(None, createWelcomeImage, self.bot.get_bg(imagename),imagename + " preview","Doesnt it look nice?","+config set welcomer.background " + imagename,ctx.message.author,ctx.message.guild,hextotupple(guildInfo['welcomer']['cclr']) or (256,256,256),hextotupple(guildInfo['welcomer']['tclr']) or (256,256,256))
            await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
            ImageObject.close()

    @commands.group(pass_context=True)
    async def welcomer(self,ctx):
        """Welcome message management"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if ctx.invoked_subcommand is None:
                embed = discord.Embed(description="+welcomer <enable/disable/setchannel>")
                embed.add_field(name="enable", value="Enables welcome messages", inline=True)
                embed.add_field(name="disable", value="Disables welcome messages", inline=True)
                embed.add_field(name="setchannel", value="Uses channel the channel the command is executed in")
                await ctx.send(embed=embed)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @welcomer.command(name="custom",pass_context=True)
    async def welcomercustomimage(self,ctx):
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        embed = discord.Embed(title="__Custom Background__",description="Please attach a file in your next message to set the new custom background.\n\nAccepted image type: .PNG\nAccepted image size: 1000x300*\n\n*Images smaler than 1000x300 will not display properly and bigger images\nwill be cropped to fit.\n\n:zero: **Back**")
        if not has_upvoted(ctx.author.id):
            embed = discord.Embed(title="**Wait a minute!**", description="\nSorry but you have to upvote the bot to be able to do this!\n[Bot list page](https://discordbots.org/bot/330416853971107840)\n\r")
            embed.set_image(url="https://i.imgur.com/m6ukOjm.gif")
            embed.set_thumbnail(url="https://i.imgur.com/1JM2U1Y.png")
            await ctx.send(embed=embed)
            return
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            m = await ctx.send(embed=embed)
            r = await self.bot.wait_for("message", check=lambda c: c.author == ctx.author and ((c.content == "0") or (len(c.attachments) > 0 and c.attachments[0].filename[-4:] == ".png")))
            if r.content == "0":
                embed = discord.Embed(title="__Custom Background__", description="Aborted.")
                await m.edit(embed=embed)
                return
            m.edit(embed=discord.Embed(title="__Custom Background__", description=":clock1:"))
            image = BytesIO()
            await r.attachments[0].save(image)
            try:
                try:
                    pp = ctx.author.avatar_url
                except:
                    pp = ctx.author.default_avatar_url
                ImageObject = await createWelcomeImage(guildInfo['welcomer']['background'],"a","b","c",ctx.author,ctx.guild,guildInfo['welcomer']['cclr'] or "FFFFFF",guildInfo['welcomer']['tclr'] or "FFFFFF",pp) # Create Welcome Image
                valid = True
            except Exception as e:
                print(e)
                valid = False
            if valid == True:
                await r.attachments[0].save("Images/custom_" + str(ctx.guild.id) + ".png")
                clearbg(ctx.guild.id)
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['welcomer']['background'] = "custom_" + str(ctx.guild.id)
                dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
                embed = discord.Embed(title="__Custom Background__", description=":white_check_mark: You have changed your custom background. Nice!")
                await m.edit(embed=embed)
                try:
                    del self.bot.cache['bg']['custom_' + str(ctx.guild.id)]
                except:
                    0
            else:
                await m.edit(embed=discord.Embed(title="__Custom Background__", description=":warning: The image failed the integrity check!\n" + str(ImageObject) + "\n\n__Possible Reasons__\n- Image may be 16 or 24 bit colour depth, i can only use 32bit.\n- This image is not a valid png file.\n- The image could of been corrupted."))
            image.close()
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @welcomer.command(name="reload",pass_context=True)
    async def welcomerreload(self,ctx):
        """Enable welcome messages"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.id == 143090142360371200) or (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if 'custom_' + str(ctx.guild.id) in self.bot.cache['bg']:
                del self.bot.cache['bg']['custom_' + str(ctx.guild.id)]
            del self.bot.cache['server_info'][str(ctx.guild.id)]
            clearbg(ctx.guild.id)
            await ctx.send(":white_check_mark: Reloaded configs.")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @welcomer.command(name="enable",pass_context=True)
    async def welcomerenable(self,ctx):
        """Enable welcome messages"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.id == 143090142360371200) or (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if ischannel(ctx.message.guild,int(guildInfo['welcomer']['channel'])):
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['welcomer']['enable'] = True
                embed = discord.Embed(description="Welcomer has been enabled.")
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(description="A channel has not been assigned yet. Do " + guildInfo['bot-prefix'] + "welcomer setchannel in the channel you would like it to use.")
                await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @welcomer.command(name="disable",pass_context=True)
    async def welcomerdisable(self,ctx):
        """Disable welcome messages"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.id == 143090142360371200) or (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (ctx.message.author.id in guildInfo['staff-members']) or (ctx.message.author.id in self.bot.specialRoles['staff']):
            self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['welcomer']['enable'] = False
            embed = discord.Embed(description="Welcomer has been disabled.")
            await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @welcomer.command(name="setchannel",pass_context=True)
    async def welcomersetchannel(self,ctx):
        """Set channel for welcome messages"""
        value = ""
        try:
            value = ctx.message.channel_mentions[0].id
        except:
            0
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            if value != "":
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['welcomer']['channel'] = str(value)
            else:
                self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['welcomer']['channel'] = str(ctx.message.channel.id)
            embed = discord.Embed(description="Welcomer channel has been set to <#" + self.bot.cache['server_info'][str(ctx.message.guild.id)]['content']['welcomer']['channel'] + ">")
            await ctx.send(embed=embed)
            dataIO.save_json("Servers/" + str(ctx.message.guild.id) + ".json",self.bot.cache['server_info'][str(ctx.message.guild.id)]['content'])
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @asyncio.coroutine
    async def on_member_remove(self,member):
        if self.bot.ready == False:
            return
        guildInfo = self.bot.get_guild_info(str(member.guild.id))
        if guildInfo['leaver']['enable'] == True:
            if ischannel(member.guild,guildInfo['welcomer']['channel']):
                try:
                    await self.bot.get_channel(int(guildInfo['welcomer']['channel'])).send(replace(guildInfo['leaver']['text'],member.guild,member))
                except Exception as e:
                    print(e)
                    print("Unable to send message on " + member.guild.name + " (" + str(member.guild.id) + ")")

    @commands.command()
    async def speedtest(self,ctx):
        taskStart = datetime.now()
        m = await ctx.send("Starting...")
        for i in range(1,10):
            await createWelcomeImage("default","hi","hi","hi",ctx.author,ctx.guild,"FFFFFF","FFFFFF",ctx.author.default_avatar_url)
        taskEnd = datetime.now()
        taskLength = taskEnd - taskStart
        await m.edit(content=str((taskLength.seconds * 1000000 + taskLength.microseconds)/10000) + "ms")

    @asyncio.coroutine
    async def on_member_join(self,member):
        if self.bot.ready == False:
            return

        """try:"""
        images = False
        textt = " "
        emb = False
        guildInfo = self.bot.get_guild_info(str(member.guild.id))
        welcomechannel = self.bot.get_channel(int(guildInfo['welcomer']['channel']))
        id = str(member.id)
        try:
            if id in self.bot.globalbans:
                if self.bot.globalbans[id] == True:
                    0
                    #await member.server.ban(member, reason="Global ban")
                    #print("Banned " + str(member) + " from " + member.server.name)
                    #await self.bot.get_channel(int(guildInfo['welcomer']['channel'])).send(str(member) + " is on a global ban and i have banned them now.")
        except Exception as e:
            print(e)
        
        if guildInfo['greet-dm']['enable'] == True:
            try:
                await member.send(embed=discord.Embed(description=replace(guildInfo['greet-dm']['text'],member.guild,member)))
            except Exception as e:
                print(e)
    
        if guildInfo['welcomer']['enable'] == False:
            return
        if not ischannel(member.guild,guildInfo['welcomer']['channel']):
            return

        if "welcomeimage" in guildInfo['welcomer']:
            image = await getImage(guildInfo['welcomeimage'])
            extention = guildInfo['welcomer']['welcomeimage'][guildInfo['welcomer']['welcomeimage'].rfind("."):]
            await self.bot.get_channel(int(guildInfo['welcomer']['channel'])).send(file=discord.File(image,"thingy" + extention)) # WelcomeImage

        if guildInfo['welcomer']['use-text'] == True:
            textt = replace(guildInfo['welcomer']['text'], member.guild, member) # Text Message

        if guildInfo['welcomer']['use-image'] == True:
            if ischannel(member.guild,guildInfo['welcomer']['channel']):
                text = guildInfo['welcomer']['imagetext'].split("|")
                try:
                    str(text[0])
                    str(text[1])
                    str(text[2])
                    str(text[3])
                except:
                    text = "Welcome|%MEMBER%|You are the %SERVER_MEMBER_COUNT%%SERVER_COUNT_SUFFIX% user|Have a good time :)".split("|")
                try:
                    try:
                        pp = member.avatar_url
                    except:
                        pp = member.default_avatar_url
                    ImageObject = await createWelcomeImage(guildInfo['welcomer']['background'],text[0],text[1],text[2],member,member.guild,guildInfo['welcomer']['cclr'] or "FFFFFF",guildInfo['welcomer']['tclr'] or "FFFFFF",pp) # Create Welcome Image
                    filehandle = discord.File(ImageObject,"Welcome.png")
                    images = True
                except Exception as e:
                    await welcomechannel.send("An error occured whilst creating this image. The Developers are aware if this was not your fault.\n\n```" + str(e) + "```")
        try:
            joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
        except:
            joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
        currentDate = datetime.now(timezone.utc)
        currentDate = currentDate.replace(tzinfo=None)
        timeSinceJoining = currentDate - joinDate
        message = "\n"
        try:
            for guild in self.bot.guilds:
                if guild.member_count >= 50:
                    try:
                        if member.id == guild.owner.id:
                            message += ":gear: **Server Owner** (" + str(guild.member_count) + " members)\n"
                    except:
                        0
        except:
            0
        if member.bot == True:
            message += ":robot: **Bot Account**\n"
        if str(member.id) in self.bot.specialRoles['staff']:
            message += ":tools: **Welcomer Support Staff**\n"
        if str(member.id) in self.bot.specialRoles['donators']:
            message += ":gem: **Donator**\n"
        if str(member.id) in self.bot.specialRoles['trusted']:
            message += ":shield: **Trusted user**\n"
        if str(member.id) == "143090142360371200":
            message += ":star2: **The one the only, Rock**\n"
        message += "\n"
        try:
            if timeSinceJoining.days < 1:
                message += ":warning: **Account was made " + (str(timeSinceJoining.hours) or "<1") + "hours ago ago**\n"
            else:
                if timeSinceJoining.days == 1:
                    message += "<:blobthonkang:" + self.bot.customemotes['blobthonkang'] + "> **Account was made " + str(timeSinceJoining.days) + " day ago**\n"
                else:
                    0
                    """
                    if "[w:showaccdate]" in  welcomechannel.topic:
                        message += ":calendar: **Account was made " + str(timeSinceJoining.days) + " days ago**\n"
                    """    
        except:
            0
        """
        if (str(member.id) in self.bot.dbanslist):
            reason = ""
            reason = self.bot.dbanslist[str(member.id)]['r'] + " [**Proof**](" + unser(self.bot.dbanslist[str(member.id)]['p']) + ")"
            message += ":no_entry: **Banned on discord list:**\n" + reason + "\n"
        """
        if message != "\n\n":
            embed = discord.Embed(description=message)
            emb = True

        try:
            await welcomechannel.send(textt,file=filehandle,embed=embed)
        except:
            try:
                await welcomechannel.send(textt,file=filehandle)
            except:
                try:
                    await welcomechannel.send(textt)
                except:
                    try:
                        await welcomechannel.send(file=filehandle,embed=embed)
                    except:
                        try:
                            await welcomechannel.send(textt,embed=embed)
                        except:
                            try:
                                await welcomechannel.send(textt,file=filehandle)
                            except:
                                0
        if images:
            ImageObject.close()
            ImageObject = None

        """except Exception as e:
            print("Cannot make image on " + str(member.guild.id) + ": " + str(e))"""

    @commands.command()
    async def badges(self, ctx):
        if len(ctx.message.mentions) < 1:
            await ctx.send("Please mention a user")
        else:
            member = ctx.message.mentions[0]
            try:
                joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
            except:
                joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
            currentDate = datetime.now(timezone.utc)
            currentDate = currentDate.replace(tzinfo=None)
            timeSinceJoining = currentDate - joinDate
            message = "Aestetical\n"
            for guild in self.bot.guilds:
                if guild.member_count >= 50:
                    try:
                        if member.id == guild.owner.id:
                            message += ":gear: **Server Owner** (" + str(guild.member_count) + " members)\n"
                    except:
                        0
            if str(member.id) in self.bot.specialRoles['staff']:
                message += ":tools: **Welcomer Support Staff**\n"
            if str(member.id) in self.bot.specialRoles['donators']:
                message += ":gem: **Donator**\n"
            if str(member.id) in self.bot.specialRoles['trusted']:
                message += ":shield: **Trusted user**\n"
            if str(member.id) == "143090142360371200":
                message += ":star2: **The one the only, Rock**\n"
            if str(member.id) == "330416853971107840":
                message += ":wave: **Oh look its me**\n"
            if member.bot == True and str(member.id) != "330416853971107840":
                message += ":robot: **A bot worse than me**\n"
            if member.id == ctx.author.id:
                message += ":neutral_face: **Likes to look at own badges**\n"
            message += "Moderation-wise\n"
            if timeSinceJoining.days < 7:
                if timeSinceJoining.days < 1:
                    message += ":warning: **Account was made <1 days ago**\n"
                else:
                    if timeSinceJoining.days == 1:
                        message += ":warning: **Account was made " + str(timeSinceJoining.days) + " day ago**\n"
                    else:
                        message += ":warning: **Account was made " + str(timeSinceJoining.days) + " days ago**\n"
            if (str(member.id) in self.bot.dbanslist):
                reason = ""
                reason = self.bot.dbanslist[str(member.id)]['r'] + " [**Proof**](" + unser(self.bot.dbanslist[str(member.id)]['p']) + ")"
                message += ":no_entry: **Banned on discord list:**\n" + reason + "\n"
            if message == "Aestetical\nModeration-wise\n":
                message = "\n:sob: **No badges (except from this)**\n\r"
            message = "\n**:passport_control: " + str(member) + "'s Badges**\n\n" + message
            embed = discord.Embed(description=message)
            await ctx.send(embed=embed)

    @commands.command()
    async def joinreligion(self, ctx, *args):
        if len(args) > 0:
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
                url = member.avatar_url
            else:
                url = args[0]
            print(url)
            ImageObject,e = await createMeme4(url)
            if ImageObject == False:
                await ctx.send("Unable to create image, was the URL invalid?\n\n`" + str(e) + "`")
            else:
                await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
        else:
            await ctx.send("Please mention a user or attach a url")

    @commands.command()
    async def betrayal(self, ctx, *args):
        if len(args) > 0:
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
                url = member.avatar_url
            else:
                url = args[0]
            print(url)
            ImageObject,e = await createMeme5(url)
            if ImageObject == False:
                await ctx.send("Unable to create image, was the URL invalid?\n\n`" + str(e) + "`")
            else:
                await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
        else:
            await ctx.send("Please mention a user or attach a url")


    @commands.command()
    async def whatalovely(self, ctx, *args):
        if len(args) > 0:
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
                url = member.avatar_url or member.default_avatar_url
            else:
                url = args[0]
            ImageObject = await createMeme(url)
            if ImageObject == False:
                await ctx.send("Unable to create image, was the URL invalid?")
            else:
                await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
        else:
            await ctx.send("Please mention a user or attach a url")

    """
    @commands.command()
    async def rape(self, ctx):
        if len(ctx.message.mentions) > 0:
            member = ctx.message.mentions[0]
            url = member.avatar_url or member.default_avatar_url
        else:
            await ctx.send("Please mention a user")
            return
        ImageObject = await createMeme3(ctx.author.avatar_url or ctx.author.default_avatar_url, url)
        if ImageObject == False:
            await ctx.send("Unable to create image. :(")
        else:
            await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
    """

    @commands.command()
    async def pleasecrop(self, ctx, *args):
        if len(args) > 0:
            if len(ctx.message.mentions) > 0:
                member = ctx.message.mentions[0]
                url = member.avatar_url or member.default_avatar_url
            else:
                url = args[0]
            ImageObject = await createMeme2(url)
            if ImageObject == False:
                await ctx.send("Unable to create image, was the URL invalid?")
            else:
                await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
        else:
            await ctx.send("Please mention a user or attach a url")

    @commands.command()
    async def banreason(self, ctx):
        if len(ctx.message.mentions) > 0:
            userscope = ctx.message.mentions[0]
            if (str(userscope.id) in self.bot.dbanslist):
                reason = ""
                reason += "**Reason**: " + self.bot.dbanslist[str(userscope.id)]['r']
                reason += "\n**[Proof](" + unser(self.bot.dbanslist[str(userscope.id)]['p']) + ")**"
                await ctx.send(reason)
            else:
                await ctx.send("This user isn't on discord bans list!")
        else:
            m = await ctx.send("Please provide a user mention")
            await asyncio.sleep(5)
            await m.delete()

    @commands.command(pass_context=True)
    async def djointest(self,ctx):
        """Tests welcome event (Bot owner only)"""
        if (ctx.message.author.guild_permissions.administrator) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            for member in ctx.message.mentions:
                member.guild = ctx.message.guild
                try:
                    await Greeter.on_member_join(self,member)
                except Exception as e:
                    trace = str(traceback.format_exc()).replace(str(self.bot.http.token),"[Censored]")
                    await ctx.send("Could not make image\n\n```" + trace + "```")

def setup(bot):
    bot.add_cog(Greeter(bot))
