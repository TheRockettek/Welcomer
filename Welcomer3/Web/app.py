import gevent.monkey
gevent.monkey.patch_all()

import os
from flask import Flask, g, session, redirect, request, url_for, jsonify
from requests_oauthlib import OAuth2Session

OAUTH2_CLIENT_ID = "330416853971107840"
OAUTH2_CLIENT_SECRET = "NMxY7QTsmuDJ_9_mkx_yLvaK8lHJYDBS"
OAUTH2_REDIRECT_URI = 'https://welcomer.fun/callback'

API_BASE_URL = os.environ.get('API_BASE_URL', 'https://discordapp.com/api')
AUTHORIZATION_BASE_URL = API_BASE_URL + '/oauth2/authorize'
TOKEN_URL = API_BASE_URL + '/oauth2/token'

app = Flask(__name__)
app.debug = True
app.config['SECRET_KEY'] = OAUTH2_CLIENT_SECRET

#if 'http://' in OAUTH2_REDIRECT_URI:
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'


def token_updater(token):
    session['oauth2_token'] = token


def make_session(token=None, state=None, scope=None):
    return OAuth2Session(
        client_id=OAUTH2_CLIENT_ID,
        token=token,
        state=state,
        scope=scope,
        redirect_uri=OAUTH2_REDIRECT_URI,
        auto_refresh_kwargs={
            'client_id': OAUTH2_CLIENT_ID,
            'client_secret': OAUTH2_CLIENT_SECRET,
        },
        auto_refresh_url=TOKEN_URL,
        token_updater=token_updater)


@app.route('/login')
def login():
    scope = request.args.get(
        'scope',
        'identify email connections guilds guilds.join')
    discord = make_session(scope=scope.split(' '))
    authorization_url, state = discord.authorization_url(AUTHORIZATION_BASE_URL)
    session['oauth2_state'] = state
    return redirect(authorization_url)


@app.route('/callback')
def callback():
    if request.values.get('error'):
        return request.values['error']
    discord = make_session(state=session.get('oauth2_state'))
    token = discord.fetch_token(
        TOKEN_URL,
        client_secret=OAUTH2_CLIENT_SECRET,
        authorization_response=request.url)
    session['oauth2_token'] = token
    return redirect(url_for('.me'))


@app.route('/dbl.css')
def cssstuff():
    return app.send_static_file('dbl.css')

@app.route('/me')
def me():
    discord = make_session(token=session.get('oauth2_token'))
    user = discord.get(API_BASE_URL + '/users/@me').json()
    guilds = discord.get(API_BASE_URL + '/users/@me/guilds').json()
    connections = discord.get(API_BASE_URL + '/users/@me/connections').json()
    return jsonify(user=user, guilds=guilds, connections=connections)


"""
/server/<string:id>
/server/<string:id>/edit
/server/<string:id>/submit
/server/<string:id>/members
/server/<string:id>/logs
/server/<string:id>/logs/stats
"""

@app.route("/server/<string:sid>")
def serverinfo(sid):
    0

@app.route("/server/<string:sid>/edit")
def serveredit(sid):
    0

@app.route("/server/<string:sid>/submit")
def serversubmit(sid):
    0

@app.route("/server/<string:sid>/members")
def servermembers(sid):
    0

@app.route("/server/<string:sid>/stats")
def serverstats(sid):
    0

@app.route("/server/<string:sid>/audit")
def serveraudit(sid):
    0

if __name__ == '__main__':
    app.run(port=5005)