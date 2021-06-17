from DataIO import dataIO
import os

total = len(os.listdir("Servers"))
current = 0
for ext in os.listdir("Servers"):
    ext = ext[:-5]
    if os.path.exists("Images/custom_" + ext + ".png"):
        info = dataIO.load_json("Servers/" + ext + ".json")
        info['welcomer']['background'] = "custom_" + ext
        dataIO.save_json("Servers/" + ext + ".json",info)
        print(str(current) + "/" + str(total) + " :" + ext)
    current += 1