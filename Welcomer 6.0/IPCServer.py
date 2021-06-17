import asyncio
import aiohttp
import random
import string
import time
import logging
import paypalrestsdk
import os
import html
import math
import discord

from urllib.parse import quote_plus
from quart import Quart, g, websocket, session, request, jsonify, render_template, send_file, redirect
from quart.ctx import copy_current_websocket_context
from rockutils import rockutils
from requests_oauthlib import OAuth2Session
from functools import wraps

import ujson as json
import rethinkdb as r

log = logging.getLogger('quart.serving')
log.setLevel(logging.ERROR)
config = rockutils.load_json("cfg/config.json")
paypal_api = paypalrestsdk.configure(config['paypal'])
rethink = r.connect(host=config['db']['host'], port=config['db']['port'], db=config['db']['table'])
rethink_sessions = r.connect(host=config['db']['host'], port=config['db']['port'], db="Quart")

_oauth2 = config['oauth']
_domain = "beta.welcomer.fun"
_debug = True

from itsdangerous import URLSafeSerializer
import pickle
from datetime import timedelta
from uuid import uuid4
from werkzeug.datastructures import CallbackDict
from quart.sessions import SessionInterface, SessionMixin

class RethinkSession(CallbackDict, SessionMixin):

    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True
        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False

class RethinkSessionInterface(SessionInterface):
    serializer = json
    session_class = RethinkSession

    def __init__(self, rethink, prefix=''):
        self.rethink = rethink
        self.prefix = prefix
        self.serialize = URLSafeSerializer(_oauth2['client_secret'])

    def generate_sid(self):
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        return app.permanent_session_lifetime

    def open_session(self, app, request):
        sid = request.cookies.get(app.session_cookie_name)
        if not sid:
            sid = self.generate_sid()
            return self.session_class(sid=sid, new=True)
        rockutils.prefix_print(f"Retreiving session {self.prefix + sid}. URL: {request.path}", prefix_colour="light blue")
        val = r.table("sessions").get(self.prefix + sid).run(self.rethink)
        if val is not None:
            data = self.serializer.loads(self.serialize.loads(val['data']))
            return self.session_class(data, sid=sid)
        return self.session_class(sid=sid, new=True)

    def save_session(self, app, session, response):
        domain = self.get_cookie_domain(app)
        if not session:
            rockutils.prefix_print(f"Deleting session {self.prefix + session.sid}. URL: {request.path}", prefix_colour="light red")
            r.table("sessions").get(self.prefix + session.sid).delete().run(self.rethink)
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        cookie_exp = self.get_expiration_time(app, session)
        val = self.serialize.dumps(self.serializer.dumps(dict(session)))
        rockutils.prefix_print(f"Updating session {self.prefix + session.sid}. URL: {request.path}", prefix_colour="light yellow")
        if r.table("sessions").get(self.prefix + session.sid).run(self.rethink):
            r.table("sessions").get(self.prefix + session.sid).replace({"id":self.prefix + session.sid,"data":val}).run(self.rethink)
        else:
            r.table("sessions").insert({"id":self.prefix + session.sid,"data":val}).run(self.rethink)
        response.set_cookie(app.session_cookie_name, session.sid, expires=cookie_exp, httponly=True, domain=domain)

app = Quart(__name__)
app.session_interface = RethinkSessionInterface(rethink_sessions)
app.secret_key = _oauth2['client_secret']

app.config['MAX_CONTENT_LENGTH'] = 268435456
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

def iterat():
    return base64.b64encode(bytes(str(time.time()*100000),"ascii")).decode().replace("=","").lower()

app.jinja_env.globals['json_loads'] = json.loads
app.jinja_env.globals['len'] = len
app.jinja_env.globals['str'] = str
app.jinja_env.globals['dict'] = dict
app.jinja_env.globals['bool'] = bool
app.jinja_env.globals['int'] = int
app.jinja_env.globals['iterat'] = iterat
app.jinja_env.globals['unesc'] = html.unescape
app.jinja_env.globals['ctime'] = time.time
app.jinja_env.globals['enumerate'] = enumerate
app.jinja_env.globals['sorted'] = sorted
app.jinja_env.globals['dirlist'] = os.listdir
app.jinja_env.globals['exist'] = os.path.exists

ipc_jobs = {}
cluster_jobs = {}
clusters_initialized = set()
last_ping = {}
user_cache = {}
cluster_status = {}
cluster_data = {}

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
    global clusters_initialized

    if request:
        o = (o if o != "" else request.headers.get("op"))
        a = (a if a != "" else request.headers.get("args"))
        r = (r if r != "" else request.headers.get("recep"))
        timeout = (timeout if timeout != 10 else int(request.headers.get("timeout")))

    job_key = "".join(random.choices(string.ascii_letters,k=32))

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
        except:
            _c = str(r).lower()
            if _c in clusters_initialized:
                    recepients.append(_c)
    
    ipc_jobs[job_key] = {}

    payload = {"o": o, "a": a, "k": job_key}

    for r in recepients:
        cluster_jobs[r].append(payload)
    
    time_start = time.time()
    delay_time = int(time_start) + timeout 

    while time.time() < delay_time:
        if len(ipc_jobs[job_key]) == len(recepients):
            break
        await asyncio.sleep(0.05)
    
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
            
            await asyncio.sleep(0.05)
    except Exception as e:
        rockutils.prefix_print(str(e), prefix="IPC Sender", prefix_colour="light red", text_colour="red")

async def receiving(cluster):
    rockutils.prefix_print(f"Started receiving for {cluster}")
    try:
        while True:
            _data = json.loads(await websocket.receive())

            o = _data['o']
            if o == "SUBMIT" and "ping" in _data['k']:
                last_ping[cluster] = time.time()
                cluster_data[cluster] = _data['d']
                rockutils.prefix_print(f"Retrieved PING from cluster {cluster}")
            elif o == "STATUS_UPDATE":
                d = _data['d']
                cluster_status[cluster] = d
                rockutils.prefix_print(f"Cluster {cluster} is now {_status_name.get(d)}")
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
                    except:
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
        rockutils.prefix_print(str(e), prefix="IPC Receiver", prefix_colour="light red", text_colour="red")

@app.route("/api/job/<auth>", methods=['POST','GET'])
async def ipc_job(auth):
    if auth != config['ipc']['auth_key']:
        return "Invalid authentication", 403
    return jsonify(await create_job(request))

@app.websocket("/api/ipc/<cluster>/<auth>")
async def ipc_slave(cluster, auth):
    if auth != config['ipc']['auth_key']:
        return "Invalid authentication", 403
    else:
        await websocket.accept()

    cluster = str(cluster).lower()

    ipc_jobs[cluster] = []
    clusters_initialized.add(cluster)

    if not cluster in cluster_jobs:
        cluster_jobs[cluster] = []

    rockutils.prefix_print(f"Connected to cluster {cluster}")

    last_ping = time.time()

    loop = asyncio.get_event_loop()
    try:
        await asyncio.gather(
                copy_current_websocket_context(sending)(cluster),
                copy_current_websocket_context(receiving)(cluster)
            )
    except Exception as e:
        rockutils.prefix_print(str(e), prefix="IPC Slave", prefix_colour="light red", text_colour="red")

#############################################################
# DASHBOARD
#############################################################

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

async def get_guild_info(id, refer=""):
    try:
        rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for G:{id}", prefix="Guild Info:Get", prefix_colour="light green")
        guild_info = r.table("guilds").get(str(id)).run(self.bot.connection)
        return guild_info or False
    except:
        rockutils.prefix_print(f"Error occured whilst retrieving info for G:{id}. {e}", prefix="Guild Info:Update", prefix_colour="red", text_colour="light red")
        return False

async def update_guild_info(id, data, forceupdate=False, refer=""):
    try:
        rockutils.prefix_print(f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for G:{id}", prefix="Guild Info:Update", prefix_colour="light green")
        t = time.time()
        if forceupdate:
            r.table("guilds").get(str(id)).update(data).run(self.bot.connection)
        else:
            r.table("guilds").get(str(id)).replace(data).run(self.bot.connection)
        te = time.time()
        if te-t > 1:             
            rockutils.prefix_print(f"Updating guild info took {math.floor((te-t)*1000)}ms", prefix="Guild Info:Update", prefix_colour="red", text_colour="light red")
        return True
    except Exception as e:
        rockutils.prefix_print(f"Error occured whilst updating info for G:{id}. {e}", prefix="Guild Info:Update", prefix_colour="red", text_colour="light red")
        return False

async def has_guild_donated(guild_info, plus=True, pro=True, extended=True, partner=True):
    _time = time.time()

    try:
        if partner:
            _userinfo = await get_user_info(guild_info['d']['g']['o']['id'])
            if _userinfo and _userinfo['m']['p']:
                return True
    except:
        pass

    try:
        for id in guild_info['d']['de']:
            _userinfo = await get_user_info(id)
            if _userinfo:
                if extended:
                    if _userinfo['m']['extended']['h'] and (_time - _userinfo['m']['extended']['u'] > 0 or _userinfo['m']['extended']['p']):
                        return True
                if pro:
                    if _userinfo['m']['pro']['h'] and (_time - _userinfo['m']['pro']['u'] > 0 or _userinfo['m']['pro']['p']):
                        return True
                if plus:
                    if _userinfo['m']['plus']['h'] and (_time - _userinfo['m']['plus']['u'] > 0 or _userinfo['m']['plus']['p']):
                        return True
    except:
        pass

    return False

async def cache_discord(url, bot_type, key=None, custom_token=None, default={}, cachetime=120):
    if not bot_type in config['tokens']:
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

    if not key in discord_cache or _t - discord_cache.get(key)['s'] > 0:
        try:
            rockutils.prefix_print(f"Retrieving {url}", prefix="Cacher")
            async with aiohttp.Session() as _session:
                async with _session.get(url, headers={"Authorization": f"Bot {token}"}) as r:
                    data = await r.json()

                    if type(data) == dict and data.get("code"):
                        rockutils.prefix_print(f"Encountered bad response: {data}", prefix="Cacher")
                        discord_cache[key] = {
                            "d": default,
                            "s": _t+cachetime
                        }
                        return False, data.get("code",-1)

                    discord_cache[key] = {
                        "d": data,
                        "s": _t+cachetime
                    }
        except Exception as e:
            print(f"[cache_discord] {e}")
            return False, []
    return True, discord_cache[key]['d']


async def has_elevation(guild_id, member_id, guild_info=None, bot_type="main"):
    
    if not guild_info:
        guild_info = await get_guild_info(guild_id)

    if guild_info['d']['b']['hd']:
        bot_type = "donator"

    bot_type = "debug" if _debug else bot_type

    guild_success, guild = await cache_discord(f"guilds/{guild_id}", bot_type, key=f"guild:{guild_id}", cachetime=600)

    if guild_info:
        if int(guild['owner_id']) == int(member_id):
            return True

        if guild_info.get("st"):
            if str(user.id) in guild_info['st']['u'].keys():
                return True

    member_success, member = await cache_discord(f"guilds/{guild_id}/members/{member_id}", bot_type, key=f"member:{guild_id}:{member_id}")
    role_success, roles = await cache_discord(f"guilds/{guild_id}/roles", bot_type, key=f"role:{guild_id}")

    member_roles = []
    for role_id in map(int,member['roles']):
        for role in roles:
            if int(role['id']) == role_id:
                permissions = discord.permissions.Permissions(role['permissions'])
                if permissions.manage_guild or permissions.ban_members or permissions.administrator:
                    return True
    return False

def get_user(token):
    _t = time.time()
    key = token['access_token']
    if not key in user_cache or _t - user_cache.get(key)['s'] > 0:
        try:
            discord = make_session(token=token)
            user = discord.get(_oauth2['api_base'] + '/users/@me').json()
            guilds = discord.get(_oauth2['api_base'] + '/users/@me/guilds').json()
            user_cache[key] = {
                "d": {"user": user, "guilds": guilds},
                "s": _t+60
            }
        except Exception as e:
            print(f"[get_user] {e}")
            return False, {}
    data = user_cache[key]['d']
    if "message" in data['user'] and "401: Unauthorized" in data['user']['message']:
        return False, data
    return True, data

async def validity_checker():
    pass

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
    discord = make_session(scope=['identify','guilds'])
    authorization_url, state = discord.authorization_url(_oauth2['authorization_url'])
    session['oauth2_state'] = state
    return redirect(authorization_url)

@app.route("/callback")
async def _callback():

    try:
        discord = make_session(state=session.get("oauth2_state"), scope=['identify','guilds'])
        token = discord.fetch_token(_oauth2['token_url'], client_secret=_oauth2['client_secret'], authorization_response=request.url)
    except Exception as e:
        print(f"[callback] {e}")
        return redirect("/login")

    user_success, user = get_user(token)
    if not user_success:
        return redirect("/login")
    
    _t = math.ceil(time.time())
    session['oauth2_token'] = token
    session['oauth2_check'] = math.ceil(time.time())
    session['user_id'] = str(user['user']['id'])
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

        if sum(1 if not session.get(c) else 0 for c in ['user_id','user_data','guild_data','oauth2_check']) > 0:
            should_check = True

        if session.get("oauth2_check") is None or time.time() - session.get("oauth2_check") > 604800:
            should_check = True

        if should_check:
            return redirect("/login")

        return f(*args, **kwargs)

    return decorated_function

def valid_dash_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session['previous_path'] = request.path
        guilds = session.get("guild_data")
        if not guilds:
            cache_data()
            guilds = session.get("guild_data")
            if not guilds:
                return redirect("/login")

        guild = None
        dashboard_guild = session.get("dashboard_guild")

        for item in guilds:
            if str(item.get("id")) == str(dashboard_guild):
                guild = item

        if not guild and not session.get("developer_mode", False):
            return redirect("/dashboard?invalidguild")

        if guild['owner']:
            return f(*args, **kwargs)

        permissions = discord.permissions.Permissions(role['permissions'])
        if permissions.manage_guild or permissions.ban_members or permissions.administrator:
            return f(*args, **kwargs)

        elevated = has_elevation(guild['id'], session.get("user_id"))
        if elevated:
            return f(*args, **kwargs)
        
        return redirect("/dashboard?missingpermission")

    return decorated_function

@app.before_request
def cache_data():
    if not "static" in request.url:
        print(f"Caching data for path {request.path}")
        _t = math.ceil(time.time())
        if session.get("reloaded_data") and session.get("oauth2_token") and _t - session.get("reloaded_data") > 120:
            user_success, user = get_user(session.get("oauth2_token"))
            if user_success:
                session['reloaded_data'] = _t
                session['user_id'] = str(user['user']['id'])
                session['user_data'] = user['user']
                session['guild_data'] = user['guilds']
                session.permanent = True

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



@app.route("/debug/permission-test")
@valid_dash_user
async def _dash_test():
    # Default tester for person who has permissions
    return "Success"

@app.route("/debug/set-guild/<id>")
async def _guild_set(id):
    session['dashboard_guild'] = id
    return f"Set id to {id}"

@app.route("/test")
async def _test():
    print(await request.form)
    return await render_template("test.html")
    # return redirect("/dashboard?missingpermission")
    # return jsonify(dict(session))
    # return jsonify(session['user_data'])

@app.route("/stats")
async def _stats():
    print(last_ping)
    print(cluster_data)

    _time = time.time()

    
    clusters = {}
    for i in set(list(last_ping.keys()) + list(cluster_data.keys())):
        clusters[i] = {
            "alive": False,
            "pingalive": False,
            "stats": {},
            "lastping": 0
        }

    for cluster, ping in last_ping.items():
        clusters[cluster]['alive'] = True
        if _time - ping < 70:
            clusters[cluster]['pingalive'] = True
        clusters[cluster]['lastping'] = _time - ping
        if cluster in cluster_data.keys():
            clusters[cluster]['stats'] = cluster_data[cluster]

    return jsonify(clusters)
    

##############################################################################################################################################################################


@app.route("/")
async def index():
    guilds = sum(v['guilds'] for v in cluster_data.values())
    return await render_template("index.html", session=session, guilds=guilds) 

@app.route("/dashboard")
async def dashboard():
    error = None
    _args = list(dict(request.args).keys())

    if len(_args) == 1:
        arg = _args[0]
        if arg == "missingpermission":
            error = '<div class="alert alert-fill-danger" role="alert"><i class="mdi mdi-do-not-disturb"></i> You do not have permission to view the dashboard of this server </div>'
        elif arg == "invalidguild":
            error = '<div class="alert alert-fill-danger" role="alert"><i class="mdi mdi-alert-circle"></i> The selected guild could not be found </div>'
        elif arg == "missingdata":
            error = '<div class="alert alert-fill-danger" role="alert"><i class="mdi mdi-database-remove"></i> Could not locate any data for this guild. <b>Please run a command on the server</b> </div>'
    return await render_template("dashboard.html", session=session, error=error)

app.run(host="0.0.0.0", port=config['ipc']['port'])