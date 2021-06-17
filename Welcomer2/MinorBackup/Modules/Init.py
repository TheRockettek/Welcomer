# coding=utf-8

import asyncio
import discord
import discord.abc
import discord.utils
import datetime
import json
import math
import os
import psutil
import rethinkdb as r
import requests
import sys
import time
import traceback
import concurrent.futures


from datetime import datetime
from discord.ext import commands
from DataIO import dataIO
import rethinkdb as r


def merge(sets):
    new = dict()
    for index, dicts in sets.items():
        for i, k in dicts.items():
            new[i] = k
    return new


def sendWebhookMessage(message, webhookurl="https://canary.discordapp.com/api/webhooks/413797385052094486/JFhGwlObwL1CIQSo81kMK_sfQViEB_VWa5nrIKtdfgyPn7y5uhiYvJ0_U5pf-2g92tnL"):
    return requests.post(webhookurl, headers={'Content-Type': 'application/json'}, data=json.dumps({"content": message}))


global bot

queues = dict()


class WelcomerInit():

    def __init__(self, bot):
        self.bot = bot
        self.running = False
        self.bot.logging_emotes = dataIO.load_json("logging_emotes.json")

    async def is_elevated(self, guild, id):
        member = guild.get_member(id)
        if guild.owner.id == member.id:
            return True
        elif member.top_role.permissions.manage_guild or member.top_role.permissions.manage_roles or member.top_role.permissions.administrator:
            return True
        else:
            return False

    async def get_elevated(self, id):
        elevated = dict()

        mutual = self.bot.get_mutual(self, id)
        for guild in mutual:
            member = guild.get_member(int(id))
            if guild.owner.id == member.id:
                elevated[str(guild.id)] = True
            elif member.top_role.permissions.manage_guild or member.top_role.permissions.manage_roles or member.top_role.permissions.administrator:
                elevated[str(guild.id)] = True
            else:
                elevated[str(guild.id)] = False
        return elevated

    async def reload_data(self, name):
        try:
            dat = dataIO.load_json(name)
            return True, dat
        except:
            return False, {}

    async def update_data(self, name, table):
        return dataIO.save_json(name, table)

    async def get_guild_invite(self, id):
        guild = self.bot.get_guild(int(id))
        if guild:
            allchannels = sorted(
                guild.channels, key=lambda item: item.position)
            channels = dict()
            for channelinfo in allchannels:
                if type(channelinfo) == discord.channel.TextChannel:
                    channels[len(channels)] = channelinfo
            for index, channel in channels.items():
                invite = await channel.create_invite(unique=False)
                if invite:
                    return invite.code

    def extractEmotes(self, guild):
        emotes = dict()
        for emote in guild.emojis:
            emotes[str(emote.name)] = {"name": emote.name, "id": str(emote.id), "emoji": emote.__str__(), "url": emote.url,
                                       "animated": emote.animated}
        return emotes

    def extractGuildInfo(self, guild):
        bots = len(set(member for member in guild.members if member.bot == True))
        members = int(guild.member_count)
        data = {"owner": str(guild.owner), "oid": str(guild.owner.id), "bots": bots, "members": members, "name": guild.name,
                "id": str(guild.id), "icon": guild.icon_url or ""}
        return data

    async def get_all_mutual(self, id, user_data):

        guilds = list()
        for o in self.bot.mutual_servers(self, str(id)):
            guilds.append(o)
        user_data['mutual'] = guilds
        return user_data

    async def extractUserInfo(self, user, id):

        if not user is None:
            user_data = {"name": str(user) or "", "id": str(id) or 0, "avatar": user.avatar_url or user.default_avatar_url or "",
                         "mutual": dict()}
        else:
            user_data = {"name": "", "id": str(
                id), "avatar": "", "mutual": dict()}

        return user_data

    def get_mutual(self, id):
        guilds = list()
        for guild in self.bot.guilds:
            for member in guild.members:
                if str(member.id) == str(id):
                    guilds.append(guild)
        return guilds

    def mutual_servers(self, id):
        guilds = list()
        for guild in self.bot.guilds:
            for member in guild.members:
                if str(member.id) == str(id):
                    guilds.append(self.bot.extractGuildInfo(self, guild))
        return guilds

    async def get_invites(self, id):
        guild = self.bot.get_guild(int(id))

        invites = dict()
        try:
            invite_list = await guild.invites()
            for invite in invite_list:
                if hasattr(invite, "inviter"):
                    inv = str(invite.inviter.id)
                else:
                    inv = "0"
                invites[invite.code] = {}
                invites[invite.code]["member"] = str(invite.inviter)
                invites[invite.code]["id"] = inv
                invites[invite.code]["uses"] = invite.uses
                invites[invite.code]["created"] = invite.created_at.timestamp() or 0
        except Exception as e:
            print(e)
            invites = {}

        return invites

    async def create_transaction(self, to, pyr, ammount, metadata=""):

        payer = await self.bot.get_user_info(self, pyr)
        recep = await self.bot.get_user_info(self, to)

        if int(payer['id']) != 330416853971107840:
            if payer['money'] < ammount:
                return False, 0

        if int(payer['id']) != 330416853971107840:
            payer['money'] -= ammount

        payload = {"from": str(pyr), "to": str(
            to), "ammount": ammount, "metadata": metadata}
        payment_data = await r.table("payments").insert(payload).run(self.bot.connection)

        payment_id = payment_data['generated_keys'][0]

        if str(pyr) != 330416853971107840:
            recep['trans'].append(payment_id)
        recep['money'] += ammount

        await self.bot.update_user_info(self, str(pyr), payer)
        await self.bot.update_user_info(self, str(to), recep)

        time = datetime.now().strftime("%H:%M:%S %d/%m")
        if metadata != "":
            metadata = "`" + metadata + "`"

        m = f"[**{time}**] [Transaction ID: **{payment_id}**]\n:money_with_wings:  | ₩ **{str(ammount)}** has been transfered from **{str(payer['name'])}** to **{str(recep['name'])}**\n{metadata}"

        user = self.bot.get_user(int(to))
        try:
            await user.send(f":file_cabinet: Transaction Proof\nTime: **{time}**\nTransaction ID: **{payment_id}**\n\nType: Incomming\n\nTeller: {payer['name']} `{str(pyr)}`\nRecipient: {recep['name']} `{str(pyr)}`\nAmount: {str(ammount)}\nMetadata: {str(metadata)}")
        except:
            0
        user = self.bot.get_user(int(pyr))
        try:
            await user.send(f":file_cabinet: Transaction Proof\nTime: **{time}**\nTransaction ID: **{payment_id}**\n\nType: Outgoing\n\nTeller: {payer['name']} `{str(pyr)}`\nRecipient: {recep['name']} `{str(pyr)}`\nAmount: {str(ammount)}\nMetadata: {str(metadata)}")
        except:
            0

        sendWebhookMessage(
            message=m, webhookurl="https://canary.discordapp.com/api/webhooks/435394892550635520/nKadQdFUGG0z7FZ7p8xrS3GRfs6WzxOoQNUdB5n-FxdFA2B3c0jvcNbYNq05avrNk-KF")

        return True, payment_id


class SyncHandler():

    def __init__(self, bot):
        self.bot = bot
        self.running = False
        globals()['bot'] = self.bot

    async def on_ready(self):
        self.bot.uptime = datetime.now()
        emotes = dataIO.load_json("logging_emotes.json")
        setattr(self.bot, "logging_emotes", emotes)
        if not bot.TEST_MODE:
            sendWebhookMessage(
                message=f":white_small_square: | Cluster **{str(bot.CLUSTER_ID)}** has restarted", webhookurl="")

    async def cpre(self, i=True):
        memberlist = list(self.bot.get_all_members())
        # responce = dict()
        # responce['members'] = len(memberlist)
        # responce['unique'] = len(set(m.id for m in memberlist))
        # responce['guilds'] = len(self.bot.guilds)
        # responce['id'] = str(self.bot.CLUSTER_ID)
        # await r.table("botinfo").get(str(self.bot.CLUSTER_ID)).replace(responce).run(self.bot.connection)
        try:
            # mini_infos = await r.table("botinfo").run(self.bot.connection)
            # i = not i
            # members = 0
            # unique = 0
            # guilds = 0
            # for mini_info in mini_infos.items:
            #     members += mini_info['members']
            #     unique += mini_info['unique']
            #     guilds += mini_info['guilds']
            guilds = len(self.bot.guilds)
            members = len(memberlist)
            if i == True:
                message = f"with {str(guilds)} guilds | ^^play"
            else:
                message = f"with {str(members)} members | ^^help"
            await self.bot.change_presence(activity=discord.Game(name=message))
        except Exception as e:
            print(str(e))

    async def req(self):

        if not hasattr(self.bot, "logging_emotes") or self.bot.logging_emotes == {}:
            beginning_time = time.time()
            try:
                emotes = dataIO.load_json("logging_emotes.json")
                setattr(self.bot, "logging_emotes", emotes)
                end_time = time.time()
                tts = math.ceil((end_time - beginning_time) * 1000)
                print(
                    f"Retrieved {str(len(bot.emotes))} emotes in {str(tts)} ms")
            except Exception as e:
                sendWebhookMessage(message=f"Cluster {str(self.bot.CLUSTER_ID)} EMOJI Error: `{str(e)}`",
                                   webhookurl="https://canary.discordapp.com/api/webhooks/430691452826288130/XbXQ-6PYPM1wfBUlkQRGTQtVEgnZMqHmqI8TGmn_hNgPrasUh4KSCp05kcgLZ1-jIVt8")

        try:
            await self.bot.get_requests(self)
        except Exception as e:
            sendWebhookMessage(
                message=f"Cluster {str(self.bot.CLUSTER_ID)} CC Error: `{str(e)}`", webhookurl="")


def setup(bot):
    setattr(bot, "logging_emotes", dataIO.load_json("logging_emotes.json"))
    WelcomerInit(bot)
    bot.add_cog(SyncHandler(bot))

    setattr(bot, "running", False)
    setattr(bot, "handler_ready", True)

    setattr(bot, "reload_data", WelcomerInit.reload_data)
    setattr(bot, "update_data", WelcomerInit.update_data)

    setattr(bot, "get_elevated", WelcomerInit.get_elevated)
    setattr(bot, "get_invites", WelcomerInit.get_invites)
    setattr(bot, "get_mutual", WelcomerInit.get_mutual)
    setattr(bot, "mutual_servers", WelcomerInit.mutual_servers)
    setattr(bot, "get_guild_invite", WelcomerInit.get_guild_invite)

    setattr(bot, "extractEmotes", WelcomerInit.extractEmotes)
    setattr(bot, "extractUserInfo", WelcomerInit.extractUserInfo)
    setattr(bot, "extractGuildInfo", WelcomerInit.extractGuildInfo)

    setattr(bot, "get_all_mutual", WelcomerInit.get_all_mutual)
    setattr(bot, "get_mutual", WelcomerInit.get_mutual)

    setattr(bot, "create_transaction", WelcomerInit.create_transaction)
    setattr(bot, "is_elevated", WelcomerInit.is_elevated)

    setattr(bot, "done", dict())
