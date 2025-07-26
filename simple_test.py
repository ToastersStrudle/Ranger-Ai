#!/usr/bin/env python3
"""
Simple connection test for Ranger AI
"""

import discord
import asyncio
import json

async def test_connection():
    """Test Discord connection"""
    try:
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        token = config.get("bot_token")
        if not token:
            print("❌ No bot token found!")
            return
        
        print("🔍 Testing Discord connection...")
        
        # Create client
        intents = discord.Intents.default()
        intents.message_content = True
        
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"✅ Connected as {client.user}")
            print(f"📊 Bot is in {len(client.guilds)} servers")
            await client.close()
        
        await client.start(token)
        
    except discord.LoginFailure:
        print("❌ Invalid bot token! Please check your token.")
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 