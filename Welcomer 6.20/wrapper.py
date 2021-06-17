from rockutils import rockutils
import sys
import time
import os

#argument = "LD_PRELOAD=/usr/local/lib/libjemalloc.so " + sys.argv[1]
argument = sys.argv[1]
while True:
    rockutils.prefix_print(argument, prefix="Wrapper")
    try:
        exit_code = os.system(argument)
    except Exception as e:
        rockutils.prefix_print(
            "Cluster has encountered fatal error and has to stop",
            prefix="Wrapper",
            prefix_colour="red")
        rockutils.prefix_print(
            str(e),
            prefix="Wrapper",
            prefix_colour="red",
            text_colour="light red")

    time.sleep(5)

    if exit_code == 100:
        rockutils.prefix_print("Cluster has stopped",
                               prefix="Wrapper", prefix_colour="red")
    elif exit_code == 101:
        rockutils.prefix_print("Cluster is restarting",
                               prefix="Wrapper", prefix_colour="green")
    elif exit_code == 102:
        rockutils.prefix_print(
            "Cluster has hung", prefix="Wrapper", prefix_colour="yellow")
        input()
