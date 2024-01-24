from __future__ import unicode_literals
import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import os
import time
class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.is_playing = False
        self.is_paused = False
        self.loop = False
        self.current = ""

        # 2d array containing [song, channel]
        self.music_queue = []
        self.YDL_OPTIONS = {'format': 'bestaudio/best',
                            'reconnect': '1',
                            'reconnect_streamed': '1',
                            'reconnect_delay_max': '5',
                            'outtmpl': 'tmp.weba'}
        self.FFMPEG_OPTIONS = {'options': '-vn'}

        self.vc = None
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

    def log(self, text):
        print(f'[log] {text}')
    def search_yt(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=True)["title"]
            return{'source':item, 'title':title}
        search = VideosSearch(item, limit=1)
        print(search.result()["result"][0]["title"], search.result()["result"][0]["link"])
        return{'source':search.result()["result"][0]["link"], 'title':search.result()["result"][0]["title"]}

    async def play_next(self):
        if len(self.music_queue) > 0 or self.loop:
            self.is_playing = True
            if not self.loop or not self.current:
                self.current = self.music_queue.pop(0)
                m_url = self.current[0]['source']
            else:
                m_url = self.current[0]['source']

            if not self.loop or not os.path.exists("tmp.weba"):
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
                song = data['url']
                if os.path.exists("tmp.weba"):
                    os.remove("tmp.weba")
                self.ytdl.download([m_url])
            self.vc.play(discord.FFmpegPCMAudio("tmp.weba", executable= "ffmpeg", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
        else:
            self.is_playing = False
            self.current = ""
            await self.check_leave()

    async def play_music(self, ctx):

        if len(self.music_queue) > 0 or self.loop:
            self.is_playing = True
            if not self.loop or not self.current:
                self.current = self.music_queue.pop(0)
                m_url = self.current[0]['source']
            else:
                m_url = self.current[0]['source']
            if not self.vc or not self.vc.is_connected():
                self.vc = await self.current[1].connect()

                if not self.vc:
                    await ctx.send("```Не могу присоединиться к голосовому каналу```")
                    return
            else:
                await self.vc.move_to(self.current[1])
            if not self.loop or not os.path.exists("tmp.weba"):
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(m_url, download=False))
                song = data['url']
                if os.path.exists("tmp.weba"):
                    os.remove("tmp.weba")
                self.ytdl.download([m_url])
            self.log("playing music")
            self.vc.play(discord.FFmpegPCMAudio("tmp.weba", executable="ffmpeg", **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))

        else:
            self.is_playing = False
            self.current = ""
            await self.check_leave()

    async def check_leave(self):
        # бот выходит, если в войсе никого нет
        members = self.vc.channel.members
        self.log(f'voice members: {len(members)}')
        await asyncio.sleep(10)
        if len(members) == 1:
            await self.vc.disconnect()


    @commands.command(name="play", aliases=["p","P","playing"], help="Играет выбраную песню с youtube.com")
    async def play(self, ctx, *args):
        query = " ".join(args)
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send("```Сначала ты должен присоедениться к голосовому каналу!```")
            return
        if self.is_paused:
            self.vc.resume()
        else:
            song = self.search_yt(query)
            if type(song) == type(True):
                await ctx.send("```Невозможно скачать песню. Некорректный формат. Возможно это прямая трансляция или плейлист```")
            else:
                if self.is_playing:
                    await ctx.send(f"**{len(self.music_queue) + 1} ' {song['title']}'** добавлена в очередь")
                else:
                    await ctx.send(f"**'{song['title']}'** добавлена в очередь")
                self.music_queue.append([song, voice_channel])
                if not self.is_playing:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="Ставит / снимает с паузы песню, которая сейчас играет")
    async def pause(self, ctx, *args):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()
        elif self.is_paused:
            self.is_paused = False
            self.is_playing = True
            self.vc.resume()


    @commands.command(name="skip", aliases=["s"], help="пропускает песню, которая сейчас играет")
    async def skip(self, ctx):
        if self.vc:
            self.vc.stop()
            await self.play_next()



    @commands.command(name="queue", aliases=["q"], help="Выводит песню, которая сейчас играет и очередь")
    async def queue(self, ctx):

        if not self.music_queue and not self.current:
                await ctx.send(f"```Нет музыки в очереди```")

        retval = ""
        if self.loop:
            retval += f"сейчас зациклена: {self.current[0]['title']} \n"
            for i in range(0, len(self.music_queue)):
                retval += f"#{i + 1} - " + self.music_queue[i][0]['title'] + "\n"
        else:
            retval += f"сейчас играет: {self.current[0]['title']} \n"
            for i in range(0, len(self.music_queue)):
                retval += f"#{i + 1} - " + self.music_queue[i][0]['title'] + "\n"
        if retval != "":
            await ctx.send(f"```Очередь:\n{retval}```")

    @commands.command(name="clear", aliases=["c", "bin"], help="Останавливает музыку и очищает очередь")
    async def clear(self, ctx):
        if self.vc != None and self.is_playing:
            self.vc.stop()
        self.music_queue = []
        await ctx.send("```Очередь очищена```")

    @commands.command(name="stop", aliases=["disconnect", "l", "d"], help="Кикает бота из голосового канала")
    async def disconnect(self, ctx):
        self.is_playing = False
        self.is_paused = False
        self.loop = False
        self.current = ""
        self.music_queue = []
        await self.vc.disconnect()
    
    @commands.command(name="remove", help="Убирает последнюю / выбранную песню из очереди")
    async def remove(self, ctx, *args):
        self.music_queue.pop(int(args[0])-1)
        await ctx.send(f"пенся удалена")

    @commands.command(name="loop", help="залупливает (зацикливает) 1 песню")
    async def loop(self, ctx, *args):
        self.loop = not self.loop
        if self.loop:
            self.log("looping on")
            await ctx.send(f"залупливание включено")
        else:
            self.log("looping off")
            await ctx.send(f"залупливание выключено")
