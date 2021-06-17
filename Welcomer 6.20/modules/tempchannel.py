import typing

import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class TempChannel(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def has_tempchannel(self, category, user):
        for channel in category.channels:
            if str(user.id) in channel.name:
                return True
        return False

    @commands.group(
        name="tempchannel",
        description="microphonesettings|Temporary voice channels for your server",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=[
            'tempvoicechannel',
            'tempchannels',
            'tempvoicechannels',
            'tempvc',
            'tempvoice',
            'tc'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def tempchannel(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @tempchannel.command(
        name="autopurge",
        description="[enable/disable]|Toggles if voice channels should be automatically removed when empty")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_channels"])
    async def tempchannel_autopurge(self, ctx, option=None):
        if option is not None:
            option = option.lower()

        if option not in [
                'disable',
                'disabled',
                'enable',
                'enabled',
                'no',
                'off',
                'on',
                'yes']:
            value = not ctx.guildinfo['tc']['ap']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["tc.ap", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Autopurge",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="setdefaultlimit",
        description="[limit]|Sets a default limit for tempchannels. If nothing is specified or is 0, any user limit will be removed",
        aliases=[
            'setuserlimit',
            'setusercount',
            'limit'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def tempchannel_setdefaultlimit(self, ctx, limit: typing.Optional[int] = 0):
        if limit > 99:
            limit = 99
        if limit < 0:
            limit = 0

        success = await self.bot.update_info(ctx, ["tc.dl", limit])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Default limit",
                    value="unlimited" if limit == 0 else limit)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="setcategory",
        description="<#>|Sets the category that tempchannel will use")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def tempchannel_setcategory(self, ctx, channel: typing.Optional[discord.CategoryChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"channel name\"`",
                ctx).format(
                    format="category channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["tc.c", str(channel.id)])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Category",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="setlobby",
        description="<#>|Sets the voice channel members can join to be moved to a tempchannel automatically")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["move_members"])
    async def tempchannel_setlobby(self, ctx, channel: typing.Optional[discord.VoiceChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"channel name\"`",
                ctx).format(
                    format="voice channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["tc.l", str(channel.id)])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Lobby Channel",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="enable",
        description="|Enables tempchannels"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_channels"])
    async def tempchannel_enable(self, ctx):
        category = discord.utils.get(ctx.guild.channels, id=int(ctx.guildinfo['tc']['c'] or 0))
        if not category:
            message = rockutils._(
                "The {key} set no longer exist.",
                ctx).format(
                    key="tempchannel category")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        success = await self.bot.update_info(ctx, ["tc.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Tempchannels",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="disable",
        description="|Disables tempchannels"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def tempchannel_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["tc.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Tempchannels",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="purge",
        description="|Deletes all tempchannels that are empty")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_channels"])
    async def tempchannel_purge(self, ctx):
        category = discord.utils.get(ctx.guild.channels, id=int(ctx.guildinfo['tc']['c'] or 0))
        if not category:
            message = rockutils._(
                "The {key} set no longer exists",
                ctx).format(
                    key="tempchannel category")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            purged = 0
            for channel in category.channels:
                if isinstance(channel, discord.VoiceChannel):
                    if len(channel.members) == 0:
                        await channel.delete(reason=f"Tempchannel Purge requested by {ctx.author}")
                        purged += 1
            message = rockutils._(
                "{value} channel(s) have been purged",
                ctx).format(
                    value=purged)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="get",
        description="|Gives yourself a tempchannel",
        aliases=["give", "new", "getvc", "givevc", "newvc"])
    @customchecks.requires_guild()
    @customchecks.requires_permission(["manage_channels"])
    async def tempchannel_give(self, ctx):
        category = discord.utils.get(ctx.guild.channels, id=int(ctx.guildinfo['tc']['c'] or 0))
        if not category:
            message = rockutils._(
                "The {key} set no longer exists",
                ctx).format(
                    key="tempchannel category")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if not ctx.guildinfo['tc']['e']:
            message = rockutils._(
                "This guild has disabled {key}. If you are staff, you can enable this by using `{command}`",
                ctx).format(
                    key="tempchannel",
                    command=f"{ctx.prefix}tempchannel enable")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if self.has_tempchannel(category, ctx.author):
            message = rockutils._("You already have an active tempchannel", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.create_voice_channel(f"{ctx.author.name}'s VC [{ctx.author.id}]", category=category, user_limit=ctx.guildinfo['tc']['dl'], reason=f"Tempchannel give requested by {ctx.author}")
            message = rockutils._("Your temporary channel has been created", ctx)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="setlimit",
        description="[#]|Sets a user limit for your temp channel")
    @customchecks.requires_guild()
    @customchecks.requires_permission(["manage_channels"])
    async def tempchannel_setlimit(self, ctx, limit: typing.Optional[int] = 0):
        if limit > 99:
            limit = 99
        if limit < 0:
            limit = 0

        _target = ctx.author
        category = discord.utils.get(ctx.guild.channels, id=int(ctx.guildinfo['tc']['c'] or 0))
        has_channel = self.has_tempchannel(category, _target)
        if not has_channel:
            message = rockutils._(
                "You do not currently have a temporary channel",
                ctx).format(
                    target=_target)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        channel = discord.utils.find(
            lambda o,
            category=category: str(
                _target.id) in o.name and o.category.id == category.id,
            ctx.guild.channels)

        try:
            await channel.edit(user_limit=limit, reason=f"Tempchannel limit change requested by {ctx.author}")
            message = rockutils._(
                "Your user limit has been successfully set to {value}",
                ctx).format(
                    key="Default limit",
                    value="unlimited" if limit == 0 else limit)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @tempchannel.command(
        name="remove",
        description="[#]|Removes yours or someone elses temp channel",
        aliases=["delete", "destroy", "removevc", "deletevc", "destroyvc"])
    @customchecks.requires_guild()
    @customchecks.requires_permission(["manage_channels"])
    async def tempchannel_remove(self, ctx, member: typing.Union[discord.Member, discord.User] = None):
        category = discord.utils.get(ctx.guild.channels, id=int(ctx.guildinfo['tc']['c'] or 0))
        if not category:
            message = rockutils._(
                "The {key} set no longer exists",
                ctx).format(
                    key="tempchannel category")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        _target = ctx.author
        if member:
            requires_elevation = await customchecks.requires_elevation(return_predicate=True, return_message=False)(ctx)
            if requires_elevation:
                _target = member

        has_channel = self.has_tempchannel(category, _target)
        if not has_channel:
            message = rockutils._(
                "No tempchannel is assigned to {target}",
                ctx).format(
                    target=_target)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)

        channel = discord.utils.find(
            lambda o,
            category=category: str(
                _target.id) in o.name and o.category.id == category.id,
            ctx.guild.channels)

        try:
            await channel.delete(reason=f"Tempchannel remove requested by {ctx.author}")
            message = rockutils._("Your temporary channel has been removed", ctx)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    # tempchannel remove [@]
    # tempchannel remove


def setup(bot):
    bot.add_cog(TempChannel(bot))
