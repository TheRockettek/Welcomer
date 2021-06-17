from discord.ext import commands
from datetime import datetime
from datetime import timezone
import discord, time, random, asyncio

class Developer():

    def __init__(self,bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def changename(self,ctx,name : str):
        if ctx.message.author.id == 143090142360371200:
            await self.bot.user.edit(username=name)
            await ctx.send("Changed name to " + name)

    @commands.command(pass_context=True)
    async def troll(self,ctx,users : str):
        """Tests welcome event (Bot owner only)"""
        if (ctx.message.author.id == 143090142360371200):
            si = random.randint(1,len(self.bot.guilds))
            for guild in self.bot.guilds:
                si -= 1
                if si == 0:
                    s = guild
            ui = int(users)
            siz = len(s.members)
            for member in s.members:
                if ui > 0:
                    member.guild = ctx.message.guild
                    member.guild.id = ctx.message.guild.id
                    for cog in self.bot.cogs:
                        try:
                            await self.bot.cogs[cog].on_member_join(member)
                        except:
                            0
                    await asyncio.sleep(random.randint(3,10))
                ui -= 1

    @commands.command(pass_context=True)
    async def guildlookup(self,ctx):
        """Checks for users that are less than a week old or on dbans"""
        newacc = 0
        banacc = 0
        ret = ""
        users = ctx.message.guild.members
        userl = str(len(users))
        msg = await ctx.send("Searching " + userl + " users...")
        for member in users:
            usr = ""
            w = False
            if "\"" + str(member.id) + "\"" in dbans:
                usr = usr + " \N{NO ENTRY}"
                w = True
                banacc = banacc + 1
            try:
                joinDate = datetime.datetime.strptime(str(member.created_at),"%Y-%m-%d %H:%M:%S.%f")
            except:
                joinDate = datetime.datetime.strptime(str(member.created_at),"%Y-%m-%d %H:%M:%S")
            currentDate = datetime.datetime.now(datetime.timezone.utc)
            currentDate = currentDate.replace(tzinfo=None)
            timeSinceJoining = currentDate - joinDate
            if timeSinceJoining.days < 7:
                usr = usr + " \N{WARNING SIGN}"
                w = True
                newacc = newacc + 1
            if w == True:
                ret = ret + usr + "`" + member.name + "#" + member.discriminator + "`\n"
        await self.bot.delete_message(msg)
        await ctx.send("Found " + str(newacc) + " new accounts and " + str(banacc) + " banned accounts")
        await ctx.send(ret)

    @commands.command(pass_context=True)
    async def dsearch(self,ctx,query : str):
        r = ""
        for guild in self.bot.guilds:
            if query in guild.name:
                r += guild.name + " | " + str(guild.id) + " | " + str(len(guild.members)) + "\n"
        if len(r) != 0:
            await ctx.send(r)
        else:
            await ctx.send("No results.")

    @commands.command(pass_context=True)
    async def invite(self,ctx):
        """Invite the bot to your guild"""
        await ctx.send("https://discordbots.org/bot/330416853971107840.\nWhy not also join our new discord guild: https://discord.gg/FeYfR9b")

    @commands.command(pass_context=True)
    async def supportinvite(self,ctx):
        """Get an invite to the support guild"""
        await self.bot.send_message(ctx.message.author,"https://discord.gg/FeYfR9b")

    @commands.command(pass_context=True)
    async def support(self,ctx):
        """Get help"""
        await ctx.send("What do you need help with (this will contact a staff member to come onto the guild)? Say cancel if this was a mistake. Do +supportinvite for a link to the support guild.")
        msg = await self.bot.wait_for('message', check=lambda u: u.author.id == ctx.message.author.id)
        print("MSG")
        if not "cancel" in msg.content.lower():
            await ctx.send("I have alerted the staff.")
            try:
                invite = await ctx.message.channel.create_invite()
            except:
                try:
                    invite = await ctx.message.guild.create_invite()
                except:
                    await ctx.send("I cant make an invite to your guild. I might not be able to get support here.")
            await self.bot.get_channel(341857855499927552).send("[" + str(ctx.message.channel.id) + "] <@143090142360371200> " + ctx.message.author.name + " from " + ctx.message.guild.name +" (" + str(ctx.message.guild.id) + ") needs your help:\n```" + msg.content + "```\n" + str(invite))

    @commands.command(pass_context=True)
    async def dinv(self,ctx,guildID : str):
            if (ctx.message.author.id == 143090142360371200) or str(ctx.author.id):
                guild = self.bot.get_guild(int(guildID))
                for channel in guild.channels:
                    break
                inv = await channel.create_invite()
                await ctx.send("https://discord.gg/" + inv.id)

    @commands.command(pass_context=True)
    async def dsize(self,ctx):
        micro = 0 #0-10
        small = 0 #11-50
        medium = 0 #51-200
        big = 0 #201-500
        massive = 0 #501-1000
        huge = 0 #1001+
        for guild in self.bot.guilds:
            size = len(guild.members)
            if size <= 10:
                micro += 1
            elif size >= 11 and size <= 50:
                small += 1
            elif size >= 51 and size <= 200:
                medium += 1
            elif size >= 201 and size <= 500:
                big += 1
            elif size >= 51 and size <= 1000:
                massive += 1
            elif size >= 1001:
                huge += 1
        await ctx.send("```Micro guilds [0-10]: " + str(micro) + "\nSmall guilds [11-50]: " + str(small) + "\nMedium guilds [51-200]: " + str(medium) + "\nBig guilds [201-500]: " + str(big) + "\nMassive guilds [501-1000]: " + str(massive) + "\nHuge guilds [1001+]: " + str(huge) + "```") 

    @commands.command(pass_context=True)
    async def dfind(self,ctx,biggerthan : str,smallerthan : str):
        stri = ""
        for guild in self.bot.guilds:
            a = len(guild.members)
            if a >= int(biggerthan) and a <= int(smallerthan):
                stri = stri + "\n" + str(guild.id) + " " + str(a) + " " + guild.name
        await ctx.send(stri)

    @commands.command(pass_context=True)
    async def dlook(self,ctx,id : str):
        l = ""
        se = 0
        for s in self.bot.guilds:
            for m in s.members:
                if m.id == int(id):
                    se += 1
                    if s.owner.id == id:
                        l = l + str(s.id) + " : " + s.name + " [O]\n"
                    else:
                        l = l + str(s.id) + " : " + s.name + "\n"
        await ctx.send(id + " is on " + str(se) + "guild(s) that im on.\n```" + l + "```")

    @commands.command(pass_context=True)
    async def dm(self,ctx,t : str):
        if (ctx.message.author.id == 143090142360371200):
            m = await self.bot.get_message(ctx.message.channel,t)
            await self.bot.delete_message(m)

    @commands.command(pass_context=True)
    async def dtell(self,ctx,channelID : str,msg : str):
        if (ctx.message.author.id == 143090142360371200):
            await self.bot.send_message(self.bot.get_channel(channelID),msg)

    @commands.command(pass_context=True)
    async def eval(self,ctx):
        """Does a thing (Bot owner only)"""
        if (ctx.message.author.id == 143090142360371200):
            try:
                e = eval(ctx.message.content[6:])
                print(e)
                print(str(type(e)))
                if str(type(e)) == "<class 'generator'>":
                    r = await e
                    try:
                        await ctx.send(r)
                    except:
                        0
                else:
                    await ctx.send(e)
            except:
                0

    @commands.command(pass_context=True)
    async def djointest(self,ctx):
        """Tests welcome event (Bot owner only)"""
        if (ctx.message.author.guild_permissions.administrator) or (str(ctx.message.author.id) in self.bot.specialRoles['staff']):
            for member in ctx.message.mentions:
                member.guild = ctx.message.guild
                for cog in self.bot.cogs:
                    try:
                        await self.bot.cogs[cog].on_member_join(member)
                    except Exception as e:
                        print(e)

    @commands.command(pass_context=True)
    async def clean(self,ctx):
        """Completely hardmless"""
        if (ctx.message.author.id == 143090142360371200):
            for user in ctx.message.mentions:
                def check(m):
                    return user.id == m.author.id
                try:
                    await ctx.message.channel.purge(limit=100, check=check, bulk=True)
                    await ctx.send(":wave: " + user.name)
                except:
                    0

    @commands.command(pass_context=True)
    async def hackclean(self,ctx,id : str):
        """Completely hardmless"""
        if (ctx.message.author.id == 143090142360371200):
            def check(m):
                return str(id) == str(m.author.id)
            m = await ctx.send("Deleting all traces of this user")
            d = await ctx.message.channel.purge(limit=10000, check=check, bulk=True)
            await m.edit(":wave: Deleted " + str(d) + " messages")

    @commands.command(pass_context=True)
    async def dperms(self,ctx):
        message = ""
        for permission in ctx.message.guild.me.guild_permissions:
            if permission[1] == True:
                message += permission[0] + "\n"
        await ctx.send("```" + message + "```")

def setup(bot):
    bot.add_cog(Developer(bot))