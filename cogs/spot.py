from re import A
import nextcord
from nextcord.ext import commands
from nextcord.ext.commands import Bot, Cog, Context, command, has_permissions
from nextcord import ApplicationInvokeError, Embed, Interaction
import asyncio
import youtube_dl
import wavelink
from wavelink import Node, Player, NodePool
from wavelink.ext import spotify
import random
import resources.console
import spotipy 

from resources.queue import *
        
        

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @command(aliases=["j"])
    async def join(self, ctx: commands.Context):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(ctx.author.voice.channel)
        await ctx.author.voice.channel.connect(cls=Player)
        vc: Player=ctx.voice_client
        x = 0
        while not vc.is_playing():
            await asyncio.sleep(10)
            await vc.disconnect()
            await ctx.send("disconnected due to inactivity")
            break
    @command(aliases=["l"])
    async def leave(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client
        await vc.disconnect()

    @commands.command(aliases=["p"])
    async def play(self, ctx: commands.Context, *, url):
        resp = ["now go reflect on your actions", "you feel like a dumb ass dont you?", "go home"]
        if ctx.author.id in RequesterBlacklist:
            await ctx.send(f"You've been blacklisted from using the music commands. {random.choice(resp)}")
        if ctx.guild.voice_client is None:
            await ctx.author.voice.channel.connect(cls=Player)
        vc: Player=ctx.guild.voice_client
        if not ctx.author.discriminator == "0":
            author = f"{ctx.author.name}#{ctx.author.discriminator}"
            pass
        else:
            author = ctx.author.name
        try:
            if not vc.is_playing():
                q = await wavelink.YouTubeTrack.search(url, return_first=True)
                await vc.play(q)
                return
            else:
                await vc.queue.put_wait(url)
                embed = Embed(description=f"Added {url} to the queue", color=nextcord.Color.green())
                await ctx.send(embed=embed)
                now_playing.append(ctx.author.name)
                return
        except AttributeError:
            if not vc.is_playing():
                await Song.add_to_queue(ctx.author.guild.id, url, f"{ctx.author.name}#{ctx.author.discriminator}")
                await Song.process(self, ctx, ctx.author.guild.id, author, vc)
                return
        
        while not vc.is_playing():
            await asyncio.sleep(10)
            await vc.disconnect()
            await ctx.send("disconnected due to inactivity")
    #if the user doesnt send a link send error message
    @play.error
    async def play_error(self, ctx: commands.Context, error):
        if isinstance(error, IndexError):
            await ctx.send("Please send a link to a song")
    
    @commands.command()
    async def pause(self, ctx: commands.Context):
        resp = ["now go reflect on your actions", "you feel like a dumb ass dont you?", "go home"]
        if ctx.author.id in RequesterBlacklist:
            await ctx.send(f"You've been blacklisted from using the music commands. {random.choice(resp)}")
        vc: wavelink.Player=ctx.voice_client
        await vc.pause()
        await ctx.send("Music paused")
    
    @commands.command()
    async def resume(self, ctx: commands.Context):
        resp = ["now go reflect on your actions", "you feel like a dumb ass dont you?", "go home"]
        if ctx.author.id in RequesterBlacklist:
            await ctx.send(f"You've been blacklisted from using the music commands. {random.choice(resp)}")
        vc: wavelink.Player=ctx.voice_client
        await vc.resume()
        await ctx.send("Music resumed")


    @commands.command(aliases=["stop"])
    async def skip(self, ctx: commands.Context):
        resp = ["now go reflect on your actions", "you feel like a dumb ass dont you?", "go home"]
        if ctx.author.id in RequesterBlacklist:
          return await ctx.send(f"You've been blacklisted from using the music commands. {random.choice(resp)}")
        vc: wavelink.Player=ctx.voice_client
        if ctx.author.id == ctx.guild.owner_id or commands.has_permissions(move_members=True):
            embed = Embed(title="Dictatorship!", description="skipped. next song please!")
            await ctx.reply(embed=embed)
            await vc.stop()
            return
        skip_count = int(len(ctx.author.voice.channel.members)/2)
        if skip_count < 1: skip_count == 1
        if len(ctx.author.voice.channel.members) == 1:
            vc: wavelink.Player=ctx.voice_client
            await vc.stop()
            embed = Embed(description=f"Skipped", color=nextcord.Color.red())
            await ctx.send(embed=embed)
            return
        if skip_count == 1: 
            vc: wavelink.Player=ctx.voice_client
            await vc.stop()
            embed = Embed(description=f"Skipped", color=nextcord.Color.red())
            await ctx.send(embed=embed)
            return
        embed = Embed(title="democracy", description=f"In order to skip, we gotta have a vote. {skip_count} votes of yes is needed to skip")
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("👍")
        try:
            def check():
                return str(reaction.emoji) == "👍" and reaction.message.id == msg.id and reaction.user_id != self.bot.user.id and reaction.user_id in ctx.author.voice.channel.members
            reaction = await self.bot.wait_for("reaction_add", timeout=90, check=check)
        except asyncio.TimeoutError:
            return
        if len(reaction[0]) >= skip_count:
            vc: wavelink.Player=ctx.voice_client
            await vc.stop()
            embed = Embed(description=f"Skipped", color=nextcord.Color.red())
            await ctx.send(embed=embed)
            return
        
        


    @commands.command()
    async def progress(self, ctx: commands.Context):
        vc: wavelink.Player=ctx.voice_client
        await ctx.send(f"Position: {vc.position} / {vc.track.duration}")
    
    @commands.command(aliases=["q"])
    async def queue(self, ctx: commands.Context):
        try:
            vc: wavelink.Player=ctx.guild.voice_client
            song_count = 0
            np_count = 0
            songs = []
            queue = vc.queue.copy()

            embed = Embed(title="Queue", description=f"Upcoming Songs", color=nextcord.Color.blurple())
            for song in queue:
                song_count += 1
                np_count += 1
                songs.append(song)
                embed.add_field(name=f"{song_count}. {song}", value=f"Requested by {now_playing[np_count]}", inline=False)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Queue", description="The queue is empty. use `-p` to play a song", color=nextcord.Color.red())
            await ctx.send(embed=embed)
            return
    @commands.command(aliases=['queue clear'])
    async def qclear(self, ctx: commands.Context):
        await Song.clear_queue(ctx.author.guild.id)
        await ctx.send("Queue cleared")

    @commands.command()
    async def loop(self, ctx: commands.Context): vc: wavelink.Player=ctx.voice_client; source = vc.source; source.loop = True; await ctx.send("Looping song")
    @commands.command()
    async def remove(self, ctx: commands.Context, *, number):
        if len(song_queue) == 0:
            await ctx.send("i can't remove NOTHING")
            return
        if number == "all":
            await Song.clear_queue(ctx.author.guild.id)
            await ctx.send("Queue cleared")
            return
        try:
            number = int(number)
        except ValueError:
            await ctx.send("Please enter a valid number")
            return
        if number > len(song_queue[ctx.author.guild.id]):
            await ctx.send("Please enter a valid number")
            return
        await Song.remove_song(ctx.author.guild.id, number)
        await ctx.send(f"Removed song {number} from queue")
    @commands.command()
    async def np(self, ctx: commands.Context):
        np_song, np_requester = await Song.get_now_playing(ctx.author.guild.id)
        embed = Embed(title="Now Playing", description=f"{np_song}", color=nextcord.Color.blurple())
        embed.set_footer(text=f"Requested by {np_requester}")
        await ctx.send(embed=embed)
    @commands.command()
    async def shuffle(self, ctx: commands.Context):
        if len(song_queue) == 0:
            await ctx.send("i can't shuffle NOTHING")
            return
        Song.shuffle_queue()
        embed = Embed(description=f"Shuffled the queue", color=nextcord.Color.dark_purple())
        await ctx.send(embed=embed)

    @commands.command()
    async def volume(self, ctx: commands.Context, volume: int):
        vc: wavelink.Player = ctx.voice_client
        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")
        vc.volume = volume / 100
        await ctx.send(f"Changed volume to {volume}%")
    
    @commands.command()
    async def move(self, ctx: commands.Context, pos1, pos2):
        if len(song_queue) == 0:
            await ctx.send("i can't move NOTHING ")
            return
        try:
            pos1 = int(pos1)
            pos2 = int(pos2)
        except ValueError:
            await ctx.send("Please enter a valid number")
            return
        if pos1 > len(song_queue[ctx.author.guild.id]) or pos2 > len(song_queue[ctx.author.guild.id]):
            await ctx.send("Please enter a valid number")
            return
        await Song.move_song(ctx.author.guild.id, pos1, pos2)
        await ctx.send(f"Moved Song {pos1} to {pos2}")
    
    @commands.command(name="Now_Playing", Aliases=["np"])
    async def now_playing(self, ctx: commands.Context):
        np, np_requester = await Song.get_now_playing(ctx.author.guild.id)
        embed = Embed(title="Now Playing", description=f"{np[0]}", color=nextcord.Color.blurple())
        embed.set_footer(text=f"Requested by {np_requester[0]}")
        await ctx.send(embed=embed)

    @commands.command(aliases=["fp"])
    async def fplay(self, ctx: commands.Context, *, url):
        track = await wavelink.YouTubeTrack.search(url, return_first=True)
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect(cls=Player)
        if ctx.author.voice.channel == None:
            await ctx.send("You are not in a voice channel.")
            return
        if ctx.author.voice.channel != ctx.voice_client.channel:
            await ctx.send("You are not in the same voice channel as the bot.")
            return
        vc: wavelink.Player = ctx.voice_client
        await vc.play(track)
        embed = Embed(title="Now Playing", description=track.title)
        embed.set_footer(text=f"Requested by: {ctx.author.name}#{ctx.author.discriminator}")
        await ctx.send(embed=embed)
        print(url)
    @command(aliases=["fs"])
    async def fskip(self, ctx: commands.Context):
        vc: wavelink.Player=ctx.voice_client
        await vc.stop()
        embed = Embed(description=f"Skipped", color=nextcord.Color.red())
        await ctx.send(embed=embed)
        return
    @commands.command()
    async def no(self, ctx: commands.Context):
        vc: wavelink.Player = ctx.voice_client        
        print(vc.nodes[0])
        print(vc.current_node)

    @commands.command()
    async def splay(self, ctx: commands.Context, *, query: str):
        if ctx.voice_client is None:
            await ctx.author.voice.channel.connect(cls=Player)
        vc: wavelink.Player = ctx.voice_client
        try:
            if not query.startswith("https://open.spotify.com/"):
                song = spot.search(query, limit=1, type="track")["tracks"]["items"][0]["uri"]
                track = await spotify.SpotifyTrack.search(query=f"{song} audio", return_first=True)
                await vc.play(track)
                embed = Embed(title="Now Playing", description=f" {track.author} - {track.title}", color=nextcord.Color.blurple())
                embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=embed)
            else:
                track = await spotify.SpotifyTrack.search(query=f"{query} audio", return_first=True)
                await vc.play(track)
                embed = Embed(title="Now Playing", description=f"{track.author} - {track.title}", color=nextcord.Color.blurple())
                embed.set_footer(text=f"Requested by {ctx.author}")
                await ctx.send(embed=embed)
        except Exception as e:
            raise e
        print(query)

    @Cog.listener()
    async def on_ready(self):
        self.bot.loop.create_task(Spotify.node_connect(self))
    @Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        print(f"Node {node.identifier} is ready.")
    @Cog.listener()
    async def on_wavelink_node_connect(self, node: wavelink.Node):
        print(f"Node {node.identifier} is connected.")
    # @Cog.listener()
    # async def on_wavelink_track_start(self, player: Player, track: wavelink.Track):
    #     vc: wavelink.Player = player
    #     await asyncio.sleep(3)
    #     await Song.update_queue(vc.guild.id)
    @Cog.listener()
    async def on_wavelink_track_end(self, player: wavelink.Player, track: wavelink.Track, reason):
        vc: wavelink.Player = player
        ctx=commands.Context
        try: 
            if len(song_queue) == 0:
                titles=["That's all folks", "Show's over folks", "fin", "*crickets*", "i got nothing folks"]
                embed = Embed(title=random.choice(titles), description="The queue has finished playing", color=nextcord.Color.red())
                await ctx.send(embed=embed)
                return
            # if str(song_queue[0]).startswith("https://www.youtube.com/") or str(song_queue[0]).startswith("https://www.youtu.be/"):
            #     await Youtube.play(ctx)
            # elif str(song_queue[0]).startswith("https://open.spotify.com/"):
            #     await Spotify.play(ctx)
            # else:
            #     await Spotify.play(ctx)
            # if str(song_queue[0]).startswith("https://open.spotify.com/"): await Spotify.plate(ctx=commands.Context)
            # else: await Youtube.play(ctx=commands.Context)
            requester = await Song.get_requester(vc.guild.id)

            await Song.process(self, ctx=Context, serverid=vc.guild.id, requester=requester, vc=vc)
            await Song.clear_now_playing(vc.guild.id)
            await asyncio.sleep(3)
            if len(song_queue[vc.guild.id]) == 0:
                await Song.del_server(vc.guild.id)
                return 
            print("Track ended")
        except IndexError:
            pass


    

    
def setup(bot):
    bot.add_cog(Music(bot))




