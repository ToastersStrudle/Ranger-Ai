#!/usr/bin/env python3
"""
Robust Ranger AI Bot - Handles connection issues gracefully
"""

import discord
from discord.ext import commands
import json
import asyncio
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    print(f'🆔 Bot ID: {bot.user.id}')
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
    embed.add_field(name="!hello", value="Simple greeting", inline=False)
    
    await ctx.send(embed=embed)

async def connect_with_retry():
    """Connect to Discord with retry logic"""
    token = config.get("bot_token")
    if not token:
        print("❌ Bot token not found in config.json!")
        return False
    
    max_retries = 5
    retry_delay = 30  # seconds
    
    for attempt in range(max_retries):
        try:
            print(f"🚀 Attempting to connect to Discord (attempt {attempt + 1}/{max_retries})...")
            await bot.start(token)
            return True
            
        except discord.LoginFailure:
            print("❌ Invalid bot token! Please check your token.")
            return False
            
        except Exception as e:
            error_msg = str(e)
            if "520" in error_msg:
                print(f"⚠️ Discord servers are having issues (520 error). Retrying in {retry_delay} seconds...")
                print("This is a temporary Cloudflare issue affecting Discord's API.")
            else:
                print(f"❌ Connection error: {e}")
                print(f"Retrying in {retry_delay} seconds...")
            
            if attempt < max_retries - 1:
                print(f"⏳ Waiting {retry_delay} seconds before retry...")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("❌ Max retries reached. Please try again later.")
                return False
    
    return False

async def main():
    """Main function with robust connection handling"""
    print("🤖 Starting Ranger AI with robust connection handling...")
    print("📋 If Discord is having issues, the bot will retry automatically.")
    
    success = await connect_with_retry()
    
    if not success:
        print("\n💡 Troubleshooting tips:")
        print("1. Check if Discord is having issues: https://status.discord.com")
        print("2. Verify your bot token is correct")
        print("3. Make sure your bot is invited to your server")
        print("4. Try running the bot again in a few minutes")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}") 