import time
import typing
import math

import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.dump = rockutils.load_json("dump.json")

    # @commands.group(
    #     name="moderation",
    #     description="gavel|Commands to manage users",
    #     case_insensitive=True,
    #     invoke_without_command=True,
    #     aliases=['mod', 'punishments', 'punish', 'moderate'])
    # @customchecks.requires_guild()
    # @customchecks.requires_elevation()
    # async def moderation(self, ctx):
    #     await self.bot.walk_help(ctx, ctx.command)

    @commands.command(
        name="moderation",
        description="|You no longer need +moderation to do moderation commands!"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def moderation(self, ctx):
        message = rockutils._(
            "People said using `+moderation` then the command was confusing. So we listened!\n\n You no longer need to prepend +moderation to moderation commands. All the commands still exist but you no longer need moderation. This means `+moderation ban` will now just be accessed through `+ban`",
            ctx)
        embed = discord.Embed(
            title="We listen!",
            colour=3553599,
            description=message)
        await ctx.send(embed=embed)

    @commands.command(
        name="forcereason",
        description="[enable/disable]|Toggles the requirement of a reason for any moderation")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def moderation_forcereason(self, ctx, option=None):
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
            value = not ctx.guildinfo['m']['fr']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["m.fr", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Forcing reasons",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="purge",
        description="<all/bots/members/@> [messages=100]|Deletes all messages based on a filter")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_messages", "read_message_history"])
    async def moderation_purge(self, ctx, _filter: typing.Union[discord.Member, discord.User, str] = None, _limit: typing.Optional[int] = None):
        if not _filter and not _limit:
            message = rockutils._(
                "Usage: `+purge [all/bots/members/@] [messages=100]`",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if _limit is None and not isinstance(
                _filter, (discord.Member, discord.User)) and isinstance(
                _filter, str) and _filter.isnumeric():
            _limit = int(_filter)
            _filter = None
        elif _limit is None:
            _limit = 100
        if _filter is None:
            _filter = "all"

        _check = None
        if isinstance(_filter, (discord.Member, discord.User)):
            if getattr(_filter, "display_name", getattr(_filter, "name")) in [
                    'all',
                    'bots',
                    'members']:
                _filter = getattr(_filter, "display_name", getattr(_filter, "name"))
            else:
                def _check(m):
                    return m.id != ctx.message.id and m.author.id == _filter.id
                _target = _filter.mention
        if (not isinstance(_filter, (discord.Member, discord.User))) or (
                isinstance(_filter, (discord.Member, discord.User)) and not _check):
            _filter = _filter.lower()
            if _filter not in [
                    'all',
                    'bots',
                    'members']:
                _filter = "all"

            if _filter == "bots":
                def _check(m):
                    return m.id != ctx.message.id and m.author.bot
                _target = "bots"
            elif _filter == "members":
                def _check(m):
                    return m.id != ctx.message.id and not m.author.bot
                _target = "members"
            else:
                def _check(m):
                    return m.id != ctx.message.id and True
                _target = "everyone"

        if _limit > 99:
            _limit = 99
        if _limit < 1:
            _limit = 1

        _limit += 1

        try:
            pins = await ctx.channel.pins()
            pinids = [m.id for m in pins]
            messages = await ctx.channel.purge(limit=_limit, check=lambda o: o.id not in pinids and _check(o))
            message = rockutils._(
                "{messages} message(s) from {target} have been purged",
                ctx).format(
                    messages=len(messages),
                    target=_target)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="ban",
        description="<@> [reason]|Bans a member from the server")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["ban_members"])
    async def moderation_ban(self, ctx, member: typing.Union[discord.User, discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.fetch_ban(member)
        except Exception:
            pass
        else:
            message = rockutils._(
                "This user is already banned",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.ban(member, reason=f"Banned by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "ban", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="banned")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="banid",
        description="<id> [reason]|Bans a member id from the server",
        aliases=['hackban'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["ban_members"])
    async def moderation_banid(self, ctx, member: typing.Union[int] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            _user = await self.bot.fetch_user(member)
        except discord.NotFound:
            _user = None

        if not _user:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid user id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (
            not ctx.author == ctx.guild.owner) and _user and (
            hasattr(
                _user, "top_role") and hasattr(
                ctx.author, "top_role") and (
                    (member.top_role > ctx.author.top_role) or (
                        _user.top_role > ctx.guild.me.top_role) or _user == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.fetch_ban(_user)
        except Exception:
            pass
        else:
            message = rockutils._(
                "This user is already banned",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.ban(_user, reason=f"Banned by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member, str(_user), str(ctx.author.id), str(ctx.author), "ban", reason or "", str(math.ceil(time.time())), "0", True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(_user),
                    value="banned")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="softban",
        description="<@> [reason]|Bans then unbans a member from the server")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["ban_members", "kick_members"])
    async def moderation_softban(self, ctx, member: typing.Union[discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.ban(member, reason=f"Softbanned by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await ctx.guild.unban(member, reason=f"Softbanned by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "softban", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="softbanned")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="tempban",
        description="<@> <minutes> [reason]|Bans then unbans a member from the server for a specified duration")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["ban_members"])
    async def moderation_tempban(self, ctx, member: typing.Union[discord.Member] = None, minutes: typing.Optional[int] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if not minutes:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="ban duration")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if minutes < 1:
            message = rockutils._(
                "Invalid {target} was specified",
                ctx).format(
                    target="ban duration")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.ban(member, reason=f"Tempbanned by {ctx.author} for {minutes} minute(s) for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "softban", reason or "", math.ceil(time.time()), 60 * minutes, False], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="softbanned")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="unban",
        description="<id/@> [reason]|Unbans a previously banned user")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["ban_members"])
    async def moderation_unban(self, ctx, member: typing.Union[discord.User, int] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if isinstance(member, int):
            try:
                _user = await self.bot.fetch_user(member)
            except discord.NotFound:
                _user = None
        else:
            _user = member

        if not _user:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid user id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (
            not ctx.author == ctx.guild.owner) and _user and (
            hasattr(
                _user, "top_role") and hasattr(
                ctx.author, "top_role") and (
                    (member.top_role > ctx.author.top_role) or (
                        _user.top_role > ctx.guild.me.top_role) or _user == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.fetch_ban(_user)
        except discord.NotFound:
            message = rockutils._(
                "This user is not banned",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.unban(_user, reason=f"Unbanned by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member, str(_user), str(ctx.author.id), str(ctx.author), "unban", reason or "", str(math.ceil(time.time())), "0", True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(_user),
                    value="unbanned")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="kick",
        description="<@> [reason]|Kick a member from the server")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["kick_members"])
    async def moderation_kick(self, ctx, member: typing.Union[discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await ctx.guild.kick(member, reason=f"Kicked by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "kick", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="kicked")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="gag",
        description="<@> [reason]|Gags a member from all voice channels")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["mute_members"])
    async def moderation_gag(self, ctx, member: typing.Union[discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await member.edit(mute=True, reason=f"Gagged by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "gag", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="gagged")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="ungag",
        description="<@> [reason]|Ungags a member from all voice channels")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["mute_members"])
    async def moderation_ungag(self, ctx, member: typing.Union[discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await member.edit(mute=False, reason=f"Ungagged by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "ungag", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="ungagged")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="mute",
        description="<@> [reason]|Mutes a member from typing")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["manage_roles"])
    async def moderation_mute(self, ctx, member: typing.Union[discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        muted_role = discord.utils.find(lambda r: "muted" in r.name.lower(), ctx.guild.roles)

        if not muted_role:
            muted_role = await ctx.guild.create_role(name="Muted", colour=discord.Colour(0x23272A), hoist=False, mentionable=False, reason="Auto-generated muted role")
            await muted_role.edit(position=ctx.guild.me.top_role.position - 1, reason="Auto-generated muted role")
            message = rockutils._(
                "Please wait",
                ctx)
            _message = await ctx.send(f"{self.bot.get_emote('loading')}  | " + message)

            for channel in ctx.guild.channels:
                if isinstance(channel, discord.TextChannel):
                    await channel.set_permissions(
                        muted_role,
                        send_messages=False,
                        reason="Muted role permission sync")

            await _message.delete()

        try:
            await member.add_roles(muted_role, reason=f"Muted by {ctx.author} for: {reason if reason else 'No reason specified'}")
            print("call log")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "mute", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="muted")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="unmute",
        description="<@> [reason]|Unmutes a member")
    @customchecks.requires_guild()
    @customchecks.requires_elevation(staffbypass=False)
    @customchecks.requires_permission(["manage_roles"])
    async def moderation_unmute(self, ctx, member: typing.Union[discord.Member] = None, *, reason=None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if ctx.guildinfo['m']['fr'] and not reason:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="reason")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if (not ctx.author == ctx.guild.owner) and (hasattr(member, "top_role") and hasattr(ctx.author, "top_role") and (
                (member.top_role > ctx.author.top_role) or (member.top_role > ctx.guild.me.top_role) or member == ctx.author)):
            message = rockutils._(
                "This user cannot be targeted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        muted_role = discord.utils.find(lambda r: "muted" in r.name.lower(), member.roles)

        if not muted_role:
            message = rockutils._(
                "This user is not muted",
                ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await member.remove_roles(muted_role, reason=f"Unmuted by {ctx.author} for: {reason if reason else 'No reason specified'}")
            await rockutils.logcsv([member.id, str(member), ctx.author.id, str(ctx.author), "unmute", reason or "", math.ceil(time.time()), 0, True], f"{ctx.guild.id}.csv", "punishments")
            message = rockutils._(
                "{target} has been successfully {value}",
                ctx).format(
                    target=str(member),
                    value="unmuted")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        except Exception as e:
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    # todo later
    # moderation tempban <@> <minutes> [reason]
    # moderation tempmute <@> <minutes> [reason]
    # moderation tempgag <@> <minutes> [reason]


def setup(bot):
    bot.add_cog(Moderation(bot))
