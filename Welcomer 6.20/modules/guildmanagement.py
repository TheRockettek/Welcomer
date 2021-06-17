import asyncio
import math
import os
import random
import time
import typing

import discord
from discord.ext import commands

from rockutils import customchecks, rockutils


class GuildManagement(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="guild",
        description="wrench|Commands to manage your server",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['server'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @guild.command(
        name="massremoverole",
        description="<target> <role>|Removes every member in target the specified role")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_massremoverole(self, ctx, target: discord.Role = None, role: discord.Role = None):
        await ctx.guild.chunk(cache=True)
        if not target:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="target role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="assigned role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        members = target.members
        done = 0
        seconds = len(members)
        start = time.time()

        _lastcheck = start

        lm, ls = list(map(lambda o: str(math.ceil(o)), divmod(seconds, 60)))
        message = await ctx.send(f"{self.bot.get_emote('loading')}  | {done}/{seconds} (0/s) (**0%**) - 0:00 / {lm}:{ls.rjust(2, '0')}")

        for member in members:
            _time = time.time()
            if role.id in [_role.id for _role in member.roles]:
                await member.remove_roles(role)
            done += 1

            _length = _time - start
            if _time - _lastcheck > 5:
                tm, ts = list(
                    map(lambda o: str(math.ceil(o)), divmod(_length, 60)))

                persec = math.floor((_length / done) * (seconds - done))
                lm, ls = list(
                    map(lambda o: str(math.ceil(o)), divmod(persec, 60)))
                await message.edit(content=f"{self.bot.get_emote('loading')}  | {done}/{seconds} ({math.ceil((_length / done)*100)/100}/s) (**{math.ceil((done/seconds)*1000)/10}%**) - {tm}:{ts.rjust(2, '0')} / {lm}:{ls.rjust(2, '0')}")
                _lastcheck = _time

        _time = time.time()
        _length = _time - start
        tm, ts = list(map(lambda o: str(math.ceil(o)), divmod(_length, 60)))
        await message.edit(content=f"{self.bot.get_emote('check')}  | Assigned role to {seconds} members in {tm}:{ts.rjust(2, '0')}")

    # @guild.command(
    #     name="banrole",
    #     description="<target>|Bans everyone the specified role")
    # @customchecks.requires_guild()
    # @customchecks.requires_elevation()
    # async def guild_banrole(self, ctx, target: discord.Role = None):
    #     if not target or target > ctx.author.top_role:
    #         message = rockutils._(
    #             "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
    #             ctx).format(
    #                 format="target role")
    #         return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    #     members = target.members
    #     done = 0
    #     seconds = len(members)
    #     start = time.time()

    #     _lastcheck = start

    #     lm, ls = list(map(lambda o: str(math.ceil(o)), divmod(seconds, 60)))
    #     message = await ctx.send(f"{self.bot.get_emote('loading')}  | {done}/{seconds} (0/s) (**0%**) - 0:00 / {lm}:{ls.rjust(2, '0')}")

    #     for member in members:
    #         _time = time.time()
    #         if member.top_role < ctx.me.top_role:
    #             await member.ban(reason=f"Ban request by {ctx.author}")
    #         done += 1

    #         _length = _time - start
    #         if _time - _lastcheck > 5:
    #             tm, ts = list(map(lambda o: str(math.ceil(o)), divmod(_length, 60)))

    #             persec = math.floor((_length / done) * (seconds - done))
    #             lm, ls = list(map(lambda o: str(math.ceil(o)), divmod(persec, 60)))
    #             await message.edit(content=f"{self.bot.get_emote('loading')}  | {done}/{seconds} ({math.ceil((_length / done)*100)/100}/s) (**{math.ceil((done/seconds)*1000)/10}%**) - {tm}:{ts.rjust(2, '0')} / {lm}:{ls.rjust(2, '0')}")
    #             _lastcheck = _time

    #     _time = time.time()
    #     _length = _time - start
    #     tm, ts = list(map(lambda o: str(math.ceil(o)), divmod(_length, 60)))
    #     await message.edit(content=f"{self.bot.get_emote('check')}  | Banned {done} members in {tm}:{ts.rjust(2, '0')}")

    @guild.command(
        name="massgiverole",
        description="<target> <role>|Gives every member in target the specified role")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_massgiverole(self, ctx, target: discord.Role = None, role: discord.Role = None):
        await ctx.guild.chunk(cache=True)
        if not target:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="target role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="assigned role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        members = target.members
        done = 0
        seconds = len(members)
        start = time.time()

        _lastcheck = start

        lm, ls = list(map(lambda o: str(math.ceil(o)), divmod(seconds, 60)))
        message = await ctx.send(f"{self.bot.get_emote('loading')}  | {done}/{seconds} (0/s) (**0%**) - 0:00 / {lm}:{ls.rjust(2, '0')}")

        for member in members:
            _time = time.time()
            if role.id not in [_role.id for _role in member.roles]:
                await member.add_roles(role)
            done += 1

            _length = _time - start
            if _time - _lastcheck > 5:
                tm, ts = list(
                    map(lambda o: str(math.ceil(o)), divmod(_length, 60)))

                persec = math.floor((_length / done) * (seconds - done))
                lm, ls = list(
                    map(lambda o: str(math.ceil(o)), divmod(persec, 60)))
                await message.edit(content=f"{self.bot.get_emote('loading')}  | {done}/{seconds} ({math.ceil((_length / done)*100)/100}/s) (**{math.ceil((done/seconds)*1000)/10}%**) - {tm}:{ts.rjust(2, '0')} / {lm}:{ls.rjust(2, '0')}")
                _lastcheck = _time

        _time = time.time()
        _length = _time - start
        tm, ts = list(map(lambda o: str(math.ceil(o)), divmod(_length, 60)))
        await message.edit(content=f"{self.bot.get_emote('check')}  | Assigned role to {seconds} members in {tm}:{ts.rjust(2, '0')}")

    @guild.command(
        name="setprefix",
        description="[prefix]|Changes the guild prefix")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_changeprefix(self, ctx, name="+"):
        name = name.strip() or "+"

        if len(name) == 0:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="prefix",
                    expects="string",
                    received=name)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["d.b.p", name])
        if success:
            message = rockutils._(
                "{key} has been successfully changed to `{value}`",
                ctx).format(
                    key="Prefix",
                    value=name)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild.command(
        name="setlocale",
        description="<name>|Change language locale")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_setlocale(self, ctx, name="en-gb"):
        locales = os.listdir("locale")
        name = name.lower()

        if name not in locales:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="locale",
                    expects=", ".join(locales),
                    received=name)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["d.b.l", name])
        if success:
            message = rockutils._(
                "{key} has been successfully changed to `{value}`",
                ctx).format(
                    key="Locale",
                    value=name)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild.command(
        name="reloaddata",
        description="|Reloads all stats for the server")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_reloaddata(self, ctx):
        success = await self.bot.update_info(ctx, [
            ["d.m.u", 0],
            ["d.d.u", 0],
            ["d.c.u", 0],
            ["d.r.u", 0],
        ])

        if not success:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        await self.bot.get_guild_info(ctx.guild.id)
        message = rockutils._(
            "Reloaded guild data",
            ctx)
        return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)

    @guild.command(
        name="channelbypass",
        description="[enable/disable]|Toggles if staff can bypass white/blacklists")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_channelbypass(self, ctx, option=None):
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
            value = not ctx.guildinfo['ch']['by']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["ch.by", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Channel Bypass",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild.group(
        name="whitelist",
        description="[enable/disable/add/remove/list] [#]|Manages channel whitelisting for welcomer",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=[
            'wl',
            'channelwl',
            'channelwhitelist'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_whitelist(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @guild_whitelist.command(
        name="enable",
        description="|Enables channel whitelisting"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_whitelist_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["ch.w.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Channel Whitelist",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_whitelist.command(
        name="disable",
        description="|Disables channel whitelisting"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_whitelist_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["ch.w.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Channel Whitelist",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_whitelist.command(
        name="add",
        description="<#>|Adds a channel to the whitelist"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_whitelist_add(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="text channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if str(channel.id) not in ctx.guildinfo['ch']['w']['c']:
            ctx.guildinfo['ch']['w']['c'].append(str(channel.id))

        success = await self.bot.update_info(ctx, ["ch.w.c", ctx.guildinfo['ch']['w']['c']])
        if success:
            message = rockutils._(
                "{value} has been added to {key}",
                ctx).format(
                    key="Channel Whitelist",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_whitelist.command(
        name="remove",
        description="<#>|Removes a channel from the whitelist"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_whitelist_remove(self, ctx, channel: typing.Union[discord.TextChannel, int] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="text channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if isinstance(channel, discord.TextChannel):
            _id = str(channel.id)
            channel = channel.mention
        else:
            _id = str(channel)

        if _id in ctx.guildinfo['ch']['w']['c']:
            ctx.guildinfo['ch']['w']['c'].remove(_id)

        success = await self.bot.update_info(ctx, ["ch.w.c", ctx.guildinfo['ch']['w']['c']])
        if success:
            message = rockutils._(
                "{value} has been removed from {key}",
                ctx).format(
                    key="Channel Whitelist",
                    value=channel)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_whitelist.command(
        name="list",
        description="|Lists all channels in whitelist"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_whitelist_list(self, ctx):
        message = ""
        for channel_id in ctx.guildinfo['ch']['w']['c']:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                sub_message = f"{channel.mention} `{channel_id}`\n"
            else:
                sub_message = f"#deleted-channel `{channel_id}`\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Whitelisted channels ({len(ctx.guildinfo['ch']['w']['c'])})")
                message = ""
            message += sub_message
        if len(ctx.guildinfo['ch']['w']['c']) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to add to this", ctx).format(
                command=f"{ctx.prefix}guild whitelist add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Whitelisted channels ({len(ctx.guildinfo['ch']['w']['c'])})")

    @guild.group(
        name="blacklist",
        description="[enable/disable/add/remove/list] [#]|Manages channel blacklisting for welcomer",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=[
            'bl',
            'channelbl',
            'channelblacklist'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_blacklist(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @guild_blacklist.command(
        name="enable",
        description="|Enables channel blacklisting"
    )
    @customchecks.requires_elevation()
    async def guild_blacklist_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["ch.b.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Channel Blacklist",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_blacklist.command(
        name="disable",
        description="|Disables channel blacklisting"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_blacklist_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["ch.b.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Channel Blacklist",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_blacklist.command(
        name="add",
        description="<#>|Adds a channel to the blacklist"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_blacklist_add(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="text channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if str(channel.id) not in ctx.guildinfo['ch']['b']['c']:
            ctx.guildinfo['ch']['b']['c'].append(str(channel.id))

        success = await self.bot.update_info(ctx, ["ch.w.c", ctx.guildinfo['ch']['b']['c']])
        if success:
            message = rockutils._(
                "{value} has been added to {key}",
                ctx).format(
                    key="Channel Blacklist",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_blacklist.command(
        name="remove",
        description="<#>|Removes a channel from the blacklist"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_blacklist_remove(self, ctx, channel: typing.Union[discord.TextChannel, int] = None):
        if not channel:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="channel",
                    expects="text channel",
                    received=str(channel))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if isinstance(channel, discord.TextChannel):
            _id = str(channel.id)
            channel = channel.mention
        else:
            _id = str(channel)

        if _id in ctx.guildinfo['ch']['b']['c']:
            ctx.guildinfo['ch']['b']['c'].remove(_id)

        success = await self.bot.update_info(ctx, ["ch.w.c", ctx.guildinfo['ch']['b']['c']])
        if success:
            message = rockutils._(
                "{value} has been removed from {key}",
                ctx).format(
                    key="Channel Blacklist",
                    value=channel)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @guild_blacklist.command(
        name="list",
        description="|Lists all channels in blacklist"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def guild_blacklist_list(self, ctx):
        message = ""
        for channel_id in ctx.guildinfo['ch']['b']['c']:
            channel = ctx.guild.get_channel(int(channel_id))
            if channel:
                sub_message = f"{channel.mention} `{channel_id}`\n"
            else:
                sub_message = f"#deleted-channel `{channel_id}`\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Blacklisted channels ({len(ctx.guildinfo['ch']['b']['c'])})")
                message = ""
            message += sub_message
        if len(ctx.guildinfo['ch']['b']['c']) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to add to this", ctx).format(
                command=f"{ctx.prefix}guild blacklist add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Blacklisted channels ({len(ctx.guildinfo['ch']['b']['c'])})")

    @commands.group(
        name="slowmode",
        description="avtimer|Commands to manage slowmode for channels",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['slow'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def slowmode(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @slowmode.command(
        name="list",
        description="|Lists slowmode intervals for channels"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def slowmode_list(self, ctx):
        intervals = {}
        for channel in ctx.guild.channels:
            if isinstance(channel, discord.TextChannel):
                delay = channel.slowmode_delay
                if delay != 0:
                    if delay not in intervals:
                        intervals[delay] = []
                    intervals[delay].append(channel)

        message = ""
        for delay in sorted(intervals.keys()):
            channels = intervals[delay]
            sub_message = f"{rockutils.produce_human_timestamp(delay)}: {' '.join(channel.mention for channel in channels)}"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Slowmoded channels ({sum(len(v) for v in intervals.values())})")
                message = ""
            message += sub_message
        if len(intervals) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to change this", ctx).format(
                command=f"{ctx.prefix}slowmode setlimit")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Slowmoded channels ({sum(len(v) for v in intervals.values())})")

    @slowmode.command(
        name="reset",
        description="[#]|Resets slowmode for specified channel or current channel"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_channels"])
    async def slowmode_reset(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if not channel:
            channel = ctx.channel

        try:
            await channel.edit(slowmode_delay=0, reason=f"Slowmode reset by {ctx.author}")
            message = rockutils._(
                "{key} for {target} has been {action}",
                ctx).format(
                    key="Slowmode",
                    action="reset",
                    target=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @slowmode.command(
        name="setlimit",
        description="<#/seconds> [seconds]|Sets slowmode in seconds for specified channel or current channel"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_channels"])
    async def slowmode_setlimit(self, ctx, channel: typing.Union[discord.TextChannel, int] = None, seconds: typing.Optional[int] = None):
        if isinstance(channel, discord.TextChannel):
            _channel = channel
            _seconds = seconds or 0
        else:
            _channel = ctx.channel
            _seconds = channel or 0

        if _seconds > 21600:
            _seconds = 21600
        if _seconds < 0:
            _seconds = 0

        try:
            await _channel.edit(slowmode_delay=_seconds, reason=f"Slowmode set by {ctx.author}")

            if _seconds == 0:
                message = rockutils._(
                    "{key} for {target} has been {action}",
                    ctx).format(
                        key="Slowmode",
                        action="reset",
                        target=_channel.mention)
            else:
                message = rockutils._(
                    "{key} for {target} has been set to {action}",
                    ctx).format(
                        key="Slowmode",
                        action=rockutils.produce_human_timestamp(_seconds),
                        target=_channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.group(
        name="staff",
        description="cctv|Manage users who can modify welcomer",
        case_insensitive=True,
        invoke_without_command=True)
    async def staff(self, ctx):
        requires_guild = await customchecks.requires_guild(return_predicate=True, return_message=False)(ctx)
        requires_elevation = await customchecks.requires_elevation(return_predicate=True, return_message=False)(ctx)

        if (requires_guild and requires_elevation) or not requires_guild:
            return await self.bot.walk_help(ctx, ctx.command)
        else:
            await self.bot.get_command("staff list").invoke(ctx)

    @staff.command(
        name="list",
        description="|Lists all staff who are on the server")
    @customchecks.requires_guild()
    async def staff_list(self, ctx):
        staff_statuses = {
            "offline": [],
            "dnd": [],
            "idle": [],
            "online": []
        }
        for staff in ctx.guildinfo['st']['u']:
            staff_id = staff[0]
            try:
                member = ctx.guild.get_member(int(staff_id))
                if member:
                    staff_statuses[str(member.status)].append(member)
            except BaseException:
                pass
        message = ""
        for key in sorted(staff_statuses.keys(), reverse=True):
            if len(staff_statuses[key]) > 0:
                message += f"{self.bot.get_emote('status_' + key)} {', '.join(list(f'{str(user)}' for user in staff_statuses[key]))}\n"
        if message == "":
            message = rockutils._(
                "This list is empty. Run `{command}` to change this", ctx).format(
                command=f"{ctx.prefix}staff add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="Guild Staff")

    @staff.command(
        name="add",
        description="<@>|Adds a member to the staff list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    async def staff_add(self, ctx, member: typing.Optional[discord.Member] = None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        staff = ctx.guildinfo['st']['u']
        staff = list(filter(lambda o: o[0] != str(member.id), staff))
        staff.append([str(member.id), True])
        success = await self.bot.update_info(ctx, ["st.u", staff])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=str(member),
                    value="added")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @staff.command(
        name="remove",
        description="<@>|Removes a user from staff")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def autorole_remove(self, ctx, user: typing.Optional[typing.Union[discord.User, int]] = None):
        if not user:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="user")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if isinstance(user, int):
            _user = self.bot.get_user(user)
            if not _user:
                try:
                    _user = await self.bot.fetch_user(user)
                except discord.NotFound:
                    _user = None
        else:
            _user = user

        if not _user:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid user")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        staff = ctx.guildinfo['st']['u']
        staff = list(filter(lambda o: o[0] != str(_user.id), staff))
        success = await self.bot.update_info(ctx, ["st.u", staff])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=_user,
                    value="removed")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    # @staff.command(
    #     name="getping",
    #     description="[enable/disable]|Toggles if you want to be able to be pinged when +staff ping is used")
    # @customchecks.requires_guild()
    # @customchecks.requires_elevation()
    # async def staff_haveping(self, ctx, option=None):
    #     if option is not None:
    #         option = option.lower()

    #     staff = ctx.guildinfo['st']['u']

    #     if option not in [
    #             'disable',
    #             'disabled',
    #             'enable',
    #             'enabled',
    #             'no',
    #             'off',
    #             'on',
    #             'yes']:
    #         chosen = list(filter(lambda o: o[0] == str(ctx.author.id), staff))
    #         if len(chosen) > 0:
    #             value = not chosen[0][1]
    #         else:
    #             value = True
    #     else:
    #         value = True if option in [
    #             'enable', 'enabled', 'on', 'yes'] else False

    #     staff = list(filter(lambda o: o[0] != str(ctx.author.id), staff))
    #     staff.append([str(ctx.author.id), value])
    #     success = await self.bot.update_info(ctx, ["st.u", staff])
    #     if success:
    #         message = rockutils._(
    #             "{key} has been successfully {value}",
    #             ctx).format(
    #                 key="GetPing",
    #                 value="enabled" if value else "disabled")
    #         return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
    #     else:
    #         message = rockutils._(
    #             "There was a problem when saving changes. Please try again", ctx)
    #         return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    # @staff.command(
    #     name="enableping",
    #     description="[enable/disable]|Toggles if users can use staff ping")
    # @customchecks.requires_guild()
    # @customchecks.requires_elevation()
    # async def staff_enableping(self, ctx, option=None):
    #     if option is not None:
    #         option = option.lower()

    #     if option not in [
    #             'disable',
    #             'disabled',
    #             'enable',
    #             'enabled',
    #             'no',
    #             'off',
    #             'on',
    #             'yes']:
    #         value = not ctx.guildinfo['m']['fr']
    #     else:
    #         value = True if option in [
    #             'enable', 'enabled', 'on', 'yes'] else False

    #     success = await self.bot.update_info(ctx, ["st.ap", value])
    #     if success:
    #         message = rockutils._(
    #             "{key} has been successfully {value}",
    #             ctx).format(
    #                 key="Staff Ping",
    #                 value="enabled" if value else "disabled")
    #         return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
    #     else:
    #         message = rockutils._(
    #             "There was a problem when saving changes. Please try again", ctx)
    #         return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    # @staff.command(
    #     name="ping",
    #     description="...|Pings any online staff for support")
    # @customchecks.requires_guild()
    # async def staff_ping(self, ctx, *, reason=None):
    #     if not ctx.guildinfo['st']['ap']:
    #         message = rockutils._(
    #             "This guild has disabled {key}. If you are staff, you can enable this by using `{command}`",
    #             ctx).format(
    #                 key="staff ping",
    #                 command=f"{ctx.prefix}staff enableping")
    #         return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    #     pingable_staff = []
    #     for staff in ctx.guildinfo['st']['u']:
    #         staff_id = staff[0]
    #         try:
    #             member = ctx.guild.get_member(int(staff_id))
    #             if member and staff[0] and str(member.status) in ['online', 'idle']:
    #                 pingable_staff.append(member)
    #         except BaseException:
    #             pass

    #     if len(pingable_staff) == 0:
    #         message = rockutils._("No staff are avaliable at the moment", ctx)
    #         return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    #     if not reason:
    #         message = rockutils._(
    #             "No {target}, which is required, was specified",
    #             ctx).format(
    #                 target="reason")
    #         return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    #     staff = random.choice(pingable_staff)
    #     embed = discord.Embed(colour=3553599, description=reason)

    #     message = rockutils._(
    #         "{staff}, {user} is in need of assistance",
    #         ctx).format(
    #             staff=staff.mention,
    #             user=ctx.author.mention)
    #     return await ctx.send(content=f"{self.bot.get_emote('check')}  | " + message, embed=embed)


def setup(bot):
    bot.add_cog(GuildManagement(bot))
