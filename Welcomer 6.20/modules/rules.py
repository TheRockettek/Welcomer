import typing
from discord.ext import commands
from rockutils import rockutils, customchecks


class RuleManagement(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="rules",
        description="clipboardtextoutline|Easily inform users about your rules",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['rule', 'guildrules', 'guildrule'])
    async def rules(self, ctx):
        requires_guild = await customchecks.requires_guild(return_predicate=True, return_message=False)(ctx)
        requires_elevation = await customchecks.requires_elevation(return_predicate=True, return_message=False)(ctx)

        if (requires_guild and requires_elevation) or not requires_guild:
            return await self.bot.walk_help(ctx, ctx.command)
        else:
            await self.bot.get_command("rules list").invoke(ctx)

    @rules.command(
        name="list",
        description="|Lists server rules")
    @customchecks.requires_guild()
    async def rules_list(self, ctx):
        rules = ctx.guildinfo['r']['r']
        if rules == [""]:
            rules = []
        message = ""
        for number, rule in enumerate(rules):
            sub_message = f"**{number+1}**) {rule}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="Server Rules")
                message = ""
            message += sub_message
        if len(rules) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to change this", ctx).format(
                command=f"{ctx.prefix}rules add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="Server Rules")

    @rules.command(
        name="add",
        description="<...>|Adds a rule to the rules list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def rules_add(self, ctx, *, message=None):
        if not message:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="rule")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['r']['r']
        rules.append(message)
        success = await self.bot.update_info(ctx, ["r.r", rules])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Rule",
                    value="added")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @rules.command(
        name="remove",
        description="<number>|Removes a rule from the rule list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def rules_remove(self, ctx, number: typing.Optional[int] = None):
        if number is None:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="rule number")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['r']['r']

        if number < 1 or number > len(rules):
            message = rockutils._(
                "Invalid {format} specified",
                ctx).format(
                    format="rule number")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules.remove(rules[number - 1])

        success = await self.bot.update_info(ctx, ["r.r", rules])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=f"Rule {number}",
                    value="removed")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @rules.command(
        name="enable",
        description="|Enables sending rules on join"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def rules_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["r.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Rules on join",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @rules.command(
        name="disable",
        description="|Disables sending rules on join"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def rules_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["r.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Rules on join",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)


def setup(bot):
    bot.add_cog(RuleManagement(bot))
