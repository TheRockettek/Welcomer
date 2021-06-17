import asyncio, discord
from datetime import datetime
from discord.ext import commands

class ModuleHandler():

    def __init__(self, bot):
        self.bot = bot

    @commands.group(aliases=['m'])
    async def modules(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send(""":wastebasket:  | **Modules usage**

:white_small_square:  | `unload <module name>` Unloads a module
:white_small_square:  | `reload <module name>` Reloads a module
:white_small_square:  | `load <module name>` Loads a module
:white_small_square:  | `reloadall` Reloads all modules
:white_small_square:  |  `list` Lists all modules""")

    @modules.command(aliases=['u'])
    async def unload(self, ctx, module):
        if str(ctx.author.id) in self.bot.data['roles']['admin'] and self.bot.data['roles']['admin'][str(ctx.author.id)] == True:
            ts = datetime.now()
            worked, ret = self.bot.modules.unload(module)
            te = datetime.now()
            tl = te - ts
            tts = (tl.seconds * 1000000 + tl.microseconds)/1000
            message = f":white_small_square:   | Finished task in **{str(tts)}**ms\n\n"

            if worked == True:
                message += f"{self.bot.logging_emotes['check']['emoji'] or ':white_small_square:'}  | `Success` in **{str(ret)}**ms\n"
            else:
                message += f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | `{str(ret)}`\n"

            await ctx.send(message)
        else:
            await ctx.send(f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | You do not have permission to do this",delete_after=60)

    @modules.command(aliases=['r'])
    async def reload(self, ctx, module):
        if str(ctx.author.id) in self.bot.data['roles']['admin'] and self.bot.data['roles']['admin'][str(ctx.author.id)] == True:
            ts = datetime.now()
            worked, ret = self.bot.modules.reload(module)
            te = datetime.now()
            tl = te - ts
            tts = (tl.seconds * 1000000 + tl.microseconds)/1000
            message = f":white_small_square:   | Finished task in **{str(tts)}**ms\n\n"

            if worked == True:
                message += f"{self.bot.logging_emotes['check']['emoji'] or ':white_small_square:'}  | `Success` in **{str(ret)}**ms\n"
            else:
                message += f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | `{str(ret)}`\n"

            await ctx.send(message)
        else:
            await ctx.send(f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | You do not have permission to do this",delete_after=60)

    @modules.command(aliases=['l'])
    async def load(self, ctx, module):
        if str(ctx.author.id) in self.bot.data['roles']['admin'] and self.bot.data['roles']['admin'][str(ctx.author.id)] == True:
            ts = datetime.now()
            worked, ret = self.bot.modules.load(module)
            te = datetime.now()
            tl = te - ts
            tts = (tl.seconds * 1000000 + tl.microseconds)/1000
            message = f":white_small_square:   | Finished task in **{str(tts)}**ms\n\n"

            if worked == True:
                message += f"{self.bot.logging_emotes['check']['emoji'] or ':white_small_square:'}  | `Success` in **{str(ret)}**ms\n"
            else:
                message += f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | `{str(ret)}`\n"

            await ctx.send(message)
        else:
            await ctx.send(f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | You do not have permission to do this",delete_after=60)

    @modules.command(aliases=['ra','rla'])
    async def reloadall(self, ctx):
        if str(ctx.author.id) in self.bot.data['roles']['admin'] and self.bot.data['roles']['admin'][str(ctx.author.id)] == True:
            ts = datetime.now()
            worked, wm, bm, ret = self.bot.modules.reloadall()
            te = datetime.now()
            tl = te - ts
            tts = (tl.seconds * 1000000 + tl.microseconds)/1000
            message = f":white_small_square:   | Finished task in **{str(tts)}**ms\n\n"

            if worked == True:
                message += f"{self.bot.logging_emotes['check']['emoji'] or ':white_small_square:'}  | Loaded **{str(wm)}**/**{str(wm+bm)}** in **{str(ret)}**ms\n"
            else:
                message += f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | `{str(wm)}`\n"

            await ctx.send(message)
        else:
            await ctx.send(f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | You do not have permission to do this",delete_after=60)

    @modules.command(name="list",aliases=['li'])
    async def modulelist(self, ctx):
        if str(ctx.author.id) in self.bot.data['roles']['admin'] and self.bot.data['roles']['admin'][str(ctx.author.id)] == True:
            message = f":white_small_square:   | Total Modules: **{str(len(self.bot.loaded_modules))}**\n\n"
                    
            for name, enabled in self.bot.loaded_modules.items():
                if enabled == True:
                    message += f"{self.bot.logging_emotes['check']['emoji'] or ':white_small_square:'}  | {name}\n"
                else:
                    message += f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | {name}\n"

            await ctx.send(message)
        else:
            await ctx.send(f"{self.bot.logging_emotes['cross']['emoji'] or ':white_small_square:'}  | You do not have permission to do this",delete_after=60)


def setup(bot):
    bot.add_cog(ModuleHandler(bot))