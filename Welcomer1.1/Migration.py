from DataIO import dataIO
import os

total = len(os.listdir("Servers"))
current = 0
for ext in os.listdir("Servers"):
    info = dataIO.load_json("Servers/" + ext)
    info['autorole']['roleid'] = str(info['autorole']['roleid'])
    info['logging']['channel'] = str(info['logging']['channel'])
    dataIO.save_json("Servers/" + ext,info)
    current += 1
    print(str(current) + "/" + str(total) + " :" + ext)