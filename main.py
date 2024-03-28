import discord
from discord.ext import commands
import asyncio

import mytoken

from help_cog import help_cog
from music_cog import music_cog

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


bot.remove_command('help')


async def main():
    async with bot:
        await bot.add_cog(help_cog(bot))
        await bot.add_cog(music_cog(bot))
        await bot.start(mytoken.token)

asyncio.run(main())

