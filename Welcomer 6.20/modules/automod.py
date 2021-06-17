import typing
import re

from discord.ext import commands
from rockutils import customchecks, rockutils


class AutoMod(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="automod",
        description="messageprocessing|Moderate your server messages automatically",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['am', 'automoderator', 'automoderation']
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @automod.command(
        name="enable",
        description="|Enables auto moderation and will moderate any features that have been set to moderate")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(['manage_messages'])
    async def automod_enable(self, ctx):
        success = await self.bot.update_info(ctx, ["am.e", True])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="AutoMod",
                    value="**enabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @automod.command(
        name="disable",
        description="|Disables auto moderation")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_disable(self, ctx):
        success = await self.bot.update_info(ctx, ["am.e", False])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="AutoMod",
                    value="**disabled**")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @automod.command(
        name="moderate",
        description="<key> [enable/disable]|Toggles what auto moderation should moderate")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_moderate(self, ctx, key=None, option=None):
        if key is not None:
            key = key.lower()

        if option is not None:
            option = option.lower()

        keys = {
            "urlredirect": "ur",
            "massmention": "mm",
            "ipgrabbers": "ig",
            "profanity": "p",
            "masscaps": "mc",
            "invites": "i",
            "filter": "f",
            "urls": "ul",
        }

        display = {
            "ur": "Url Redirections",
            "mm": "Mass Mentions",
            "ig": "IP Grabbers",
            "mc": "Mass Capitals",
            "ul": "Urls",
            "f": "Filtered Words",
            "i": "Invites",
            "p": "Profanity",
        }

        if key not in keys:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="moderation type",
                    expects=", ".join(keys),
                    received=key)
            return await ctx.send(f"{self.bot.get_emote('alert')}  | " + message)
        _key = keys[key]

        if option not in [
                'disable',
                'disabled',
                'enable',
                'enabled',
                'no',
                'off',
                'on',
                'yes']:
            value = not ctx.guildinfo['am']['g'][_key]
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, [f"am.g.{_key}", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=f"Moderating {display[_key]}",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @automod.command(
        name="smartmod",
        description="[enable/disable]|Toggles if messages should be moderated with smartmod",
        aliases=['smart'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_smartmod(self, ctx, option=None):
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
            value = not ctx.guildinfo['am']['sm']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["am.sm", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="SmartMod",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @automod.group(
        name="regex",
        description="<list/add/remove> [...]|Allows for regex formatting",
        case_insensitive=True,
        invoke_without_command=True)
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_regex(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @automod_regex.command(
        name="list",
        description="|Lists all currently configured regex rules")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_regex_list(self, ctx):
        rules = ctx.guildinfo['am']['r']
        message = ""
        for number, rule in enumerate(rules):
            sub_message = f"**{number+1}**) {rule}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="AutoMod Regex Rules")
                message = ""
            message += sub_message
        if len(rules) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to change this", ctx).format(
                command=f"{ctx.prefix}automod regex add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="AutoMod Regex Rules")

    @automod_regex.command(
        name="add",
        description="<...>|Adds a rule to the regex rule list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_regex_add(self, ctx, *, message=None):
        if not message:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="rule")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            re.compile(message)
        except Exception as e:
            message = rockutils._(
                "Encountered an error whilst checking your regex. Use <{site}> and set the flavour to python to test out the regex the bot will use\n```{error}```",
                ctx).format(
                    site="https://regex101.com/",
                    error=str(e))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['am']['r']
        rules.append(message)
        success = await self.bot.update_info(ctx, ["am.r", rules])
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

    @automod_regex.command(
        name="remove",
        description="<number>|Removes a rule from the regex rule list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_regex_remove(self, ctx, number: typing.Optional[int] = None):
        if number is None:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="regex rule number")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['am']['r']

        if number < 1 or number > len(rules):
            message = rockutils._(
                "Invalid {format} specified",
                ctx).format(
                    format="regex rule number")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules.remove(rules[number - 1])

        success = await self.bot.update_info(ctx, ["am.r", rules])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=f"Regex Rule {number}",
                    value="removed")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @automod.group(
        name="filter",
        description="<list/add/remove> [...]|Allows for filtering text from messages",
        case_insensitive=True,
        invoke_without_command=True)
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_filter(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @automod_filter.command(
        name="list",
        description="|Lists all currently configured filter rules")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_filter_list(self, ctx):
        rules = ctx.guildinfo['am']['f']
        message = ""
        for number, rule in enumerate(rules):
            sub_message = f"**{number+1}**) {rule}\n"
            if len(message) + len(sub_message) > 2048:
                await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="AutoMod Filter Rules")
                message = ""
            message += sub_message
        if len(rules) == 0:
            message = rockutils._(
                "This list is empty. Run `{command}` to change this", ctx).format(
                command=f"{ctx.prefix}automod filter add")
        await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="AutoMod Filter Rules")

    @automod_filter.command(
        name="add",
        description="<...>|Adds a rule to the filter rule list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_filter_add(self, ctx, *, message=None):
        if not message:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="rule")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['am']['f']
        rules.append(message)
        success = await self.bot.update_info(ctx, ["am.f", rules])
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

    @automod_filter.command(
        name="remove",
        description="<number>|Removes a rule from the filter rule list")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_filter_remove(self, ctx, number: typing.Optional[int] = None):
        if number is None:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="filter rule number")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules = ctx.guildinfo['am']['f']

        if number < 1 or number > len(rules):
            message = rockutils._(
                "Invalid {format} specified",
                ctx).format(
                    format="Filter rule number")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        rules.remove(rules[number - 1])

        success = await self.bot.update_info(ctx, ["am.f", rules])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key=f"Filter Rule {number}",
                    value="removed")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @automod.command(
        name="threshold",
        description="<mentions/caps> [count]|Modifies thresholds for mentions or caps")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def automod_threshold(self, ctx, key=None, number: typing.Optional[int] = None):
        if key is not None:
            key = key.lower()

        if key == "mentions":
            _key = "m"
            if number is not None:
                if number < 1:
                    number = 1
                if number > 10:
                    number = 10
        elif key == "caps":
            _key = "c"
            if number is not None:
                if number <= 1:
                    number = 1
                if number > 100:
                    number = 100
        else:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="threshold type",
                    expects="mentions, caps",
                    received=key)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if number is None:
            message = rockutils._(
                "Invalid argument for `{argument_name}`. Expected `{expects}` but received `{received}`",
                ctx).format(
                    argument_name="threshold",
                    expects="number",
                    received=number)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, [f"am.t.{_key}", number])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key=("Mentions" if key == "mentions" else "Capitals") + " threshold",
                    value=f"{number}" if key == "mentions" else f"{number}%")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)


def setup(bot):
    bot.add_cog(AutoMod(bot))
