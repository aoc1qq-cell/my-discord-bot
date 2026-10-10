import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True  # تفعيل صلاحية تتبع الصوت

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

# --- نظام سجلات الدخول والخروج (Embed) ---
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

# --- تتبع الخروج والطرود من القنوات الصوتية ---
@bot.event
async def on_voice_state_update(member, before, after):
    # التحقق فقط عند الخروج من روم صوتية (كان في روم وأصبح لا يوجد روم)
    if before.channel is not None and after.channel is None:
        log_channel = discord.utils.get(member.guild.text_channels, name='logs')
        if not log_channel:
            return

        await asyncio.sleep(1) # الانتظار ثانية لتحديث سجلات السيرفر (Audit Logs)
        
        kicker = None
        # البحث في سجل الأحداث لطرود الصوت الأخيرة
        try:
            async for entry in member.guild.audit_logs(limit=3, action=discord.AuditLogAction.member_disconnect):
                if entry.target.id == member.id:
                    kicker = entry.user
                    break
        except Exception:
            pass

        if kicker:
            # حالة الطرد: إظهار اسم المطرود واسم الطارد
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية",
                description=(
                    f"👤 **الشخص المطرود:** {member.mention} (`{member.name}`)\n"
                    f"🛡️ **بواسطة (الطارد):** {kicker.mention} (`{kicker.name}`)\n"
                    f"🔊 **من الروم:** {before.channel.name}"
                ),
                color=discord.Color.dark_red()
            )
        else:
            # حالة الخروج الطبيعي
            embed = discord.Embed(
                title="🔊 خروج من روم صوتية",
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
