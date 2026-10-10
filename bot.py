import discord
from discord import app_commands
from discord.ext import commands
import os
import time
import asyncio

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
last_voice_time = {}

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

# --- نظام سجلات دخول وخروج الأعضاء من السيرفر ---
@bot.event
async def on_member_join(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(
            title="📥 دخول عضو جديد",
            description=f"دخول {member.mention}!",
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

# --- تتبع الصوت تلقائياً مع كشف النقل والطرد من الـ Audit Logs ---
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if not log_channel:
        return

    current_time = time.time()

    # حماية من تكرار الرسائل لنفس الشخص
    if member.id in last_voice_time and (current_time - last_voice_time[member.id]) < 3:
        return

    # 1. حالة الانتقال بين الرومات الصوتية
    if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        last_voice_time[member.id] = current_time
        await asyncio.sleep(1) # انتظار ثانية لتسجيل ديسكورد للحدث

        mover = None
        try:
            async for entry in member.guild.audit_logs(limit=2, action=discord.AuditLogAction.member_move):
                # التأكد أن الحدث يخص هذا العضو وحدث الآن (خلال آخر 5 ثوانٍ)
                if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 5:
                    mover = entry.user
                    break
        except Exception:
            pass

        if mover and mover.id != member.id:
            embed = discord.Embed(
                title="🔄 نقل بين الرومات الصوتية",
                description=(
                    f"👤 **العضو:** {member.mention}\n"
                    f"🛡️ **نُقِل بواسطة:** {mover.mention}\n"
                    f"📍 **من روم:** **{before.channel.name}**\n"
                    f"🎯 **إلى روم:** **{after.channel.name}**"
                ),
                color=discord.Color.purple()
            )
        else:
            embed = discord.Embed(
                title="🔄 انتقال بين الرومات الصوتية",
                description=f"انتقل {member.mention} من روم **{before.channel.name}** إلى روم **{after.channel.name}**",
                color=discord.Color.purple()
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    # 2. حالة دخول روم صوتية
    elif before.channel is None and after.channel is not None:
        last_voice_time[member.id] = current_time
        embed = discord.Embed(
            title="🔊 دخول إلى روم صوتية",
            description=f"دخل {member.mention} إلى روم **{after.channel.name}**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    # 3. حالة خروج أو طرد من روم صوتية
    elif before.channel is not None and after.channel is None:
        last_voice_time[member.id] = current_time
        await asyncio.sleep(1) # انتظار ثانية لتسجيل ديسكورد للحدث

        kicker = None
        try:
            async for entry in member.guild.audit_logs(limit=2, action=discord.AuditLogAction.member_disconnect):
                if entry.target.id == member.id and (discord.utils.utcnow() - entry.created_at).total_seconds() < 5:
                    kicker = entry.user
                    break
        except Exception:
            pass

        if kicker and kicker.id != member.id:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية",
                description=(
                    f"👤 **الشخص المطرود:** {member.mention}\n"
                    f"🛡️ **طُرِد بواسطة:** {kicker.mention}\n"
                    f"🔊 **من روم:** **{before.channel.name}**"
                ),
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="🔇 خروج من روم صوتية",
                description=f"خرج {member.mention} من روم **{before.channel.name}**",
                color=discord.Color.orange()
            )

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

# --- أمر سلاش: مرحبا ---
@bot.tree.command(name="marhaba", description="يرد عليك البوت لتحييدك")
async def marhaba(interaction: discord.Interaction):
    if interaction.channel.name != 'chat-bot':
        await interaction.response.send_message("⚠️ يرجى استخدام الأوامر في روم #chat-bot!", ephemeral=True)
        return
    await interaction.response.send_message("أهلاً بك! بوتك يعمل بنجاح 🚀")

bot.run(os.getenv("TOKEN"))
