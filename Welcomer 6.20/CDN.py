import io
import math
from math import floor
from time import time
from os import listdir, remove
from os.path import exists, join
from rockutils import rockutils
from PIL import Image, ImageDraw, ImageFont
import uuid
from sanic import Sanic, request, response
from sanic.response import json as jsonify
import psycopg2
import imghdr
import string
import base64
import random

import gc
gc.enable()

app = Sanic(__name__)
config = rockutils.load_json("cfg/config.json")
cdn_path = config['cdn']['location']
distribution_path = "Output"
ss_path = "Mirror"
fallback_back = "default.png"
custom_path = "CustomImages"
normal_path = "Images"

_atlas = Image.open("xpasset.png")
_assets = {}
_lastreq = 0

a = list(string.digits + string.ascii_letters)


host = config['db']['host']
db = config['db']['db']
password = config['db']['password']
user = config['db']['user']

connection_sync = psycopg2.connect(user=user, password=password,
                                   database=db, host=host)


def incr_db(connection, table, key, value):

    try:

        cursor = connection.cursor()
        cursor.execute(
            f"""
            UPDATE {table}
                SET value = value + %s
            WHERE id = %s;""",
            (value, key)
        )
        connection.commit()
        cursor.close()
    except psycopg2.errors.InFailedSqlTransaction:
        print("SQLTrans failed. Rolling back")
        connection.rollback()
    except psycopg2.InterfaceError:
        global connection_sync

        host = config['db']['host']
        db = config['db']['db']
        password = config['db']['password']
        user = config['db']['user']

        connection_sync = psycopg2.connect(user=user, password=password,
                                           database=db, host=host)
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        print("Failed to set value", table, ":", key, e)


for y in range(4):
    _assets[y] = []
    for x in range(3):
        _box = [(x * 10), (y * 5), (x * 10) + 11, (y * 5) + 5]
        _crop = _atlas.crop(_box)
        _assets[y].append(_crop)


async def generate_xp_bar(
        bars=15,
        percent=0,
        fill_type=2,
        background_type=0,
        scale=2):

    if not rockutils.canint(bars):
        bars = 15
    else:
        bars = int(bars)
    if bars < 2:
        bars = 2
    if bars > 100:
        bars = 100

    if not rockutils.canint(percent):
        percent = 0
    else:
        percent = int(percent)
    if percent < 0:
        percent = 0
    if percent > 100:
        percent = 0

    if not rockutils.canint(fill_type):
        fill_type = 2
    else:
        fill_type = int(fill_type)
    if fill_type > 3:
        fill_type = 3
    if fill_type < 0:
        fill_type = 0

    if not rockutils.canint(background_type):
        background_type = 0
    else:
        background_type = int(background_type)
    if background_type > 3:
        background_type = 3
    if background_type < 0:
        background_type = 0

    if not rockutils.canint(scale):
        scale = 2
    else:
        scale = int(scale)
    if scale < 1:
        scale = 1
    if scale > 10:
        scale = 10

    width = (10 * (bars - 2)) + 21
    background_bars = Image.new("RGBA", (width, 5))
    filled_bars = Image.new("RGBA", (width, 5))

    _x = 0
    for i in range(bars):
        if i == 0:
            _type = 0
        elif i + 1 == bars:
            _type = 2
        else:
            _type = 1
        background_bars.paste(_assets[background_type][_type], (_x, 0))
        _x += 10

    _x = 0
    totalbars = math.ceil(bars * (percent / 100))
    for i in range(totalbars):
        if i == 0:
            _type = 0
        elif i + 1 == bars:
            _type = 2
        else:
            _type = 1
        filled_bars.paste(_assets[fill_type][_type], (_x, 0))
        _x += 10

    _percentage = math.ceil(width * (percent / 100))
    _cropped = filled_bars.crop([0, 0, _percentage, 5])
    background_bars.paste(_cropped, (0, 0))
    background_bars = background_bars.resize(
        (width * scale, 5 * scale), Image.NEAREST)

    _image = io.BytesIO()
    background_bars.save(_image, "PNG")
    _image.seek(0)
    return _image


@app.route("/")
async def index(request):
    path = join(cdn_path, "image.jpg")
    return await response.file_stream(path)


@app.route("/imoog/<path>", methods=['GET'])
async def screenshot_get(request, path):
    path_before = path[:path.rfind(".")]
    path_after = path[path.rfind("."):]
    _filename = (path_before.encode("punycode")
                 [-10:]).decode("ascii") + path_after

    path = join(cdn_path, ss_path, _filename)
    return await response.file_stream(path)


@app.route("/imoog", methods=['POST'])
async def screenshot_upload(request):
    if request.headers.get("Authorization") != "[removed]":
        return response.json({"url": "Get Welcomer at https://welcomer.gg today B) I tried uploading an image but i didn't have the token"})
    i = int.from_bytes(
        base64.b64decode(
            str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) + str(uuid.uuid4()) +
            str(uuid.uuid4()) + str(uuid.uuid4()).replace("-", "")),
        'big', signed=True)
    # _id = base64.urlsafe_b64encode(i.to_bytes((i.bit_length() + 8) // 8, 'big', signed=True)).decode("ascii")
    # _id = base64.b85encode(i.to_bytes((i.bit_length() + 8) // 8, 'big', signed=True)).decode("ascii")

    random.seed(i)
    _id = "".join(random.choices(a, k=8))
    _tid = (_id.encode("punycode")[-10:]).decode("ascii")

    files = request.files
    _file = files.get('file', None)

    if not _file:
        return "{success: false}", 403

    _format = imghdr.what(io.BytesIO(_file.body))
    if _format:
        _filename = _tid + "." + _format
        _fakefilename = _id + "." + _format
        path = join(cdn_path, ss_path, _filename)
        with open(path, "wb") as f:
            f.write(_file.body)
        return jsonify(
            {"success": True, "id": _filename,
             "url": f"https://cdn.welcomer.gg/imoog/{_fakefilename}"})


@app.route("/resize/<url>")
async def resize(*, url):
    try:
        a = requests.get(url)
        b = Image.open(io.BytesIO(a.text()))
        b.thumbnail((800, 450))

        image = io.BytesIO()

        b.save(image, format="PNG", compress_level=1)

        image.seek(0)
        headers = {"content-Type": "image/png"}
        resp = response.raw(image.read(), headers=headers)
    except:
        return await response.file_stream("brokenimage.png")


@app.route("/images/get/<path>")
async def images_get(request, path):
    if exists(join(cdn_path, distribution_path, path)):
        location = join(cdn_path, distribution_path, path)
    else:
        location = "brokenimage.png"

    await purge_files()
    incr_db(connection_sync, "stats", "images_requested", 1)
    return await response.file_stream(location)


async def purge_files():
    global _lastreq
    t = floor(time() * 1000)
    if t - _lastreq > 60000:
        _lastreq = t
        output = join(cdn_path, distribution_path)
        dirlist = listdir(output)
        for _file in dirlist:
            if t - int(_file[:_file.find(".")]) > 604800000:  # 1 week
                remove(join(output, _file))


@app.route("/profile")
async def pfp(request):
    ip = "ImRock"
    for _h in ['CF-Connecting-IP', 'CF_CONNECTING_IP', 'X_FORWARDED_FOR', 'REMOTE_ADDR']:
        _ip = request.headers.get(_h, False)
        if _ip:
            ip = _ip
            break
    print(ip)
    if ip != "ImRock":
        i = Image.new("RGBA", (256, 256))

        size = 50  # initial font size
        font_location = join(cdn_path, "Fonts", "default.ttf")
        font_draw = ImageDraw.Draw(i)

        print(ip)
        while size > 0:
            font = ImageFont.truetype(font_location, size)
            text_width, text_height = font_draw.textsize(
                text=ip,
                font=font)
            print(size, text_width, text_height)
            if text_width < i.width and text_height < i.height:
                break
            size -= 1

        font_draw.text(
            (math.floor((i.width - text_width) / 2),
             math.floor((i.height - text_height) / 2)),
            text=ip,
            align="left",
            font=font,
            fill=(255, 255, 255))

        font_draw.text(
            (math.floor((i.width - text_width) / 2) - 1,
             math.floor((i.height - text_height) / 2) - 1),
            text=ip,
            align="left",
            font=font,
            fill=(0, 0, 0))

        bytes_image = io.BytesIO()
        i.save(bytes_image, format="PNG", compress_level=1)
        bytes_image.seek(0)

        headers = {"content-Type": "image/png"}
        resp = response.raw(bytes_image.read(), headers=headers)
        return resp
    else:
        return response.file_stream("/home/rock/Welcomer 6.0/twist.png")


@app.route("/minecraftxp", methods=['GET', 'POST'])
async def generate(request):

    data = request.args
    image = await generate_xp_bar(
        data.get("bars", 15),
        data.get("percent", 0),
        data.get("fill_type", 3),
        data.get("background_type", 0),
        data.get("scale", 2)
    )

    headers = {"content-Type": "image/png"}
    resp = response.raw(image.read(), headers=headers)
    return resp

app.run(host="0.0.0.0", port=config['cdn']['port'])
