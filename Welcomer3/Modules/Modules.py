import asyncio, discord
from discord.ext import commands

class ModuleHandler():

    def __init__(self, bot):
        self.bot = bot
    
    @commands.group()
    async def modules(self, ctx):
        if await self.bot.is_operator(ctx.author):
            if ctx.invoked_subcommand is None:
                await ctx.send(":gear: __**Modules usage**__\nmodules <list/reload/load/unload/reloadall>\n- list: Shows a list of all loaded modules\n- reload <module>: Reloads a module\n- load <module>: Loads a module\n- unload <module>: Unloads a module\n- reloadall: Reloads all modules")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @modules.command(name="list")
    async def listm(self, ctx):
        if await self.bot.is_operator(ctx.author):
            workingmodules = ("` `".join(list(i for i,k in self.bot.loadedmodules.items() if k == True)))
            brokenmodules = (("` `".join(list(i for i,k in self.bot.loadedmodules.items() if k == False))) if len(set(i for i,k in self.bot.loadedmodules.items() if k == False)) > 0 else ("None"))
            await ctx.send(f":gear: **Modules: list**\n__Working:__\n `{workingmodules}`\n__Broken:__\n `{brokenmodules}`")
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @modules.command(name="load")
    async def loadm(self, ctx, moduleName : str):
        if await self.bot.is_operator(ctx.author):
            if self.bot.TEST_MODE == False:
                ClusterResp = False
                Error = False
                if "SyncHandler" in self.bot.cogs:
                    if "broadCast" in dir(self.bot.cogs['SyncHandler']):
                        try:
                            res, ttf = await self.bot.cogs['SyncHandler'].broadCast(8,"*", moduleName)
                            ClusterResp = True
                        except Exception as e:
                            ClusterResp = True
                            Error = True
                msg = (f"Loaded **{moduleName}** successfuly on **{str(len(set(i for i,k in res.items() if k[0] == True)))}**/**{str(self.bot.CLUSTER_COUNT)}** clusters in {str(ttf)}ms" if ClusterResp == True else (":arrows_counterclockwise: **Sync** is not loaded or SyncHanler.broadCast is missing"))
                await ctx.send(f":gear: **Modules: load**\n{msg}\n" + ("```"+str(e)+"```" if Error == True else ""))
            else:
                worked, ttl = self.bot.modules.load(moduleName)
                await ctx.send((f":gear: **Modules: load**\nLoaded **{moduleName}** successfuly in **{str(ttl)}**ms") if worked == True else (f":gear: **Modules: load**\nLoading **{moduleName}** did not preform successfuly\n```{str(ttl)}``` "))
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @modules.command(name="unload")
    async def unloadm(self, ctx, moduleName : str):
        if await self.bot.is_operator(ctx.author):
            if self.bot.TEST_MODE == False:
                ClusterResp = False
                Error = False
                if "SyncHandler" in self.bot.cogs:
                    if "broadCast" in dir(self.bot.cogs['SyncHandler']):
                        try:
                            res, ttf = await self.bot.cogs['SyncHandler'].broadCast(9,"*", moduleName)
                            ClusterResp = True
                        except Exception as e:
                            ClusterResp = True
                            Error = True
                msg = (f"Unloaded **{moduleName}** successfuly on **{str(len(set(i for i,k in res.items() if k[0] == True)))}**/**{str(self.bot.CLUSTER_COUNT)}** clusters in {str(ttf)}ms" if ClusterResp == True else (":arrows_counterclockwise: **Sync** is not loaded or SyncHanler.broadCast is missing"))
                await ctx.send(f":gear: **Modules: unload**\n{msg}\n" + ("```"+str(e)+"```" if Error == True else ""))
            else:
                worked, ttl = self.bot.modules.unload(Name)
                await ctx.send((f":gear: **Modules: load**\nUnloaded **{moduleName}** successfuly in **{str(ttl)}**ms") if worked == True else (f":gear: **Modules: unload**\nUnloading **{moduleName}** did not preform successfuly\n```{str(ttl)}```"))
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

    @modules.command(name="reload")
    async def reloadm(self, ctx, moduleName : str):
        if not await self.bot.is_operator(ctx.author):
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return
        if self.bot.TEST_MODE == False:
            ClusterResp = False
            Error = False
            if "SyncHandler" in self.bot.cogs:
                if "broadCast" in dir(self.bot.cogs['SyncHandler']):
                    try:
                        res, ttf = await self.bot.cogs['SyncHandler'].broadCast(7,"*", moduleName)
                        ClusterResp = True
                    except Exception as e:
                        ClusterResp = True
                        Error = True
            if ClusterResp == False:
                msg = ":arrows_counterclockwise: **Sync** is not loaded or SyncHanler.broadCast is missing"
            else:
                loadedon = len(set(i for i,k in res.items() if k[0] == True))
                msg = f"Reloaded **{moduleName}** successfuly on **{str(loadedon)}**/**{str(self.bot.CLUSTER_COUNT)}** clusters in {str(ttf)}ms"
            await ctx.send(f":gear: **Modules: reload**\n{msg}\n" + ("```"+str(e)+"```" if Error == True else ""))
        else:
            worked, ttl = self.bot.modules.reload(moduleName)
            if worked == True:
                await ctx.send(f":gear: **Modules: load**\nReloaded **{moduleName}** successfuly in **{str(ttl)}**ms")
            else:
                await ctx.send(f":gear: **Modules: reload**\nReloading **{moduleName}** did not preform successfuly\n```{str(ttl)}```")

    @modules.command(name="reloadall")
    async def reloadallb(self, ctx):
        if await self.bot.is_operator(ctx.author):
            if self.bot.TEST_MODE == False:
                ClusterResp = False
                Error = False
                if "SyncHandler" in self.bot.cogs:
                    if "broadCast" in dir(self.bot.cogs['SyncHandler']):
                        try:
                            res, ttf = await self.bot.cogs['SyncHandler'].broadCast(10,"*", "")
                            print(res)
                            ClusterResp = True
                        except Exception as e:
                            ClusterResp = True
                            Error = True
                msg = (f"Reloaded modules successfuly on **{str(len(set(i for i,k in res.items() if k[0] == True)))}**/**{str(self.bot.CLUSTER_COUNT)}** clusters in {str(ttf)}ms" if ClusterResp == True else (":arrows_counterclockwise: **Sync** is not loaded or SyncHanler.broadCast is missing"))
                await ctx.send(f":gear: **Modules: reloadall**\n{msg}\n\n" + "\n".join(f"Cluster **{i}**: **{k[1]}**/**{k[2]}**" for i,k in res.items()) + f"\n" + ("```"+str(e)+"```" if Error == True else ""))
            else:
                worked, mw, mf, ttl = self.bot.modules.reloadall()
                await ctx.send((f":gear: **Modules: reloadall**\nLoaded **{str(mw + mf)}** modules in **{str(ttl)}**ms.\nWorking: {str(mw)} | Failed: {str(mf)}") if worked == True else (f":gear: **Modules: reloadall**\nReloading modules did not preform successfuly\n```{str(mw)}```"))
        else:
            await ctx.message.add_reaction("\N{NO ENTRY}")
            return

def setup(bot):
    bot.add_cog(ModuleHandler(bot))