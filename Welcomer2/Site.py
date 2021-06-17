"""from flask import Flask
app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello World!"

app.run(host='0.0.0.0', port=80)
"""
from aiohttp import web
import asyncio

@asyncio.coroutine
async def getimage(request):
    bgid = request.match_info.get('id', "0")
    file = open("/root/home/rock/Welcomer/Images/custom_" + bgid + ".png","rb")
    print("Request for " + str(bgid))
    data = file.read()
    ws = web.StreamResponse()
    await ws.prepare(request)
    ws.content_type = "image/png"
    ws.write(data)
    await ws.drain()
    return ws

@asyncio.coroutine
async def home(request):
    print("A person :D")
    return web.Response(text="Hello there :)")

app = web.Application()
app.router.add_get("/getbg/{id}.png", getimage)
app.router.add_get("/", home)

web.run_app(app, host="0.0.0.0", port=6789)
#web.run_app(app, host="0.0.0.0", port=80)


