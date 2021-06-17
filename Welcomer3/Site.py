import asyncio
import rethinkdb as r
from aiohttp import web

CLIENT_ID = ""
CLIENT_SECRET = ""
REDIRECT = "https://welcomer.fun/api/discord/callback"

@asyncio.coroutine
async def login(request):
    return web.HTTPFound("https://discordapp.com/oauth2/authorize?client_id=" + CLIENT_ID + "&scope=identify&response_type=code&redirect_uri=" + REDIRECT)

app = web.Application()
app.router.add_get("/login", login)
app.router.add_static("/","/home/rock/W3lcomer/static")

web.run_app(app, host="0.0.0.0", port=5005)
