import asyncio
import aiohttp
import os

import ujson as json
from rockutils import rockutils
from quart import Response, Quart, send_file, request, jsonify, abort, websocket
from quart.ctx import copy_current_websocket_context

app = Quart(__name__)
config = rockutils.load_json("cfg/config.json")
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = 'true'

lavalink_address = f"ws://{':'.join(map(str,config['lavalink']['server']))}"
rockutils.prefix_print(f"Lavalink address set to: {lavalink_address}")

async def mitm_sender(lavalink_ws, authorization, num_shards, user_id):
    # get information from bot and relay to lavalink
    while True:
        data = await websocket.receive()
        print(f"[>>] {data}")
        await lavalink_ws.send_str(data)

async def mitm_receiver(lavalink_ws, authorization, num_shards, user_id):
    # get information from lavalink and relay to bot
    while True:
        async for msg in lavalink_ws:
            print(f"[<<] {msg.data}")
            await websocket.send(msg.data)

@app.websocket("/")
async def lavalink_mitm():
    await websocket.accept()
    headers = websocket.headers
    authorization = headers.get("authorization", None)
    num_shards = headers.get("num-shards", None)
    user_id = headers.get("user-id", None)
    print(headers)
    if authorization and \
        num_shards and \
        user_id:


        async with aiohttp.ClientSession() as _session:
            async with _session.ws_connect(lavalink_address, headers={
                "Authorization": authorization,
                "Num-Shards": num_shards,
                "User-Id": user_id
            }) as lavalink_ws:

                loop = asyncio.get_event_loop()
                try:
                    await asyncio.gather(
                            copy_current_websocket_context(mitm_sender)(lavalink_ws, authorization, num_shards, user_id),
                            copy_current_websocket_context(mitm_receiver)(lavalink_ws, authorization, num_shards, user_id)
                        )
                except Exception as e:
                    rockutils.prefix_print(str(e), prefix="IPC Slave", prefix_colour="light red", text_colour="red")

    else:
        return abort(403)

app.run(host="0.0.0.0", port=config['lavalink']['mitm'][1])