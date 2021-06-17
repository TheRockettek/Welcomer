import asyncio
import string
import random
import time
import asyncio
import math
import copy
import psutil
import os
import logging

from quart import Quart, g, websocket, session, redirect, request, url_for, jsonify, render_template, send_file, abort
from rockutils import rockutils

import ujson as json

config = rockutils.load_json("data/bot_data.json")

app = Quart(__name__)

log = logging.getLogger('quart.serving')
log.setLevel(logging.ERROR)

activejobs = {}
clusterjobs = {}

clusterstatus = {}

default = {
    "pid": "",
    "cpus": "",
    "cores": [],
    "status": "Unknown",
    "guilds": "",
    "members": "",
    "usedmem": 0,
    "botmem": 0,
    "totalmem": 0,
    "vmem": 0
}

clusterstatus['IPC'] = copy.deepcopy(default)
clusterstatus['CDN'] = copy.deepcopy(default)

name = "py"
user = "DESKTOP-LMH7BFS\\Gamer"

for i in range(0, config['sharding']['clusters']):
    clusterstatus[str(i)] = copy.deepcopy(default)

def getthreads():
    try:
        python_threads = list(p for p in set(psutil.process_iter()) if name in p.name())
        rocks_threads = list(p for p in python_threads if p.username() == user)
        rocks_threads = sorted(rocks_threads, key=lambda o: o.pid)
        return rocks_threads
    except:
        return getthreads()


def get_info():
    rocks_threads = getthreads()

    global clusterstatus

    tmem = psutil.virtual_memory().available/1000000000
    tmem = f"{math.ceil(tmem*100)/100}G"
    umem = psutil.virtual_memory().used/1000000000
    umem = f"{math.ceil(umem*100)/100}G"

    cpupercents = psutil.cpu_percent(percpu=True)
    for thread in rocks_threads:
        cmdline = thread.cmdline()
        if len(cmdline) >= 3:
            if cmdline[2] in ["Welcomer.py","IPCServer.py","CDNServer.py"]:
                if "IPC" in cmdline[2]:
                    target = "IPC"
                    clusterstatus[target]['guilds'] = ""
                    clusterstatus[target]['members'] = ""
                    clusterstatus[target]['latency'] = ""
                    clusterstatus[target]['latencies'] = []
                    clusterstatus[target]['status'] = "Ready"
                elif "CDN" in cmdline[2]:
                    target = "IPC"
                    clusterstatus[target]['guilds'] = ""
                    clusterstatus[target]['members'] = ""
                    clusterstatus[target]['latency'] = ""
                    clusterstatus[target]['latencies'] = []
                else:
                    target = cmdline[3]

                clusterstatus[target]['pid'] = thread.pid
                clusterstatus[target]['cpus'] = str(thread.cpu_affinity())
                clusterstatus[target]['cores'] = list(cpupercents[id] for id in thread.cpu_affinity())

                mem = thread.memory_info()
                vmem = mem.vms/1000000000
                if vmem > 1:
                    clusterstatus[target]['vmem'] = f"{math.ceil(vmem*100)/100}G"
                else:
                    clusterstatus[target]['vmem'] = f"{math.ceil(vmem*100000)/100}M"
                
                rmem = mem.rss/1000000000
                if rmem > 1:
                    clusterstatus[target]['botmem'] = f"{math.ceil(rmem*100)/100}G"
                else:
                    clusterstatus[target]['botmem'] = f"{math.ceil(rmem*100000)/100}M"
                
                clusterstatus[target]['usedmem'] = umem
                clusterstatus[target]['totalmem'] = tmem

async def create_job(request, op="", args="", recep=""):
    
    global activejobs
    global clusterjobs
    
    if request:
        head = request.headers

        reqtimeout = head.get("timeout",10)
        if op == "":
            op = head.get("op")
        if args == "":
            args = head.get("args")
        if recep == "":
            recep = head.get("recep")
    job_key = "".join(random.choices(string.ascii_letters,k=32))

    rockutils.pprint(f"Recieved job results with key {job_key[:10]}...", prefix=">", prefix_colour="red", text_colour="light red")
    rockutils.pprint(f"- recepients: {recep}", prefix=">", prefix_colour="red", text_colour="light red")
    rockutils.pprint(f"- opcode: {op}", prefix=">", prefix_colour="red", text_colour="light red")

    recepients = []
    
    if recep == "*":
        recepients = list(range(0,config['sharding']['clusters']))
    else:
        try:
            recepients = [int(r) for r in json.loads(recep)]
        except:
            recepients = [int(recep)]

    activejobs[job_key] = {}

    headers = {
        "op": op,
        "args": args,
        "key": job_key
    }

    for recep in recepients:
        if not recep in clusterjobs:
            clusterjobs[recep] = []
        clusterjobs[recep].append(headers)

    time_start = time.time()
    wait = time_start + reqtimeout

    while len(activejobs[job_key]) != len(recepients) and time.time() < wait:
        if len(activejobs[job_key]) == len(recepients):
            break
        await asyncio.sleep(0.05)

    responce = {
        "key": job_key,
        "recep": recep,
        "op": op,
        "args": args,
        "job_start": time_start,
        "data": {}
    }

    for cluster,data in activejobs[job_key].items():
        responce['data'][cluster] = data

    time_end = time.time()
    responce['job_duration'] = time_end - time_start

    del activejobs[job_key]

    rockutils.pprint(f"Finished job with key {job_key[:10]}...", prefix="<", prefix_colour="green", text_colour="light green")
    rockutils.pprint(f"- recepients: {recepients}", prefix="<", prefix_colour="green", text_colour="light green")
    rockutils.pprint(f"- opcode: {op}", prefix="<", prefix_colour="green", text_colour="light green")
    rockutils.pprint(f"- time taken: {math.ceil(responce['job_duration']*1000)}ms", prefix="<", prefix_colour="green", text_colour="light green")
    
    return responce

@app.route("/api/submit/<job_key>/<cluster>", methods=['POST'])
async def submit(job_key,cluster):
    global activejobs

    cluster = int(cluster)
    data = await request.get_json(force=True)
    rockutils.pprint(f"Recieved job results from port {cluster} with key {job_key[:10]}...", prefix=">", prefix_colour="yellow", text_colour="light yellow")

    if data and "internal" in job_key:
        clusterstatus[str(cluster)].update(data)
        return jsonify({"success": True})
    else:
        if data and (not cluster is None) and (job_key in activejobs):
            activejobs[job_key][cluster] = data
            return jsonify({"success": True})
        else:
            return jsonify({"success": True, "error": "InvalidArgument"})

@app.route("/api/pushstatus/<cluster>/<status>", methods=['POST'])
async def pushstatus(cluster,status):
    statuses = {
        "0": "Offline",
        "1": "Restarting",
        "2": "Ready",
        "3": "Connecting",
        "4": "Hung"
    }
    global clusterstatus
    clusterstatus[cluster]['status'] = statuses[status]
    return ""

@app.websocket("/api/slave/<cluster>")
async def slave(cluster):
    cluster = int(cluster)
    global clusterjobs
    if not cluster in clusterjobs:
        clusterjobs[cluster] = []
    rockutils.pprint(f"Added cluster {cluster}", prefix="IPC-Slave", prefix_colour="light blue", text_colour="cyan")
    last_pong = time.time()
    pongjob = {
        "op": "details",
        "args": "",
        "key": f"internal.{cluster}"
    }
    clusterjobs[cluster].append(pongjob)
    while True:
        jobs = clusterjobs[cluster]

        if time.time()-last_pong > 15:
            jobs.append(pongjob)
            last_pong = time.time()
        if len(jobs) > 0:
            json_resp = json.dumps(jobs)
            clusterjobs[cluster] = []
            await websocket.send(json_resp)
        await asyncio.sleep(0.05)

@app.route("/api/signal/<cluster>/<opcode>")
async def signal(cluster, opcode):
    op = {
        "1": "restart",
        "2": "hang",
        "3": "exit",
        "4": "kill"
    }
    opcode = op.get(opcode)
    if opcode == "kill":
        cluster = clusterstatus.get(cluster)
        if cluster:
            try:
                pid = cluster['pid']
                if pid and not pid in [0,'0',""," "]:
                    proc = psutil.Process(int(pid))
                    proc.kill()
                    return jsonify({"success":True})
            except Exception as e:
                return jsonify({"success":False, "error":f"{e}"})
    if opcode:
        try:
            int(cluster)
            await create_job(None, opcode, "", int(cluster))
            return jsonify({"success":True})
        except:
            if cluster == "CDN":
                return jsonify({"success":False, "error":"InvalidArgument: You cannot preform signals on this cluster"})
            elif cluster == "IPC":
                exitcode = {
                    "restart": 1,
                    "hang": 2,
                    "exit": 0
                }
                os._exit(exitcode[opcode])
            else:
                return jsonify({"success":False, "error":"InvalidArgument: No such cluster"})
    else:
        return jsonify({"success":False, "error":"InvalidArgument: No such opcode"})

@app.route("/api/request/", methods=['GET','POST'])
async def requestjob():
    head = request.headers
    op = head.get("op")
    args = head.get("args")
    recep = head.get("recep")
    return jsonify(await create_job(request, op, args, recep))

@app.route("/admin/dashboard", methods=['GET','POST'])
async def apidashboard():
    global clusterstatus
    if request.method == "POST":
        get_info()
        return jsonify(clusterstatus)
    else:
        return await render_template("admin_dashboard.html", clusters=clusterstatus.keys())

rockutils.pprint("Starting up", prefix="IPC-Server")
get_info()
app.run(host="0.0.0.0", port=config['ipc_port'])