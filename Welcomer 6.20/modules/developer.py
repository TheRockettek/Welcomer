import time
import typing
from io import StringIO, BytesIO

import aiohttp
import discord
import yaml
from collections import Counter
import io
from datetime import datetime
from discord.ext import commands
# from guppy import hpy
from rockutils import customchecks, rockutils
from pympler import summary, muppy
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import ujson as json
import operator
import collections
import os


class DeveloperCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="dev",
        description="cogs|Commands for use with development",
        brief="developer|admin",
        case_insensitive=True,
        invoke_without_command=True)
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @commands.Cog.listener()
    async def on_socket_response(self, msg):
        self.bot.socket_stats[msg.get('t')] += 1
        self.bot.socket_stats_size[msg.get('t')] += len(msg)

    @dev.command(
        name="broadcast",
        description="<opcode> <recep>|send ipc"
    )
    async def dev_broadcast(self, ctx, opcode, recp):
        resp = await self.bot.broadcast(opcode, recp)
        res = json.dumps(resp)
        if len(res) > 2000:
            await ctx.send(file=discord.File(io.StringIO(res), "output.json"))
        else:
            await ctx.send(res)

    @dev.command(
        name="istats",
        description="...|vnstati"
    )
    async def dev_istats(self, ctx):
        if os.path.exists("vnstati.png"):
            os.remove("vnstati.png")
        os.system("vnstati -i enp8s0 -o vnstati.png -s")
        with open("vnstati.png", "rb") as f:
            await ctx.send(file=discord.File(f))

    @dev.command(
        name="playing",
        description="...|Changes bots presence"
    )
    async def dev_playing(self, ctx, *, text):
        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("change_presence", "*", text)
        message = ""
        for cluster_id, cluster_data in response['d'].items():
            # if cluster_data:
            #     message += f"{self.bot.get_emote('check')}  | Cluster **{cluster_id}**: Success`\n"
            # else:
            if not cluster_data:
                message += f"{self.bot.get_emote('cross')}  | Cluster **{cluster_id}**: {cluster_data}`\n"

        await _m.edit(content=message)

    @dev.command(
        name="fmemoryusage",
        description="|Fast Memory usage"
    )
    async def dev_fmemoryusage(self, ctx):
        _heap = summary.summarize(muppy.get_objects())
        _sort = sorted(_heap, key=lambda o: o[2], reverse=True)

        html = "<table style=\"width:100%\"><tr><th>Name</th><th>Occur</th><th>Size</th></tr>"
        for sort in _sort:
            html += f"<tr><th>{sort[0]}</th><th>{sort[1]}</th><th>{sort[2]}</th></tr>"
        html += "</table>"
        await ctx.send(file=discord.File(StringIO(html), "memory.html"))
        await ctx.send(file=discord.File(StringIO(str(_sort)), "raw.list"))

    # @dev.command(
    #     name="memoryusage",
    #     description="|Memory usage"
    # )
    # async def dev_memoryusage(self, ctx):
    #     h = await self.bot.loop.run_in_executor(None, hpy)
    #     _heap = await self.bot.loop.run_in_executor(None, h.heap)
    #     await ctx.send(f"```{_heap}```")

    # @dev.command(
    #     name="fb",
    #     description="|"
    # )
    # async def dev_fb(self, ctx, g: int, m: int):
    #     guild = await self.bot.fetch_guild(g)
    #     ban = await guild.fetch_ban(self.bot.get_user(m))
    #     await ctx.send(str(ban))

    # @dev.command(
    #     name="dm",
    #     description="|Tells a user they have mail from you in dm"
    # )
    # async def dev_dm(self, ctx, m: int):
    #     user = await self.bot.fetch_user(m)
    #     await user.send(f":mailbox_with_mail: | You have received mail from `{ctx.author}`")

    @dev.command(
        name="socketstats",
        description="|Socket stats"
    )
    async def dev_socketstats(self, ctx):
        async with aiohttp.ClientSession() as _session:
            async with _session.get(f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/status") as r:
                print(await r.text())
                response = await r.json()
                _socket_stats = response['socketstats']['totalevents']
                socket_stats = dict(
                    zip(_socket_stats.keys(), map(int, _socket_stats.values())))

        sorted_x = sorted(socket_stats.items(), key=lambda o: o[1])
        sorted_dict = dict(sorted_x)

        total = sum(sorted_dict.values())
        cpm = float(response['socketstats']['average'])
        newline = "\n"
        await ctx.send(f'{total} socket events observed ({cpm:.2f}/minute):\n```{newline.join([f"{i}: {v}" for i,v in sorted_dict.items()])}```')

    @dev.command(
        name="socketstatsgraph",
        description="|Socket stats"
    )
    async def dev_graphsocketstats(self, ctx, scale=None):
        # _stats = sorted(self.bot.socket_stats.items(), key=lambda o: o[1], reverse=True)[:5]
        plt.rcdefaults()
        plt.rcParams["figure.figsize"] = [12.8, 4.8]

        async with aiohttp.ClientSession() as _session:
            async with _session.get(f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/status") as r:
                response = await r.json()

                _stats = sorted(
                    response['socketstats']['totalevents'].items(),
                    key=lambda o: o[1],
                    reverse=True)[
                    :10]
                # keys = socketstats.keys()
                # values = list(map(int, socketstats.values()))

        keys = list(map(lambda o: o[0], _stats))
        values = list(map(lambda o: int(o[1]), _stats))
        y_pos = np.arange(len(keys))

        plt.bar(y_pos, values, align='center', alpha=0.5, color="red")
        plt.xticks(y_pos, keys, rotation=30, horizontalalignment='right')
        plt.ylabel('Discord Events')
        if scale not in ['linear', 'log', 'symlog', 'logit']:
            scale = "log"
        plt.yscale(scale)
        plt.title('Socket Event Stats')
        _bio = BytesIO()
        plt.savefig(_bio, format="png", transparent=False, bbox_inches='tight')
        plt.clf()
        _bio.seek(0)
        file = discord.File(_bio, filename="output.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://output.png")
        await ctx.send(file=file, embed=embed)

    @dev.command(
        name="socketstatspie",
        description="|Socket stats"
    )
    async def dev_piesocketstats(self, ctx):
        # _stats = sorted(self.bot.socket_stats.items(), key=lambda o: o[1], reverse=True)[:5]
        plt.rcdefaults()
        plt.rcParams["figure.figsize"] = [8, 4.8]

        async with aiohttp.ClientSession() as _session:
            async with _session.get(f"http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/api/status") as r:
                response = await r.json()

                _stats = sorted(
                    response['socketstats']['totalevents'].items(),
                    key=lambda o: o[1],
                    reverse=True)[
                    :10]
                # keys = socketstats.keys()
                # values = list(map(int, socketstats.values()))

        def func(pct, allvals):
            absolute = int(pct / 100. * np.sum(allvals))
            return "{:.1f}%\n({:d})".format(pct, absolute)

        keys = list(map(lambda o: o[0], _stats))
        values = list(map(lambda o: int(o[1]), _stats))
        fig, ax = plt.subplots(
            figsize=(8, 4.8), subplot_kw=dict(aspect="equal"))
        wedges, texts, autotexts = plt.pie(
            values, autopct=lambda pct: func(pct, values))

        ax.legend(
            wedges,
            keys,
            title="Socket Event Stats",
            loc="center left",
            bbox_to_anchor=(
                1,
                0,
                0.5,
                1))

        plt.axis("equal")
        plt.title('Socket Event Stats')
        _bio = BytesIO()
        plt.savefig(_bio, format="png", transparent=False, bbox_inches='tight')
        plt.clf()
        _bio.seek(0)
        file = discord.File(_bio, filename="output.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://output.png")
        await ctx.send(file=file, embed=embed)

    @dev.command(name="givex5", description="...|Give users welcomer x5")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_givedonfive(self, ctx, *users):
        _time = time.time() + 2592000
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = True
            userinfo['m']['5']['h'] = True
            userinfo['m']['5']['p'] = True
            userinfo['m']['5']['u'] = _time

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="givex3", description="...|Give users welcomer x3")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_givedonthree(self, ctx, *users):
        _time = time.time() + 2592000
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = True
            userinfo['m']['3']['h'] = True
            userinfo['m']['3']['p'] = True
            userinfo['m']['3']['u'] = _time

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="givex1", description="...|Give users welcomer x1")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_givedonone(self, ctx, *users):
        _time = time.time() + 2592000
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = True
            userinfo['m']['1']['h'] = True
            userinfo['m']['1']['p'] = True
            userinfo['m']['1']['u'] = _time

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="givepart", description="...|Give users partner")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_givepart(self, ctx, *users):
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = True
            userinfo['m']['p'] = True

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="givecbg", description="...|Give users custom background")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_givecbg(self, ctx, *users):
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = True

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="removedon", description="...|Removes users welcomer x5")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_removedon(self, ctx, *users):
        # _time = time.time() + 2592000
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = False
            userinfo['m']['5']['h'] = False
            userinfo['m']['5']['p'] = False
            userinfo['m']['5']['u'] = 0

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="removepart", description="...|Removes users partner")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_removepart(self, ctx, *users):
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = False
            userinfo['m']['p'] = False

            await self.bot.set_value("users", str(userid), userinfo)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="removecbg", description="...|Removes users custom background")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_removecbg(self, ctx, *users):
        for userid in users:
            userinfo = await self.bot.get_user_info(int(userid))
            userinfo['m']['hs'] = False

            await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
            # await r.table("users").get(str(userid)).update(userinfo).run(self.bot.connection)
        await ctx.send("Done")

    @dev.command(name="mreloadall", description="|Reloads all modules")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_mreloadall(self, ctx):
        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("modulesreloadall", "*")
        message = ""
        for cluster_id, cluster_data in response['d'].items():
            # if cluster_data['success']:
            #     message += f"{self.bot.get_emote('check')}  | Cluster **{cluster_id}**: Loaded `{len(cluster_data['loaded'])}/{len(cluster_data['loaded']) + len(cluster_data['failed'])}`\n"
            # else:
            if not cluster_data['success']:
                message += f"{self.bot.get_emote('cross')}  | Cluster **{cluster_id}**: `{cluster_data['error']}`\n"
        await _m.edit(content=message)

    @dev.command(name="mreload", description="<module>|Reloads a modules")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_mreload(self, ctx, module):
        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("modulesreload", "*", module)
        message = ""
        for cluster_id, cluster_data in response['d'].items():
            # if cluster_data['success']:
            #     message += f"{self.bot.get_emote('check')}  | Cluster **{cluster_id}**: Reloaded successfully"
            # else:
            if not cluster_data['success']:
                message += f"{self.bot.get_emote('cross')}  | Cluster **{cluster_id}**: `{cluster_data['error']}`\n"
        await _m.edit(content=message)

    @dev.command(name="mload", description="<module>|Loads a modules")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_mload(self, ctx, module):
        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("modulesload", "*", module)
        message = ""
        for cluster_id, cluster_data in response['d'].items():
            # if cluster_data['success']:
            #     message += f"{self.bot.get_emote('check')}  | Cluster **{cluster_id}**: Loaded successfully"
            # else:
            if not cluster_data['success']:
                message += f"{self.bot.get_emote('cross')}  | Cluster **{cluster_id}**: `{cluster_data['error']}`\n"
        await _m.edit(content=message)

    @dev.command(name="munload", description="<module>|Unloads a modules")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_munload(self, ctx, module):
        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("modulesunload", "*", module)
        message = ""
        for cluster_id, cluster_data in response['d'].items():
            # if cluster_data['success']:
            #     message += f"{self.bot.get_emote('check')}  | Cluster **{cluster_id}**: Unloaded successfully"
            # else:
            if not cluster_data['success']:
                message += f"{self.bot.get_emote('cross')}  | Cluster **{cluster_id}**: `{cluster_data['error']}`\n"
        await _m.edit(content=message)

    @dev.command(name="eval", description="...|Evaluates an expression")
    @customchecks.requires_special_elevation(developer=True)
    async def dev_eval(self, ctx, *, text):
        try:
            fas = False
            if text[:2] == "-a":
                fas = True
                e = eval(text[3:])
            else:
                e = eval(text)
            if fas or (str(type(e)) == "<class 'generator'>") or (
                    "<coroutine object" in str(type(e))) or (
                    "<generator object" in str(type(e))):
                r = await e
                try:
                    await ctx.send(r)
                except BaseException:
                    await ctx.send("`" + str(e) + "`")
            else:
                await ctx.send(e)
        except Exception as e:
            await ctx.send("`" + str(e) + "`")

    @dev.command(name="status", description="|Returns all cluster status")
    @customchecks.requires_special_elevation(developer=True, admin=True)
    async def dev_status(self, ctx):
        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        async with aiohttp.ClientSession() as _session:
            async with _session.get(f"http://127.0.0.1:{self.bot.config['ipc']['port']}/api/internal-status") as r:
                response = await r.json()
                message = ""
                _status_name = {
                    0: "Connecting",
                    1: "Ready",
                    2: "Restarting",
                    3: "Hung",
                    4: "Resuming",
                    5: "Stopped"
                }

                for cluster_id, status in response.items():
                    message += f"Cluster **{cluster_id}**: {_status_name.get(status, f'Unknown status id {status}')}\n"
                await _m.edit(content=message)

    @commands.group(
        name="admin",
        description="wrench|Commands for use when supporting users",
        brief="developer|admin|support",
        case_insensitive=True,
        invoke_without_command=True)
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    async def admin(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @admin.command(
        name="config-export",
        description="[id]|Exports the config of the specified guild. Will export current guild if no guild specified")
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    @customchecks.requires_guild()
    async def admin_config_export(self, ctx, guild: typing.Optional[int] = None):
        if self.bot.get_guild(guild):
            guild_info = await self.bot.get_guild_info(guild.id)
        else:
            guild_info = ctx.guildinfo
        await ctx.send(file=discord.File(StringIO(yaml.dump(guild_info)), filename="guild-info.yml"))

    @admin.command(
        name="config-reset",
        description="[confirmation]|Resets the config of the server this command is ran on")
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    @customchecks.requires_guild()
    async def admin_config_reset(self, ctx, id=None):
        if id != hex(ctx.guild.id)[2:15]:
            message = f"As this command is destructive, please append `{hex(ctx.guild.id)[2:15]}` to the message. **Data is not restorable once removed unless exported**"
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
        try:
            await r.table("guilds").get(str(ctx.guild.id)).delete().run(self.bot.connection)
        except Exception as e:
            message = f"An error occured whilst running this command: {str(e)}"
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
        else:
            message = "Guild data has been successfully reset"
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)

    @admin.command(
        name="search",
        description="<guild/user> <name/id> <term>|Finds a guild or user based off term")
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    async def admin_search(self, ctx, stype=None, ttype=None, term=None):
        if stype not in ['guild', 'server', 'member', 'user']:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="search type",
                    expects="guild, user",
                    received=stype)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if ttype not in ['name', 'id']:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="term type",
                    expects="name, id",
                    received=ttype)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if term is None or len(term.strip()) < 1:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="term",
                    expects="string",
                    received=term)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if ttype == "id":
            canint, term = rockutils.canint(term)

            if not canint:
                message = rockutils._(
                    "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                    ctx).format(
                        argument_name="term id",
                        expects="id",
                        received=term)
                return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        message = ""
        if stype in ['guild', 'server']:
            response = await self.bot.broadcast("guildsfind", "*", args=[0 if ttype == "id" else 1, term])
            guilds = {}
            for cluster_id, cluster_data in response['d'].items():
                if cluster_data['success']:
                    if ttype == "id" and cluster_data['results'] != []:
                        guilds[term] = cluster_data['results']
                    else:
                        for guild in cluster_data['results']:
                            guilds[guild['id']] = guild
            guilds = list(guilds.values())

            message = ""
            for number, result in enumerate(
                    sorted(guilds, key=lambda o: o['users'], reverse=True)[:20]):
                sub_message = f"**{number+1}**) **{result['name']}** - **{result['users']}** members [Guild Info](http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/g/{result['id']}) [Invite](http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/i/{result['id']}) `{result['id']}`\n"
                if len(message) + len(sub_message) > 2048:
                    await self.bot.send_data(ctx, message, ctx.userinfo, title=f"Search results for {stype} ({ttype}): {term}")
                    message = ""
                message += sub_message
            await self.bot.send_data(ctx, message, ctx.userinfo, title=f"Search results for {stype} ({ttype}): {term}")

        if stype in ['member', 'user']:
            response = await self.bot.broadcast("userfind", "*", args=[0 if ttype == "id" else 1, term])
            users = {}
            for cluster_id, cluster_data in response['d'].items():
                if cluster_data['success']:
                    if ttype == "id" and cluster_data['results'] != []:
                        users[term] = cluster_data['results']
                    else:
                        for user in cluster_data['results']:
                            users[user['id']] = user
            users = list(users.values())

            message = ""
            for number, result in enumerate(
                    sorted(
                        users,
                        key=lambda o: o['creation'])
                    [: 20]):
                sub_message = f"**{number+1}**) **{result['name']}#{result['discriminator']}** [Profile](http://{self.bot.config['ipc']['host']}:{self.bot.config['ipc']['port']}/p/{result['id']}) `{result['id']}`\n"
                if len(message) + len(sub_message) > 2048:
                    await self.bot.send_data(ctx, message, ctx.userinfo, title=f"Search results for {stype} ({ttype}): {term}")
                    message = ""
                message += sub_message
            await self.bot.send_data(ctx, message, ctx.userinfo, title=f"Search results for {stype} ({ttype}): {term}")

    @admin.command(
        name="invite",
        description="<guild id>|Creates an invite for a specified guild")
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    async def admin_invite(self, ctx, _id: typing.Optional[int] = None):

        canint, _id = rockutils.canint(_id)

        if not canint:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="guild id",
                    expects="number",
                    received=_id)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("guildinvite", "*", _id)
        message = ""
        for cluster_id, cluster_data in response['d'].items():
            if cluster_data['success']:
                message += f"{self.bot.get_emote('check')}  | Cluster **{cluster_id}**: https://discord.gg/{cluster_data['invite']}"
            # else:
            #     message += f"{self.bot.get_emote('cross')}  | Cluster **{cluster_id}**: `{cluster_data['error']}`"
        await _m.edit(content=message)

    @admin.command(
        name="leave",
        description="<guild id>|Leave a specified guild")
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    async def admin_leave(self, ctx, _id: typing.Optional[int] = None):

        canint, _id = rockutils.canint(_id)

        if not canint:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="guild id",
                    expects="number",
                    received=_id)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        guild = await self.bot.fetch_guild(_id)
        await guild.leave()
        await ctx.send("Done :)")

    @admin.command(
        name="info",
        description="<guild id>|Returns serialised information for a specific guild")
    @customchecks.requires_special_elevation(
        support=True, developer=True, admin=True)
    async def admin_info(self, ctx, _id: typing.Optional[int] = None):
        canint, _id = rockutils.canint(_id)

        if not canint:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="guild id",
                    expects="number",
                    received=_id)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        _m = await ctx.send(f"{self.bot.get_emote('loading')}")
        response = await self.bot.broadcast("guildsfind", "*", args=[0, _id])
        message = ""
        guild = None
        for cluster_id, cluster_data in response['d'].items():
            if cluster_data['success']:
                guild = cluster_data['results']

        if guild:
            longest = max(len(k) for k in guild.keys())
            for key, value in guild.items():
                message += f"{' '*(longest-len(key))}{key}: {value}\n"
        else:
            message = "Failed to retrieve information for this guild"
        await _m.edit(content=f"```{message}```")


def setup(bot):
    if not hasattr(bot, 'uptime'):
        bot.uptime = datetime.utcnow()

    if not hasattr(bot, 'socket_stats'):
        bot.socket_stats = Counter()
    if not hasattr(bot, 'socket_stats_size'):
        bot.socket_stats_size = Counter()

    bot.add_cog(DeveloperCommands(bot))
