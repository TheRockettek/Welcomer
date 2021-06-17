import typing
import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class AutoRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="autorole",
        description="accountstar|Automatically give new members roles",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['ar', 'automaticrole', 'joinrole', 'autoroles', 'joinroles', 'automaticroles'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def autorole(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @autorole.command(
        name="enable",
        description="|Enables autorole"
    )
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_roles"])
    async def autorole_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["ar.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Autorole",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @autorole.command(
        name="disable",
        description="|Disables autorole"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def autorole_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["ar.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Autorole",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @autorole.command(
        name="add",
        description="<@>|Adds a role to be automatically assigned when a user joins")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def autorole_add(self, ctx, role: typing.Optional[discord.Role] = None):
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['ar']['r']
        rules.append(str(role.id))
        success = await self.bot.update_info(ctx, ["r.r", rules])

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

    @autorole.command(
        name="remove",
        description="<@>|Removes a role from autorole")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def autorole_remove(self, ctx, role: typing.Optional[typing.Union[discord.Role, int]] = None):
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

        roles = ctx.guildinfo['ar']['r']
        if _id in roles:
            roles.remove(_id)

        success = await self.bot.update_info(ctx, ["ar.r", roles])
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

    @autorole.command(
        name="list",
        description="|Lists all roles being auto assigned to users on join"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def autorole_list(self, ctx):
        message = ""
        for role_id in ctx.guildinfo['ar']['r']:
            role = ctx.guild.get_role(int(role_id))
            if role:
                sub_message = f"{role.mention} `{role_id}`\n"
            else:
                sub_message = f"#unknown-role `{role_id}`\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Autorole roles ({len(ctx.guildinfo['ar']['r'])})")
                message = ""
            message += sub_message
        if len(ctx.guildinfo['ar']['r']) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to add to this", ctx).format(
                command=f"{ctx.prefix}autorole add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title=f"Autorole roles ({len(ctx.guildinfo['ar']['r'])})")


def setup(bot):
    bot.add_cog(AutoRole(bot))
