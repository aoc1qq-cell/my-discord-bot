import discord
from discord import app_commands
from discord.ext import commands
import os
import random

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print("تم مزامنة أوامر السلاش بنجاح!")

bot = MyBot()
secret_numbers = {}

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

# --- نظام تسجيل دخول وخروج الأعضاء بشكل منسق (Embed) في روم logs ---
@bot.event
async def on_member_join(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(
            title="📥 دخول عضو جديد",
            description=f"النور نورك يا {member.mention}!",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(
            title="📤 مغادرة عضو",
            description=f"عضو غادر السيرفر: **{member.name}**",
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

# --- أمر سلاش: مرحبا ---
@bot.tree.command(name="marhaba", description="يرد عليك البوت لتحييدك")
async def marhaba(interaction: discord.Interaction):
    if interaction.channel.name != 'chat-bot':
        await interaction.response.send_message("⚠️ يرجى استخدام الأوامر في روم #chat-bot!", ephemeral=True)
        return
    await interaction.response.send_message("أهلاً بك! بوتك يعمل بنجاح 🚀")

# --- أمر سلاش: لعبة تخمين الرقم ---
@bot.tree.command(name="guess", description="لعبة تخمين رقم سري بين 1 و 100")
@app_commands.describe(number="الرقم الذي تخمنه")
async def guess(interaction: discord.Interaction, number: int):
    if interaction.channel.name != 'chat-bot':
        await interaction.response.send_message("⚠️ لعبة تخمين الأرقام مخصصة فقط في روم #chat-bot!", ephemeral=True)
        return

    channel_id = interaction.channel.id
    if channel_id not in secret_numbers:
        secret_numbers[channel_id] = random.randint(1, 100)
    
    target = secret_numbers[channel_id]
    
    if number < target:
        await interaction.response.send_message("📈 الرقم صغير جداً! ابحث عن رقم **أكبر**.")
    elif number > target:
        await interaction.response.send_message("📉 الرقم كبير جداً! ابحث عن رقم **أصغر**.")
    else:
        await interaction.response.send_message(f"🎉 كفووو! لقد فزت يا {interaction.user.mention}! الرقم الصحيح كان {target}.")
        secret_numbers[channel_id] = random.randint(1, 100)

bot.run(os.getenv("TOKEN"))
