import asyncio, discord
from discord.ext import commands

import unicodedata

class ModerationHandler():

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def decancer(self, ctx, user: discord.Member):
        if await self.bot.is_elevated(ctx.author, ctx.guild, super=False):
            newtext = unicodedata.normalize("NFKD", user.name).encode("ascii","ignore").decode()
            await user.edit(nick=newtext)
            await ctx.send(f"Decancered `{user.name}` into `{newtext}`")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

def setup(bot):
    bot.add_cog(ModerationHandler(bot))