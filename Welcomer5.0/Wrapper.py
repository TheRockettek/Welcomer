from rockutils import rockutils
import requests
import sys
import os

config = rockutils.load_json("data/bot_data.json")

cluster = sys.argv[1]
argument = sys.argv[2]

def send(op):
    if cluster != "IPC":
        try:
            requests.post(f"http://localhost:{config['ipc_port']}/pushstatus/{cluster}/{op}")
        except:
            pass

while True:
    rockutils.pprint(argument, prefix="Wrapper")
    send("1")
    try:
        exit_code = os.system(argument)
    except Exception as e:
        rockutils.pprint("Cluster has encountered fatal error and has to stop", prefix="Wrapper", prefix_colour="red")
        rockutils.pprint(str(e), prefix="Wrapper", prefix_colour="red", text_colour="light red")
        break

    if exit_code == 0:
        rockutils.pprint("Cluster has stopped", prefix="Wrapper", prefix_colour="red")
        send("0")
        break
    elif exit_code == 1:
        rockutils.pprint("Cluster is restarting", prefix="Wrapper", prefix_colour="green")
        send("1")
    elif exit_code == 2:
        rockutils.pprint("Cluster has hung", prefix="Wrapper", prefix_colour="yellow")
        send("4")
        input()