import discord
from discord.ext import commands
import os
class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.help_message = ""
        self.text_channel_list = []
        self.set_message()

    def set_message(self):
        self.help_message = f"""
Команды :
```
{self.bot.command_prefix}help - это меню
{self.bot.command_prefix}q - очередь
{self.bot.command_prefix}p <песня> - играть песню
{self.bot.command_prefix}skip - пропустить песню, которая сейчас играет
{self.bot.command_prefix}clear - очистить очередь
{self.bot.command_prefix}stop - выйти из голосового чата
{self.bot.command_prefix}pause - поставить бота на паузу / продолжить
{self.bot.command_prefix}remove - убирает последнюю песню в очереди
{self.bot.command_prefix}remove <номер> - убирает песню в очереди с выбранным номером 
{self.bot.command_prefix}loop - залупливает (зацикливает) песню, которая сейчас играет
```
"""

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{self.bot.command_prefix}help | music bot"))
        os.remove("tmp.weba")

    @commands.command(name="help", help="Выводит все команды")
    async def help(self, ctx):
        await ctx.send(self.help_message)
