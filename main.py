import discord
from discord.ext import commands
import asyncio

import mytoken

from help_cog import HelpCog
from music_cog import MusicCog
from test_cog import test_cog

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


bot.remove_command('help')


async def main():
    async with bot:
        await bot.add_cog(HelpCog(bot))
        await bot.add_cog(MusicCog(bot))
        await bot.start(mytoken.token)

asyncio.run(main())
