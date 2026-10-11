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


# دالة مساعدة لتوليد الصوت وتشغيله في الروم
async def speak_in_vc(vc, text):
  output_file = "voice_response.mp3"
  communicate = edge_tts.Communicate(text, voice="ar-SA-HamedNeural")
  await communicate.save(output_file)

  if vc.is_playing():
    vc.stop()

  vc.play(discord.FFmpegPCMAudio(output_file))


# --- تتبع أحداث الصوت (دخول، خروج، والسوالف التلقائية) ---
@bot.event
async def on_voice_state_update(member, before, after):
  # تجاهل البوتات لكي لا يدخل مع نفسه
  if member.bot:
    return

  log_channel = discord.utils.get(member.guild.text_channels, name="logs")

  # --- دخول عضو إلى روم صوتية (البوت يدخل تلقائياً ويسولف) ---
  if before.channel is None and after.channel is not None:
    # 1. إرسال سجل الدخول إلى روم #logs
    if log_channel:
      embed = discord.Embed(
          title="🔊 دخول إلى روم صوتية",
          description=f"دخل {member.mention} إلى روم **{after.channel.name}**",
          color=discord.Color.blue(),
      )
      embed.set_thumbnail(url=member.display_avatar.url)
      embed.set_footer(text=f"Masorh Group • {member.guild.name}")
      await log_channel.send(embed=embed)

    # 2. انضمام البوت تلقائياً للروم الصوتي والتحدث فوراً
    try:
      vc = await after.channel.connect()

      # طلب تحية وسالفة سريعة من الذكاء الاصطناعي
      system_instruction = (
          "أنت صديق يسولف في روم صوتي ديسكورد، ورحب بالعضو بأسلوب عامي لطيف"
          " ومختصر جداً بدون تشكيل أو رموز."
      )
      prompt = f"رحب بالعضو {member.display_name} وسولف معه بشكل سريع ومختصر"

      response = ai_client.models.generate_content(
          model="gemini-2.5-flash",
          contents=f"{system_instruction}\n{prompt}",
      )

      # تحويل الرد إلى صوت وتشغيله تلقائياً
      await speak_in_vc(vc, response.text)

    except Exception as e:
      print(f"خطأ عند دخول الروم أو التحدث: {e}")

  # --- خروج عضو من الروم الصوتي (البوت يخرج إذا فرغت الروم) ---
  elif before.channel is not None and after.channel is None:
    if log_channel:
      embed = discord.Embed(
          title="🔇 خروج من روم صوتية",
          description=f"خرج {member.mention} من روم **{before.channel.name}**",
          color=discord.Color.orange(),
      )
      embed.set_thumbnail(url=member.display_avatar.url)
      embed.set_footer(text=f"Masorh Group • {member.guild.name}")
      await log_channel.send(embed=embed)

    # خروج البوت إذا لم يبقَ أحد في الروم
    vc = discord.utils.get(bot.voice_clients, guild=member.guild)
    if vc and len(before.channel.members) == 1:  # البوت هو الوحيد المتبقي
      await vc.disconnect()


# --- أمر للسوالف معه أثناء وجوده بالروم ---
@bot.command()
async def ask(ctx, *, prompt: str):
  vc = ctx.voice_client
  if not vc or not vc.is_connected():
    await ctx.send("البوت ليس متواجد في روم صوتية حالياً!")
    return

  system_instruction = (
      "أنت صديق يسولف في روم صوتي، أجب بأسلوب عربي عامي لطيف ومختصر جداً بدون"
      " رموز أو تشكيل أو تنسيقات نصوص."
  )

  response = ai_client.models.generate_content(
      model="gemini-2.5-flash",
      contents=f"{system_instruction}\nالمستخدم يقول: {prompt}",
  )

  await speak_in_vc(vc, response.text)
  await ctx.send(f"🗣️ **البوت:** {response.text}")


# تشغيل البوت
bot.run(DISCORD_TOKEN)
