import asyncio, discord, json, io, math
from discord.ext import commands

def tableSet(table,value,key):
    newtable = table
    args = "newtable"
    for val in value.split("."):
        args += "['" + val + "']"
    args += " = " + str(key)
    exec(args)
    return newtable

def tableGet(table,value):
    try:
        newtable = table
        args = "newtable"
        for val in value.split("."):
            args += "['" + val + "']"
        return eval(args)
    except:
        return None

def setserverconfig(table,value,key):
    val = tableGet(table,value)
    if type(val) == int:
        tableSet(table,value,int(key))
    elif type(val) == str:
        tableSet(table,value,str(key))
    elif type(val) == bool:
        tableSet(table,value,(key.lower() == "true"))
    else:
        return False
    return True

def nicify(i,t,stri):
    if i == 0:
        stri = ""
    for key, value in t.items():
        if type(value) == dict:
            stri += " "*(i-1) + " " + key + ":\n"
            i += 1
            stri = nicify(i+1,value,stri)
            i -= 1
        else:
            stri += " "*(i-1) + " " + key + ": " + str(value) + "\n"
    return stri

def cut(table, start, end):
    return list(k for i,k in table if i >= start and i <= end)

class SupportHandler():

    def __init__(self, bot):
        self.bot = bot


    @commands.group()
    async def sup(self, ctx):
        if await self.bot.is_operator(ctx.author, False):
            if ctx.invoked_subcommand is None:
                await ctx.send(":mag: __**Support commands usage**__\nsup <ssearch/usearch/sconfig/ssconfiguconfig/ulookup/slookup/sinv>\n- ssearch <term> [page]: Search for a server by term\n- usearch <term>: Search for a user by term\n- sconfig <server id>: Return a servers config\n- ssconfig <server id> <key> <value>: Change a servers config\n- uconfig <user id>: Return a users config\n- ulookup <user id>: Find mutual servers with a user\n- slookup <server id>: Find information on a discord server\n- sinv <server id>: Get an invite to a server")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="ssearch")
    async def ssearchsu(self, ctx, term : str, page = 1):
        if await self.bot.is_operator(ctx.author, False):
            """
            s = ""
            r = 0
            term = term.lower()
            for server in self.bot.guilds:
                if term in server.name.lower():
                    r += 1
                    if r <= 10*page:
                        result = r % 10
                        dpage = ((r-result)/10)
                        if r >= (((page-1)*10)+1) and r <= (page*10):
                            us = 0
                            bo = 0
                            for member in server.members:
                                if member.bot == True:
                                    bo += 1
                                us += 1
                            s += str(r) + ") " + server.name + " `" + str(server.id) + "` | T**" + str(us) + "** / B**" + str(us-bo) + "** / B**" + str(bo) + "** | **" + str(math.floor(bo/us*10000)/100) + "%**\n"
            """
            if self.bot.TEST_MODE == False:
                ClusterResp = False
                Error = False
                if "SyncHandler" in self.bot.cogs:
                    if "broadCast" in dir(self.bot.cogs['SyncHandler']):
                        try:
                            res, ttf = await self.bot.cogs['SyncHandler'].broadCast(2,"*", "")
                            ret = list()
                            for k in res:
                                print(k)
                                ret.insert(len(ret),k)
                            print(ret)
                            ClusterResp = True
                        except Exception as e:
                            print(str(e) )
                            ClusterResp = True
                            Error = True
            else:
                ret = list(k for k in self.bot.guilds if term.lower() in k.name.lower())
            print(ret)
            servers = cut(ret, (page*10)-9, (page*10))
            serverlist = ""
            for k in servers:
                totalusers = str(len(list(m for l,m in k.members.items())))
                botcount = str(len(list(p for q,p in k.members.items() if k.bot == True)))
                membercount = str(len(list(o for n,o in k.members.items() if k.bot == False)))
                serverlist += f"**{k.name}** `{str(k.id)}` | T **{totalusers}** | M **{membercount}** | B **{botcount}**\n"
            await ctx.send(f":mag: Page {str(page)}/{str(math.ceil(r/10))} | **{str(len(servers))}** results | Showing results **{str((page*10)-9)}** to **{str((page*10))}**\n{serverlist}" if len(servers) > 0 else ":mag: No results found")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="usearch")
    async def usearchsu(self, ctx, term : str, page = 1):
        if await self.bot.is_operator(ctx.author, False):
            s = ""
            r = 0
            term = term.lower()
            for user in self.bot.users:
                if term in user.name.lower():
                    r += 1
                    if r <= 10*page:
                        result = r % 10
                        dpage = ((r-result)/10)
                        if r >= (((page-1)*10)+1) and r <= (page*10):
                            us = 0
                            bo = 0
                            mu = 0
                            for server in self.bot.guilds:
                                for member in server.members:
                                    if member == user:
                                        mu += 1
                            s += str(r) + ") " + str(user).lower() + " `" + str(user.id) + "` | **" + str(mu) + "** mutual servers\n"
            if len(s) == 0:
                t = ":mag: No results found"
            else:
                t = ":mag: Page " + str(page) + "/" + str(math.ceil(r/10)) + " | **" + str(r) + "** results | Showing results **" + str((((page-1)*10)+1)) + "** to **" + str((page*10)) + "**\n" + s
            await ctx.send(t)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="sconfig")
    async def sconfigsu(self, ctx, serverid : str, key = ""):
        if serverid == "^":
            serverid = ctx.guild.id
        if await self.bot.is_operator(ctx.author, False):
            serverData = await self.bot.get_guild_info(serverid)
            if key == "":
                await ctx.send(file=discord.File(io.StringIO(json.dumps(serverData)),"serverconfig.txt"))
            else:
                await ctx.send(":mag: " + key + ": " + str(tableGet(serverData,key)))
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="ssconfig")
    async def ssconfigsu(self, ctx, serverid : str, key : str, value : str):
        if serverid == "^":
            serverid = ctx.guild.id
        if await self.bot.is_operator(ctx.author, False):
            serverData = await self.bot.get_guild_info(serverid)
            work = setserverconfig(serverData,key,value)
            await self.bot.update_guild_info(serverid, serverData)
            await ctx.send(":mag: Assigned **" + key + "** to `" + str(tableGet(serverData,key)) + "`")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="uconfig")
    async def uconfigsu(self, ctx, userid : str, key = ""):
        if await self.bot.is_operator(ctx.author, False):
            userData = await self.bot.get_user_info(userid)
            if key == "":
                await ctx.send(file=discord.File(io.StringIO(json.dumps(userData)),"userconfig.txt"))
            else:
                await ctx.send(":mag: " + key + ": " + tableGet(userData,key))
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="ulookup")
    async def ulookupsu(self, ctx, userid : str, page = 1):
        if await self.bot.is_operator(ctx.author, False):
            s = ""
            r = 0
            m = dict()
            for server in self.bot.guilds:
                for member in server.members:
                    if str(member.id) == userid:
                        m[len(m)+1] = server
            print(m)
            for key,server in m.items():
                print(key)
                print(server)
                r += 1
                if r <= 10*page:
                    result = r % 10
                    dpage = ((r-result)/10)
                    if r >= (((page-1)*10)+1) and r <= (page*10):
                        us = 0
                        bo = 0
                        for member in server.members:
                            if member.bot == True:
                                bo += 1
                            us += 1
                        s += str(r) + ") " + server.name + " `" + str(server.id) + "` | T**" + str(us) + "** / B**" + str(us-bo) + "** / B**" + str(bo) + "** | **" + str(math.floor(bo/us*10000)/100) + "%**\n"
            if len(s) == 0:
                t = ":mag: No results found"
            else:
                t = ":mag: Page " + str(page) + "/" + str(math.ceil(r/10)) + " | **" + str(r) + "** results | Showing results **" + str((((page-1)*10)+1)) + "** to **" + str((page*10)) + "**\n" + s
            await ctx.send(t)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="slookup")
    async def slookupsu(self, ctx, serverid : int):
        if serverid == "^":
            serverid = ctx.guild.id
        if await self.bot.is_operator(ctx.author, False):
            server = await self.bot.get_guild(serverid)
            if server is None:
                await ctx.send(":mag: Could not find that server")
            else:
                serverinfo = ""
                us = 0
                bo = 0
                for member in server.members:
                    if member.bot == True:
                        bo += 1
                    us += 1
                serverinfo = ":mag: Server Info\n"
                serverinfo += "Total Users: **" + str(bo+us) + "**\n"
                serverinfo += "Humans: **" + str(us) + "**\n"
                serverinfo += "Bots: **" + str(bo) + "**\n"
                serverinfo += "Bot Ratio: **" + str(math.ceil((bo/us)*10000)/100) + "**\n"
                serverinfo += "Owner: **" + str(server.owner) + "** `" + str(server.owner.id) + "`"
                await ctx.send(serverinfo)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @sup.command(name="sinv")
    async def sinvsu(self, ctx, serverid : str):
        if serverid == "^":
            serverid = ctx.guild.id
        if await self.bot.is_operator(ctx.author, False):
            guild = self.bot.get_guild(int(serverid))
            def f(e):
                return e.position
            sortd = sorted(guild.channels, key=f, reverse=True)
            for chan in sortd:
                if type(chan) == discord.channel.TextChannel:
                    try:
                        invite = await chan.create_invite()
                        await ctx.send(":mag: Invite link: " + str(invite))
                        return
                    except Exception as e:
                        print(e)
            await ctx.send(":mag: Failed to obtain an invite link")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

def setup(bot):
    bot.add_cog(SupportHandler(bot))