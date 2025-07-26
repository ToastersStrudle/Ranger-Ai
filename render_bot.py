#!/usr/bin/env python3
import os
import discord
from discord.ext import commands

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = os.getenv("OWNER_ID")

if not BOT_TOKEN:
    print("Error: BOT_TOKEN environment variable not set!")
    exit(1)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 {bot.user} has connected to Discord!")
    print(f"📊 Bot is in {len(bot.guilds)} servers")
bot.run(BOT_TOKEN)
