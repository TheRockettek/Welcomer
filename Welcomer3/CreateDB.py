"""
{
    "staff"
        "staffid"
    "servers"
        "0"
            "prefix": "+"
            "staff"
                0: true
            "whitelist"
                "e" #enabled
                "c" #channels
                    0: True
            "blacklist"
                "e" #enabled
                "c" #channels
            "autodelete"
                "in" #invites
                "me" #mentions
                "mt" #mention theshold
                "ur" #urls
                "em" #embed
                "pf" #swearing
                "br" #bot responces
                "rt" #bot timeout
            "welcomer"
                "e" #enabled
                "c" #channel
                "it" #imagetext
                "t" #text
                "b" #background
                "cc" #circle colour
                "tc" #text colour
                "sb" #show badges
                "ue" #use embed
                "sj" #show joindate
                "dt" #dm text
                "ud" #use dm
                "ui" #use image
                "ut" #use text
            "leaver"
                "e" #enabled
                "c" #channel
                "t" #text
            "autorole"
                "e" #enabled
                "r" #roleid
    "users"
        "0"
            "rep": 0 #reputation
            "bal": 0 #balance
            "gxp": 0 #global xp
            "pn": #previous names
                "Rock"
                "LeRock"
                "Rockeh"
            "bd": #badges
                "Support"
                "Developer"
                "Donator"
    "badges"
        "name"
            "n" #display name
            "e" #emoji
        "Support"
            "n": "**Welcomer Support Staff**"
            "e": ":shield:"
    "Records"
        "ci": 1 #current id
        "bans"
            "3"
                "a" #banned by
                "r" #banned reason
                "d" #date of ban
                "p" #is perm
                "s" #server id
        "warns"
        "mutes"
        "kicks"
}
"""

print("Hi")
import json
import rethinkdb as r
connection = r.connect("localhost", 28015)
#r.db("welcomer").table_create("staff").run(connection)
#r.db("welcomer").table("staff").insert({"id": 3,"snowflake":"abcd"}).run(connection)
r.db('welcomer').table('staff').replace(r.row.without(3)).run(connection)
u = r.db("welcomer").table("staff").run(connection)
for p in u:
    print(u)
print("Wew")