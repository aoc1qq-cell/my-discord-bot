import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # إضافة مجموعة أوامر الأدمن لشجرة الأوامر
        self.tree.add_command(admin_group)
        # مزامنة الأوامر مع ديسكورد
        synced = await self.tree.sync()
        print(f"تم مزامنة {len(synced)} أمر سلاش بنجاح!")

bot = MyBot()

# --- مجموعة أوامر الإدارة (Admin Commands Group) ---
admin_group = app_commands.Group(name="admin", description="أوامر الإدارة والمشرفين")

# 1. أمر مسح الرسائل (/admin clear)
@admin_group.command(name="clear", description="مسح عدد محدد من الرسائل في الشات")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 تم بنجاح مسح **{len(deleted)}** رسالة.", ephemeral=True)

# 2. أمر الطرد (/admin kick)
@admin_group.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك طرد عضو رتبته أعلى منك أو مساوية لرتبتك!", ephemeral=True)
        return
    
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👞 تم طرد {member.mention}\n**السبب:** {reason}")

# 3. أمر الباند (/admin ban)
@admin_group.command(name="ban", description="حظر (باند) عضو من السيرفر")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك حظر عضو رتبته أعلى منك أو مساوية لرتبتك!", ephemeral=True)
        return
    
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم إعطاء باند لـ {member.mention}\n**السبب:** {reason}")

# 4. أمر التايم أوت (/admin timeout)
@admin_group.command(name="timeout", description="إعطاء تايم أوت (عزل/ميوت) لعضو بالدقائق")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "لم يتم تحديد سبب"):
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك تطبيق تايم أوت على عضو رتبته أعلى منك!", ephemeral=True)
        return

    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"⏰ تم إعطاء تايم أوت لـ {member.mention} لمدة **{minutes}** دقيقة.\n**السبب:** {reason}")

# التعامل مع خطأ نقص الصلاحيات عند تشغيل أمر السلاش
@clear.error
@kick.error
@ban.error
@timeout.error
async def admin_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ ليس لديك الصلاحيات الكافية لاستخدام هذا الأمر!", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ حدث خطأ: {error}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")
