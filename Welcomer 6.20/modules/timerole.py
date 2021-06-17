import math
import time
import typing
from datetime import datetime

import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class TimeRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="timeroles",
        description="folderclock|Give members roles after being on the server for a while",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['tr', 'timerole', 'roletime', 'timerankup'])
    async def timeroles(self, ctx):
        requires_guild = await customchecks.requires_guild(return_predicate=True, return_message=False)(ctx)
        requires_elevation = await customchecks.requires_elevation(return_predicate=True, return_message=False)(ctx)

        if (requires_guild and requires_elevation) or not requires_guild:
            return await self.bot.walk_help(ctx, ctx.command)
        else:
            await self.bot.get_command("timeroles check").invoke(ctx)

    @timeroles.command(
        name="check",
        description="|Displays the time until your next timerole")
    @customchecks.requires_guild()
    async def timeroles_check(self, ctx):
        if not ctx.guildinfo['tr']['e']:
            message = rockutils._(
                "This guild has disabled {key}. If you are staff, you can enable this by using `{command}`",
                ctx).format(
                    key="timeroles",
                    command=f"{ctx.prefix}timeroles enable")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        _joinseconds = time.time() - ctx.author.joined_at.timestamp()
        _timeroles = []

        for role, seconds in ctx.guildinfo['tr']['r']:
            _role = ctx.guild.get_role(int(role))
            seconds = int(seconds)
            if _role:
                _timeroles.append([
                    _joinseconds > seconds,
                    seconds - _joinseconds,
                    seconds,
                    _role,
                    100 if seconds == 0 else (math.floor((_joinseconds / seconds) * 1000) / 10)])

        _timedroles = sorted(_timeroles, key=lambda o: o[1])

        _notassigned = list(filter(lambda o: not o[0], _timedroles))
        _assigned = list(filter(lambda o: o[0], _timedroles))

        if len(_notassigned) > 0:
            moreroles = True
            nextrole = _notassigned[0]
        else:
            moreroles = False
            nextrole = None

        _time = rockutils.since_seconds_str(
            _joinseconds, allow_secs=False, include_ago=False)

        message = ""
        message += rockutils._(
            "You have been on this server for {time}",
            ctx).format(
                time=_time)
        message += "\n\n"

        if moreroles:
            _time = rockutils.since_seconds_str(
                nextrole[2] - _joinseconds, allow_secs=False, include_ago=False)
            message += rockutils._(
                "Next role: {role}\nTime until next role: {time}",
                ctx).format(
                    role=nextrole[3].mention,
                    time=_time)
        else:
            message += rockutils._(
                "There are no more timeroles left!", ctx)
        message += "\n\n__"
        message += rockutils._(
            "TimeRoles:", ctx)
        message += "__\n"

        for role in _assigned:
            sub_message = f"{self.bot.get_emote('check')} {role[3].mention} {rockutils.since_seconds_str(role[2], allow_secs=False, include_ago=False)}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"TimeRole information")
                message = ""
            message += sub_message

        for role in _notassigned:
            sub_message = f"{self.bot.get_emote('cross')} {role[3].mention} {rockutils.since_seconds_str(role[2], allow_secs=False, include_ago=False)}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"TimeRole information")
                message = ""
            message += sub_message

        if len(message) > 0:
            embed_kwargs = {}
            embed_kwargs['description'] = message
            embed_kwargs['timestamp'] = datetime.utcfromtimestamp(
                math.ceil(time.time()))
            embed_kwargs['title'] = "TimeRole information"
            embed = discord.Embed(colour=3553599, **embed_kwargs)
            if nextrole:
                embed.set_image(
                    url=f"https://cdn.welcomer.fun/minecraftxp?percent={math.floor(nextrole[4])}")
            await ctx.send(embed=embed)

    @timeroles.command(
        name="list",
        description="|Lists all roles that are setup in timeroles")
    @customchecks.requires_guild()
    async def timeroles_list(self, ctx):
        _joinseconds = time.time() - ctx.author.joined_at.timestamp()
        _timeroles = []

        for role, seconds in ctx.guildinfo['tr']['r']:
            _role = ctx.guild.get_role(int(role))
            seconds = int(seconds)
            if _role:
                _timeroles.append([
                    _joinseconds > seconds,
                    seconds - _joinseconds,
                    seconds,
                    _role,
                    100 if seconds == 0 else (math.floor((_joinseconds / seconds) * 1000) / 10)])

        _timedroles = sorted(_timeroles, key=lambda o: o[1])

        _notassigned = list(filter(lambda o: not o[0], _timedroles))
        _assigned = list(filter(lambda o: o[0], _timedroles))
        message = ""

        for role in _assigned:
            sub_message = f"{self.bot.get_emote('check')} {role[3].mention} {rockutils.since_seconds_str(role[2], allow_secs=False, include_ago=False)}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Timed Roles")
                message = ""
            message += sub_message
        for role in _notassigned:
            sub_message = f"{self.bot.get_emote('cross')} {role[3].mention} {rockutils.since_seconds_str(role[2], allow_secs=False, include_ago=False)}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Timed Roles")
                message = ""
            message += sub_message
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Timed Roles")

    @timeroles.command(
        name="enable",
        description="|Enables timeroles"
    )
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_roles"])
    async def timeroles_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["tr.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Timeroles",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @timeroles.command(
        name="disable",
        description="|Disables timeroles"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def timeroles_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["tr.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Timeroles",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @timeroles.command(
        name="add",
        description="<@> <minutes>|Adds a timed role in units of minutes")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def timeroles_add(self, ctx, role: typing.Optional[discord.Role] = None, minutes: typing.Optional[int] = None):
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if minutes is None:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="minutes",
                    expects="number",
                    received=minutes)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        roles = ctx.guildinfo['tr']['r']
        roles = list(filter(lambda o: o[0] != str(role.id), roles))
        roles.append([str(role.id), minutes * 60])
        success = await self.bot.update_info(ctx, ["tr.r", roles])

        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=role.name,
                    value="added")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @timeroles.command(
        name="remove",
        description="<@>|Removes a role from timeroles")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def timeroles_remove(self, ctx, role: typing.Optional[typing.Union[discord.Role, int]] = None):
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if isinstance(role, int):
            _role = ctx.guild.get_role(role)
            if _role:
                role = role

        if isinstance(role, int):
            _id = str(role)
            _target = _id
        else:
            _id = str(role.id)
            _target = role.name

        roles = ctx.guildinfo['tr']['r']
        _timeroles = list(filter(lambda o: o[0] == str(role.id), roles))
        print(_timeroles, roles, str(role.id))
        for timerole in _timeroles:
            roles.remove(timerole)

        success = await self.bot.update_info(ctx, ["tr.r", roles])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=_target,
                    value="removed")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)


def setup(bot):
    bot.add_cog(TimeRole(bot))
