import asyncpg
import asyncio
import psycopg2
import base64
import copy
import csv
import html
import imghdr
import logging
import math
import os
import pathlib
import random
import re
import shutil
import string
import sys
import time
import traceback
# import tracemalloc
from datetime import timedelta, datetime
from functools import wraps
from urllib.parse import urlparse
from uuid import uuid4
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

import aiohttp
import discord
import yaml
from itsdangerous import URLSafeSerializer
from PIL import Image, ImageDraw, ImageFont
from quart import (Quart, abort, jsonify, redirect, render_template, request,
                   send_file, session, websocket)
from quart.json import JSONDecoder, JSONEncoder
from quart.ctx import copy_current_websocket_context
from quart.sessions import SessionInterface, SessionMixin
from werkzeug.datastructures import CallbackDict

import asyncio
# import aiosmtplib
import sys

# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

import paypalrestsdk
import ujson as json
import uvloop
from quart_compress import Compress
from aoauth2_session import AOAuth2Session as OAuth2Session
from rockutils import rockutils

uvloop.install()
# tracemalloc.start()

config = rockutils.load_json("cfg/config.json")
paypal_api = paypalrestsdk.configure(config['paypal'])
recaptcha_key = config['keys']['recaptcha']

_oauth2 = config['oauth']
_domain = "welcomer.gg"
# _domain = "192.168.0.29:15007"
_debug = False

connection = None
connection_sync = None


async def connect(_debug, _config):
    global connection
    global connection_sync
    host = config['db']['host']
    db = config['db']['db']
    password = config['db']['password']
    user = config['db']['user']

    rockutils.prefix_print(f"Connecting to DB {user}@{host}")
    try:
        connection = await asyncpg.create_pool(user=user, password=password,
                                               database=db, host=host, max_size=50)
        connection_sync = psycopg2.connect(user=user, password=password,
                                           database=db, host=host)
    except Exception as e:
        rockutils.prefix_print(
            f"Failed to connect to DB: {e}.",
            prefix_colour="light red",
            text_colour="red")
        exit()

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(
    [asyncio.ensure_future(connect(_debug, config))]))


async def get_value(connection, table, key, default=None, raw=False):
    print("FETCH", table, key)

    async with connection.acquire() as pconnection:
        value = await pconnection.fetchrow(
            f"SELECT * FROM {table} WHERE id = $1",
            key
        )

    if value:
        print("FETCH", table, key, "OK")
        if raw:
            return value["value"]
        else:
            return json.loads(value["value"])
    else:
        print("FETCH", table, key, "FAIL")
        return default


async def set_value(connection, table, key, value):
    if key is None:
        key = str(uuid.uuid4())

    print("SET", table, key)

    try:
        async with connection.acquire() as pconnection:
            await pconnection.execute(
                f"INSERT INTO {table}(id, value) VALUES($1, $2) ON CONFLICT (id) DO UPDATE SET value = $2",
                key, json.dumps(value),
            )
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        print("Failed to set value", table, ":", key, e)
        # return False
    else:
        # return True
        return {
            "generated_keys": [key]
        }


def get_value_sync(connection, table, key, default=None):

    try:
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT * FROM {table} WHERE id = %s",
            (key,)
        )
        value = cursor.fetchone()

        if value:
            print("FETCH", table, key, "OK")
            return value[1]
        else:
            print("FETCH", table, key, "FAIL")
            return default
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

    return False


def set_value_sync(connection, table, key, value):
    if key is None:
        key = str(uuid.uuid4())

    print("SET", table, key)

    try:

        cursor = connection.cursor()
        cursor.execute(
            f"""
            INSERT INTO {table} (id, value)
            VALUES (%s, %s)
            ON CONFLICT (id)
            DO UPDATE SET
                value = EXCLUDED.value;""",
            (key, json.dumps(value))
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
        # return False
    else:
        # return True
        return {
            "generated_keys": [key]
        }


class Cache:
    def __init__(self):
        self.cache = {}

    def check_cache(self, key):
        if key in self.cache:
            keypair = self.cache[key]
            if time.time() >= (keypair['now'] + keypair['timeout']):
                return False, keypair['value']
            else:
                return True, keypair['value']
        else:
            return False, None

    def add_cache(self, key, timeout, value):
        self.cache[key] = {
            "now": time.time(),
            "timeout": timeout,
            "value": value,
        }

    def get_cache(self, key):
        val = self.cache[key]


cache = Cache()

blackfriday = False
# black friday sales 25% off everything

if blackfriday:
    prices = {
        '0:1': 3.75,
        '1:1': 3.75,
        '1:3': 11.25,
        '1:6': 22.5,
        '3:1': 7.5,
        '3:3': 22.5,
        '3:6': 45.0,
        '5:1': 11.25,
        '5:3': 33.75,
        '5:6': 67.5,
    }
else:
    prices = {
        "0:1": 5,
        "1:1": 5,
        "1:3": 13.50,
        "1:6": 24.00,
        "3:1": 10,
        "3:3": 27,
        "3:6": 48,
        "5:1": 15,
        "5:3": 40.50,
        "5:6": 72.00,
    }


_lastpost = 0


def empty(val):
    return val in ['', ' ', None]


class PostgresSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False

    # def __setitem__(self, item, value):
    #     print(item, value)
    #     if item != "_permanent":
    #         self.modified = True
    #     super(CallbackDict, self).__setitem__(item, value)


class PostgresSessionInterface(SessionInterface):
    serializer = json
    session_class = PostgresSession

    def __init__(self, connection_sync, prefix=''):
        self.connection_sync = connection_sync
        self.prefix = prefix
        self.serialize = URLSafeSerializer(_oauth2['serial_secret'])
        self.modified = False

    def generate_sid(self):
        return str(uuid4())

    # def get_redis_expiration_time(self, app, session):
    #     return app.permanent_session_lifetime

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)

        rockutils.prefix_print(
            f"Retreiving session {self.prefix + sid}. URL: {request.path}",
            prefix_colour="light blue")

        # val = r.table("sessions").get(self.prefix + sid).run(self.rethink)
        val = get_value_sync(self.connection_sync,
                             "sessions", self.prefix + sid)

        if val is not None:
            data = self.serializer.loads(self.serialize.loads(val['data']))
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        path = self.get_cookie_path(app)
        if not session:
            if session.modified:
                rockutils.prefix_print(
                    f"Deleting session {self.prefix + session.sid}. URL: {request.path}",
                    prefix_colour="light red")

                # r.table("sessions").get(self.prefix +
                #                         session.sid).delete().run(self.rethink)

                # TODO: actually clean sessions lol
                # delete_value_sync(self.connection_sync,
                #                   "sessions", self.prefix + session.sid)

                response.delete_cookie(app.session_cookie_name,
                                       domain=domain,
                                       path=path)
            return

        domain = self.get_cookie_domain(app)
        cookie_exp = self.get_expiration_time(app, session)
        val = self.serialize.dumps(self.serializer.dumps(dict(session)))
        rockutils.prefix_print(
            f"Updating session {self.prefix + session.sid}. URL: {request.path}",
            prefix_colour="light yellow")
        # if r.table("sessions").get(
        #         self.prefix +
        #         session.sid).run(
        #         self.rethink):
        #     r.table("sessions").get(self.prefix +
        #                             session.sid).replace({"id": self.prefix +
        #                                                   session.sid, "data": val}).run(self.rethink)
        # else:
        #     r.table("sessions").insert(
        #         {"id": self.prefix + session.sid, "data": val}).run(self.rethink)
        set_value_sync(self.connection_sync, "sessions", self.prefix +
                       session.sid, {"id": self.prefix + session.sid, "data": val})

        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True, domain=domain, secure=False)
        # response.set_cookie(app.session_cookie_name, session.sid,
        #                     expires=cookie_exp, httponly=True, domain=domain, secure=True)

        print(app.session_cookie_name, session.sid, domain, cookie_exp)


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):
        try:
            return json.dumps(obj)
        except TypeError:
            return JSONEncoder.default(self, obj)


class CustomJSONDecoder(JSONDecoder):
    def default(self, obj):
        try:
            return json.dumps(obj)
        except TypeError:
            return JSONDecoder.default(self, obj)


print("[init] Setting up quart")
app = Quart(__name__)
app.json_encoder = CustomJSONEncoder
app.json_decoder = CustomJSONDecoder

# Compress(app, True)
app.session_cookie_name = "session"
app.session_interface = PostgresSessionInterface(connection_sync)
app.secret_key = _oauth2['secret_key']
# app.config["SESSION_COOKIE_DOMAIN"] = _domain

app.jinja_env.trim_blocks = True
app.jinja_env.lstrip_blocks = True

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.jinja_options['auto_reload'] = True

app.config['MAX_CONTENT_LENGTH'] = 268435456
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


logging.basicConfig(filename='errors.log', level=logging.ERROR,
                    format='[%(asctime)s] %(levelname)-8s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
# log = logging.getLogger('requests_oauthlib')
# log.setLevel(logging.DEBUG)


def normalize_colour(string):
    if isinstance(string, int):
        return f"RGB|FFFFFF"
    if string.lower() == "transparent":
        return f"transparent"
    if string.startswith("RGBA|"):
        return string
    elif string.startswith("RGB|"):
        return string
    else:
        try:
            _hex = str(hex(int(string)))[2:]
            if len(_hex) >= 8:
                return f"RGBA|{str(hex(string))[:8]}"
            elif len(_hex) >= 6:
                return f"RGB|{str(hex(string))[:6]}"
        except BaseException:
            pass
        return f"RGB|FFFFFF"


def normalize_form(v):
    if str(v).lower() == "true":
        return True
    if str(v).lower() == "false":
        return False
    try:
        if v[0] == "#":
            return int(v[1:], 16)
    except BaseException:
        pass
    try:
        return int(v)
    except BaseException:
        return v


def get_size(start_path):
    _sh = os.popen(f"du -sb {start_path}")
    resp = _sh._stream.read()
    _sh.close()
    return int(resp.split()[0])


def expect(v, t):
    if t == "hex":
        if v:
            if v[0] == "#":
                try:
                    int(v[1:], 16)
                    return True
                except BaseException:
                    pass
            if "rgba" in v:
                return True
        if v.lower() == "transparent":
            return True
        try:
            int(v, 16)
            return True
        except BaseException:
            pass
    if t == "int":
        try:
            int(v)
            return True
        except BaseException:
            pass
    if t == "bool":
        if v in [True, "true", "True", False, "false", "False"]:
            return True
    return False


def iterat():
    i = math.ceil(time.time() * 100000)
    return base64.b32encode(
        i.to_bytes(
            (i.bit_length() + 8) // 8,
            'big',
            signed=True)).decode("ascii").replace(
        "=",
        "").lower()


def sub(s, b, e=None, a=False):
    s = str(s)
    if e:
        return s[b:e]
    else:
        if a:
            return s[:b]
        else:
            return s[b:]


app.jinja_env.globals['json_loads'] = json.loads
app.jinja_env.globals['len'] = len
app.jinja_env.globals['str'] = str
app.jinja_env.globals['dict'] = dict
app.jinja_env.globals['bool'] = bool
app.jinja_env.globals['int'] = int
app.jinja_env.globals['hex'] = hex
app.jinja_env.globals['sub'] = sub
app.jinja_env.globals['list'] = list
app.jinja_env.globals['iterat'] = iterat
app.jinja_env.globals['unesc'] = html.unescape
app.jinja_env.globals['ctime'] = time.time
app.jinja_env.globals['ceil'] = math.ceil
app.jinja_env.globals['enumerate'] = enumerate
app.jinja_env.globals['sorted'] = sorted
app.jinja_env.globals['dirlist'] = os.listdir
app.jinja_env.globals['exist'] = os.path.exists
app.jinja_env.globals['since_unix_str'] = rockutils.since_unix_str
app.jinja_env.globals['recaptcha_key'] = recaptcha_key

ipc_jobs = {}
ipc_locks = {}
cluster_jobs = {}
clusters_initialized = set()
last_ping = {}
user_cache = {}
cluster_status = {}
cluster_data = {}
identify_locks = {}

_status_name = {
    0: "Connecting",
    1: "Ready",
    2: "Restarting",
    3: "Hung",
    4: "Resuming",
    5: "Stopped"
}

discord_cache = {}


async def create_job(request=None, o="", a="", r="", timeout=10):
    global ipc_jobs
    global ipc_locks
    global clusters_initialized

    if request:
        o = (o if o != "" else request.headers.get("op"))
        a = (a if a != "" else request.headers.get("args"))
        r = (r if r != "" else request.headers.get("recep"))
        if timeout == 10:
            timeout = int(request.headers.get("timeout"))

    job_key = "".join(random.choices(string.ascii_letters, k=32))

    recepients = []
    if r == "*":
        for i in clusters_initialized:
            recepients.append(i)
    else:
        try:
            for i in json.loads(r):
                _c = str(i).lower()
                if _c in clusters_initialized:
                    recepients.append(_c)
        except BaseException:
            _c = str(r).lower()
            if _c in clusters_initialized:
                recepients.append(_c)

    ipc_jobs[job_key] = {}
    ipc_locks[job_key] = asyncio.Lock()

    payload = {"o": o, "a": a, "k": job_key, "t": time.time()}

    for r in recepients:
        cluster_jobs[r].append(payload)

    time_start = time.time()
    start_time = time_start
    delay_time = int(time_start) + timeout

    while time.time() < delay_time:
        if len(ipc_jobs[job_key]) == len(recepients):
            break
        await asyncio.sleep(0.05)
        if time.time()-start_time > 1:
            start_time = time.time()
            print("Waiting on job", job_key, "received:",
                  ipc_jobs[job_key].keys(), "total:", recepients)

    responce_payload = {
        "k": job_key,
        "r": r,
        "o": o,
        "a": a,
        "js": time_start,
        "d": ipc_jobs[job_key]
    }

    time_end = time.time()
    responce_payload['jd'] = time_end - time_start

    del ipc_jobs[job_key]

    return responce_payload


async def sending(cluster):
    rockutils.prefix_print(f"Started sending for {cluster}")
    _last_ping = 0
    alive = time.time()
    try:
        while True:
            _t = time.time()
            _jobs = cluster_jobs[cluster]
            if _t - _last_ping > 60:
                _jobs.append({
                    "o": "PING",
                    "a": "",
                    "k": f"ping.{cluster}"
                })
                _last_ping = _t
            if len(_jobs) > 0:
                await websocket.send(json.dumps(_jobs))
                cluster_jobs[cluster] = []

            await asyncio.sleep(0.1)
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        rockutils.prefix_print(str(e), prefix="IPC Sender",
                               prefix_colour="light red", text_colour="red")


async def receiving(cluster):
    rockutils.prefix_print(f"Started receiving for {cluster}")
    try:
        while True:
            _data = json.loads(await websocket.receive())

            print(">>>", _data)
            o = _data['o']
            if o == "SUBMIT" and "ping" in _data['k']:
                last_ping[cluster] = time.time()
                cluster_data[cluster] = _data['d']
                rockutils.prefix_print(
                    f"Retrieved PING from cluster {cluster}")
            elif o == "SHARD_UPDATE":
                d = _data['d']

                text = f"- **Shard {d[1]}** is now **{_status_name.get(d[0])}**"
                await rockutils.send_webhook("https://canary.[removed]", text)

                rockutils.prefix_print(
                    f"shard {d[1]} is now {_status_name.get(d[0])}")
            elif o == "STATUS_UPDATE":
                d = _data['d']
                cluster_status[cluster] = d

                text = f"**Cluster {cluster}** is now **{_status_name.get(d)}**"
                await rockutils.send_webhook("https://canary.[removed]_e9YSarA", text)

                rockutils.prefix_print(
                    f"Cluster {cluster} is now {_status_name.get(d)}")
            elif o == "SUBMIT" and _data['k'] != "push":
                k = _data['k']
                r = _data['r']
                d = _data['d']

                if k in ipc_jobs:
                    ipc_jobs[k][r] = d
            elif o == "PUSH_OPCODE":
                d = _data['d']
                _opcode = d[0]
                _args = d[1]
                r = d[2]

                recepients = []
                if r == "*":
                    for i in clusters_initialized:
                        recepients.append(i)
                else:
                    try:
                        for i in json.loads(r):
                            _c = str(i).lower()
                            if _c in clusters_initialized:
                                recepients.append(_c)
                    except BaseException:
                        _c = str(r).lower()
                        if _c in clusters_initialized:
                            recepients.append(_c)

                for _r in recepients:
                    ipc_jobs[_r].append({
                        "o": _opcode,
                        "a": _args,
                        "k": "push"
                    })

            await asyncio.sleep(0.05)
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        rockutils.prefix_print(str(e), prefix="IPC Receiver",
                               prefix_colour="light red", text_colour="red")


# @app.route("/_internal/sendemail", methods=["POST"])
# async def sendemail():
#     headers = request.headers
#     if headers["Authorization"] != "gFt3hNzXnGmUC93BumXjzYfhXTFgcGCnprvxSDwu33ChAChs":
#         return "", 400

#     body = await request.data
#     j = json.loads(body)

#     mail_params = j["transport"]
#     res = j["mail"]

#     # Prepare Message
#     msg = MIMEMultipart()
#     msg.preamble = res["subject"]
#     msg['Subject'] = res["subject"]
#     msg['From'] = res["from"]
#     msg['To'] = res["to"]

#     msg.attach(MIMEText(res["data"], res["type"], 'utf-8'))

#     # Contact SMTP server and send Message
#     host = mail_params.get('host', 'localhost')
#     isSSL = mail_params.get('SSL', False)
#     isTLS = mail_params.get('TLS', False)
#     port = mail_params.get('port', 465 if isSSL else 25)
#     smtp = aiosmtplib.SMTP(hostname=host, port=port, use_tls=isSSL)
#     await smtp.connect()
#     if isTLS:
#         await smtp.starttls()
#     if 'user' in mail_params:
#         await smtp.login(mail_params['user'], mail_params['password'])
#     await smtp.send_message(msg)
#     await smtp.quit()


@app.route("/future")
async def future():
    return await render_template("future.html", session=session)


@app.route("/robots.txt")
async def robots():
    return await send_file("robots.txt")


@app.route("/d5df36181ddf2ea3a832645f2aa16371.txt")
async def detectify():
    return await send_file("d5df36181ddf2ea3a832645f2aa16371.txt")


@app.route("/a")
async def senda():
    return await send_file("a.js")


@app.route("/ads.txt")
async def ads():
    return await send_file("ads.txt")


@app.route("/.well-known/apple-developer-merchantid-domain-association")
async def apple_pay():
    return await send_file("apple-developer-merchantid-domain-association")


@app.route("/api/interactions", methods=['POST'])
async def interactions():
    # Your public key can be found on your application in the Developer Portal
    PUBLIC_KEY = '2f519b930c9659919c7e96617a8e9a400b285ddfbb9fb225d36a0441b7e697bb'

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = await request.data

    message = timestamp.encode() + await request.data

    print(message)
    try:
        vk = VerifyKey(bytes.fromhex(PUBLIC_KEY))
        vk.verify(message, bytes.fromhex(signature))
    except BadSignatureError:
        print("invalid signature")
        return abort(401, 'invalid request signature')
    except Exception as e:
        print(e)
        return abort(500, 'oops')

    payload = await request.json
    if payload["type"] == 1:
        return jsonify({
            "type": 1
        })

    if payload["data"]["name"] == "pog":
        return jsonify({
            "type": 4,
            "data": {
                "content": "<:_:732274836038221855>:mega: pog"
            }
        })
    if payload["data"]["name"] == "rock" and payload["guild_id"] == "341685098468343822":
        user_id = payload["member"]["user"]["id"]

        a = datetime.now()
        b = time.time()
        week = b + (60*60*24*7)

        if a.month != 12 or not (31 >= a.day >= 25):
            return jsonify({
                "type": 3,
                "data": {
                    "content": "It is not that time of the year yet. Come back soon!"
                }
            })

        userinfo = await get_user_info(user_id)

        if userinfo["m"]["1"]["u"] and userinfo["m"]["1"]["u"] > week:
            return jsonify({
                "type": 3,
                "data": {
                    "content": "You already have this present. Don't try again!"
                }
            })

        userinfo["m"]["1"]["h"] = True
        userinfo["m"]["1"]["u"] = week

        await set_value(connection, "users", str(user_id), userinfo)

        return jsonify({
            "type": 4,
            "data": {
                "content": f":gift:<:_:732274836038221855> Enjoy the rest of this year <@{user_id}>, heres a week of Welcomer Pro for a special server of your choosing. Do `+membership add` on the server you want to add this to"
            }
        })

    return jsonify({
        "type": 5,
    })


@app.route("/api/job/<auth>", methods=['POST', 'GET'])
async def ipc_job(auth):
    if auth != config['ipc']['auth_key']:
        return "Invalid authentication", 403
    return jsonify(await create_job(request))


@app.route("/api/ipc_identify/<key>/<cluster>/<auth>", methods=["POST", "GET"])
async def ipc_identify(key, cluster, auth):
    if auth != config['ipc']['auth_key']:
        return "Invalid authentication", 403

    cluster = str(cluster).lower()

    lock = identify_locks.get(key)
    if not lock:
        identify_locks[key] = {
            'limit': 1,
            'available': 1,
            'duration': 5.5, # 5.5 seconds
            'resetsAt': 0,
        }

        lock = identify_locks[key]

    now = time.time()

    if lock['resetsAt'] <= now:
        print(f"{key} has refreshed identify lock for {cluster}")
        lock['resetsAt'] = now + lock['duration']
        lock['available'] = lock['limit']

    if lock['available'] <= 0:
        sleepTime = lock['resetsAt'] - now
        print(f"{cluster} has hit identify lock on {key} told to wait {sleepTime} seconds")
        return jsonify({
            "available": False,
            "sleep": sleepTime,
        })

    lock['available'] -= 1

    print(f"{cluster} has gotten identify lock on {key}")
    return jsonify({
        "available": True,
    })


@app.route("/api/ipc_submit/<cluster>/<auth>", methods=["POST"])
async def ipc_submit(cluster, auth):
    if auth != config['ipc']['auth_key']:
        return "Invalid authentication", 403

    cluster = str(cluster).lower()

    form = dict(await request.json)

    k = form['k']
    r = form['r']
    d = form['d']

    if k == "push":
        print(cluster, "pushed submit")
        return "OK", 200

    if "ping" in k:
        last_ping[cluster] = time.time()
        cluster_data[cluster] = d
        rockutils.prefix_print(
            f"Retrieved PING from cluster {cluster}")

    else:
        if k in ipc_jobs:
            ipc_jobs[k][r] = d
            print("Submitted", k, "for", cluster)
        else:
            print(k, "is not valid key")

    return "OK", 200


@app.websocket("/api/ipc/<cluster>/<auth>")
async def ipc_slave(cluster, auth):
    if auth != config['ipc']['auth_key']:
        return "Invalid authentication", 403
    else:
        await websocket.accept()

    cluster = str(cluster).lower()

    ipc_jobs[cluster] = []
    clusters_initialized.add(cluster)

    if cluster not in cluster_jobs:
        cluster_jobs[cluster] = []

    rockutils.prefix_print(f"Connected to cluster {cluster}")

    # loop = asyncio.get_event_loop()
    try:
        await asyncio.gather(
            copy_current_websocket_context(sending)(cluster),
            copy_current_websocket_context(receiving)(cluster)
        )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        rockutils.prefix_print(str(e), prefix="IPC Slave",
                               prefix_colour="light red", text_colour="red")

#############################################################
# DASHBOARD
#############################################################


@app.errorhandler(404)
async def not_found_error(e):
    if "php" in request.url or ".env" in request.url:
        return (await render_template('fakephpinfo.html', request=request)), 200

    if "static" in request.url:
        return "404", 404

    return (await render_template('error.html', error="I cant seem to find this page. Maybe you went to the wrong place?", image="finding")), 404


@app.errorhandler(403)
async def forbidden_error(e):
    print("403")
    if "static" in request.url:
        return "403"
    return (await render_template('error.html', error="Hm, it seems you cant access this page. Good try though old chap. If this was a guild page, the owner disabled the public listing.", image="sir")), 403


@app.errorhandler(500)
async def internal_server_error(e):
    print("500")
    print(e)
    if "static" in request.url:
        return "500"
    return (await render_template('error.html', error="Uh oh, seems something pretty bad just happened... Mr Developer, i dont feel so good...", image=random.choice(["sad1", "sad2", "sad3"]))), 500

# Functions


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=_oauth2['client_id'],
        token=token,
        state=state,
        scope=scope,
        redirect_uri=_oauth2['redirect_uri'][_domain],
        auto_refresh_kwargs={
            'client_id': _oauth2['client_id'],
            'client_secret': _oauth2['client_secret'],
        },
        auto_refresh_url=_oauth2['token_url'],
        token_updater=token_updater
    )


async def get_user_info(id, refer=""):
    try:
        rockutils.prefix_print(
            f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for U:{id}",
            prefix="User Info:Get",
            prefix_colour="light green")
        # guild_info = r.table("users").get(str(id)).run(rethink)
        guild_info = await get_value(connection, "users", str(id))

        return guild_info or None
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        rockutils.prefix_print(
            f"Error occured whilst retrieving info for U:{id}. {e}",
            prefix="User Info:Update",
            prefix_colour="red",
            text_colour="light red")
        return False


async def get_guild_info(id, refer="", default_if_empty=True):
    try:
        rockutils.prefix_print(
            f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for G:{id}",
            prefix="Guild Info:Get",
            prefix_colour="light green")
        # guild_info = r.table("guilds").get(str(id)).run(rethink)
        guild_info = await get_value(connection, "guilds", str(id))

        if not guild_info:
            await create_job(o="cachereload", a=str(id), r="*")
            # guild_info = r.table("guilds").get(str(id)).run(rethink)
            guild_info = await get_value(connection, "guilds", str(id))

        if default_if_empty:
            return guild_info or rockutils.load_json("cfg/default_guild.json")
        else:
            return guild_info
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        rockutils.prefix_print(
            f"Error occured whilst retrieving info for G:{id}. {e}",
            prefix="Guild Info:Update",
            prefix_colour="red",
            text_colour="light red")
        return rockutils.load_json("cfg/default_guild.json")


async def update_guild_info(id, data, forceupdate=False, refer=""):
    try:
        rockutils.prefix_print(
            f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for G:{id}",
            prefix="Guild Info:Update",
            prefix_colour="light green")
        t = time.time()
        # if forceupdate:
        #     r.table("guilds").get(str(id)).update(data).run(rethink)
        # else:
        #     r.table("guilds").get(str(id)).replace(data).run(rethink)
        await set_value(connection, "guilds", str(id), data)
        te = time.time()
        if te - t > 1:
            rockutils.prefix_print(
                f"Updating guild info took {math.floor((te-t)*1000)}ms",
                prefix="Guild Info:Update",
                prefix_colour="red",
                text_colour="light red")
        return True
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        rockutils.prefix_print(
            f"Error occured whilst updating info for G:{id}. {e}",
            prefix="Guild Info:Update",
            prefix_colour="red",
            text_colour="light red")
        return False


async def get_guild_donations(guild_info):
    _time = time.time()
    valid_donations = []

    try:
        _userinfo = await get_user_info(guild_info['d']['g']['o']['id'])
        if _userinfo and _userinfo['m']['p']:
            valid_donations.append("partner")
    except BaseException:
        pass

    if guild_info['d']['b']['hb']:
        valid_donations.append("cbg")

    for id in guild_info['d']['de']:
        try:
            if has_special_permission(id, support=True, developer=True, admin=True, trusted=True):
                return True
            _userinfo = await get_user_info(id)
            if _userinfo:
                if _userinfo['m']['1']['h'] and (
                        _time < _userinfo['m']['1']['u'] or
                        _userinfo['m']['1']['p']):
                    valid_donations.append("donation")
                    break
                if _userinfo['m']['3']['h'] and (
                        _time < _userinfo['m']['3']['u'] or
                        _userinfo['m']['3']['p']):
                    valid_donations.append("donation")
                    break
                if _userinfo['m']['5']['h'] and (
                        _time < _userinfo['m']['5']['u'] or
                        _userinfo['m']['5']['p']):
                    valid_donations.append("donation")
                    break
        except BaseException:
            pass

    return valid_donations


async def has_special_permission(self, id, support=False,
                                 developer=False, admin=False,
                                 trusted=False):
    try:
        id = int(id)
    except BaseException:
        return False

    if support and id in config['roles']['support']:
        return True

    if developer and id in config['roles']['developer']:
        return True

    if admin and id in config['roles']['admins']:
        return True

    if trusted and id in config['roles']['trusted']:
        return True

    return False


async def has_guild_donated(guild_info, donation=True, partner=True):
    _time = time.time()

    try:
        if partner:
            _userinfo = await get_user_info(guild_info['d']['g']['o']['id'])
            if _userinfo and _userinfo['m']['p']:
                return True
    except BaseException:
        pass

    for id in guild_info['d']['de']:
        try:
            _userinfo = await get_user_info(id)
            if has_special_permission(id, support=True, developer=True, admin=True, trusted=True):
                return True
            if _userinfo:
                if donation:
                    if _userinfo['m']['1']['h'] and (
                            _time < _userinfo['m']['1']['u'] or
                            _userinfo['m']['1']['p']):
                        return True
                    if _userinfo['m']['3']['h'] and (
                            _time < _userinfo['m']['3']['u'] or
                            _userinfo['m']['3']['p']):
                        return True
                    if _userinfo['m']['5']['h'] and (
                            _time < _userinfo['m']['5']['u'] or
                            _userinfo['m']['5']['p']):
                        return True
        except BaseException:
            pass

    return False


# async def async_cache_discord(url, bot_type, key=None, custom_token=None, default={}, cachetime=120):
#     if bot_type not in config['tokens']:
#         return False, default
#     if not custom_token:
#         token = config['tokens'].get(bot_type)
#     else:
#         token = custom_token
#         key = token['access_token']

#     if not key:
#         key = url

#     url = f"{_oauth2['api_base']}/v6/{url}"
#     _t = time.time()

#     if key not in discord_cache or _t - discord_cache.get(key)['s'] > 0:
#         try:
#             rockutils.prefix_print(f"Retrieving {url}", prefix="Cacher")
#             async with aiohttp.ClientSession() as session:
#                 async with requests.get(url, headers={"Authorization": f"Bot {token}"}) as r:
#                     data = await r.json()

#                     if isinstance(data, dict) and data.get("code"):
#                         rockutils.prefix_print(
#                             f"Encountered bad response: {data}", prefix="Cacher")
#                         discord_cache[key] = {
#                             "d": default,
#                             "s": _t + cachetime
#                         }
#                         return False, data.get("code", -1)

#                     discord_cache[key] = {
#                         "d": data,
#                         "s": _t + cachetime
#                     }
#         except Exception as e:
#             exc_info = sys.exc_info()
#             traceback.print_exception(*exc_info)
#             rockutils.prefix_print(
#                 str(e), prefix="cache_discord", text_colour="red")
#             return False, []
#     return True, discord_cache[key]['d']


async def cache_discord(url, bot_type, key=None, custom_token=None, default={}, cachetime=120):
    if bot_type not in config['tokens']:
        return False, default
    if not custom_token:
        token = config['tokens'].get(bot_type)
    else:
        token = custom_token
        key = token['access_token']

    if not key:
        key = url

    url = f"{_oauth2['api_base']}/v6/{url}"
    _t = time.time()

    if key not in discord_cache or _t - discord_cache.get(key)['s'] > 0:
        try:
            rockutils.prefix_print(f"Retrieving {url}", prefix="Cacher")
            async with aiohttp.ClientSession() as _session:
                async with _session.get(url, headers={"Authorization": f"Bot {token}"}) as res:
                    data = await res.json()

                    if isinstance(data, dict) and data.get("code"):
                        rockutils.prefix_print(
                            f"Encountered bad response: {data}", prefix="Cacher")
                        discord_cache[key] = {
                            "d": default,
                            "s": _t + cachetime
                        }
                        return False, data.get("code", -1)

                    discord_cache[key] = {
                        "d": data,
                        "s": _t + cachetime
                    }
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            rockutils.prefix_print(
                str(e), prefix="cache_discord", text_colour="red")
            return False, []
    return True, discord_cache[key]['d']


async def has_elevation(guild_id, member_id, guild_info=None, bot_type="main"):
    continue_cache = True

    # if "user_id" in session:
    #     user_id = int(session['user_id'])

    #     if user_id in config['roles']['support']:
    #         return True
    #     if user_id in config['roles']['developer']:
    #         return True
    #     if user_id in config['roles']['admins']:
    #         return True

    # _member_id = int(member_id)
    # if _member_id in config['roles']['support']:
    #     return True
    # if _member_id in config['roles']['developer']:
    #     return True
    # if _member_id in config['roles']['admins']:
    #     return True

    elevated = False
    responce = await create_job(o="iselevated", a=[str(member_id), str(guild_id)], r="*")
    for _, cluster_data in responce['d'].items():
        if cluster_data.get("success", False):
            if cluster_data.get("elevated", False):
                elevated = True

    return elevated
    # if not guild_info:
    #     guild_info = await get_guild_info(guild_id)

    # if isinstance(guild_info, dict) and guild_info['d']['b']['hd']:
    #     bot_type = "donator"

    # bot_type = "debug" if _debug else bot_type
    # guild_success, guild = await cache_discord(f"guilds/{guild_id}", bot_type, key=f"guild:{guild_id}", cachetime=600)
    # if asyncio.iscoroutine(guild):
    #     guild = await guild()
    # if not guild_success and guild == 50001:
    #     continue_cache = False

    # if guild_info:
    #     if guild_info['d']['g']['o']:
    #         if int(guild_info['d']['g']['o']['id'] == int(member_id)):
    #             return True

    # if guild_success:
    #     if "owner_id" in guild and (int(guild['owner_id']) == int(member_id)):
    #         return True

    #     if guild_info:
    #         # check staff list and if they are on it
    #         if guild_info.get("st"):
    #             if str(member_id) in guild_info['st']['u']:
    #                 return True

    # if continue_cache:
    #     member_success, member = await cache_discord(f"guilds/{guild_id}/members/{member_id}", bot_type, key=f"member:{guild_id}:{member_id}", cachetime=60)
    #     if asyncio.iscoroutine(member):
    #         member = await member()
    #     if not member_success and guild == 50001:
    #         continue_cache = False

    # if continue_cache:
    #     role_success, roles = await cache_discord(f"guilds/{guild_id}/roles", bot_type, key=f"role:{guild_id}", cachetime=60)
    #     if asyncio.iscoroutine(roles):
    #         roles = await roles()
    #     if not role_success and guild == 50001:
    #         continue_cache = False

    # # get member and roles they have and check if they have certain roles
    # if continue_cache:
    #     if member_success and role_success and "roles" in member:
    #         for role_id in map(int, member['roles']):
    #             for role in roles:
    #                 if int(role['id']) == role_id:
    #                     permissions = discord.permissions.Permissions(
    #                         role['permissions'])
    #                     if permissions.manage_guild or permissions.ban_members or permissions.administrator:
    #                         return True
    # return False


# async def has_elevation(guild_id, member_id, guild_info=None, bot_type="main"):

#     if "user_id" in session:
#         user_id = int(session['user_id'])

#         if user_id in config['roles']['support']:
#             return True
#         if user_id in config['roles']['developer']:
#             return True
#         if user_id in config['roles']['admins']:
#             return True

#     if not guild_info:
#         guild_info = await get_guild_info(guild_id)

#     if isinstance(guild_info, dict) and guild_info['d']['b']['hd']:
#         bot_type = "donator"

#     bot_type = "debug" if _debug else bot_type
#     guild_success, guild = await async_cache_discord(
#         f"guilds/{guild_id}", bot_type, key=f"guild:{guild_id}", cachetime=600)
#     if asyncio.iscoroutine(guild):
#         guild = await guild()

#     if guild_info:
#         if int(guild_info['d']['g']['o']['id'] == int(member_id)):
#             return True

#     if guild_success:
#         if "owner_id" in guild and (int(guild['owner_id']) == int(member_id)):
#             return True

#         if guild_info:
#             # check staff list and if they are on it
#             if guild_info.get("st"):
#                 if str(member_id) in guild_info['st']['u']:
#                     return True

#     member_success, member = await async_cache_discord(
#         f"guilds/{guild_id}/members/{member_id}", bot_type, key=f"member:{guild_id}:{member_id}")
#     role_success, roles = await async_cache_discord(
#         f"guilds/{guild_id}/roles", bot_type, key=f"role:{guild_id}")
#     if asyncio.iscoroutine(member):
#         member = await member()
#     if asyncio.iscoroutine(roles):
#         roles = await roles()

#     # get member and roles they have and check if they have certain roles
#     if member_success and role_success and "roles" in member:
#         for role_id in map(int, member['roles']):
#             for role in roles:
#                 if int(role['id']) == role_id:
#                     permissions = discord.permissions.Permissions(
#                         role['permissions'])
#                     if permissions.manage_guild or permissions.ban_members or permissions.administrator:
#                         return True
#     return False


async def get_guild_roles(guild_id):
    roles = {}
    responce = await create_job(o="getguildroles", a=str(guild_id), r="*")
    for _, cluster_data in responce['d'].items():
        if cluster_data.get("success", False):
            for role in cluster_data.get("roles"):
                if role['id'] in roles:
                    if role['higher'] == True:
                        roles[role['id']]['higher'] = True
                else:
                    roles[role['id']] = role
    return roles.values()


async def get_guild_channels(guild_id):
    responce = await create_job(o="getguildchannels", a=str(guild_id), r="*")
    for _, cluster_data in responce['d'].items():
        if cluster_data.get("success", False):
            return cluster_data.get("channels")


async def get_user(token):

    _t = time.time()
    key = token['access_token']

    if key not in user_cache or _t - user_cache.get(key)['s'] > 0:
        try:
            discord = make_session(token=token)

            user = await discord.request("GET", _oauth2['api_base'] + '/users/@me')
            _users = await user.json()

            has, _guilds = cache.check_cache(
                "user:" + _users['id'] + ":guilds")
            if not has:
                guilds = await discord.request("GET", _oauth2['api_base'] + '/users/@me/guilds')
                _guilds = await guilds.json()

                cache.add_cache(
                    "user:" + _users['id'] + ":guilds", 30, _guilds)

            await discord.close()
            user_cache[key] = {
                "d": {"user": _users, "guilds": _guilds},
                "s": _t + 60
            }

            data = user_cache[key]['d']

            if str(user.status)[0] != "2":
                return False, data
            if str(guilds.status)[0] != "2":
                return False, data
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            print(f"[get_user] {e}")
            return False, {}

    data = user_cache[key]['d']

    if data['user'].get('code') == 0 and "401" in data['user'].get('message', ''):
        return False, data

    # if "message" in data['user'] and "401: Unauthorized" in data['user'][
    #         'message']:
    #     return False, data

    return True, data

# has_elevation(guild id, member id, bot type)
# has_elevation(436243598925627392, 143090142360371200, "debug")

#############################################################
# DASHBOARD PAGES
#############################################################


@app.route("/logout")
async def _logout():
    session.clear()
    return redirect("/")


@app.route("/login")
async def _login():
    discord = make_session(scope=['identify', 'guilds'])
    authorization_url, state = discord.authorization_url(
        _oauth2['authorization_url'])
    session['oauth2_state'] = state
    await discord.close()
    return redirect(authorization_url)


@app.route("/callback")
async def _callback():

    url = request.url.replace('http://', 'https://', 1)

    try:
        discord = make_session(state=session.get(
            "oauth2_state"), scope=['identify', 'guilds'])
        token = await discord.fetch_token(
            _oauth2['token_url'],
            client_secret=_oauth2['client_secret'],
            authorization_response=url)
        await discord.close()
    except Exception as e:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        return redirect("/login")

    user_success, user = await get_user(token)
    if asyncio.iscoroutine(user):
        user = await user()
    if not user_success:
        return redirect("/login")

    _t = math.ceil(time.time())
    session['oauth2_token'] = token
    session['oauth2_check'] = math.ceil(time.time())
    if user_success:
        session['user_id'] = str(user['user']['id'])
        session['user'] = str(user['user']['username']) + \
            "#" + str(user['user']['discriminator'])
        session['user_data'] = user['user']
        session['guild_data'] = user['guilds']
    session['reloaded_data'] = _t
    session['dashboard_guild'] = "-"
    session['developer_mode'] = False
    session.permanent = True

    if session.get("previous_path"):
        return redirect(session['previous_path'])

    return redirect("/dashboard")


def valid_oauth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session['previous_path'] = request.path
        if session.get("oauth2_token") is None:
            return redirect("/login")

        should_check = False

        if sum(
            1 if not session.get(c) else 0 for c in [
                'user_id',
                'user_data',
                'guild_data',
                'oauth2_check']) > 0:
            should_check = True

        if session.get("oauth2_check") is None or time.time() - \
                session.get("oauth2_check") > 604800:
            should_check = True

        if should_check:
            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function


async def is_valid_dash_user():
    session['previous_path'] = request.path

    # Manualy retrieving the guild data from oauth2 every
    # time is not required as oauth is updated every 2 minutes.
    # Handled by before_requests -> cache_data()
    guilds = session.get("guild_data")

    if not guilds:
        cache_data()
        guilds = session.get("guild_data")
        if not guilds:
            return redirect("/login")

    guild = None
    dashboard_guild = session.get("dashboard_guild")

    for item in guilds:
        if isinstance(item, dict) and str(item.get("id")) == str(dashboard_guild):
            guild = item

    # redirects to invalid guild if no data and no developer mode
    if not guild and not session.get("developer_mode", False):
        return redirect("/dashboard?invalidguild")

    # allow if they are the owner
    if guild['owner']:
        return True

    # check users permissions from oauth2
    permissions = discord.permissions.Permissions(guild['permissions'])
    if permissions.manage_guild or permissions.ban_members or permissions.administrator:
        return True

    # check if has elevation
    return await has_elevation(
        guild['id'],
        session.get("user_id"),
        bot_type="main")


def valid_dash_user(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        session['previous_path'] = request.path

        # Manualy retrieving the guild data from oauth2 every
        # time is not required as oauth is updated every 2 minutes.
        # Handled by before_requests -> cache_data()
        guilds = session.get("guild_data")

        if not guilds:
            cache_data()
            guilds = session.get("guild_data")
            if not guilds:
                return redirect("/login")

        guild = None
        dashboard_guild = session.get("dashboard_guild")

        for item in guilds:
            if isinstance(item, dict) and str(item.get("id")) == str(dashboard_guild):
                guild = item

        # redirects to invalid guild if no data and no developer mode
        if not guild and not session.get("developer_mode", False):
            return redirect("/dashboard?invalidguild")

        # allow if they are the owner
        if guild['owner']:
            return f(*args, **kwargs)

        # check users permissions from oauth2
        permissions = discord.permissions.Permissions(guild['permissions'])
        if permissions.manage_guild or permissions.ban_members or permissions.administrator:
            return f(*args, **kwargs)

        # check if has elevation
        if not await has_elevation(
                guild['id'],
                session.get("user_id"),
                bot_type="main"):
            return redirect("/dashboard?missingpermission")

        return f(*args, **kwargs)

    return decorated_function


@app.before_request
async def cache_data():
    # Checks all oauth2 information is up to date and does not check if it is
    # a static page
    if "static" not in request.url:
        _t = math.ceil(time.time())
        if session.get("reloaded_data") and session.get(
                "oauth2_token") and _t - session.get("reloaded_data") > 120:
            user_success, user = await get_user(session.get("oauth2_token"))
            if asyncio.iscoroutine(user):
                user = await user()
            if user_success:
                session['reloaded_data'] = _t
                session['user_id'] = str(user['user']['id'])
                session['user_data'] = user['user']
                session['guild_data'] = user['guilds']
                session.permanent = True

    session.permanent = True
    app.permanent_session_lifetime = timedelta(days=7)

# @app.route("/dashboard")
# @valid_oauth_required
# async def _dashboard():
#     return "I am dashboard"

#     _args = list(dict(request.args).keys())
#     if len(_args) == 1:
#         arg = _args[0]
#         if arg == "missingpermission":
#             pass
#         elif arg == "invalidguild":
#             pass
#         elif arg == "missingdata":
#             pass
    # handle invalid guild
    # handle missing guild info
    # handle no permissions\


@app.route("/api/session")
async def getsession():
    return jsonify(dict(session))


@app.route("/api/getbackground/<background>")
async def getbackground(background):
    cdnpath = config['cdn']['location']
    if "custom" not in background:
        f = os.path.join(cdnpath, "Images", background)
    else:
        f = os.path.join(cdnpath, "CustomImages", background)
        if not os.path.exists(f):
            background = background.replace(".png", ".gif")
            f = os.path.join(cdnpath, "CustomImages", background)
            if not os.path.exists(f):
                background = background.replace(".gif", ".jpg")
                f = os.path.join(cdnpath, "CustomImages", background)

    if not os.path.exists(f):
        bgloc = f"preview-samples/none.jpg"
        if not os.path.exists(bgloc):
            txt = "This background could not be found"
            f_h = open(os.path.join(cdnpath, "Images", "default.png"), "rb")
            i_h = Image.open(f_h)
            i_h = i_h.convert("RGBA")

            size = 40
            while True:
                default = ImageFont.truetype(os.path.join(
                    cdnpath, "Fonts", "default.ttf"), size)
                size -= 1
                w, h = default.getsize(txt)
                if w < i_h.size[0] or size < 2:
                    break

            iw, ih = i_h.size
            y = ih - 20 - h
            x = math.floor((iw - w) / 2)
            frame_draw = ImageDraw.Draw(i_h)
            frame_draw.text((x + 1, y + 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x + 1, y - 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x - 1, y + 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x - 1, y - 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x, y), txt, font=default, fill=(255, 255, 255))
            i_h = i_h.convert("RGB")
            i_h.thumbnail((400, 160))
            i_h.save(bgloc, format="jpeg", quality=50)
            f_h.close()
    else:
        bgloc = f"preview-samples/{'.'.join(background.split('.')[:-1])}.jpg"
        if not os.path.exists(bgloc) or "custom" in f.lower():
            txt = background

            f_h = open(f, "rb")
            i_h = Image.open(f_h)
            i_h = i_h.convert("RGBA")

            txt = ".".join(txt.split(".")[:-1])

            size = 40
            while True:
                default = ImageFont.truetype(os.path.join(
                    cdnpath, "Fonts", "default.ttf"), size)
                size -= 1
                w, h = default.getsize(txt)
                if w < i_h.size[0] or size < 2:
                    break

            iw, ih = i_h.size
            y = ih - 20 - h
            x = math.floor((iw - w) / 2)
            frame_draw = ImageDraw.Draw(i_h)
            frame_draw.text((x + 1, y + 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x + 1, y - 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x - 1, y + 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x - 1, y - 1), txt, font=default, fill=(0, 0, 0))
            frame_draw.text((x, y), txt, font=default, fill=(255, 255, 255))
            i_h = i_h.convert("RGB")
            i_h.thumbnail((400, 160))
            i_h.save(bgloc, format="jpeg", quality=50)
            f_h.close()

    return await send_file(bgloc, cache_timeout=-1)


@app.route("/api/internal-status")
async def api_internal_status():
    return jsonify(cluster_status)


@app.route("/api/status")
async def api_status():
    _time = time.time()

    clusters = {}
    for i in list(["debug", "donator", "b"] + list(range(config['bot']['clusters']))):
        if i == "debug":
            name = "DB"
        elif i == "b":
            name = "B"
        elif "donator" in str(i):
            name = i.replace("donator", "DN")
        else:
            name = f"C{i}"

        clusters[str(i)] = {
            "alive": False,
            "pingalive": False,
            "stats": {},
            "lastping": 0,
            "id": i,
            "name": name
        }

    for cluster, ping in last_ping.items():
        cluster = str(cluster)
        clusters[cluster]['alive'] = True
        if _time - ping < 70:
            clusters[cluster]['pingalive'] = True
        clusters[cluster]['lastping'] = _time - ping

    for cluster, data in cluster_data.items():
        print(cluster, data)
        cluster = str(cluster)
        clusters[cluster]['stats'] = data
        clusters[cluster]['stats']['uptime'] = time.time() - data['init']
        clusters[cluster]['stats']['displayed'] = rockutils.produce_human_timestamp(
            time.time() - data['init'])
        if data.get("latencies"):
            clusters[cluster]['stats']['highest_latency'] = max(
                list(map(lambda o: o[1], data['latencies'])))
            clusters[cluster]['stats']['lowest_latency'] = max(
                list(map(lambda o: o[1], data['latencies'])))
        else:
            clusters[cluster]['stats']['highest_latency'] = 0
            clusters[cluster]['stats']['lowest_latency'] = 0

    cdnpath = os.path.join(config['cdn']['location'], "Output")
    total, used, free = shutil.disk_usage(config['cdn']['location'])
    space_used = round(get_size(cdnpath) / 10000000) / 100
    total_space = round(total / 10000000) / 100
    space_percentage = round((space_used / total_space) * 1000) / 10
    total_images = len(os.listdir(cdnpath))

    data = {}
    totalstats = {}
    averages = {}
    for v, k in clusters.items():
        if "socketstats" in k.get('stats', {}):
            for name, value in k['stats']['socketstats'][0].items():
                if name not in totalstats:
                    totalstats[name] = 0
                totalstats[name] += value
            averages[v] = k['stats']['socketstats'][2]

    data['socketstats'] = {
        "events": sum([int(c['stats']['socketstats'][1]) for c in clusters.values() if "socketstats" in c.get('stats', {})]),
        "totalevents": totalstats,
        "average": str(sum([int(c['stats']['socketstats'][2]) for c in clusters.values() if "socketstats" in c.get('stats', {})])),
        "averages": averages,
    }

    _clusters = {}
    for k, v in clusters.items():
        _clusters[k] = copy.deepcopy(v)
        if "socketstats" in _clusters[k].get('stats', {}):
            _clusters[k]['stats'].pop("socketstats")

    data['clusters'] = list(
        sorted(_clusters.values(), key=lambda o: o['name']))
    data['space'] = {
        "space_used": space_used,
        "total_space": total_space,
        "space_percentage": space_percentage,
        "stored_images": total_images,
        "analytics": {
            "kb_generated": int(await get_value(connection, "stats", "kb_generated", raw=True)),
            "images_made": int(await get_value(connection, "stats", "images_made", raw=True)),
            "images_requested": int(await get_value(connection, "stats", "images_requested", raw=True))
        }
    }

    return jsonify(data)


@ app.route("/api/search", methods=["GET", "POST"])
async def api_search():
    form = dict(await request.form)
    if "term" in form and len(form['term']) > 3:
        term = form.get("term")
        if len(term) > 2:
            try:
                term = int(term)
                canInt = True
            except BaseException:
                canInt = False
                pass

            if canInt:
                result_payload = await create_job(request=None, o="guildsfind", a=[0, term], r="*")
                payload = []
                for data in result_payload['d'].values():
                    if data['success']:
                        payload = [data['results']]
            else:
                result_payload = await create_job(request=None, o="guildsfind", a=[1, term], r="*")
                payload = rockutils.merge_results_lists(result_payload['d'])
                payload = sorted(
                    payload, key=lambda o: o['users'], reverse=True)
                _payload = payload

                ids = []
                for load in payload:
                    if not load['id'] in ids:
                        _payload.append(load)
                        ids.append(load['id'])
            return jsonify(success=True, data=_payload)
        else:
            return jsonify(success=True, data=[])
    else:
        return jsonify(
            success=False,
            error="Missing search term at key 'term'")


@ app.route("/api/searchemoji", methods=["GET", "POST"])
async def api_searchemoji():
    form = dict(await request.form)
    if "term" in form and len(form['term']) > 3:
        result_payload = await create_job(request=None, o="searchemoji", a=form.get("term"), r="*")
        payload = rockutils.merge_results_lists(
            result_payload['d'], key="data")
        for i, v in enumerate(payload):
            payload[i][3] = ""
        return jsonify(success=True, data=payload)

    return jsonify(
        success=False,
        error="Missing search term at key 'term'")


async def check_guild(guild):
    guildinfo = await get_guild_info(int(guild.get("id")), default_if_empty=False)
    if guildinfo:
        return await has_elevation(int(guild.get("id")), int(session.get("user_id")), guild_info=guildinfo, bot_type="main")
    else:
        return False


@ app.route("/api/guilds")
@ valid_oauth_required
async def api_guilds():
    user_id = session.get("user_id", None)

    has, mutres = cache.check_cache("user:" + user_id + ":guilds_mutual")

    if has:
        _guilds = mutres[0]
        clusters = mutres[1]
        missing = mutres[2]
    else:
        # try:
        #     discord = make_session(token=session.get("oauth2_token"))
        #     user_guilds = await discord.request("GET", _oauth2['api_base'] + '/users/@me/guilds')

        #     guilds = []
        #     for guild in await user_guilds.json():
        #         if isinstance(guild, dict):
        #             guild['has_elevation'] = await check_guild(guild)
        #             guilds.append(guild)
        # except Exception as e:
        #     return jsonify({"success": False, "error": str(e)})
        # return jsonify({"success": True, "guilds": guilds})

        discord = make_session(token=session.get("oauth2_token"))

        has, val = cache.check_cache("user:" + session['user_id'] + ":guilds")
        if not has:
            guilds = await discord.request("GET", _oauth2['api_base'] + '/users/@me/guilds')
            user_guilds_json = await guilds.json()

            if type(user_guilds_json) == dict:
                if user_guilds_json.get("message", "") == "You are being rate limited.":
                    # fuck
                    return jsonify({"success": False, "error": f"We are being ratelimited, try again in {user_guilds_json.get('retry_after')} seconds"})

            cache.add_cache(
                "user:" + session['user_id'] + ":guilds", 30, user_guilds_json)
        else:
            user_guilds_json = val

        # user_guilds = await discord.request("GET", _oauth2['api_base'] + '/users/@me/guilds')
        # user_guilds_json = await user_guilds.json()
        # print(user_guilds_json)
        ids = list(map(lambda o: o['id'], user_guilds_json))

        guilds = []
        clusters = []
        missing = list(["debug", "donator", "b"] +
                       list(map(str, range(config['bot']['clusters']))))

        if user_id:
            responce = await create_job(o="userelevated", a=[user_id, ids], r="*", timeout=50)
            for cluster, cluster_data in responce['d'].items():
                if cluster_data.get("success", False):
                    if cluster in missing:
                        missing.remove(cluster)
                    else:
                        print(cluster, "is not in missing list")
                    clusters.append(cluster)
                    guilds += cluster_data.get("mutual", [])

        _guildids = {}
        _guilds = []
        for guild in guilds:
            _id = guild['id']
            if _guildids.get(_id, True):
                _guilds.append(guild)
                _guildids[_id] = False

        cache.add_cache(
            "user:" + user_id + ":guilds_mutual", 30, [_guilds, clusters, missing])

    return jsonify({"success": True, "guilds": _guilds, "clusters": clusters, "missing": missing})


@ app.route("/api/resetconfig", methods=["POST"])
@ valid_oauth_required
async def api_resetconfig():
    user_id = session.get("user_id", None)
    guild_id = session.get("dashboard_guild", None)
    if not guild_id:
        return jsonify(success=False, error="Invalid guild key")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return jsonify(success=False, error="No guild information")

    if not await has_elevation(guild_id, user_id, guild_info=guild_info, bot_type="main"):
        return jsonify(success=False, error="Missing permissions")

    # r.table("guilds").get(guild_id).delete().run(rethink)
    await self.delete_value("guilds", guild_id)
    await create_job(o="cachereload", a=guild_id, r="*")
    return jsonify(success=True)


@ app.route("/api/invites", methods=["POST"])
@ valid_oauth_required
async def api_invites():
    user_id = session.get("user_id", None)
    guild_id = session.get("dashboard_guild", None)
    if not guild_id:
        return jsonify(success=False, error="Invalid guild key")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return jsonify(success=False, error="No guild information")

    if not await has_elevation(guild_id, user_id, guild_info=guild_info, bot_type="main"):
        return jsonify(success=False, error="Missing permissions")

    invites = []
    _time = time.time()
    for invite in guild_info['d']['i']:

        invite['duration'] = int(invite.get('duration', 0))
        invite['created_at_str'] = rockutils.since_unix_str(
            invite['created_at'])

        if invite['duration'] > 0:
            invite['expires_at_str'] = rockutils.since_seconds_str(
                _time - (invite['created_at'] + invite['duration']), include_ago=False)
        else:
            invite['expires_at_str'] = "∞"

        invites.append(invite)

    invites = sorted(invites, key=lambda o: o['uses'], reverse=True)
    return jsonify(success=True, data=invites)


@ app.route("/api/punishments/<mtype>", methods=["GET", "POST"])
@ valid_oauth_required
# @valid_dash_user
async def api_punishments(mtype="false"):
    res = await is_valid_dash_user()
    if res != True:
        return res

    # user id | user display | moderator id | moderator name | punishment type
    # | reason | punishment start | punishment duration | is handled
    guild_id = session.get("dashboard_guild", None)
    if not guild_id:
        return jsonify(success=False, error="Invalid guild key")

    if not mtype.lower() in ['true', 'false', 'reset', 'export']:
        mtype = "false"

    if mtype.lower() in ['true', 'false']:
        try:
            if os.path.exists(f"punishments/{guild_id}.csv"):
                file = open(f"punishments/{guild_id}.csv", "r")
                data = csv.reader(file)
            else:
                data = []

            if mtype.lower() == "true":
                data = list(filter(lambda o: o[8].lower() == "false", data))

            # punishment type | user display | moderator display | reason |
            # date occured | duration | handled
            _data = sorted(data, key=lambda o: int(o[6]), reverse=True)
            data = []

            for audit in _data:
                data.append(
                    [f"{audit[4][0].upper()}{audit[4][1:].lower()}",
                     f"{audit[1]} ({audit[0]})", f"{audit[3]} ({audit[2]})",
                     "-" if audit[5] in [None, "", " "] else audit[5].strip(),
                     rockutils.since_unix_str(int(audit[6])).strip(),
                     rockutils.since_seconds_str(
                         int(audit[7]),
                         allow_secs=True, include_ago=False).strip()
                     if int(audit[7]) > 0 else ("∞" if "temp" in audit[4].lower() else "-"),
                     "Handled" if audit[8].lower() == "true" else "Ongoing", ])

            return jsonify(success=True, data=data)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))
    elif mtype.lower() == "export":
        if os.path.exists(f"punishments/{guild_id}.csv"):
            return await send_file(f"punishments/{guild_id}.csv", as_attachment=True, attachment_filename=f"{guild_id}.csv")
        else:
            return jsonify(success=False)
    elif mtype.lower() == "reset":
        if os.path.exists(f"punishments/{guild_id}.csv"):
            os.remove(f"punishments/{guild_id}.csv")
            return jsonify(success=True)
        else:
            return jsonify(success=True)


@ app.route("/api/logs/<mtype>", methods=["GET", "POST"])
@ valid_oauth_required
# @valid_dash_user
async def api_logs(mtype="false"):
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    if not guild_id:
        return jsonify(success=False, error="Invalid guild key")

    if not mtype.lower() in ['view', 'reset', 'export']:
        mtype = "view"

    if mtype.lower() == "view":
        try:
            if os.path.exists(f"logs/{guild_id}.csv"):
                file = open(f"logs/{guild_id}.csv", "r")
                data = list(csv.reader(file))
            else:
                data = []

            return jsonify(success=True, data=data)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))
    elif mtype.lower() == "export":
        if os.path.exists(f"logs/{guild_id}.csv"):
            return await send_file(f"logs/{guild_id}.csv", as_attachment=True, attachment_filename=f"{guild_id}.csv")
        else:
            return jsonify(success=False)
    elif mtype.lower() == "reset":
        if os.path.exists(f"logs/{guild_id}.csv"):
            os.remove(f"logs/{guild_id}.csv")
            return jsonify(success=True)
        else:
            return jsonify(success=True)


@ app.route("/api/invite/<id>", methods=["GET", "POST"])
async def api_invite(id):
    guild_info = await get_guild_info(id)
    if not guild_info:
        return jsonify(success=False, error="This guild is not valid")

    if not guild_info['d']['b']['ai']:
        return jsonify(
            success=False,
            error="This server has disabled invites through welcomer")

    has_invite = False
    invite_code = ""
    responce = await create_job(o="guildinvite", a=str(id), r="*")

    for cluster_id, cluster_data in responce['d'].items():
        if cluster_data.get("success", False) and \
           cluster_data.get("invite", None):
            invite_code = cluster_data['invite']
            has_invite = True

    if not has_invite:
        return jsonify(
            success=False,
            error="Failed to create an invite. The bot may be missing permissions")

    return jsonify(success=True, code=invite_code)

# /api/logs/retrieve
# /api/logs/clear
# /api/logs/export

# /api/punishments/retrieve
# /api/punishments/clear
# /api/punishments/export

##########################################################################


@ app.route("/patreonhook", methods=['GET', 'POST'])
async def patreon():
    print("Received patreon webhook")
    headers = request.headers
    json_data = await request.json

    print("recieved patreon hook")

    patreon_event = headers['X-Patreon-Event']
    try:
        discord_info = json_data['included'][1]['attributes']['social_connections']['discord']
    except BaseException:
        discord_info = None

    if isinstance(discord_info, dict):
        patreon_discord_id = discord_info.get("user_id")
    else:
        patreon_discord_id = 0

    if "members:" in patreon_event:

        await rockutils.send_webhook("https://canary.[removed]", json.dumps(json_data['data']['attributes']))
        patreon_donation_ammount = json_data['data']['attributes'].get(
            'will_pay_amount_cents', 0) / 100
        lifetime_donation = json_data['data']['attributes'].get(
            'lifetime_support_cents', 0) / 100
        patreon_name = json_data['data']['attributes']['full_name']
        patreon_webhook = rockutils.load_json(
            "cfg/config.json")['webhooks']['donations']

        if patreon_event == "members:pledge:create":
            await rockutils.send_webhook(patreon_webhook, f":money_with_wings: | `{patreon_name}` {f'<@{patreon_discord_id}> `{patreon_discord_id}`' if patreon_discord_id != 0 else '`No discord provided`'} has pledged $`{patreon_donation_ammount}`! Total Pledge: $`{lifetime_donation}`")
        elif patreon_event == "members:pledge:update":
            await rockutils.send_webhook(patreon_webhook, f":money_with_wings: | `{patreon_name}` {f'<@{patreon_discord_id}> `{patreon_discord_id}`' if patreon_discord_id != 0 else '`No discord provided`'} has updated their pledge to $`{patreon_donation_ammount}`! Total Pledge: $`{lifetime_donation}`")
        elif patreon_event == "members:pledge:delete":
            await rockutils.send_webhook(patreon_webhook, f":money_with_wings: | `{patreon_name}` {f'<@{patreon_discord_id}> `{patreon_discord_id}`' if patreon_discord_id != 0 else '`No discord provided`'} is no longer pledging. Total Pledge: $`{lifetime_donation}`")
        elif patreon_event == "members:delete":
            await rockutils.send_webhook(patreon_webhook, f":money_with_wings: | `{patreon_name}` {f'<@{patreon_discord_id}> `{patreon_discord_id}`' if patreon_discord_id != 0 else '`No discord provided`'} is no longer pledging. Total Pledge: $`{lifetime_donation}`")

        if patreon_discord_id != 0:
            await create_job(o="retrieveuser", a=patreon_discord_id, r="*")
            # userinfo = r.table("users").get(
            #     str(patreon_discord_id)).run(rethink)
            userinfo = await get_value(connection, "users", str(patreon_discord_id))

            values = ['1', '3', '5']

            if userinfo:
                for key in values:
                    if key in userinfo['m']:
                        if userinfo['m'][key]['p']:
                            userinfo['m'][key]['h'] = False
                            userinfo['m'][key]['p'] = False

                donation_types = {
                    "0": ["Welcomer Custom Background"],
                    "1": ["Welcomer Pro x1"],
                    "3": ["Welcomer Pro x3"],
                    "5": ["Welcomer Pro x5"]
                }

                k = None
                if patreon_donation_ammount == 5:
                    k = "1"
                elif patreon_donation_ammount == 10:
                    k = "3"
                elif patreon_donation_ammount == 15:
                    k = "5"

                if k:
                    if patreon_event == "members:pledge:create":
                        userinfo['m'][k]['h'] = True
                        userinfo['m'][k]['p'] = True
                    elif patreon_event == "members:pledge:update":
                        userinfo['m'][k]['h'] = True
                        userinfo['m'][k]['p'] = True
                if patreon_donation_ammount in [1, 6]:
                    k = "0"
                    userinfo['m']['hs'] = True

                if k:
                    membership_name = donation_types[k]
                else:
                    return "False"

                # r.table("users").get(str(patreon_discord_id)
                #                      ).update(userinfo).run(rethink)

                await set_value(connection, "users", str(patreon_discord_id), userinfo)
                mutual_clusters = sorted(userinfo['m'].keys())
                for recep in mutual_clusters:
                    try:
                        recep = int(recep)
                    except BaseException:
                        pass
                    data = await create_job(o="donationannounce", a=[patreon_discord_id, membership_name], r=recep)
                    if recep in data['d']:
                        break

    return "True"


@ app.route("/donate/<dtype>/<months>")
@ valid_oauth_required
async def donate_create(dtype, months):

    # return redirect("/donate?disabled")

    donation_types = {
        "0": ["Welcomer Custom Background"],
        "1": ["Welcomer Pro x1"],
        "3": ["Welcomer Pro x3"],
        "5": ["Welcomer Pro x5"],
    }

    dontype = dtype + ":" + str(months)

    if str(dtype) == "0":
        months = "ever"
    else:
        months = f" {months} month(s)"

    if dontype not in prices.keys():
        return redirect("/donate?invaliddonation")

    donation = donation_types.get(dtype)
    price = prices.get(dontype)
    description = f"{donation[0]} for{months}"

    patreon_webhook = config['webhooks']['donations']

    if not donation:
        return redirect("/donate?invaliddonation")

    payer = {"payment_method": "paypal"}

    items = [{"name": dontype, "price": price,
              "currency": "GBP", "quantity": "1"}]
    amount = {"total": price, "currency": "GBP"}

    redirect_urls = {
        "return_url": f"https://{_domain}/donate/confirm?success=true",
        "cancel_url": f"https://{_domain}/donate?cancel"}
    payment = paypalrestsdk.Payment({"intent": "sale",
                                     "payer": payer,
                                     "redirect_urls": redirect_urls,
                                     "transactions": [{"item_list": {"items": items},
                                                       "amount": amount,
                                                       "description": description}]},
                                    api=paypal_api)

    valid = payment.create()

    if valid:
        for link in payment.links:
            if link['method'] == "REDIRECT":
                return redirect(link["href"])
    else:
        await rockutils.send_webhook(patreon_webhook, f"`{str(payment.error)}`")
        return redirect("/donate?paymentcreateerror")


@ app.route("/donate/confirm")
@ valid_oauth_required
async def donate_confirm():

    # return redirect("/donate?disabled")

    user = session['user_data']
    userid = session['user_id']

    responce = await create_job(o="retrieveuser", a=userid, r="*")
    # userinfo = r.table("users").get(str(userid)).run(rethink)
    userinfo = await get_value(connection, "users", str(userid))

    if not userinfo:
        return redirect("/donate?userinfogone")

    try:
        payment = paypalrestsdk.Payment.find(request.args.get('paymentId'))
    except BaseException:
        return redirect("/donate?invalidpaymentid")

    name = payment.transactions[0]['item_list']['items'][0]['name']
    amount = float(payment.transactions[0]["amount"]["total"])

    if name not in prices or amount != prices.get(name):
        return redirect("/donate?invalidprice")

    dtype, months = name.split(":")
    try:
        months = int(months)
    except BaseException:
        return redirect("/donate?invalidmonth")

    if not dtype or not months:
        return redirect("/donate?invalidarg")

    donation_types = {
        "0": ["Welcomer Custom Background"],
        "1": ["Welcomer Pro x1"],
        "3": ["Welcomer Pro x3"],
        "5": ["Welcomer Pro x5"]
    }
    dname = donation_types.get(dtype, "???")

    success = payment.execute({"payer_id": request.args.get('PayerID')})
    with open("pperrs.txt", "a+") as fil:
        print(f"\n{request.args.get('PayerID')} : {success}\n")
        fil.write(f"\n{request.args.get('PayerID')} : {success}\n")

    if success:
        patreon_webhook = config['webhooks']['donations']

        message = f"""User: `{user.get('username')}` <@{userid}>\nDonation: **{dname[0]}** (£ **{amount}**)\nMonths: {months}"""
        await rockutils.send_webhook(patreon_webhook, message)

        try:
            name = payment.transactions[0]["amount"]
            if dtype == "0":
                userinfo['m']['hs'] = True
                membership_name = "Custom Background"
            if dtype == "1":
                userinfo['m']['1']['h'] = True
                userinfo['m']['1']['u'] = time.time() + \
                    (2592000 * (months))
                membership_name = "Welcomer Pro x1"
            elif dtype == "3":
                userinfo['m']['3']['h'] = True
                userinfo['m']['3']['u'] = time.time() + \
                    (2592000 * (months))
                membership_name = "Welcomer Pro x3"
            elif dtype == "5":
                userinfo['m']['5']['h'] = True
                userinfo['m']['5']['u'] = time.time() + \
                    (2592000 * (months))
                membership_name = "Welcomer Pro x5"
            else:
                membership_name = f"Donation (£{amount})"

            # r.table("users").get(str(userid)).update(userinfo).run(rethink)
            await set_value(connection, "users", str(userid), userinfo)

            receps = []
            for cluster_id, cluster_data in responce['d'].items():
                if cluster_data.get("success", False):
                    receps.append(cluster_id)

            for recep in receps:
                data = await create_job(o="donationannounce", a=[userid, membership_name], r=recep)
                if recep in data['d'] and data['d'][recep]:
                    break

            return redirect("/donate?success")
        except Exception as e:
            await rockutils.send_webhook(patreon_webhook, f":warning: | <@143090142360371200> Problem processing donation for <@{userid}>\n`{e}`")
            return redirect("/donate?fatalexception")
    else:
        return redirect("/")

##########################################################################

# @app.route("/dashboard/{}", methods=['GET', 'POST'])
# @valid_oauth_required
# @valid_dash_user
# async def dashboard_():
# guild_id = session.get("dashboard_guild", None)
# guilds = list(sorted(session.get("guild_data", []), key=lambda o: o.get("name", "")))
# guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

# if not guild_id:
#     return redirect("/dashboard")

# guild_info = await get_guild_info(guild_id)
# guild_donations = await get_guild_donations(guild_info)
# if not guild_info:
#     return redirect("/dashboard?missingdata")

# if request.method == "GET":
#     _config = {
#         "_all_translations": os.listdir("locale"),
#         "_donations": guild_donations,
#         "prefix": guild_info['d']['b']['p'],
#         "locale": guild_info['d']['b']['l'],
#         "forcedms": guild_info['d']['g']['fd'],
#         "embedcolour": guild_info['d']['b']['ec'],
#         "showstaff": guild_info['d']['b']['ss'],
#         "allowinvites": guild_info['d']['b']['ai'],
#         "splash": guild_info['d']['b']['s'] or "",
#         "description": guild_info['d']['b']['d'] or ""
#     }
# return await render_template("dashboard/botconfig.html",
# session=session, guild=guild, guilds=guilds, config=config)

# if request.method == "POST":
#     form = dict(await request.form)
#     try:
#         update_payload = {}
#         replaces = [
#             ["d.b.p", form['prefix'], False, None, "prefix"       ],
#             ["d.b.l", form['locale'], False, None, "locale"       ],
#             ["d.b.d", form['description'], False, None, "description"  ],
#             ["d.b.ec", form['embedcolour'], True, "hex", "embedcolour"  ],
#             ["d.b.ss", form['showstaff'], True, "bool", "showstaff"    ],
#             ["d.b.ai", form['allowinvites'], True, "bool", "allowinvites" ],
#             ["d.g.fd", form['forcedms'], True, "bool", "forcedms"     ],
#         ]

#         for replace in replaces:
#             if replace[2] and replace[3] and expect(replace[1], replace[3]) or not replace[2]:
#                 if not replace[1] is None:
#                     value = normalize_form(replace[1])
#                     oldvalue = rockutils.getvalue(replace[0], guild_info)
#                     rockutils.setvalue(replace[0], guild_info, value)
#                     if oldvalue != value:
#                         update_payload[replace[4]] = [oldvalue, value]

#         if len(guild_donations) > 0:
#             parsed_url = urlparse(form['splash'])
#             if "imgur.com" in parsed_url.netloc:
#                 guild_info['d']['b']['s'] = form['splash']
#                 if form['splash'] != rockutils.getvalue("d.b.s", guild_info):
#                     update_payload['splash'] = [guild_info['d']['b']['s'], form['splash']]

#         await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user_id", ""), json.dumps(update_payload)], f"{guild_id}.csv")
#         await update_guild_info(guild_id, guild_info)
#         await create_job(o="cachereload", a=guild_id, r="*")
#         return jsonify(success=True)
#         except Exception as e:
#             return jsonify(success=False, error=str(e))


@ app.route("/dashboard/botconfig", methods=["GET", "POST"])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_botconfig():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    guild_donations = await get_guild_donations(guild_info)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "_all_translations": os.listdir("locale"),
            "_donations": guild_donations,
            "prefix": guild_info['d']['b']['p'],
            "locale": guild_info['d']['b']['l'],
            "forcedms": guild_info['d']['g']['fd'],
            "embedcolour": guild_info['d']['b']['ec'],
            "showstaff": guild_info['d']['b']['ss'],
            "allowinvites": guild_info['d']['b']['ai'],
            "splash": guild_info['d']['b']['s'] or "",
            "description": guild_info['d']['b']['d'] or "",
            "showwebsite": guild_info['d']['b'].get('sw', True)
        }
        return await render_template("dashboard/botconfig.html", session=session, guild=guild, guilds=guilds, config=_config)
    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ["d.b.p", form['prefix'], False, None, "bot.prefix"],
                ["d.b.l", form['locale'], False, None, "bot.locale"],
                ["d.g.fd", form['forcedms'], True, "bool", "bot.forcedms"],
                ["d.b.ss", form['showstaff'], True, "bool", "bot.showstaff"],
                ["d.b.d", form['description'], False, None, "bot.description"],
                ["d.b.ec", form['embedcolour'], True, "hex", "bot.embedcolour"],
                ["d.b.ai", form['allowinvites'], True, "bool", "bot.allowinvites"],
                ["d.b.sw", form['showwebsite'], True, "bool", "bot.showwebsite"]
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])
            if len(guild_donations) > 0:
                parsed_url = urlparse(form['splash'])
                if "imgur.com" in parsed_url.netloc:
                    oldvalue = rockutils.getvalue("d.b.s", guild_info)
                    rockutils.setvalue("d.b.s", guild_info, form['splash'])
                    if oldvalue != form['splash']:
                        rockutils.setvalue(
                            "bot.splash", update_payload, [
                                rockutils.getvalue(
                                    "d.b.s", guild_info), form['splash']])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/guilddetails")
@ valid_oauth_required
# @valid_dash_user
async def dashboard_guilddetails():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    await create_job(o="cachereload", a=guild_id, r="*")
    guild_info = await get_guild_info(guild_id)
    guild_donations = await get_guild_donations(guild_info)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    return await render_template("dashboard/guilddetails.html", session=session, guild=guild, guilds=guilds, config=guild_info, donations=guild_donations)


@ app.route("/dashboard/invites")
@ valid_oauth_required
# @valid_dash_user
async def dashboard_invites():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    guild_donations = await get_guild_donations(guild_info)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    return await render_template("dashboard/invites.html", session=session, guild=guild, guilds=guilds, config=guild_info, donations=guild_donations)


@ app.route("/dashboard/welcomergeneral", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_welcomergeneral():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "channel": guild_info['w']['c'],
            "embed": guild_info['w']['e'],
            "badges": guild_info['w']['b'],
            "invited": guild_info['w']['iv'],
            "imagesenabled": guild_info['w']['i']['e'],
            "textenabled": guild_info['w']['t']['e'],
            "dmsenabled": guild_info['w']['dm']['e'],
            "embedenabled": guild_info['w']['ue'],
            "customembed": guild_info['w']['em'][1],
        }
        channellist = []
        for channel in sorted(
                channels['text'],
                key=lambda o: o['position']):
            channellist.append(f"{channel['name']} ({channel['id']})")
        if guild_info['w']['c']:
            _config['welcomerchannel'] = f"deleted-channel ({guild_info['w']['c']})"
            results = list(filter(lambda o, id=guild_info['w']['c']: str(
                o['id']) == str(id), channels['text']))
            if len(results) == 1:
                _config['welcomerchannel'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['welcomerchannel'] = ""

        return await render_template("dashboard/welcomergeneral.html", session=session, guild=guild, guilds=guilds, config=_config, channellist=channellist)
    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['w.b', form['badges'], True, "bool", "welcomer.badges"],
                ['w.iv', form['invited'], True, "bool", "welcomer.invited"],
                ['w.e', form['embed'], True, "bool", "welcomer.embed"],
                ['w.i.e', form['imagesenabled'], True,
                    "bool", "welcomer.imagesenabled"],
                ['w.t.e', form['textenabled'], True,
                    "bool", "welcomer.textenabled"],
                ['w.dm.e', form['dmsenabled'], True,
                    "bool", "welcomer.dmsenabled"],
                ['w.ue', form['embedenabled'], True,
                    "bool", "welcomer.embedenabled"]
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = re.findall(r".+ \(([0-9]+)\)", form['channel'])
            if len(value) == 1:
                value = value[0]
                results = list(filter(lambda o, id=value: str(
                    o['id']) == str(id), channels['text']))
                if len(results) == 1:
                    oldvalue = rockutils.getvalue("w.c", guild_info)
                    rockutils.setvalue("w.c", guild_info, value)
                    if oldvalue != value:
                        rockutils.setvalue(
                            "welcomer.channel", update_payload, [
                                oldvalue, value])
            else:
                value = None
                oldvalue = rockutils.getvalue("w.c", guild_info)
                rockutils.setvalue("w.c", guild_info, value)
                if oldvalue != value:
                    rockutils.setvalue(
                        "welcomer.channel", update_payload, [
                            oldvalue, value])

            value = form['customembed']
            loader_type = None

            try:
                yaml.load(value, Loader=yaml.SafeLoader)
                loader_type = "y"
            except BaseException:
                pass
            try:
                json.loads(value)
                loader_type = "j"
            except BaseException:
                pass

            if loader_type:
                oldvalue = rockutils.getvalue("w.em", guild_info)[1]
                rockutils.setvalue("w.em", guild_info, [loader_type, value])
                if oldvalue != value:
                    rockutils.setvalue(
                        "welcomer.customembed", update_payload, None)

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/welcomerimages", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_welcomerimages():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    guild_donations = await get_guild_donations(guild_info)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    # welcomer channel
    # welcomer badges
    # welcomer invited

    # welcomer images enable
    # welcomer text enabled
    # welcomer dm enabled

    if request.method == "GET":
        if isinstance(guild_info['w']['i']['m'], list):
            guild_info['w']['i']['m'] = "\n".join(guild_info['w']['i']['m'])

        _config = {
            "donations": guild_donations,
            "enableimages": guild_info['w']['i']['e'],
            "textcolour": guild_info['w']['i']['c']['b'],
            "textbordercolour": guild_info['w']['i']['c']['bo'],
            "profileoutlinecolour": guild_info['w']['i']['c']['pb'],
            "imagebordercolour": guild_info['w']['i']['c']['ib'],
            "enableimageborder": guild_info['w']['i']['b'],
            "textalign": guild_info['w']['i']['a'],
            "texttheme": guild_info['w']['i']['t'],
            "profilebordertype": guild_info['w']['i']['pb'],
            "message": guild_info['w']['i']['m'],
            "background": guild_info['w']['i']['bg'],
        }

        keys = ['textcolour', 'textbordercolour',
                'profileoutlinecolour', 'imagebordercolour']
        for key in keys:
            if key in _config:
                _config[key] = normalize_colour(_config[key])

        backgrounds = list(map(lambda o: pathlib.Path(o).stem, os.listdir(
            os.path.join(config['cdn']['location'], "Images"))))
        return await render_template("dashboard/welcomerimages.html", session=session, guild=guild, guilds=guilds, config=_config, backgrounds=backgrounds)
    if request.method == "POST":
        files = await request.files
        _file = files.get('file', None)
        form = dict(await request.form)
        try:
            update_payload = {}

            _allow_bg = False
            if len(guild_donations) > 0:
                _allow_bg = True

                # if "cbg" in guild_donations:
                #     _allow_bg = True
                # if "donation" in guild_donations:
                #     _allow_bg = True
                # _allow_hq = True
                # if "donation" in guild_donations:
                #     _allow_gif = True

            if _file and _allow_bg:
                location = os.path.join(
                    config['cdn']['location'],
                    "CustomImages",
                    f"custom_{guild['id']}")
                isgif = imghdr.what(_file.filename, h=_file.read()) in [
                    "gif"]
                _file.seek(0)

                if os.path.exists(location + ".gif"):
                    os.remove(location + ".gif")

                if os.path.exists(location + ".png"):
                    os.remove(location + ".png")

                if os.path.exists(location + ".jpg"):
                    os.remove(location + ".jpg")

                if isgif:
                    location += ".gif"
                    _file.save(location)
                    # image.save(location, "gif")
                else:
                    location += ".png"
                    image = Image.open(_file)
                    image.save(location, "png")

                # else:
                #     location += ".jpg"
                #     image = image.convert("RGB")
                #     image.save(location, "jpeg", quality=30,
                #                 optimize=True, progressive=True)

                form['background'] = f"custom_{guild['id']}"

            replaces = [
                # ['w.b', form['badges'], True, "bool", "badges"],
                ['w.i.e', form['enableimages'],
                    True, "bool", "welcomer.imagesenabled"],
                ['w.i.b', form['enableimageborder'], True,
                    "bool", "welcomerimg.enableimageborder"],
                ['w.i.a', form['textalign'],
                    False, None, "welcomerimg.textalign"],
                ['w.i.t', form['texttheme'], True,
                    "int", "welcomerimg.texttheme"],
                ['w.i.pb', form['profilebordertype'], True,
                    "int", "welcomerimg.profilebordertype"],
                ['w.i.m', form['message'],
                    False, None, "welcomerimg.message"],
                ['w.i.bg', form['background'],
                    False, None, "welcomerimg.background"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            replaces = [
                ['w.i.c.b', form['textcolour'], True,
                    "hex", "welcomerimg.textcolour"],
                ['w.i.c.bo', form['textbordercolour'], True,
                    "hex", "welcomerimg.textbordercolour"],
                ['w.i.c.pb', form['profileoutlinecolour'], True,
                    "hex", "welcomerimg.profileoutlinecolour"],
                ['w.i.c.ib', form['imagebordercolour'], True,
                    "hex", "welcomerimg.imagebordercolour"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = None
                        if "rgba" in replace[1]:
                            matches = re.findall(
                                r"rgba\((\d+),(\d+),(\d+),([\d\.?]+)\)", replace[1])
                            if len(matches) > 0:
                                rgba = matches[0]
                                _hex = ""
                                _hex += f"{str(hex(rgba[0]))[2:]}"
                                _hex += f"{str(hex(rgba[1]))[2:]}"
                                _hex += f"{str(hex(rgba[2]))[2:]}"
                                _hex += f"{str(hex(rgba[3]))[2:]}"
                                value = f"RGBA|{_hex}"
                        elif replace[1] == "transparent":
                            value = f"transparent"
                        else:
                            rgb = replace[1].replace("#", "")
                            try:
                                int(rgb, 16)
                                isrgb = True
                            except BaseException:
                                isrgb = False

                            if isrgb:
                                value = f"RGB|{rgb[:6]}"

                        if value:
                            oldvalue = rockutils.getvalue(
                                replace[0], guild_info)
                            rockutils.setvalue(replace[0], guild_info, value)
                            if oldvalue != value:
                                rockutils.setvalue(
                                    replace[4], update_payload, [oldvalue, value])

            keys = ['w.i.c.b', 'w.i.c.b', 'w.i.c.pb', 'w.i.c.ib']
            for key in keys:
                value = rockutils.getvalue(key, guild_info)
                newvalue = normalize_colour(value)
                rockutils.setvalue(key, guild_info, newvalue)

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/welcomertext", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_welcomertext():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "badges": guild_info['w']['b'],
            "invited": guild_info['w']['iv'],
            "textenabled": guild_info['w']['t']['e'],
            "embedenabled": guild_info['w']['ue'],
            "customembed": guild_info['w']['em'][1],
            "message": guild_info['w']['t']['m'],
        }
        channellist = []
        for channel in sorted(
                channels['text'],
                key=lambda o: o['position']):
            channellist.append(f"{channel['name']} ({channel['id']})")
        if guild_info['w']['c']:
            _config['welcomerchannel'] = f"deleted-channel ({guild_info['w']['c']})"
            results = list(filter(lambda o, id=guild_info['w']['c']: str(
                o['id']) == str(id), channels['text']))
            if len(results) == 1:
                _config['welcomerchannel'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['welcomerchannel'] = ""

        return await render_template("dashboard/welcomertext.html", session=session, guild=guild, guilds=guilds, config=_config, channellist=channellist)
    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['w.b', form['badges'], True,
                    "bool", "welcomer.badges"],
                ['w.iv', form['invited'], True,
                    "bool", "welcomer.invited"],
                ['w.t.e', form['textenabled'], True,
                    "bool", "welcomer.textenabled"],
                ['w.ue', form['embedenabled'], True,
                    "bool", "welcomer.embedenabled"],
                ['w.t.m', form['message'], False,
                    None, "welcomer.message"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = form['customembed']
            loader_type = None

            try:
                yaml.load(value, Loader=yaml.SafeLoader)
                loader_type = "y"
            except BaseException:
                pass
            try:
                json.loads(value)
                loader_type = "j"
            except BaseException:
                pass

            if loader_type:
                oldvalue = rockutils.getvalue("w.em", guild_info)[1]
                rockutils.setvalue("w.em", guild_info, [loader_type, value])
                if oldvalue != value:
                    rockutils.setvalue(
                        "welcomer.customembed", update_payload, None)

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/welcomerdms", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_welcomerdms():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "dmsenabled": guild_info['w']['dm']['e'],
            "embedenabled": guild_info['w']['dm']['ue'],
            "customembed": guild_info['w']['dm']['em'][1],
            "message": guild_info['w']['dm']['m'],
        }
        channellist = []
        for channel in sorted(
                channels['text'],
                key=lambda o: o['position']):
            channellist.append(f"{channel['name']} ({channel['id']})")
        if guild_info['w']['c']:
            _config['welcomerchannel'] = f"deleted-channel ({guild_info['w']['c']})"
            results = list(filter(lambda o, id=guild_info['w']['c']: str(
                o['id']) == str(id), channels['text']))
            if len(results) == 1:
                _config['welcomerchannel'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['welcomerchannel'] = ""

        return await render_template("dashboard/welcomerdms.html", session=session, guild=guild, guilds=guilds, config=_config, channellist=channellist)
    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['w.dm.e', form['dmenabled'], True,
                    "bool", "welcomerdms.enabled"],
                ['w.dm.ue', form['embedenabled'], True,
                    "bool", "welcomerdms.embedenabled"],
                ['w.dm.m', form['message'], False,
                    None, "welcomerdms.message"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = form['customembed']
            loader_type = None

            try:
                yaml.load(value, Loader=yaml.SafeLoader)
                loader_type = "y"
            except BaseException:
                pass
            try:
                json.loads(value)
                loader_type = "j"
            except BaseException:
                pass

            if loader_type:
                oldvalue = rockutils.getvalue("w.dm.em", guild_info)[1]
                rockutils.setvalue("w.dm.em", guild_info, [loader_type, value])
                if oldvalue != value:
                    rockutils.setvalue(
                        "welcomerdms.customembed", update_payload, None)

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/punishments", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_punishments():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "forcereason": guild_info['m']['fr'],
            "logmoderation": guild_info['lo']['m']
        }

        hasfile = os.path.exists(f"punishments/{guild_id}.csv")

        return await render_template("dashboard/punishmentmanage.html", session=session, guild=guild, guilds=guilds, config=_config, has_file=hasfile)
    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['m.fr', form['forcereason'], True,
                    "bool", "moderation.forcereason"],
                ['lo.m', form['logmoderation'], True,
                    "bool", "logging.logmoderation"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/punishments/<ptype>")
@ valid_oauth_required
# @valid_dash_user
async def dashboard_punishments_view(ptype="recent"):
    res = await is_valid_dash_user()
    if res != True:
        return res

    if ptype not in ['recent', 'active']:
        ptype = "recent"

    if ptype == "active":
        isactive = True
        ptype = "true"
    else:
        isactive = False
        ptype = "false"

    ptype = f"/api/punishments/{ptype}"

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    guild_donations = await get_guild_donations(guild_info)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    return await render_template("dashboard/punishmentview.html", session=session, guild=guild, guilds=guilds, config=guild_info, donations=guild_donations, ptype=ptype, isactive=isactive)


@ app.route("/dashboard/timerole", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_timerole():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    roles = await get_guild_roles(guild_id)
    setroles = {}

    for role in roles:
        role['enabled'] = False
        role['seconds'] = ""
        setroles[role['id']] = role

    for role in guild_info['tr']['r']:
        if role[0] in setroles:
            setroles[role[0]]['enabled'] = True
            setroles[role[0]]['seconds'] = str(role[1])

    for id, value in setroles.items():
        try:
            setroles[id]['seconds'] = math.floor(
                int(setroles[id]['seconds']) / 60)
        except BaseException:
            pass

    if guild_id in setroles:
        del setroles[str(guild_id)]

    if request.method == "GET":
        _config = {
            "enabled": guild_info['tr']['e'],
            "roles": setroles,
        }

        return await render_template("dashboard/timerole.html", session=session, guild=guild, guilds=guilds, config=_config, roles=roles)
    if request.method == "POST":
        form = json.loads(list(await request.form)[0])
        try:
            update_payload = {}
            replaces = [
                ['tr.e', form['enabled'], True, "bool", "timerole.enable"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            timeroles = []
            for id, role in form['roles'].items():
                if role[0]:
                    try:
                        seconds = int(math.floor(float(role[1])) * 60)
                        if seconds > 0:
                            timeroles.append([str(id), str(seconds)])
                    except BaseException:
                        pass

            oldvalue = rockutils.getvalue("tr.r", guild_info)
            rockutils.setvalue("tr.r", guild_info, timeroles)
            if timeroles != oldvalue:

                # log added roles
                # log removed roles
                # log edited roles
                rockutils.setvalue("freerole.roles", update_payload, "")

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/autorole", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_autorole():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    roles = await get_guild_roles(guild_id)
    setroles = {}

    for role in roles:
        role['enabled'] = False
        setroles[role['id']] = role

    for role in guild_info['ar']['r']:
        if role in setroles:
            setroles[role]['enabled'] = True

    if guild_id in setroles:
        del setroles[str(guild_id)]

    if request.method == "GET":
        _config = {
            "enabled": guild_info['ar']['e'],
            "roles": setroles
        }

        return await render_template("dashboard/autorole.html", session=session, guild=guild, guilds=guilds, config=_config, roles=roles)
    if request.method == "POST":
        form = json.loads(list(await request.form)[0])
        try:
            update_payload = {}
            replaces = [
                ['ar.e', form['enabled'], True, "bool", "autorole.enable"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            autorole = []
            for id, role in form['roles'].items():
                if role:
                    autorole.append(id)

            oldvalue = rockutils.getvalue("ar.r", guild_info)
            rockutils.setvalue("ar.r", guild_info, autorole)
            if autorole != oldvalue:

                # log added roles
                # log removed roles
                # log edited roles
                rockutils.setvalue("autorole.roles", update_payload, "")

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/freerole", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_freerole():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    roles = await get_guild_roles(guild_id)
    setroles = {}

    for role in roles:
        role['enabled'] = False
        setroles[role['id']] = role

    for role in guild_info['fr']['r']:
        if role[0] in setroles:
            setroles[role[0]]['enabled'] = True

    if guild_id in setroles:
        del setroles[str(guild_id)]

    if request.method == "GET":
        _config = {
            "enabled": guild_info['fr']['e'],
            "roles": setroles
        }

        return await render_template("dashboard/freerole.html", session=session, guild=guild, guilds=guilds, config=_config, roles=roles)
    if request.method == "POST":
        form = json.loads(list(await request.form)[0])
        try:
            update_payload = {}
            replaces = [
                ['fr.e', form['enabled'], True, "bool", "freerole.enable"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            freerole = []
            for id, role in form['roles'].items():
                if role:
                    freerole.append(id)

            oldvalue = rockutils.getvalue("fr.r", guild_info)
            rockutils.setvalue("fr.r", guild_info, freerole)
            if freerole != oldvalue:

                # log added roles
                # log removed roles
                # log edited roles
                rockutils.setvalue("freerole.roles", update_payload, "")

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/logs", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_logs():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "enabled": guild_info['lo']['e'],
            "audit": guild_info['lo']['a'],
            "moderation": guild_info['lo']['m'],
            "joinleaves": guild_info['lo']['jl'],
        }

        hasfile = os.path.exists(f"logs/{guild_id}.csv")

        return await render_template("dashboard/logs.html", session=session, guild=guild, guilds=guilds, config=_config, has_file=hasfile)
    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['lo.e', form['enabled'], True, "bool", "logging.enabled"],
                ['lo.a', form['audit'], True, "bool", "logging.audit"],
                ['lo.m', form['moderation'], True, "bool", "logging.moderation"],
                ['lo.jl', form['joinleaves'], True, "bool", "logging.joinleaves"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if replace[1]:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv(
                    [
                        math.floor(time.time()),
                        'CONFIG_CHANGE',
                        int(session.get("user_id", 0)),
                        session.get("user", ""),
                        json.dumps(update_payload)
                    ],
                    f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/leaver", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_leaver():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "enabled": guild_info['l']['e'],
            "message": guild_info['l']['t'],
            "embed": guild_info['l']['em'],
        }
        channellist = []
        for channel in sorted(
                channels['text'],
                key=lambda o: o['position']):
            channellist.append(f"{channel['name']} ({channel['id']})")
        if guild_info['l']['c']:
            _config['channel'] = f"deleted-channel ({guild_info['l']['c']})"
            results = list(filter(lambda o, id=guild_info['l']['c']: str(
                o['id']) == str(id), channels['text']))
            if len(results) == 1:
                _config['channel'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['channel'] = ""

        return await render_template("dashboard/leaver.html", session=session, guild=guild, guilds=guilds, config=_config, channellist=channellist)
    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['l.e', form['enabled'], True, "bool", "leaver.enabled"],
                ['l.t', form['message'], False, None, "leaver.text"],
                ['l.em', form['embed'], True, "bool", "leaver.embed"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = re.findall(r".+ \(([0-9]+)\)", form['channel'])
            if len(value) == 1:
                value = value[0]
                results = list(filter(lambda o, id=value: str(
                    o['id']) == str(id), channels['text']))
                if len(results) == 1:
                    oldvalue = rockutils.getvalue("l.c", guild_info)
                    rockutils.setvalue("l.c", guild_info, value)
                    if oldvalue != value:
                        rockutils.setvalue(
                            "leaver.channel", update_payload, [
                                oldvalue, value])
            else:
                value = None
                oldvalue = rockutils.getvalue("l.c", guild_info)
                rockutils.setvalue("l.c", guild_info, value)
                if oldvalue != value:
                    rockutils.setvalue(
                        "leaver.channel", update_payload, [
                            oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/staff", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_staff():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "allowping": guild_info['st']['ap'],
        }

        ids = [v[0] for v in guild_info['st']['u']]
        _config['staffids'] = ",".join(ids)

        result_payload = await create_job(request=None, o="guildstaff", a=int(guild_id), r="*", timeout=2)
        staff = []
        for data in result_payload['d'].values():
            if data['success']:
                stafflist = data['data']
                staff = []
                for _staff in stafflist:
                    _staff['preferdms'] = True
                    for userid, preferdms in guild_info['st']['u']:
                        if str(userid) == str(_staff['id']):
                            _staff['preferdms'] = preferdms
                    staff.append(_staff)

        return await render_template("dashboard/staff.html", session=session, guild=guild, guilds=guilds, config=_config, staff=staff)
    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['st.ap', form['allowping'], True, "bool", "staff.allowping"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            ids = form['staffids'].split(",")
            staffids = [str(v[0]) for v in guild_info['st']['u']]

            added, removed = [], []

            for id in ids:
                if id not in staffids:
                    added.append(id)
            for id in staffids:
                if id not in ids:
                    removed.append(id)

            stafflist = {}
            for staff_id in ids:
                stafflist[staff_id] = True
            for staff_id, prefer_ping in guild_info['st']['u']:
                if staff_id in ids:
                    stafflist[str(staff_id)] = prefer_ping

            staff_list = []
            for staff_id, prefer_ping in stafflist.items():
                staff_list.append([
                    staff_id, prefer_ping
                ])

            if len(added) + len(removed) > 0:
                rockutils.setvalue("st.u", guild_info, staff_list)
                rockutils.setvalue(
                    "staff.staff", update_payload, [
                        added, removed])
            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/rules", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_rules():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "enabled": guild_info['r']['e'],
            "rules": "\n".join(guild_info['r']['r']),
        }

        return await render_template("dashboard/rules.html", session=session, guild=guild, guilds=guilds, config=_config)
    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['r.e', form['enabled'], True, "bool", "rules.enabled"],
                ['r.r', form['rules'].split("\n"), False, None, "rules.rules"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/automod", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_automod():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "enabled": guild_info['am']['e'],
            "smartmod": guild_info['am']['sm'],
            "automodfiltinvites": guild_info['am']['g']['i'],
            "automodfilturlredir": guild_info['am']['g']['ur'],
            "automodfilturls": guild_info['am']['g']['ul'],
            "automodfiltipgrab": guild_info['am']['g']['ig'],
            "automodfiltmasscap": guild_info['am']['g']['mc'],
            "automodfiltmassmen": guild_info['am']['g']['mm'],
            "automodfiltprofan": guild_info['am']['g']['p'],
            "automodfiltfilter": guild_info['am']['g']['f'],
            "thresholdmention": guild_info['am']['t']['m'],
            "thresholdcaps": guild_info['am']['t']['c'],
            "filter": "\n".join(guild_info['am']['f']),
            "regex": "\n".join(guild_info['am']['r']),
        }

        return await render_template("dashboard/automod.html", session=session, guild=guild, guilds=guilds, config=_config)
    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['am.e', form['enabled'], True, "bool", "automod.enabled"],
                ['am.sm', form['smartmod'], True, "bool", "automod.smartmod"],
                ['am.g.i', form['automodfiltinvites'], True,
                    "bool", "automod.automodfiltinvites"],
                ['am.g.ur', form['automodfilturlredir'], True,
                    "bool", "automod.automodfilturlredir"],
                ['am.g.ul', form['automodfilturls'], True,
                    "bool", "automod.automodfilturls"],
                ['am.g.ig', form['automodfiltipgrab'], True,
                    "bool", "automod.automodfiltipgrab"],
                ['am.g.mc', form['automodfiltmasscap'], True,
                    "bool", "automod.automodfiltmasscap"],
                ['am.g.mm', form['automodfiltmassmen'], True,
                    "bool", "automod.automodfiltmassmen"],
                ['am.g.p', form['automodfiltprofan'], True,
                    "bool", "automod.automodfiltprofan"],
                ['am.g.f', form['automodfiltfilter'], True,
                    "bool", "automod.automodfiltfilter"],
                ['am.t.m', form['thresholdmention'], True,
                    "int", "automod.thresholdmention"],
                ['am.t.c', form['thresholdcaps'], True,
                    "int", "automod.thresholdcaps"],
                ['am.f', form['filter'].split(
                    "\n"), False, None, "automod.filter"],
                ['am.r', form['regex'].split(
                    "\n"), False, None, "automod.regex"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/borderwall", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_borderwall():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    roles = await get_guild_roles(guild_id)
    setroles = {}

    for role in roles:
        role['enabled'] = False
        setroles[role['id']] = role

    _roles = guild_info['bw']['r']
    if not isinstance(_roles, list):
        _roles = [_roles]

    for role in _roles:
        if role in setroles:
            setroles[role]['enabled'] = True

    if guild_id in setroles:
        del setroles[str(guild_id)]

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "channel": guild_info['bw']['c'],
            "enabled": guild_info['bw']['e'],
            "senddms": guild_info['bw']['d'],
            "waittime": guild_info['bw']['w'],
            "message": guild_info['bw']['m'],
            "messageverify": guild_info['bw']['mv'],
            "roles": setroles
        }

        channellist = []
        for channel in sorted(
                channels['text'],
                key=lambda o: o['position']):
            channellist.append(f"{channel['name']} ({channel['id']})")
        if guild_info['bw']['c']:
            _config['channel'] = f"deleted-channel ({guild_info['bw']['c']})"
            results = list(filter(lambda o, id=guild_info['bw']['c']: str(
                o['id']) == str(id), channels['text']))
            if len(results) == 1:
                _config['channel'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['channel'] = ""

        return await render_template("dashboard/borderwall.html", session=session, guild=guild, guilds=guilds, config=_config, channellist=channellist, roles=roles)
    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        form = json.loads(list(await request.form)[0])
        try:
            update_payload = {}
            replaces = [
                ['bw.e', form['enabled'], True, "bool", "borderwall.enabled"],
                ['bw.d', form['senddms'], True, "bool", "borderwall.senddms"],
                # ['bw.w', form['waittime'], True, "int", "borderwall.waittime"],
                ['bw.m', form['message'], False, None, "borderwall.message"],
                ['bw.mv', form['messageverify'], False,
                    None, "borderwall.messageverify"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = re.findall(r".+ \(([0-9]+)\)", form['channel'])
            if len(value) == 1:
                value = value[0]
                results = list(filter(lambda o, id=value: str(
                    o['id']) == str(id), channels['text']))
                if len(results) == 1:
                    oldvalue = rockutils.getvalue("bw.c", guild_info)
                    rockutils.setvalue("bw.c", guild_info, value)
                    if oldvalue != value:
                        rockutils.setvalue(
                            "borderwall.channel", update_payload, [
                                oldvalue, value])
            else:
                value = None
                oldvalue = rockutils.getvalue("bw.c", guild_info)
                rockutils.setvalue("bw.c", guild_info, value)
                if oldvalue != value:
                    rockutils.setvalue(
                        "borderwall.channel", update_payload, [
                            oldvalue, value])

            bwroles = []
            for id, role in form['roles'].items():
                if role:
                    bwroles.append(str(id))

            oldvalue = rockutils.getvalue("bw.r", guild_info)
            rockutils.setvalue("bw.r", guild_info, bwroles)
            if bwroles != oldvalue:

                # log added roles
                # log removed roles
                # log edited roles
                rockutils.setvalue("borderwall.roles", update_payload, "")

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/tempchannel", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_tempchannel():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "enabled": guild_info['tc']['e'],
            "category": guild_info['tc']['c'],
            "lobby": guild_info['tc']['l'],
            "defaultlimit": guild_info['tc']['dl'],
            "autopurge": guild_info['tc']['ap']
        }

        categorylist = []
        for channel in sorted(
                channels['categories'],
                key=lambda o: o['position']):
            categorylist.append(f"{channel['name']} ({channel['id']})")

        channellist = []
        for channel in sorted(
                channels['voice'],
                key=lambda o: o['position']):
            channellist.append(f"{channel['name']} ({channel['id']})")

        if guild_info['tc']['c']:
            _config['category'] = f"deleted-category ({guild_info['tc']['c']})"
            results = list(filter(lambda o, id=guild_info['tc']['c']: str(
                o['id']) == str(id), channels['categories']))
            if len(results) == 1:
                _config['category'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['category'] = ""

        if guild_info['tc']['l']:
            _config['lobby'] = f"deleted-channel ({guild_info['tc']['l']})"
            results = list(filter(lambda o, id=guild_info['tc']['l']: str(
                o['id']) == str(id), channels['voice']))
            if len(results) == 1:
                _config['lobby'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['lobby'] = ""

        return await render_template("dashboard/tempchannel.html", session=session, guild=guild, guilds=guilds, config=_config, channellist=channellist, categorylist=categorylist)
    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        # form = json.loads(list(await request.form)[0])
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['tc.e', form['enabled'], True, "bool", "tempchannel.enabled"],
                ['tc.ap', form['autopurge'], False, None, "tempchannel.autopurge"],
                ['tc.dl', form['defaultlimit'], True,
                    "int", "tempchannel.defaultlimit"]
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = re.findall(r".+ \(([0-9]+)\)", form['category'])
            if len(value) == 1:
                value = value[0]
                results = list(filter(lambda o, id=value: str(
                    o['id']) == str(id), channels['categories']))
                if len(results) == 1:
                    oldvalue = rockutils.getvalue("tc.c", guild_info)
                    rockutils.setvalue("tc.c", guild_info, value)
                    if oldvalue != value:
                        rockutils.setvalue(
                            "tempchannel.category", update_payload, [
                                oldvalue, value])
            else:
                value = None
                oldvalue = rockutils.getvalue("tc.c", guild_info)
                rockutils.setvalue("tc.c", guild_info, value)
                if oldvalue != value:
                    rockutils.setvalue(
                        "tempchannel.category", update_payload, [
                            oldvalue, value])

            value = re.findall(r".+ \(([0-9]+)\)", form['lobby'])
            if len(value) == 1:
                value = value[0]
                results = list(filter(lambda o, id=value: str(
                    o['id']) == str(id), channels['voice']))
                if len(results) == 1:
                    oldvalue = rockutils.getvalue("tc.l", guild_info)
                    rockutils.setvalue("tc.l", guild_info, value)
                    if oldvalue != value:
                        rockutils.setvalue(
                            "tempchannel.lobby", update_payload, [
                                oldvalue, value])
            else:
                value = None
                oldvalue = rockutils.getvalue("tc.l", guild_info)
                rockutils.setvalue("tc.l", guild_info, value)
                if oldvalue != value:
                    rockutils.setvalue(
                        "tempchannel.lobby", update_payload, [
                            oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


# @app.route("/dashboard/namepurge", methods=['GET', 'POST'])
# @valid_oauth_required
# # @valid_dash_user
# async def dashboard_namepurge():
#     res = await is_valid_dash_user()
#     if res != True:
#         return res

#     guild_id = session.get("dashboard_guild", None)
#     guilds = list(sorted(session.get("guild_data", []),
#                          key=lambda o: o.get("name", "")))
#     guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

#     if not guild_id:
#         return redirect("/dashboard")

#     guild_info = await get_guild_info(guild_id)
#     if not guild_info:
#         return redirect("/dashboard?missingdata")

#     if request.method == "GET":
#         _config = {
#             "enabled": guild_info['np']['e'],
#             "ignore": guild_info['np']['i'],
#             "filter": "\n".join(guild_info['np']['f']),
#         }

#         return await render_template("dashboard/namepurge.html", session=session, guild=guild, guilds=guilds, config=_config)
#     if request.method == "POST":
#         form = dict(await request.form)
#         try:
#             update_payload = {}
#             replaces = [
#                 ['np.e', form['enabled'], True, "bool", "namepurge.enabled"],
#                 ['np.i', form['ignore'], True, "bool", "namepurge.ignorebot"],
#                 ['np.f', form['filter'].split(
#                     "\n"), False, None, "namepurge.filter"]
#             ]

#             for replace in replaces:
#                 if replace[2] and replace[3] and expect(
#                         replace[1], replace[3]) or not replace[2]:
#                     if not replace[1] is None:
#                         value = normalize_form(replace[1])
#                         oldvalue = rockutils.getvalue(replace[0], guild_info)
#                         rockutils.setvalue(replace[0], guild_info, value)
#                         if oldvalue != value:
#                             rockutils.setvalue(
#                                 replace[4], update_payload, [oldvalue, value])

#             if len(update_payload) > 0:
#                 await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
#                 await update_guild_info(guild_id, guild_info)
#                 await create_job(o="cachereload", a=guild_id, r="*")
#             return jsonify(success=True)
#         except Exception as e:
#             exc_info = sys.exc_info()
#             traceback.print_exception(*exc_info)
#             return jsonify(success=False, error=str(e))


@ app.route("/dashboard/music", methods=['GET', 'POST'])
@ valid_oauth_required
# @valid_dash_user
async def dashboard_music():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        _config = {
            "djsenabled": guild_info['mu']['d']['e'],
            "djs": ",".join(guild_info['mu']['d']['l']),
            "skiptype": guild_info['mu']['st'],
            "threshold": guild_info['mu']['t'],
        }

        return await render_template("dashboard/music.html", session=session, guild=guild, guilds=guilds, config=_config)

    if request.method == "POST":
        form = dict(await request.form)
        try:
            update_payload = {}
            replaces = [
                ['mu.d.e', form['djsenabled'], True, "bool", "music.djsenabled"],
                ['mu.st', form['skiptype'], True, "int", "music.skiptype"],
                ['mu.t', form['threshold'], True, "int", "music.threshold"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            ids = form['djs'].split(",")
            djids = guild_info['mu']['d']['l']

            added, removed = [], []

            for id in ids:
                if id not in djids:
                    added.append(id)
            for id in djids:
                if id not in ids:
                    removed.append(id)

            if len(added) + len(removed) > 0:
                rockutils.setvalue("mu.d.l", guild_info, ids)
                rockutils.setvalue(
                    "music.djslist", update_payload, [
                        added, removed])
            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))


@ app.route("/dashboard/serverstats/list")
@ valid_oauth_required
# @valid_dash_user
async def dashboard_serverstats_list():
    res = await is_valid_dash_user()
    if res != True:
        return res

    try:
        guild_id = session.get("dashboard_guild", None)
        guilds = list(sorted(session.get("guild_data", []),
                             key=lambda o: o.get("name", "")))

        if not guild_id:
            return redirect("/dashboard")

        guild_info = await get_guild_info(guild_id)
        if not guild_info:
            return redirect("/dashboard?missingdata")

        return jsonify({"success": True, "config": guild_info['s']['c']})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@ app.route("/dashboard/serverstats", methods=['GET', 'POST'])
@ valid_oauth_required
async def dashboard_serverstats():
    res = await is_valid_dash_user()
    if res != True:
        return res

    guild_id = session.get("dashboard_guild", None)
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild = list(filter(lambda o, id=guild_id: o['id'] == guild_id, guilds))[0]

    if not guild_id:
        return redirect("/dashboard")

    guild_info = await get_guild_info(guild_id)
    if not guild_info:
        return redirect("/dashboard?missingdata")

    if request.method == "GET":
        channels = await get_guild_channels(guild_id)
        _config = {
            "enabled": guild_info['s']['e'],
            "category": guild_info['s']['ca'],
            "channels": channels['categories'],
        }

        categorylist = []
        for channel in sorted(
                _config['channels'],
                key=lambda o: o['position']):
            categorylist.append(f"{channel['name']} ({channel['id']})")

        if guild_info['s']['ca']:
            _config['category'] = f"deleted-category ({guild_info['s']['ca']})"
            results = list(filter(lambda o, id=guild_info['s']['ca']: str(
                o['id']) == str(id), channels['categories']))
            if len(results) == 1:
                _config['category'] = f"{results[0]['name']} ({results[0]['id']})"
        else:
            _config['category'] = ""

        return await render_template("dashboard/serverstats.html", session=session, guild=guild, guilds=guilds, config=_config, categorylist=categorylist)

    if request.method == "POST":
        channels = await get_guild_channels(guild_id)
        form = json.loads(list(await request.form)[0])
        try:
            update_payload = {}
            replaces = [
                ['s.e', form['enabled'], True, "bool", "serverstats.enabled"],
            ]

            for replace in replaces:
                if replace[2] and replace[3] and expect(
                        replace[1], replace[3]) or not replace[2]:
                    if not replace[1] is None:
                        value = normalize_form(replace[1])
                        oldvalue = rockutils.getvalue(replace[0], guild_info)
                        rockutils.setvalue(replace[0], guild_info, value)
                        if oldvalue != value:
                            rockutils.setvalue(
                                replace[4], update_payload, [oldvalue, value])

            value = re.findall(r".+ \(([0-9]+)\)", form['category'])
            if len(value) == 1:
                value = value[0]
                results = list(filter(lambda o, id=value: str(
                    o['id']) == str(id), channels['categories']))
                if len(results) == 1:
                    oldvalue = rockutils.getvalue("s.ca", guild_info)
                    rockutils.setvalue("s.ca", guild_info, value)
                    if oldvalue != value:
                        rockutils.setvalue(
                            "serverstats.category", update_payload, [
                                oldvalue, value])
            else:
                value = None
                oldvalue = rockutils.getvalue("s.ca", guild_info)
                rockutils.setvalue("s.ca", guild_info, value)
                if oldvalue != value:
                    rockutils.setvalue(
                        "serverstats.category", update_payload, [
                            oldvalue, value])

            if len(update_payload) > 0:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', int(session.get("user_id", 0)), session.get("user", ""), json.dumps(update_payload)], f"{guild_id}.csv")
                await update_guild_info(guild_id, guild_info)
                await create_job(o="cachereload", a=guild_id, r="*")
            return jsonify(success=True)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            return jsonify(success=False, error=str(e))

# /dashboard/serverstats
# configured stats

# /dashboard/analytics
# enabled
# analytics listing
#    change by (5 minute, 30 minute, 1 hour, 6 hour, 12 hour, 1 day, 1 week, 1 month)
#    members joined
#    members left
#    member count
#    messages sent
#    bot count
#    user count
# reset
# export


# ????
    # /dashboard/xp
    # enabled
    # reset

    # (? may have xprole on the xp page or have it as a tab and have Manage and XPRole)
    # /dashboard/xprole
    # enabled
    # roles (toggle then xp minimum)
    #       (? maybe a list saying how many users will have it)

# /formatting
# /customembeds
# /dashboard/logs/view


# /dashboard/api/xp/leaderboard
# /dashboard/api/xp/resetuser/<user id>
# /dashboard/api/xp/export
# /dashboard/api/xp/reset

# /profile
# /invite/<name>
# /guild/<id>

##########################################################################


async def post_no_wait(url, *args, **kwargs):
    timeout = aiohttp.ClientTimeout(total=1)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            await session.post(
                url,
                *args,
                **kwargs
            )
            await session.close()
    except Exception as e:
        print(e)
        pass


@ app.route("/")
async def index():
    guilds = sum(v.get('guilds', 0) for v in cluster_data.values())
    members = sum(v.get('totalmembers', 0) for v in cluster_data.values())
    _time = time.time()
    global _lastpost
    if _time - _lastpost >= 240:
        tasks = [
            post_no_wait(
                "https://bots.ondiscord.xyz/bot-api/bots/330416853971107840/guilds",
                headers={
                    "Authorization": "[removed]",
                },
                data={
                    "guildCount": guilds
                }),
            post_no_wait(
                "https://api.discordextremelist.xyz/v1/bot/330416853971107840",
                headers={
                    "Authorization": "[removed]"},
                data={
                    "guildCount": guilds,
                }),
            post_no_wait(
                "https://discordbots.org/api/bots/330416853971107840/stats",
                headers={
                    "Authorization": "[removed]"},
                data={
                    "server_count": guilds,
                    "shard_count": 50,
                }),
            post_no_wait(
                "https://discord.boats/api/v2/bot/330416853971107840",
                headers={
                    "Authorization": "[removed]",
                },
                data={
                    "server_count": guilds
                }),
            post_no_wait(
                "https://botsfordiscord.com/api/bot/330416853971107840",
                headers={
                    "Authorization": "[removed]"
                },
                data={
                    "server_count": guilds
                }),
            post_no_wait(
                "https://discordsbestbots.xyz/api/bots/330416853971107840/stats",
                headers={
                    "Authorization": "[removed]"
                },
                data={
                    "guilds": guilds
                })
        ]
        await asyncio.gather(*tasks)
        _lastpost = _time

    cdnpath = os.path.join(config['cdn']['location'], "Output")
    total_images = len(os.listdir(cdnpath))
    return await render_template("index.html", session=session, guild_count=guilds, member_count=members, stored_images=total_images)


@ app.route("/command-documentation")
async def command_documentation():
    try:
        with open("cfg/command-documentation.yaml", 'r') as stream:
            data_loaded = yaml.load(stream, Loader=yaml.BaseLoader)
            loaded = True
    except BaseException:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        data_loaded = {}
        loaded = False

    return await render_template("command-documentation.html", session=session, loaded=loaded, docs=data_loaded)


@ app.route("/documentation")
async def documentation():
    try:
        with open("cfg/documentation.yaml", 'r') as stream:
            data_loaded = yaml.load(stream, Loader=yaml.BaseLoader)
            loaded = True
    except BaseException:
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        data_loaded = {}
        loaded = False

    return await render_template("documentation.html", session=session, loaded=loaded, docs=data_loaded)


@ app.route("/formatting")
async def formatting():

    markdown_docs = {
        "users": {
            "user": "Alias of user.name",
            "user.mention": "User mention",
            "user.name": "The users name",
            "user.discriminator": "The users discriminator tag",
            "user.id": "The users id",
            "user.avatar": "Url of users avatar",
            "user.created.timestamp": "Timestamp for when the users account was created",
            "user.created.since": "String for how long a user has been on discord",
            "user.joined.timestamp": "Timestamp of how long a user has been on the server",
            "user.joined.since": "String for how long a user has been on the server",
        },
        "server": {
            "members": "Alias of server.members",
            "server": "Alias of server.name",
            "server.name": "The servers name",
            "server.id": "The servers id",
            "server.members": "Number of users and prefix of users on server",
            "server.member.count": "Number of users who are on the server",
            "server.member.prefix": "Count prefix for server.member.count",
            "server.icon": "Url for the server icon",
            "server.created.timestamp": "Timestamp for when server was created",
            "server.created.since": "Stringh for how long the server has existed for",
            "server.splash": "Url of splash the server has (if there is one)",
            "server.shard_id": "Shard Id that the server is on",
        },
        "invite": {
            "invite.code": "Code that the invite has been assigned to",
            "invite.inviter": "Name of user who created the invite",
            "invite.inviter.id": "Id of user who created the invite",
            "invite.uses": "How many people have used the invite",
            "invite.temporary": "Boolean that specifies if the invite is temporary",
            "invite.created.timestamp": "Timestamp for when it was created",
            "invite.created.since": "String for how long it has been since the invite was made",
            "invite.max": "Max invites for an invite. Will return 0 if it is unlimited"
        }
    }

    return await render_template("formatting.html", session=session, markdown_docs=markdown_docs)


@ app.route("/customembeds")
async def customembeds():
    return await render_template("customembeds.html", session=session)


@ app.route("/status")
async def status():
    _time = time.time()

    clusters = {}
    for i in list(["debug", "donator", "b"] + list(range(config['bot']['clusters']))):
        clusters[str(i)] = {
            "alive": False,
            "pingalive": False,
            "stats": {},
            "lastping": 0
        }

    for cluster, ping in last_ping.items():
        cluster = str(cluster)
        clusters[cluster]['alive'] = True
        if _time - ping < 70:
            clusters[cluster]['pingalive'] = True
        clusters[cluster]['lastping'] = _time - ping

    for cluster, data in cluster_data.items():
        cluster = str(cluster)
        clusters[cluster]['stats'] = data
        if clusters[cluster]['stats'].get('highest_latency'):
            clusters[cluster]['stats']['highest_latency'] = max(
                list(map(lambda o: o[1], data['latencies'])))
        else:
            clusters[cluster]['stats']['highest_latency'] = 0

    clusters = list(sorted(clusters.items(), key=lambda o: str(o[0])))

    online = list(
        sorted(
            filter(
                lambda o: o[1]['alive'] and o[1]['pingalive'],
                clusters),
            key=lambda o: str(
                o[0])))
    degrade = list(
        sorted(
            filter(
                lambda o: o[1]['alive'] and not o[1]['pingalive'],
                clusters),
            key=lambda o: str(
                o[0])))
    offline = list(
        sorted(
            filter(
                lambda o: not o[1]['alive'],
                clusters),
            key=lambda o: str(
                o[0])))

    clusters = list(online + degrade + offline)
    clusters = dict(
        zip(map(lambda o: o[0], clusters), map(lambda o: o[1], clusters)))

    return await render_template("status.html", session=session, clusters=clusters, botconfig=config['bot'])


@ app.route("/search")
async def search():
    return await render_template("search.html", session=session)


@ app.route("/searchemojis")
async def searchemoji():
    return await render_template("searchemojis.html", session=session)


@ app.route("/guild/<id>")
@ app.route("/g/<id>")
async def guild(id):
    is_guild = False
    staff = []
    guild_donations = []

    if id.isnumeric():
        guild_info = await get_guild_info(id)
        if guild_info:
            is_guild = True

    if rockutils.hasvalue("d.b.sw", guild_info) and not guild_info['d']['b'].get('sw', False):
        return abort(403)

    if is_guild:
        result_payload = await create_job(request=None, o="guildstaff", a=int(id), r="*", timeout=1)
        guild_donations = await get_guild_donations(guild_info)

        for data in result_payload['d'].values():
            if data['success']:
                staff = data['data']

    return await render_template("guild.html", session=session, valid_guild=is_guild, id=id, guildinfo=guild_info, donations=guild_donations, staff=staff)


@ app.route("/invite/<id>")
@ app.route("/i/<id>")
async def invite(id):
    invite_id = id

    # temporary
    vanity = {
        "biffa": 136759842948907008,
        "welcomer": 341685098468343822,
        "lust": 440255430271434763
    }

    if invite_id in vanity:
        id = vanity[invite_id]

    guild_info = await get_guild_info(id)
    return await render_template("invite.html", session=session, id=invite_id, guild_id=id, guild_info=guild_info)


@ app.route("/borderwall")
@ app.route("/borderwall/<id>")
@ valid_oauth_required
async def borderwall(id=""):
    error = ""

    # borderwall_details = r.table("borderwall").get(id).run(rethink) or {}
    borderwall_details = await get_value(connection, "borderwall", id, default={})
    if borderwall_details:
        if borderwall_details['a']:
            valid_borderwall = False
            error = '<div class="success success-fill" role="info"><i class="mdi mdi-check"></i> This borderwall id has already been validated </div>'
        else:
            valid_borderwall = True
    else:
        valid_borderwall = False
        error = '<div class="primary primary-fill" role="info">The borderwall id specified is not valid </div>'

    ip = "Unknown"
    for _h in ['CF-Connecting-IP', 'CF_CONNECTING_IP', 'X_FORWARDED_FOR', 'REMOTE_ADDR']:
        _ip = request.headers.get(_h, False)
        if _ip:
            ip = _ip
            break

    return await render_template("borderwall.html", headers=request.headers, session=session, data=borderwall_details, borderwall_id=id, ip=ip, error=error, show_bw=valid_borderwall)


@ app.route("/borderwall/<id>/authorize", methods=['POST', 'GET'])
@ valid_oauth_required
async def borderwall_authorize(id):
    form = dict(await request.form)
    token = form.get("token", False)
    # borderwall_details = r.table("borderwall").get(id).run(rethink)
    borderwall_details = await get_value(connection, "borderwall", id)

    if not token:
        return jsonify(success=False, error="Invalid token given")
    if not borderwall_details:
        return jsonify(success=False, error="Invalid borderwall code given")

    user_id = session.get('user_id')
    if not user_id:
        return jsonify(
            success=False,
            error="An error occured. Log out and log back in"
        )
    else:
        if str(user_id) != str(borderwall_details.get("ui", "")):
            return jsonify(
                success=False,
                error="You are authorized on a different users account. Please log out"
            )

    data = {
        "secret": config['keys']['recaptcha-server'],
        "response": token
    }

    ip = "Unknown"
    for _h in ['CF-Connecting-IP', 'CF_CONNECTING_IP', 'X_FORWARDED_FOR', 'REMOTE_ADDR']:
        _ip = request.headers.get(_h, False)
        if _ip:
            data['remoteip'] = _ip
            ip = _ip
            break

    if ip != "Unknown":
        user_id = session.get('user_id')
        if user_id:
            user_info = await get_user_info(str(user_id))
            if user_info:
                if "ip" not in user_info:
                    user_info['ip'] = []
                user_info['ip'].append(ip)
                # r.table("users").get(str(user_id)).update(
                #     user_info).run(rethink)
                await set_value(connection, "users", str(user_id), user_info)

    async with aiohttp.ClientSession() as _session:
        async with _session.post("https://www.google.com/recaptcha/api/siteverify", data=data) as res:
            gpayload = await res.json()
            getipintelcheck = False

            if gpayload['success']:
                if getipintelcheck and ip != "Unknown":
                    url = f"http://check.getipintel.net/check.php?ip={ip}&contact=[removed]&oflags=b&format=json"
                    async with _session.post(url) as res:
                        ipayload = await res.json()
                        if ipayload['status'] == "success":
                            if ipayload['BadIP'] == 1:
                                pass
                                return jsonify(
                                    success=False,
                                    error="Your IP score was too low to verify. Please disable a VPN or Proxy if you are using one.")

                if gpayload.get('score', 1) > 0.5:
                    borderwall_details['a'] = True
                    borderwall_details['ip'] = ip
                    # r.table("borderwall").get(id).update(
                    #     borderwall_details).run(rethink)
                    await set_value(connection, "borderwall", id, borderwall_details)
                    await create_job(o="borderwallverify", a=[borderwall_details['gi'], borderwall_details['ui'], id], r="*")
                    return jsonify(success=True)
                else:
                    return jsonify(
                        success=False,
                        error="Your IP score was too low to verify. Please disable a VPN or Proxy if you are using one.")
            return jsonify(success=False, error="Recaptcha failed")
    return jsonify(success=True)


@ app.route("/invitebot")
@ app.route("/invitebot/<btype>")
async def invitebot(btype="bot"):
    if btype == "bot":
        id = config['ids']['main']
    elif btype == "beta":
        id = config['ids']['debug']
    elif btype == "donator":
        id = config['ids']['donator']
    elif btype == "fallback":
        id = config['ids']['bcomer']
    else:
        return redirect("/")

    return redirect(
        f"https://discordapp.com/oauth2/authorize?client_id={id}&scope=bot&permissions=8")


@ app.route("/backgrounds")
async def backgrounds():
    path = os.path.join(config['cdn']['location'], "Images")
    backgrounds = sorted(os.listdir(path))
    return await render_template("backgrounds.html", session=session, backgrounds=backgrounds, background_count=len(backgrounds))


@ app.route("/donate")
async def donate():
    error = ""
    _args = list(dict(request.args).keys())

    # error = '<div class="alert alert-fill-danger" role="info"><i class="mdi mdi-do-not-disturb"></i> Paypal donations are temporarily disabled. Please use patreon instead. You may remove your pledge once you start to still receive the rewards. Please make sure to bind your discord account to patreon.</div>'

    if len(_args) == 1:
        arg = _args[0]
        if arg == "disabled":
            error = '<div class="alert alert-fill-danger" role="info"><i class="mdi mdi-do-not-disturb"></i> Paypal donations are temporarily disabled. Please use patreon instead. You may remove your pledge once you start to still receive the rewards. Please make sure to bind your discord account to patreon.</div>'
        if arg == "invaliddonation":
            error = '<div class="alert alert-fill" role="info"><i class="mdi mdi-do-not-disturb"></i> An invalid donation type was specified in your request. If you have changed the donation url manually, change it back. </div>'
        if arg == "paymentcreateerror":
            error = '<div class="alert alert-fill-alert" role="alert"><i class="mdi mdi-do-not-disturb"></i> We were unable to create a payment for you to be able to use. Please try again. </div>'
        if arg == "userinfogone":
            error = '<div class="alert alert-fill-alert" role="alert"><i class="mdi mdi-do-not-disturb"></i> We were unable to retrieve your user information. Please try again. </div>'
        if arg == "invalidpaymentid":
            error = '<div class="alert alert-fill" role="info"><i class="mdi mdi-do-not-disturb"></i> Your request has returned an invalid payment id. Please attempt this again. Please note you have not been charged. </div>'
        if arg == "invalidprice":
            error = '<div class="alert alert-fill" role="info"><i class="mdi mdi-do-not-disturb"></i> Invalid price was specified in your request. If you have changed the donation url manually, change it back. </div>'
        if arg == "invalidmonth":
            error = '<div class="alert alert-fill" role="info"><i class="mdi mdi-do-not-disturb"></i> Invalid month was specified in your request. If you have changed the donation url manually, change it back. </div>'
        if arg == "invalidarg":
            error = '<div class="alert alert-fill-alert" role="alert"><i class="mdi mdi-do-not-disturb"></i> Your request is missing arguments. If you have changed the donation url manually, change it back. </div>'
        if arg == "fatalexception":
            error = '<div class="alert alert-fill-danger" role="danger"><i class="mdi mdi-do-not-disturb"></i> There was a problem assigning your donation role. Please visit the support server to fix this immediately as the payment has been processed </div>'

        if arg == "success":
            error = '<div class="alert alert-fill-success" role="alert"><i class="mdi mdi-check"></i> Thank you for donating! Your donation has gone through and been processed automatically. If you have not blocked your direct messages, you should receive a message from the bot and it should show on the support server under #donations </div>'

    if blackfriday:
        return await render_template("donate-blackfriday.html", session=session, error=error)
    return await render_template("donate.html", session=session, error=error)


@ app.route("/dashboard")
@ valid_oauth_required
async def dashboard():
    error = ""
    errortype = 0
    _args = list(dict(request.args).keys())

    if len(_args) == 1:
        arg = _args[0]
        if arg == "missingpermission":
            error = '<div class="alert alert-fill-danger" role="alert"><i class="mdi mdi-do-not-disturb"></i> You do not have permission to view the dashboard of this server </div>'
            errortype = 1
        elif arg == "invalidguild":
            error = '<div class="alert alert-fill-danger" role="alert"><i class="mdi mdi-alert-circle"></i> The selected guild could not be found </div>'
            errortype = 2
        elif arg == "missingdata":
            error = '<div class="alert alert-fill-danger" role="alert"><i class="mdi mdi-database-remove"></i> Could not locate any data for this guild. <b>Please run a command on the server</b> </div>'
            errortype = 3

    guilddata = None
    if isinstance(session.get("guild_data", []), list):
        guilds = list(sorted(session.get("guild_data", []),
                             key=lambda o: o.get("name", "")))
    else:
        guilds = []
    guild_id = session.get("dashboard_guild", 0)
    for item in guilds:
        if str(item.get("id")) == str(guild_id):
            guilddata = item
    if guilddata:
        guildinfo = await get_guild_info(guild_id)
    else:
        guildinfo = {}

    # return jsonify(guilds, guild_id, guilddata, guildinfo)
    return await render_template("dashboard/guilddetails.html", session=session, error=error, errortype=errortype, guilds=guilds, guild=guilddata, guildinfo=guildinfo)


@ app.route("/dashboard/changeguild/<id>")
@ valid_oauth_required
async def change_dashboard_guild(id):
    guilds = list(sorted(session.get("guild_data", []),
                         key=lambda o: o.get("name", "")))
    guild_id = id
    guilddata = None

    for item in guilds:
        if str(item.get("id")) == str(guild_id):
            guilddata = item

    if guilddata:
        if await has_elevation(guild_id, session.get("user_id"), guild_info=None, bot_type="main"):
            session['dashboard_guild'] = id
            return redirect("/dashboard")

        return redirect("/dashboard?missingpermission")
    else:
        return redirect("/dashboard?invalidguild")


@ app.route("/errors/<id>", methods=['GET', 'POST'])
async def error_view(id):
    # error = r.table("errors").get(id).run(rethink) or {}
    error = await get_value(connection, "errors", id, default={})

    if request.method == "POST":

        session['previous_path'] = request.path
        if session.get("oauth2_token") is None:
            return redirect("/login")

        should_check = False

        if sum(
            1 if not session.get(c) else 0 for c in [
                'user_id',
                'user_data',
                'guild_data',
                'oauth2_check']) > 0:
            should_check = True

        if session.get("oauth2_check") is None or time.time() - \
                session.get("oauth2_check") > 604800:
            should_check = True

        if should_check:
            return redirect("/login")

        _config = rockutils.load_json("cfg/config.json")
        user_id = int(session['user_id'])
        elevated = False

        if user_id in _config['roles']['support']:
            elevated = True
        if user_id in _config['roles']['developer']:
            elevated = True
        if user_id in _config['roles']['admins']:
            elevated = True
        if user_id in _config['roles']['trusted']:
            elevated = True

        if elevated and error != {}:
            if error['status'] == "not handled":
                error['status'] = "handled"
            else:
                error['status'] = "not handled"
            # r.table("errors").get(id).update(error).run(rethink)
            await set_value(connection, "errors", id, error)

    return await render_template("command_error.html", error=error)


@ app.route("/errors")
async def error_list():
    # _config = rockutils.load_json("cfg/config.json")
    # user_id = int(session['user_id'])
    # elevated = False

    # if user_id in _config['roles']['support']:
    #     elevated = True
    # if user_id in _config['roles']['developer']:
    #     elevated = True
    # if user_id in _config['roles']['admins']:
    #     elevated = True
    # if user_id in _config['roles']['trusted']:
    #     elevated = True

    # if not elevated:
    #     return "", 401

    results = []
    # values = r.table("errors").run(rethink)

    async with connection.acquire() as pconnection:
        vals = pconnection.fetch("SELECT * FROM errors")

    for val in vals:
        results.append(json.loads(val["value"]))

    # while True:
    #     try:
    #         _val = values.next()
    #         results.append(_val)
    #     except Exception:
    #         break

    not_handled = list(filter(lambda o: o['status'] == "not handled", results))
    handled = list(filter(lambda o: o['status'] == "handled", results))
    return await render_template("command_error_list.html", not_handled=not_handled, handled=handled)


app.run(host="0.0.0.0", port=config['ipc']['port'],
        use_reloader=False, loop=asyncio.get_event_loop())
# :comfy:
