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
    # مزامنة أوامر السلاش مع سيرفرات ديسكورد عند التشغيل
    await self.tree.sync()
    print("تم مزامنة أوامر السلاش (/join_voice) بنجاح!")


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


# --- أمر سلاش: /join_voice ---
@bot.tree.command(
    name="join_voice",
    description="يدخل البوت القناة الصوتية ويسولف معك فوراً",
)
async def join_voice(interaction: discord.Interaction):
  # 1. التأكد أن المستخدم داخل روم صوتي
  if not interaction.user.voice:
    await interaction.response.send_message(
        "❌ لازم تكون داخل روم صوتي عشان أقدر أدخل معك!", ephemeral=True
    )
    return

  # إبلاغ ديسكورد أن البوت قيد معالجة الطلب
  await interaction.response.defer()

  user_channel = interaction.user.voice.channel
  vc = interaction.guild.voice_client

  # 2. دخول البوت أو التنقل للقناة الصوتية
  try:
    if not vc or not vc.is_connected():
      vc = await user_channel.connect()
    elif vc.channel != user_channel:
      await vc.move_to(user_channel)
  except Exception as e:
    await interaction.followup.send(f"❌ خطأ في الاتصال الصوتي: {e}")
    return

  # 3. جلب رد ترحيبي وسالفة سريعة بالذكاء الاصطناعي
  system_instruction = (
      "أنت صديق يسولف في روم صوتي ديسكورد، أجب بأسلوب عربي عامي لطيف ومختصر جداً"
      " ورحب بالعضو بدون رموز أو تشكيل."
  )
  prompt = f"رحب بالعضو {interaction.user.display_name} وسولف معه بشكل سريع"

  ai_reply = None
  models_to_try = ["gemini-2.0-flash", "gemini-1.5-flash"]

  for model_name in models_to_try:
    try:
      response = await ai_client.aio.models.generate_content(
          model=model_name,
          contents=f"{system_instruction}\n{prompt}",
      )
      if response and response.text:
        ai_reply = response.text
        break
    except Exception as e:
      print(f"فشلت المحاولة مع {model_name}: {e}")
      continue

  if not ai_reply:
    ai_reply = f"أهلاً بك يا {interaction.user.display_name}! نورت الروم الصوتي."

  # 4. تشغيل الصوت وإرسال رد تفاعلي
  try:
    await speak_in_vc(vc, ai_reply)
    await interaction.followup.send(f"🗣️ **البوت:** {ai_reply}")
  except Exception as e:
    await interaction.followup.send(f"❌ خطأ أثناء تشغيل الصوت: {e}")


# --- أمر سلاش لمغادرة المكالمة: /leave ---
@bot.tree.command(
    name="leave", description="يخرج البوت من القناة الصوتية الحالية"
)
async def leave_voice(interaction: discord.Interaction):
  if interaction.guild.voice_client:
    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message("تم الخروج من الروم الصوتي 👋")
  else:
    await interaction.response.send_message(
        "البوت غير متواجد في أي روم صوتي حالياً.", ephemeral=True
    )


bot.run(DISCORD_TOKEN)
