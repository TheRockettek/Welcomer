# Deprecated since move to Postgres

import rethinkdb
import time

_now = time.time()
r = rethinkdb.RethinkDB()
rethink = r.connect(host="localhost", port=28015, db="welcomer6")


def get_user_info(user):
    _id = user['id']
    fix = False
    expired = False

    if user:
        months = 1
        if _id in ["481895630252539935"]:
            months = 3
        if _id in []:
            months = 5

        expire = 6
        div = 6
        threshold = 2592000*6

        if user['m']['1']['h'] or user['m']['3']['h'] or user['m']['5']['h']:
            print(f"{_id}: {months} months")
            if user['m']['1']['u'] and (user['m']['1']['u'] - _now) > threshold:
                print(f"- x1: {(user['m']['1']['u'] - _now)/2592000} months")
                _days = user['m']['1']['u'] / (2592000 * (months * 31))
                newtime = _now + (86400*((31 * months) - _days))
                user['m']['1']['u'] = newtime

                if (user['m']['1']['u'] - _now)/2592000 < 0.5:
                    user['m']['1']['u'] = 0

                if (user['m']['1']['u'] - _now)/2592000 > expire or (user['m']['1']['u'] - _now)/2592000 < 0:
                    print("EXPIRED")
                    expired = True

                print(f"-> x1: {(user['m']['1']['u'] - _now)/2592000} months")
                fix = True
            if user['m']['3']['u'] and (user['m']['3']['u'] - _now) > threshold:
                print(f"- x3: {(user['m']['3']['u'] - _now)/2592000} months")
                _days = user['m']['3']['u'] / (2592000 * (months * 31))
                newtime = _now + (86400*((31 * months) - _days))
                user['m']['3']['u'] = newtime

                if (user['m']['3']['u'] - _now)/2592000 < 0.5:
                    user['m']['3']['u'] = 0

                if (user['m']['3']['u'] - _now)/2592000 > expire or (user['m']['3']['u'] - _now)/2592000 < 0:
                    print("EXPIRED")
                    expired = True

                print(f"-> x3: {(user['m']['3']['u'] - _now)/2592000} months")
                fix = True
            if user['m']['5']['u'] and (user['m']['5']['u'] - _now) > threshold:
                print(f"- x5: {(user['m']['5']['u'] - _now)/2592000} months")
                _days = user['m']['5']['u'] / (2592000 * (months * 31))
                newtime = _now + (86400*((31 * months) - _days))
                user['m']['5']['u'] = newtime

                if (user['m']['5']['u'] - _now)/2592000 < 0.5:
                    user['m']['5']['u'] = 0

                if (user['m']['5']['u'] - _now)/2592000 > expire or (user['m']['5']['u'] - _now)/2592000 < 0:
                    print("EXPIRED")
                    expired = True

                print(f"-> x5: {(user['m']['5']['u'] - _now)/2592000} months")
                fix = True

            # user = r.table("users").get(_id).update(user).run(rethink)

    return fix, expired


docs = r.table("users").run(rethink)
fix = 0
exp = 0
for x in docs:
    a, b = get_user_info(x)
    if a:
        fix += 1
    if b:
        exp += 1

print("Need to fix memberships for ", fix,
      "users.", exp, "have expired memberships")
