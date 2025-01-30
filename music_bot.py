import os
import discord
from discord.ext import commands
from discord.ui import Button, View
from dotenv import load_dotenv
import yt_dlp as youtube_dl
import asyncio

# Load token dari .env
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

# Inisialisasi bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Konfigurasi yt-dlp
ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Bot telah berhasil masuk sebagai {bot.user}')
    activity = discord.Activity(type=discord.ActivityType.listening, name="!tutorial")
    await bot.change_presence(activity=activity)

@bot.command(name='tutorial', help='Menampilkan tutorial penggunaan MUSIC BOT Y.O.G.A')
async def tutorial(ctx):
    tutorial_embed = discord.Embed(
        title="🎶 **Tutorial Penggunaan MUSIC BOT Y.O.G.A 🎶**",
        description="Berikut adalah cara menggunakan bot ini untuk memutar musik di server Discord kamu. Berikut adalah beberapa perintah utama yang bisa kamu gunakan:",
        color=discord.Color.green()
    )
    tutorial_embed.add_field(name="1️⃣ **Bergabung ke Voice Channel**", value="Gunakan perintah `!gabung` untuk meminta bot bergabung ke voice channel tempat kamu berada.", inline=False)
    tutorial_embed.add_field(name="2️⃣ **Memutar Musik**", value="Gunakan perintah `!mainkan [URL YouTube]` untuk memutar musik dari YouTube. Contoh: `!mainkan https://youtube.com/xyz123`", inline=False)
    tutorial_embed.add_field(name="⏸️ **Jeda Musik**", value="Gunakan perintah `!jeda` untuk menjeda musik yang sedang diputar.", inline=False)
    tutorial_embed.add_field(name="▶️ **Melanjutkan Musik**", value="Gunakan perintah `!lanjutkan` untuk melanjutkan musik yang sudah dijeda.", inline=False)
    tutorial_embed.add_field(name="🛑 **Hentikan Musik**", value="Gunakan perintah `!hentikan` untuk menghentikan pemutaran musik.", inline=False)
    tutorial_embed.add_field(name="🔴 **Keluar Voice Channel**", value="Gunakan perintah `!tinggalkan` untuk meminta bot meninggalkan voice channel.", inline=False)
    tutorial_embed.add_field(name="📌**NOTE**", value="Jika tombol Jeda, Pause, dan Hentikan terjadi kegagalan interaksi, tolong pakai perintah yang sudah disediakan saja🙂", inline=False)
    tutorial_embed.set_footer(text="🎵 **MUSIC BOT Y.O.G.A | Nikmati musiknya!**")

    await ctx.send(embed=tutorial_embed)

@bot.command(name='gabung', help='Meminta bot untuk bergabung ke voice channel')
async def join(ctx):
    if not ctx.message.author.voice:
        await ctx.send("🔴 **Anda harus berada di voice channel untuk menggunakan perintah ini!**")
        return

    channel = ctx.message.author.voice.channel
    if not ctx.voice_client:
        await channel.connect()

        embed = discord.Embed(
            title="🎶 Bot Bergabung ke Voice Channel 🎶",
            description=f"✅ **Bot berhasil bergabung ke voice channel: {channel.name}**",
            color=discord.Color.green()
        )
        embed.add_field(name="📣 **Pemanggil**", value=f"💬 **{ctx.message.author.display_name}**", inline=False)
        embed.set_footer(text="Diperbarui oleh MUSIC BOT Y.O.G.A")

        await ctx.send(embed=embed)
    else:
        await ctx.send("⚠️ **Bot sudah bergabung ke voice channel!**")

@bot.command(name='tinggalkan', help='Meminta bot untuk keluar dari voice channel')
async def leave(ctx):
    if ctx.voice_client:
        channel = ctx.voice_client.channel
        await ctx.voice_client.disconnect()

        embed = discord.Embed(
            title="🎶 Bot Keluar dari Voice Channel 🎶",
            description=f"⚠️ **Bot berhasil keluar dari voice channel: {channel.name}**",
            color=discord.Color.red()
        )
        embed.add_field(name="📣 **Pemanggil**", value=f"💬 **{ctx.message.author.display_name}**", inline=False)
        embed.set_footer(text="Diperbarui oleh MUSIC BOT Y.O.G.A")

        await ctx.send(embed=embed)
    else:
        await ctx.send("🔴 **Bot tidak sedang berada di voice channel.**")

@bot.command(name='mainkan', help='Memutar lagu dari URL YouTube atau nama lagu')
async def play(ctx, *, query):
    async with ctx.typing():
        try:
            if "youtube.com" in query or "youtu.be" in query:
                player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)
            else:
                query = f"ytsearch:{query}"
                player = await YTDLSource.from_url(query, loop=bot.loop, stream=True)

            if ctx.voice_client is None:
                await ctx.author.voice.channel.connect()

            ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(notify_on_end(ctx, e)))

            embed = discord.Embed(
                title="🎶 Sekarang Memutar 🎶",
                description=f"**{player.title}**",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=player.data['thumbnail'])
            embed.add_field(name="🔊 Durasi", value=str(player.data.get('duration', 'Durasi Tidak Diketahui')), inline=True)
            embed.add_field(name="🎤 Artis", value=player.data.get('artist', 'Artis Tidak Diketahui'), inline=True)
            embed.add_field(name="🎧 Pemutar", value=ctx.message.author.display_name, inline=False)
            embed.set_footer(text="Diperbarui oleh MUSIC BOT Y.O.G.A")

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ **Terjadi kesalahan saat memutar lagu:** {e}")

# Fungsi untuk memberi tahu saat lagu selesai
async def notify_on_end(ctx, error):
    if error:
        print(f"Error: {error}")
    
    if hasattr(ctx.bot, 'last_music_message'):
        await ctx.bot.last_music_message.delete()
    
    embed = discord.Embed(
        title="🎵 Lagu Selesai Diputar! 🎶",
        description="✨ Musik telah selesai dimainkan!",
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

@bot.command(name='hentikan', help='Menghentikan pemutaran musik')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        if hasattr(ctx.bot, 'last_music_message'):
            await ctx.bot.last_music_message.delete()
        
        embed = discord.Embed(
            title="🛑 Musik Dihentikan!",
            description="⚠️ Pemutaran musik dihentikan oleh pengguna.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

bot.run(TOKEN)
