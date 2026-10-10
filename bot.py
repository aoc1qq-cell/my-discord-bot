import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
import yt_dlp

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

bot = MyBot()

# --- إعدادات yt-dlp و FFmpeg ---
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
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

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

# 🛠️ أمر يدوي لمزامنة وتثبيت الأوامر فوراً مجرب ومضمون
@bot.command(name="sync")
async def sync_commands(ctx):
    # مسح الأوامر العامة القديمة
    bot.tree.clear_commands(guild=None)
    await bot.tree.sync(guild=None)
    
    # نسخ ومزامنة الأوامر لسيرفرك المباشر
    bot.tree.copy_global_to(guild=ctx.guild)
    synced = await bot.tree.sync(guild=ctx.guild)
    
    await ctx.send(f"✅ تم مسح التكرارات وإعادة مزامنة {len(synced)} أمر في السيرفر بنجاح! جرب الكوماندات الآن.")

# --- نظام سجلات دخول وخروج الأعضاء ---
@bot.event
async def on_member_join(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(title="📥 دخول عضو جديد", description=f"دخول {member.mention}!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(title="📤 مغادرة عضو", description=f"عضو غادر السيرفر: **{member.name}**", color=discord.Color.red())
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

# --- تتبع الأحداث الصوتية ---
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if not log_channel:
        return

    if before.mute != after.mute:
        await asyncio.sleep(0.5)
        admin = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_update):
                if entry.target.id == member.id:
                    admin = entry.user
                    break
        except Exception:
            pass

        admin_mention = admin.mention if admin else "مشرف"
        room_name = after.channel.name if after.channel else "غير معروف"

        if after.mute:
            embed = discord.Embed(title="🎙️ إعطاء ميوت صوتي (Server Mute)", description=f"👤 **العضو:** {member.mention}\n🛡️ **بواسطة المشرف:** {admin_mention}\n🔊 **في روم:** **{room_name}**", color=discord.Color.red())
        else:
            embed = discord.Embed(title="🎙️ فك الميوت الصوتي (Server Unmute)", description=f"👤 **العضو:** {member.mention}\n🛡️ **بواسطة المشرف:** {admin_mention}", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)
        return

    if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        embed = discord.Embed(title="🔄 انتقال بين الرومات الصوتية", description=f"انتقل {member.mention} من روم **{before.channel.name}** إلى روم **{after.channel.name}**", color=discord.Color.purple())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    elif before.channel is None and after.channel is not None:
        embed = discord.Embed(title="🔊 دخول إلى روم صوتية", description=f"دخل {member.mention} إلى روم **{after.channel.name}**", color=discord.Color.blue())
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    elif before.channel is not None and after.channel is None:
        await asyncio.sleep(1.5)
        kicker = None
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                if entry.target.id == member.id:
                    if (discord.utils.utcnow() - entry.created_at).total_seconds() < 10:
                        kicker = entry.user
                        break
        except Exception:
            pass

        if kicker and kicker.id != member.id:
            embed = discord.Embed(title="🚫 طرد من روم صوتية (Disconnect)", description=f"👤 **الشخص المطرود:** {member.mention}\n🛡️ **طُرِد بواسطة المشرف:** {kicker.mention}\n🔊 **من روم:** **{before.channel.name}**", color=discord.Color.red())
        else:
            embed = discord.Embed(title="🔇 خروج من روم صوتية", description=f"خرج {member.mention} من روم **{before.channel.name}**", color=discord.Color.orange())

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

# --- أوامر السلاش ---
@bot.tree.command(name="marhaba", description="يرد عليك البوت لتحييدك")
async def marhaba(interaction: discord.Interaction):
    if interaction.channel.name != 'chat-bot':
        await interaction.response.send_message("⚠️ يرجى استخدام الأوامر في روم #chat-bot!", ephemeral=True)
        return
    await interaction.response.send_message("أهلاً بك! بوتك يعمل بنجاح 🚀")

@bot.tree.command(name="play", description="تشغيل مقطع صوتي من رابط فيديو في القناة الصوتية")
async def play(interaction: discord.Interaction, url: str):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ يجب أن تكون متواجداً داخل قناة صوتية أولاً!", ephemeral=True)
        return

    await interaction.response.defer(thinking=True)

    voice_client = interaction.guild.voice_client
    if not voice_client:
        try:
            voice_client = await interaction.user.voice.channel.connect(timeout=10.0, reconnect=True)
        except Exception as e:
            await interaction.followup.send(f"❌ تعذر الانضمام لقناة الصوت: {e}")
            return

    try:
        loop = asyncio.get_running_loop()
        def extract():
            with yt_dlp.YoutubeDL(YTDL_OPTIONS) as ydl:
                return ydl.extract_info(url, download=False)

        data = await loop.run_in_executor(None, extract)

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url']
        title = data.get('title', 'مقطع صوتي')

        if voice_client.is_playing():
            voice_client.stop()

        audio_source = discord.FFmpegPCMAudio(filename, **FFMPEG_OPTIONS)
        voice_client.play(audio_source)

        await interaction.followup.send(f"🎶 جاري تشغيل: **{title}**")

    except Exception as e:
        print(f"Play Error: {e}")
        await interaction.followup.send(f"⚠️ حدث خطأ أثناء جلب الرابط أو تشغيل الصوت.")

@bot.tree.command(name="stop", description="إيقاف تشغيل الصوت والخروج من القناة الصوتية")
async def stop(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    if voice_client and voice_client.is_connected():
        await voice_client.disconnect()
        await interaction.response.send_message("👋 تم إيقاف الصوت والخروج من القناة الصوتية.")
    else:
        await interaction.response.send_message("❌ البوت غير متصل بأي قناة صوتية حالياً.", ephemeral=True)

bot.run(os.getenv("TOKEN"))
