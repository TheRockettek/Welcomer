from discord.ext import commands
import discord

class Moderation:

    def __init__(self,bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def clear(self,ctx,*args):
        limit = 100
        deletebots = 1
        deleteusers = 1
        if len(bots) >= 1:
            for key in args:
                args[key]


def setup(bot):
    bot.add_cog(Moderation(bot))