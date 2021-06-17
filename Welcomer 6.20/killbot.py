import sys
import psutil
import os
import time

args = sys.argv
seconds = int(args[1])
clusters = args[2:]

print(f"Killing clusters: {clusters} with wait time: {seconds} [y/n]?")

if input() != "y":
    print("Aborted")
    exit()

print("Killing main bots")
for p in psutil.process_iter():
    cmdline = " ".join(p.cmdline())
    detatch = False
    if "sh -c pyston welcomer" in cmdline:
        raw = cmdline.replace("sh -c pyston welcomer.py", "").strip()
        if raw in clusters:
            detatch = True
            p.kill()
            print(f"Killed welcomer process {raw}")

    if "pyston welcomer.py" in cmdline and "sh" not in cmdline:
        raw = cmdline.replace("pyston welcomer.py", "").strip()
        if raw in clusters:
            detatch = True
            p.kill()

    if "python3.8 wrapper.py pyston welcomer.py" in cmdline:
        raw = cmdline.replace("python3.8 wrapper.py pyston welcomer.py", "").strip()
        if raw in clusters:
            detatch = True
            p.kill()
            print(f"Killed welcomer daemon {raw}")

    if detatch:
        os.system(f"screen -X -S Shard{raw} kill")
        print(f"Killed screen Shard{raw}")


print("Enter to startup")
input()
tasks = {}

for i in clusters:
    tasks[f"Shard{str(i)}"] = []
    tasks[f"Shard{str(i)}"].append("cd Welcomer\\ 6.0")
    tasks[f"Shard{str(i)}"].append(f"python3.8 wrapper.py 'pyston welcomer.py {i}'")

for screen_name, task_list in tasks.items():

    os.system(f"screen -dmS {screen_name}")
    print(f"created screen {screen_name}")

    for task in task_list:
        os.system(f"screen -S {screen_name} -X stuff \"{task}^M\"")
        print(f"ran task {task} on screen {screen_name}")

    if "Shard" in screen_name:
        time.sleep(seconds)
