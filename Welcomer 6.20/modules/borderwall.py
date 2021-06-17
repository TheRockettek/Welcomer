import typing

import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class Borderwall(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="borderwall",
        description="castle|Moderate new users who join the server",
        case_insensitive=True,
        invoke_without_command=True)
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @borderwall.command(
        name="enable",
        description="|Enables borderwall which will make new users need to authenticate"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(['manage_roles'])
    async def borderwall_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["bw.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Borderwall",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @borderwall.command(
        name="disable",
        description="|Disables borderwall authenticating new users")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["bw.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Borderwall",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @borderwall.command(
        name="setrole",
        description="<@>|Changes the role verified users are assigned",
        aliases=['role', 'roleset', 'verifyrole'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall_setrole(self, ctx, role: typing.Optional[discord.Role] = None):
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["bw.r", str(role.id)])

        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Role",
                    value=role.name)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @borderwall.command(
        name="setchannel",
        description="<#>|Sets the channel that borderwall will use")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall_setchannel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"channel name\"`",
                ctx).format(
                    format="text channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["bw.c", str(channel.id)])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Borderwall channel",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @borderwall.command(
        name="setwaittime",
        description="[limit]|Sets a time limit in minutes for how long borderwall should wait before a user is kicked. If nothing is specified or is 0, there will be no limit",
        aliases=[
            'settime',
            'setwait',
            'wait',
            'waittime',
            'timeout',
            'verifytimeout'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall_setwaittime(self, ctx, limit: typing.Optional[int] = 0):
        if limit < 0:
            limit = 0

        success = await self.bot.update_info(ctx, ["bw.w", limit])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Wait time",
                    value="unlimited" if limit == 0 else limit)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @borderwall.command(
        name="dms",
        description="[enable/disable]|Toggles if borderwall should send the verify messages through direct messages",
        aliases=[
            'usedms',
            'directmessages',
            'usedirect',
            'usedirects',
            'direct'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall_dms(self, ctx, option=None):
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
            value = not ctx.guildinfo['bw']['d']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["bw.d", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Direct Messages",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @borderwall.command(
        name="setmessage",
        description="<verify/verified> ...|Modifies the message that is sent to users when they have verified",
        aliases=[
            'text',
            'setmsg',
            'msg',
            'message'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def borderwall_setmessage(self, ctx, mtype=None, *, message=None):
        if mtype is not None:
            mtype = mtype.lower()

        if mtype not in ['verify', 'verified']:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="message type",
                    expects="verify, verified",
                    received=mtype)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)

        if not message:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="message")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        key = "bw.mv" if mtype == "verified" else "bw.m"
        success = await self.bot.update_info(ctx, [key, message])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key=f"{'Verified' if mtype == 'verified' else 'Verify'} message",
                    value=message)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)


def setup(bot):
    bot.add_cog(Borderwall(bot))
