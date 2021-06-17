import asyncio
import rethinkdb as r
from aiohttp import web

app = web.Application()
app.router.add_static("/","/home/rock/Welcomer/")

web.run_app(app, host="0.0.0.0", port=2000)
