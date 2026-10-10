import discord
from discord import app_commands
from discord.ext import commands
import os
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

# --- تتبع أحداث الصوت العادية (دخول، خروج، انتقال، ميوت) ---
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

    # 4. حالة خروج من روم صوتية
    elif before.channel is not None and after.channel is None:
        embed = discord.Embed(
            title="🔇 خروج من روم صوتية",
            description=f"خرج {member.mention} من روم **{before.channel.name}**",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text=f"Masorh Group • {member.guild.name}")
        await log_channel.send(embed=embed)

# --- أمر إداري دقيق 100%: طرد عضو من الروم الصوتية وتسجيل اسم المشرف ---
@bot.tree.command(name="kick_voice", description="طرد عضو من المكالمة الصوتية مع تسجيل اسم المشرف فوراً في الـ logs")
@app_commands.describe(member="العضو المراد طرده")
@app_commands.checks.has_permissions(move_members=True)
async def kick_voice(interaction: discord.Interaction, member: discord.Member):
    if member.voice and member.voice.channel:
        channel_name = member.voice.channel.name
        await member.move_to(None)
        
        log_channel = discord.utils.get(interaction.guild.text_channels, name='logs')
        if log_channel:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 الشخص المطرود", value=f"{member.mention} (`{member.name}`)", inline=False)
            embed.add_field(name="🛡️ طُرِد بواسطة المشرف", value=f"{interaction.user.mention} (`{interaction.user.name}`)", inline=False)
            embed.add_field(name="🔊 من روم", value=f"**{channel_name}**", inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Masorh Group • {interaction.guild.name}")
            await log_channel.send(embed=embed)
            
        await interaction.response.send_message(f"✅ تم طرد {member.mention} وتوثيق العملية في #logs بنجاح!", ephemeral=True)
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
