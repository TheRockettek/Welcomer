import asyncio, random

CustomMessages = dict()

CustomMessages['349893105543151616'] = dict()
file_content = open('349893105543151616.custom')
file_content = file_content.readlines()
for lines in file_content[0:]:
    CustomMessages['349893105543151616'][len(CustomMessages['349893105543151616'])] = lines

class CustomStuff():

    def __init__(self,bot):
        self.bot = bot

    @asyncio.coroutine
    async def on_member_join(self,member):
        if member.guild.id == "349893105543151616":
            message = random.randint(1,len(CustomMessages['349893105543151616']))
            message = CustomMessages['349893105543151616'][message]
            message = message.replace("%","<@" + member.id + ">")
            await self.bot.send_message(self.bot.get_channel(self.bot.cache['guild_info'][member.guild.id]['content']['welcomer']['channel']),message)

def setup(bot):
    bot.add_cog(CustomStuff(bot))