import discord, asyncio, random
from discord.ext import commands

def isrole(serverroles,name):
    for role in serverroles:
        if role.name == name:
            return True, role
    return False, None

class GiveColourRole():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def givecolour(self,ctx,colour : str):
        try:
            colourid = int(colour,16)
            hexcolour = colour[0:6].upper()
            print(hexcolour,str(colourid))
            r = int(hexcolour[0:2],16)
            g = int(hexcolour[2:4],16)
            b = int(hexcolour[4:6],16)
            print(str(r) + str(g) + str(b) + " : " + hexcolour)
            discordcolour = discord.Colour.from_rgb(r, b, g)
            rolename = "#" + hexcolour.upper()
            hasrole, role = isrole(ctx.message.guild.roles,rolename)
            if hasrole == True:
                await ctx.message.author.add_roles(role)
            else:
                role = await ctx.message.guild.create_role(name=rolename,colour=discordcolour,mentionable=False,hoist=False,reason="Colour role non-existent however persitent")
                await ctx.message.author.add_roles(role)
            embed = discord.Embed(title=rolename + " has been assigned",colour=int(hexcolour,16))
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Could not give role",description="```" + str(e) + "```")
            await ctx.send(embed=embed)

    @commands.command()
    async def giverandomcolour(self,ctx):
        try:
            colour = str(hex(random.randint(0,16777216)))[2:]
            colourid = int(colour,16)
            hexcolour = colour[0:6].upper()
            print(hexcolour,str(colourid))
            r = int(hexcolour[0:2],16)
            g = int(hexcolour[2:4],16)
            b = int(hexcolour[4:6],16)
            print(str(r) + str(g) + str(b) + " : " + hexcolour)
            discordcolour = discord.Colour.from_rgb(r, b, g)
            rolename = "#" + hexcolour.upper()
            hasrole, role = isrole(ctx.message.guild.roles,rolename)
            if hasrole == True:
                await ctx.message.author.add_roles(role)
            else:
                role = await ctx.message.guild.create_role(name=rolename,colour=discordcolour,mentionable=False,hoist=False,reason="Colour role non-existent however persitent")
                await ctx.message.author.add_roles(role)
            embed = discord.Embed(title=rolename + " has been assigned",colour=int(hexcolour,16))
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            embed = discord.Embed(title="Could not give role",description="```" + str(e) + "```")
            await ctx.send(embed=embed)

    @commands.command()
    async def uncolour(self,ctx,colour : str):
        for role in ctx.message.author.roles:
            if role.name == "#" + colour.upper():
                await ctx.message.author.remove_roles(role,reason="Unassigned colour role")
                embed = discord.Embed(title="Colour removed")
                await ctx.send(embed=embed)
                return
        embed = discord.Embed(title="You do not have the colour role #" + colour.upper())
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(GiveColourRole(bot))