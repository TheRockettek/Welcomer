import os
import time
import math


def scrape(_dir):
    for file in os.listdir(_dir):
        file = os.path.join(_dir, file)
        if os.path.isdir(file):
            if "pycache" not in file:
                scrape(file)
        else:
            if file[-3:] == ".py":
                a = time.time()
                os.system(
                    f"autopep8 --experimental {'-a '*10} --max-line-length 100 -i {file}")
                b = time.time()
                print(f"{file} completed in {math.ceil((b-a)*1000)/1000} seconds")


scrape(".")
