import typing
import traceback
import sys

import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class Leaver(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="leaver",
        description="exittoapp|Manages messages that are sent when users leave",
        case_insensitive=True,
        invoke_without_command=True)
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def leaver(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @leaver.command(
        name="enable",
        description="|Enables sending messages when a user leaves"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def leaver_enable(self, ctx):
        channel = discord.utils.get(ctx.guild.channels, id=int(ctx.guildinfo['l']['c'] or 0))
        if not channel:
            message = rockutils._(
                "The {key} set no longer exist.",
                ctx).format(
                    key="leaver channel")
        success = await self.bot.update_info(ctx, ["l.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Leaver",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @leaver.command(
        name="disable",
        description="|Disables leaver"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def leaver_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["l.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Leaver",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @leaver.command(
        name="setchannel",
        description="<#>|Sets the channel that leaver will use")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def leaver_setchannel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"channel name\"`",
                ctx).format(
                    format="text channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["l.c", str(channel.id)])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Leaver channel",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @leaver.command(
        name="test",
        description="[@]|Texts your current welcomer leaver against yourself or a mentioned user")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def welcomer_test(self, ctx, member: typing.Optional[discord.Member] = None):
        if not member:
            member = ctx.author

        if not ("Worker" in self.bot.cogs and hasattr(self.bot.cogs['Worker'], "execute_leaver")):
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error="Could not find leaver executor in worker cog")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await self.bot.cogs['Worker'].execute_leaver(member, ctx.guild.id)
            message = rockutils._("Operation completed successfully", ctx)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            exc_info = sys.exc_info()
            traceback.print_exception(*exc_info)
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @leaver.command(
        name="setmessage",
        description="<...>|Sets the message that leaver will use")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def leaver_setmessage(self, ctx, *, message=None):
        if not message:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="message")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["l.t", message])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Leaver message",
                    value=message)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @leaver.command(
        name="useembed",
        description="[enable/disable]|Toggles if leaver should use embeds",
        aliases=['embeds', 'embed', 'useembeds'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def leaver_useembed(self, ctx, option=None):
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
            value = not ctx.guildinfo['l']['em']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["l.em", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Leaver embeds",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)


def setup(bot):
    bot.add_cog(Leaver(bot))
