import aiohttp
import imghdr
import math
import ujson as json
import time
import os
import PIL
import traceback

from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageSequence
from quart import Quart, send_file, send_file_obj, request, jsonify
import shutil

app = Quart(__name__)

IMAGE_LOCATION = "/home/rock/CDN/"
BORDER_DIFF = 1

def convert_hex(hex_val):
    if str(hex_val) == "0":
        hex_val = "FFFFFF"
    hex_val = hex_val.replace("#","")
    if len(hex_val) == 6:
        try:
            r = int(hex_val[0:2],16)
            g = int(hex_val[2:4],16)
            b = int(hex_val[4:6],16)
            # return (r,g,b)
            return (r,g,b,255)
        except:
            # return (255,255,255)
            return (255,255,255,0)
    else:
        try:
            a = int(hex_val[0:2],16)
            r = int(hex_val[2:4],16)
            g = int(hex_val[4:6],16)
            b = int(hex_val[6:8],16)
            # return (r,g,b)
            return (r,g,b,a)
        except:
            # return (255,255,255)
            return (255,255,255,0)

async def getImage(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.read()
            data = BytesIO(data)
            image = PIL.Image.open(data)
            return image

cache = dict()

async def get_bg(bg_id):
    if not "default" in cache:
        location = IMAGE_LOCATION + "Images/default.png"
        if os.path.exists(location):
            cache['default'] = dict()
            cache['default']['timeout'] = time.time()
            cache['default']['image'] = Image.open(location)
            file_data = open(location,"rb")
            cache['default']['type'] = imghdr.what(file_data)
            file_data.close()

    # if bg_id in cache:
    #     if not 'timeout' in cache[bg_id]:
    #         cache[bg_id]['timeout'] = time.time()
    #     if time.time()-cache[bg_id]['timeout'] < 600:
    #         if "image" in cache[bg_id]:
    #             return cache[bg_id]['image'], cache[bg_id]['type']
    #         else:
    #             return cache['default']['image'], cache['default']['type']

    cache[bg_id] = dict()
    cache[bg_id]['timeout'] = time.time()

    if "custom" in bg_id:
        ret = False
        location = IMAGE_LOCATION + "CustomImages/" + bg_id + ".gif"
        if os.path.exists(location):
            cache[bg_id]['image'] = Image.open(location)
            file_data = open(location,"rb")
            cache[bg_id]['type'] = imghdr.what(file_data)
            file_data.close()
            ret = True
        location = IMAGE_LOCATION + "CustomImages/" + bg_id + ".png"
        if os.path.exists(location) and not ret:
            cache[bg_id]['image'] = Image.open(location)
            file_data = open(location,"rb")
            cache[bg_id]['type'] = imghdr.what(file_data)
            file_data.close()
            ret = True
        location = IMAGE_LOCATION + "CustomImages/" + bg_id + ".jpg"
        if os.path.exists(location) and not ret:
            cache[bg_id]['image'] = Image.open(location)
            file_data = open(location,"rb")
            cache[bg_id]['type'] = imghdr.what(file_data)
            file_data.close()
            ret = True
    else:
        location = IMAGE_LOCATION + "Images/" + bg_id + ".png"
        if os.path.exists(location):
            cache[bg_id] = dict()
            cache[bg_id]['image'] = Image.open(location)
            file_data = open(location,"rb")
            cache[bg_id]['type'] = imghdr.what(file_data)
            file_data.close()

    if "image" in cache[bg_id]:
        return cache[bg_id]['image'], cache[bg_id]['type']
    else:
        return cache['default']['image'], cache['default']['type']

async def create_welcome_image(avatar_url, image_content, background="default", circle_colour="FFFFFF",
text_border="000000", text_colour="FFFFFF", resolution=[1000,300]):

    taskStart = datetime.now()

    base, image_type = await get_bg(background)
    base.seek(0)

    resolution[0] = int(resolution[0])
    resolution[1] = int(resolution[1])

    frames = []
    processed_frames = []

    if image_type == "gif":
        while True:
            try:
                try:
                    image = base.convert("RGBA")
                except:
                    image = base.convert("RGB")
                frames.append(image)
                base.seek(base.tell() + 1)
            except EOFError:
                break
            except Exception as e:
                print("Exception: " + str(e))
                break
    else:
        frames.append(base)

    width = resolution[0]
    height = resolution[1]

    if width == 0:
        width = 1000
    if height == 0:
        height = 300

    alias_scale = 10
    diam_scale = 10

    if width > height:
        if (width-height)/width < 0.5:
            diameter = math.ceil(height/2)
        else:
            diameter = math.ceil(((height-BORDER_DIFF)/6)*5)
    else:
        if height > 0 and (height-width)/height < 0.5:
            diameter = math.ceil(width/2)
        else:
            diameter = math.ceil(((width-BORDER_DIFF)/6)*5)

    profile_mask = Image.new("L",(diameter*alias_scale,diameter*alias_scale),0)
    profile_mask = profile_mask.resize((diameter*2, diameter*2), resample=PIL.Image.ANTIALIAS)
    draw = PIL.ImageDraw.Draw(profile_mask)
    draw.ellipse(((0,0),(diameter*2,diameter*2)),fill=255)

    profile = await getImage(avatar_url)

    profile_area = ImageOps.fit(profile,(diameter*2,diameter*2),centering=(diameter*2,diameter*2))
    profile_area.putalpha(profile_mask)
    profile_area = profile_area.resize((diameter, diameter), resample=PIL.Image.ANTIALIAS)

    if width <= height:
        profile_coords = [math.floor((width-diameter)/2), math.floor(height/20)]
        if profile_coords[0] > diameter/2:
            profile_coords[0] = diameter/4
    else:
        profile_coords = [10+diam_scale,math.floor((height-diameter)/2)]
        if profile_coords[1] > diameter/2:
            profile_coords[1] = diameter/4

    profile_coords[0] = int(math.floor(profile_coords[0]))
    profile_coords[1] = int(math.floor(profile_coords[1]))

    text_pos = []

    h_change = 30
    insize = 80
    siter = 80
    text_max_height = 60
    text_spacing = 64
    smallest = 80

    if width <= height:

        start_height = math.ceil(math.floor(height/10)+diameter)
        fiter = 0

        last = 66

        for line in image_content:

            fiter += 1
            line = line.replace("\r","")
            line = line.replace("\n","")
            text = line.encode("utf8").decode()

            size = int(math.ceil(last * 1.2))
            for i in range(0,siter):
                if fiter == 1:
                    default_font = ImageFont.truetype(IMAGE_LOCATION + "Fonts/default.ttf", size)
                elif fiter == 2:
                    default_font = ImageFont.truetype(IMAGE_LOCATION + "Fonts/italic.ttf", size)
                else:
                    default_font = ImageFont.truetype(IMAGE_LOCATION + "Fonts/small.ttf", size)
                size -= 1
                w,h = default_font.getsize(text)
                if w+10+BORDER_DIFF < width and h < height/4 or size == 1:
                    if size < smallest:
                        smallest = size
                    last = size
                    break

            text_pos.append({
                "pos": [math.floor((width-w)/2),start_height],
                "text": text,
                "size": size}
            )
            start_height += h+5
    else:
        start_height = math.floor( (height-(text_spacing*len(image_content)))/2 + (text_spacing-text_max_height)/2 )

        fiter = 0

        last = 66
     
        for line in image_content:

            fiter += 1
            line = line.replace("\r","")
            line = line.replace("\n","")
            text = line.encode("utf8").decode()

            size = int(math.ceil(last * 1.2))
            for i in range(0,siter):
                if fiter == 1:
                    default_font = ImageFont.truetype(IMAGE_LOCATION + "Fonts/default.ttf", size)
                elif fiter == 2:
                    default_font = ImageFont.truetype(IMAGE_LOCATION + "Fonts/italic.ttf", size)
                else:
                    default_font = ImageFont.truetype(IMAGE_LOCATION + "Fonts/small.ttf", size)

                size -= 1
                w,h = default_font.getsize(text)
                if w+diameter+(diam_scale*2)+30 < width and h < text_max_height:
                    if size < smallest:
                        smallest = size
                    last = size
                    break
    
            text_pos.append({
                "pos": [diameter+(diam_scale*2)+20,start_height],
                "text": text,
                "size": size}
            )
            start_height += text_spacing


    for frame in frames:

        current_frame = PIL.ImageOps.fit(frame,(width*2, height*2), centering=(width/2, height/2))
        current_frame = current_frame.resize((width, height), resample=PIL.Image.ANTIALIAS)
        current_frame = current_frame.convert(mode="RGBA")

        draw = ImageDraw.Draw(current_frame)
        draw.ellipse([profile_coords[0]-diam_scale,profile_coords[1]-diam_scale,profile_coords[0]+diameter+diam_scale,profile_coords[1]+diameter+diam_scale],fill=convert_hex(circle_colour))

        current_frame.paste(profile_area, (profile_coords[0],profile_coords[1]), profile_area)

        frame_draw = PIL.ImageDraw.Draw(current_frame)
        
        fiter = 0

        for text_data in text_pos:

            fiter += 1
            if fiter == 1:
                default = ImageFont.truetype(IMAGE_LOCATION + "Fonts/default.ttf", text_data['size'])
            elif fiter == 1:
                default = ImageFont.truetype(IMAGE_LOCATION + "Fonts/italic.ttf", text_data['size'])
            else:
                default = ImageFont.truetype(IMAGE_LOCATION + "Fonts/small.ttf", text_data['size'])
            frame_draw.text((text_data['pos'][0]+BORDER_DIFF,text_data['pos'][1]+BORDER_DIFF), text_data['text'], font=default, fill=convert_hex(text_border))
            frame_draw.text((text_data['pos'][0]-BORDER_DIFF,text_data['pos'][1]+BORDER_DIFF), text_data['text'], font=default, fill=convert_hex(text_border))
            frame_draw.text((text_data['pos'][0]+BORDER_DIFF,text_data['pos'][1]-BORDER_DIFF), text_data['text'], font=default, fill=convert_hex(text_border))
            frame_draw.text((text_data['pos'][0]-BORDER_DIFF,text_data['pos'][1]-BORDER_DIFF), text_data['text'], font=default, fill=convert_hex(text_border))
            frame_draw.text((text_data['pos'][0],text_data['pos'][1]), text_data['text'], font=default, fill=convert_hex(text_colour))

        processed_frames.append(current_frame)

        del current_frame
        del frame_draw
        del draw

    final_image = BytesIO()

    if image_type == "gif":
        is_gif = True
        durations = []

        for frame in ImageSequence.Iterator(base):
            try:
                durations.append(frame.info['duration'])
            except KeyError:
                durations.append(1/30)
            durations.append(1/30)
        try:
            processed_frames[0].save(final_image, format="GIF", optimize=False, disposal=2, save_all=True, append_images=processed_frames, loop=0, duration=durations)
        except Exception as e:
            traceback.print_exc()
            processed_frames[0].save(final_image, format="GIF")
    else:
        is_gif = False
        processed_frames[0].save(final_image, format="PNG", compress_level=1)

    final_image.seek(0)

    taskEnd = datetime.now()
    taskLength = taskEnd - taskStart
    maketime = (taskLength.seconds * 1000000 + taskLength.microseconds)/10000
    print("Made image in " + str(maketime) + "ms.")

    return final_image,is_gif

@app.route("/create_image", methods=['POST'])
async def process_welcome_image():
    data = await request.form
    image,is_gif = await create_welcome_image(data['avatar_url'], json.loads(data['image_content']), data['background'],
    data['circle_colour'], data['text_border'], data['text_colour'], json.loads(data['resolution']))
    if data['cdn'].lower() == "true":
        image.seek(0)
        out = str(math.floor(time.time()*10)) + (".gif" if is_gif else ".png")
        with open(IMAGE_LOCATION + "Output/" + out, 'wb') as f:
            shutil.copyfileobj(image, f, length=131072)
        print(f"Saved to cdn as {out}")

        if len(os.listdir(IMAGE_LOCATION + "Output")) > 100:
            t = math.floor(time.time()*10)
            for a in os.listdir(IMAGE_LOCATION + "Output"):
                madeat = int(a[:a.find(".")])
                if t-madeat > 6048000:
                    os.remove(IMAGE_LOCATION + "Output/" + a)
                    print(f"Purged {a}")
        return jsonify({
            "success": True
            "code": out[:-4],
            "url": f"https://cdn.welcomer.fun/retrieve/{out}"
        }) 
    else:
        return await send_file_obj(image)

@app.route("/retrieve/<output>")
async def retrieve(output):
    if os.path.exists(IMAGE_LOCATION + "Output/" + output):
        return await send_file(IMAGE_LOCATION + "Output/" + output)
    else:
        return jsonify({
            "error": "No such image on CDN"
        })

@app.route("/clear", methods=['POST'])
async def clear_background():
    data = await request.form
    background_id = data['id']

    print(f"Clearing {background_id}, Exists: {background_id in cache}")
    if background_id in cache:
        del cache[background_id]
        return "True"

    return "False"

@app.route("/")
async def index():
    return "Hi :)"

app.run(host="0.0.0.0", port=5005)
