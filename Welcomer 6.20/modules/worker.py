import asyncio
import copy
import codecs
import imghdr
import io
import math
import re
import time
import aiohttp
import discord
import random
import pytz
# import spacy
import ujson as json
import yaml
import sys
import traceback
import importlib

from datetime import datetime
from urllib.parse import urlparse
from discord.ext import commands, tasks
# from profanity_filter import ProfanityFilter
import rockutils as _rockutils

try:
    importlib.reload(_rockutils)
except Exception as e:
    print(e)

rockutils = _rockutils.rockutils
gameretriever = _rockutils.gameretriever

"""
python3.6 -m spacy download en
python3.6 -m spacy download de
python3.6 -m spacy download fr
python3.6 -m spacy download es
python3.6 -m spacy download pt
python3.6 -m spacy download it
python3.6 -m spacy download nl
python3.6 -m spacy download el
"""


# # spacys_import = ["en", "de", "fr", "es", "pt", "it", "np", "el"]
# spacys_import = ["en"]

# nlps = {}
# for spacy_name in spacys_import:
#     if spacy_name in ['en']:
#         name = f"{spacy_name}_core_web_sm"
#     else:
#         name = f"{spacy_name}_core_news_sm"

#     try:
#         try:
#             _start = time.time()
#             rockutils.prefix_print(f"Loading spacy model: {name}", prefix="Spacy Init", prefix_colour="light green")
#             nlps[spacy_name] = spacy.load(name)
#             rockutils.prefix_print(f"Loaded spacy model {name} in {math.ceil((time.time() - _start)*1000)} ms", prefix="Spacy Init", prefix_colour="light green")
#         except OSError:
#             try:
#                 nlps[spacy_name] = __import__(name).load()
#             except ModuleNotFoundError:
#                 try:
#                     spacy.cli.download(name)
#                 except Exception as e:
#                     rockutils.prefix_print(f"Unable to download spacy model {spacy_name}: {e}", prefix="Spacy Init", prefix_colour="light red", text_colour="red")

#                 nlps[spacy_name] = spacy.load(name)
#                 rockutils.prefix_print(f"Downloaded spacy model: {spacy_name}", prefix="Spacy Init", prefix_colour="green")
#         except Exception as e:
#             rockutils.prefix_print(f"Unable to import spacy model {spacy_name}: {e}", prefix="Spacy Init", prefix_colour="light red", text_colour="red")
#     except Exception as e:
#         rockutils.prefix_print(f"Unable to import spacy model {spacy_name}: {e}", prefix="Spacy Init", prefix_colour="light red", text_colour="red")

# for _, nlp in nlps.items():
#     try:
#         nlp.add_pipe(profanity_filter.spacy_component, last=True)
#     except Exception as e:
#         rockutils.prefix_print(f"Unable to add pipe for spacy model {spacy_name}: {e}", prefix="Spacy Init", prefix_colour="light red", text_colour="red")

# rockutils.prefix_print(f"Loaded {len(nlps)}/{len(spacys_import)} spacy models", prefix="Spacy Init", prefix_colour="light green")


# nlp = spacy.load('en_core_web_sm')
# nlp = spacy.load('en')
# profanity_filter = ProfanityFilter(nlps={'en': nlp})
# nlp.add_pipe(profanity_filter.spacy_component, last=True)
# pf = ProfanityFilter()

blockeddomains = {
    "grabify", "iplogger", "2no.co", "yip.su", "blasze", "whatstheirip",
    "fuglekos", "ipgrabber", "ip-grabber", "ip-", "bit.ly", "bmwforum.co",
    "leancoding.co", "quickmessage.io", "spottyfly.com", "spötify", "stopify",
    "yoütu", "yoütübe", "xda-developers.io", "starbucks.bio",
    "starbucksiswrong.com", "starbucksisbadforyou.com", "bucks", "discörd",
    "minecräft", "shört", "cyberh1", "freegiftcards.co", "fortnite.space",
    "watches-my.stream", "joinmy.site", "youshouldclick.us",
    "fortnitechat.site", "quickmessage.us", "särahah.pl", "särahah.eu",
    "disçordapp.com", "privatepage.vip"}

profanity = {
    "2g1c", "2 girls 1 cup", "acrotomophilia", "alabama hot pocket",
    "alaskan pipeline", "anal", "anilingus", "anus", "apeshit", "arsehole",
    "ass", "asshole", "assmunch", "auto erotic", "autoerotic", "babeland",
    "baby batter", "baby juice", "ball gag", "ball gravy", "ball kicking",
    "ball licking", "ball sack", "ball sucking", "bangbros", "bareback",
    "barely legal", "barenaked", "bastard", "bastardo", "bastinado", "bbw",
    "bdsm", "beaner", "beaners", "beaver cleaver", "beaver lips", "bestiality",
    "big black", "big breasts", "big knockers", "big tits", "bimbos",
    "birdlock", "bitch", "bitches", "black cock", "blonde action",
    "blonde on blonde action", "blowjob", "blow job", "blow your load",
    "blue waffle", "blumpkin", "bollocks", "bondage", "boner", "boob", "boobs",
    "booty call", "brown showers", "brunette action", "bukkake", "bulldyke",
    "bullet vibe", "bullshit", "bung hole", "bunghole", "busty", "butt",
    "buttcheeks", "butthole", "camel toe", "camgirl", "camslut", "camwhore",
    "carpet muncher", "carpetmuncher", "chocolate rosebuds", "circlejerk",
    "cleveland steamer", "clit", "clitoris", "clover clamps", "clusterfuck",
    "cock", "cocks", "coprolagnia", "coprophilia", "cornhole", "coon", "coons",
    "creampie", "cum", "cumming", "cunnilingus", "cunt", "darkie", "date rape",
    "daterape", "deep throat", "deepthroat", "dendrophilia", "dick", "dildo",
    "dingleberry", "dingleberries", "dirty pillows", "dirty sanchez",
    "doggie style", "doggiestyle", "doggy style", "doggystyle", "dog style",
    "dolcett", "domination", "dominatrix", "dommes", "donkey punch",
    "double dong", "double penetration", "dp action", "dry hump", "dvda",
    "eat my ass", "ecchi", "ejaculation", "erotic", "erotism", "escort",
    "eunuch", "faggot", "fecal", "felch", "fellatio", "feltch",
    "female squirting", "femdom", "figging", "fingerbang", "fingering",
    "fisting", "foot fetish", "footjob", "frotting", "fuck", "fuck buttons",
    "fuckin", "fucking", "fucktards", "fudge packer", "fudgepacker",
    "futanari", "gang bang", "gay sex", "genitals", "giant cock", "girl on",
    "girl on top", "girls gone wild", "goatcx", "goatse", "god damn", "gokkun",
    "golden shower", "goodpoop", "goo girl", "goregasm", "grope", "group sex",
    "g-spot", "guro", "hand job", "handjob", "hard core", "hardcore", "hentai",
    "homoerotic", "honkey", "hooker", "hot carl", "hot chick", "how to kill",
    "how to murder", "huge fat", "humping", "incest", "intercourse",
    "jack off", "jail bait", "jailbait", "jelly donut", "jerk off", "jigaboo",
    "jiggaboo", "jiggerboo", "jizz", "juggs", "kike", "kinbaku", "kinkster",
    "kinky", "knobbing", "leather restraint", "leather straight jacket",
    "lemon party", "lolita", "lovemaking", "make me come", "male squirting",
    "masturbate", "menage a trois", "milf", "missionary position",
    "motherfucker", "mound of venus", "mr hands", "muff diver", "muffdiving",
    "nambla", "nawashi", "negro", "neonazi", "nigga", "nigger", "nig nog",
    "nimphomania", "nipple", "nipples", "nsfw images", "nude", "nudity",
    "nympho", "nymphomania", "octopussy", "omorashi", "one cup two girls",
    "one guy one jar", "orgasm", "orgy", "paedophile", "paki", "panties",
    "panty", "pedobear", "pedophile", "pegging", "penis", "phone sex",
    "piece of shit", "pissing", "piss pig", "pisspig", "playboy",
    "pleasure chest", "pole smoker", "ponyplay", "poof", "poon", "poontang",
    "punany", "poop chute", "poopchute", "porn", "porno", "pornography",
    "prince albert piercing", "pthc", "pubes", "pussy", "queaf", "queef",
    "quim", "raghead", "raging boner", "rape", "raping", "rapist", "rectum",
    "reverse cowgirl", "rimjob", "rimming", "rosy palm",
    "rosy palm and her 5 sisters", "rusty trombone", "sadism", "santorum",
    "scat", "schlong", "scissoring", "semen", "sex", "sexo", "sexy",
    "shaved beaver", "shaved pussy", "shemale", "shibari", "shit", "shitblimp",
    "shitty", "shota", "shrimping", "skeet", "slanteye", "slut", "s&m", "smut",
    "snatch", "snowballing", "sodomize", "sodomy", "spic", "splooge",
    "splooge moose", "spooge", "spread legs", "spunk", "strap on", "strapon",
    "strappado", "strip club", "style doggy", "suck", "sucks", "suicide girls",
    "sultry women", "swastika", "swinger", "tainted love", "taste my",
    "tea bagging", "threesome", "throating", "tied up", "tight white", "tit",
    "tits", "titties", "titty", "tongue in a", "topless", "tosser",
    "towelhead", "tranny", "tribadism", "tub girl", "tubgirl", "tushy",
    "twat", "twink", "twinkie", "two girls one cup", "undressing", "upskirt",
    "urethra play", "urophilia", "vagina", "venus mound", "vibrator",
    "violet wand", "vorarephilia", "voyeur", "vulva", "wank", "wetback",
    "wet dream", "white power", "wrapping men", "wrinkled starfish", "xx",
    "xxx", "yaoi", "yellow showers", "yiffy", "zoophilia", "🖕"}


async def get_final_url(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"user-agent": f"aiohttp/{aiohttp.__version__} (compatible; WelcomerBot/7.0;+https://welcomer.gg)"}) as resp:
            return str(getattr(resp, "url", ""))


class Worker(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.delay = 60
        self.channel_updates = {}

    #     self.serverstats.start()

    # def cog_unload(self):
    #     self.serverstats.cancel()

    # @tasks.loop(seconds=60)
    # async def serverstats(self):
    #     _purged = {}
    #     for _guild_id, _guild_stats in self.bot.cache['stats'].items():
    #         if _guild_stats.get('e', False) and isinstance(_guild_stats.get('c', []), list):
    #             for _channel in _guild_stats.get('c', []):
    #                 purge_channel = False
    #                 if _channel.get("c"):
    #                     channel = self.bot.get_channel(int(_channel['c']))
    #                     if channel:
    #                         await self.bot.handle_stats(_channel, channel=channel)
    #                     else:
    #                         purge_channel = True
    #                 else:
    #                     purge_channel = True

    #                 if purge_channel:
    #                     if _guild_id not in _purged:
    #                         _purged[_guild_id] = []
    #                     _purged[_guild_id].append(_channel)

    #     for _guild_id, _purge in _purged.items():
    #         guildinfo = await self.bot.get_guild_info(_guild_id, refer="Execute Worker")
    #         channels = guildinfo['s']['c']
    #         for _purged in _purge:
    #             if _purged in self.bot.cache['stats'][_guild_id]['c']:
    #                 self.bot.cache['stats'][_guild_id]['c'].remove(_purged)
    #             if _purged in channels:
    #                 channels.remove(_purged)
    #         guildinfo['s']['c'] = channels
    #         await self.bot.update_guild_info(_guild_id, guildinfo, refer="Execute Worker")

    async def worker_task(self):
        rockutils.prefix_print(f"Awaiting ready", prefix="Worker Task")

        rockutils.prefix_print(f"Starting worker", prefix="Worker Task")

        workdata = {}
        while True:
            try:
                workdata = await self.bot.execute_worker(workdata)
            except Exception as e:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
                rockutils.prefix_print(
                    str(e),
                    prefix="Worker Task",
                    prefix_colour="light red",
                    text_colour="red")

            if "processing" not in workdata:
                rockutils.prefix_print(
                    f"Processing not passed, defaulting 0", prefix="Worker Task")
                workdata['processing'] = 0

            await asyncio.sleep(self.delay - workdata['processing'])

    # async def execute_namepurge(self, member, _guildinfo, _guildid):
    #     _bot = member.bot
    #     if _guildid in self.bot.cache['namepurge'] and \
    #             self.bot.cache['namepurge'][_guildid]['e']:
    #         # continue if not a bot or a bot and ignore bots is disabled
    #         if not _bot or (
    #                 _bot and not self.bot.cache['namepurge'][_guildid]['i']):
    #             _rawfilter = self.bot.cache['namepurge'][_guildid]['f']
    #             _filter = []
    #             for sText in _rawfilter:
    #                 sText = sText.strip()
    #                 if len(sText) > 0:
    #                     _filter.append(sText)
    #             has_matched, matched = rockutils.regex_text(
    #                 member.name, _filter, return_string=True)
    #             if has_matched:
    #                 guildinfo = await self.bot.get_guild_info(_guildid, refer="Namepurge")
    #                 has_elevation = await self.bot.has_elevation(member.guild, guildinfo, member)
    #                 if not has_elevation:
    #                     try:
    #                         try:
    #                             message = rockutils._(
    #                                 "Your name contains **{matched}** which is not allowed on **{server}**",
    #                                 _guildinfo).format(
    #                                 matched=matched,
    #                                 server=member.guild.name)
    #                             await self.bot.send_user_data(member, message)
    #                             # await self.send_data(None, message, force_dm=True)
    #                         except BaseException:
    #                             pass
    #                         await member.kick(reason=f"NamePurge: Name contains {matched}")
    #                         return False
    #                     except BaseException:
    #                         pass
    #     return True

    async def execute_leaver(self, member, _guildid):
        if _guildid in self.bot.cache['leaver'] and self.bot.cache['leaver'][_guildid]['e']:
            leaver_channel = member.guild.get_channel(
                int(self.bot.cache['leaver'][_guildid]['c'] or 0))
            if leaver_channel:
                try:
                    message = self.format_message(
                        self.bot.cache['leaver'][_guildid]['t'],
                        guild=member.guild, user=member, include_user=True,
                        include_guild=True, extras={})

                    message_kwargs = {}
                    if self.bot.cache['leaver'][_guildid]['em']:
                        embed = discord.Embed(description=message)
                        message_kwargs['embed'] = embed
                    else:
                        message_kwargs['content'] = message

                    await leaver_channel.send(**message_kwargs)
                except BaseException:
                    exc_info = sys.exc_info()
                    traceback.print_exception(*exc_info)

    async def execute_welcomer(self, member, guildinfo, _should_welcome=True, test=False):
        _bot = member.bot
        _guildid = member.guild.id

        if _should_welcome:
            if not _bot and _guildid in self.bot.cache['welcomer']:
                welcomer_config = self.bot.cache['welcomer'][_guildid]
                if welcomer_config['i']['e'] or welcomer_config['dm']['e'] or welcomer_config['t']['e']:
                    message = ""
                    s = ""
                    image_obj = None
                    invite_obj = {}
                    has_image = False
                    has_raw_image = False
                    message_kwargs = {}
                    welcome_channel = None

                    welcome_channel = member.guild.get_channel(
                        int(welcomer_config['c'] or 0))

                    try:
                        if welcomer_config['iv']:
                            invites = await self.bot.serialiser.invites(member.guild)
                            if invites != []:
                                guildinfo = await self.bot.get_guild_info(member.guild.id, refer="on_member_join")

                                if invites != guildinfo['d']['i']:
                                    oldinvites = copy.deepcopy(
                                        guildinfo['d']['i'])
                                    guildinfo['d']['i'] = invites
                                    await self.bot.update_guild_info(member.guild.id, guildinfo, refer="on_member_join")
                                else:
                                    oldinvites = invites

                                invite_ids = list(
                                    map(lambda o: o['code'], guildinfo['d']['i']))
                                changed_invites = []

                                for invite in invites:
                                    if not invite['code'] in invite_ids:
                                        if invite['uses'] == 1:
                                            changed_invites.append(invite)
                                    else:
                                        if invite['code'] in invite_ids:
                                            c = list(
                                                filter(
                                                    lambda o,
                                                    invitecode=invite
                                                    ['code']: o['code'] == invitecode, oldinvites))
                                            if len(c) > 0:
                                                if invite['uses'] - \
                                                        c[0]['uses'] == 1:
                                                    changed_invites.append(
                                                        invite)

                                if len(changed_invites) == 1:
                                    invite_obj = changed_invites[0]
                    except BaseException as e:
                        print(e)
                        if test:
                            raise e
                        pass

                    if welcomer_config['dm']['e']:
                        dm_message_kwargs = {}
                        if welcomer_config['dm']['ue']:

                            if welcomer_config['dm']['em'][0] == "y":
                                edict = yaml.load(
                                    welcomer_config['dm']['em'][1], Loader=yaml.SafeLoader)
                            if welcomer_config['dm']['em'][0] == "j":
                                edict = json.loads(
                                    welcomer_config['dm']['em'][1])

                            if type(edict) != dict:
                                edict = {
                                    "content": "It seems your/the server this is set for's custom embed is misconfigured! Use https://www.welcomer.gg/customembeds"}

                            def _i(d):
                                if isinstance(d, dict):
                                    for k, v in d.items():
                                        if type(v) in [list, dict]:
                                            d[k] = _i(v)
                                        elif isinstance(v, str):
                                            d[k] = self.format_message(
                                                v, guild=member.guild,
                                                user=member, invite=invite_obj,
                                                include_user=True,
                                                include_guild=True,
                                                include_invites=True,
                                                extras={}).replace("\\n", "\n")
                                elif isinstance(d, list):
                                    for k, v in enumerate(d):
                                        if type(v) in [list, dict]:
                                            _i(v)
                                        elif isinstance(v, str):
                                            d[k] = self.format_message(
                                                v, guild=member.guild,
                                                user=member, invite=invite_obj,
                                                include_user=True,
                                                include_guild=True,
                                                include_invites=True,
                                                extras={}).replace("\\n", "\n")
                                return d

                            edict = _i(edict)

                            if isinstance(edict, dict):
                                if isinstance(edict.get('color', ""), str):
                                    if "color" in edict:
                                        edict['color'] = int(
                                            edict['color'].replace("#", ""), 16)

                                if edict.get("footer"):
                                    edict['footer'] = {
                                        "text": edict.get("footer")}  # crappy builder
                                if (edict.get("url", "") == "" or not isinstance(
                                        edict.get("url", ""), str)):
                                    if "url" in edict:
                                        del edict['url']
                                if (edict.get("thumbnail", {}).get("url", "") == "" or not isinstance(
                                        edict.get("thumbnail", {}).get("url", ""), str)):
                                    if "thumbnail" in edict:
                                        if "url" in edict['thumbnail']:
                                            del edict['thumbnail']['url']
                                if (edict.get("author", {}).get("icon_url", "") == "" or not isinstance(
                                        edict.get("author", {}).get("icon_url", ""), str)):
                                    if "author" in edict:
                                        if "icon_url" in edict['author']:
                                            del edict['author']['icon_url']

                            embed = discord.Embed.from_dict(edict)
                            dm_message_kwargs['embed'] = embed

                            if edict.get("content"):
                                message = self.format_message(
                                    edict['content'],
                                    guild=member.guild,
                                    user=member,
                                    invite=invite_obj,
                                    include_user=True,
                                    include_guild=True,
                                    include_invites=True,
                                    extras={})
                                dm_message_kwargs['content'] = message
                        else:
                            message = self.format_message(
                                welcomer_config
                                ['dm']['m'],
                                guild=member.guild,
                                user=member,
                                invite=invite_obj,
                                include_user=True,
                                include_guild=True,
                                include_invites=True,
                                extras={})
                            dm_message_kwargs['content'] = message

                        try:
                            await member.send(**dm_message_kwargs)
                        except BaseException as e:
                            exc_info = sys.exc_info()
                            traceback.print_exception(*exc_info)
                            if test:
                                raise e
                            pass

                    if welcome_channel:

                        embed = discord.Embed()
                        if welcomer_config['i']['e']:
                            _message = []
                            lines = welcomer_config['i']['m']
                            if isinstance(lines, str):
                                lines = lines.split("\n")
                            for line in lines:
                                _line = self.format_message(
                                    line,
                                    guild=member.guild,
                                    user=member,
                                    invite=invite_obj,
                                    include_user=True,
                                    include_guild=True,
                                    include_invites=True,
                                    extras={}
                                )
                                _message.append(_line)

                            payload = {
                                "allowed_gif": "true",
                                "image_data": json.dumps(
                                    {
                                        "bg": welcomer_config['i']['bg'],
                                        "b": welcomer_config['i']['b'],
                                        "pb": welcomer_config['i']['pb'],
                                        "c": welcomer_config['i']['c'],
                                        "a": welcomer_config['i']['a'],
                                        "t": welcomer_config['i']['t'],
                                        "m": _message,
                                    }),
                                "avatar_url": str(
                                    member.avatar_url_as(
                                        format="png",
                                        size=256)) or str(
                                    member.default_avatar_url),
                                "cache": "true"}

                            async with aiohttp.ClientSession() as session:
                                async with session.post(f"http://127.0.0.1:{self.bot.config['cdn']['daemonport']}/images/create", data=payload) as response:
                                    if response.status == 200:
                                        if response.headers['content-type'] == "application/octet-stream":
                                            image_obj = io.BytesIO(await response.read())
                                            _file = "welcomeimage." + \
                                                imghdr.what(image_obj)
                                            message_kwargs['file'] = discord.File(
                                                image_obj, filename=_file)
                                            has_raw_image = True
                                        else:
                                            j = await response.json()
                                            image_obj = j['url']
                                            has_image = True

                        if welcomer_config['t']['e']:
                            message = self.format_message(
                                welcomer_config
                                ['t']['m'],
                                guild=member.guild,
                                user=member,
                                invite=invite_obj,
                                include_user=True,
                                include_guild=True,
                                include_invites=True,
                                extras={})

                        if welcomer_config['b']:
                            user_info = await self.bot.get_user_info(member.id)
                            badges = user_info['b']
                            message += "\n\n"
                            for badge in badges:
                                message += f"{badge[0]} **{badge[1]}**  | `{badge[2]}`\n"

                        showembed = False
                        if welcomer_config['ue']:
                            if welcomer_config['em'][0] == "y":
                                edict = yaml.load(
                                    welcomer_config['em'][1], Loader=yaml.SafeLoader)
                            if welcomer_config['em'][0] == "j":
                                edict = json.loads(welcomer_config['em'][1])

                            if type(edict) != dict:
                                edict = {
                                    "content": "It seems your/the server this is set for's custom embed is misconfigured! Use https://www.welcomer.gg/customembeds"}

                            def _i(d):
                                if isinstance(d, dict):
                                    for k, v in d.items():
                                        if type(v) in [list, dict]:
                                            d[k] = _i(v)
                                        elif isinstance(v, str):
                                            d[k] = self.format_message(
                                                v, guild=member.guild,
                                                user=member, invite=invite_obj,
                                                include_user=True,
                                                include_guild=True,
                                                include_invites=True,
                                                extras={}).replace("\\n", "\n")
                                elif isinstance(d, list):
                                    for k, v in enumerate(d):
                                        if type(v) in [list, dict]:
                                            _i(v)
                                        elif isinstance(v, str):
                                            d[k] = self.format_message(
                                                v, guild=member.guild,
                                                user=member, invite=invite_obj,
                                                include_user=True,
                                                include_guild=True,
                                                include_invites=True,
                                                extras={}).replace("\\n", "\n")
                                return d

                            edict = _i(edict)
                            if isinstance(edict, dict):
                                if isinstance(edict.get('color', ""), str):
                                    if "color" in edict:
                                        edict['color'] = int(
                                            edict['color'].replace("#", ""), 16)

                                if edict.get("footer"):
                                    edict['footer'] = {
                                        "text": edict.get("footer")}  # crappy builder
                                if (edict.get("url", "") == "" or not isinstance(
                                        edict.get("url", ""), str)):
                                    if "url" in edict:
                                        del edict['url']
                                if (edict.get("thumbnail", {}).get("url", "") == "" or not isinstance(
                                        edict.get("thumbnail", {}).get("url", ""), str)):
                                    if "thumbnail" in edict:
                                        if "url" in edict['thumbnail']:
                                            del edict['thumbnail']['url']
                                if (edict.get("author", {}).get("icon_url", "") == "" or not isinstance(
                                        edict.get("author", {}).get("icon_url", ""), str)):
                                    if "author" in edict:
                                        if "icon_url" in edict['author']:
                                            del edict['author']['icon_url']
                            embed = discord.Embed.from_dict(edict)
                            showembed = True

                            if edict.get("content"):
                                message = self.format_message(
                                    edict['content'],
                                    guild=member.guild,
                                    user=member,
                                    invite=invite_obj,
                                    include_user=True,
                                    include_guild=True,
                                    include_invites=True,
                                    extras={})
                                message_kwargs['content'] = message
                        else:
                            if welcomer_config['e']:
                                embed = discord.Embed(description=message)
                                showembed = True
                            else:
                                message_kwargs['content'] = message

                        if has_image:
                            embed.set_image(url=image_obj)
                            showembed = True

                        if has_raw_image:
                            embed.set_image(url=f"attachment://{_file}")
                            showembed = True

                        if showembed:
                            message_kwargs['embed'] = embed

                        try:
                            await welcome_channel.send(**message_kwargs)
                        except BaseException as e:
                            exc_info = sys.exc_info()
                            traceback.print_exception(*exc_info)
                            if test:
                                raise e

    async def perform_automod(self, message, guild, config):
        link_regex = r"(https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*))"
        invite_regex = r"(?:https?://)?discord(?:app\.com/invite|\.gg)/?[a-zA-Z0-9]+/?"
        user_mention_regex = r"<@!?(\d+)>"
        # role_mention_regex = r"<@&(\d+)>"
        formatted_message = message.clean_content
        raw_message = str(message.clean_content)
        bad_message = False
        remove_message = False
        allow_automod = True

        reason = ""
        matches = []

        # invites
        if config['g']['i']:
            matches = re.findall(invite_regex, raw_message)
            if len(matches) > 0:
                bad_message = True
                remove_message = True
                for match in matches:
                    raw_message = raw_message.replace(
                        match,
                        ""
                    )
                    formatted_message = formatted_message.replace(
                        match, "\\*" * len(match))
                reason = "Discord Invite in message"

        if config['g']['ur'] or \
                config['g']['ul']:
            matches = re.findall(link_regex, raw_message)
            matches = [v[0] for v in matches]

        # any urls
        if config['g']['ul']:
            if len(matches) > 0:
                bad_message = True
                for match in matches:
                    formatted_message = formatted_message.replace(
                        match, "\\*" * len(match))
                    reason = "URL in message"

        # url redirects
        if config['g']['ur']:
            if len(matches) > 0:
                for match in matches:
                    final = await get_final_url(match)
                    matches = re.findall(invite_regex, message.clean_content)
                    if urlparse(match).netloc != urlparse(final).netloc:
                        bad_message = True
                        formatted_message = formatted_message.replace(
                            match, "\\*" * len(match))

                    # filter redirects to invites
                    if config['g']['i']:
                        matches = re.findall(
                            invite_regex, message.clean_content)
                        if len(matches) > 0:
                            bad_message = True
                            for match in matches:
                                formatted_message = formatted_message.replace(
                                    match, "\\*" * len(match))
                                reason = "Bad URL redirection"

        # ipgrabbers
        if config['g']['ig']:
            matches = list(
                filter(lambda o: o in blockeddomains, message.clean_content))
            if len(matches) > 0:
                bad_message = True
                for match in matches:
                    formatted_message = formatted_message.replace(
                        match, "\\*" * len(match))
                    reason = "URL IP grabber"

        # mass caps
        if config['g']['mc'] and config['t']['c'] > 0 and len(message.clean_content) > 0:
            cap_count = sum(1 for c in list(
                message.clean_content) if c.isupper())
            cap_percentage = cap_count / len(message.clean_content)
            if cap_percentage > config['t']['c']:
                bad_message = True
                remove_message = True
                allow_automod = False
                reason = "Reached caps threshold"

        # mass mentions
        if config['g']['mm'] and config['t']['m'] > 0:
            user_mentions = set(re.findall(
                user_mention_regex, message.clean_content))
            mentions = len(user_mentions)
            if mentions > config['t']['m']:
                bad_message = True
                remove_message = True
                allow_automod = False
                reason = "Reached mention threshold"

        # profanity
        # if config['g']['p']:
        #     text = message.clean_content
        #     doc = nlp(text)
        #     has_profanity = False
        #     for token in doc:
        #         if token._.is_profane:
        #             bad_message = True
        #             remove_message = True
        #             allow_automod = True
        #             formatted_message = formatted_message.replace(
        #                 token._.original_profane_word, token._.censored.replace("*", "\\*"))
        #             reason = "Profanity"

        # # filter
        # if config['g']['f']:
        #     # text filter
        #     if len(config['f']) > 0:
        #         pf.custom_profane_word_dictionaries = {'en': list(
        #             filter(lambda o: len(o.strip()) > 0, config['f']))}
        #         pf.censor_char = "*"
        #         if pf.is_profane(message.clean_content):
        #             bad_message = True
        #             remove_message = True
        #             allow_automod = True
        #             formatted_message = pf.censor(message.clean_content)
        #             reason = f"Text Filter match"

            # # regex
            # if len(config['r']) > 0:
            #     for _regex in config['r']:
            #         if len(_regex.strip()) == 0:
            #             _regex = _regex.replace("+", "")
            #             try:
            #                 re.compile(_regex)
            #             except BaseException:
            #                 pass
            #             else:
            #                 _regex_matches = re.findall(
            #                     _regex, message.clean_content)
            #                 if len(_regex_matches) > 0:
            #                     bad_message = True
            #                     remove_message = True
            #                     allow_automod = True
            #                     for match in _regex_matches:
            #                         formatted_message = formatted_message.replace(
            #                             match, "\\*" * len(match))
            #                     reason = f"Regex Filter match: '{_regex}'"

        if bad_message:
            guildinfo = await self.bot.get_guild_info(message.guild.id, refer="AutoMod")
            has_elevation = await self.bot.has_elevation(message.guild, guildinfo, message.author)
            if has_elevation:
                bad_message = False

        # smartmod
        if bad_message:
            if remove_message:
                try:
                    await message.delete()
                except Exception as e:
                    print(e)

            if config['sm']:
                if allow_automod:
                    try:
                        webhooks = await message.channel.webhooks()
                    except Exception as e:
                        webhooks = None
                        print(e)

                    if webhooks is not None:
                        welcomer_hooks = list(filter(
                            lambda o: o.name.lower() == "welcomer smartmod",
                            webhooks))
                        if len(welcomer_hooks) == 0:
                            webhook = await message.channel.create_webhook(name="Welcomer SmartMod")
                        else:
                            webhook = welcomer_hooks[0]

                        # async with aiohttp.ClientSession() as session:
                        #     webhook = Webhook.partial(hook_id, hook_token, adapter=AsyncWebhookAdapter(session))

                        avatar = str(
                            message.author.avatar_url or message.author.default_avatar_url)
                        await webhook.send(
                            formatted_message,
                            username=str(message.author),
                            avatar_url=avatar)

    # async def handle_stats(self, data, channel=None):
    #     if not channel:
    #         channel = self.bot.get_channel(int(data.get('c', 0)))
    #         if not channel:
    #             return False

    #     _type = data.get("t", None)
    #     _text = data.get("f", None)
    #     _args = data.get("d", None)

    #     _formats = {}

    #     if not _type and not _text:
    #         return False

    #     if _type in [
    #         "mc",
    #         "a2s",
    #         "yt",
    #         "twitter",
    #         "steam",
    #             "factorio"] and not _args:
    #         return False

    #     if _type == "time":
    #         if not _args:
    #             _args = "UTC"

    #         timezone = pytz.timezone(_args)
    #         _time = timezone.localize(datetime.now())

    #         _text = _time.strftime(_text)
    #         # _text = time.strftime(_text, _time)
    #         _formats = {
    #             "tz": _args,
    #             "icon": rockutils.retrieve_time_emoji(_time.timestamp()),
    #         }

    #     if _type == "mc":
    #         success, data = await gameretriever.minecraft(_args)
    #         if success:
    #             _formats = {
    #                 "ip": _args,
    #                 "online": data.players.online,
    #                 "limit": data.players.max,
    #                 "ping": math.ceil(data.latency)
    #             }
    #         else:
    #             _formats = {
    #                 "ip": _args,
    #                 "online": "?",
    #                 "limit": "?",
    #                 "ping": "?"
    #             }

    #     if _type == "a2s":
    #         success, data = await gameretriever.a2s(_args)
    #         if success:
    #             _formats = {
    #                 "name": data.get("server_name", "?"),
    #                 "map": data.get("map", "?"),
    #                 "game": data.get("game", "?"),
    #                 "online": data.get("player_count", "?"),
    #                 "limit": data.get("max_players", "?"),
    #                 "version": data.get("version", "?"),
    #                 "ip": _args
    #             }
    #         else:
    #             _formats = {
    #                 "name": "?",
    #                 "map": "?",
    #                 "game": "?",
    #                 "online": "?",
    #                 "limit": "?",
    #                 "version": "?",
    #                 "ip": _args
    #             }

    #     if _type == "youtube":
    #         success, data = await gameretriever.youtube(_args)
    #         if success:
    #             _formats = {
    #                 "id": _args, "subscribers": data['statistics'].get(
    #                     'subscriberCount', '0') if not data['statistics'].get(
    #                     'hiddenSubscriberCount', False) else 'HIDDEN', "videos": data['statistics'].get(
    #                     'videoCount', '0'), "views": data['statistics'].get(
    #                     'viewCount', '0'), "comments": data['statistics'].get(
    #                     'commentCount', '0'), }
    #         else:
    #             _formats = {
    #                 "id": _args,
    #                 "subscribers": "?",
    #                 "videos": "?",
    #                 "views": "?",
    #                 "comments": "?"
    #             }

    #     if _type == "guild":
    #         guild = channel.guild
    #         _formats = {
    #             "channels": len(guild.channels),
    #             "voicechannels": len(list(c for c in guild.channels if isinstance(c, discord.channel.VoiceChannel))),
    #             "textchannels": len(list(c for c in guild.channels if isinstance(c, discord.channel.TextChannel))),
    #             "categories": len(list(c for c in guild.channels if isinstance(c, discord.channel.CategoryChannel))),
    #             "users": len(list(u for u in guild.members if not u.bot)),
    #             "bots": len(list(u for u in guild.members if u.bot)),
    #             "members": guild.member_count
    #         }

    #     if _type == "twitter":
    #         success, data = await gameretriever.twitter(_args)
    #         if success:
    #             _formats = {
    #                 "name": _args,
    #                 "id": data.get("id", "?"),
    #                 "age_restricted": data.get("age_gated", "?"),
    #                 "followers": data.get("followers_count", "?")
    #             }
    #         else:
    #             _formats = {
    #                 "name": _args,
    #                 "id": "?",
    #                 "age_restricted": "?",
    #                 "followers": "?"
    #             }

    #     if _type == "steam":
    #         success, data = await gameretriever.steam_group(_args)
    #         if success:
    #             _formats = {
    #                 "ingame": data.get("ingame", "?"),
    #                 "online": data.get("online", "?"),
    #                 "members": data.get("members", "?"),
    #                 "name": data.get("display", "?"),
    #                 "id": _args
    #             }
    #         else:
    #             _formats = {
    #                 "ingame": "?",
    #                 "online": "?",
    #                 "members": "?",
    #                 "name": "?",
    #                 "id": _args
    #             }

    #     if _type == "factorio":
    #         success, data = await gameretriever.factorio(_args)
    #         if success:
    #             _formats = {
    #                 "gameid": _args,
    #                 "name": data.get("name", "?"),
    #                 "serverid": data.get("server_id", "?"),
    #                 "version": data['application_version']['game_version'],
    #                 "limit": data.get("max_players", "?"),
    #                 "online": len(data.get("players", [])),
    #                 "ip": data.get("host_address", "?")
    #             }
    #         else:
    #             _formats = {
    #                 "gameid": _args,
    #                 "name": "?",
    #                 "serverid": "?",
    #                 "version": "?",
    #                 "limit": "?",
    #                 "online": 0,
    #                 "ip": "?"
    #             }

    #     _text = rockutils.text_format(_text, _formats, ["{", "}"])

    #     if _text != channel.name:
    #         try:
    #             await channel.edit(name=_text)
    #         except BaseException as e:
    #             print(e)
    #             return False
    #     return True

    def format_message(
            self,
            string,
            guild=None,
            user=None,
            invite={},
            include_user=True,
            include_guild=True,
            include_invites=True,
            extras={}):
        formatting = {}
        if include_user and user:
            formatting["id"] = str(user.id)
            formatting["user"] = str(user)
            formatting["user.name"] = user.name
            formatting["user.id"] = str(user.id)
            formatting["user.mention"] = user.mention
            formatting["mention"] = user.mention
            formatting["user.discriminator"] = str(user.discriminator)
            try:
                formatting["user.avatar"] = str(
                    user.avatar_url_as(
                        format="png", size=256)) or str(
                    user.default_avatar_url)
                formatting["user.created.timestamp"] = str(user.created_at)
                formatting["user.created.since"] = self.bot.maketimestamp(
                    user.created_at.timestamp(), allow_secs=True)
                formatting["user.joined.timestamp"] = str(user.joined_at)
                formatting["user.joined.since"] = self.bot.maketimestamp(
                    user.joined_at.timestamp(), allow_secs=True)
            except BaseException:
                pass

        if include_guild and guild:
            users = sum([1 for m in guild.members if not m.bot])
            formatting["server"] = guild.name
            formatting["server.id"] = guild.id
            formatting["server.name"] = guild.name
            formatting["server.splash"] = guild.splash_url
            formatting["server.shard_id"] = guild.shard_id
            formatting["server.user.count"] = guild.member_count
            formatting["server.created.timestamp"] = guild.created_at
            formatting["server.user.prefix"] = rockutils.getprefix(
                guild.member_count)
            formatting["server.icon"] = str(
                guild.icon_url_as(
                    format="png", size=256)) or ""
            formatting["users"] = f"{users}{rockutils.getprefix(users)}"
            formatting["members"] = f"{guild.member_count}{rockutils.getprefix(guild.member_count)}"
            formatting[
                "server.users"] = f"{users}{rockutils.getprefix(users)}"
            formatting[
                "server.members"] = f"{guild.member_count}{rockutils.getprefix(guild.member_count)}"
            formatting["server.created.since"] = self.bot.maketimestamp(
                guild.created_at.timestamp(), allow_secs=True)

        if include_invites:
            formatting["invite.code"] = invite.get('code', 'Unknown')
            formatting["invite.inviter"] = invite.get('inviter_str', 'Unknown')
            formatting["invite.inviter.id"] = invite.get('inviter', 'Unknown')
            formatting["invite.uses"] = invite.get('uses', 'Unknown')
            formatting["invite.temporary"] = invite.get('temp', 'Unknown')
            formatting["invite.created.timestamp"] = datetime.fromtimestamp(
                invite.get('created_at', time.time()))
            formatting["invited.created.since"] = self.bot.maketimestamp(
                invite.get('created_at', time.time()), allow_secs=True)
            formatting["invited.max"] = invite.get('max', 'Unknown')

        _formatting = {}
        for key, value in formatting.items():
            if "user" in key and not key.replace("user", "member") in _formatting:
                _formatting[key.replace("user", "member")] = value
            if "server" in key and not key.replace("server", "guild") in _formatting:
                _formatting[key.replace("server", "guild")] = value
            _formatting[key] = value

        for key, value in extras.items():
            _formatting[key] = value

        if guild:
            string = rockutils.markmessage(string, guild)

        return rockutils.text_format(string, _formatting, ["{", "}"])

    async def execute_worker(self, workdata):
        _tstart = time.time()

        # timed moderation

        workdata['processing'] = time.time() - _tstart
        if workdata['processing'] > self.delay / 2:
            rockutils.prefix_print(
                f"Work job took {math.ceil(workdata['processing'] * 1000)}ms",
                prefix="Worker Task",
                prefix_colour="light red")
        return workdata

    @commands.Cog.listener()
    async def on_message(self, message):
        # timeroles
        if message.guild is None:
            return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        _tstart = time.time()
        _guildid = message.guild.id
        guild = message.guild

        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Prefix")

        if not self.bot.donator:
            if message.guild.get_member(498519480985583636):
                return

        if not message.author.bot and _guildid in self.bot.cache['timeroles'] and \
                self.bot.cache['timeroles'][_guildid]['e'] and \
                len(self.bot.cache['timeroles'][_guildid]['r']) > 0:

            _guild_stats = self.bot.cache['timeroles'][_guildid]
            guild, m, _purged = message.guild, message.author, []

            if guild.me.guild_permissions.administrator or guild.me.guild_permissions.manage_roles:
                _roles = []

                for _role_data in _guild_stats.get('r', []):
                    _role = guild.get_role(int(_role_data[0]))
                    if _role and _role < guild.me.top_role:
                        _roles.append([_role, _role_data[1]])
                    else:
                        _purged.append(_role_data)

                if not m.bot and (
                        m.top_role < guild.me.top_role or guild.me.guild_permissions.administrator):
                    _added = []
                    _duration = _tstart - m.joined_at.timestamp()
                    for _role_data in _roles:
                        if _duration >= int(
                                _role_data[1]) and not _role_data[0] in m.roles:
                            _added.append(_role_data[0])
                    if len(_added) > 0:
                        try:
                            await m.add_roles(*_added)
                        except Exception as e:
                            print(e)

                for roledata in _purged:
                    self.bot.cache['timeroles'][
                        message.guild.id]['r'].remove(roledata)

        if _guildid in self.bot.cache['automod'] and \
                self.bot.cache['automod'][_guildid]['e'] and \
                not message.author.bot:
            config = self.bot.cache['automod'][_guildid]
            await self.perform_automod(message, guild, config)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        _guildid = member.guild.id
        _bot = member.bot

        _should_welcome = True

        _bw_check = False
        _bw_seconds = 0

        _guildinfo = None

        if hasattr(member.guild, "chunk"):
            await self.bot.chunk_guild(member.guild)

        # if not self.bot.chunkcache.get(member.guild.id, False) and not member.guild.chunked:
        #     rockutils.prefix_print(
        #         f"Chunking {member.guild.id}", prefix_colour="light yellow", prefix="Worker:OnMemberJoin")
        #     self.bot.chunkcache[member.guild.id] = True
        #     a = time.time()
        #     await member.guild.chunk(cache=True)
        #     rockutils.prefix_print(
        #         f"Chunked {member.guild.id} in {math.ceil((time.time()-a)*1000)}ms", prefix_colour="light yellow", prefix="Worker:OnMemberJoin")
        #     self.bot.chunkcache[member.guild.id] = False

        if not self.bot.donator:
            if member.guild.get_member(498519480985583636):
                return

        id = random.randint(0, 65000)
        while self.bot.cachemutex:
            await asyncio.sleep(5)
            print("Waiting for cache mutex... " + str(id))
        # serverlock
        # if not _bot and _guildid in self.bot.cache['serverlock'] and \
        #         self.bot.cache['serverlock'][_guildid]['wl']['e']:
        #     if not str(_userid) in self.bot.cache['serverlock'][_guildid][
        #             'wl']['u']:
        #         if not _guildinfo:
        #             _guildinfo = await self.bot.get_guild_info(member.guild.id, refer="Member Join")
        #         try:
        #             try:
        #                 message = rockutils._(
        #                     "You are not whitelisted to join **{server}**",
        #                     _guildinfo).format(
        #                     server=member.guild.name)
        #                 await self.bot.send_user_data(member, message)
        #                 # await self.send_data(None, message, force_dm=True)
        #             except BaseException:
        #                 pass
        #             await member.kick(reason="ServerLock: User not in whitelist")
        #             _should_welcome = False
        #         except BaseException:
        #             pass

        # namepurge
        _bw_iter_wait = False
        # if _guildid in self.bot.cache['namepurge'] and \
        #         self.bot.cache['namepurge'][_guildid]['e']:
        #     if not _guildinfo:
        #         _guildinfo = await self.bot.get_guild_info(member.guild.id, refer="Member Join")
        #     await self.execute_namepurge(member, _guildinfo, _guildid)

        if not _bot and _guildid in self.bot.cache['borderwall'] and \
                self.bot.cache['borderwall'][_guildid]['e']:
            if self.bot.cache['borderwall'][_guildid]['c']:
                _bw_channel = member.guild.get_channel(
                    int(self.bot.cache['borderwall'][_guildid]['c'] or 0))
            else:
                _bw_channel = None

            _borderwall_link = "https://welcomer.fun/borderwall/{id}"
            insert_payload = {
                "u": str(member),
                "s": str(member.guild),
                "ui": str(member.id),
                "gi": str(member.guild.id),
                "a": False
            }

            insert_information = await self.bot.set_value("borderwall", None, insert_payload)
            # insert_information = await r.table("borderwall").insert(insert_payload).run(self.bot.connection)

            _borderwall_key = insert_information['generated_keys'][0]
            _borderwall_url = _borderwall_link.format(id=_borderwall_key)
            _sent_dm = False
            _should_welcome = False

            _bw_iter_wait = True
            _bw_seconds = self.bot.cache['borderwall'][_guildid]['w'] * 60
            if _bw_seconds == 0:
                _bw_iter_wait = False

            message = self.format_message(
                self.bot.cache['borderwall'][_guildid]['m'],
                guild=member.guild,
                user=member,
                include_user=True,
                include_guild=True,
                extras={
                    "link": _borderwall_url
                })

            if _bw_channel is None or self.bot.cache['borderwall'][_guildid]['d']:
                if not _guildinfo:
                    _guildinfo = await self.bot.get_guild_info(member.guild.id, refer="Member Join")
                try:
                    try:
                        await self.bot.send_user_data(member, message)
                        _sent_dm = True
                    except BaseException:
                        pass
                except BaseException:
                    pass

            if _bw_channel:
                embed = discord.Embed(
                    colour=self.bot.cache['guilddetails'][_guildid]['ec'],
                    description=message)
                try:
                    await _bw_channel.send(embed=embed)
                except BaseException:
                    try:
                        await _bw_channel.send(message)
                    except BaseException:
                        # Dont send a second dm if they have already been sent
                        # one
                        if not _sent_dm:
                            try:
                                await self.bot.send_user_data(member, message)
                            except BaseException:
                                pass

        # rules
        if not _bot and _guildid in self.bot.cache['rules'] and \
                self.bot.cache['rules'][_guildid]['e']:
            message = ""
            pages = 0
            for num, rule in enumerate(self.bot.cache['rules'][_guildid]['r']):
                submessage = f"**{num + 1}**) {rule}\n"
                if len(submessage) + len(message) > 2000:
                    pages += 1
                    await self.bot.send_user_data(member, message, title=f"Rules Page {pages}")
                    # await self.bot.send_data(None, message, force_dm=True, title=f"Rules
                    # Page {pages}")
                    message = ""

                message += submessage

            if len(message) > 0:
                pages += 1
                await self.bot.send_user_data(member, message, title=f"Rules Page {pages}")
                # await self.bot.send_data(None, message, force_dm=True, title=f"Rules
                # Page {pages}")

        # autorole
        if not _bot and _guildid in self.bot.cache['autorole'] and \
                self.bot.cache['autorole'][_guildid]['e']:
            role_list = []
            for role_id in self.bot.cache['autorole'][_guildid]['r']:
                try:
                    _role = member.guild.get_role(int(role_id))
                    if _role:
                        role_list.append(_role)
                except BaseException:
                    pass
            if len(role_list) > 0:
                try:
                    await member.add_roles(*role_list)
                except BaseException:
                    pass

        # welcomer
        if not member.bot and _guildid in self.bot.cache['welcomer']:
            if not _guildinfo:
                _guildinfo = await self.bot.get_guild_info(member.guild.id, refer="Member Join")
            welcomer_config = self.bot.cache['welcomer'][_guildid]
            if welcomer_config['i']['e'] or welcomer_config['dm']['e'] or welcomer_config['t']['e']:
                await self.execute_welcomer(member, _guildinfo, _should_welcome)

        # if _bw_check:
        #     validated = False

        if _bw_iter_wait:
            if not _bot and _guildid in self.bot.cache['borderwall'] and \
                    self.bot.cache['borderwall'][_guildid]['e']:
                _bw_check = False
                _bw_start = time.time()
                while True:
                    await asyncio.sleep(5)
                    # data = await r.table("borderwall").get(_borderwall_key).run(self.bot.connection)
                    data = await self.bot.get_value("borderwall", _borderwall_key)
                    if data['a']:
                        break

                    if (time.time() - _bw_start) > _bw_seconds:
                        break
                    if not member.guild.get_member(member.id):
                        break

            #     if validated:
                    # roles = []
                    # for roleid in list(
                    #         self.bot.cache['borderwall'][_guildid]['r']):
                    #     role = member.guild.get_role(int(roleid))
                    #     if role:
                    #         roles.append(role)

                    # try:
                    #     if len(roles) > 0:
                    #         await member.add_roles(*roles)
                    # except BaseException:
                        # exc_info = sys.exc_info()
                        # traceback.print_exception(*exc_info)

            #         try:
                        # message = self.format_message(
                        #     self.bot.cache['borderwall'][_guildid]['mv'],
                        #     guild=member.guild,
                        #     user=member,
                        #     include_user=True,
                        #     include_guild=True,
                        #     extras={
                        #         "link": _borderwall_url,
                        #         "ip": user_ip if user_ip else "?"})
            #             embed = discord.Embed(
            #                 colour=self.bot.cache['guilddetails'][_guildid]['ec'],
            #                 message=message)
            #             if _bw_channel:
            #                 try:
            #                     await _bw_channel.send(embed=embed)
            #                 except BaseException:
            #                     try:
            #                         await _bw_channel.send(message)
            #                     except BaseException:
            #                         # Dont send a second dm if they have already
            #                         # been sent one
            #                         if not _sent_dm:
            #                             try:
            #                                 await self.bot.send_user_data(member, message)
            #                                 # await self.send_data(None, message, force_dm=True)
            #                             except BaseException:
            #                                 pass
            #             else:
            #                 try:
            #                     await self.bot.send_user_data(member, message)
            #                     # await self.send_data(None, message, force_dm=True)
            #                 except BaseException:
            #                     pass
            #         except BaseException:
            #             exc_info = sys.exc_info()
            #             traceback.print_exception(*exc_info)

            # if not _bw_check:
            #     try:
            #         await self.bot.send_user_data(member, rockutils._("You have been kicked for not validating with borderwall", _guildinfo))
            #         # await self.send_data(None, rockutils._("You have been kicked for not
            #         # validating with borderwall", _guildinfo))
            #     except BaseException:
            #         exc_info = sys.exc_info()
            #         traceback.print_exception(*exc_info)

            #     try:
            #         await member.kick(reason="BorderWall: Verification Timeout")
            #     except BaseException:
            #         exc_info = sys.exc_info()
            #         traceback.print_exception(*exc_info)

        # logging
        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e'] and \
                self.bot.cache['logging'][_guildid]['jl']:
            await rockutils.logcsv([math.floor(time.time()), 'MEMBER_JOIN', member.id, str(member)], f"{member.guild.id}.csv")

        if member.id == self.bot.user.id and self.bot.donator:
            if not _guildinfo:
                _guildinfo = await self.bot.get_guild_info(member.guild.id, refer="Has Donator Sync")
            if not _guildinfo['d']['b']['hd']:
                _guildinfo['d']['b']['hd'] = True
                await self.bot.update_guild_info(_guildid, _guildinfo, refer="On Member Join")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        _guildid = member.guild.id

        if hasattr(member.guild, "chunk"):
            await self.bot.chunk_guild(member.guild)

        # if not self.bot.chunkcache.get(member.guild.id, False) and not member.guild.chunked:
        #     rockutils.prefix_print(
        #         f"Chunking {member.guild.id}", prefix_colour="light yellow", prefix="Worker:OnMemberRemove")
        #     self.bot.chunkcache[member.guild.id] = True
        #     a = time.time()
        #     await member.guild.chunk(cache=True)
        #     rockutils.prefix_print(
        #         f"Chunked {member.guild.id} in {math.ceil((time.time()-a)*1000)}ms", prefix_colour="light yellow", prefix="Worker:OnMemberRemove")
        #     self.bot.chunkcache[member.guild.id] = False

        if not self.bot.donator:
            if member.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        await self.execute_leaver(member, _guildid)

        # leaver
        # if _guildid in self.bot.cache['leaver'] and \
        #         self.bot.cache['leaver'][_guildid]['e']:
        #     leaver_channel = member.guild.get_channel(
        #         int(self.bot.cache['leaver'][_guildid]['c'] or 0))
        #     if leaver_channel:
        #         try:
        #             message = self.format_message(
        #                 self.bot.cache['leaver'][_guildid]['t'],
        #                 guild=member.guild, user=member, include_user=True,
        #                 include_guild=True, extras={})

        #             message_kwargs = {}
        #             if self.bot.cache['leaver'][_guildid]['em']:
        #                 embed = discord.Embed(description=message)
        #                 message_kwargs['embed'] = embed
        #             else:
        #                 message_kwargs['content'] = message

        #             await leaver_channel.send(**message_kwargs)
        #         except BaseException:
        #             exc_info = sys.exc_info()
        #             traceback.print_exception(*exc_info)

        # logging
        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e'] and \
                self.bot.cache['logging'][_guildid]['jl']:
            await rockutils.logcsv([math.floor(time.time()), 'MEMBER_LEAVE', member.id, str(member)], f"{member.guild.id}.csv")

        # staff list check
        update = False
        guildinfo = await self.bot.get_guild_info(member.guild.id, refer="Member Leave")
        if (_guildid in self.bot.cache['staff'] and str(member.id) in [
                u[0] for u in self.bot.cache['staff'][_guildid]['u']]):
            guildinfo['st']['u'] = list(
                filter(
                    lambda o: o[0] != str(
                        member.id),
                    guildinfo['st']['u']))
            await rockutils.logcsv([math.floor(time.time()), 'STAFF_REMOVE', member.id, str(member)], f"{member.guild.id}.csv")
            update = True

        if not member.guild.get_member(498519480985583636) and guildinfo['d']['b']['hd']:
            guildinfo['d']['b']['hd'] = False
            update = True

        if update:
            await self.bot.update_guild_info(_guildid, guildinfo, refer="Has Donator Sync")

    # @commands.Cog.listener()
    # async def on_member_update(self, before, after):
    #     if not after.guild:
    #         return

    #     if not self.bot.donator:
    #         if after.guild.get_member(498519480985583636):
    #             return

    #     # namepurge
    #     _guildid = after.guild.id
    #     _bot = after.bot

    #     # if _guildid not in self.bot.cache['prefix']:
    #     #     await self.bot.get_guild_info(_guildid, refer="Member Update")

    #     if after.guild:

    #         if _guildid in self.bot.cache['namepurge'] and \
    #                 self.bot.cache['namepurge'][_guildid]['e']:
    #             # continue if not a bot or a bot and ignore bots is disabled
    #             if not _bot or (
    #                     _bot and not self.bot.cache['namepurge'][_guildid]['i']):
    #                 _filter = list(filter(lambda o: o.strip() != "", self.bot.cache['namepurge'][_guildid]['f']))
    #                 has_matched = rockutils.regex_text(
    #                     after.display_name, _filter)
    #                 if has_matched:
    #                     matching = [
    #                         before.display_name,
    #                         before.nick,
    #                         "change your name :)"]
    #                     for name in matching:
    #                         if name and name.strip() != "":
    #                             has_matched = rockutils.regex_text(name, _filter)
    #                             if not has_matched:
    #                                 try:
    #                                     await after.edit(nick=name)
    #                                 except BaseException:
    #                                     pass
    #                                 break

    #         if _guildid in self.bot.cache['logging'] and \
    #                 self.bot.cache['logging'][_guildid]['e'] and \
    #                 self.bot.cache['logging'][_guildid]['a']:
    #             profile_change = {}

    #             removed_roles = list(map(lambda o: [o.name, o.id], filter(
    #                 lambda o: o not in after.roles, before.roles)))
    #             added_roles = list(map(lambda o: [o.name, o.id], filter(
    #                 lambda o: o not in before.roles, after.roles)))

    #             if len(removed_roles) > 0:
    #                 profile_change['rem_roles'] = removed_roles

    #             if len(added_roles) > 0:
    #                 profile_change['add_roles'] = added_roles

    #             if before.nick != after.nick:
    #                 profile_change['nick'] = [before.nick, after.nick]
    #             if before.mute != after.mute:
    #                 profile_change['now_mute'] = after.mute
    #             if before.deaf != after.deaf:
    #                 profile_change['now_deaf'] = after.deaf

    #             # ensure there are changes to the member state that we are
    #             # interested in.
    #             if profile_change != {}:
    # await rockutils.logcsv([math.floor(time.time()), 'MEMBER_UPDATE',
    # after.id, str(after), json.dumps(profile_change)],
    # f"{after.guild.id}.csv")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # self.bot.cache['tempchannel'][_guildid]['e'] - enabled
        # self.bot.cache['tempchannel'][_guildid]['l'] - channel id for the lobby
        # self.bot.cache['tempchannel'][_guildid]['c'] - category for tempchannel
        # self.bot.cache['tempchannel'][_guildid]['e'] - autopurge (deleting of channels when empty)

        if not member.guild:
            return

        # if not member.guild.chunked:
        #     await member.guild.chunk(cache=True)

        if not self.bot.donator:
            if member.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        _guildid = member.guild.id

        if _guildid not in self.bot.cache['tempchannel']:
            await self.bot.get_guild_info(_guildid, refer="Voice State Update")

        if member.guild and _guildid in self.bot.cache['tempchannel']:
            category = discord.utils.get(member.guild.channels,
                                         id=int(self.bot.cache['tempchannel'][_guildid]['c'] or 0))

            def has_tempchannel(category, user):
                for channel in category.channels:
                    if str(member.id) in channel.name:
                        return True
                return False

            if self.bot.cache['tempchannel'][_guildid]['e'] and after.channel:
                if category and hasattr(after.channel, "category") and \
                        str(after.channel.id) == self.bot.cache['tempchannel'][_guildid]['l']:
                    if has_tempchannel(category, member):
                        channel = discord.utils.find(lambda o: str(
                            member.id) in o.name, category.channels)
                    else:
                        channel = await member.guild.create_voice_channel(f"{member.name}'s VC [{member.id}]", category=category, user_limit=self.bot.cache['tempchannel'][_guildid]['dl'], reason=f"Tempchannel give requested by lobby")

                    try:
                        await member.move_to(channel)
                    except BaseException:
                        pass

            if before.channel:
                if "'s VC [" in before.channel.name and len(
                    list(
                        filter(
                            lambda o: not o.bot,
                            before.channel.members))) == 0:
                    if _guildid in self.bot.cache['tempchannel'] and \
                            self.bot.cache['tempchannel'][_guildid]['e'] and \
                            self.bot.cache['tempchannel'][_guildid]['ap']:
                        if before.channel.category and str(
                                before.channel.category.id) == self.bot.cache['tempchannel'][_guildid]['c'] and str(
                                before.channel.id) != self.bot.cache['tempchannel'][_guildid]['l']:
                            try:
                                await before.channel.delete(
                                    reason="TempChannel: AutoPurge")
                            except BaseException:
                                pass

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):

        if not self.bot.donator:
            if role.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        _guildid = role.guild.id
        _roleid = str(role.id)
        _config_change = False
        _guildinfo = await self.bot.get_guild_info(_guildid, refer="Role Delete")
        update_payload = {}

        await self.bot.update_info_key(_guildinfo, ["d.r", {
            "r": self.bot.serialiser.roles(role.guild),
            "u": time.time()}],
            refer="on_guild_role_delete")

        # logging
        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e']:
            await rockutils.logcsv([math.floor(time.time()), 'ROLE_DELETE', role.id, role.name], f"{role.guild.id}.csv")

        # freerole
        if _guildid in self.bot.cache['freerole'] and \
                _roleid in self.bot.cache['freerole'][_guildid]['r']:
            update_payload['freerole'] = ["ROLE_REMOVE", _roleid]
            _guildinfo['fr']['r'].remove(_roleid)
            _config_change = True

        # autorole
        if _guildid in self.bot.cache['autorole'] and \
                _roleid in self.bot.cache['autorole'][_guildid]['r']:
            update_payload['autorole'] = ["ROLE_REMOVE", _roleid]
            _guildinfo['ar']['r'].remove(_roleid)
            _config_change = True

        # borderwall
        if _guildid in self.bot.cache['borderwall'] and \
                _roleid == self.bot.cache['borderwall'][_guildid]['r']:
            update_payload['borderwall'] = ["ROLE", _roleid, None]
            _guildinfo['bw']['r'] = None
            _config_change = True

        # timeroles
        if _guildid in self.bot.cache['timeroles'] and _roleid in list(
                map(lambda o: o[0], self.bot.cache['timeroles'][_guildid]['r'])):
            update_payload['timeroles'] = ["ROLE_REMOVE", _roleid]
            _guildinfo['fr']['r'] = list(
                filter(
                    lambda o: o[0] != _roleid,
                    self.bot.cache['timeroles'][_guildid]['r']))
            _config_change = True

        if _config_change:
            await self.bot.update_guild_info(_guildid, _guildinfo, refer="Role Delete")

            if _guildid in self.bot.cache['logging'] and \
                    self.bot.cache['logging'][_guildid]['e'] and \
                    self.bot.cache['logging'][_guildid]['a']:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', self.bot.user.id, str(self.bot.user), json.dumps(update_payload)], f"{role.guild.id}.csv")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):

        if not self.bot.donator:
            if channel.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        _guildid = channel.guild.id
        _channelid = str(channel.id)
        _config_change = False
        _guildinfo = await self.bot.get_guild_info(_guildid, refer="Channel Delete")
        update_payload = {}

        _channels = self.bot.serialiser.channels(channel.guild)
        await self.bot.update_info_key(_guildinfo, ["d.c", {
            "c": _channels['categories'],
            "v": _channels['voice'],
            "t": _channels['text'],
            "u": time.time()}],
            refer="on_guild_channel_delete")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e']:
            await rockutils.logcsv([math.floor(time.time()), 'CHANNEL_DELETE', channel.id, channel.name], f"{channel.guild.id}.csv")

        # logging
        if _guildid in self.bot.cache['borderwall'] and \
                _channelid == self.bot.cache['borderwall'][_guildid]['c']:
            update_payload['borderwall'] = ["CHANNEL", _channelid, None]
            _guildinfo['bw']['c'] = None
            _config_change = True

        # welcomer
        if _guildid in self.bot.cache['welcomer'] and \
                _channelid == self.bot.cache['welcomer'][_guildid]['c']:
            update_payload['welcomer'] = ["CHANNEL", _channelid, None]
            _guildinfo['w']['c'] = None
            _config_change = True

        # leaver
        if _guildid in self.bot.cache['leaver'] and \
                _channelid == self.bot.cache['leaver'][_guildid]['c']:
            update_payload['leaver'] = ["CHANNEL", _channelid, None]
            _guildinfo['l']['c'] = None
            _config_change = True

        # tempchannel
        if _guildid in self.bot.cache['leaver'] and \
                _channelid == self.bot.cache['leaver'][_guildid]['c']:
            update_payload['tempchannel'] = ["CATEGORY", _channelid, None]
            _guildinfo['tc']['c'] = None
            _config_change = True

        # whitelist
        if _guildid in self.bot.cache['channels'] and \
                _channelid in self.bot.cache['channels'][_guildid]['w']['c']:
            update_payload['whitelist'] = ["CHANNEL_REMOVE", _channelid]
            _guildinfo['ch']['w']['c'].remove(_channelid)
            _config_change = True

        # blacklist
        if _guildid in self.bot.cache['channels'] and \
                _channelid in self.bot.cache['channels'][_guildid]['b']['c']:
            update_payload['blacklist'] = ["CHANNEL_REMOVE", _channelid]
            _guildinfo['ch']['b']['c'].remove(_channelid)
            _config_change = True

        # serverstats
        if _guildid in self.bot.cache['stats']:
            _channels = self.bot.cache['stats'][_guildid]['c']
            channels = []
            for channel in _channels:
                if channel.guild.get_channel(int(channel['c'])):
                    channels.append(channel)
                else:
                    _config_change = True
            self.bot.cache['stats'][_guildid]['c'] = channels
            _guildinfo['s']['c'] = channels

        if _config_change:
            await self.bot.update_guild_info(_guildid, _guildinfo, refer="Channel Delete")

            if _guildid in self.bot.cache['logging'] and \
                    self.bot.cache['logging'][_guildid]['e'] and \
                    self.bot.cache['logging'][_guildid]['a']:
                await rockutils.logcsv([math.floor(time.time()), 'CONFIG_CHANGE', self.bot.user.id, str(self.bot.user), json.dumps(update_payload)], f"{channel.guild.id}.csv")

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if not after.guild:
            return

        if not self.bot.donator:
            if after.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        _guildid = after.guild.id

        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Message Edit")

        if after.guild:
            _guildid = after.guild.id
            if _guildid in self.bot.cache['automod'] and \
                    self.bot.cache['automod'][_guildid]['e'] and \
                    not after.author.bot:

                message = after
                guild = after.guild
                config = self.bot.cache['automod'][_guildid]
                await self.perform_automod(message, guild, config)

    # @commands.Cog.listener()
    # async def on_raw_reaction_add(self, payload):
        # while self.bot.cachemutex:
        #     await asyncio.sleep(5)
    #     _user_id = payload.user_id
    #     _guildid = payload.guild_id
    #     _partial_emoji = payload.emoji
    #     _message_id = payload.message_id
    #     _channel_id = payload.channel_id

    #     if not _guildid:
    #         return

    #     is_number = False
    #     try:
    #         number = int(str(_partial_emoji.name).replace(
    #             "️", "").replace("⃣", ""))
    #         is_number = True
    #     except ValueError:
    #         number = None

    #     if _guildid not in self.bot.cache['prefix']:
    #         await self.bot.get_guild_info(_guildid, refer="Reaction Add")

    #     if is_number and number:
    #         if _guildid in self.bot.cache['polls']:
    #             results = list(
    #                 filter(
    #                     lambda o: o['m'] == [
    #                         str(_channel_id),
    #                         str(_message_id)],
    #                     self.bot.cache['polls']))
    #             if results > 0:
    #                 poll = results[0]
    #                 if not str(_user_id) in poll['v']:
    #                     poll['v'][str(_user_id)] = number
    #                     polls = list(
    #                         filter(
    #                             lambda o: o['m'] != [
    #                                 str(_channel_id),
    #                                 str(_message_id)],
    #                             self.bot.cache['polls']))

    #                     channel = self.bot.get_channel(_guildid)
    #                     if channel:
    #                         message = await channel.fetch_message(_message_id)
    #                         embed = rockutils.create_poll_embed(poll)
    #                         if message:
    #                             try:
    #                                 await message.edit(embed=embed)
    #                             except BaseException:
    #                                 pass
    #                         else:
    #                             try:
    #                                 message = await channel.send(embed=embed)
    #                                 poll['m'] = [str(message.id), str(channel.id)]
    #                             except BaseException:
    #                                 pass

    #                     polls.append(poll)
    #                     await self.bot.update_guild_info(_guildid, {"p": polls}, refer="Reaction Add")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        _guildid = channel.guild.id
        if not self.bot.donator:
            if channel.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        _channels = self.bot.serialiser.channels(channel.guild)
        await self.bot.update_info_key(channel.guild.id, ["d.c", {
            "c": _channels['categories'],
            "v": _channels['voice'],
            "t": _channels['text'],
            "u": time.time()}],
            refer="on_guild_channel_create")

        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Channel Create")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e']:
            await rockutils.logcsv([math.floor(time.time()), 'CHANNEL_CREATE', channel.id, channel.name], f"{channel.guild.id}.csv")

        # moderation mute sync
        muted_role = discord.utils.find(
            lambda r: "muted" in r.name.lower(), channel.guild.roles)
        if muted_role:
            try:
                await channel.set_permissions(muted_role, send_messages=False, reason="Muted role permission sync")
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        _guildid = after.guild.id

        if not self.bot.donator:
            if after.guild.get_member(498519480985583636):
                return

        _channels = self.bot.serialiser.channels(after.guild)

        if before.name != after.name:
            if _guildid not in self.channel_updates:
                self.channel_updates[_guildid] = []
            self.channel_updates[_guildid].append(time.time())
            self.channel_updates[_guildid] = sorted(
                self.channel_updates[_guildid])[-60:]

            if len(self.channel_updates[_guildid]) == 60:
                seconds_between_warning = 60  # more than 60 events in less than X seconds triggers it
                difference = self.channel_updates[_guildid][-1] - \
                    self.channel_updates[_guildid][0]

                if difference <= seconds_between_warning:
                    await rockutils.send_webhook("https://[removed]", f"{discord.utils.escape_mentions(discord.utils.escape_markdown(after.guild.name))} ({after.guild.id}) has sent 60 events in {math.ceil(difference)} seconds\n`{before.name}`->`{after.name}`")
                    self.channel_updates[_guildid] = []

        changes = ['name', 'category', 'bitrate',
                   'slowmode', 'userlimit', 'nsfw', 'news']
        hc = False
        for change in changes:
            if hasattr(before, change) and hasattr(after, change):
                if getattr(before, change) != getattr(after, change):
                    hc = True
                    break

        if not hc:
            return

        await self.bot.update_info_key(after.guild.id, ["d.c", {
            "c": _channels['categories'],
            "v": _channels['voice'],
            "t": _channels['text'],
            "u": time.time()}],
            refer="on_guild_channel_update")

        muted_role = discord.utils.find(
            lambda r: "muted" in r.name.lower(), after.guild.roles)
        if muted_role and isinstance(after, discord.TextChannel):
            if muted_role not in after.overwrites:
                try:
                    await after.set_permissions(muted_role, send_messages=False, reason="Muted role permission sync")
                except Exception:
                    pass

        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Channel Update")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e'] and \
                self.bot.cache['logging'][_guildid]['a']:
            update_payload = {}

            if before.name != after.name:
                update_payload['name'] = [before.name, after.name]
            # if before.topic != after.topic:
            #     update_payload['topic'] = [before.topic, after.topic]
            if before.category != after.category:
                update_payload['category'] = [
                    before.category.name, after.category.name]

            if isinstance(after, discord.VoiceChannel):
                if before.bitrate != after.bitrate:
                    update_payload['bitrate'] = [before.bitrate, after.bitrate]
                if before.user_limit != after.user_limit:
                    update_payload['userlimit'] = [
                        before.user_limit, after.user_limit]

            if isinstance(after, discord.TextChannel):
                if before.slowmode_delay != after.slowmode_delay:
                    update_payload['slowmode'] = [
                        before.slowmode_delay, after.slowmode_delay]
                if before.is_nsfw() != after.is_nsfw():
                    update_payload['nsfw'] = [
                        before.is_nsfw(),
                        after.is_nsfw()]
                if before.is_news() != after.is_news():
                    update_payload['news'] = [
                        before.is_news(),
                        after.is_news()]

            if isinstance(after, discord.CategoryChannel):
                if before.is_nsfw() != after.is_nsfw():
                    update_payload['nsfw'] = [
                        before.is_nsfw(),
                        after.is_nsfw()]

            if update_payload != {}:
                await rockutils.logcsv([math.floor(time.time()), 'CHANNEL_UPDATE', after.id, after.name, json.dumps(update_payload)], f"{after.guild.id}.csv")

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        _guildid = role.guild.id

        if not self.bot.donator:
            if role.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Role Create")

        await self.bot.update_info_key(role.guild.id, ["d.r", {
            "r": self.bot.serialiser.roles(role.guild),
            "u": time.time()}],
            refer="on_guild_role_create")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e'] and \
                self.bot.cache['logging'][_guildid]['a']:

            role_payload = {}
            role_payload['name'] = role.name
            role_payload['mention'] = role.mentionable
            role_payload['hoist'] = role.hoist
            role_payload['colour'] = role.colour.value

            nodes = list(
                node for node in dir(
                    discord.Permissions.all()) if isinstance(
                    getattr(
                        discord.Permissions.all(),
                        node),
                    bool))
            permissions = list(
                filter(
                    lambda o,
                    role=role: getattr(
                        role.permissions,
                        o),
                    nodes))
            role_payload['permissions'] = permissions

            await rockutils.logcsv([math.floor(time.time()), 'ROLE_CREATE', role.id, role.name, json.dumps(role_payload)], f"{role.guild.id}.csv")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        _guildid = after.guild.id

        if not self.bot.donator:
            if after.guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Role Update")

        # await self.bot.update_info_key(after.guild.id, ["d.r", {
        #     "r": self.bot.serialiser.roles(after.guild),
        #     "u": time.time()}])

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e'] and \
                self.bot.cache['logging'][_guildid]['a']:

            role_payload = {}
            if before.name != after.name:
                role_payload['name'] = [before.name, after.name]
            if before.mentionable != after.mentionable:
                role_payload['mention'] = after.mentionable
            if before.hoist != after.hoist:
                role_payload['hoist'] = after.hoist
            if before.colour != after.colour:
                role_payload['colour'] = [
                    before.colour.value, after.colour.value]

            nodes = list(
                node for node in dir(
                    discord.Permissions.all()) if isinstance(
                    getattr(
                        discord.Permissions.all(),
                        node),
                    bool))
            before_permissions = list(
                filter(
                    lambda o,
                    role=after: getattr(
                        role.permissions,
                        o),
                    nodes))
            after_permissions = list(
                filter(
                    lambda o,
                    role=before: getattr(
                        role.permissions,
                        o),
                    nodes))
            added_permissions = list(
                filter(
                    lambda o: o not in before_permissions,
                    after_permissions))
            removed_permissions = list(
                filter(
                    lambda o: o not in
                    after_permissions,
                    before_permissions))

            if len(added_permissions) > 0:
                role_payload['permsadd'] = added_permissions
            if len(removed_permissions) > 0:
                role_payload['permsrem'] = removed_permissions

            if role_payload != {}:
                await rockutils.logcsv([math.floor(time.time()), 'ROLE_CREATE', after.id, after.name, json.dumps(role_payload)], f"{after.guild.id}.csv")

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        _guildid = guild.id

        if not self.bot.donator:
            if guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Emoji Update")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e'] and \
                self.bot.cache['logging'][_guildid]['a']:
            emoji_payload = {}

            added_emojis = list(
                filter(
                    lambda o: o not in before.emojis,
                    after.emojis))
            removed_emojis = list(
                filter(
                    lambda o: o not in after.emojis,
                    before.emojis))

            if len(added_emojis) > 0:
                emoji_payload['added'] = list(
                    map(lambda o: [o.id, o.name], added_emojis))
            if len(removed_emojis) > 0:
                emoji_payload['removed'] = list(
                    map(lambda o: [o.id, o.name], removed_emojis))

            if emoji_payload != {}:
                await rockutils.logcsv([math.floor(time.time()), 'EMOJIS_UPDATE', json.dumps(emoji_payload)], f"{guild.id}.csv")

    @commands.Cog.listener()
    async def on_member_ban(self, guild, user):
        _guildid = guild.id

        if not self.bot.donator:
            if guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Member Ban")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e']:
            await rockutils.logcsv([math.floor(time.time()), 'MEMBER_BAN', user.id, str(user)], f"{guild.id}.csv")

    @commands.Cog.listener()
    async def on_member_unban(self, guild, user):
        _guildid = guild.id

        if not self.bot.donator:
            if guild.get_member(498519480985583636):
                return
        while self.bot.cachemutex:
            await asyncio.sleep(5)
        if _guildid not in self.bot.cache['prefix']:
            await self.bot.get_guild_info(_guildid, refer="Member Unban")

        if _guildid in self.bot.cache['logging'] and \
                self.bot.cache['logging'][_guildid]['e']:
            await rockutils.logcsv([math.floor(time.time()), 'MEMBER_UNBAN', user.id, str(user)], f"{guild.id}.csv")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):

        if guild.member_count > 100:
            url = self.bot.config['webhooks']['big_guilds']
        else:
            url = self.bot.config['webhooks']['guilds']

        await rockutils.send_webhook(url, f"[**{rockutils.retrieve_gmt()}**] <:yup:400591876262068226> Joined `{discord.utils.escape_mentions(discord.utils.escape_markdown(guild.name))} {guild.id}` which has **{guild.member_count}** members, of which are **{len(list(m for m in guild.members if m.bot))}** bots")
        pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):

        if guild.member_count > 100:
            url = self.bot.config['webhooks']['big_guilds']
        else:
            url = self.bot.config['webhooks']['guilds']

        await rockutils.send_webhook(url, f"[**{rockutils.retrieve_gmt()}**] <:nuu:400591973037113354> Left `{discord.utils.escape_mentions(discord.utils.escape_markdown(guild.name))} {guild.id}` which had **{guild.member_count}** members, of which are **{len(list(m for m in guild.members if m.bot))}** bots")
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        if self.bot.cachemutex:
            return
        self.bot.cachemutex = True
        done = 0
        l = time.time()
        _time = time.time()
        for guild in self.bot.guilds:
            try:
                guild_info = await self.bot.get_guild_info(guild.id, direct=True, request_invites=False, refer="cache")
                await self.bot.create_guild_cache(guild_info, guild)
                done += 1
                if _time-l > 0.5:
                    print(f"{done}/{len(self.bot.guilds)}")
                    l = _time
            except Exception as e:
                exc_info = sys.exc_info()
                traceback.print_exception(*exc_info)
        rockutils.prefix_print(
            f"Preloaded {done} guilds in {round((time.time() - _time)*1000)} ms",
            prefix="Load Task")
        self.bot.cachemutex = False


def setup(bot):
    worker = Worker(bot)
    setattr(bot, "execute_worker", worker.execute_worker)
    setattr(bot, "worker_task", worker.worker_task)
    # setattr(bot, "handle_stats", worker.handle_stats)
    setattr(bot, "format_message", worker.format_message)

    bot.add_cog(worker)
