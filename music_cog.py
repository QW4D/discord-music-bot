from __future__ import unicode_literals
import discord
from discord.ext import commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import os


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.channel = {}

        self.YDL_OPTIONS = {'format': 'bestaudio/best',
                            'reconnect': 1,
                            'reconnect_streamed': 1,
                            'reconnect_delay_max': 5}
        self.FFMPEG_OPTIONS = {'options': '-vn'}
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)

    @staticmethod
    def log(text):
        print(f'[log] {text}')

    def search_yt(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=False)["title"]
            return{'source': item, 'title': title}
        search = VideosSearch(item, limit=1)
        print(search.result()["result"][0]["title"], search.result()["result"][0]["link"])
        return{'source': search.result()["result"][0]["link"], 'title': search.result()["result"][0]["title"]}

    async def play_next(self, vcid):
        self.log("play_next")
        await asyncio.sleep(0.5)
        self.channel[vcid].vc.stop()
        if len(self.channel[vcid].music_queue) > 0 or self.channel[vcid].loop:
            self.channel[vcid].is_playing = True

            m_url = await self.get_song(vcid)
            await self.check_leave(vcid)
            await self.play_song(m_url, vcid)
        else:
            self.channel[vcid].is_playing = False
            self.channel[vcid].current = ""

    async def play_music(self, ctx):
        vcid = ctx.author.voice.channel.id
        if len(self.channel[vcid].music_queue) > 0 or self.channel[vcid].loop:
            self.channel[vcid].is_playing = True

            m_url = await self.get_song(vcid)
            await self.connect_vc(ctx)
            await self.check_leave(vcid)
            await self.play_song(m_url, vcid)
        else:
            self.channel[vcid].is_playing = False
            self.channel[vcid].current = ""

    async def get_song(self, vcid):
        if not self.channel[vcid].loop or not self.channel[vcid].current:
            self.channel[vcid].current = self.channel[vcid].music_queue.pop(0)
        m_url = self.channel[vcid].current[0]['source']
        return m_url

    async def play_song(self, m_url, vcid):
        if not self.channel[vcid].loop or not os.path.exists(f"tmp/{vcid}.weba"):
            await self.download_song(m_url, vcid)

        self.log("playing music")
        #loop.run_until_complete(self.channel[vcid].vc.play(discord.FFmpegPCMAudio(f"tmp/{vcid}.weba", executable="ffmpeg", **self.FFMPEG_OPTIONS)))
        #await self.play_next(vcid)
        self.channel[vcid].vc.play(discord.FFmpegPCMAudio(f"tmp/{vcid}.weba", executable="ffmpeg", **self.FFMPEG_OPTIONS),
                                   after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(vcid), self.bot.loop))


    async def download_song(self, m_url, vcid):
        loop = asyncio.get_event_loop()
        if os.path.exists(f"tmp/{vcid}.weba"):
            os.remove(f"tmp/{vcid}.weba")
        opts = self.YDL_OPTIONS
        opts["outtmpl"] = f"tmp/{vcid}.weba"
        ytdl = YoutubeDL(opts)
        await loop.run_in_executor(None, lambda: ytdl.download(m_url))
        self.log(m_url)

    async def connect_vc(self, ctx):
        vcid = ctx.author.voice.channel.id
        if not self.channel[vcid].vc or not self.channel[vcid].vc.is_connected():
            self.channel[vcid].vc = await self.channel[vcid].current[1].connect()

            if not self.channel[vcid].vc:
                await ctx.send("```Не могу присоединиться к голосовому каналу```")
                return
        else:
            await self.channel[vcid].vc.move_to(self.channel[vcid].current[1])

    @commands.Cog.listener()
    async def on_voice_state_update(self, _member, before, _after):
        vcid = before.channel.id
        await self.check_leave(vcid)

    async def check_leave(self, vcid):
        if len(self.channel[vcid].vc.channel.members) == 1:
            await self.stop(vcid)
        pass

    @commands.command(name="play", aliases=["p", "P", "playing"], help="Играет выбраную песню с youtube")
    async def play(self, ctx, *args):
        vcid = ctx.author.voice.channel.id
        query = " ".join(args)
        if vcid not in self.channel:
            self.channel[vcid] = Channel()
        try:
            voice_channel = ctx.author.voice.channel
        except:
            await ctx.send("```Сначала ты должен присоедениться к голосовому каналу!```")
            return
        if self.channel[vcid].is_paused:
            self.channel[vcid].vc.resume()
        else:
            song = self.search_yt(query)
            if isinstance(song, bool):
                await ctx.send("```Невозможно скачать песню. Некорректный формат. Возможно это прямая трансляция или плейлист```")
            else:
                if self.channel[vcid].is_playing:
                    await ctx.send(f"**{len(self.channel[vcid].music_queue) + 1} ' {song['title']}'** добавлена в очередь")
                else:
                    await ctx.send(f"**'{song['title']}'** добавлена в очередь")
                self.channel[vcid].music_queue.append([song, voice_channel])
                if not self.channel[vcid].is_playing:
                    await self.play_music(ctx)

    @commands.command(name="pause", help="Ставит / снимает с паузы песню, которая сейчас играет")
    async def pause(self, ctx):
        vcid = ctx.author.voice.channel.id
        if self.channel[vcid].is_playing:
            self.channel[vcid].is_playing = False
            self.channel[vcid].is_paused = True
            self.channel[vcid].vc.pause()
        elif self.channel[vcid].is_paused:
            self.channel[vcid].is_paused = False
            self.channel[vcid].is_playing = True
            self.channel[vcid].vc.resume()

    @commands.command(name="skip", aliases=["s"], help="пропускает песню, которая сейчас играет")
    async def skip(self, ctx):
        vcid = ctx.author.voice.channel.id
        if self.channel[vcid].vc:
            self.channel[vcid].vc.stop()
            await self.play_next(vcid)

    @commands.command(name="queue", aliases=["q"], help="Выводит песню, которая сейчас играет и очередь")
    async def queue(self, ctx):
        vcid = ctx.author.voice.channel.id
        if not self.channel[vcid].music_queue and not self.channel[vcid].current:
            await ctx.send(f"```Нет музыки в очереди```")

        retval = ""
        if self.channel[vcid].loop:
            retval += f"сейчас зациклена: {self.channel[vcid].current[0]['title']} \n"
        else:
            retval += f"сейчас играет: {self.channel[vcid].current[0]['title']} \n"
        for i in range(0, len(self.channel[vcid].music_queue)):
            retval += f"#{i + 1} - " + self.channel[vcid].music_queue[i][0]['title'] + "\n"
        if retval != "":
            await ctx.send(f"```Очередь:\n{retval}```")

    @commands.command(name="clear", aliases=["c", "bin"], help="Останавливает музыку и очищает очередь")
    async def clear(self, ctx):
        vcid = ctx.author.voice.channel.id
        if self.channel[vcid].vc is not None and self.channel[vcid].is_playing:
            self.channel[vcid].vc.stop()
        self.channel[vcid].is_playing = False
        self.channel[vcid].is_paused = False
        self.channel[vcid].loop = False
        self.channel[vcid].current = ""
        self.channel[vcid].music_queue = []
        await ctx.send("```Очередь очищена```")

    @commands.command(name="stop", aliases=["disconnect", "l", "d"], help="Кикает бота из голосового канала")
    async def disconnect(self, ctx):
        vcid = ctx.author.voice.channel.id
        await self.stop(vcid)

    async def stop(self, vcid):
        self.channel[vcid].is_playing = False
        self.channel[vcid].is_paused = False
        self.channel[vcid].loop = False
        self.channel[vcid].current = ""
        self.channel[vcid].music_queue = []
        await self.channel[vcid].vc.disconnect()
    
    @commands.command(name="remove", aliases=["r"], help="Убирает выбранную песню из очереди")
    async def remove(self, ctx, *args):
        vcid = ctx.author.voice.channel.id
        if args[0]:
            self.channel[vcid].music_queue.pop(int(args[0])-1)
        await ctx.send(f"пенся удалена")

    @commands.command(name="loop", help="залупливает (зацикливает) 1 песню")
    async def loop(self, ctx):
        self.log(123)
        vcid = ctx.author.voice.channel.id
        self.channel[vcid].loop = not self.channel[vcid].loop
        if self.channel[vcid].loop:
            self.log("looping on")
            await ctx.send("залупливание включено")
        else:
            self.log("looping off")
            await ctx.send("залупливание выключено")

class Channel:
    def __init__(self):
        self.is_playing = False
        self.is_paused = False
        self.loop = False
        self.current = ""

        self.music_queue = []
        self.vc = None
