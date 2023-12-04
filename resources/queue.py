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

song_queue = {}
now_playing = []

SPOTIFY_CLIENT_ID = "7ccdc6415d4b4596b1df027c18d70d49"
SPOTIFY_CLIENT_SECRET = "0f438af4f9c24fd8833bc8b54c36bc3a"



spot = spotipy.Spotify(auth_manager=spotipy.SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET, redirect_uri="http://localhost:8888/callback", scope="user-read-playback-state,user-modify-playback-state,user-read-currently-playing,streaming,app-remote-control,playlist-read-private,playlist-read-collaborative,playlist-modify-public,playlist-modify-private,user-library-read,user-library-modify,user-read-recently-played,user-top-read,ugc-image-upload,user-follow-read,user-follow-modify,"))

#for youtube playback
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
YDL_OPTIONS = {'format': "bestaudio"}


youtube_urls = ["youtube.com", "youtu.be", "www.youtube.com", "www.youtu.be", "https://youtube.com", "https://yotu.be"]


RequesterBlacklist = {

}



class Song:
    def __init__(self, url, requester):
        self.url = url
        self.requester = requester
    async def add_to_queue(serverid, url, requester):
        if serverid not in song_queue:
            song_queue[serverid] = []
        song_queue[serverid].append({'url': url, 'requester': requester})

    async def get_queue(serverid):
        queue = song_queue[serverid]
        for i in range(len(queue)):
            song = queue[i]['url']
            requester = queue[i]['requester']
            num = i+1
            return song, requester, num
    
    async def get_requester(serverid):
        queue = song_queue[serverid]
        requester = queue[0]['requester']
        return requester
    async def remove_song(serverid, num):
        song_queue[serverid].pop(num-1)
    
    async def move_song(serverid, num, new_pos):
        song_queue[serverid].insert(new_pos-1, song_queue[serverid].pop(num-1))

    async def update_queue(serverid):
        song_queue[serverid].pop(0)

    async def shuffle_queue(serverid):
        random.shuffle(song_queue[serverid])

    async def clear_queue(serverid):
        song_queue[serverid] = []

    async def add_now_playing(serverid, url, requester):
        now_playing[serverid] = {'url': url, 'requester': requester}

    async def clear_now_playing(serverid):
        now_playing[serverid] = {}

    async def get_now_playing(serverid):
        np_song = now_playing['url']
        np_requester = now_playing['requester']
        return np_song, np_requester
    
    async def del_server(serverid):
        del song_queue[serverid]
        del now_playing[serverid]

    async def process(self, ctx: commands.Context, serverid, requester, vc):
        song = song_queue[serverid][0]['url']
        try:
            if str(song).startswith("https://open.spotify.com/playlist/"):
                await Song.update_queue(serverid)
                async for partial in spotify.SpotifyTrack.iterator(query=song):
                    
                    await Song.add_to_queue(serverid, partial, requester=requester)
                    resources.console.console.info(song_queue)
                await Song.process(self, ctx, serverid, requester)
                return
                
            if str(song).startswith("https://open.spotify.com/"):
                await Spotify.play(ctx, serverid)
                return 
            else:
                await Youtube.play(self, ctx, song, serverid, vc)
                return
        except Exception as e:
            # await Song.update_queue(serverid)
            # await Song.process(self, ctx, serverid, requester)
            raise e


    
class Youtube:
    def __init__(self, bot):
        self.song_queue = song_queue


    async def play(self, ctx: commands.Context, track, serverid, vc: Player):
        if not str(track).startswith("https://") or not str(track).startswith("http://"):
            requester = await Song.get_requester(serverid)
            song = await wavelink.YouTubeTrack.search(track, return_first=True)
            await Song.add_now_playing(serverid, song.title, requester)
            vc: Player = ctx.voice_client
            await vc.play(song)
            embed = Embed(title="Now Playing", description=f"{song.title}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"Uploader: {song.author} | Requested by {requester}")
            await ctx.send(embed=embed)
            return
        else:
            song = await Node.get_tracks(self, cls=Player, query=track)
            await Song.add_now_playing(ctx.guild.id, song.title, requester)
            await vc.play(song)
            embed = Embed(title="Now Playing", description=f"{song.title}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"Requested by {requester}")
            await ctx.send(embed=embed)
            return

class Spotify:
    def __init__(self, bot):
        self.song_queue = song_queue

    async def node_connect(self):
            await self.bot.wait_until_ready()
            await NodePool.create_node(bot=self.bot, host="10.0.0.52", port=2096, password="youshallnotpass", spotify_client=spotify.SpotifyClient(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))
            # await NodePool.create_node(bot=self.bot, host="lavalinkinc.ml", port=443, password="incognito",https=True, spotify_client=spotify.SpotifyClient(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET))

    async def play(ctx: commands.Context, serverid):
        vc: Player = ctx.voice_client
        cs= str(song_queue[serverid][0]['url'])
        try:
            print(cs)
            if cs.startswith("https://open.spotify.com/playlist/"):
                track = await spotify.SpotifyTrack.search(query=cs, return_first=True)
                requester = await Song.get_requester(ctx.guild.id)
                await Song.add_now_playing(ctx.guild.id, track.title, requester)
                await vc.play(track)
                embed = Embed(title="Now Playing", description=f"{track.title}", color=nextcord.Color.blurple())
                embed.set_footer(text=f"Requested by {requester}")
                await ctx.send(embed=embed)
            else:
                vc: Player = ctx.voice_client
                print("Spotify Link Detected")
                track = await spotify.SpotifyTrack.search(query=cs, return_first=True)
                requester = await Song.get_requester(ctx.guild.id)
                await Song.add_now_playing(ctx.guild.id, track.title, requester)
                print(f"Attempted to play {track.title}")
                await vc.play(track)
                embed = Embed(title="Now Playing", description=f"{track.title}", color=nextcord.Color.blurple())
                embed.set_footer(text=f"Requested by {requester}")
                await ctx.send(embed=embed)
        except Exception as e:
            raise e
            
