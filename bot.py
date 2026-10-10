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
        # تسجيل المجموعات في شجرة الأوامر
        self.tree.add_command(admin_group)
        self.tree.add_command(games_group)
        
        # مزامنة جميع الأوامر (العادية والمجموعات) عالمياً
        synced = await self.tree.sync()
        print(f"تم مزامنة {len(synced)} أمر سلاش بنجاح!")

bot = MyBot()

# ==========================================
# 1. أوامر السلاش العادية (التي خارج المجموعات)
# ==========================================

@bot.tree.command(name="marhaba", description="يرد عليك البوت لتحييدك")
async def marhaba(interaction: discord.Interaction):
    if interaction.channel.name != 'chat-bot':
        await interaction.response.send_message("⚠️ يرجى استخدام الأوامر في روم #chat-bot!", ephemeral=True)
        return
    await interaction.response.send_message("أهلاً بك! بوتك يعمل بنجاح 🚀")


# ==========================================
# 2. مجموعة أوامر الإدارة (/admin ...)
# ==========================================
admin_group = app_commands.Group(name="admin", description="أوامر الإدارة والمشرفين")

@admin_group.command(name="clear", description="مسح عدد محدد من الرسائل في الشات")
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(interaction: discord.Interaction, amount: int):
    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(f"🧹 تم بنجاح مسح **{len(deleted)}** رسالة.", ephemeral=True)

@admin_group.command(name="kick", description="طرد عضو من السيرفر")
@app_commands.checks.has_permissions(kick_members=True)
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك طرد عضو رتبته أعلى منك!", ephemeral=True)
        return
    await member.kick(reason=reason)
    await interaction.response.send_message(f"👞 تم طرد {member.mention}\n**السبب:** {reason}")

@admin_group.command(name="ban", description="حظر (باند) عضو من السيرفر")
@app_commands.checks.has_permissions(ban_members=True)
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str = "لم يتم تحديد سبب"):
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك حظر عضو رتبته أعلى منك!", ephemeral=True)
        return
    await member.ban(reason=reason)
    await interaction.response.send_message(f"🔨 تم إعطاء باند لـ {member.mention}\n**السبب:** {reason}")

@admin_group.command(name="timeout", description="إعطاء تايم أوت (ميوت) لعضو بالدقائق")
@app_commands.checks.has_permissions(moderate_members=True)
async def timeout(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str = "لم يتم تحديد سبب"):
    if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك تطبيق تايم أوت على عضو رتبته أعلى منك!", ephemeral=True)
        return
    duration = timedelta(minutes=minutes)
    await member.timeout(duration, reason=reason)
    await interaction.response.send_message(f"⏰ تم إعطاء تايم أوت لـ {member.mention} لمدة **{minutes}** دقيقة.")

@admin_group.command(name="role", description="إعطاء أو سحب رتبة من عضو")
@app_commands.checks.has_permissions(manage_roles=True)
@app_commands.choices(action=[
    app_commands.Choice(name="give (إعطاء)", value="give"),
    app_commands.Choice(name="remove (سحب)", value="remove")
])
async def role(interaction: discord.Interaction, action: str, target: discord.Member, role: discord.Role):
    if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
        await interaction.response.send_message("❌ لا يمكنك التحكم برتبة مساوية أو أعلى من رتبتك!", ephemeral=True)
        return

    if action == "give":
        await target.add_roles(role)
        await interaction.response.send_message(f"✅ تم إعطاء الرتبة **{role.name}** لـ {target.mention}")
    elif action == "remove":
        await target.remove_roles(role)
        await interaction.response.send_message(f"✅ تم سحب الرتبة **{role.name}** من {target.mention}")


# ==========================================
# 3. مجموعة أوامر الألعاب (/games ...)
# ==========================================
games_group = app_commands.Group(name="games", description="أوامر الألعاب والترفيه")

@games_group.command(name="balance", description="عرض رصيدك الحالي في السيرفر")
async def balance(interaction: discord.Interaction):
    await interaction.response.send_message(f"💰 رصيدك الحالي يا {interaction.user.mention} هو: **$50**", ephemeral=True)

@games_group.command(name="blackjack", description="بدء لعبة بلاك جاك جديدة")
async def blackjack_cmd(interaction: discord.Interaction):
    await interaction.response.send_message("🃏 تم بدء لعبة البلاك جاك!")


# ==========================================
# الأحداث (Events) والـ Logs
# ==========================================

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

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

@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if not log_channel:
        return

    # 1. حالة الميوت الصوتي (Server Mute / Unmute)
    if before.mute != after.mute:
        await asyncio.sleep(0.5)
        admin = None
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_update):
                if entry.target.id == member.id:
                    admin = entry.user
                    break
        except Exception:
            pass

        admin_mention = admin.mention if admin else "مشرف"
        room_name = after.channel.name if after.channel else "غير معروف"

        if after.mute:
            embed = discord.Embed(
                title="🎙️ إعطاء ميوت صوتي (Server Mute)",
                description=f"👤 **العضو:** {member.mention}\n🛡️ **بواسطة المشرف:** {admin_mention}\n🔊 **في روم:** **{room_name}**",
                color=discord.Color.red()
            )
        else:
            embed = discord.Embed(
                title="🎙️ فك الميوت الصوتي (Server Unmute)",
                description=f"👤 **العضو:** {member.mention}\n🛡️ **بواسطة المشرف:** {admin_mention}",
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

    # 4. حالة خروج أو طرد (Disconnect) من روم صوتية
    elif before.channel is not None and after.channel is None:
        await asyncio.sleep(1.5)
        kicker = None
        try:
            async for entry in member.guild.audit_logs(limit=5, action=discord.AuditLogAction.member_disconnect):
                if entry.target.id == member.id:
                    time_diff = (discord.utils.utcnow() - entry.created_at).total_seconds()
                    if time_diff < 10:
                        kicker = entry.user
                        break
        except Exception:
            pass

        if kicker and kicker.id != member.id:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية (Disconnect)",
                description=f"👤 **الشخص المطرود:** {member.mention}\n🛡️ **طُرِد بواسطة المشرف:** {kicker.mention}\n🔊 **من روم:** **{before.channel.name}**",
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

bot.run(os.getenv("TOKEN"))
