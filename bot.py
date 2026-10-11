import asyncio
import os
import discord
from discord.ext import commands
import edge_tts
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("TOKEN")

# استخدام النموذج المستقر والرسمي من جوجل
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


async def speak_in_vc(vc, text):
  output_file = "voice_response.mp3"
  communicate = edge_tts.Communicate(text, voice="ar-SA-HamedNeural")
  await communicate.save(output_file)

  if vc.is_playing():
    vc.stop()

  vc.play(discord.FFmpegPCMAudio(output_file))


# --- أمر السوالف والتحدث بالصوت (النهائي) ---
@bot.command()
async def ask(ctx, *, prompt: str):
  # 1. التأكد أنك داخل روم صوتي
  if not ctx.author.voice:
    await ctx.send("❌ لازم تكون داخل روم صوتي عشان أقدر أدخل معك!")
    return

  user_channel = ctx.author.voice.channel
  vc = ctx.voice_client

  # 2. دخول البوت للمكالمة فوراً
  try:
    if not vc or not vc.is_connected():
      vc = await user_channel.connect()
    elif vc.channel != user_channel:
      await vc.move_to(user_channel)
  except Exception as e:
    await ctx.send(f"❌ خطأ في الاتصال الصوتي: {e}")
    return

  # 3. توليد الرد من الذكاء الاصطناعي
  try:
    system_instruction = (
        "أنت صديق يسولف في روم صوتي، أجب بأسلوب عربي عامي لطيف ومختصر جداً بدون"
        " رموز أو تشكيل أو تنسيقات نصوص."
    )

    response = await ai_client.aio.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"{system_instruction}\nالسؤال: {prompt}",
    )

    ai_reply = response.text
    if not ai_reply:
      ai_reply = "هلا بك، معك!"

    # 4. تشغيل الصوت وإرسال الرسالة في الشات
    await speak_in_vc(vc, ai_reply)
    await ctx.send(f"🗣️ **البوت:** {ai_reply}")

  except Exception as e:
    await ctx.send(f"❌ حدث خطأ تقني: {e}")


# --- أمر مغادرة الروم ---
@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send("تم الخروج من الروم الصوتي.")


bot.run(DISCORD_TOKEN)
