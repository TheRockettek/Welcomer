import asyncio, discord, time, math
from discord.ext import commands
import rethinkdb as r

#opcodes

"""
0 - HEARTBEAT
1 - RELOAD_CONFIG
2 - SEARCH_SERVER_STR
3 - SEARCH_SERVER_INT
4 - SEARCH_USER_STR
5 - SEARCH_USER_INT
6 - CREATE_INVITE_INT

7 - MODULE_RELOAD
8 - MODULE_LOAD
9 - MODULE_UNLOAD
10 - MODULE_RELOADALL
11 - GET_ELEVATED
"""


class SyncHandler():

    def __init__(self, bot):
        self.bot = bot
        self.running = False

    @commands.command()
    async def sync(self, ctx):
        m = await ctx.send("<a:loading:393852367751086090>")
        userinfo = await self.bot.get_user_info(ctx.author.id)
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id == ctx.author.id:
                    if not str(guild.id) in userinfo['stats']['elevatedon']:
                        if self.bot.TEST_MODE == False:
                            ClusterResp = False
                            Error = False
                            if "SyncHandler" in self.bot.cogs:
                                if "broadCast" in dir(bot.cogs['SyncHandler']):
                                    try:
                                        res, ttf = await self.bot.cogs['SyncHandler'].broadCast(11,"*", id)
                                        elev = dict()
                                        for clusterid, clusterdata in res.items():
                                            for serverid, elevated in clusterdata.items():
                                                elev[str(serverid)] = elevated
                                        userinfo['stats']['elevatedon'] = elev
                                        ClusterResp = True
                                    except Exception as e:
                                        ClusterResp = True
                                        Error = True
                    userinfo['stats']['elevatedon'][str(guild.id)] = await self.bot.has_elevated_roles(self, member, guild.id)
        await self.bot.update_user_info(member.id, userinfo)
        await ctx.send(content="Done")

    async def on_member_join(self, member):
        userinfo = await self.bot.get_user_info(member.id)
        userinfo['stats']['elevatedon'][str(member.guild.id)] = await self.bot.has_elevated_roles(self, member, member.guild.id)
        await self.bot.update_user_info(member.id, userinfo)

    async def on_member_remove(self, member):
        userinfo = await self.bot.get_user_info(member.id)
        if str(member.guild.id) in userinfo['stats']['elevatedon']:
            del userinfo['stats']['elevatedon'][str(member.guild.id)]
        await self.bot.update_user_info(member.id, userinfo)

    async def on_member_update(self, before, after):
        update = False
        for attr in dir(before):
            if attr[0] != "_":
                if before.__getattribute__(attr) != after.__getattribute__(attr):
                    if attr == "roles":
                        update = True
                        break
        if update == False:
            return
        userinfo = await self.bot.get_user_info(before.id)
        userinfo['stats']['elevatedon'][str(before.guild.id)] = await self.bot.has_elevated_roles(self, after, before.guild.id)
        await self.bot.update_user_info(before.id, userinfo)

    async def on_connect(self):
        if self.running == False:
            self.running = True
            while True:
                await asyncio.sleep(0.5)
                await self.getRequests()

    async def getRequests(self):
            cursor = await r.db("welcomer").table("crosscommunication").run(self.bot.connection)
            for request in cursor.items:
                if self.bot.CLUSTER_ID in request['OUT']:
                    print("Task from " + str(request['be']) + " (id " + str(request['id']) + ") with opcode " + str(request['OP']) + " to " + str(request['OUT']))
                    id = request['id']
                    if "ARGS" in request:
                        print("Args: " + str(request['ARGS']))
                    tabledata = dict()

                    if request['OP'] == 0:
                        # ping
                        tabledata = time.time()

                    if request['OP'] == 1:
                        # reload data
                        tabledata = self.bot.reload_data()

                    elif request['OP'] == 2:
                        # get guild str
                        tabledata = list({"name": guild.name, "id": guild.id, "members": len(set(member for member in guild.members if member.bot == False)), "bots": len(set(member for member in guild.members if member.bot == True)), "owner": str(guild.owner), "ownerid": guild.owner.id} for guild in self.bot.guilds if request['ARG'].lower() in guild.name.lower())

                    elif request['OP'] == 3:
                        # get guild id
                        guild = self.bot.get_guild(int(request['ARG']))
                        tabledata = {"name": guild.name, "id": guild.id, "members": len(set(member for member in guild.members if member.bot == False)), "bots": len(set(member for member in guild.members if member.bot == True)), "owner": str(guild.owner), "ownerid": guild.owner.id}

                    elif request['OP'] == 4:
                        # get user str
                        for guild in self.bot.guilds:
                            for member in guild.members:
                                if request['ARG'].lower() in member.name.lower():
                                    if not str(member.id) in tabledata:
                                        tabledata = {"name": str(member), "id": member.id, "avatar": member.avatar_url or member.default_avatar_url, "mutual": dict()}
                                    tabledata['mutual'][str(guild.id)] = {"name": guild.name, "id": guild.id, "members": len(set(member for member in guild.members if member.bot == False)), "bots": len(set(member for member in guild.members if member.bot == True)), "owner": str(guild.owner), "ownerid": guild.owner.id}

                    elif request['OP'] == 5:
                        # get user id
                        user = self.bot.get_user(int(request['ARG']))
                        if user:
                            tabledata = {"name": str(user), "id": user.id, "avatar": user.avatar_url or user.default_avatar_url, "mutual": dict()}
                            for guild in self.bot.guilds:
                                for member in guild.members:
                                    if int(request['ARG']) == member.id:
                                        tabledata['mutual'][str(guild.id)] = {"name": guild.name, "id": guild.id, "members": len(set(member for member in guild.members if member.bot == False)), "bots": len(set(member for member in guild.members if member.bot == True)), "owner": str(guild.owner), "ownerid": guild.owner.id}

                    elif request['OP'] == 6:
                        # createinvite
                        guild = self.bot.get_guild(int(request['ARG']))
                        if guild:
                            allchannels = sorted(guild.channels, key=lambda item: item.position)
                            channels = dict()
                            for channelinfo in allchannels:
                                if type(channelinfo) == discord.channel.TextChannel:
                                    channels[len(channels)] = channelinfo
                            for index, channel in channels.items():
                                invite = await channel.create_invite(unique=False)
                                if invite:
                                    tabledata = invite.code
                                    break

                    elif request['OP'] == 7:
                        # reload
                        tabledata = self.bot.modules.reload(request['ARG'])

                    elif request['OP'] == 8:
                        # load
                        tabledata = self.bot.modules.load(request['ARG'])

                    elif request['OP'] == 9:
                        # unload
                        tabledata = self.bot.modules.unload(request['ARG'])

                    elif request['OP'] == 10:
                        # reloadall
                        tabledata = self.bot.modules.reloadall()
                    
                    elif request['OP'] == 11:
                        # get elevated
                        # arg: userid
                        user = self.bot.get_user(int(request['ARG']))
                        if user != None:
                            for guild in self.bot.guilds:
                                for member in guild.members:
                                    if member.id == int(request['ARG']):
                                        tabledata[str(guild.id)] = await self.bot.has_elevated_roles(self, user, guild.id)
                    data = await r.table("crosscommunication").get(id).run(self.bot.connection)
                    data['IN'][str(self.bot.CLUSTER_ID)] = tabledata
                    data['OUT'].remove(self.bot.CLUSTER_ID)
                    await r.table("crosscommunication").get(id).update(data).run(self.bot.connection)

    @commands.command()
    async def test(self, ctx, opcode, receipitents, args):
        if await self.bot.is_operator(ctx.author):
            text, ttg = await self.bot.broadcast(self, int(opcode),receipitents,args)
            print(text)
            await ctx.send(str(ttg) + "ms\n" + str(text))

    @commands.command()
    async def opcode(self, ctx):
        await ctx.send("""
# OPCODES:

0 - HEARTBEAT
1 - RELOAD_CONFIG
2 - SEARCH_SERVER_STR
3 - SEARCH_SERVER_INT
4 - SEARCH_USER_STR
5 - SEARCH_USER_INT
6 - CREATE_INVITE_INT

7 - MODULE_RELOAD
8 - MODULE_LOAD
9 - MODULE_UNLOAD
10 - MODULE_RELOADALL
11 - GET_ELEVATED
""")

    async def broadCast(self, OP_CODE,RECEP,ARG):
        bt = time.time()
        if RECEP == "*":
            RECEP = list(range(0,self.bot.CLUSTER_COUNT+1))
        id = math.floor(time.time()*100)
        resp = await r.table("crosscommunication").insert({"be": self.bot.CLUSTER_COUNT, "id": id, "OP": OP_CODE, "OUT": RECEP, "ARG": ARG, "IN": {}}).run(self.bot.connection)
        table = await r.table("crosscommunication").get(id).run(self.bot.connection)
        while True:
            await asyncio.sleep(1)
            table = await r.table("crosscommunication").get(id).run(self.bot.connection)
            if (len(table['OUT']) == 1) or (math.ceil((time.time()-bt)*1000) >= 30000):
                await r.table("crosscommunication").get(id).delete().run(self.bot.connection)
                return table['IN'], math.ceil((time.time()-bt)*1000)

    @commands.command()
    async def sping(self, ctx):
        st = time.time()
        pings, ttg = await self.bot.broadcast(self, 0, "*", "")
        string = "Time to retrieve " + str(ttg) + "ms\n\nDelay\n"
        for item, ping in pings.items():
            string += "Cluster **" + str(item) + "**: " + str(math.ceil((ping-st)*1000)) + "ms\n"
        await ctx.send(string)

def setup(bot):
    setattr(bot, "broadcast", SyncHandler.broadCast)
    bot.add_cog(SyncHandler(bot))
