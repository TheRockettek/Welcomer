import discord,time,datetime,ctypes
client = discord.Client()

from PIL import Image,ImageFont,ImageOps,ImageDraw
from io import BytesIO
import PIL,urllib.request,datetime

global defaultFont
global smallFont
global italicFont
defaultFont = ImageFont.truetype("C:\\Windows\\Fonts\\Uni Sans Heavy.otf",80)
smallFont =  ImageFont.truetype("C:\\Windows\\Fonts\\Uni Sans Heavy.otf",26)
italicFont = ImageFont.truetype("C:\\Windows\\Fonts\\Uni Sans Heavy Italic.otf",50)

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
def getImage(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"urllib2/1.0"}))

def createWelcomeImage(name,profileUrl,serverCount):
    starttime = datetime.datetime.now()
    print("Creating base...")
    global WelcomePicture
    WelcomePicture = Image.new("RGB",(1000,300))
    Background = Image.open("F:\\Bot\\base.png")
    WelcomePicture.paste(Background)
    WelcomePicture = WelcomePicture.resize((1000,300), PIL.Image.NEAREST)

    # Load profile picture and make template
    print("Creating profile template")
    ProfileArea = Image.new("L",(256,256),0)
    draw = ImageDraw.Draw(ProfileArea)
    draw.ellipse(((0,0),(256,256)),fill=255)
    print("Downloading file...")
    startime = datetime.datetime.now()
    ProfilePicture = Image.open(getImage(profileUrl))
    endime = datetime.datetime.now()
    diff = (endime-startime)
    print("downloaded in " + str(diff.microseconds/1000000) + " seconds")
    print("Converting image to circle")
    ProfileAreaOutput = ImageOps.fit(ProfilePicture,(256,256),centering=(0.5,0.5))
    ProfileAreaOutput.putalpha(ProfileArea)

    # Create profile picture
    drawtwo = ImageDraw.Draw(WelcomePicture)
    drawtwo.ellipse(((14,14),(286,286)),fill=(64,64,64))
    WelcomePicture.paste(ProfileAreaOutput,(22,22),ProfileAreaOutput)
    print("Saving to base")

    # Draw welcome text
    print("Pasting pictures")
    drawtwo.text((300,20),"Welcome to SFG",font=defaultFont, fill=(255,255,255))
    drawtwo.text((320,100),name,font=italicFont, fill=(255,255,255))
    drawtwo.text((310,200),"You are the " + str(serverCount) + getSuffix(serverCount) + " user!",font=smallFont, fill=(255,255,255))

    # Export
    print("Saving")
    WelcomePicture = WelcomePicture.resize((2000,600),PIL.Image.NEAREST)
    WelcomePicture.save("F:\\Bot\\welcomen.png")
    endtime = datetime.datetime.now()
    global dif
    dif = (endtime-starttime)
    print("Created in " + str(diff.microseconds/1000000) + " seconds")

# Main program

whitelist = True
serverID = "257596928450232322"

global peopleLeft
global peopleJoined
peopleLeft = 0
peopleJoined = 0

@client.event
async def on_ready():
    print("Loaded welcomer")
    print(client.user.name)

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

@client.event
async def on_member_join(member):
    global peopleJoined
    global peopleLeft
    peopleJoined = peopleJoined + 1
    print("J | " + member.name + " (" + member.id + ") :" + member.server.name)
    if whitelist == True and member.server.id != serverID:
        return
    server = member.server
    players = len(member.server.members)
    if member.avatar_url == "":
        member.avatar_url = "http://smaller.hol.es/uploads/FrrJ7q45dv.png"
    createWelcomeImage(member.name + "#" + str(member.discriminator),member.avatar_url,players)
    await client.send_file(member.server.default_channel,"F:\\Bot\\welcomen.png")

@client.event
async def on_message(message):
    if "@330416853971107840" in message.content:
        if message.author.id == "201720501742206976":
            await client.send_message(message.channel,"Please do not talk to me, i concider this sexual harassment")
    if ("+generate" in message.content) and (message.author.id == "143090142360371200"):
        createWelcomeImage("Example1234","http://via.placeholder.com/256x256",54321)
        await client.send_file(message.server.default_channel,"F:\\Bot\\welcomen.png")
            
@client.event
async def on_member_remove(member):
    global peopleLeft
    global peopleJoined
    peopleLeft = peopleLeft + 1
    print("L | " + member.name + " (" + member.id + ") :" + member.server.name)
	if whitelist == True and member.server.id != serverID:
		return
	server = member.server
	players = len(member.server.members)
	embed = discord.Embed(description="Now since they have left, theres only  " + str(players) + " users on here. Hopefully they come back", colour=discord.Colour(0x3ff530), timestamp=datetime.datetime.utcfromtimestamp(int(time.time())))
	embed.set_thumbnail(url=member.server.icon_url)
	embed.set_author(name="Its a shame " + member.name + " had to leave.", icon_url=member.avatar_url)
	await client.send_message(member.server.default_channel,embed=embed)

client.run("")