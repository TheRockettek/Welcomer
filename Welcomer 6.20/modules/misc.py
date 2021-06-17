import io
import math
import random
import sys
import time
import typing
import zipfile

import numpy as np
import aiohttp
import discord
import psutil
from discord.ext import commands
from datetime import datetime
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont, ImageOps
from collections import Counter

import ujson as json
from rockutils import customchecks, rockutils


def get_size(obj, seen=None):
    """Recursively finds size of objects"""

    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'K', 'M', 'G']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def sizeof_fmt_mb(num, suffix='B'):
    for unit in ['M', 'G']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


class Miscellaneous(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # time in seconds between rep. 86400 is 1 day
        self.rep_delay = 86400

    @commands.command(
        name="inspiration",
        description="|Get some inspiration from inspirobot"
    )
    async def inspiration(self, ctx):
        embed = discord.Embed(title="Heres a quote to keep you inspired")

        async with aiohttp.ClientSession() as session:
            async with session.get("http://inspirobot.me/api?generate=true") as resp:
                res = await resp.text()

        embed.set_image(url=res)
        await ctx.send(embed=embed)

    @commands.command(
        name="randomreactions",
        description="<message id> <reaction> <count>| Returns count of users who reacted with reaction on message with id"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def randomreactions(self, ctx, messageid: int, reaction: str, count: int = 1):
        message = await ctx.channel.fetch_message(messageid)
        if message:
            for _reaction in message.reactions:
                if type(_reaction.emoji) in [discord.Emoji, discord.PartialEmoji]:
                    if str(_reaction.emoji) == reaction:
                        reactors = await _reaction.users().flatten()
                        winners = random.choices(reactors, k=count)
                        await ctx.send(f"Winners are: {' '.join([w.mention for w in winners])}")
                        return
                else:
                    if _reaction.emoji == reaction:
                        reactors = await _reaction.users().flatten()
                        winners = random.choices(reactors, k=count)
                        await ctx.send(f"Winners are: {' '.join([w.mention for w in winners])}")
                        return
            else:
                await ctx.send(f"Could not find any reactions that are {str(reaction)} in that message")
        else:
            await ctx.send("Could not find message with that id in this channel")

    @commands.command(
        name="joingraph",
        description="...|Join graph"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def joingraph(self, ctx):
        counts = Counter([datetime.strftime(u.joined_at, '%b %Y')
                          for u in ctx.guild.members])
        plt.rcdefaults()
        plt.rcParams["figure.figsize"] = [12.8, 4.8]

        _stats = sorted(
            counts.items(), key=lambda o: datetime.strptime(o[0], "%b %Y"))

        keys = list(map(lambda o: o[0], _stats))
        values = list(map(lambda o: int(o[1]), _stats))
        y_pos = np.arange(len(keys))

        plt.bar(y_pos, values, align='center', alpha=0.5, color="green")
        plt.xticks(y_pos, keys, rotation=30, horizontalalignment='right')

        plt.title('User joins')
        _bio = io.BytesIO()
        plt.savefig(_bio, format="png", transparent=False, bbox_inches='tight')
        plt.clf()
        _bio.seek(0)
        file = discord.File(_bio, filename="output.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://output.png")
        await ctx.send(file=file, embed=embed)

    @commands.command(
        name="weirdgraph",
        description="[user...]|Noone knows what this means"
    )
    @customchecks.requires_guild()
    async def wierdgraph(self, ctx, users: commands.Greedy[discord.User]):
        start = time.time()
        # users = list(set(users))
        if len(users) == 0:
            return await ctx.send("You need at least 1 user")

        sub = Image.open("horrible.png")
        main = Image.new("RGBA", (sub.width, sub.height))

        m = {}
        for x in range(9):
            m[x] = {}
            for y in range(9):
                m[x][y] = True
        m[4][4] = False

        for user in users:
            for i in range(1000):
                x = random.randint(0, 8)
                y = random.randint(0, 8)
                if m[x][y]:
                    m[x][y] = False
                    break
            else:
                break

            ava = io.BytesIO()
            await user.avatar_url_as(format="png", size=64).save(ava)
            ava.seek(0)

            _ava = Image.open(ava)
            if _ava.format == "RGBA":
                main.paste(_ava, (50+(x*64), 50+(y*64)), _ava)
            else:
                main.paste(_ava, (50+(x*64), 50+(y*64)))

        out = io.BytesIO()
        sub.paste(main, (0, 0), main)
        sub.save(out, "PNG")
        out.seek(0)

        await ctx.send(f"Done in {math.ceil((time.time() - start)*1000)} ms", file=discord.File(out, "weirdgraph.png"))

    @commands.command(
        name="guildgraph",
        description="...|Guild graph"
    )
    @customchecks.requires_guild()
    async def guildgraph(self, ctx):
        data = await self.bot.broadcast("guildcount", "*")

        counts = Counter()
        for i in data['d'].values():
            if i.get("success", True):
                counts += i

        plt.rcdefaults()
        plt.rcParams["figure.figsize"] = [18, 4.8]

        _stats = sorted(
            counts.items(), key=lambda o: datetime.strptime(o[0], "%b %Y"))

        keys = list(map(lambda o: o[0], _stats))
        values = list(map(lambda o: int(o[1]), _stats))
        y_pos = np.arange(len(keys))

        plt.bar(y_pos, values, align='center', alpha=0.5, color="green")
        plt.xticks(y_pos, keys, rotation=30, horizontalalignment='right')

        plt.title('Kinda guild joins')
        _bio = io.BytesIO()
        plt.savefig(_bio, format="png", transparent=False, bbox_inches='tight')
        plt.clf()
        _bio.seek(0)
        file = discord.File(_bio, filename="output.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://output.png")
        await ctx.send(file=file, embed=embed)

    @commands.command(
        name="membergraph",
        description="...|Member graph"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def membergraph(self, ctx):
        counts = Counter([datetime.strftime(u.joined_at, '%b %Y')
                          for u in ctx.guild.members])
        plt.rcdefaults()
        plt.rcParams["figure.figsize"] = [12.8, 4.8]

        _stats = sorted(
            counts.items(), key=lambda o: datetime.strptime(o[0], "%b %Y"))

        keys = list(map(lambda o: o[0], _stats))
        values = list(map(lambda o: int(o[1]), _stats))
        y_pos = np.arange(len(keys))

        for i, k in enumerate(values):
            if i > 0:
                values[i] += values[i-1]

        plt.bar(y_pos, values, align='center', alpha=0.5, color="green")
        plt.xticks(y_pos, keys, rotation=30, horizontalalignment='right')

        plt.title('User joins')
        _bio = io.BytesIO()
        plt.savefig(_bio, format="png", transparent=False, bbox_inches='tight')
        plt.clf()
        _bio.seek(0)
        file = discord.File(_bio, filename="output.png")
        embed = discord.Embed()
        embed.set_image(url="attachment://output.png")
        await ctx.send(file=file, embed=embed)

    @commands.command(
        name="sendtext",
        description="...|Sends some text"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def sendtext(self, ctx, channel: typing.Optional[discord.TextChannel] = None, *, text):
        if channel is None:
            channel = ctx.channel
        await channel.send(text)

    @commands.command(
        name="editembed",
        description="<messageid> ...|Sends an embed from an custom embed format. Find builder at https://welcomer.fun/customembeds"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def editembed(self, ctx, messageid: int, *, data):
        try:
            msg = await ctx.channel.fetch_message(messageid)
        except Exception as e:
            return await ctx.send(f"Could not find this message: {e}")

        data = json.loads(data)

        if "embed" in data:
            content = data.get("content", None)
            embed = discord.Embed.from_dict(data['embed'])
            await msg.edit(content=content, embed=embed)
        else:

            if isinstance(data.get('color', None), str):
                data['color'] = int(data['color'].replace("#", ""), 16)
            if data.get("footer"):
                data['footer'] = {"text": data.get("footer")}

            embed = discord.Embed.from_dict(data)
            await msg.edit(embed=embed)

    @commands.command(
        name="sendembed",
        description="...|Sends an embed from an custom embed format. Find builder at https://welcomer.fun/customembeds"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def sendembed(self, ctx, *, data):
        data = json.loads(data)

        if "embed" in data:
            content = data.get("content", None)
            embed = discord.Embed.from_dict(data['embed'])
            await ctx.send(content=content, embed=embed)
        else:

            if isinstance(data.get('color', None), str):
                data['color'] = int(data['color'].replace("#", ""), 16)
            if data.get("footer"):
                data['footer'] = {"text": data.get("footer")}

            embed = discord.Embed.from_dict(data)
            await ctx.send(embed=embed)

    # @commands.command(
    #     name="choosefromroles",
    #     description="<roles>|Choses one user from a list of roles you provide"
    # )
    # async def choosefromroles(self, ctx, roles: commands.Greedy[discord.Role]):
    #     members = set()
    #     for role in roles:
    #         for member in role.members:
    #             members.add(member)
    #     winner = random.choice(list(members))
    #     if winner.id == 680835476034551925:
    #         await ctx.send(f"{winner} sucks lol :^)")
    #     await ctx.send(f"From a random list of {len(members)} users, the winner was {winner}")

    @commands.command(
        name="stealemoji",
        description="<emoji>|Steals an emoji"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def stealemoji(self, ctx, emoji: typing.Union[discord.Emoji, discord.PartialEmoji], text=None):
        _url = emoji.url
        e = ""
        if not text:
            _name = emoji.name
        else:
            e = f" as {text}"
            _name = text

        async with aiohttp.ClientSession() as session:
            resp = await session.get(str(_url))
            respo = await resp.read()
        imageobj = io.BytesIO(respo)
        imageobj.seek(0)

        _e = await ctx.guild.create_custom_emoji(name=_name, image=imageobj.getvalue())
        await ctx.send(f"I have stolen {_e}{e}")

    @commands.command(
        name="embeddata",
        description="<channel> <message>|Sends embed data"
    )
    async def embeddata(self, ctx, c: int, m: int):
        _c = ctx.guild.get_channel(c)
        _m = await _c.fetch_message(m)
        await ctx.send(str(_m.embeds[0].to_dict()))

    @commands.command(
        name="textblock",
        description="<prefix> ...|Makes emojis from your text"
    )
    @customchecks.requires_guild()
    @customchecks.requires_elevation()
    async def textblock(self, ctx, alias, *, text):

        m = await ctx.send("Creating image")
        s = time.time()

        max_height = 40

        fontsize = max_height
        while fontsize > 5:
            font = ImageFont.truetype("/home/rock/CDN/default.ttf", fontsize)
            width, height = font.getsize(text)
            if height > 55:
                fontsize -= 1
            else:
                break
        image = Image.new("RGBA", (width, height))
        imagedraw = ImageDraw.Draw(image)
        imagedraw.text((0, 0), text, fill=(114, 137, 218), font=font)
        # lowest = 15
        # lowestval = 100
        # for i in range(15, 0, -1):
        #     if abs((image.width / i) - height) < lowestval:
        #         lowest = i
        #         lowestval = abs((i / width) - height)
        parts = []
        # imagewidths = round(image.width / lowest)
        # totalimages = math.floor(image.width / imagewidths)
        # print(totalimages, image.width, imagewidths)
        # for f in range(totalimages):
        #     box = (
        #         f * imagewidths, 0,
        #         (f * imagewidths) + (imagewidths - 1), image.height - 1
        #     )
        # crop = image.crop(box)
        # _bio = io.BytesIO()
        # print(box)
        # crop.save(_bio, "PNG")
        # _bio.seek(0)
        # parts.append(_bio)

        blocks = math.ceil(image.width / image.height)
        for i in range(blocks):
            box = (
                i * image.height, 0,
                min(image.width, ((i + 1) * image.height)), image.height
            )
            crop = Image.new("RGBA", (image.height, image.height), 255)
            cropped = image.crop(box)

            crop.paste(cropped, (0, 0), cropped)
            if crop.size != cropped.size:
                cropped = ImageOps.fit(
                    cropped, crop.size, centering=(
                        0.0, 0.0), method=Image.ANTIALIAS)

            crop = Image.alpha_composite(crop, cropped)

            _bio = io.BytesIO()
            crop.save(_bio, "PNG")
            _bio.seek(0)
            parts.append(_bio)

        meem = []
        for num, emoji in enumerate(parts):
            await m.edit(content=f"Creating emojis {num}/{len(parts)}")

            _e = await ctx.guild.create_custom_emoji(name=f"{alias}{num}", image=emoji.read())
            meem.append(_e)
        await m.edit(content=f"Done in {math.ceil((time.time()-s)*10000)/10}ms\n{''.join(str(m) for m in meem)}")

    @commands.command(
        name="biggest",
        description="[limit=10]|Returns a list of the biggest guilds")
    async def biggest(self, ctx, limit: typing.Optional[int] = 10):
        if limit > 100:
            limit = 100

        data = await self.bot.broadcast("filterguilds", "*", [0, False, 100, 1])

        aguilds = []

        for shard, guild_list in data['d'].items():
            if isinstance(guild_list, dict) and guild_list['success']:
                for guild in guild_list['guilds']:
                    guild['shard'] = shard
                    aguilds.append(guild)

        fguilds = []
        ids = []
        for guild in aguilds:
            if guild['id'] not in ids:
                fguilds.append(guild)
            ids.append(guild['id'])
        guilds = sorted(fguilds, key=lambda o: o['users'], reverse=True)[
            :limit]
        message = ""
        for number, guild in enumerate(guilds):
            submessage = f"**{number+1}**) **{guild['name']}** - **{guild['users']}** users [Guild Info](https://welcomer.fun/g/{guild['id']}) [Invite](https://welcomer.fun/i/{guild['id']}) ({guild['shard']})\n"
            if len(message) + len(submessage) > 2000:
                embed = discord.Embed(
                    title="Biggest Guilds", description=message)
                await ctx.send(embed=embed)
                message = ""
            message += submessage
        embed = discord.Embed(title="Biggest Guilds", description=message)
        await ctx.send(embed=embed)

    @commands.group(
        name="membership",
        description="gift|Commands to manage your membership",
        case_insensitive=True,
        invoke_without_command=True)
    async def membership(self, ctx):
        await self.bot.walk_help(ctx, ctx.command)
        # await self.bot.get_command("membership list").invoke(ctx)

    @membership.command(
        name="list",
        description="|Gives information on your current subscription")
    async def membership_list(self, ctx):
        limit = 0
        limit += 1 if ctx.userinfo['m']['1']['h'] else 0
        limit += 3 if ctx.userinfo['m']['3']['h'] else 0
        limit += 5 if ctx.userinfo['m']['5']['h'] else 0

        if await self.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True, trusted=True):
            limit = 42069

        message = ""
        has_donated = await self.bot.has_guild_donated(ctx.guild, ctx.guildinfo, donation=True, partner=True)

        if ctx.guild:
            message += "__Guild Memberships__\n\n"
            message += f"Active Membership: {self.bot.get_emote('checkboxmarkedoutline' if has_donated else 'closeboxoutline')}\n"
            message += f"Custom Backgrounds: {self.bot.get_emote('checkboxmarkedoutline' if ctx.guildinfo['d']['b']['hb'] else 'closeboxoutline')}\n\n"

        message += "__Your Memberships__\n\n"
        message += f"Custom Backgrounds: {self.bot.get_emote('checkboxmarkedoutline' if ctx.userinfo['m']['hs'] or ctx.userinfo['m']['1']['h'] or ctx.userinfo['m']['3']['h'] or ctx.userinfo['m']['5']['h'] else 'checkboxblankoutline')}\n"
        message += f"Welcomer x1: {self.bot.get_emote('checkboxmarkedoutline' if ctx.userinfo['m']['1']['h'] else 'checkboxblankoutline')} {self.bot.get_emote('patreon') if ctx.userinfo['m']['1']['p'] else ''}\n"
        message += f"Welcomer x3: {self.bot.get_emote('checkboxmarkedoutline' if ctx.userinfo['m']['3']['h'] else 'checkboxblankoutline')} {self.bot.get_emote('patreon') if ctx.userinfo['m']['3']['p'] else ''}\n"
        message += f"Welcomer x5: {self.bot.get_emote('checkboxmarkedoutline' if ctx.userinfo['m']['5']['h'] else 'checkboxblankoutline')} {self.bot.get_emote('patreon') if ctx.userinfo['m']['5']['p'] else ''}\n\n"
        message += f"__Given Guilds (**{len([g for g in ctx.userinfo['m']['s'] if g['type'] != 'cbg'])}/{limit}**) __\n\n"

        for guild in ctx.userinfo['m']['s']:
            if guild['type'] != "cbg":
                submessage = f"{self.bot.get_emote('imageframe' if guild['type'] == 'cbg' else 'starbox')} {guild['name']} `{guild['id']}`\n"

                if len(message) + len(submessage) > 2048:
                    embed = discord.Embed(
                        title="Bot Information", description=message)
                    await ctx.send(embed=embed)
                    message = ""
                message += submessage

        if len(ctx.userinfo['m']['s']) == 0:
            if limit > 0:
                message += f"To add memberships, do `{ctx.prefix}membership add`"
            else:
                message += f"To add memberships, you must donate first at `{ctx.prefix}donate`"

        embed = discord.Embed(title="Welcomer Membership", description=message)
        await ctx.send(embed=embed)

    @membership.command(
        name="add",
        description="[guild id]|Gives the current guild or the guild specified a membership")
    async def membership_add(self, ctx, guild_id: int = None):
        if not guild_id:
            if ctx.guild:
                guild_id = ctx.guild.id
            else:
                message = rockutils._(
                    "No {target}, which is required, was specified",
                    ctx).format(
                        target="guild id")
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        limit = 0
        limit += 1 if ctx.userinfo['m']['1']['h'] else 0
        limit += 3 if ctx.userinfo['m']['3']['h'] else 0
        limit += 5 if ctx.userinfo['m']['5']['h'] else 0

        if await self.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True, trusted=True):
            limit = 42069

        if len(ctx.userinfo['m']['s']) >= limit:
            message = rockutils._(
                "You have used your limit of **{limit}** guilds. To increase this limit you require a higher tiered Welcomer Pro plan. Find out more at `{command}`\nIf you meant to add a custom background, run `{acbcommand}` instead",
                ctx).format(
                limit=limit,
                command=f"{ctx.prefix}donate",
                acbcommand=f"{ctx.prefix}membership addcustombackground")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            guild = await self.bot.fetch_guild(guild_id)
        if not guild:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid guild id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        guild_info = await self.bot.get_guild_info(guild.id, refer="membership add")
        guild_info['d']['de'].append(str(ctx.author.id))
        guild_info['d']['de'] = list(set(guild_info['d']['de']))
        guild_info['d']['b']['hb'] = True
        success = await self.bot.update_guild_info(guild.id, guild_info, refer="membership add")

        if success:
            guild_serialized = self.bot.serialiser.guild(guild)
            guild_serialized['type'] = "don"
            ctx.userinfo['m']['s'] = list(
                filter(
                    lambda o: not (
                        o['id'] == str(
                            guild.id)),
                    ctx.userinfo['m']['s']))
            print(ctx.userinfo['m']['s'])
            ctx.userinfo['m']['s'].append(guild_serialized)
            success = await self.bot.update_user_info(ctx.author.id, ctx.userinfo)
            if success:
                message = rockutils._(
                    "You have successfully given **{name}** a membership. You have used **{used}** of your current limit of **{limit}**",
                    ctx).format(
                    name=guild.name,
                    used=len(
                        ctx.userinfo['m']['s']),
                    limit=limit)
                await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
            else:
                message = rockutils._(
                    "There was a problem when saving changes. Please try again", ctx)
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @membership.command(
        name="addcustombackground",
        description="[guild id]|Gives the current guild or the guild specified a custom background membership forever",
        alias=['addbackground'])
    async def membership_addcustombackground(self, ctx, guild_id: int = None):
        if not guild_id:
            if ctx.guild:
                guild_id = ctx.guild.id
            else:
                message = rockutils._(
                    "No {target}, which is required, was specified",
                    ctx).format(
                        target="guild id")
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if not (ctx.userinfo['m']['hs'] or ctx.userinfo['m']['1']['h'] or ctx.userinfo['m']['3']['h'] or ctx.userinfo['m']['5']['h']) and not await self.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True, trusted=True):
            message = rockutils._(
                "You are unable to add a custom background as you have not donated for this. Find out more at `{command}`",
                ctx).format(
                command=f"{ctx.prefix}donate")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            guild = await self.bot.fetch_guild(guild_id)
        if not guild:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid guild id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        guild_info = await self.bot.get_guild_info(guild.id, refer="membership addcbg")
        guild_info['d']['b']['hb'] = True
        success = await self.bot.update_guild_info(guild.id, guild_info, refer="membership addcbg")

        if success:
            guild_serialized = self.bot.serialiser.guild(guild)
            guild_serialized['type'] = "cbg"
            ctx.userinfo['m']['s'] = list(
                filter(
                    lambda o: not (
                        o['id'] == str(
                            guild.id) and o['type'] == "cbg"),
                    ctx.userinfo['m']['s']))
            ctx.userinfo['m']['s'].append(guild_serialized)
            success = await self.bot.update_user_info(ctx.author.id, ctx.userinfo, refer="membership addcbg")
            if success:
                message = rockutils._(
                    "You have successfully given **{name}** a custom background",
                    ctx).format(
                        name=guild.name)
                await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
            else:
                message = rockutils._(
                    "There was a problem when saving changes. Please try again", ctx)
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @membership.command(
        name="removecustombackground",
        description="[guild id]|Removes the current guild or the guild specified's custom background membership",
        alias=['removebackground'])
    @customchecks.requires_elevation()
    async def membership_removecustombackground(self, ctx, guild_id: int = None):
        if not guild_id:
            if ctx.guild:
                guild_id = ctx.guild.id
            else:
                message = rockutils._(
                    "No {target}, which is required, was specified",
                    ctx).format(
                        target="guild id")
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        guild_info = await self.bot.get_guild_info(guild_id, refer="membership removecbg")
        if not guild_info:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid guild id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        guild_info['d']['b']['hb'] = False
        success = await self.bot.update_guild_info(guild_id, guild_info, refer="membership removecbg")

        if success:
            message = rockutils._(
                "You have removed the custom background")
            await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @membership.command(
        name="remove",
        description="[guild id]|Removes a membership from a specific server if you have given it a membership")
    async def membership_remove(self, ctx, guild_id: int = None):
        if not guild_id:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="guild id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        limit = 0
        limit += 1 if ctx.userinfo['m']['1']['h'] else 0
        limit += 3 if ctx.userinfo['m']['3']['h'] else 0
        limit += 5 if ctx.userinfo['m']['5']['h'] else 0

        if await self.bot.has_special_permission(ctx.author, support=True, developer=True, admin=True, trusted=True):
            limit = 42069

        guild_info = await self.bot.get_guild_info(guild_id, refer="membership remove")
        if not guild_info:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid guild id")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if ctx.author.id in guild_info['d']['de']:
            guild_info['d']['de'].remove(ctx.author.id)
        success = await self.bot.update_guild_info(guild_id, guild_info, refer="membership remove")
        if success:
            ctx.userinfo['m']['s'] = list(
                filter(
                    lambda o: not (
                        o['id'] == str(
                            guild_id) and o['type'] == "don"),
                    ctx.userinfo['m']['s']))
            success = await self.bot.update_user_info(ctx.author.id, ctx.userinfo)
            if success:
                message = rockutils._(
                    "You have successfully removed your membership from **{name}**. You have used **{used}** of your current limit of **{limit}**",
                    ctx).format(
                    name=guild_id,
                    used=len(
                        ctx.userinfo['m']['s']),
                    limit=limit)
                await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
            else:
                message = rockutils._(
                    "There was a problem when saving changes. Please try again", ctx)
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="prefix",
        description="|Returns prefix for current server")
    @customchecks.requires_guild()
    async def prefix(self, ctx):
        message = rockutils._(
            "This prefix for this server is `{prefix}`",
            ctx).format(
            prefix=ctx.prefix)
        await ctx.send(f"{self.bot.get_emote('check')}  | " + message)

    @commands.command(
        name="cluster",
        description="|Returns statistics for the cluster")
    async def cluster(self, ctx):
        p = psutil.Process()
        mi = p.memory_info()

        message = ""
        message += f"Cluster: **{self.bot.cluster_id}**\n"
        message += f"Uptime: {rockutils.since_seconds_str(time.time() - self.bot.init_time, allow_secs=True, include_ago=False)}\n\n"

        message += f"Guilds: **{len(self.bot.guilds)}**\n"
        message += f"Users: **{len(self.bot.users)}**\n\n"

        message += f"Shards: #**{min(self.bot.shards)}** - #**{max(self.bot.shards)}**\n"
        message += f"Library: **{discord.__name__} {discord.__version__}**\n\n"

        message += f"Memory (RSS): **{sizeof_fmt(mi.rss)}**\n"
        message += f"Memory (SHR): **{sizeof_fmt(mi.shared)}**\n"
        message += f"Threads: **{p.num_threads()}** (**{p.num_threads() - (psutil.cpu_count() * 5)}**)\n\n"

        for shard in self.bot.latencies:
            ms = math.ceil(shard[1] * 1000)
            submessage = f"{self.bot.get_emote('status_idle' if ms > 500 else 'status_online')}Shard **{shard[0]}** - **{ms}**ms\n"

            if len(message) + len(submessage) > 2000:
                embed = discord.Embed(
                    title="Cluster Information", description=message)
                await ctx.send(embed=embed)
                message = ""

            message += submessage

        embed = discord.Embed(title="Cluster Information", description=message)
        await ctx.send(embed=embed)

    @commands.command(
        name="botinfo",
        description="|Returns statistics for the entire bot")
    async def botinfo(self, ctx):
        data = await self.bot.broadcast("botinfo", "*")
        guilds = 0
        members = 0
        unique = 0
        threads = 0
        mbused = 0

        for clusterdata in data['d'].values():
            guilds += clusterdata['guilds']
            unique += clusterdata['unique']
            mbused += clusterdata['mbused']
            members += clusterdata['members']
            threads += clusterdata['threads']

        message = ""
        message += f"Guilds: **{guilds}**\n"
        message += f"Users: **{members}**\n"
        message += f"Uniq. Users: **{unique}**\n\n"

        message += f"Shards: #**{min(self.bot.shards)}** - #**{max(self.bot.shards)}**\n"
        message += f"Total Shards: **{self.bot.shard_count}**\n"
        message += f"Clusters: **{self.bot.cluster_count}**\n\n"

        message += f"Library: **{discord.__name__} {discord.__version__}**\n"
        message += f"Version: Welcomer **{self.bot.config['bot']['version']}**\n"
        message += f"Memory used: **{sizeof_fmt_mb(mbused)}**\n"
        message += f"Threads: **{threads}**\n\n"

        embed = discord.Embed(title="Bot Information", description=message)
        fields = 0

        for clusterid, clusterdata in data['d'].items():
            try:
                ms = math.ceil(clusterdata['latency'] * 1000)
            except:
                ms = "?"

            title = f"{self.bot.get_emote('status_idle' if ms > 500 else 'status_online')}"
            if clusterid == str(self.bot.cluster_id):
                title += f"**Cluster {clusterid}**"
            else:
                title += f"Cluster {clusterid}"
            title += f" - {ms}ms\n"

            submessage = f"Uptime: {rockutils.produce_timestamp(clusterdata['uptime'])}\n"
            submessage += f"Guilds: {clusterdata['guilds']} ({clusterdata['members']}/{clusterdata['unique']})\n\n"
            embed.add_field(name=title, value=submessage, inline=True)

            if fields >= 25:
                await ctx.send(embed=embed)
                embed = discord.Embed()

        if embed != discord.Embed():
            await ctx.send(embed=embed)

    @commands.command(
        name="badges",
        description="[@]|Lists your or someone elses badge badges")
    async def badges(self, ctx, user: discord.Member = None):
        if user and user != ctx.author:
            user = await self.bot.get_user_info(user.id)
            badges = user['b']
        else:
            badges = ctx.userinfo['b']
        message = ""
        for badge in badges:
            message += f"{badge[0]} **{badge[1]}**  | `{badge[2]}`\n"
        if len(badges) == 0:
            message = "You/They do not have any badges :("
        embed = discord.Embed(title="Badges", description=message)
        await ctx.send(embed=embed)

    @commands.command(
        name="ping",
        description="|Returns latencies for all clusters")
    async def ping(self, ctx):
        _time = time.time()
        data = await self.bot.broadcast("heartbeat", "*")

        message = ""

        for clusterid, clusterdata in data['d'].items():
            try:
                latency = math.ceil(clusterdata['latency'] * 1000)
            except:
                latency = "?"
            ipcping = math.ceil((clusterdata['time'] - _time) * 1000)
            message += f"Cluster **{clusterid}**: **{latency}**ms (IPC: **{ipcping}**ms)\n"

        embed = discord.Embed(title="Bot Ping", description=message)
        await ctx.send(embed=embed)

    @commands.command(
        name="donate",
        description="|Information on donating")
    async def donate(self, ctx):
        embed = discord.Embed(
            description="Want to help out with the development and hosting of Welcomer? You can now unlock more features by donating towards the bot. You can either get monthly plans with Patreon or pay one month at a time with paypal. You also unlock more savings by choosing longer duration!\n\n[I want to know more](https://welcomer.fun/donate)\n[Visit the Patreon](https://www.patreon.com/WelcomerBot)\n\n[Why are certain features locked to donators only?](https://welcomer.fun/donate)")
        embed.add_field(name="Custom Welcome Backgrounds",
                        value="Donator Only Bot")
        embed.add_field(name="Unlimited Server Stat Slots",
                        value="Animated Welcomer Backgrounds")
        embed.add_field(name="Timed Roles",
                        value="... Any many more features!")
        await ctx.send(embed=embed)

    @commands.group(
        name="rep",
        description="star|Give users reputation or view your own",
        case_insensitive=True,
        invoke_without_command=True)
    async def rep(self, ctx):
        await self.bot.get_command("rep get").invoke(ctx)

    @rep.command(
        name="get",
        description="[@]|Returns your reputation or someone elses")
    async def rep_get(self, ctx, member: typing.Optional[discord.User] = None):
        if member and member != ctx.author:
            userinfo = await self.bot.get_user_info(member.id)
            isme = False
        else:
            userinfo = ctx.userinfo
            isme = True

        message = rockutils._(
            "{mention} reputation count is `{reputation}`",
            ctx).format(
                mention="Your" if isme else f"{member}'s",
                reputation=userinfo['r']['r'])
        await ctx.send(f"{self.bot.get_emote('check')}  | " + message)

    @rep.command(
        name="give",
        description="[@]|Gives someone else reputation")
    async def rep_give(self, ctx, member: typing.Optional[discord.User] = None):
        if not member:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="target member")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        if member.id == ctx.author.id:
            message = rockutils._("You are unable to rep yourself", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        _time = time.time()
        if (_time - ctx.userinfo['r']['l']) < self.rep_delay:
            message = rockutils._(
                "You are unable to rep yet. Time left: {time}", ctx).format(
                time=rockutils.since_seconds_str(
                    self.rep_delay - (time.time() - ctx.userinfo['r']['l']),
                    allow_secs=True, include_ago=False))
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        userinfo = await self.bot.get_user_info(member.id)
        userinfo['r']['r'] += 1
        success = await self.bot.update_user_info(member.id, userinfo)
        if success:
            ctx.userinfo['r']['l'] = _time
            success = await self.bot.update_user_info(ctx.author.id, ctx.userinfo)
            if success:
                message = rockutils._(
                    "You have given {user} a rep point. You can rep again in {time}", ctx).format(
                    user=member.name, time=rockutils.since_seconds_str(
                        self.rep_delay, allow_secs=True, include_ago=False))
                return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
            else:
                message = rockutils._(
                    "There was a problem when saving changes. Please try again", ctx)
                return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(
        name="invites",
        description="|Lists users who invite the most users",
        aliases=['invite', 'guildinvites', 'guildinvite', 'topinvites', 'topinvite'])
    @customchecks.requires_guild()
    @customchecks.requires_permission(["manage_guild"])
    async def invites(self, ctx):
        inviters = {}
        invites = await self.bot.serialiser.invites(ctx.guild)

        for invite in invites:
            if not invite['inviter'] in inviters:
                inviters[invite['inviter']] = 0
            inviters[invite['inviter']] += invite['uses']

        if "Unknown" in inviters:
            del inviters['Unknown']

        sorted_keys = sorted(
            inviters.keys(), key=lambda i: inviters[i], reverse=True)
        sorted_values = list(map(lambda i: inviters[i], sorted_keys))
        sorted_invites = dict(zip(sorted_keys, sorted_values))

        myinvites = 0
        inviteposition = -1
        if str(ctx.author.id) in sorted_invites.keys():
            myinvites = inviters[str(ctx.author.id)]
            inviteposition = list(sorted_invites.keys()).index(
                str(ctx.author.id)) + 1

        limit = 15

        message = ""
        message += f"You have invited {myinvites} user{'s' if myinvites != 1 else ''}\n"
        if 100 > inviteposition >= 1:
            message += f"You are current #**{inviteposition}** on the invite leaderboard\n"
        else:
            message += f"You are not currently on the invite leaderboard. Invite more users!\n"
        message += "\n"

        position = 0
        for user_id, invites in sorted_invites.items():
            position += 1
            user = self.bot.get_user(int(user_id))
            submessage = f"**{position}**) {user if user else f'Unknown user {user_id}'} - **{invites}** invite{'s' if invites != 1 else ''}\n"
            if len(message) + len(submessage) > 2048:
                embed = discord.Embed(
                    title="Invite Leaderboard", description=message)
                await ctx.send(embed=embed)
                message = ""
            message += submessage

            if position >= limit:
                break

        if len(message.strip()) > 0:
            embed = discord.Embed(
                title="Invite Leaderboard", description=message)
            await ctx.send(embed=embed)

    @commands.command(
        name="newusers",
        description="[limit<100]|Lists new users who have joined")
    @customchecks.requires_guild()
    async def newusers(self, ctx, limit: int = 5):
        new_users = sorted(ctx.guild.members,
                           key=lambda o: o.joined_at.timestamp(), reverse=True)
        print(time.time() - new_users[0].joined_at.timestamp())
        print(time.time() - new_users[-1].joined_at.timestamp())
        message = ""
        for count, member in enumerate(new_users[:limit]):
            submessage = f"**{count + 1}**) {member} {member.mention} `{member.id}`\n**```Joined: {self.bot.maketimestamp(member.joined_at.timestamp())}\nCreated: {self.bot.maketimestamp(member.created_at.timestamp())}```**\n"
            if len(message) + len(submessage) > 2048:
                embed = discord.Embed(title="New Users", description=message)
                await ctx.send(embed=embed)
                message = ""
            message += submessage

        if len(message.strip()) > 0:
            embed = discord.Embed(title="New Users", description=message)
            await ctx.send(embed=embed)

    @commands.command(
        name="oldusers",
        description="[limit<100]|Lists oldest users who have joined")
    @customchecks.requires_guild()
    async def newusers(self, ctx, limit: int = 5):
        new_users = sorted(ctx.guild.members,
                           key=lambda o: o.joined_at.timestamp())
        print(time.time() - new_users[0].joined_at.timestamp())
        print(time.time() - new_users[-1].joined_at.timestamp())
        message = ""
        for count, member in enumerate(new_users[:limit]):
            submessage = f"**{count + 1}**) {member} {member.mention} `{member.id}`\n**```Joined: {self.bot.maketimestamp(member.joined_at.timestamp())}\nCreated: {self.bot.maketimestamp(member.created_at.timestamp())}```**\n"
            if len(message) + len(submessage) > 2048:
                embed = discord.Embed(title="Old Users", description=message)
                await ctx.send(embed=embed)
                message = ""
            message += submessage

        if len(message.strip()) > 0:
            embed = discord.Embed(title="Old Users", description=message)
            await ctx.send(embed=embed)

    @commands.command(
        name="preferdms",
        description="[enable/disable]|Toggles help should be sent in the guild or in dms",
        aliases=['dmhelp', 'usedms', 'deferguild'])
    async def preferdms(self, ctx, option=None):
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
            value = not ctx.userinfo['g']['b']['pd']
        else:
            value = True if option in [
                'enable', 'enabled', 'on', 'yes'] else False

        ctx.userinfo['g']['b']['pd'] = value
        success = await self.bot.update_user_info(ctx.author.id, ctx.userinfo)
        if success:
            message = rockutils._(
                "{key} has been successfully {value}",
                ctx).format(
                    key="Prefer Dms",
                    value="enabled" if value else "disabled")
            return await ctx.send(f"{self.bot.get_emote('check')}  | " + message)
        else:
            message = rockutils._(
                "There was a problem when saving changes. Please try again", ctx)
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

    @commands.command(name="guildinfo", description="|Displays information about the guild")
    async def guildinfo(self, ctx):
        games = {}
        discriminators = {}

        status = {
            "online": 0,
            "idle": 0,
            "dnd": 0,
            "offline": 0
        }
        verification_levels = {
            "none": "None",
            "low": "Low",
            "medium": "Medium",
            "high": "(╯°□°）╯︵ ┻━┻",
            "extreme": "┻━┻ ﾐヽ(ಠ益ಠ)ノ彡┻━┻"
        }
        content_filters = {
            "disabled": "None",
            "no_role": "No roles only",
            "all_members": "Everyone"
        }

        # for member in ctx.guild.members:
        #     status[str(member.status)] += 1
        #     if member.activity is not None and member.activity.name is not None:
        #         if member.activity.name not in games:
        #             games[member.activity.name] = {
        #                 "name": member.activity.name, "played": 0}
        #         games[member.activity.name]['played'] += 1

        #     if member.discriminator not in discriminators:
        #         discriminators[member.discriminator] = {
        #             "discriminator": member.discriminator, "people": 0}
        #     discriminators[member.discriminator]['people'] += 1

        # topgame = sorted(
        #     games.values(), key=lambda o: o['played'], reverse=True)[0]

        # discriminators = sorted(discriminators.values(),
        #                         key=lambda o: o['people'], reverse=True)
        # disc = discriminators[0]

        message = ""
        message += f"Guild: **{ctx.guild}** `{ctx.guild.id}`\n"
        message += f"Owner: **{ctx.guild.owner}** {ctx.guild.owner.mention}\n"
        message += f"Created: {rockutils.since_unix_str(ctx.guild.created_at.timestamp())}\n"
        message += f"\n"
        message += f"Region: **{str(ctx.guild.region).replace('-', ' ')}**\n"
        message += f"Content Filter: **{content_filters[str(ctx.guild.explicit_content_filter)]}**\n"
        if ctx.guild.afk_channel:
            message += f"AFK Timeout: **{int(ctx.guild.afk_timeout/60)}** minutes {ctx.guild.afk_channel.name}\n"
        else:
            message += f"AFK Timeout: **None**\n"
        message += f"Verification: **{verification_levels[str(ctx.guild.verification_level)]}**\n"
        message += f"MFA: **{'Enabled' if ctx.guild.mfa_level else 'Disabled'}**\n"
        message += f"\n"
        message += f"Splash url: **{ctx.guild.splash_url or None}**\n"
        message += f"Shard Number: **{ctx.guild.shard_id}**\n"
        # message += f"\n"
        # message += f"Most played game currently: **{topgame['name']}** (**{topgame['played']}**)\n"
        # message += f"Most common discriminator: **{disc['discriminator']}** (**{disc['people']}**)"

        # await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="Guild Info")
        embed = discord.Embed(title="Guild Info", description=message)
        if ctx.guild.icon_url:
            embed.set_thumbnail(url=ctx.guild.icon_url)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", description="[@]|Lists information about a user")
    async def userinfo(self, ctx, user: typing.Optional[discord.User] = None):
        if user:
            userinfo = await self.bot.get_user_info(user.id)
        else:
            userinfo = ctx.userinfo
            user = ctx.author

        message = ""
        message += f"Name: **{user}** `{user.id}`\n"
        message += f"Bot Account: **{user.bot}**\n"
        message += "\n"
        message += f"Created: {self.bot.maketimestamp(user.created_at.timestamp(), allow_secs=False, include_ago=True)}\n"
        message += f"Added: {self.bot.maketimestamp(userinfo['g']['g']['ua'], allow_secs=False, include_ago=True)}\n"
        if ctx.guild.get_member(user.id):
            user = ctx.guild.get_member(user.id)
            message += f"Joined: {self.bot.maketimestamp(user.joined_at.timestamp(), allow_secs=False, include_ago=True)}\n"
        message += "\n"
        message += f"Partner: {userinfo['m']['p']}\n"
        message += f"Donator: {userinfo['m']['1']['h'] or userinfo['m']['3']['h'] or userinfo['m']['5']['h'] or userinfo['m']['hs']}\n"
        message += f"\n"
        message += f"Reputation: {userinfo['r']['r']}\n"
        # message += f"Global XP: {userinfo['xp']['g']}\n"

        # await self.bot.send_data(ctx, message, ctx.userinfo, force_guild=True, title="User Info")
        embed = discord.Embed(title="User Info", description=message)
        embed.set_thumbnail(url=user.avatar_url or user.default_avatar_url)
        await ctx.send(embed=embed)

    @commands.command(
        name="zipemojis",
        description="|Returns a zip with all guild emojis")
    @customchecks.requires_guild()
    async def zipemojis(self, ctx):
        message = await ctx.send(self.bot.get_emote('downloading'))

        _zipf = io.BytesIO()
        with zipfile.ZipFile(_zipf, mode="w", compression=zipfile.ZIP_DEFLATED) as _zip:
            for emoji in ctx.guild.emojis:
                _e = io.BytesIO()
                await emoji.url.save(_e)
                _e.seek(0)

                _zip.writestr(
                    f"{emoji.name}.{'png' if not emoji.animated else 'gif'}", data=_e.read(-1))
        _zipf.seek(0)
        _file = discord.File(_zipf, f"emojis-{ctx.guild.id}.zip")
        await ctx.send(f"{self.bot.get_emote('packagevariantclosed')}  | Emojis successfully packed", file=_file)
        await message.delete()

    @commands.command(
        name="emojis",
        description="|Lists all guild emojis")
    @customchecks.requires_guild()
    async def emojis(self, ctx):
        message = ""
        emoji_list = []
        emoji_list += sorted(filter(lambda o: not o.animated,
                                    ctx.guild.emojis), key=lambda o: o.name)
        emoji_list += sorted(filter(lambda o: o.animated,
                                    ctx.guild.emojis), key=lambda o: o.name)
        for emoji in emoji_list:
            submessage = f"{emoji} **{emoji.name}** `{emoji.id}`\n"
            if len(message) + len(submessage) > 2048:
                embed = discord.Embed(
                    title="Guild Emojis", description=message)
                embed.set_footer(
                    text="To download this servers emojis, just do +zipemojis")
                await ctx.send(embed=embed)
                message = ""
            message += submessage
        embed = discord.Embed(title="Guild Emojis", description=message)
        embed.set_footer(
            text="To download this servers emojis, just do +zipemojis")
        await ctx.send(embed=embed)

    @commands.command(
        name="verify",
        description="<code>|Manually verifies borderwall access")
    async def verify(self, ctx, code=None):
        if not code:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="borderwall code")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        # bw_information = await r.table("borderwall").get(code).run(self.bot.connection)
        bw_information = await self.bot.get_value("borderwall", code)
        if not bw_information:
            message = rockutils._(
                "No {target}, which is required, was specified",
                ctx).format(
                    target="valid borderwall code")
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if bw_information['ui'] != str(ctx.author.id):
            message = "You cannot verify borderwall for someone else"
            return await ctx.send(f"{self.bot.get_emote('cross')}  | " + message)

        if bw_information['a']:
            await self.bot.broadcast("borderwallverify", "*", [bw_information['gi'], bw_information['ui'], code])
        else:
            _borderwall_link = f"https://welcomer.fun/borderwall/{code}"
            embed = discord.Embed(
                message=f"You have not verified yet, verify [here]({_borderwall_link})")
            await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Miscellaneous(bot))
