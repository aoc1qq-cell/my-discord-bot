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

# --- تتبع الخروج العادي من الرومات الصوتية ---
@bot.event
async def on_voice_state_update(member, before, after):
    # إذا كان خروجاً طبيعياً (انتقال من روم إلى None)
    if before.channel is not None and after.channel is None:
        log_channel = discord.utils.get(member.guild.text_channels, name='logs')
        if not log_channel:
            return

        embed = discord.Embed(
            title="🔊 خروج من روم صوتية",
            description=f"خرج {member.mention} من روم **{before.channel.name}**",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

# --- أمر سلاش للطرد من الروم مع تسجيل اسم الطارد والمطرود في logs بدقة ---
@bot.tree.command(name="disconnect", description="طرد عضو من الروم الصوتية وتسجيله في الـ logs")
@app_commands.describe(member="العضو المراد طرده من الروم")
@app_commands.checks.has_permissions(move_members=True)
async def disconnect(interaction: discord.Interaction, member: discord.Member):
    if member.voice and member.voice.channel:
        channel_name = member.voice.channel.name
        # إخراج العضو من الروم الصوتية
        await member.move_to(None)
        
        # إرسال رسالة في شات الـ logs
        log_channel = discord.utils.get(interaction.guild.text_channels, name='logs')
        if log_channel:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية (بواسطة مشرف)",
                description=(
                    f"👤 **الشخص المطرود:** {member.mention}\n"
                    f"🛡️ **طُرِد بواسطة المشرف:** {interaction.user.mention}\n"
                    f"🔊 **من الروم:** {channel_name}"
                ),
                color=discord.Color.dark_red()
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Masorh Group • {interaction.guild.name}")
            await log_channel.send(embed=embed)
            
        await interaction.response.send_message(f"تم طرد {member.mention} بنجاح وتسجيل العملية في #logs.", ephemeral=True)
    else:
        await interaction.response.send_message("⚠️ هذا العضو ليس في أي روم صوتية حالياً!", ephemeral=True)

# --- أمر سلاش: مرحبا ---
@bot.tree.command(name="marhaba", description="يرد عليك البوت لتحييدك")
async def marhaba(interaction: discord.Interaction):
    if interaction.channel.name != 'chat-bot':
        await interaction.response.send_message("⚠️ يرجى استخدام الأوامر في روم #chat-bot!", ephemeral=True)
        return
    await interaction.response.send_message("أهلاً بك! بوتك يعمل بنجاح 🚀")

bot.run(os.getenv("TOKEN"))
