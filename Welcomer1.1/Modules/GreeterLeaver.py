from PIL import Image, ImageFont, ImageOps, ImageDraw
import asyncio, discord, os, PIL, urllib.request, time
from datetime import datetime, timezone
from discord.ext import commands
from DataIO import dataIO
from io import BytesIO

Images = dict()

for ext in os.listdir("Images"):
    name = ext[:ext.find(".")]
    Images[name] = Image.open("Images/" + ext)

def getSuffix(num):
    num = str(num)
    last = num[len(num)-1:len(num)]
    if last == "1":
        return "st"
    elif last == "2":
        return "nd"
    elif last == "3":
        return "rd"
    else:
        return "th"

def ischannel(guild, channelName):
    for channel in guild.channels:
        if str(channel.id) == str(channelName):
            return True
    return False

@asyncio.coroutine
async def getImage(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"urllib2/1.0"}))

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

@asyncio.coroutine
async def createWelcomeImage(backgroundImage,toptext,middletext,bottomtext,member,guild,circlecolour,textcolour):
    # Initialize Image
    WelcomePicture = ImageOps.fit(backgroundImage,(2000,600),centering=(0.5,0.5))
    # Insert Background Image
    WelcomePicture = WelcomePicture.resize((2000,600), PIL.Image.NEAREST)

    # Create Profile Picture Mask
    ProfileArea = Image.new("L",(512,512),0)
    draw = ImageDraw.Draw(ProfileArea)
    draw.ellipse(((0,0),(512,512)),fill=255)

    ProfilePicture = Image.open(await getImage(member.avatar_url or member.default_avatar_url))
    ProfileAreaOutput = ImageOps.fit(ProfilePicture,(512,512),centering=(0,0))
    ProfileAreaOutput.putalpha(ProfileArea)

    drawtwo = ImageDraw.Draw(WelcomePicture)
    drawtwo.ellipse(((28,28),(572,572)),fill=circlecolour)
    WelcomePicture.paste(ProfileAreaOutput,(44,44),ProfileAreaOutput)

    defaultFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/default.ttf", 80)
    smallFont =  ImageFont.truetype("/home/rock/Welcomer/Fonts/small.ttf", 40)
    italicFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/default.ttf", 44)

    WelcomePicture = WelcomePicture.resize((1000,300),resample=PIL.Image.ANTIALIAS)
    drawtwo = ImageDraw.Draw(WelcomePicture)

    # CustomText
    size = 85
    text = replace(toptext,guild,member).encode("utf8")
    while defaultFont.getsize(text.decode())[0] > 700:
        size -= 1
        defaultFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/default.ttf", size)
    size -= 1
    defaultFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/default.ttf", size)
    drawtwo.text((300,30),text.decode(),font=defaultFont, fill=textcolour)

    size = 40
    text = replace(middletext,guild,member).encode("utf8")
    while italicFont.getsize(text.decode())[0] > 700:
        size -= 1
        italicFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/default.ttf", size)
    size -= 1
    italicFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/default.ttf", size)
    drawtwo.text((315,125),text.decode(),font=italicFont, fill=textcolour)

    size = 40
    text = replace(bottomtext,guild,member).encode("utf8")
    while smallFont.getsize(text.decode())[0] > 700:
        size -= 1
        smallFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/small.ttf", size)
    size -= 1
    smallFont = ImageFont.truetype("/home/rock/Welcomer/Fonts/small.ttf", size)
    drawtwo.text((300,220),text.decode(),font=smallFont, fill=textcolour)

    # Save Image
    ImageObject = BytesIO()
    WelcomePicture.save(ImageObject, format="PNG")
    ImageObject.seek(0)

    return ImageObject

##

__version__ = "0.2"
__license__ ="MIT/X11"

DESC = "Scanii's python command line client"
API_URL = "https://scanii.com/api/scan/"
ENV_VAR = 'SCANII_CRED'

class Client(object):
    """
    Simple and reusable client for scanii.com
    """
    def __init__(self,key, secret,url=API_URL,):
        self.url = url
        self.key = key
        self.secret = secret
        self.infected = []
        self.clean= []
                
        log.debug('client init with endpoint %s' % url)         
        
    def api_call(self,data):
        """http heavy lifting """
    
        req = urllib2.Request(self.url, data )
        passman = urllib2.HTTPPasswordMgrWithDefaultRealm()

        passman.add_password(None, self.url, self.key, self.secret)

        authhandler = urllib2.HTTPBasicAuthHandler(passman)
        # create the AuthHandler

        opener = urllib2.build_opener(authhandler)

        urllib2.install_opener(opener)
        resp = urllib2.urlopen(req)
        j = json.loads(resp.read())
        
        log.debug('raw json response: %s' % j)
        
        return j

    def scan(self, filename):
        """ converts a file into bytes and scans it using the internal api"""
        
        try:
            file = open(filename, 'r')
        except:
            file = filename
        try:
            return self.api_call(file.read() )    
        finally:
            file.close()

##

class Greeter():

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def welcome(self,ctx):
        """Welcomes a user (tag them)"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        text = guildInfo['welcomer']['imagetext'].split("|")
        for member in ctx.message.mentions:
            ImageObject = await createWelcomeImage(Images[guildInfo['welcomer']['background']] or Images['404'],text[0],text[1],text[3],member,member.guild,(256,256,256),(256,256,256))
            try:
                await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))
            except:
                print("Unable to send message on " + message.guild.name + " (" + str(message.guild.id) + ")")

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
        if not imagename in Images:
            embed = discord.Embed(description="This image does not exist.")
            await ctx.send(embed=embed)
        else:
            ImageObject = await createWelcomeImage(Images[imagename],imagename + " preview","Doesnt it look nice?","+config set welcomer.background " + imagename,ctx.message.author,ctx.message.guild,(255,255,255),(255,255,255))
            await ctx.message.channel.send(file=discord.File(ImageObject,"Welcome.png"))

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

    @welcomer.command(name="enable",pass_context=True)
    async def welcomerenable(self,ctx):
        """Enable welcome messages"""
        userInfo, guildInfo = self.bot.get_guild_user_info(ctx)
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (str(ctx.message.author.id) in guildInfo['staff-members']) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
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
        if (ctx.message.author.guild_permissions.administrator) or (ctx.message.author.id == ctx.message.guild.owner.id) or (ctx.message.author.id in guildInfo['staff-members']) or (ctx.message.author.id in self.bot.specialRoles['staff']):
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
        guildInfo = self.bot.get_guild_info(str(member.guild.id))
        if guildInfo['leaver']['enable'] == True:
            if ischannel(member.guild,guildInfo['leaver']['channel']):
                try:
                    await self.bot.get_channel(int(guildInfo['leaver']['channel'])).bot.send_message(replace(guildInfo['leaver']['text'],member.guild,member))
                except:
                    print("Unable to send message on " + member.guild.name + " (" + str(member.guild.id) + ")")

    @asyncio.coroutine
    async def on_member_join(self,member):
        guildInfo = self.bot.get_guild_info(str(member.guild.id))
        if guildInfo['welcomer']['enable'] == True and guildInfo['welcomer']['use-image'] == True:
            if ischannel(member.guild,guildInfo['welcomer']['channel']):
                text = guildInfo['welcomer']['imagetext'].split("|")
                ImageObject = await createWelcomeImage(Images[guildInfo['welcomer']['background']] or Images['404'],text[0],text[1],text[2],member,member.guild,(256,256,256),(256,256,256))
                await self.bot.get_channel(int(guildInfo['welcomer']['channel'])).send(file=discord.File(ImageObject,"Welcome.png"))
                try:
                    joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S.%f")
                except:
                    joinDate = datetime.strptime(str(member.created_at), "%Y-%m-%d %H:%M:%S")
                currentDate = datetime.now(timezone.utc)
                currentDate = currentDate.replace(tzinfo=None)
                timeSinceJoining = currentDate - joinDate
                message = "\n"
                for guild in self.bot.guilds:
                    if len(guild.members) >= 50:
                        if member.id == guild.owner.id:
                            message += ":gear: **Server Owner** (" + str(len(guild.members)) + " members)\n"
                if str(member.id) in self.bot.specialRoles['staff']:
                    message += ":tools: **Welcomer Support Staff**\n"
                if str(member.id) in self.bot.specialRoles['donators']:
                    message += ":gem: **Donator**\n"
                if str(member.id) in self.bot.specialRoles['trusted']:
                    message += ":shield: **Trusted user**\n"
                message += "\n"
                if timeSinceJoining.days < 7:
                    if timeSinceJoining.days < 1:
                        message += ":warning: **Account was made <1 days ago**\n"
                    else:
                        if timeSinceJoining.days == 1:
                            message += ":warning: **Account was made " + str(timeSinceJoining.days) + " day ago**\n"
                        else:
                            message += ":warning: **Account was made " + str(timeSinceJoining.days) + " days ago**\n"
                if str(member.id) in self.bot.dbanslist:
                    message += ":no_entry: **Banned on discord list**\n"
                if message != "\n\n":
                    embed = discord.Embed(description=message)
                    await self.bot.get_channel(int(guildInfo['welcomer']['channel'])).send(embed=embed)

def setup(bot):
    bot.add_cog(Greeter(bot))