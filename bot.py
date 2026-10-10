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

# --- تتبع الدخول، الخروج، والانتقال (مع كشف المشرف في حال الطرد أو النقل الإداري) ---
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if not log_channel:
        return

    current_time = time.time()
    
    # حماية من التكرار السريع
    if member.id in last_voice_time and (current_time - last_voice_time[member.id]) < 2:
        return

    # 1. حالة الانتقال بين رومين
    if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        last_voice_time[member.id] = current_time
        
        # انتظار بسيط لقراءة الـ Audit Log في حال تم نقله بواسطة مشرف
        await asyncio.sleep(1)
        mover = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_move):
                if entry.target.id == member.id:
                    mover = entry.user
                    break
        except Exception:
            pass

        if mover:
            embed = discord.Embed(
                title="🔄 نقل عضو بين الرومات (بواسطة مشرف)",
                description=(
                    f"👤 **العضو المنقول:** {member.mention}\n"
                    f"🛡️ **بواسطة المشرف:** {mover.mention}\n"
                    f"📍 **من روم:** {before.channel.name}\n"
                    f"🎯 **إلى روم:** {after.channel.name}"
                ),
                color=discord.Color.purple()
            )
        else:
            embed = discord.Embed(
                title="🔄 انتقال بين الرومات الصوتية",
                description=f"انتقل {member.mention} من روم **{before.channel.name}** إلى روم **{after.channel.name}**",
                color=discord.Color.blue()
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
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    # 3. حالة خروج أو طرد نهائي من روم صوتية
    elif before.channel is not None and after.channel is None:
        last_voice_time[member.id] = current_time
        
        # انتظار قراءة الـ Audit Log في حال تم طرده بواسطة مشرف
        await asyncio.sleep(1)
        kicker = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_disconnect):
                if entry.target.id == member.id:
                    kicker = entry.user
                    break
        except Exception:
            pass

        if kicker:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية (بواسطة مشرف)",
                description=(
                    f"👤 **الشخص المطرود:** {member.mention}\n"
                    f"🛡️ **بواسطة المشرف:** {kicker.mention}\n"
                    f"🔊 **من روم:** {before.channel.name}"
                ),
                color=discord.Color.dark_red()
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
