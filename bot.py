import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

@bot.command()
async def مرحبا(ctx):
    await ctx.send("أهلاً بك! بوتك يعمل بنجاح")
import os
bot.run(os.getenv("TOKEN"))
