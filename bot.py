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
        # تسجيل مجموعات الأوامر في شجرة الأوامر
        self.tree.add_command(admin_group)
        self.tree.add_command(games_group)
        
        synced = await self.tree.sync()
        print(f"تم مزامنة {len(synced)} أمر سلاش بنجاح!")

bot = MyBot()

# ==========================================
# 1. مجموعة أوامر الإدارة (/admin ...)
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
        await interaction.response.send_message("❌ لا يمكنك طرد عضو رتبته أعلى منك أو مساوية لرتبتك!", ephemeral=True)
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

# أمر إدارة الرتب (إعطاء أو سحب رتبة) مثل طلبك في الصورة
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
# 2. مجموعة أوامر الألعاب (/games ...)
# ==========================================
games_group = app_commands.Group(name="games", description="أوامر الألعاب والترفيه")

@games_group.command(name="balance", description="عرض رصيدك الحالي في السيرفر")
async def balance(interaction: discord.Interaction):
    # كمثال مبدئي، يمكنك ربطه بقاعدة بيانات لاحقاً
    await interaction.response.send_message(f"💰 رصيدك الحالي يا {interaction.user.mention} هو: **$50**", ephemeral=True)

@games_group.command(name="blackjack", description="بدء لعبة بلاك جاك جديدة وتحدي البوت")
async def blackjack_game(interaction: discord.Interaction):
    await interaction.response.send_message("🃏 تم بدء لعبة البلاك جاك! (جارٍ توزيع الأوراق...)")

# معالجة أخطاء الصلاحيات للأوامر
@clear.error
@kick.error
@ban.error
@timeout.error
@role.error
async def admin_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ ليس لديك الصلاحيات الكافية لاستخدام هذا الأمر!", ephemeral=True)
    else:
        await interaction.response.send_message(f"⚠️ حدث خطأ: {error}", ephemeral=True)

@bot.event
async def on_ready():
    print(f"تم تسجيل الدخول بنجاح باسم {bot.user}")

# --- نظام سجلات دخول وخروج الأعضاء ---
@bot.event
async def on_member_join(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(title="📥 دخول عضو جديد", description=f"دخول {member.mention}!", color=discord.Color.green())
        embed.set_thumbnail(url=member.display_avatar.url)
        await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if log_channel:
        embed = discord.Embed(title="📤 مغادرة عضو", description=f"عضو غادر السيرفر: **{member.name}**", color=discord.Color.red())
        await log_channel.send(embed=embed)

# --- تتبع الأحداث الصوتية ---
@bot.event
async def on_voice_state_update(member, before, after):
    log_channel = discord.utils.get(member.guild.text_channels, name='logs')
    if not log_channel:
        return
    # [بقية كود الفويس ومراقبة الميوت والخروج كما هي...]

bot.run(os.getenv("TOKEN"))
