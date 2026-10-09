import discord
from discord.ext import commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("تم تسجيل الدخول بنجاح")

@bot.command()
async def مرحبا(ctx):
    await ctx.send("أهلاً بك! بوتك يعمل بنجاح 🚀")

bot.run("MTU1ODE3Nzg2NzMyMDI3MDkyOQ.Gaosey.yHLE6PsJIpPMjUf2Q5UyeWIyzKUQXxYk9vMdRo")
