import copy
import math
import time
import os

import rethinkdb as r

from datetime import datetime
from rockutils import rockutils

class WelcomerCore():
    def __init__(self, bot):
        self.bot = bot

    async def check_permissions(self, permission_list:list, nodes:list, wildcards=True):
        permissions = []
        targets = []

        for node in nodes:
            targets.append(node)
            if wildcards:
                node_sep = node.split(".")
                for i in range(0, len(node_sep)):
                    tnode = node_sep[:i]
                    tnode.append("*")
                    targets.append(".".join(tnode))
        allowed = 0
        for target in permission_list:
            if target in targets:
                return True
        return False

    async def has_permission(self, member, guild, guildinfo, userinfo, server_staff=False, adminstrator=False,
                moderator=False, owner=False, developer=False, pro=False, plus=False, partner=False):
        if server_staff:
            if guild:
                if str(member.id) in guildinfo['permissions']['staff']:
                    return True
                if list(str(r.id) for r in member.roles):
                    return True
                if has_guild_permissions(self, member, "manage_guild"):
                    return True
                if member.id == guild.owner.id:
                    return True
        if adminstrator:
            if member.id in self.config['staff']['admins']:
                return True
        if owner:
            if guild:
                if member.id == guild.owner.id:
                    return True
        if developer:
            if member.id in self.config['staff']['developer']:
                return True
        if pro:
            if userinfo['membership']['pro']:
                return True
        if plus:
            if userinfo['membership']['plus']:
                return True
        if partner:
            if userinfo['membership']['partner']:
                return True

        return False

    async def send_data(self, ctx, message, raw=False, force_guild=False, force_dm=False, alert=True, title=None, footer=None):
        extra = None
        message_kwargs = {}
        if raw:
            message_kwargs['content'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
        else:
            kwargs = {}
            kwargs['description'] = message[:2048]
            if len(message) > 2048:
                extra = message[2048:]
            kwargs['colour'] = discord.Colour(0x678f98),
            kwargs['timestamp'] = datetime.utcfromtimestamp(math.ceil(time.time()))
            if title:
                kwargs['title'] = title
            embed = discord.Embed(**kwargs)
            embed.set_footer(text=footer)
            message_kwargs['embed'] = embed

        guild_works = True
        dm_works = True

        if force_guild:
            try:
                await ctx.send(**message_kwargs)
            except:
                return
        
        if force_dm:
            try:
                if alert:
                    try:
                        await ctx.send(":mailbox_with_mail: __Support has been sent in your Direct Messages if possible__")
                    except:
                        pass
                await ctx.author.send(**message_kwargs)
            except:
                return

        # prefer_dms

        if extra is None:
            return
        else:
            await self.send_data(self, ctx, extra, raw=raw, force_guild=force_guild, force_dm=force_dm, alert=False, title=title, footer=footer)

    async def reload_data(self, filename, key=None):
        if not key:
            head, key = os.path.split(filename)
            key = key[:key.find(".")]

        if os.path.exists(filename):
            data = rockutils.load_json(filename)
            if not key:
                head, key = os.path.split(filename)
                key = key[:key.find(".")]
            setattr(self.bot, key, data)
            return True, key
        else:
            return False, key

    async def get_guild_info(self, guild_id, refer=""):
        rockutils.pprint(f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for {guild_id}", prefix="get_guild_info", prefix_colour="light green")
        guild_data = await r.table("guilds").get(int(guild_id)).run(self.bot.connection)

        update = False
        new = False

        guild = self.bot.get_guild(self, int(guild_id))

        if guild_data is None and guild:
            guild_data = copy.deepcopy(rockutils.load_json("data/default_guild.json"))
            guild_data['id'] = int(guild_id)
            guild_data['details']['guild_addition'] = math.ceil(time.time())
            mew = True

        guild_data['cluster'] = self.bot.cluster_id

        if guild:
            if time.time()-guild_data['details']['update'] > 600:
                guild_data['details']['splash'] = guild.splash
                guild_data['details']['region'] = str(guild.region)
                guild_data['details']['icon'] = [
                    guild.icon_url_as(format="jpeg",size=64),
                    guild.icon_url_as(format="png",size=256)
                ]
                guild_data['details']['name'] = guild.name
                guild_data['details']['guild_creation'] = math.ceil(guild.created_at.timestamp())
                guild_data['details']['owner'] = str(guild.owner.id)
                guild_data['details']['update'] = time.time()
                update = True
            if time.time()-guild_data['details']['detailed']['update'] > 300:
                detailed = self.extract_guild_detailed(self, guild)
                guild_data['details']['detailed'] = detailed
                guild_data['details']['detailed']['update'] = time.time()
                guild_data['details']['members']['bots'] = detailed['bots']
                guild_data['details']['members']['members'] = detailed['members']
                guild_data['details']['members']['all'] = detailed['bots']+detailed['members']
                del guild_data['details']['detailed']['bots']
                del guild_data['details']['detailed']['members']
                update = True
            if time.time()-guild_data['details']['guild']['channels']['update'] > 1800:
                channels = self.extract_channels(self, guild)
                guild_data['guild']['channels'] = channels
                guild_data['guild']['channels']['update'] = time.time()
                update = True
        
        if update or new:
            if new:
                rockutils.pprint(f"Creating information for {guild_id}", prefix="get_guild_info", prefix_colour="light green")
                await r.table("guilds").insert(guild_data).run(self.bot.connection)
            else:
                await update_guild_info(self, guild_id, guild_data, refer="get_guild_info")

        return guild_data

    async def get_user_info(self, user_id, refer=""):
        rockutils.pprint(f"{f'[Refer: {refer}] ' if refer != '' else ''}Getting information for {user_id}", prefix="get_user_info", prefix_colour="light green")
        user_data = await r.table("users").get(int(user_id)).run(self.bot.connection)

        update = False
        new = False

        user = self.bot.get_user(self, int(user_id))

        if user_data is None and user:
            user_data = copy.deepcopy(rockutils.load_json("data/default_user.json"))
            user_data['id'] = int(user_id)
            user_data['details']['user_addition'] = math.ceil(time.time())
            user_data['previous_names'].append([user.name,math.ceil(time.time())])
            new = True

        if user:
            if not self.bot.cluster_id in user_data['last_mutual']:
                user_data['last_mutual'][self.bot.cluster_id] = 0
                update = True
            if time.time()-user_data['last_mutual'][self.bot.cluster_id] > 600:
                user_data['mutual'][self.bot.cluster_id] = self.mutual_guilds(self, user)
                user_data['last_mutual'][self.bot.cluster_id] = time.time()
                update = True

            if time.time()-user_data['details'] > 600:
                user_data['details']['avatar'] = [
                    user.avatar_url_as(format="jpeg",size=64),
                    user.avatar_url_as(format="png",size=256)
                ]
                if user.name != user_data['details']['name']:
                    user_data['previous_names'].append([user.name,math.ceil(time.time())])
                user_data['details']['name'] = user.name
                user_data['details']['discriminator'] = user.discriminator
                user_data['details']['user_creation'] = math.ceil(user.created_at.timestamp())
                user_data['details']['update'] = time.time()
                update = True
        
        if update or new:
            if new:
                rockutils.pprint(f"Creating information for {user_id}", prefix="get_user_info", prefix_colour="light green")
                await r.table("users").insert(user_data).run(self.bot.connection)
            else:
                await update_user_info(self, user_id, user_data, refer="get_user_info")

        return user_data

    async def update_guild_info(self, guild_id, data, refer=""):
        try:
            rockutils.pprint(f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for {guild_id}", prefix="update_guild_info", prefix_colour="light green")
            await r.table("guilds").get(int(guild_id)).update(data).run(self.bot.connection)
            return True
        except:
            return False

    async def update_user_info(self, user_id, data, refer=""):
        try:
            rockutils.pprint(f"{f'[Refer: {refer}] ' if refer != '' else ''}Updating information for {guild_id}", prefix="update_user_info", prefix_colour="light green")
            await r.table("users").get(int(user_id)).update(data).run(self.bot.connection)
            return True
        except:
            return False

    def has_guild_permissions(self, target, check_for, return_has=False):
        permissions = discord.Permissions.all()
        my_permissions = {}
        for key in list(node.upper() for node in dir(permissions) if type(getattr(permissions, node)) == bool):
            my_permissions[key] = False

        for role in target.roles:
            for node in my_permissions:
                if getattr(role.permissions, node.lower()) == True:
                    my_permissions[node] = True

        if len(check_for) > 0:
            my_permissions = list(node for node,val in my_permissions.items() if val)
            if "ADMINISTRATOR" in my_permissions:
                return True

            for node in check_for:
                if node.upper() in my_permissions:
                    return True, my_permissions
            return False, my_permissions
        elif return_has:
            return list(node for node,val in my_permissions.items() if val)
        else:
            return my_permissions

    def extract_guild_detailed(self, guild):
        detailed = {
            "streaming": 0,
            "online": 0,
            "idle": 0,
            "dnd": 0,
            "offline": 0,
            "bots": 0,
            "members": 0,
        }

        for member in guild.members:
            if member.bot:
                detailed['bots'] += 1
            else:
                detailed['members'] += 1
            if hasattr(member, "activity") and str(member.activity.type) == "ActivityType.streaming":
                detailed['streaming'] += 1
            if hasattr(member, "status"):
                detailed[str(member.status)] += 1

        return detailed

    def extract_channels(self, guild):
        channels = {
            "categories": [],
            "voice": [],
            "text": []
        }

        for channel in guild.channels:
            if type(channel) == discord.TextChannel:
                channels['text'].append({
                    "name": channel.name,
                    "id": channel.id,
                    "position": channel.position,
                    "category": getattr(channel,"category_id"),
                    "topic": channel.topic,
                    "nsfw": channel.is_nsfw()
                })
            if type(channel) == discord.VoiceChannel:
                channels['voice'].append({
                    "name": channel.name,
                    "id": channel.id,
                    "position": channel.position,
                    "category": getattr(channel,"category_id"),
                    "bitrate": channel.bitrate,
                    "user_limit": channel.user_limit
                })
            if type(channel) == discord.CategoryChannel:
                channels['categories'].append({
                    "name": channel.name,
                    "id": channel.id,
                    "position": channel.position,
                    "nsfw": channel.is_nsfw()
                })

        return channels

    def extract_guild_info(self, guild):
        return guild

    def extract_user_info(self, user):
        return user

    def extract_emotes(self, guild):
        emotes = []
        for emoji in guild.emojis:
            emotes.append({
                "name": emoji.name,
                "animated": emoji.animated,
                "url": emoji.url,
                "created_at": math.ceil(emoji.created_at.timestamp())
            })
        return emotes

    async def extract_invites(self, guild):
        invites = []
        try:
            for invite in await guild.invites():
                if not invite.revoked:
                    invites.append({
                        "code": invite.code,
                        "created_at": math.ceil(invite.created_at.timestamp()),
                        "temp": invite.temporary,
                        "uses": invite.uses,
                        "max": invite.max_uses,
                        "inviter": invite.inviter.id,
                        "inviter_str": str(invite.inviter)
                    })
        except:
            pass
        return invites

    def mutual_guilds(self, user):
        guilds = []
        for guild in self.bot.guilds:
            for member in guild.members:
                if member.id == user.id:
                    guilds.append(self.extract_guild_info(self, guild))
        return guilds

    # emotes

    # prefix cache
    # giveaway cache
    # voting cache

    # automod cache
    # welcomer cache
    # logging cache
    # serverstats cache
    # counting cache
    # borderwall cache
    # xp cache
    # white/blacklist cache
    # slowmode cache
    # timerole cache
    # serverlock cache

    # message handle
    # process command handle

    # is_elevated
    # broadcast
    # 

def setup(bot):
    bot.add_cog(WelcomerCore(bot))

    def existingattr(subject, key, data):
        if not hasattr(subject, key):
            setattr(subject, key, data)

    def existingdict(subject, key, data):
        if not subject.get(key):
            subject[key] = data

    caches = [
        "prefix",
        "giveaway",
        "voting-polls",
        "automod",
        "welcomer",
        "logging",
        "serverstats",
        "counting",
        "borderwall",
        "xp",
        "channel-management",
        "slowmode",
        "timeroles",
        "serverlock"
    ]

    for name in caches:
        existingdict(bot.cache, name, {})

    setattr(bot, "check_permission", WelcomerCore.check_permissions)
    setattr(bot, "has_permission", WelcomerCore.has_permission)
    setattr(bot, "has_guild_permissions", WelcomerCore.has_guild_permissions)

    setattr(bot, "get_guild_info", WelcomerCore.get_guild_info)
    setattr(bot, "get_user_info", WelcomerCore.get_user_info)

    setattr(bot, "update_guild_info", WelcomerCore.update_guild_info)
    setattr(bot, "update_user_info", WelcomerCore.update_user_info)

    setattr(bot, "send_data", WelcomerCore.send_data)
    setattr(bot, "mutual_guilds", WelcomerCore.mutual_guilds)

    setattr(bot, "extract_invites", WelcomerCore.extract_invites)
    setattr(bot, "extract_emotes", WelcomerCore.extract_emotes)
    setattr(bot, "extract_user_info", WelcomerCore.extract_user_info)
    setattr(bot, "extract_guild_info", WelcomerCore.extract_guild_info)
    setattr(bot, "extract_channels", WelcomerCore.extract_channels)
    setattr(bot, "extract_guild_detailed", WelcomerCore.extract_guild_detailed)
