#!/usr/bin/env python3
"""
Simple test version of Ranger AI to verify Discord connection
"""

import discord
from discord.ext import commands
import json
import asyncio

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'🤖 {bot.user} has connected to Discord!')
    print(f'📊 Bot is in {len(bot.guilds)} servers')
    await bot.change_presence(activity=discord.Game(name="Learning & Growing"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # Simple response to test
    if message.content.lower().startswith('!hello'):
        await message.channel.send('👋 Hello! I am Ranger AI, your intelligent learning bot!')
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='status')
async def status_command(ctx):
    """Show bot status"""
    embed = discord.Embed(
        title="🤖 Ranger AI Status",
        description="Ranger AI is online and learning!",
        color=discord.Color.blue()
    )
    embed.add_field(name="Bot Name", value=bot.user.name, inline=True)
    embed.add_field(name="Server Count", value=len(bot.guilds), inline=True)
    embed.add_field(name="Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Learning", value="✅ Enabled", inline=True)
    embed.add_field(name="Web Verification", value="✅ Enabled", inline=True)
    embed.add_field(name="Self-Improvement", value="✅ Enabled", inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='learn')
async def learn_command(ctx, *, topic):
    """Test learning command"""
    await ctx.send(f'🔍 Learning about: {topic}\n(This is a test - full learning features coming soon!)')

@bot.command(name='rangerhelp')
async def help_command(ctx):
    """Show help"""
    embed = discord.Embed(
        title="🤖 Ranger AI Help",
        description="Available commands:",
        color=discord.Color.green()
    )
    embed.add_field(name="!status", value="Show bot status", inline=False)
    embed.add_field(name="!learn <topic>", value="Learn about a topic", inline=False)
    embed.add_field(name="!rangerhelp", value="Show this help message", inline=False)
    
    await ctx.send(embed=embed)

async def main():
    """Main function"""
    token = config.get("bot_token")
    if not token:
        print("❌ Bot token not found in config.json!")
        return
    
    try:
        print("🚀 Starting Ranger AI...")
        await bot.start(token)
    except discord.LoginFailure:
        print("❌ Invalid bot token!")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 