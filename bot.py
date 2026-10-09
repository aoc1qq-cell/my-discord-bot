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

bot.run("MTU1ODE3Nzg2NzMyMDI3MDkyOQ.GIdEk8.sfY8yrBhVxDGw6_Ru9r5C-GhoKg82SLM2RdRzE")
