import asyncio
import os
import discord
from discord.ext import commands
import edge_tts
from google import genai

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


bot = MyBot()


@bot.event
async def on_ready():
  print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")


# دالة تشغيل الصوت
async def speak_in_vc(vc, text):
  output_file = "voice_response.mp3"
  communicate = edge_tts.Communicate(text, voice="ar-SA-HamedNeural")
  await communicate.save(output_file)

  if vc.is_playing():
    vc.stop()

  vc.play(discord.FFmpegPCMAudio(output_file))


# --- أمر السوالف والتحدث بالصوت ---
@bot.command()
async def ask(ctx, *, prompt: str):
  # 1. التأكد أن العضو داخل روم صوتي
  if not ctx.author.voice:
    await ctx.send("❌ لازم تكون داخل روم صوتي عشان أقدر أدخل معك!")
    return

  user_channel = ctx.author.voice.channel
  vc = ctx.voice_client

  # 2. دخول البوت للمكالمة الصوتية
  try:
    if not vc or not vc.is_connected():
      vc = await user_channel.connect()
    elif vc.channel != user_channel:
      await vc.move_to(user_channel)
  except Exception as e:
    await ctx.send(f"❌ خطأ في الاتصال الصوتي: {e}")
    return

  # 3. جلب الرد من الذكاء الاصطناعي مع نظام بدائل تلقائي
  ai_reply = None
  models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]

  for model_name in models_to_try:
    try:
      system_instruction = (
          "أنت صديق يسولف في روم صوتي، أجب بأسلوب عربي عامي لطيف ومختصر جداً بدون"
          " رموز أو تشكيل أو تنسيقات نصوص."
      )

      response = await ai_client.aio.models.generate_content(
          model=model_name,
          contents=f"{system_instruction}\nالسؤال: {prompt}",
      )
      if response and response.text:
        ai_reply = response.text
        break
    except Exception as e:
      print(f"المحاولة بالفشل مع النموذج {model_name}: {e}")
      continue

  if not ai_reply:
    ai_reply = "هلا بك، معك!"

  # 4. تشغيل الصوت وإرسال الرسالة في الشات
  try:
    await speak_in_vc(vc, ai_reply)
    await ctx.send(f"🗣️ **البوت:** {ai_reply}")
  except Exception as e:
    await ctx.send(f"❌ خطأ أثناء تشغيل الصوت: {e}")


# --- أمر مغادرة الروم ---
@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send("تم الخروج من الروم الصوتي.")


bot.run(DISCORD_TOKEN)
