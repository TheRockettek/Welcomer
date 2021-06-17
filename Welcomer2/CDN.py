from aiohttp import web
import aiohttp, asyncio
from PIL import Image, ImageFont, ImageOps, ImageDraw
import PIL
from colormap import hex2rgb
from datetime import datetime
from io import BytesIO
import os, time
cache = dict()
cache['bg'] = dict()

holidaycheer = False

def get_bg(id):

    return Image.open("Images/" + id + ".png")

    id = str(id)
    print("Retrieving " + id)
    if id in cache['bg']:
        if "timeout" in cache['bg'][id]:
            if int(time.time()) < cache['bg'][id]['timeout']:
                cache['bg'][id]['timeout'] = int(time.time()) + 600 # Resets timer so it doesnt unload every 5 minutes, but only if not used in 5 minutes
                return cache['bg'][id]['content']
    cache['bg'][id] = dict()
    if not os.path.exists("Images/" + str(id) + ".png"):
        print("/Images/" + id + ".png does not exist.")
        cache['bg'][id]['content'] = Image.open("Images/default.png")
    try:
        cache['bg'][id]['content'] = Image.open("Images/" + id + ".png")
        cache['bg'][id]['timeout'] = int(time.time()) + 600
        print("Loaded /Images/" + id + ".png")
        return cache['bg'][id]['content']
    except Exception as e:
        print("Could not load /Images/" + id + ".png")
        print(e)
        cache['bg'][id]['content'] = Image.open("Images/default.png")
        cache['bg'][id]['timeout'] = int(time.time()) + 600
        return cache['bg'][id]['content']

@asyncio.coroutine
async def getImage(url):
    with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()
            data = BytesIO(data)
            image = Image.open(data)
            return image

@asyncio.coroutine
async def createWelcomeImage(backgroundImage,toptext,middletext,bottomtext,circlecolour,textcolour,pfp):
    taskStart = datetime.now()
    # Initialize Image
    WelcomePicture = ImageOps.fit(get_bg(backgroundImage),(1000,300),centering=(0.5,0.5))
    # Insert Background Image
    WelcomePicture = WelcomePicture.resize((1000,300), resample=PIL.Image.ANTIALIAS)

    # Create Profile Picture Mask
    usecircle = True
    if usecircle:
        ProfileArea = Image.new("L",(256,256),0)
        draw = ImageDraw.Draw(ProfileArea)
        draw.ellipse(((0,0),(256,256)),fill=255)

        ProfilePicture = await getImage(pfp)
        ProfileAreaOutput = ImageOps.fit(ProfilePicture,(256,256),centering=(0,0))
        ProfileAreaOutput.putalpha(ProfileArea)

        drawtwo = ImageDraw.Draw(WelcomePicture)
        drawtwo.ellipse(((14,14),(286,286)),fill=circlecolour)
        WelcomePicture.paste(ProfileAreaOutput,(22,22),ProfileAreaOutput)
    else:
        ProfilePicture = await getImage(pfp)
        ProfilePicture = ProfilePicture.resize((256,256), resample=PIL.Image.ANTIALIAS)
        draw = ImageDraw.Draw(WelcomePicture)
        draw.rectangle([(14,14),(286,286)],fill=circlecolour)
        WelcomePicture.paste(ProfilePicture,(22,22))

    defaultFont = ImageFont.truetype("Fonts/default.ttf", 50)
    smallFont =  ImageFont.truetype("Fonts/small.ttf", 50)
    italicFont = ImageFont.truetype("Fonts/default.ttf", 50)
    drawtwo = ImageDraw.Draw(WelcomePicture)

    # CustomText
    size = 85
    text = toptext.encode("utf8")
    while True:
        if defaultFont.getsize(text.decode())[0] > 600:
            size -= 1
            defaultFont = ImageFont.truetype("Fonts/default.ttf", size)
        else:
            break
    drawtwo.text((300,30),text.decode(),font=defaultFont, fill=textcolour)

    size = 40
    text = middletext.encode("utf8")
    while True:
        if italicFont.getsize(text.decode())[0] > 600:
            size -= 1
            italicFont = ImageFont.truetype("Fonts/default.ttf", size)
        else:
            break
    drawtwo.text((315,125),text.decode(),font=italicFont, fill=textcolour)

    size = 40
    text = bottomtext.encode("utf8")
    while True:
        if smallFont.getsize(text.decode())[0] > 600:
            size -= 1
            smallFont = ImageFont.truetype("Fonts/small.ttf", size)
        else:
            break
    drawtwo.text((300,220),text.decode(),font=smallFont, fill=textcolour)

    # Save Image
    ImageObject = BytesIO()
    WelcomePicture.save(ImageObject, format="PNG", compress_level=1)
    ImageObject.seek(0)
    taskEnd = datetime.now()
    taskLength = taskEnd - taskStart
    print("Made image in " + str((taskLength.seconds * 1000000 + taskLength.microseconds)/10000) + "ms")
    return ImageObject

def test(default, var):
    try:
        return var
    except:
        return default

@asyncio.coroutine
async def genimage(request):
    data = await request.post()
    backgroundImage = test("default", data['bg'])
    circlecolour = test((255,255,255),hex2rgb(data['cc'].upper()))
    textcolour = test((255,255,255),hex2rgb(data['tc'].upper()))
    toptext = test("",data['tt'])
    middletext = test(" ",data['mt'])
    bottomtext = test(" ",data['bt'])
    pfp = test("https://cdn.discordapp.com/embed/avatars/1.png",data['av'])

    image = await createWelcomeImage(backgroundImage,toptext,middletext,bottomtext,circlecolour,textcolour,pfp)

    data = image.read()
    ws = web.StreamResponse()
    await ws.prepare(request)
    ws.content_type = "image/png"
    ws.write(data)
    await ws.drain()
    return ws

@asyncio.coroutine
async def reload(request):
    data = await request.post()
    id = data['id']
    key = "custom_" + str(id)
    del cache['bg'][key]
    print("Reloaded " + str(id))
    return aiohttp.web.Response("ok")

app = web.Application()
app.router.add_post("/img.png",genimage)
app.router.add_post("/clear",reload)

web.run_app(app, host="localhost", port=1337)