import discord
from discord.ext import commands
import os
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # مهم جداً لمراقبة دخول وخروج الأعضاء

bot = commands.Bot(command_prefix="!", intents=intents)

secret_numbers = {}

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

# --- نظام الـ Logs لتسجيل دخول وخروج الأعضاء تلقائياً ---
@bot.event
async def on_member_join(member):
    # البحث عن روم logs في السيرفر
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        await log_channel.send(f"📥 **عضو جديد دخل السيرفر:** {member.mention} (نورتنا يا بطل!)")

@bot.event
async def on_member_remove(member):
    # البحث عن روم logs في السيرفر
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        await log_channel.send(f"📤 **عضو طلع من السيرفر:** {member.name}")

# --- الأوامر العادية ---
@bot.command()
async def مرحبا(ctx):
    if ctx.channel.name not in ['chat-bot', 'cmds']:
        await ctx.send(f"⚠️ يرجى استخدام الأوامر في روم الـ chat-bot لتنظيم السيرفر!")
        return
    await ctx.send("أهلاً بك! بوتك يعمل بنجاح 🚀")

# --- لعبة تخمين الرقم (في chat-bot) ---
@bot.command()
async def guess(ctx, number: int = None):
    if ctx.channel.name != 'chat-bot':
        await ctx.send("⚠️ لعبة تخمين الأرقام مخصصة فقط في روم #chat-bot!")
        return

    if number is None:
        await ctx.send("⚠️ يرجى كتابة رقم بعد الأمر، هكذا مثلاً: `!guess 50`")
        return
    
    if ctx.channel.id not in secret_numbers:
        secret_numbers[ctx.channel.id] = random.randint(1, 100)
    
    target = secret_numbers[ctx.channel.id]
    
    if number < target:
        await ctx.send("📈 الرقم صغير جداً! ابحث عن رقم **أكبر**.")
    elif number > target:
        await ctx.send("📉 الرقم كبير جداً! ابحث عن رقم **أصغر**.")
    else:
        await ctx.send(f"🎉 كفووو! لقد فزت يا {ctx.author.mention}! الرقم الصحيح كان {target}.")
        secret_numbers[ctx.channel.id] = random.randint(1, 100)

bot.run(os.getenv("TOKEN"))
