import asyncio, discord
from discord.ext import commands

class SpecialRoleHandler():

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def specialroles(self, ctx):
        if await self.bot.is_operator(ctx.author):
            if ctx.invoked_subcommand is None:
                roles = list(i for i,k in self.bot.data['roles'].items())
                await ctx.send(f":name_badge: **Special Roles**\nspecialroles <add/remove/list>\n- add <group> <@>: Add the mentioned user to type\n- remove <group> <@>: Remove the mentioned user from type\n- list <group>: List users in type\n\n**Role list** ({str(len(roles))}):\n`{'` `'.join(roles)}`")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @specialroles.command(name="add")
    async def addsr(self, ctx, group : str, user : discord.Member):
        if await self.bot.is_operator(ctx.author):
            if not group in self.bot.data['roles']:
                await ctx.send(f":name_badge: **Special Roles: add**\n**{group}** is not a valid group.")
            else:
                self.bot.data['roles'][group][str(user.id)] = True
                self.bot.update_data()
                await ctx.send(f":name_badge: **Special Roles: add**\nAdded **{str(user)}** to group **{group}** successfuly")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @specialroles.command(name="remove")
    async def removesr(self, ctx, group : str, user : discord.Member):
        if await self.bot.is_operator(ctx.author):
            if not group in self.bot.data['roles']:
                await ctx.send(f":name_badge: **Special Roles: remove**\n**{group}** is not a valid group.")
            else:
                if str(user.id) in self.bot.data['roles'][group]:
                    del self.bot.data['roles'][group][str(user.id)]
                    self.bot.update_data()
                    await ctx.send(f":name_badge: **Special Roles: remove**\Removed **{str(user)}** from group **{group}** successfuly")
                else:
                    await ctx.send(f":name_badge: **Special Roles: remove**\**{str(user)}** was not in the group **{group}** anyway")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @specialroles.command(name="list")
    async def listsr(self, ctx, group : str):
        if await self.bot.is_operator(ctx.author):
            if not group in self.bot.data['roles']:
                await ctx.send(f":name_badge: **Special Roles: list**\n**{group}** is not a valid group.")
            else:
                members = list((str(self.bot.get_user(int(i))) if self.bot.get_user(int(i)) != None else i) for i,k in self.bot.data['roles'][group].items() if i != "0")
                await ctx.send(f":name_badge: **Special Roles: list**\nUsers in group **{group}** ({str(len(members))}):\n`{'` `'.join(members)}`")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

def setup(bot):
    bot.add_cog(SpecialRoleHandler(bot))