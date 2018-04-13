import discord
from discord.ext import commands
import pylava
import aiohttp
import asyncio
import random
import async_timeout
import time
from bs4 import BeautifulSoup
import re
from config import Bot

from itertools import islice


def str_to_seconds(st):
    a = st.split(":")
    hours = int(a[0])
    minutes = int(a[1])
    seconds = int(a[2])
    return hours * 3600 + minutes*60 + seconds


def seconds_to_str(msec):
    sec = msec//1000
    minutes, seconds = divmod(sec, 60)
    minutes = int(minutes)
    seconds = int(seconds)
    hours, minutes = divmod(minutes, 60)
    hours = int(hours)
    # Create a fancy string
    duration = []
    if hours > 0: duration.append(f'{hours}h')
    if minutes > 0 or hours > 0: duration.append(f'{minutes:02d}m')
    if seconds > 0 or minutes > 0 or hours > 0 or len(duration) == 0: duration.append(f'{seconds:02d}s')
    return ''.join(duration)


def track_to_str(track):
    return f"**{track['info']['title']}** from **{track['info']['author']}** (duration : {seconds_to_str(track['info']['length'])})"


def modup(ctx):
    return ctx.message.channel.permissions_for(ctx.message.author).manage_messages


class MusicError(commands.UserInputError):
    pass


class Playlist(asyncio.Queue):

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return len(self._queue)

    def __getitem__(self, item):
        return self._queue[item]

    def clear(self):
        self._queue.clear()

    def get_song(self):
        return self.get_nowait()

    def reverse(self):
        self._queue.reverse()

    def put_song(self, song):
        self.put_nowait(song)

    def put_on_top(self, song):
        self._queue.appendleft(song)

    def shuffle(self):
        random.shuffle(self._queue)

    def __str__(self):
        fmt = "Current Queue:\n {}"
        s = ""
        for k, song in enumerate(self):
            s += "{}. {}\n".format(str(k+1), str(song))
        return fmt.format(s)


class MusicState:
    def __init__(self, connection, guild):
        self.queue = Playlist(maxsize=100)
        self.loop = asyncio.get_event_loop()
        self.current = None
        self.connection = connection
        self.guild = guild
        self.skips = set()
        self.time = None
        self.ptime = None
        self.channel = None
        self.t = None
        self.requester = None

    async def task(self):
        while self.connection.get_player(self.guild.id).playing:
            await asyncio.sleep(1)
        await self.play_next()

    async def play_next(self, ctx=None, error=None):
        if error:
            await self.channel.send(f"An error has occurred while playing {track_to_str(self.current)}: {error}")
            pass
        self.skips.clear()
        player = self.connection.get_player(self.guild.id)
        if ctx:
            self.channel = ctx.channel
        if self.queue.empty():
            self.current = None
            self.channel = None
            self.time = None
            self.requester = None
        else:
            track = self.queue.get_song()
            self.current = track
            if ctx:
                self.requester = ctx.author
            await self.channel.send(f"Now playing: {track_to_str(track)}")
            await player.play(track["track"])
            self.time = time.time()
            await asyncio.sleep(2)
            self.t = self.loop.create_task(self.task())


class Music:
    """Music player commands
    Powered by Lavalink
    """

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession()
        self.states = {}
        self.connection = pylava.Connection(self.bot, Bot.PASSWORD, Bot.WEBSOCKET, Bot.REST)

    async def __error(self, ctx, error):
        if not isinstance(error, commands.UserInputError):
            raise error

        try:
            await ctx.send(error)
        except discord.Forbidden:
            pass  # /shrug

    def _unload(self):
        for state in self.states.values():
            self.bot.loop.create_task(state.player.disconnect())
        self.bot.loop.create_task(self.connection.disconnect())
        self.session.close()

    async def __before_invoke(self, ctx):
        ctx.music_state = self.states.setdefault(ctx.guild.id, MusicState(self.connection, ctx.guild))

    async def hastebin(self, link, ctx):
        nl = link.split("/")[3]
        nl = "https://hastebin.com/raw/" + nl.split('.')[0]
        with async_timeout.timeout(10):
            async with self.session.get(nl) as response:
                    html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        pl = soup.prettify()
        await ctx.send(f"Got `{len(pl.splitlines())}` songs via hastebin playlist: `{link[21:]}`. "
                       f"\nIt might take some time to load the playlist. please stay patient.")
        first = True
        for url in pl.splitlines():
                a = await self.connection.query(url)
                player = self.connection.get_player(ctx.guild.id)
                track = a[0]
                ctx.music_state.queue.put_song(track)
                if not player.connected:
                    await player.connect(ctx.author.voice.channel.id)
                if first and player.stopped:
                    await ctx.music_state.play_next(ctx=ctx)
                    first = False

    async def wastebin(self, link, ctx):
        nl = link.split("/")[3]
        nl = "https://wastebin.party/raw/" + nl.split('.')[0]
        async with self.session.get(nl) as response:
            html = await response.text()
        soup = BeautifulSoup(html, "html.parser")
        pl = soup.prettify()
        await ctx.send(f"Got `{len(pl.splitlines())}` songs via hastebin playlist: `{link[23:]}`. "
                       f"\nIt might take some time to load the playlist. please stay patient.")
        first = True
        for url in pl.splitlines():
            a = await self.connection.query(url)
            player = self.connection.get_player(ctx.guild.id)
            track = a[0]
            ctx.music_state.queue.put_song(track)
            if not player.connected:
                await player.connect(ctx.author.voice.channel.id)

            if first and player.stopped:
                await ctx.music_state.play_next(ctx=ctx)
                first = False

    @commands.command(no_pm=True)
    @commands.cooldown(1, 1.)
    async def play(self, ctx, *, song: str, no_displaying=False):
        """Plays a song."""
        await self.connection.wait_until_ready()
        player = self.connection.get_player(ctx.guild.id)
        if not player.connected:
            if not ctx.author.voice:
                raise MusicError("You are not connected to a voice channel")
            await player.connect(ctx.author.voice.channel.id)
        if song.startswith("https://hastebin.com/"):
            await self.hastebin(song, ctx)
            return
        if song.startswith("https://wastebin.party/"):
            await self.wastebin(song, ctx)
            return
        if not song.startswith("http"):
            tracks = await player.query("ytsearch:" + song)
            if not tracks:
                raise MusicError("No results were found. :frowning:")
            s = "**Choose a song:**\n[1-5]\n"
            for i in range(5):
                s += f"{i+1}. **{tracks[i]['info']['title']}** from **{tracks[i]['info']['author']}**\n"
            m = await ctx.send(s)
            try:
                mess = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=20.)
            except asyncio.TimeoutError:
                pass
                return
            if mess is not None:
                if "1" in mess.content:
                    i = 0
                elif "2" in mess.content:
                    i = 1
                elif "3" in mess.content:
                    i = 2
                elif "4" in mess.content:
                    i = 3
                elif "5" in mess.content:
                    i = 4
                else:
                    await m.delete()
                    await mess.delete()
                    return
            else:
                return
            await m.delete()
            await mess.delete()
            track = tracks[i]
        else:
            tracks = await player.query(song)
            if not tracks:
                raise MusicError("No results were found. :frowning:")
            track = tracks[0]
        try:
            ctx.music_state.queue.put_song(track)
        except asyncio.QueueFull:
            raise MusicError('Playlist is full, try again later.')
        if player.stopped:
            await ctx.music_state.play_next(ctx=ctx)
        else:
            if not no_displaying:
                await ctx.send(f"Enqueued: {track_to_str(track)}")

    @commands.command(no_pm=True, aliases=["disconnect"])
    async def stop(self, ctx):
        """Stops the player and disconnects."""
        player = self.connection.get_player(ctx.guild.id)
        ctx.music_state.queue.clear()
        if ctx.music_state.t:
            ctx.music_state.t.cancel()
        if not player.stopped:
            await player.stop()
        if player.connected:
            await player.disconnect()
        if ctx.voice_client:
            await ctx.voice_client.disconnect()

    @commands.command(no_pm=True, aliases=["nowplaying", "playing"])
    async def np(self, ctx):
        """Shows info about the currently playing song."""
        p = self.connection.get_player(ctx.guild.id)
        if p.playing:
            track = ctx.music_state.current
            secs = int(time.time() - ctx.music_state.time)
            await ctx.send(f'Now playing: {track_to_str(track)}'
                           f' at {seconds_to_str(secs*1000)}, {seconds_to_str(track["info"]["length"]-secs*1000)} remaining.')
        else:
            await ctx.send(f'Not playing anything.')

    @commands.command(no_pm=True)
    async def pause(self, ctx):
        """Pauses the currently played song."""
        player = self.connection.get_player(ctx.guild.id)
        if not player.paused:
            ctx.music_state.ptime = time.time()
            await player.set_pause(True)

    @commands.command(no_pm=True, aliases=["resume"])
    async def unpause(self, ctx):
        """Pauses the currently played song."""
        player = self.connection.get_player(ctx.guild.id)
        if player.paused:
            ctx.music_state.time = ctx.music_state.time + time.time() - ctx.music_state.ptime
            ctx.music_state.ptime = None
            await player.set_pause(False)

    @commands.command(no_pm=True)
    async def skip(self, ctx):
        """Skip the current playing song."""
        player = self.connection.get_player(ctx.guild.id)
        if not player.playing:
            raise MusicError("Not playing anything.")
        if modup(ctx) or ctx.author == ctx.music_state.requester:
            await player.stop()
        elif ctx.author.id in ctx.music_state.skips:
            raise MusicError("You already voted to skip!")
        else:
            ctx.music_state.skips.add(ctx.author.id)

    @commands.command(no_pm=True)
    @commands.cooldown(1, 2)
    async def seek(self, ctx, ctime: str):
        """Seeks to a certain point in song. (((hh):mm):ss)"""
        player = self.connection.get_player(ctx.guild.id)
        if not player.playing:
            raise MusicError("Not playing anything.")
        p = re.compile(r"([0-9]{2}[:][0-9]{2}[:][0-9]{2})")
        p2 = re.compile(r"([0-9]{2}[:][0-9]{2})")
        p3 = re.compile(r"([0-9]{2})")
        if re.fullmatch(p, ctime):
            ltime = ctime
        elif re.fullmatch(p2, ctime):
            ltime = "00:" + ctime
        elif re.fullmatch(p3, ctime):
            ltime = "00:00:" + ctime
        else:
            await ctx.message.channel.send("Time format is wrong, correct is hh:mm:ss for h = hour, m = minute"
                                           " and s = second")
            return
        csec = time.time()
        secs = str_to_seconds(ltime)
        if not (secs < 0 or secs > ctx.music_state.current["info"]["length"]//1000):
            raise MusicError(f"Out of bounds, please do between 0 to {seconds_to_str(ctx.music_state.current['info']['length']//1000)}")
        ctx.music_state.time = csec - secs
        await player.seek(secs)
        
    @commands.group(no_pm=True)
    async def queue(self, ctx):
        """List of the queue (%help queue for more)"""
        if ctx.invoked_subcommand is None:
            player = self.connection.get_player(ctx.guild.id)
            if player.playing or player.paused:
                if ctx.music_state.queue.empty():
                    raise MusicError("Queue is empty.")
                def cs(page, c):
                    s = ""
                    for k, i in enumerate(page):
                        s += "{}. {}\n".format(str(k+c+1), track_to_str(i))
                    return s
                track = ctx.music_state.current
                pages = []
                right = "\N{BLACK RIGHT-POINTING TRIANGLE}"
                left = "\N{BLACK LEFT-POINTING TRIANGLE}"
                c = 0
                for i in range(0, len(ctx.music_state.queue), 5):
                    pages.append(list(islice(ctx.music_state.queue._queue, i, min(i+5, len(ctx.music_state.queue)))))
                text = f"```Now playing {track_to_str(track)}.\nThere are {len(ctx.music_state.queue)} songs in the queue." + \
                       f" \n{cs(pages[c], c)}```"
                m = await ctx.send(text)
                await m.add_reaction(left)
                await m.add_reaction(right)
                def check(r, u):
                    return r.message.id == m.id and u == ctx.message.author and ((r.emoji == left and not c == 0) or (r.emoji==right and not c==len(pages)-1))
                try:
                    while True:
                        a = await ctx.bot.wait_for('reaction_add', timeout=60.0, check=check)
                        if a[0].emoji == left:
                            c-=5
                        else:
                            c+=5
                        content = f"```Now playing {track_to_str(track)}.\nThere are {len(ctx.music_state.queue)} songs in the queue." + \
                                  f" \n{cs(pages[c//5], c)}```\n\nPage: {c//5+1}"
                        await m.edit(content=content)
                except TimeoutError:
                    return
            else:
                await ctx.send(f'Not playing anything.')

    @queue.command(no_pm=True)
    async def shuffle(self, ctx):
        """Shuffles the queue to randomize order."""
        ctx.music_state.queue.shuffle()
        await ctx.send("Queue shuffled.")

    @queue.command(no_pm=True)
    async def export(self, ctx):
        player = self.connection.get_player(ctx.guild.id)
        if player.playing and not ctx.music_state.queue.empty():
            s = ""
            for t in ctx.music_state.queue:
                s += t["info"]["uri"] + "\n"
            try:
                with async_timeout.timeout(10):
                    async with self.session.post('https://hastebin.com/documents', data=s) as resp:
                        j = await resp.json()
                        await ctx.send("https://hastebin.com/" + j["key"]+".dondish"
                                       "\nYou can play this later via the play command.")
            except Exception:
                with async_timeout.timeout(10):
                    async with self.session.post("https://wastebin.party/documents", data=s) as resp:
                        j = await resp.json()
                        await ctx.send("https://wastebin.party/"+j["key"]+".dondish"
                                       "\nYou can play this later via the play command.")

    @queue.command(no_pm=True)
    async def clear(self, ctx):
        """Clears the current queue (stops after current song)"""
        ctx.music_state.queue.clear()

    @queue.command(no_pm=True)
    async def reverse(self, ctx):
        """Reverses queue"""
        ctx.music_state.queue.reverse()

def setup(bot):
    bot.add_cog(Music(bot))
