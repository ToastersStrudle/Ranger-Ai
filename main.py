#!/usr/bin/env python3
"""
Ranger AI - An Intelligent Discord Bot
A self-learning AI that can verify information from the web and modify its own code.
"""

import asyncio
import discord
from discord.ext import commands
import os
import json
import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import datetime
import logging
from typing import Dict, List, Any, Optional
import threading
import time
import hashlib
import pickle
from pathlib import Path

# Import custom modules
from modules.learning_engine import LearningEngine
from modules.web_verifier import WebVerifier
from modules.code_modifier import CodeModifier
from modules.knowledge_base import KnowledgeBase
from modules.conversation_analyzer import ConversationAnalyzer
from modules.self_improvement import SelfImprovement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ranger_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RangerAI(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.messages = True
        intents.guilds = True
        
        super().__init__(command_prefix='!', intents=intents)
        
        # Initialize core components
        self.learning_engine = LearningEngine()
        self.web_verifier = WebVerifier()
        self.code_modifier = CodeModifier()
        self.knowledge_base = KnowledgeBase()
        self.conversation_analyzer = ConversationAnalyzer()
        self.self_improvement = SelfImprovement()
        
        # Bot configuration
        self.name = "Ranger AI"
        self.version = "1.0.0"
        self.creator = "Braxton"
        self.last_improvement = datetime.datetime.now()
        
        # Load configuration
        self.load_config()
        
        # Setup event handlers
        self.setup_events()
        
    def load_config(self):
        """Load bot configuration from config.json"""
        try:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        except FileNotFoundError:
            self.config = {
                "bot_token": "",
                "owner_id": "",
                "learning_enabled": True,
                "web_verification_enabled": True,
                "self_improvement_enabled": True,
                "max_context_length": 2000,
                "learning_rate": 0.1,
                "verification_threshold": 0.8
            }
            self.save_config()
    
    def save_config(self):
        """Save bot configuration to config.json"""
        with open('config.json', 'w') as f:
            json.dump(self.config, f, indent=4)
    
    def setup_events(self):
        """Setup Discord event handlers"""
        
        @self.event
        async def on_ready():
            logger.info(f'{self.user} has connected to Discord!')
            logger.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
            await self.change_presence(activity=discord.Game(name="Learning & Growing"))
            
            # Start background tasks
            self.bg_task = self.loop.create_task(self.background_tasks())
        
        @self.event
        async def on_message(message):
            if message.author == self.user:
                return
            
            # Process message for learning
            if self.config.get("learning_enabled", True):
                await self.process_message_for_learning(message)
            
            # Handle commands
            await self.process_commands(message)
        
        @self.event
        async def on_command_error(ctx, error):
            if isinstance(error, commands.CommandNotFound):
                # Try to learn from the unknown command
                await self.learning_engine.learn_from_unknown_command(ctx.message.content)
            else:
                logger.error(f"Command error: {error}")
                await ctx.send(f"An error occurred: {str(error)}")
    
    async def process_message_for_learning(self, message):
        """Process messages for learning and knowledge acquisition"""
        try:
            # Analyze conversation context
            context = await self.conversation_analyzer.analyze_context(message)
            
            # Extract potential knowledge
            knowledge = await self.learning_engine.extract_knowledge(message.content, context)
            
            if knowledge:
                # Verify knowledge using web sources
                if self.config.get("web_verification_enabled", True):
                    verification_result = await self.web_verifier.verify_knowledge(knowledge)
                    
                    if verification_result['is_verified']:
                        # Store verified knowledge
                        await self.knowledge_base.store_knowledge(knowledge, verification_result)
                        logger.info(f"Stored verified knowledge: {knowledge['topic']}")
                    else:
                        # Store with uncertainty flag
                        knowledge['uncertainty'] = verification_result['confidence']
                        await self.knowledge_base.store_knowledge(knowledge, verification_result)
                        logger.info(f"Stored uncertain knowledge: {knowledge['topic']}")
                else:
                    # Store without verification
                    await self.knowledge_base.store_knowledge(knowledge, {'is_verified': False, 'confidence': 0.0})
            
            # Check for self-improvement opportunities
            if self.config.get("self_improvement_enabled", True):
                improvement_suggestions = await self.self_improvement.analyze_performance(message)
                if improvement_suggestions:
                    await self.handle_improvement_suggestions(improvement_suggestions)
                    
        except Exception as e:
            logger.error(f"Error processing message for learning: {e}")
    
    async def handle_improvement_suggestions(self, suggestions):
        """Handle self-improvement suggestions"""
        for suggestion in suggestions:
            if suggestion['type'] == 'code_modification':
                success = await self.code_modifier.apply_modification(suggestion['code'])
                if success:
                    logger.info(f"Applied code modification: {suggestion['description']}")
                else:
                    logger.error(f"Failed to apply code modification: {suggestion['description']}")
    
    async def background_tasks(self):
        """Background tasks for continuous learning and improvement"""
        while True:
            try:
                # Periodic knowledge consolidation
                await self.knowledge_base.consolidate_knowledge()
                
                # Periodic self-improvement check
                if self.config.get("self_improvement_enabled", True):
                    await self.self_improvement.periodic_improvement_check()
                
                # Update bot status
                await self.update_status()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in background tasks: {e}")
                await asyncio.sleep(60)
    
    async def update_status(self):
        """Update bot status with current learning stats"""
        knowledge_count = await self.knowledge_base.get_knowledge_count()
        verified_count = await self.knowledge_base.get_verified_knowledge_count()
        
        status_text = f"Learned {knowledge_count} things | {verified_count} verified"
        await self.change_presence(activity=discord.Game(name=status_text))

# Command definitions
class RangerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(name='learn')
    async def learn_command(self, ctx, *, topic):
        """Manually trigger learning about a specific topic"""
        await ctx.send(f"🔍 Learning about: {topic}")
        
        # Search web for information
        web_info = await self.bot.web_verifier.search_web(topic)
        
        if web_info:
            # Verify and store
            verification = await self.bot.web_verifier.verify_knowledge({
                'topic': topic,
                'content': web_info,
                'source': 'web_search'
            })
            
            await self.bot.knowledge_base.store_knowledge({
                'topic': topic,
                'content': web_info,
                'source': 'web_search'
            }, verification)
            
            await ctx.send(f"✅ Learned about {topic}! Information verified and stored.")
        else:
            await ctx.send(f"❌ Couldn't find reliable information about {topic}")
    
    @commands.command(name='knowledge')
    async def knowledge_command(self, ctx, *, query=None):
        """Query the bot's knowledge base"""
        if query:
            knowledge = await self.bot.knowledge_base.search_knowledge(query)
            if knowledge:
                response = f"📚 **Knowledge about '{query}':**\n{knowledge['content']}"
                if knowledge.get('verified'):
                    response += "\n✅ *Verified information*"
                else:
                    response += f"\n⚠️ *Confidence: {knowledge.get('confidence', 0):.2f}*"
                await ctx.send(response)
            else:
                await ctx.send(f"🤔 I don't have information about '{query}' yet.")
        else:
            stats = await self.bot.knowledge_base.get_stats()
            await ctx.send(f"📊 **Knowledge Base Stats:**\n"
                         f"Total items: {stats['total']}\n"
                         f"Verified: {stats['verified']}\n"
                         f"Uncertain: {stats['uncertain']}")
    
    @commands.command(name='improve')
    @commands.is_owner()
    async def improve_command(self, ctx):
        """Trigger self-improvement process"""
        await ctx.send("🔧 Starting self-improvement process...")
        
        improvements = await self.bot.self_improvement.trigger_improvement()
        
        if improvements:
            await ctx.send(f"✅ Applied {len(improvements)} improvements!")
        else:
            await ctx.send("ℹ️ No improvements needed at this time.")
    
    @commands.command(name='status')
    async def status_command(self, ctx):
        """Show bot status and statistics"""
        stats = await self.bot.knowledge_base.get_stats()
        
        embed = discord.Embed(
            title="🤖 Ranger AI Status",
            color=discord.Color.blue()
        )
        embed.add_field(name="Knowledge Items", value=stats['total'], inline=True)
        embed.add_field(name="Verified", value=stats['verified'], inline=True)
        embed.add_field(name="Uncertain", value=stats['uncertain'], inline=True)
        embed.add_field(name="Learning Enabled", value=self.bot.config.get("learning_enabled", True), inline=True)
        embed.add_field(name="Web Verification", value=self.bot.config.get("web_verification_enabled", True), inline=True)
        embed.add_field(name="Self-Improvement", value=self.bot.config.get("self_improvement_enabled", True), inline=True)
        
        await ctx.send(embed=embed)

async def main():
    """Main function to run Ranger AI"""
    bot = RangerAI()
    
    # Add command cog
    await bot.add_cog(RangerCommands(bot))
    
    # Load bot token
    token = bot.config.get("bot_token")
    if not token:
        logger.error("Bot token not found in config.json!")
        logger.info("Please add your Discord bot token to config.json")
        return
    
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid bot token!")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 