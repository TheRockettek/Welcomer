import asyncio
import aiohttp
import discord
import time
import datetime
import shlex
import subprocess
import functools
import threading
import random
import re
import json
import math
import os

from urllib.parse import urlparse, parse_qs
from io import BytesIO, StringIO
from . import opus
from discord.ext import commands

def validint(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

class MusicHandler():

    def __init__(self, bot):
        self.bot = bot

    def shuffle_list(self, list):
        newlist = []
        oldlist = list.copy()
        newlist.append(oldlist[0])
        oldlist.pop(0)
        while len(oldlist) > 0:
            index = random.randint(0,oldlist)
            newlist.append(oldlist[index])
            oldlist.pop(index)
        return newlist

    def get_timeframe(self, seconds):
        secs = seconds % 60
        minutes = int((seconds-secs)/60)
        secs_padding = "0"*(2-len(str(secs))) + str(secs)

        return str(minutes) + ":" + secs_padding

    def youtube_url_validation(self, url):
        youtube_regex = (
            r'(?:https?:\/\/)?(?:www\.)?(?:youtu\.be\/|youtube\.com\/(?:\/|v\/|watch\?v=|watch\?.+(?:&|&#38;);v=))((?:\w|-|_){11})(?:(?:\?|&|&#38;)index=((?:\d){1,3}))?(?:(?:\?|&|&#38;)list=((?:\w|-|_){24}))?(?:\S+)?')

        return not (re.match(youtube_regex, url) is None)

    def ytdl_run(self, cmd):

        args = shlex.split(cmd)

        print(cmd)

        buff = BytesIO()
        p = subprocess.Popen(args, stdin=None, stdout=subprocess.PIPE, stderr=None)
        while True:
            if p.poll() == None:
                std = p.communicate()
                if std[0] is None:
                    break
                buff.write(std[0])
            else:
                break
        decoded = buff.getvalue()
        return self.serialize_ytdl_output(decoded)

    def search_tag(self, term, results=5):

        results = str(results*2)

        cmd = "youtube-dl ytsearch{}:\"{}\" -j --flat-playlist --no-playlist"
        cmd = cmd.format(results, term)

        args = shlex.split(cmd)

        print(cmd)

        buff = BytesIO()
        p = subprocess.Popen(args, stdin=None, stdout=subprocess.PIPE, stderr=None)
        while True:
            if p.poll() == None:
                std = p.communicate()
                if std[0] is None:
                    break
                buff.write(std[0])
            else:
                break
        decoded = buff.getvalue()
        return self.serialize_ytdl_output(decoded)

    def serialize_ytdl_output(self, decoded):
        decoded = decoded.decode()
        list = decoded.split("\n")
        results = []
        for result in list:
            try:
                res = json.loads(result)
                results.append({"url":res['url'],"title":res['title']})
            except Exception as e:
                print(e)

        return results

    def get_voice_client_from_guild(self, id):
        voice_client = list(client for client in self.bot.voice_clients if client.channel.guild.id == id)[0]
        if voice_client:
            return voice_client
        else:
            return None

    def get_ffmpeg_audio(self, filename, *, use_avconv=False, pipe=False, stderr=None, options=None,
                             before_options=None, headers=None, after=None):

        cmd = 'ffmpeg - -f mp3 -ar {} -ac {} -loglevel warning'
        cmd = cmd.format(opus.Encoder(48000, 2).sampling_rate, opus.Encoder(48000, 2).channels)

        print(cmd)

        stdin = None if not pipe else filename
        args = shlex.split(cmd)
        try:
            buff = BytesIO()
            p = subprocess.Popen(args, stdin=stdin, stdout=subprocess.PIPE, stderr=stderr)
            while True:
                if p.poll() == None:
                    std = p.communicate()
                    if std[0] is None:
                        break
                    buff.write(std[0])
                else:
                    break
                print(len(buff.getvalue()))
            self.file = discord.FFmpegPCMAudio(filename)

            return self
        except FileNotFoundError as e:
            raise ClientException('ffmpeg/avconv was not found in your PATH environment variable') from e
        except subprocess.SubprocessError as e:
            raise ClientException('Popen failed: {0.__name__} {1}'.format(type(e), str(e))) from e

    @asyncio.coroutine
    def create_youtube_player(self, url, *, ytdl_options=None, **kwargs):
        import youtube_dl

        opts = {
            'format': 'webm[abr>0]/bestaudio/best',
            'prefer_ffmpeg': True
        }

        ydl = youtube_dl.YoutubeDL(opts)
        func = functools.partial(ydl.extract_info, url, download=False)
        info = yield from self.bot.loop.run_in_executor(None, func)

        if "entries" in info:
            info = info['entries'][0]

        download_url = info['url']

        player = self.get_ffmpeg_audio(download_url, **kwargs)

        player.download_url = download_url
        player.url = url
        player.yt = ydl
        player.views = info.get('view_count')
        player.is_live = bool(info.get('is_live'))
        player.likes = info.get('like_count')
        player.dislikes = info.get('dislike_count')
        player.duration = info.get('duration')
        player.uploader = info.get('uploader')

        is_twitch = 'twitch' in url
        if is_twitch:
            player.title = info.get('description')
            player.description = None
        else:
            player.title = info.get('title')
            player.description = info.get('description')

        date = info.get('upload_date')
        if date:
            try:
                date = datetime.datetime.strptime(date, '%Y%M%d').date()
            except ValueError:
                date = None

        player.upload_date = date

        return player


    @commands.command()
    async def eval(self,ctx):
        if ctx.author.id == 143090142360371200:
            try:
                fas = False
                if ctx.message.content[7:9] == "-a":
                    fas = True
                    e = eval(ctx.message.content[10:])
                else:
                    e = eval(ctx.message.content[7:])
                print(str(e).encode("utf8"))
                if fas == True or (str(type(e)) == "<class 'generator'>") or ("<coroutine object" in str(type(e))) or ("<generator object" in str(type(e))):
                    r = await e
                    try:
                        await ctx.send(r)
                    except:
                        await ctx.send("`" + str(e) + "`")
                else:
                    await ctx.send(e)
            except Exception as e:
                await ctx.send("`" + str(e) + "`")

    @commands.command()
    async def play(self, ctx, *url):
        url = " ".join(url)
        self.id = str(ctx.guild.id)
        if ctx.author.voice is None:
            await ctx.send("You are not in a voice channel")
            return

        if not self.id in self.bot.queue:
            self.bot.queue[self.id] = list()

        joined_guilds = set(o.channel.guild.id for o in self.bot.voice_clients)

        if ctx.guild.id in joined_guilds:
            voice_client = list(client for client in self.bot.voice_clients if client.channel.guild.id == ctx.guild.id)[0]
            if voice_client.channel.id != ctx.author.voice.channel.id:
                await voice_client.move_to(ctx.author.voice.channel)
            voice = voice_client
        else:
            voice = await ctx.author.voice.channel.connect()

        # if voice.is_playing():

        toadd = []
        if self.youtube_url_validation(url):

            if "list=" in url:

                print(url)
                urlparsed = urlparse(url)
                query = parse_qs(urlparsed.query)
                if "list" in query:
                    url = f"https://www.youtube.com/playlist?list={query['list'][0]}"
                else:
                    await ctx.send("Unable to parse playlist url")
                    return
                pl = await ctx.send(f"{self.bot.logging_emotes['loading']['emoji']} Loading Playlist...")
                cmd = f"youtube-dl {url} -j --flat-playlist"
                search = self.ytdl_run(cmd)
                if len(search) == 0:
                    await pl.edit(content="No playlist with this id could be found. Is the url valid?")
                    return
                else:
                    for result in search:
                        toadd.append(result)

            else:

                cmd = f"youtube-dl {url} -j --flat-playlist --no-playlist"
                search = self.ytdl_run(cmd)
                print(search)
                if search == []:
                    await ctx.send(content="This is not a valid youtube video. Is the url valid?")
                    return
                else:
                    toadd.append(search[0])

        else:
            search = self.search_tag(url)
            result_str = ""
            for id, result in enumerate(search):
                result_str += f"[{str(id+1)}] - {str(result['title'])}\n"
            string = f"""```css
Select a result to play:

[0] Cancel

{result_str}

```"""
            message = await ctx.send(string)
            messagee = await self.bot.wait_for('message', check=lambda o: ctx.author.id == o.author.id and validint(o.content) and int(o.content) >= 0 and int(o.content) <= len(search) or "^^play" in o.content, timeout=60)
            await message.delete()
            if messagee is None or messagee.content == "0" or "^^play" in messagee.content:
                return
            result = search[int(messagee.content)-1]
            toadd.append(result)

        self.ctx = ctx

        bulk = False
        if len(toadd) > 1:
            bulk = True
            total = len(toadd)
            await pl.edit(content=f"{self.bot.logging_emotes['loading']['emoji']} 0% Downloading **{str(len(search))}** song{'s' if len(search) != 1 else ''} and adding to queue")
        t = time.time()

        for result in toadd:

            url = "https://youtube.com/watch?v=" + result['url']

            player = await self.create_youtube_player(url, pipe=False)
            player.audio = discord.PCMVolumeTransformer(player.file)
            player.called = time.time()
            player.requested = ctx.author.id
            self.bot.queue[self.id].append(player)
            if time.time()-t > 2 and bulk:
                await pl.edit(content=f"{self.bot.logging_emotes['loading']['emoji']} {str(math.ceil((total-len(toadd))/total*100))}% Downloading **{str(len(search))}** song{'s' if len(search) != 1 else ''} and adding to queue")

        if len(toadd) > 1:
            await ctx.send(f"Queued **{str(len(toadd))}** song{'s' if len(toadd) != 1 else ''}")
        else:
            await ctx.send(f"Queued **{str(player.title)}**")

        if not self.id in self.bot.active:
            self.bot.active.append(self.id)
            waiting = 0
            while True:
                queue = self.bot.queue[self.id]
                print(queue)
                while voice.is_playing() == True:
                    await asyncio.sleep(0.25)
                if len(queue) > 0:
                    next = queue[0]
                    await self.ctx.send(f"Now playing **{str(player.title)}**")
                    voice.play(player.audio)
                    while voice.is_playing() == True:
                        await asyncio.sleep(0.5)
                    if next in self.bot.queue[self.id]:
                        self.bot.queue[self.id].remove(next)
                await asyncio.sleep(1)
                if len(self.bot.queue[self.id]) == 0:
                    waiting += 1
                if waiting >= 60:
                    await voice.disconnect()
                    await ctx.send("Finished queue")
                    if self.id in self.bot.skips:
                        del self.bot.skips[self.id]
                        del self.bot.active[self.id]
                    return

    @commands.command()
    async def queue(self, ctx):
        """Lists current queue"""
        self.id = str(ctx.guild.id)
        if not self.id in self.bot.queue:
            self.bot.queue[self.id] = list()

        total = 0
        for p in self.bot.queue[self.id]:
            total += p.duration
        q = "\n".join(set(f'[{str(number+1)}] {player.title} [{self.get_timeframe(player.duration)}]' for number, player in enumerate(self.bot.queue[self.id])))
        if q is "":
            q = "The queue is empty, do ^^play <term or youtube url>"
        await ctx.send(f"""```css
Current Queue:

{q}

Total Time: {self.get_timeframe(total)}```""")

    @commands.command(aliases=['setvolume','setvol','vol'])
    async def volume(self, ctx, volume:int=100):
        """Changes audio volume"""
        vol = volume/100
        if vol > 2:
            vol = 2
        self.id = str(ctx.guild.id)
        if self.id in self.bot.queue:
            if len(self.bot.queue[self.id]) > 0:
                setattr(self.bot.queue[self.id][0].audio, "volume", vol)
                await ctx.send(f"Set volume to **{str(vol*100)}**%")
            else:
                await ctx.send("You do not have anything playing at the moment", delete_after=30)
        else:
            await ctx.send("Minor is not connected to any voice channels on this server", delete_after=30)

    @commands.command()
    async def shuffle(self, ctx):
        """Shuffles all songs in queue"""
        self.id = str(ctx.guild.id)

        if len(self.bot.queue[self.id]) > 0:
            self.bot.queue[self.id] = self.shuffle_list(self.bot.queue[self.id])
            await ctx.send(f"Shuffled **{str(len(self.bot.queue[self.id]))}** song{'s' if len(self.bot.queue[self.id]) != 1 else ''}")
        else:
            await ctx.send("You do not have any songs on queue", delete_after=30)

    @commands.command()
    async def skip(self, ctx):
        """Requests song skip"""
        voted = False
        self.id = str(ctx.guild.id)
        if not self.id in self.bot.skips:
            self.bot.skips[self.id] = list()

        if ctx.author.id in self.bot.skips[self.id]:
            voted = True
        else:
            self.bot.skips[self.id].append(ctx.author.id)
        voice_client = self.get_voice_client_from_guild(ctx.guild.id)
        total_users = list(u.id for u in ctx.author.voice.channel.members if u.bot == False)
        needed = math.ceil(len(total_users) / 2)
        skipped = 0
        for user in total_users:
            if user in self.bot.skips[self.id]:
                skipped += 1

        if skipped >= needed:
            voice_client.stop()
            await ctx.send("Skipped song")
        else:
            if not voted:
                await ctx.send(f"**{str(ctx.author)}** has voted to skip the song [**{str(skipped)}**/**{str(needed)}**]")
            else:
                await ctx.send(f"You have already voted to skip. [**{str(skipped)}**/**{str(needed)}**]")


def setup(bot):
    bot.add_cog(MusicHandler(bot))