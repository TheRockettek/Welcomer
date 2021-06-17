import asyncio
import aiohttp
import imghdr
import math
import time
import os
import PIL
import shutil
import traceback

import ujson as json

from rockutils import rockutils
import rethinkdb as r
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageSequence
from quart import Response, Quart, send_file, request, jsonify
from os.path import join, exists

app = Quart(__name__)
config = rockutils.load_json("cfg/config.json")

# cdn_path = config['cdn']['location']
# custom_path = "custom-backgrounds"
# normal_path = "backgrounds"
# distribution_path = "distribution"
# fallback_back = "default.png"

cdn_path = "/home/rock/CDN"
custom_path = "CustomImages"
normal_path = "Images"
distribution_path = "Output"
fallback_back = "default.png"

image_caches = dict()
profile_cache = dict()

host = config['db']['host']
port = config['db']['port']

connection = r.connect(host=host, port=port)

def rounded_rectangle(imagedraw, xy, corner_radius, fill=None, outline=None):
    upper_left_point = xy[0]
    bottom_right_point = xy[1]
    imagedraw.rectangle(
        [
            (upper_left_point[0], upper_left_point[1] + corner_radius),
            (bottom_right_point[0], bottom_right_point[1] - corner_radius)
        ],
        fill=fill,
        outline=outline
    )
    imagedraw.rectangle(
        [
            (upper_left_point[0] + corner_radius, upper_left_point[1]),
            (bottom_right_point[0] - corner_radius, bottom_right_point[1])
        ],
        fill=fill,
        outline=outline
    )
    imagedraw.pieslice([upper_left_point, (upper_left_point[0] + corner_radius * 2, upper_left_point[1] + corner_radius * 2)],
        180,
        270,
        fill=fill,
        outline=outline
    )
    imagedraw.pieslice([(bottom_right_point[0] - corner_radius * 2, bottom_right_point[1] - corner_radius * 2), bottom_right_point],
        0,
        90,
        fill=fill,
        outline=outline
    )
    imagedraw.pieslice([(upper_left_point[0], bottom_right_point[1] - corner_radius * 2), (upper_left_point[0] + corner_radius * 2, bottom_right_point[1])],
        90,
        180,
        fill=fill,
        outline=outline
    )
    imagedraw.pieslice([(bottom_right_point[0] - corner_radius * 2, upper_left_point[1]), (bottom_right_point[0], upper_left_point[1] + corner_radius * 2)],
        270,
        360,
        fill=fill,
        outline=outline
    )


async def retrieve_background(name):
    location = ""

    if "custom" in name:
        if exists(join(cdn_path, custom_path, f"{name.replace('custom-', '')}.gif")):
            location = (join(cdn_path, custom_path, f"{name.replace('custom-', '')}.gif"))
            key = name.replace("custom-", "")

        elif exists(join(cdn_path, custom_path, f"{name.replace('custom-', '')}.png")):
            location = (join(cdn_path, custom_path, f"{name.replace('custom-', '')}.png"))
            key = name.replace("custom-", "")

        elif exists(join(cdn_path, custom_path, f"{name.replace('custom-', '')}.jpg")):
            location = (join(cdn_path, custom_path, f"{name.replace('custom-', '')}.jpg"))
            key = name.replace("custom-", "")
    else:
        location = join(cdn_path, normal_path, f"{name}.png")
        key = name

    if not exists(location):
        print(f"{location} does not exist")
        location = join(cdn_path, normal_path, fallback_back)
        key = "default"

    print(location)
    return await get_background(location, key)

async def get_background(path, key, timeout=600):
    retrieve_image = False
    _t = time.time()
    if key in image_caches:
        if time.time() - image_caches[key][1] > 0:
            retrieve_image = True
    else:
        retrieve_image = True

    if retrieve_image:
        print(f"Retrieving image from {path}")
        if os.path.exists(path):
            try:
                image_caches[key] = list()
                image_caches[key].append(Image.open(path))
                image_caches[key].append(_t + timeout)
                image_caches[key].append(imghdr.what(open(path, "rb")))
            except:
                return await get_background("default", "default")
                return image_caches['default'][0], image_caches['default'][2], image_caches[key][2].lower() == "gif"

    return image_caches[key][0], image_caches[key][2], image_caches[key][2].lower() == "gif"

async def getImage(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return Image.open(BytesIO(await resp.read()))

def normalize_colour(string):
    # rgba(255,255,255,0.4)
    # rgb(255,255,255) -> rgba(255,255,255,255)
    # #ffffff -> rgba(255,255,255,255)
    # #ffffff00 -> rgba(255,255,255,0)
    # transparent -> rgba(0,0,0,0)

    def convert(string):
        try:
            return int(string,16)
        except:
            return 0

    string = string.replace("#","")
    r,g,b,a = 0,0,0,1

    if str(string) == "0":
        return 0,0,0,1

    try:
        int(string,16)
        canhex = True
    except:
        canhex = False

    if canhex:
        if len(string) == 6:
            r = convert(string[0:2])
            g = convert(string[2:4])
            b = convert(string[4:6])
        if len(string) == 8:
            r = convert(string[0:2])
            g = convert(string[2:4])
            b = convert(string[4:6])
            a = convert(string[6:8])

    if "rgb" in string:
        finds = re.findall(r"\d+",string)
        if len(finds) >= 4 and string[0:4] == "rgba":
            r,g,b,a = finds[0], finds[1], finds[2], finds[3]
        elif len(finds) >= 4 and string[0:4] == "argb":
            a,r,g,b = finds[0], finds[1], finds[2], finds[3]
        elif len(finds) == 3:
            r,g,b = finds[0], finds[1], finds[2]

    r = int(r)
    g = int(g)
    b = int(b)
    a = float(a)

    if a <= 1.0:
        a = int(255*a/1)
    return r,g,b,int(a)

async def create_welcomer_image(
        avatar_url,
        image_data,
        allowed_gif=True
    ):
    
    START_TIME = time.time()
    ORIG_TIME = time.time()

    PROFILE_MASK_SCALE = 3 # how upscaled the image will be then descaled with anti alias
    PROFILE_MASK_SIZE = (256,256) # how big the profile picture will be
    BORDER_SIZE = 10 # how wide border will be

    background = image_data.get('bg','default')
    border = image_data.get('b',False)
    profile_border = image_data.get('pb',0)
    # 0: circular border
    # 1: no border
    # 2: square border
    # 3: circular no border
    colours = image_data['c']
    # bo: font outline
    # b: font colour
    # pb: profile border
    # ib: image border
    align = image_data.get('a',0)
    # 0: left
    # 1: middle
    # 2: right
    theme = image_data['t']
    #
    message = image_data['m'].replace("\r", "")

    a = time.time()

    image_content, image_type, image_is_gif = await retrieve_background(background)
    profile_image = await getImage(avatar_url)

    preprocessed_frames = []
    processed_frames = []
    durations = []

    if theme == 0:
        RESOLUTION = (1000, 300)
    elif theme == 1:
        RESOLUTION = (800,450)
    elif theme == 2:
        RESOLUTION = (1000,286)
    elif theme == 3:
        RESOLUTION = (1000, 300)
    elif theme == 4:
        RESOLUTION = (1000, 500)

    # extract frames
    # if border, add border and resize initial
    if image_is_gif and allowed_gif:
        for frame in ImageSequence.Iterator(image_content):
            try:
                image = frame.convert("RGBA")
            except Exception as e:
                print(e)
                image = frame.convert("RGB")

            if theme == 4:
                image_redo = Image.new("RGBA", RESOLUTION, (32, 34, 37, 0))
                image = ImageOps.fit(image, (RESOLUTION[0], 220), method = Image.ANTIALIAS)
                image_redo.paste(image, (0,0))
                image = image_redo
            else:
                image = ImageOps.fit(image, RESOLUTION, method = Image.ANTIALIAS)

            if theme == 3:
                image_tint_mask = Image.new("L", RESOLUTION, 0)
                image_tint_mask_draw = ImageDraw.Draw(image_tint_mask)
                image_tint_mask_draw.polygon([(550,0), (RESOLUTION[0], 0), RESOLUTION, (450, RESOLUTION[1])], fill=96)
                image_tint = Image.new("RGB", RESOLUTION, 0)
                image_content.paste(image_tint, image_tint_mask)

            preprocessed_frames.append(image)
            durations.append(image.info.get('duration',1/30))
    else:
        try:
            image_content = image_content.convert("RGBA")
        except Exception as e:
            print(e)
            image_content = image_content.convert("RGB")

        if theme == 4:
            image_redo = Image.new("RGBA", RESOLUTION, (32, 34, 37, 255))
            image_content = ImageOps.fit(image_content, (RESOLUTION[0], 220), method = Image.ANTIALIAS)
            image_redo.paste(image_content, (0,0))
            image_content = image_redo
        else:
            image_content = ImageOps.fit(image_content, RESOLUTION, method = Image.ANTIALIAS)

        if theme == 3:
            image_tint_mask = Image.new("L", RESOLUTION, 0)
            image_tint_mask_draw = ImageDraw.Draw(image_tint_mask)
            image_tint_mask_draw.polygon([(550,0), (RESOLUTION[0], 0), RESOLUTION, (450, RESOLUTION[1])], fill=96)
            image_tint = Image.new("RGB", RESOLUTION, 0)
            image_content.paste(image_tint, image_tint_mask)

        preprocessed_frames.append(image_content)
        durations.append(image_content.info.get('duration',1/30))

    # create a circular mask and put it on the profile picture
    # construct a final image
    # create a second mask for the border
    # paste the border on the image
    # paste the masked image on it

    user_size = (int(PROFILE_MASK_SIZE[0] * PROFILE_MASK_SCALE), int(PROFILE_MASK_SIZE[1] * PROFILE_MASK_SCALE))
    profile_mask = None
    border_mask = None

    if profile_border == 0:
        # circular
        profile_mask = Image.new("1", ((PROFILE_MASK_SIZE[0] * PROFILE_MASK_SCALE) - 2*(10 * PROFILE_MASK_SCALE), (PROFILE_MASK_SIZE[1] * PROFILE_MASK_SCALE) - 2*(10 * PROFILE_MASK_SCALE)), 0)
        profile_mask_draw = ImageDraw.Draw(profile_mask)
        profile_mask_draw.ellipse((0, 0, profile_mask.width, profile_mask.height), fill=255)

        area_mask = Image.new("1", user_size, 0)
        area_mask_draw = ImageDraw.Draw(area_mask)
        area_mask_draw.ellipse((0, 0, area_mask.width, area_mask.height), fill=255)
    elif profile_border == 1:
        # no border
        profile_mask = Image.new("1", user_size, 255)
        area_mask = Image.new("1", user_size, 255)
    elif profile_border == 2:
        # square border
        profile_mask = Image.new("1", ((PROFILE_MASK_SIZE[0] * PROFILE_MASK_SCALE) - 2*(10 * PROFILE_MASK_SCALE), (PROFILE_MASK_SIZE[1] * PROFILE_MASK_SCALE) - 2*(10 * PROFILE_MASK_SCALE)), 0)
        profile_mask_draw = ImageDraw.Draw(profile_mask)
        # profile_mask_draw.rectanRugle((0, 0, profile_mask.width, profile_mask.height), fill=255)
        rounded_rectangle(profile_mask_draw, ((0, 0), (profile_mask.width, profile_mask.height)), 30, fill=255)

        area_mask = Image.new("1", user_size, 0)
        area_mask_draw = ImageDraw.Draw(area_mask)
        # area_mask_draw.rectangle((0, 0, area_mask.width, area_mask.height), fill=255)
        rounded_rectangle(area_mask_draw, ((0, 0), (area_mask.width, area_mask.height)), 30, fill=255)
    elif profile_border == 3:
        # no border circular
        profile_mask = Image.new("1", user_size, 255)
        area_mask = Image.new("1", user_size, 0)
        area_mask_draw = ImageDraw.Draw(area_mask)
        area_mask_draw.ellipse((0, 0, area_mask.width, area_mask.height), fill=255)

    profile_image = ImageOps.fit(profile_image, (profile_mask.width, profile_mask.height))

    image_border_colour = normalize_colour(str(colours['ib']))
    text_border_colour = normalize_colour(str(colours['bo']))
    text_colour = normalize_colour(str(colours['b']))
    profile_border = normalize_colour(str(colours['pb']))

    TEXT_POSITION = ()
    TEXT_ALIGN = ""
    AVATAR_POSITION = ()

    print(user_size, profile_border, type(user_size), type(profile_border))
    profile_area = Image.new("RGBA", user_size, profile_border)
    profile_area.paste(profile_image, (int((profile_area.width - profile_image.width)/2), int((profile_area.height - profile_image.height)/2)), profile_mask)
    profile_area.putalpha(area_mask)

    finalised_profile = profile_area.resize(PROFILE_MASK_SIZE)
    area_mask = area_mask.resize(PROFILE_MASK_SIZE)
    finalised_profile.putalpha(area_mask)

    if theme == 0:
        if align >= 0 and align <= 2:
            TEXT_ALIGN = ["left","center","right"][align]
        else:
            TEXT_ALIGN = "left"

        size = 50 # initial font size
        font_location = join(cdn_path, "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        initial_x = int(finalised_profile.width + (RESOLUTION[1] - finalised_profile.height)) # initial X position which is the same distance from avatar to border
        total_width = int(RESOLUTION[0] - initial_x  - (RESOLUTION[1] - finalised_profile.height)/2) # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(text=message, font=font)
            if text_width < total_width and text_height < RESOLUTION[1]-10:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((preprocessed_frames[0].height - finalised_profile.height)/2), int((preprocessed_frames[0].height - finalised_profile.height)/2))
        TEXT_POSITION = (initial_x, int((RESOLUTION[1] - text_height)/2))
    elif theme == 1:
        TEXT_ALIGN = "center"

        size = 50 # initial font size
        font_location = join(cdn_path, "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        total_width = RESOLUTION[0] - 20 # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(text=message, font=font)
            if text_width < total_width and text_height < RESOLUTION[1] - 286:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((RESOLUTION[0] - finalised_profile.width)/2), 10)
        TEXT_POSITION = (int((RESOLUTION[0] - text_width)/2), 276 + int((RESOLUTION[1] - 286 - text_height)/2))
    elif theme == 2:
        TEXT_ALIGN = "right"

        size = 50 # initial font size
        font_location = join(cdn_path, "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        initial_x = int(finalised_profile.width + (RESOLUTION[1] - finalised_profile.height)) # initial X position which is the same distance from avatar to border
        total_width = int(RESOLUTION[0] - initial_x  - (RESOLUTION[1] - finalised_profile.height)/2) # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(text=message, font=font)
            if text_width < total_width and text_height < RESOLUTION[1]-10:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((preprocessed_frames[0].height - finalised_profile.height)/2), int((preprocessed_frames[0].height - finalised_profile.height)/2))
        TEXT_POSITION = (RESOLUTION[0] - 10 - text_width, int((RESOLUTION[1] - text_height)/2))
    elif theme == 3:
        TEXT_ALIGN = "center"

        size = 50 # initial font size
        font_location = join(cdn_path, "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        initial_x = int(finalised_profile.width + (RESOLUTION[1] - finalised_profile.height)) # initial X position which is the same distance from avatar to border
        total_width = int(RESOLUTION[0] - initial_x  - (RESOLUTION[1] - finalised_profile.height)/2) # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(text=message, font=font)
            if text_width < total_width and text_height < RESOLUTION[1]-10:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((preprocessed_frames[0].height - finalised_profile.height)/2), int((preprocessed_frames[0].height - finalised_profile.height)/2))
        TEXT_POSITION = (int(initial_x + (total_width - text_width)/2), int((RESOLUTION[1] - text_height)/2))
    elif theme == 4:
        if align >= 0 and align <= 2:
            TEXT_ALIGN = ["left","center","right"][align]
        else:
            TEXT_ALIGN = "left"

        size = 50 # initial font size
        font_location = join(cdn_path, "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(text=message, font=font)
            if text_width < RESOLUTION[0] - 20 and text_height < RESOLUTION[1] - finalised_profile.height - 30:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (10,10)
        TEXT_POSITION = (min(20,int((RESOLUTION[1] - finalised_profile.height -text_height)/2)), finalised_profile.height + int((RESOLUTION[1] - finalised_profile.height -text_height)/2))
        # (RESOLUTION[1] - finalised_profile.height - 30) + ((RESOLUTION[1] - finalised_profile.height - 30) - text_height)/2

    image_width, image_height = text_width, text_height
    text_image = Image.new("RGBA", (image_width+20, image_height+20), 255)
    text_image_draw = ImageDraw.Draw(text_image)

    textborder = 2
    features = ["-liga","-kern"]

    text_image_draw.multiline_text((0, 0), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    text_image_draw.multiline_text((4, 0), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    text_image_draw.multiline_text((0, 4), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    text_image_draw.multiline_text((4, 4), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)

    text_image_draw.multiline_text((1, 1), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    text_image_draw.multiline_text((3, 0), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    text_image_draw.multiline_text((0, 3), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    text_image_draw.multiline_text((3, 3), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)

    text_image_draw.multiline_text((2, 2), text=message, align=TEXT_ALIGN, font=font, fill=text_colour)

    for frame in preprocessed_frames:
        frame_draw = ImageDraw.Draw(frame)

        frame.paste(text_image, TEXT_POSITION, text_image)
        frame.paste(finalised_profile, AVATAR_POSITION, area_mask)

        if border:
            # border_frame = Image.new("RGBA", ((frame.width+20) * PROFILE_MASK_SCALE, (frame.height+20) * PROFILE_MASK_SCALE), (0,0,0,0))
            # border_draw = ImageDraw.Draw(border_frame)
            # rounded_rectangle(border_draw, ((0, 0), (border_frame.width, border_frame.height)), 30, fill=colour)
            # border_frame = border_frame.resize((frame.width+20, frame.height+20), resample = Image.ANTIALIAS)

            # # create mask to make the welcome image round
            # frame_round_mask = Image.new("1", (frame.width * PROFILE_MASK_SCALE, frame.height * PROFILE_MASK_SCALE), 0)
            # frame_round_mask_draw = ImageDraw.Draw(frame_round_mask)
            # rounded_rectangle(frame_round_mask_draw, ((0, 0), (frame_round_mask.width, frame_round_mask.height)), 30, fill=255)
            # frame_round_mask = frame_round_mask.resize((frame.width, frame.height), resample = Image.ANTIALIAS)
            # border_frame.paste(frame, (10, 10), frame_round_mask)

            border_frame = Image.new("RGBA", (frame.width+20, frame.height+20), image_border_colour)
            border_frame.paste(frame, (10, 10))
            processed_frames.append(border_frame)
        else:
            processed_frames.append(frame)

    bytes_image = BytesIO()
    image_is_gif = len(processed_frames) > 1 and allowed_gif
    durations.append(1/30)
    durations = durations[0]

    print(f"Created image in {math.ceil((time.time()-ORIG_TIME)*1000)}ms")

    if len(processed_frames) > 1 and allowed_gif:
        try:
            processed_frames[0].save(bytes_image, format="GIF", allow_mixed=True, optimize=False, save_all=True, append_images=processed_frames, loop=0, duration=durations)
        except Exception as e:
            traceback.print_exc()
            processed_frames[0].save(bytes_image, format="GIF")
    else:
        processed_frames[0].save(bytes_image, format="PNG", compress_level=1)

    fkb = math.ceil(len(bytes_image.getvalue())/1000)
    rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "kb_generated", count=fkb, keyname="count")
    rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "images_made", count=1, keyname="count")
    bytes_image.seek(0)
    return bytes_image, image_is_gif

@app.route("/images/create", methods=['POST'])
async def images_create():
    data = await request.form
    image, is_gif = await create_welcomer_image(
        data['avatar_url'],
        json.loads(data.get('image_data', '{}')),
        data.get('allowed_gif', "true") == "true"
    )

    if data.get('cache',"true") == "true":
        out_name = str(math.floor(time.time()*10))
        file_name = out_name + (".gif" if is_gif else ".png")
        file_path = join(cdn_path, distribution_path, file_name)
        with open(file_path, 'wb') as f:
            shutil.copyfileobj(image, f, length=131072)

        return jsonify({
            "url": f"https://cdn.welcomer.fun/images/get/{out_name}" + (".gif" if is_gif else ".png")
        }) 
    else:
        headers = {"content-Type": "application/octet-stream"}
        resp = Response(image.read(), headers=headers)
        return resp

def purge_files():
    output = join(cdn_path, distribution_path)
    dirlist = os.listdir(output)
    t = math.floor(time.time()*10)
    r = 0
    if len(dirlist) > 100:
        for _file in dirlist:
            madeat = int(_file[:_file.find(".")])
            if t-madeat > 1209600/2: # 1 week
                filelocation = join(output, _file)
                os.remove(filelocation)
                r += 1
    if r > 0:
        print(f"Purged {r} files")

# POST /images/create
# avatar_url*
# allowed_gif="true"
# image_data={}
# cache="true"

@app.route("/images/get/<path>")
async def images_get(path):
    path = path.replace(".png", "")
    path = path.replace(".gif", "")
    path = path.replace(".jpg", "")

    rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "images_requested", count=1, keyname="count")

    file_path = join(cdn_path, distribution_path, path + ".png")
    if os.path.exists(file_path):
        fkb = math.ceil(os.path.getsize(file_path)/1000)
        rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "kb_sent", count=fkb, keyname="count")
        return await send_file(file_path)

    file_path = join(cdn_path, distribution_path, path + ".gif")
    if os.path.exists(file_path):
        fkb = math.ceil(os.path.getsize(file_path)/1000)
        rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "kb_sent", count=fkb, keyname="count")
        return await send_file(file_path)

    rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "images_expired", count=1, keyname="count")
    return jsonify({
        "error": "No such image on CDN"
    })

@app.route("/images/clear/<name>")
async def images_clear(name):
    if name in image_caches:
        del image_caches[name]
        return "True"
    return "False"

app.run(host="0.0.0.0", port=5005)
