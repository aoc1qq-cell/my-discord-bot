import asyncio
import os
import discord
from discord import app_commands
from discord.ext import commands
import edge_tts
from google import genai

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DISCORD_TOKEN = os.getenv("TOKEN")

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


async def speak_in_vc(vc, text):
  output_file = "voice_response.mp3"
  communicate = edge_tts.Communicate(text, voice="ar-SA-HamedNeural")
  await communicate.save(output_file)

  if vc.is_playing():
    vc.stop()

  vc.play(discord.FFmpegPCMAudio(output_file))


# --- أمر السوالف والتحدث بالصوت مع نظام البديل التلقائي ---
@bot.command()
async def ask(ctx, *, prompt: str):
  if not ctx.author.voice:
    await ctx.send("لازم تكون داخل روم صوتي عشان أقدر أسولف معك!")
    return

  user_channel = ctx.author.voice.channel
  vc = ctx.voice_client

  if not vc or not vc.is_connected():
    try:
      vc = await user_channel.connect(reconnect=True, timeout=10.0)
    except Exception:
      if ctx.guild.voice_client:
        await ctx.guild.voice_client.move_to(user_channel)
        vc = ctx.guild.voice_client

  system_instruction = (
      "أنت صديق يسولف في روم صوتي، أجب بأسلوب عربي عامي لطيف ومختصر جداً بدون"
      " رموز أو تشكيل أو تنسيقات نصوص."
  )

  ai_reply = None

  # محاولة استخدام النموذج الأساسي
  try:
    response = await ai_client.aio.models.generate_content(
        model="gemini-3.8-flash",
        contents=f"{system_instruction}\nالمستخدم يقول: {prompt}",
    )
    ai_reply = response.text
  except Exception:
    # محاولة نموذج بديل فوراً في حال واجه ضغطاً (503)
    try:
      response = await ai_client.aio.models.generate_content(
          model="gemini-1.5-flash",
          contents=f"{system_instruction}\nالمستخدم يقول: {prompt}",
      )
      ai_reply = response.text
    except Exception as e:
      await ctx.send(f"❌ عذراً، الخدمة تحت الضغط حالياً. جرب بعد قليل.")
      return

  if ai_reply:
    await speak_in_vc(vc, ai_reply)
    await ctx.send(f"🗣️ **البوت:** {ai_reply}")


# --- أمر مغادرة الروم ---
@bot.command()
async def leave(ctx):
  if ctx.voice_client:
    await ctx.voice_client.disconnect()
    await ctx.send("تم الخروج من الروم الصوتي.")


bot.run(DISCORD_TOKEN)
