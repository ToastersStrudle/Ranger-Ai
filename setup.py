#!/usr/bin/env python3
"""
Ranger AI Setup Script
Helps with installation and initial configuration
"""

import os
import sys
import json
import subprocess
import sqlite3
from pathlib import Path

def print_banner():
    """Print Ranger AI banner"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                    🤖 RANGER AI SETUP 🤖                    ║
    ║                                                              ║
    ║  An Intelligent Discord Bot with Self-Learning Capabilities  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required!")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ["backups", "logs", "data"]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def initialize_database():
    """Initialize the SQLite database"""
    print("\n🗄️ Initializing database...")
    try:
        conn = sqlite3.connect('ranger_ai.db')
        cursor = conn.cursor()
        
        # Create tables (these will be created by the modules, but we ensure they exist)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT,
                extraction_method TEXT,
                confidence REAL DEFAULT 0.0,
                verified BOOLEAN DEFAULT FALSE,
                verification_confidence REAL DEFAULT 0.0,
                timestamp TEXT,
                last_accessed TEXT,
                access_count INTEGER DEFAULT 0,
                tags TEXT,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully!")
        return True
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        return False

def configure_bot():
    """Help user configure the bot"""
    print("\n⚙️ Bot Configuration")
    print("You need to configure your Discord bot token and owner ID.")
    
    config = {}
    
    # Load existing config if it exists
    if os.path.exists('config.json'):
        with open('config.json', 'r') as f:
            config = json.load(f)
    
    # Get bot token
    print("\n1. Discord Bot Token:")
    print("   - Go to https://discord.com/developers/applications")
    print("   - Create a new application or select existing one")
    print("   - Go to 'Bot' section and copy the token")
    
    bot_token = input("   Enter your bot token: ").strip()
    if bot_token:
        config['bot_token'] = bot_token
    
    # Get owner ID
    print("\n2. Owner ID:")
    print("   - Enable Developer Mode in Discord (User Settings > Advanced)")
    print("   - Right-click your username and copy ID")
    
    owner_id = input("   Enter your Discord user ID: ").strip()
    if owner_id:
        config['owner_id'] = owner_id
    
    # Save configuration
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=4)
    
    print("✅ Configuration saved!")
    return True

def download_nltk_data():
    """Download required NLTK data"""
    print("\n📚 Downloading NLTK data...")
    try:
        import nltk
        
        # Download required NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        
        print("✅ NLTK data downloaded successfully!")
        return True
    except Exception as e:
        print(f"❌ Error downloading NLTK data: {e}")
        return False

def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    try:
        # Test imports
        import discord
        import requests
        import beautifulsoup4
        import nltk
        import textblob
        
        print("✅ All modules imported successfully!")
        
        # Test database connection
        conn = sqlite3.connect('ranger_ai.db')
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM knowledge')
        conn.close()
        print("✅ Database connection successful!")
        
        # Test config
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully!")
        
        return True
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def print_next_steps():
    """Print next steps for the user"""
    print("""
    🎉 SETUP COMPLETE!
    
    Next steps:
    1. Make sure your Discord bot is invited to your server
    2. Run the bot: python main.py
    3. Test the bot with: !status
    4. Start learning with: !learn <topic>
    
    Bot Commands:
    - !learn <topic> - Learn about a specific topic
    - !knowledge <query> - Query the knowledge base
    - !status - Show bot status
    - !improve - Trigger self-improvement (owner only)
    
    For help and troubleshooting, check the README.md file.
    
    Happy learning! 🤖✨
    """)

def main():
    """Main setup function"""
    print_banner()
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install dependencies
    if not install_dependencies():
        return False
    
    # Create directories
    if not create_directories():
        return False
    
    # Initialize database
    if not initialize_database():
        return False
    
    # Download NLTK data
    if not download_nltk_data():
        return False
    
    # Configure bot
    configure_bot()
    
    # Test installation
    if not test_installation():
        return False
    
    # Print next steps
    print_next_steps()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n✅ Setup completed successfully!")
        else:
            print("\n❌ Setup failed. Please check the errors above.")
    except KeyboardInterrupt:
        print("\n\n⚠️ Setup interrupted by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error during setup: {e}") 