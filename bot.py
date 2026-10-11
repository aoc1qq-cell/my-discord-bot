import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands
import edge_tts
from google import genai

# قراءة المفاتيح بأمان من متغيرات البيئة (Railway / .env)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("TOKEN")

# التحقق من وجود المفاتيح
if not GEMINI_API_KEY:
  print("⚠️ تحذير: مفتاح GEMINI_API_KEY غير موجود في متغيرات البيئة!")
if not DISCORD_TOKEN:
  print("⚠️ تحذير: توكن TOKEN غير موجود في متغيرات البيئة!")

# إعداد عميل الذكاء الاصطناعي
ai_client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True


class MyBot(commands.Bot):

  def __init__(self):
    super().__init__(command_prefix="!", intents=intents)

  async def setup_hook(self):
    await self.tree.sync()
    print("تم مزامنة أوامر السلاش بنجاح!")


bot = MyBot()


@bot.event
async def on_ready():
  print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")


# --- نظام سجلات دخول وخروج الأعضاء من السيرفر ---
@bot.event
async def on_member_join(member):
  log_channel = discord.utils.get(member.guild.text_channels, name="logs")
  if log_channel:
    embed = discord.Embed(
        title="📥 دخول عضو جديد",
        description=f"دخول {member.mention}!",
        color=discord.Color.green(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Masorh Group • {member.guild.name}")
    await log_channel.send(embed=embed)


@bot.event
async def on_member_remove(member):
  log_channel = discord.utils.get(member.guild.text_channels, name="logs")
  if log_channel:
    embed = discord.Embed(
        title="📤 مغادرة عضو",
        description=f"عضو غادر السيرفر: **{member.name}**",
        color=discord.Color.red(),
    )
    embed.set_footer(text=f"Masorh Group • {member.guild.name}")
    await log_channel.send(embed=embed)


# --- تتبع جميع أحداث الصوت (دخول، خروج، طرد، إلخ) ---
@bot.event
async def on_voice_state_update(member, before, after):
  log_channel = discord.utils.get(member.guild.text_channels, name="logs")
  if not log_channel:
    return

  # 1. حالة الميوت الصوتي
  if before.mute != after.mute:
    await asyncio.sleep(0.5)
    admin = None
    try:
      async for entry in member.guild.audit_logs(
          limit=3, action=discord.AuditLogAction.member_update
      ):
        if entry.target.id == member.id:
          admin = entry.user
          break
    except Exception:
      pass

    admin_mention = admin.mention if admin else "مشرف"
    room_name = after.channel.name if after.channel else "غير معروف"

    if after.mute:
      embed = discord.Embed(
          title="🎙️ إعطاء ميوت صوتي (Server Mute)",
          description=(
              f"👤 **العضو:** {member.mention}\n🛡️ **بواسطة المشرف:"
              f"** {admin_mention}\n🔊 **في روم:** **{room_name}**"
          ),
          color=discord.Color.red(),
      )
    else:
      embed = discord.Embed(
          title="🎙️ فك الميوت الصوتي (Server Unmute)",
          description=(
              f"👤 **العضو:** {member.mention}\n🛡️ **بواسطة المشرف:**"
              f" {admin_mention}"
          ),
          color=discord.Color.green(),
      )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Masorh Group • {member.guild.name}")
    await log_channel.send(embed=embed)
    return

  # 2. الانتقال بين الرومات
  if (
      before.channel is not None
      and after.channel is not None
      and before.channel.id != after.channel.id
  ):
    embed = discord.Embed(
        title="🔄 انتقال بين الرومات الصوتية",
        description=(
            f"انتقل {member.mention} من روم **{before.channel.name}** إلى روم"
            f" **{after.channel.name}**"
        ),
        color=discord.Color.purple(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Masorh Group • {member.guild.name}")
    await log_channel.send(embed=embed)

  # 3. دخول روم صوتية
  elif before.channel is None and after.channel is not None:
    embed = discord.Embed(
        title="🔊 دخول إلى روم صوتية",
        description=f"دخل {member.mention} إلى روم **{after.channel.name}**",
        color=discord.Color.blue(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Masorh Group • {member.guild.name}")
    await log_channel.send(embed=embed)

  # 4. خروج من روم صوتية
  elif before.channel is not None and after.channel is None:
    embed = discord.Embed(
        title="🔇 خروج من روم صوتية",
        description=f"خرج {member.mention} من روم **{before.channel.name}**",
        color=discord.Color.orange(),
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_footer(text=f"Masorh Group • {member.guild.name}")
    await log_channel.send(embed=embed)


# --- أوامر الذكاء الاصطناعي والصوت (السوالف) ---


@bot.command()
async def join(ctx):
  if ctx.author.voice:
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.send("أهلاً! دخلت الروم الصوتي وجاهز أدردش معكم 🎙️")
  else:
    await ctx.send("لازم تكون داخل روم صوتي عشان أقدر أدخل عندك!")


@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send("تم الخروج من الروم الصوتي.")


@bot.command()
async def ask(ctx, *, prompt: str):
  vc = ctx.voice_client
  if not vc or not vc.is_connected():
    await ctx.send("ادخلني الروم الصوتي أولاً باستخدام `!join`")
    return

  # توجيه الذكاء الاصطناعي للرد بأسلوب محادثة شفهية وسريعة
  system_instruction = (
      "أنت صديق يسولف في روم صوتي، أجب بأسلوب عربي عامي لطيف ومختصر جداً بدون"
      " رموز أو تشكيل أو تنسيقات نصوص."
  )

  response = ai_client.models.generate_content(
      model="gemini-2.5-flash",
      contents=f"{system_instruction}\nالمستخدم يقول: {prompt}",
  )
  ai_reply = response.text

  # تحويل الرد إلى صوت عربي وتشغيله
  output_file = "voice_response.mp3"
  communicate = edge_tts.Communicate(ai_reply, voice="ar-SA-HamedNeural")
  await communicate.save(output_file)

  if vc.is_playing():
    vc.stop()

  vc.play(discord.FFmpegPCMAudio(output_file))
  await ctx.send(f"🗣️ **البوت:** {ai_reply}")


# --- أمر سلاش: مرحبا ---
@bot.tree.command(name="marhaba", description="يرد عليك البوت لتحييدك")
async def marhaba(interaction: discord.Interaction):
  if interaction.channel.name != "chat-bot":
    await interaction.response.send_message(
        "⚠️ يرجى استخدام الأوامر في روم #chat-bot!", ephemeral=True
    )
    return
  await interaction.response.send_message("أهلاً بك! بوتك يعمل بنجاح 🚀")


# تشغيل البوت باستخدام المتغير البيئي للتوكن
bot.run(DISCORD_TOKEN)
