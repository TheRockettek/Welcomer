import asyncio, discord
from discord.ext import commands

"""
logging enable
logging disable
logging setchannel
logging log
logging unlog
"""

class LoggingHandler():

    def __init__(self, bot):
        self.bot = bot

    @commands.group()
    async def logging(self, ctx):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            if ctx.invoked_subcommand is None:
                guildinfo = await self.bot.get_guild_info(ctx.guild.id)
                possiblevalues = "` `".join(list(i for i,k in guildinfo['logging'].items() if i != "enable" and type(k) == bool))
                if guildinfo['logging']['enable'] == True:
                    enabled = "**Currently logging**\n`" + "` `".join(list(i for i,k in guildinfo['logging'].items() if i != "enable" and k == True))
                else:
                    enabled = ":information_source: **Logging is currently disabled**"
                await ctx.send(f":book: __**Logging commands usage**__\nlogging <enable/disable/setchannel/log/unlog>\n- enable: Enables logging\n- disable: Disables logging\n- setchannel: Sets channel for bot to use as a log channel\n- log: Sets new value to start logging with\n- unlog: Unsets value to stop logging\n\n{enabled}\n`Hi` `Hi`\n\n**Possible Keys**\n`{possiblevalues}`")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")

    @logging.command(name="enable")
    async def enablelg(self, ctx, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            guildinfo['logging']['enable'] = True
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
            await ctx.send(f":nut_and_bolt: __**Logging**__: \nLogging has been **enabled**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @logging.command(name="disable")
    async def disablelg(self, ctx, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            guildinfo['logging']['enable'] = False
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
            await ctx.send(f":nut_and_bolt: __**Logging**__: \nLogging has been **disabled**")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

def setup(bot):
	bot.add_cog(LoggingHandler(bot))