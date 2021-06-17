import typing

import discord
from discord.ext import commands
from rockutils import customchecks, rockutils


class FreeRole(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="freeroles",
        description="accountstar|Easily manage self assignable roles to users",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['fr', 'selfrole', 'freerole', 'frs', 'selfroles', 'sr', 'srs']
    )
    async def freeroles(self, ctx):
        requires_guild = await customchecks.requires_guild(return_predicate=True, return_message=False)(ctx)
        requires_elevation = await customchecks.requires_elevation(return_predicate=True, return_message=False)(ctx)

        if (requires_guild and requires_elevation) or not requires_guild:
            return await self.bot.walk_help(ctx, ctx.command)
        else:
            await self.bot.get_command("freeroles list").invoke(ctx)

    @freeroles.command(
        name="list",
        description="|Lists all self assignable roles")
    @customchecks.requires_guild()
    async def freeroles_list(self, ctx):
        roles = ctx.guildinfo['fr']['r']
        message = ""
        for number, roleid in enumerate(roles):
            role = ctx.guild.get_role(int(roleid))
            if role:
                sub_message = f"**{number+1}**) {role.mention} {role.name} - `{role.id}`\n"
                if len(message) + len(sub_message) > 2048:
                    await self.bot.send_data(ctx, message, ctx.userinfo, title="FreeRoles")
                    message = ""
                message += sub_message
        if len(roles) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to change this", ctx).format(
                command=f"{ctx.prefix}freeroles addrole")
        await self.bot.send_data(ctx, message, ctx.userinfo, title="FreeRoles")

    @freeroles.command(
        name="enable",
        description="|Enables freerole"
    )
    @customchecks.requires_elevation()
    @customchecks.requires_permission(["manage_roles"])
    async def freeroles_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["fr.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Freeroles",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @freeroles.command(
        name="disable",
        description="|Disables freerole"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def freeroles_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["fr.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Freeroles",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @freeroles.command(
        name="addrole",
        description="<@>|Adds a role to freerole",
        aliases=['roleadd'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def freeroles_addrole(self, ctx, role: typing.Optional[discord.Role] = None):
        if not role:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"{format} name\"`",
                ctx).format(
                    format="role")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['fr']['r']
        rules.append(str(role.id))
        success = await self.bot.update_info(ctx, ["fr.r", rules])

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

    @freeroles.command(
        name="removerole",
        description="<@>|Removes a role from freerole",
        aliases=['roleremove'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def freeroles_removerole(self, ctx, role: typing.Optional[typing.Union[discord.Role, int]] = None):
        if not ctx.guildinfo['fr']['e']:
            message = rockutils._(
                "This guild has disabled {key}. If you are staff, you can enable this by using `{command}`",
                ctx).format(
                    key="freeroles",
                    command=f"{ctx.prefix}freeroles enable")

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

        roles = ctx.guildinfo['fr']['r']
        if _id in roles:
            roles.remove(_id)

        success = await self.bot.update_info(ctx, ["fr.r", roles])
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

    @freeroles.command(
        name="give",
        description="<@>|Gives yourself a role from the freerole list",
        aliases=['giverole', 'add'])
    @customchecks.requires_guild()
    @customchecks.requires_permission(['manage_roles'])
    async def freeroles_give(self, ctx, role: typing.Optional[typing.Union[discord.Role, int]] = None):
        if not ctx.guildinfo['fr']['e']:
            message = rockutils._(
                "This guild has disabled {key}. If you are staff, you can enable this by using `{command}`",
                ctx).format(
                    key="freeroles",
                    command=f"{ctx.prefix}freeroles enable")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

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

        roles = ctx.guildinfo['fr']['r']
        if _id in roles:
            await ctx.author.add_roles(role, reason="FreeRole request")
            message = rockutils._(
                "You have been given your role", ctx)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "{key} is not a valid freerole role",
                ctx).format(
                    key=_target)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @freeroles.command(
        name="remove",
        description="<@>|Removes a role you have that is from the freerole list",
        aliases=['take', 'takerole'])
    @customchecks.requires_guild()
    @customchecks.requires_permission(['manage_roles'])
    async def freeroles_remove(self, ctx, role: typing.Optional[typing.Union[discord.Role, int]] = None):
        if not ctx.guildinfo['fr']['e']:
            message = rockutils._(
                "This guild has disabled {key}. If you are staff, you can enable this by using `{command}`",
                ctx).format(
                    key="freeroles",
                    command=f"{ctx.prefix}freeroles enable")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

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

        roles = ctx.guildinfo['fr']['r']
        if _id not in roles:
            message = rockutils._(
                "{key} is not a valid freerole role",
                ctx).format(
                    key=_target)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        await ctx.author.remove_roles(role, reason="FreeRole request")
        message = rockutils._(
            "You have been given your role", ctx)
        return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)

    @commands.command(
        name="giverole",
        description="<@>|Gives yourself a role from the freerole list",
        aliases=['rolegive', 'getrole', 'roleget', 'iam'])
    async def freeroles_give_alias(self, ctx):
        await self.bot.get_command("freeroles give").invoke(ctx)

    @commands.command(
        name="removerole",
        description="<@>|Removes a role you have that is from the freerole list",
        aliases=['roleremove', 'takerole', 'roletake', 'iamnot'])
    async def freeroles_removerole_alias(self, ctx):
        await self.bot.get_command("freeroles remove").invoke(ctx)


def setup(bot):
    bot.add_cog(FreeRole(bot))
