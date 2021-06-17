import asyncio
import datetime
import discord
import json
import io
import math

from discord.ext import commands

class Core():

	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	async def botinfo(self, ctx):
		await ctx.send(embed=self.bot.botinfo())

	@commands.command()
	async def migrate(self, ctx):
		a = self.bot.data['default_configs']['server']
		b = await self.bot.get_guild_info(ctx.guild.id)
		c = b.update(a)
		await self.bot.update_guild_info(ctx.guild.id,c)
		await ctx.send(":thumbsup:")

	@commands.command()
	async def umigrate(self, ctx):
		a = self.bot.data['default_configs']['user'].copy()
		b = await self.bot.get_user_info(ctx.author.id)
		c = b.update(a)
		await self.bot.update_user_info(ctx.author.id,c)
		await ctx.send(":thumbsup:")

	@commands.command()
	async def eval(self,ctx):
		if await self.bot.is_operator(ctx.author):
			try:
				e = eval(ctx.message.content[6:])
				print(e)
				if str(type(e)) == "<class 'generator'>":
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
	async def grab(self, ctx):
		await ctx.send("Start")
		pb = """
		<link href="https://use.fontawesome.com/releases/v5.0.6/css/all.css" rel="stylesheet">

<head>
    <link rel="stylesheet" type="text/css" href="https://welcomer.fun/static/site.css">
    <title>Welcomer</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#2f3136">
    <meta property="og:title" content="welcomer.fun">
    <meta property="og:description" content="Welcomer the discord bot!">
    <meta property="og:url" content="https://welcomer.fun">
</head>

<header>
    <ul class="menu">
            <li><a href="/">Welcomer</a></li>
            <li><a href="https://discordapp.com/oauth2">Invite</a></li>
            <li><a href="https://discord.gg/abc">Support</a></li>
            <li><a href="/donate">Donate</a></li>
            <li><a href="/serverlist">Server List</a></li>
            <li><a href="/me">ImRock#3779</a></li>
            <li><a href="/logout">Logout</a></li>
    </ul>
</header>

<div class="container">

<div class="userinfo">
    <img class="pfp" src="https://cdn.discordapp.com/icons/341685098468343822/77e95d701fd41e6414177cb61108436f.webp?size=64">
    <div class="info">
        <div>
            <a class="name">This Server is Required</a>
            <a class="badge" style="background-color: orangered">Pro</a>
        </div>
        <div class="badges">
            <a class="badge" style="background-color: #3a3c3a">Total Users: 5352</a>
            <a class="badge" style="background-color: #525452">Members: 5338</a>
            <a class="badge" style="background-color: #717371">Bots: 14</a>      
        </div>
        <div class="badges">
            <a class="badge" style="background-color: green">Online: 2877</a>
            <a class="badge" style="background-color: #fb8b06">Idle: 45</a>
            <a class="badge" style="background-color: #dc3101">DND: 124</a>
            <a class="badge" style="background-color: #232323">Offline: 2226</a>
        </div>
    </div>
</div>

<br>

<div class="title">Server Administration</div>
<div class="container">
    <a href="/server/341685098468343822/edit" class="mysetting">
        <div class="upper">
            <div class="img-wrapper">
                <img class="img-icon" src="https://canary.discordapp.com/assets/c61c8e1ffdcbf98496bc098c35f0f694.svg">
            </div>
        </div>
        <div class="lower">
            <span>Manage Server</span>
        </div>
    </a>
    <a href="/server/341685098468343822/members" class="mysetting">
        <div class="upper">
            <div class="img-wrapper">
                <img class="img-icon" src="https://canary.discordapp.com/assets/ffcdb50ce310bfbe221f01a8e72034a8.svg">
            </div>
        </div>
        <div class="lower">
            <span>Manage Members</span>
        </div>
    </a>
    <a href="/server/341685098468343822/stats" class="mysetting">
        <div class="upper">
            <div class="img-wrapper">
                <img class="img-icon" src="https://canary.discordapp.com/assets/79a590ea84f8e3a347aa62b32b78e0d5.svg">
            </div>
        </div>
        <div class="lower">
            <span>Server Stats</span>
        </div>
    </a>
    <a href="/server/341685098468343822/logs" class="mysetting">
        <div class="upper">
            <div class="img-wrapper">
                <img class="img-icon" src="https://canary.discordapp.com/assets/3f19971e1ed28b05a799827e337fd9fe.svg">
            </div>
        </div>
        <div class="lower">
            <span>Server Logs</span>
        </div>
    </a>
    <a href="/server/341685098468343822/listing" class="mysetting">
        <div class="upper">
            <div class="img-wrapper">
                <img class="img-icon" src="https://canary.discordapp.com/assets/a77e0fdf1c1dddb8de08f3b67a971bff.svg">
            </div>
        </div>
        <div class="lower">
            <span>Manage Server Listing</span>
        </div>
    </a>
</div>

<br>

<div class="title">Members (5000)</div>
<div class="container">
	<table class="userlist" style="width: 100%">



		"""
		pe = """
			</table>
</div>

</body>
		"""
		stringg = """
<tr>
		<td>
				<img class="upfp" src="%avatar%">
			</td>
			<td>
			<a class="myuser">
				<div class="upper">
					<span>%name%</span>
				</div>
				<div class="lower">
					<div class="roles">
						<p>Roles </p>
						%roles%
					</div>
				</div>
			</a>
			</td>
</tr>"""

		st = ""
		for k in sorted(ctx.guild.members, key=lambda obj: obj.top_role.position, reverse=True):
			s = stringg
			#s = s.replace("%avatar%",(k.avatar_url or k.default_avatar_url).replace("?size=1024","?size=64"))
			s = s.replace("%name%",str(k))
			b = "\n".join(f"<p class=\"role\" style=\"border-color: {m.colour}\">{m.name}</p>" for m in sorted(k.roles, key=lambda item: item.position))
			s = s.replace("%roles%",b)
			st += "\n" + s

		f = io.open("test.html","w")
		f.write(pb + st + pe)
		f.close()
		await ctx.send("Done")

def setup(bot):
	bot.add_cog(Core(bot))