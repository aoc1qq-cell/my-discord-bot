import discord
from discord import app_commands
from discord.ext import commands
import os
import time

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
last_leave_time = {}

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
    if before.channel is not None and after.channel is None:
        current_time = time.time()
        if member.id in last_leave_time and (current_time - last_leave_time[member.id]) < 5:
            return
        last_leave_time[member.id] = current_time

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

# --- أمر /disconnect المخصص للطرد مع إظهار المطرود والطارد بوضوح ---
@bot.tree.command(name="disconnect", description="طرد عضو من الروم الصوتية وتسجيل اسم الطارد والمطرود")
@app_commands.describe(member="العضو المراد طرده من الروم")
@app_commands.checks.has_permissions(move_members=True)
async def disconnect(interaction: discord.Interaction, member: discord.Member):
    if member.voice and member.voice.channel:
        channel_name = member.voice.channel.name
        
        # طرد العضو من المكالمة
        await member.move_to(None)
        
        # إرسال التقرير الشامل في روم logs
        log_channel = discord.utils.get(interaction.guild.text_channels, name='logs')
        if log_channel:
            embed = discord.Embed(
                title="🚫 طرد من روم صوتية",
                color=discord.Color.red()
            )
            embed.add_field(name="👤 الشخص المطرود", value=f"{member.mention} (`{member.name}`)", inline=False)
            embed.add_field(name="🛡️ طُرِد بواسطة (الأدمن)", value=f"{interaction.user.mention} (`{interaction.user.name}`)", inline=False)
            embed.add_field(name="🔊 من الروم", value=f"**{channel_name}**", inline=False)
            
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Masorh Group •
