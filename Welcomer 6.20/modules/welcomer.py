import discord
import typing
from discord.ext import commands
import sys
import traceback
from rockutils import customchecks, rockutils


markdown = {
    "users": {
        "user": "Alias of user.name",
        "user.mention": "User mention",
        "user.name": "The users name",
        "user.discriminator": "The users discriminator tag",
        "user.id": "The users id",
        "user.avatar": "Url of users avatar",
        "user.created.timestamp": "Timestamp for when the users account was created",
        "user.created.since": "String for how long a user has been on discord",
        "user.joined.timestamp": "Timestamp of how long a user has been on the server",
        "user.joined.since": "String for how long a user has been on the server",
    },
    "server": {
        "members": "Alias of server.members",
        "server": "Alias of server.name",
        "server.name": "The servers name",
        "server.id": "The servers id",
        "server.members": "Number of users and prefix of users on server",
        "server.member.count": "Number of users who are on the server",
        "server.member.prefix": "Count prefix for server.member.count",
        "server.icon": "Url for the server icon",
        "server.created.timestamp": "Timestamp for when server was created",
        "server.created.since": "String for how long the server has existed for",
        "server.splash": "Url of splash the server has (if there is one)",
        "server.shard_id": "Shard Id that the server is on",
    },
    "invite": {
        "invite.code": "Code that the invite has been assigned to",
        "invite.inviter": "Name of user who created the invite",
        "invite.inviter.id": "Id of user who created the invite",
        "invite.uses": "How many people have used the invite",
        "invite.temporary": "Boolean that specifies if the invite is temporary",
        "invite.created.timestamp": "Timestamp for when it was created",
        "invited.created.since": "String for how long it has been since the invite was made",
        "invited.max": "Max invites for an invite. Will return 0 if it is unlimited"
    }
}


class Welcomer(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="welcomer",
        description="messageprocessing|Welcome new users with customizablilty and ease",
        case_insensitive=True,
        invoke_without_command=True,
        aliases=['whalecummer', 'welcome'])
    @customchecks.requires_elevation()
    async def welcomer(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)

    @welcomer.command(
        name="test",
        description="[@]|Texts your current welcomer config against yourself or a mentioned user")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def welcomer_test(self, ctx, member: typing.Optional[discord.Member] = None):
        if not member:
            member = ctx.author

        if not ("Worker" in self.bot.cogs and hasattr(self.bot.cogs['Worker'], "execute_welcomer")):
            message = rockutils._(
                "A problem has occured during this operation: {error}",
                ctx).format(
                    error="Could not find welcomer executor in worker cog")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        try:
            await self.bot.cogs['Worker'].execute_welcomer(member, self.bot.cache['welcomer'][ctx.guild.id], test=True)
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

    @welcomer.command(
        name="setchannel",
        description="<#>|Sets the channel that welcomer will use")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def welcomer_setchannel(self, ctx, channel: typing.Optional[discord.TextChannel] = None):
        if not channel:
            message = rockutils._(
                "No {format} was mentioned. Either mention it, provide the id or name. If you are using the name, make sure you cover it in quotes like: `\"channel name\"`",
                ctx).format(
                    format="text channel")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        success = await self.bot.update_info(ctx, ["w.c", str(channel.id)])
        if success:
            message = rockutils._(
                "{key} has been successfully set to {value}",
                ctx).format(
                    key="Welcomer channel",
                    value=channel.mention)
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @welcomer.command(
        name="embeds",
        description="[enable/disable]|Toggles if embeds will be used to contain welcome messages",
        aliases=['embed', 'useembed', 'useembeds', 'em'])
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def welcomer_embeds(self, ctx, option=None):
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
            value = not ctx.guildinfo['w']['e']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        success = await self.bot.update_info(ctx, ["w.e", value])
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Embeds",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @welcomer.command(
        name="text",
        description="|Allows the configuring of welcomer text")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(['send_embeds'])
    async def welcomer_text(self, ctx):
        dashlink = f"{self.bot.config['bot']['site']}/dashboard/changeguild/{ctx.guild.id}"
        message = rockutils._(
            "Configuring welcomer settings have now been moved to the dashboard [here]({dashboardlink}) to allow for more ease of use",
            ctx).format(
            dashboardlink=dashlink)
        message += "\n\n"
        message += rockutils._("To configure your Welcomer config, click the link above, log in and click on the Welcomer group on the sidebar. If you need any help, you can find the support server on the site.", ctx)
        embed = discord.Embed(
            title="We have moved",
            colour=3553599,
            url=dashlink,
            description=message)
        embed.set_image(url=f"{self.bot.config['bot']['site']}/static/promo/moved-final.png")
        await ctx.send(embed=embed)

    @welcomer.command(
        name="images",
        description="|Allows the configuring of welcomer images")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    @customchecks.requires_permission(['send_embeds'])
    async def welcomer_images(self, ctx):
        dashlink = f"{self.bot.config['bot']['site']}/dashboard/changeguild/{ctx.guild.id}"
        message = rockutils._(
            "Configuring welcomer settings have now been moved to the dashboard [here]({dashboardlink}) to allow for more ease of use",
            ctx).format(
            dashboardlink=dashlink)
        message += "\n\n"
        message += rockutils._("To configure your Welcomer config, click the link above, log in and click on the Welcomer group on the sidebar. If you need any help, you can find the support server on the site.", ctx)
        embed = discord.Embed(
            title="We have moved",
            colour=3553599,
            url=dashlink,
            description=message)
        embed.set_image(url=f"{self.bot.config['bot']['site']}/static/promo/moved-final.png")
        await ctx.send(embed=embed)

    @welcomer.command(
        name="dms",
        description="|Allows the configuring of welcomer direct messages")
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def welcomer_dms(self, ctx):
        dashlink = f"{self.bot.config['bot']['site']}/dashboard/changeguild/{ctx.guild.id}"
        message = rockutils._(
            "Configuring welcomer settings have now been moved to the dashboard [here]({dashboardlink}) to allow for more ease of use",
            ctx).format(
            dashboardlink=dashlink)
        message += "\n\n"
        message += rockutils._("To configure your Welcomer config, click the link above, log in and click on the Welcomer group on the sidebar. If you need any help, you can find the support server on the site.", ctx)
        embed = discord.Embed(
            title="We have moved",
            colour=3553599,
            url=dashlink,
            description=message)
        embed.set_image(url=f"{self.bot.config['bot']['site']}/static/promo/moved-final.png")
        await ctx.send(embed=embed)

    # @welcomer.command(
    #     name="formatting",
    #     description="|Displays formatting that welcomer uses")
    # @customchecks.requires_guild()
    # @customchecks.requires_elevation()
    # async def welcomer_formatting(self, ctx):
    #     dashlink = f"{self.bot.config['bot']['site']}/formatting"
    #     message = rockutils._(
    #         "Formatting list has now been moved [here]({dashboardlink}).").format(
    #             dashboardlink=dashlink)
    #     embed = discord.Embed(
    #         title="We have moved",
    #         colour=3553599,
    #         url=dashlink,
    #         description=message)
    #     await ctx.send(embed=embed)

    @welcomer.command(
        name="formatting",
        aliases=[
            'markdown',
            'text-formatting',
            'textformatting',
            'format'],
        description="|Lists all welcomer text formatting")
    async def welcomer_markdown(self, ctx):
        mmessage = r"**Must be in the format \{key\}**\n\n"
        for mark_title, mark_list in markdown.items():
            mmessage += f"**{mark_title.upper()}**\n"
            for mark_tag, mark_desc in mark_list.items():
                message = f"{mark_tag} - `{mark_desc}`\n"
                if len(message) + len(mmessage) > 2048:
                    await self.bot.send_data(ctx, mmessage, ctx.userinfo, title="Welcomer Text Formatting", force_guild=True)
                    mmessage = ""
                mmessage += message
            mmessage += "\n"
        await self.bot.send_data(ctx, mmessage, ctx.userinfo, title=f"Welcomer Text Formatting", force_guild=True)


def setup(bot):
    bot.add_cog(Welcomer(bot))
