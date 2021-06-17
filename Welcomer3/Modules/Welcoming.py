import asyncio, discord
from discord.ext import commands

"""                "badges" : {
                    "e" : true
                },
                "dm" : {
                    "e" : true,
                    "t" : {
                        "d" : "Enjoy your time at %name%!",
                        "t" : "Welcome $name$",
                        "iu" : "",
                        "ui" : False,
                    }
                },
                "img" : {
                    "b" : "default",
                    "c" : 0,
                    "e" : true,
                    "ig" : "default"
                },
                "leaver" : {
                    "e" : false,
                    "t" : "Looks like $name$ has left us :sob:"
                },
                "text" : {
                    "e" : true,
                    "t" : "Welcome $mention$ to **%name%**! You are the %members% member on the server :)"
                }
            }"""

class WelcomingHandler():

    def __init__(self,bot):
        self.bot = bot

    """
    enable <key>
    disable <key>
    toggle <key>
    list
    """
    """:wave: __**Welcomer commands usage**__
    welcomer <dm/text/image/setchannel>
    - setchannel <channel mention>: Set channel for image and text
    - dm <enable/disable/set>: Manage dm messages for people who join
            - set <title/description/image> <text>: Set the text in the dm message
    - text <enable/disable/set>: Manage text messages for people who join
            - set <text>: Sets text for welcome message
    - image <enable/disable/set>: Manage images for people who join
            - set <background/text> <text>: Sets background and image text"""
    """
    welcomer setchannel #
    welcomer dm enable
    welcomer dm disable
    welcomer dm set <title description set> <text>
    welcomer text enable
    welcomer text disable
    welcomer text set <text>
    welcomer image enable
    welcomer image disable
    welcomer image set <background text> <text>

    welcomer enable <dm/text/image>
    welcomer disable <dm/text/image>
    welcomer set <channel/imagebackground/imagetext/text/dmdescription/dmtitle/imagetcolour/imageccolour>
    
    """

    @commands.group()
    async def welcomer(self, bot):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            if ctx.invoked_subcommand is None:
                await ctx.send(":wave: __**Welcomer commands usage**__\nwelcomer <dm/text/image/setchannel>\n- setchannel <channel mention>: Set channel for image and text\n- dm <enable/disable/set>: Manage dm messages for people who join\n        - set <title/description/image> <text>: Set the text in the dm message\n- text <enable/disable/set>: Manage text messages for people who join\n        - set <text>: Sets text for welcome message\n- image <enable/disable/set>: Manage images for people who join\n        - set <background/text> <text>: Sets background and image text")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @welcomer.group(name="dm")
    async def welcomerdm(self, bot):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            if ctx.invoked_subcommand is None:
                await ctx.send(":wave: __**Welcomer DM commands usage**__\nwelcomer dm <enable/disable/set>:\n        - set <title/description/image> <text>: Set the text in the dm message")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @welcomerdm.command(name="enable")
    async def enablewelcomerdm(self, bot):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            guildinfo['welcomer']['dm']['e'] = True
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @welcomerdm.command(name="disable")
    async def disablewelcomerdm(self, bot):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            guildinfo = await self.bot.get_guild_info(ctx.guild.id)
            guildinfo['welcomer']['dm']['e'] = False
            await self.bot.update_guild_info(ctx.guild.id, guildinfo)
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @welcomerdm.command(name="set")
    async def setwelcomerdm(self, bot, key=""):
        if await self.bot.is_elevated(ctx.author, ctx.guild, False):
            if key != "title":
                await ctx.send(":wave: __**Welcomer DM commands usage**__\nwelcomer dm set <title/description> <text>:\n        - title <text>: Sets the title of a dm message\n        - description <text>: Sets the description of a dm message")

def setup(bot):
    bot.add_cog(WelcomingHandler(bot))