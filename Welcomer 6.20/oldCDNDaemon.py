import asyncio
import aiohttp
import imghdr
import json
import math
import PIL
import traceback
import time
import datetime
import shutil
import imageio
import gc
import logging
import numpy
import os

from rockutils import rockutils
from PIL import Image, ImageOps, ImageDraw, ImageFont, ImageSequence
from quart import Response, Quart, send_file, request, jsonify, websocket
from io import BytesIO
from os.path import join, exists


app = Quart(__name__)
gc.enable()
config = rockutils.load_json("cfg/config.json")
cdn_path = config['cdn']['location']
deadimage = Image.open("deadimage.png")

custom_path = "CustomImages"
normal_path = "Images"
distribution_path = "Output"
fallback_back = "default.png"

image_caches = dict()
easter = False
shouldcache = False

log = logging.getLogger('quart.serving')
log.setLevel(logging.ERROR)


def addtimings(_d, name):
    _d.append([name, time.time()])


def printtimings(_d, threshold=0.5):
    start = _d[0][1]
    for val in _d:
        dif = val[1] - start
        if dif > threshold:
            print(f"\033[1;31;40m{val[0]} took too long! Took {round(dif*1000)} ms\033[0;32;37m")
        start = val[1]


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
    imagedraw.pieslice(
        [upper_left_point,
         (upper_left_point[0] + corner_radius * 2, upper_left_point[1] +
          corner_radius * 2)],
        180, 270, fill=fill, outline=outline)
    imagedraw.pieslice(
        [(bottom_right_point[0] - corner_radius * 2, bottom_right_point[1] -
          corner_radius * 2),
         bottom_right_point],
        0, 90, fill=fill, outline=outline)
    imagedraw.pieslice(
        [(upper_left_point[0],
          bottom_right_point[1] - corner_radius * 2),
         (upper_left_point[0] + corner_radius * 2, bottom_right_point[1])],
        90, 180, fill=fill, outline=outline)
    imagedraw.pieslice(
        [(bottom_right_point[0] - corner_radius * 2, upper_left_point[1]),
         (bottom_right_point[0],
          upper_left_point[1] + corner_radius * 2)],
        270, 360, fill=fill, outline=outline)


async def retrieve_background(name):
    location = ""

    if not name:
        name = "default"

    if "custom" in name:
        if exists(
            join(
                cdn_path,
                custom_path,
                f"{name.replace('custom-', '')}.gif")):
            location = (
                join(
                    cdn_path,
                    custom_path,
                    f"{name.replace('custom-', '')}.gif"))
            key = name.replace("custom-", "")

        elif exists(join(cdn_path, custom_path, f"{name.replace('custom-', '')}.png")):
            location = (
                join(
                    cdn_path,
                    custom_path,
                    f"{name.replace('custom-', '')}.png"))
            key = name.replace("custom-", "")

        elif exists(join(cdn_path, custom_path, f"{name.replace('custom-', '')}.jpg")):
            location = (
                join(
                    cdn_path,
                    custom_path,
                    f"{name.replace('custom-', '')}.jpg"))
            key = name.replace("custom-", "")
    else:
        location = join(cdn_path, normal_path, f"{name}.png")
        key = name

    if not exists(location):
        location = join(cdn_path, normal_path, fallback_back)
        key = "default"

    _time = time.time()
    deletes = []
    for _key, value in image_caches.items():
        if _time - value[3] > 300 and _key != key:
            deletes.append(_key)
    for _key in deletes:
        del image_caches[_key]

    if key in image_caches:
        image_caches[key][3] = _time
        return image_caches[key][0], image_caches[key][2], image_caches[key][2].lower(
        ) == "gif"

    try:
        if not shouldcache:
            return Image.open(location), 0, imghdr.what(location) == "gif"

        if key not in image_caches:
            image_caches[key] = list()
            image_caches[key].append(Image.open(location))
            image_caches[key].append(0)
            image_caches[key].append(imghdr.what(location))
            image_caches[key].append(_time)

        return image_caches[key][0], image_caches[key][2], image_caches[key][2].lower(
        ) == "gif"
    except Exception as e:
        print("Caught Exception on image caching", e)
        location = (join(cdn_path, "Images", f"default.png"))
        key = "default"

        if not shouldcache:
            return Image.open(location), 0, imghdr.what(location) == "gif"

        if key not in image_caches:
            image_caches[key] = list()
            image_caches[key].append(Image.open(location))
            image_caches[key].append(0)
            image_caches[key].append(imghdr.what(location))
            image_caches[key].append(_time)

        return image_caches[key][0], image_caches[key][2], image_caches[key][2].lower(
        ) == "gif"


async def getImage(url):
    url = url.replace(".webp", ".png")
    url = url.replace(".gif", ".png")

    try:
        timeout = aiohttp.ClientTimeout(total=0.25)
        session = aiohttp.ClientSession(timeout=timeout)

        print(f"Retrieving from {url}")
        resp = await session.get(url)
        respo = await resp.read()
        imageobj = BytesIO(respo)
        _image = Image.open(imageobj)
        await session.close()
        return _image
    except asyncio.TimeoutError:
        pass
    except BaseException:
        traceback.print_exc()
        print("Falling back on image retrieval")
        pass

    await session.close()
    return deadimage


def normalize_colour(string):
    try:
        if string.startswith("RGBA|"):
            r = int(string[5:7], 16)
            g = int(string[7:9], 16)
            b = int(string[9:11], 16)
            a = int(string[11:13], 16)
            return r, g, b, a
        elif string.startswith("RGB|"):
            r = int(string[4:6], 16)
            g = int(string[6:8], 16)
            b = int(string[8:10], 16)
            return r, g, b, 255
    except BaseException as e:
        print("Exception on colour normalization", e)
        pass
    return 255, 255, 255, 255

    # try:
    #     string = string.replace("#", "")
    #     intcol = int(string, 16)
    #     tmp, blue = divmod(intcol, 256)
    #     tmp, green = divmod(tmp, 256)
    #     alpha, red = divmod(tmp, 256)
    #     return red, green, blue
    # except Exception as e:
    #     print(e)

    # try:
    #     intcol = int(string, 10)
    #     tmp, blue = divmod(intcol, 256)
    #     tmp, green = divmod(tmp, 256)
    #     alpha, red = divmod(tmp, 256)
    #     return alpha, red, green, blue
    # except Exception as e:
    #     print(e)
    #     return 0, 0, 0, 1


async def create_welcomer_image(
    avatar_url,
    image_data,
    allowed_gif=True
):
    imtimings = []

    ORIG_TIME = time.time()

    PROFILE_MASK_SCALE = 3  # how upscaled the image will be then descaled with anti alias
    PROFILE_MASK_SIZE = (256, 256)  # how big the profile picture will be
    BORDER_SIZE = 10  # how wide border will be

    background = image_data.get('bg', 'default')
    border = image_data.get('b', False)
    profile_border = image_data.get('pb', 0)
    # 0: circular border
    # 1: no border
    # 2: square border
    # 3: circular no border
    # 4: no profile
    colours = image_data['c']
    # bo: font outline
    # b: font colour
    # pb: profile border
    # ib: image border
    align = image_data.get('a', 0)
    # 0: left
    # 1: middle
    # 2: right
    theme = image_data.get('t', 0)
    message = image_data.get("m", "")
    if isinstance(message, list):
        message = "\n".join(message)
    message = message.replace("\r", "")

    addtimings(imtimings, "Init")

    image_content, image_type, image_is_gif = await retrieve_background(background)

    addtimings(imtimings, "Background Retrieval")

    profile_image = await getImage(avatar_url)

    addtimings(imtimings, "Profile Picture")

    preprocessed_frames = []
    processed_frames = []
    durations = []

    if theme == 0:
        RESOLUTION = (1000, 300)
    elif theme == 1:
        RESOLUTION = (800, 450)
    elif theme == 2:
        RESOLUTION = (1000, 286)
    elif theme == 3:
        RESOLUTION = (1000, 300)
    elif theme == 4:
        RESOLUTION = (1000, 500)

    # extract frames
    # if border, add border and resize initial
    if image_is_gif and allowed_gif:
        for frame in ImageSequence.Iterator(image_content):
            # ratio = 256
            # image = PIL.Image.eval(frame, lambda value: math.trunc(value / ratio) * ratio)

            try:
                image = frame.convert("RGBA")
            except Exception as e:
                print("Cause Exception on frame conversion", e)
                image = frame.convert("RGB")

            if theme == 4:
                image_redo = Image.new("RGBA", RESOLUTION, (32, 34, 37, 0))
                image = ImageOps.fit(
                    image, (RESOLUTION[0], 220), method=Image.ANTIALIAS)
                image_redo.paste(image, (0, 0))
                image = image_redo
            else:
                image = ImageOps.fit(image, RESOLUTION, method=Image.ANTIALIAS)

            if theme == 3:
                image_tint_mask = Image.new("L", RESOLUTION, 0)
                image_tint_mask_draw = ImageDraw.Draw(image_tint_mask)
                image_tint_mask_draw.polygon(
                    [(550, 0), (RESOLUTION[0], 0), RESOLUTION, (450, RESOLUTION[1])], fill=96)
                image_tint = Image.new("RGB", RESOLUTION, 0)
                image.paste(image_tint, image_tint_mask)

            preprocessed_frames.append(image)
            durations.append(image.info.get('duration', 1 / 30))
    else:
        # ratio = 256 / 24
        # image_content = PIL.Image.eval(image_content, lambda value: math.trunc(value / ratio) * ratio)

        try:
            image_content = image_content.convert("RGBA")
        except Exception as e:
            print("Cause Exception on frame conversion", e)
            image_content = image_content.convert("RGB")

        if theme == 4:
            image_redo = Image.new("RGBA", RESOLUTION, (32, 34, 37, 255))
            image_content = ImageOps.fit(
                image_content, (RESOLUTION[0], 220), method=Image.ANTIALIAS)
            image_redo.paste(image_content, (0, 0))
            image_content = image_redo
        else:
            image_content = ImageOps.fit(
                image_content, RESOLUTION, method=Image.ANTIALIAS)

        if theme == 3:
            image_tint_mask = Image.new("L", RESOLUTION, 0)
            image_tint_mask_draw = ImageDraw.Draw(image_tint_mask)
            image_tint_mask_draw.polygon(
                [(550, 0), (RESOLUTION[0], 0), RESOLUTION, (450, RESOLUTION[1])], fill=96)
            image_tint = Image.new("RGB", RESOLUTION, 0)
            image_content.paste(image_tint, image_tint_mask)

        preprocessed_frames.append(image_content)
        durations.append(image_content.info.get('duration', 1 / 30))

    addtimings(imtimings, "Frame Extraction")

    # create a circular mask and put it on the profile picture
    # construct a final image
    # create a second mask for the border
    # paste the border on the image
    # paste the masked image on it

    user_size = (
        int(PROFILE_MASK_SIZE[0] * PROFILE_MASK_SCALE),
        int(PROFILE_MASK_SIZE[1] * PROFILE_MASK_SCALE))
    profile_mask = None

    display_avatar = profile_border != 4

    if display_avatar:
        if profile_border == 0:
            # circular
            profile_mask = Image.new(
                "1",
                ((PROFILE_MASK_SIZE[0] * PROFILE_MASK_SCALE) - 2 *
                 (10 * PROFILE_MASK_SCALE),
                 (PROFILE_MASK_SIZE[1] * PROFILE_MASK_SCALE) - 2 *
                 (10 * PROFILE_MASK_SCALE)),
                0)
            profile_mask_draw = ImageDraw.Draw(profile_mask)
            profile_mask_draw.ellipse(
                (0, 0, profile_mask.width, profile_mask.height), fill=255)

            area_mask = Image.new("1", user_size, 0)
            area_mask_draw = ImageDraw.Draw(area_mask)
            area_mask_draw.ellipse(
                (0, 0, area_mask.width, area_mask.height), fill=255)
        elif profile_border == 1:
            # no border square
            profile_mask = Image.new("1", user_size, 255)
            area_mask = Image.new("1", user_size, 255)
        elif profile_border == 2:
            # square border
            profile_mask = Image.new(
                "1",
                ((PROFILE_MASK_SIZE[0] * PROFILE_MASK_SCALE) - 2 *
                 (10 * PROFILE_MASK_SCALE),
                 (PROFILE_MASK_SIZE[1] * PROFILE_MASK_SCALE) - 2 *
                 (10 * PROFILE_MASK_SCALE)),
                0)
            profile_mask_draw = ImageDraw.Draw(profile_mask)
            # profile_mask_draw.rectanRugle((0, 0, profile_mask.width, profile_mask.height), fill=255)
            rounded_rectangle(
                profile_mask_draw,
                ((0, 0),
                 (profile_mask.width, profile_mask.height)),
                30, fill=255)

            area_mask = Image.new("1", user_size, 0)
            area_mask_draw = ImageDraw.Draw(area_mask)
            # area_mask_draw.rectangle((0, 0, area_mask.width, area_mask.height), fill=255)
            rounded_rectangle(
                area_mask_draw, ((0, 0),
                                 (area_mask.width, area_mask.height)),
                30, fill=255)
        elif profile_border == 3:
            # no border circular
            profile_mask = Image.new("1", user_size, 255)
            area_mask = Image.new("1", user_size, 0)
            area_mask_draw = ImageDraw.Draw(area_mask)
            area_mask_draw.ellipse(
                (0, 0, area_mask.width, area_mask.height), fill=255)

        profile_image = ImageOps.fit(
            profile_image, (profile_mask.width, profile_mask.height))

    addtimings(imtimings, "Mask creation")

    image_border_colour = normalize_colour(str(colours['ib']))
    text_border_colour = normalize_colour(str(colours['bo']))
    text_colour = normalize_colour(str(colours['b']))
    profile_border = normalize_colour(str(colours['pb']))

    TEXT_POSITION = ()
    TEXT_ALIGN = "left"
    AVATAR_POSITION = ()

    if display_avatar:

        # print(user_size, profile_border, type(user_size), type(profile_border))
        profile_area = Image.new("RGBA", user_size, profile_border)
        if profile_image.mode == "rgba":
            profile_area.paste(
                profile_image,
                (int((profile_area.width - profile_image.width) / 2),
                 int((profile_area.height - profile_image.height) / 2)),
                profile_image)
        else:
            profile_area.paste(
                profile_image,
                (int((profile_area.width - profile_image.width) / 2),
                 int((profile_area.height - profile_image.height) / 2)),
                profile_mask)
        profile_area.putalpha(area_mask)
    # :clap:

    addtimings(imtimings, "Profile Processing")

    if display_avatar:
        finalised_profile = profile_area.resize(PROFILE_MASK_SIZE)
        area_mask = area_mask.resize(PROFILE_MASK_SIZE)
        finalised_profile.putalpha(area_mask)

    if theme == 0:
        if isinstance(align, str):
            try:
                align = int(align)
                if align >= 0 and align <= 2:
                    TEXT_ALIGN = ["left", "center", "right"][align]
                else:
                    TEXT_ALIGN = "left"
            except BaseException:
                if align.lower() in ['left', 'center', 'right']:
                    TEXT_ALIGN = align.lower()
                else:
                    TEXT_ALIGN = "left"

        size = 50  # initial font size
        font_location = join(cdn_path, "Fonts", "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        # initial X position which is the same distance from avatar to border
        initial_x = int(
            finalised_profile.width +
            (RESOLUTION[1] - finalised_profile.height))
        total_width = int(
            RESOLUTION[0] - initial_x -
            (RESOLUTION[1] - finalised_profile.height) / 2)  # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(
                text=message,
                font=font)
            if text_width < total_width and text_height < RESOLUTION[1] - 10:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((preprocessed_frames[0].height - finalised_profile.height) / 2), int(
            (preprocessed_frames[0].height - finalised_profile.height) / 2))
        TEXT_POSITION = (initial_x, int((RESOLUTION[1] - text_height) / 2))
    elif theme == 1:
        TEXT_ALIGN = "center"

        size = 50  # initial font size
        font_location = join(cdn_path, "Fonts", "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        total_width = RESOLUTION[0] - 20  # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(
                text=message,
                font=font)
            if text_width < total_width and text_height < RESOLUTION[1] - 286:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (
            int((RESOLUTION[0] - finalised_profile.width) / 2),
            10)
        TEXT_POSITION = (
            int((RESOLUTION[0] - text_width) / 2),
            271 + int((RESOLUTION[1] - 286 - text_height) / 2))
    elif theme == 2:
        TEXT_ALIGN = "right"

        size = 50  # initial font size
        font_location = join(cdn_path, "Fonts", "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        # initial X position which is the same distance from avatar to border
        initial_x = int(
            finalised_profile.width +
            (RESOLUTION[1] - finalised_profile.height))
        total_width = int(
            RESOLUTION[0] - initial_x -
            (RESOLUTION[1] - finalised_profile.height) / 2)  # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(
                text=message,
                font=font)
            if text_width < total_width and text_height < RESOLUTION[1] - 10:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((preprocessed_frames[0].height - finalised_profile.height) / 2), int(
            (preprocessed_frames[0].height - finalised_profile.height) / 2))
        TEXT_POSITION = (
            RESOLUTION[0] - 10 - text_width,
            int((RESOLUTION[1] - text_height) / 2))
    elif theme == 3:
        TEXT_ALIGN = "center"

        size = 50  # initial font size
        font_location = join(cdn_path, "Fonts", "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        # initial X position which is the same distance from avatar to border
        initial_x = int(
            finalised_profile.width +
            (RESOLUTION[1] - finalised_profile.height))
        total_width = int(
            RESOLUTION[0] - initial_x -
            (RESOLUTION[1] - finalised_profile.height) / 2)  # total width of the text allowed

        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(
                text=message,
                font=font)
            if text_width < total_width and text_height < RESOLUTION[1] - 10:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (int((preprocessed_frames[0].height - finalised_profile.height) / 2), int(
            (preprocessed_frames[0].height - finalised_profile.height) / 2))
        TEXT_POSITION = (
            int(initial_x + (total_width - text_width) / 2),
            int((RESOLUTION[1] - text_height) / 2))
    elif theme == 4:
        # if align >= 0 and align <= 2:
        #     TEXT_ALIGN = ["left", "center", "right"][align]
        # else:
        #     TEXT_ALIGN = "left"

        if isinstance(align, str):
            try:
                align = int(align)
                if align >= 0 and align <= 2:
                    TEXT_ALIGN = ["left", "center", "right"][align]
                else:
                    TEXT_ALIGN = "left"
            except BaseException:
                TEXT_ALIGN = "left"

        size = 50  # initial font size
        font_location = join(cdn_path, "Fonts", "default.ttf")
        font_draw = ImageDraw.Draw(preprocessed_frames[0])
        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.multiline_textsize(
                text=message,
                font=font)
            if text_width < RESOLUTION[0] - 20 and text_height < RESOLUTION[1] - finalised_profile.height - 30:
                break
            size -= 1
        font = ImageFont.truetype(font_location, size)

        AVATAR_POSITION = (10, 10)
        TEXT_POSITION = (min(20, int((RESOLUTION[1] -
                                      finalised_profile.height -
                                      text_height) /
                                     2)), finalised_profile.height +
                         int((RESOLUTION[1] -
                              finalised_profile.height -
                              text_height) /
                             2))
        # (RESOLUTION[1] - finalised_profile.height - 30) + ((RESOLUTION[1] - finalised_profile.height - 30) - text_height)/2

    addtimings(imtimings, "Theme Generation")

    image_width, image_height = text_width, text_height
    text_image = Image.new(
        "RGBA",
        (math.ceil(
            image_width *
            1.2),
            math.ceil(
            text_height *
            1.2)),
        255)
    text_image_draw = ImageDraw.Draw(text_image)

    features = ["-liga", "-kern"]

    text_image_draw.multiline_text(
        (0,
         0),
        text=message,
        align=TEXT_ALIGN,
        font=font,
        fill=text_border_colour,
        features=features)
    text_image_draw.multiline_text(
        (2,
         0),
        text=message,
        align=TEXT_ALIGN,
        font=font,
        fill=text_border_colour,
        features=features)
    text_image_draw.multiline_text(
        (0,
         2),
        text=message,
        align=TEXT_ALIGN,
        font=font,
        fill=text_border_colour,
        features=features)
    text_image_draw.multiline_text(
        (2,
         2),
        text=message,
        align=TEXT_ALIGN,
        font=font,
        fill=text_border_colour,
        features=features)
    # text_image_draw.multiline_text((1, 1), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    # text_image_draw.multiline_text((3, 0), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    # text_image_draw.multiline_text((0, 3), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)
    # text_image_draw.multiline_text((3, 3), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour, features=features)

    # text_image_draw.multiline_text((0, 0), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour)
    # text_image_draw.multiline_text((2, 0), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour)
    # text_image_draw.multiline_text((0, 2), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour)
    # text_image_draw.multiline_text((2, 2), text=message, align=TEXT_ALIGN, font=font, fill=text_border_colour)

    text_image_draw.multiline_text(
        (1, 1), text=message, align=TEXT_ALIGN, font=font, fill=text_colour)

    addtimings(imtimings, "Text Display")

    for frame in preprocessed_frames:
        # frame_draw = ImageDraw.Draw(frame)

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

            border_frame = Image.new(
                "RGBA", (frame.width + 20, frame.height + 20),
                image_border_colour)
            border_frame.paste(frame, (10, 10))
            if easter:
                border_frame = ImageOps.flip(border_frame)
                border_frame = ImageOps.mirror(border_frame)

            processed_frames.append(border_frame)
        else:
            if easter:
                frame = ImageOps.flip(frame)
                frame = ImageOps.mirror(frame)

            processed_frames.append(frame)

    addtimings(imtimings, "Frame Creation")

    bytes_image = BytesIO()
    bytes_image.name = "output.gif"

    image_is_gif = len(processed_frames) > 1 and allowed_gif

    durations = list(map(lambda o: o / 1000, durations))

    _processed_frames = []
    if len(processed_frames) > 1 and allowed_gif:
        """

        Depreciated code using PIL, now uilising imageIO

        """

        # try:
        #     processed_frames[0].save(
        #         bytes_image,
        #         format="GIF",
        #         allow_mixed=True,
        #         optimize=False,
        #         append_images=processed_frames,
        #         loop=0,
        #         duration=durations)
        # except BaseException:
        #     traceback.print_exc()
        #     processed_frames[0].save(bytes_image, format="GIF")
        # _processed_frames = list(map(lambda o: numpy.array(o), processed_frames))

        for image in processed_frames:
            fi = image.convert("RGB")
            _array = numpy.array(fi).reshape(image.height, image.width, 3)
            _processed_frames.append(_array)
        imageio.mimsave(
            bytes_image,
            _processed_frames,
            duration=durations,
            format="GIF-FI",
            loop=0,
            subrectangles=True)
    else:
        processed_frames[0].save(bytes_image, format="PNG", compress_level=1)

    addtimings(
        imtimings,
        f"Image creation Frames: {len(processed_frames)} Allowed Gif: {allowed_gif} Gif Background: {background}")
    printtimings(imtimings, threshold=0.2)

    print(f"Created image in {math.ceil((time.time()-ORIG_TIME)*1000)}ms")

    # fkb = math.ceil(len(bytes_image.getvalue()) / 1000)
    # rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "kb_generated", count=fkb, keyname="count")
    # rockutils.incr_db_noasync(connection, config['db']['table'], "stats", "images_made", count=1, keyname="count")
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

    if data.get('cache', "true") == "true":
        out_name = str(math.floor(time.time() * 1000))
        file_name = out_name + (".gif" if is_gif else ".png")
        file_path = join(cdn_path, distribution_path, file_name)

        with open(file_path, 'wb') as f:
            shutil.copyfileobj(image, f, length=131072)

        return jsonify(
            {"url": f"https://cdn.welcomer.fun/images/get/{out_name}" +
             (".gif" if is_gif else ".png")})
    else:
        headers = {"content-Type": "application/octet-stream"}
        resp = Response(image.read(), headers=headers)
        return resp


def purge_files():
    output = join(cdn_path, distribution_path)
    dirlist = os.listdir(output)
    t = math.floor(time.time() * 1000)
    r = 0
    if len(dirlist) > 100:
        for _file in dirlist:
            madeat = int(_file[:_file.find(".")])
            if t - madeat > 1209600000 / 2:  # 1 week
                filelocation = join(output, _file)
                os.remove(filelocation)
                r += 1
    if r > 0:
        print(f"Purged {r} files")


app.run(host="0.0.0.0", port=config['cdn']['daemonport'])
