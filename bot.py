import discord
from discord import app_commands
from discord.ext import commands
import os

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

# --- تتبع جميع أحداث الصوت (دخول، خروج، طرد إداري، انتقال، ديفين) ---
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if not log_channel:
        return

    # 1. حالة الديفين (Server Deafen / Undeafen)
    if before.deafen != after.deafen:
        admin = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_update):
                if entry.target.id == member.id:
                    admin = entry.user
                    break
        except Exception:
            pass

        if after.deafen:
            embed = discord.Embed(
                title="🎧 إعطاء ديفين (Server Deafen)",
                description=(
                    f"👤 **العضو:** {member.mention}\n"
                    f"🛡️ **بواسطة المشرف:** {admin.mention if admin else 'مشرف'}\n"
                    f"🔊 **في روم:** **{after.channel.name if after.channel else 'غير معروف'}**"
                ),
                color=discord.Color.dark_red()
            )
        else:
            embed = discord.Embed(
                title="🎧 فك الديفين (Server Undeafen)",
                description=(
                    f"👤 **العضو:** {member.mention}\n"
                    f"🛡️ **بواسطة المشرف:** {admin.mention if admin else 'مشرف'}"
                ),
                color=discord.Color.green()
            )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)
        return

    # 2. حالة الانتقال بين الرومات الصوتية
    if before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
        embed = discord.Embed(
            title="🔄 انتقال بين الرومات الصوتية",
            description=f"انتقل {member.mention} من روم **{before.channel.name}** إلى روم **{after.channel.name}**",
            color=discord.Color.purple()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    # 3. حالة دخول روم صوتية
    elif before.channel is None and after.channel is not None:
        embed = discord.Embed(
            title="🔊 دخول إلى روم صوتية",
            description=f"دخل {member.mention} إلى روم **{after.channel.name}**",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

    # 4. حالة خروج أو طرد من روم صوتية
    elif before.channel is not None and after.channel is None:
        kicker = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_disconnect):
                if entry.target.id == member.id:
                    kicker = entry.user
                    break
        except Exception:
            pass

        if kicker and kicker.id != member.id:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية",
                description=(
                    f"👤 **الشخص المطرود:** {member.mention}\n"
                    f"🛡️ **طُرِد بواسطة:** {kicker.mention
