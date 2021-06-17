import asyncio, discord
from discord.ext import commands

def splitT(t,s,o):
    return list(k for i,k in t.items() if i >= s and i <= o)

class BadgeHandler():

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def badges(self, ctx):
        if await self.bot.is_operator(ctx.author, False):
            if ctx.invoked_subcommand is None:
                await ctx.send(":medal: __**Badge command usage**__\nsup <list/add/get/assign/deassign>\n- list: Lists all badges\n- add <badge name> <badge emoji>: Adds a new badge\n- get <mentioned user>: Gets badges a user has\n- assign <mentioned user> <badge id>: Gives a user a badge\n- deassign <mentioned user> <badge id>: Removes a users badge")
        else:
            if len(ctx.message.mentions) > 0:
                userinfo = await self.bot.get_user_info(ctx.message.mentions[0].id)
            else:
                userinfo = await self.bot.get_user_info(ctx.author.id)
            await ctx.send(f":medal: **{str(member)}'s badges**\n\n" + "".join(list((f"{self.bot.data['badges'][str(i)]['e']} **{self.bot.data['badges'][str(i)]['n']}**" if (str(i) in self.bot.data['badges']) else f":grey_question: Invalid Badge ID {str(i)}") for i,k in userinfo['badges'].items())))
            return

    @badges.command(name="list")
    async def listb(self, ctx):
        if await self.bot.is_operator(ctx.author, False):
            await ctx.send(f":medal: **Badges: list**\n" + "\n".join(list(f"{k['i']}) {k['e']} **{k['n']}** added by {(k.get('c'))}" for i,k in self.bot.data['badges'].items())))
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @badges.command(name="add")
    async def addb(self, ctx, name : str, emoji : str):
        if await self.bot.is_operator(ctx.author, False):
            id = len(self.bot.data['badges'])
            self.bot.data['badges'][str(id)] = {'n': name, 'e': emoji, 'c': str(ctx.author), 'i': id}
            self.bot.update_data()
            await ctx.send(f":medal: **Badges: add**\nAdded new badge (ID {str(id)}):\n{emoji} **{name}**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @badges.command(name="get")
    async def getb(self, ctx, member : discord.Member):
        userinfo = await self.bot.get_user_info(member.id)
        await ctx.send(f":medal: **{str(member)}'s badges**\n\n" + "\n".join(list((f"{self.bot.data['badges'][str(i)]['e']} **{self.bot.data['badges'][str(i)]['n']}**" if (str(i) in self.bot.data['badges']) else f":grey_question: Invalid Badge ID {str(i)}") for i,k in userinfo['badges'].items())))

    @badges.command(name="assign")
    async def assignb(self, ctx, member : discord.Member, badge : str):
        if await self.bot.is_operator(ctx.author, False):
            userinfo = await self.bot.get_user_info(member.id)
            if not badge in self.bot.data['badges']:
                badges = list(i for i,k in self.bot.data['badges'].items() if badge.lower() in k['n'].lower())
                if len(badges) > 1:
                    await ctx.send(f":medal: **{str(len(badge))}** results\n" + "\n".join(list(f"{k['e']} **{k['n']}**" for i,k in badges.items())))
                    return
                elif len(badges) == 0:
                    await ctx.send(":medal: **Badges: assign**\nNo badges with this id/name could be found")
                    return
                else:
                    badge = badges[0]
            userinfo['badges'][badge] = str(ctx.author)
            await self.bot.update_user_info(member.id, userinfo)
            await ctx.send(f":medal: **Badges: assign**\nGiven **{self.bot.data['badges'][badge]['n']}** to **{str(member)}**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @badges.command(name="deassign")
    async def deassignb(self, ctx, member : discord.Member, badge : str):
        if await self.bot.is_operator(ctx.author, False):
            userinfo = await self.bot.get_user_info(member.id)
            if badge in userinfo['badges']:
                userinfo['badges'][badge] = None
            else:
                for badgename, badgedata in  userinfo['badges'].copy().items():
                    if (badgename.lower() == badge.lower()) or (self.bot.data['badges'][badgename]['n'].lower() == badge.lower()):
                        del userinfo['badges'][badgename]
                        badge = badgename
            print(userinfo['badges'])
            await self.bot.update_user_info(member.id, userinfo)
            await ctx.send(f":medal: **Badges: deassign**\nRemoved **{self.bot.data['badges'][badge]['n']}** ({badge}) from **{str(member)}**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

def setup(bot):
    bot.add_cog(BadgeHandler(bot))