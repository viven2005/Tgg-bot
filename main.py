#!/usr/bin/env python3
"""
Escrow Telegram Bot - Main Entry Point

A secure escrow bot for Telegram that facilitates safe transactions
between parties using UPI payments and manual confirmation.

Features:
- User registration and deal creation
- UPI QR code generation for payments
- Manual payment confirmation system
- Deal status tracking and management
- Trust rating system
- Dispute handling
- Admin panel for management

Author: Escrow Bot Team
"""

import os
import sys
import logging
import signal
import asyncio
import threading
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from config import BOT_TOKEN, WEB_HOST, WEB_PORT
from bot import EscrowBot
from admin import run_admin_server
from database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('escrow_bot.log')
    ]
)

logger = logging.getLogger(__name__)

class EscrowBotApplication:
    """Main application class for the Escrow Bot"""
    
    def __init__(self):
        self.bot = None
        self.web_thread = None
        self.running = False
        
        # Validate configuration
        self.validate_config()
        
        # Initialize database
        self.init_database()
    
    def validate_config(self):
        """Validate required configuration"""
        if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
            logger.error("BOT_TOKEN environment variable is not set or invalid!")
            logger.error("Please set BOT_TOKEN environment variable with your Telegram bot token")
            sys.exit(1)
        
        logger.info("Configuration validated successfully")
    
    def init_database(self):
        """Initialize the database"""
        try:
            db = Database()
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            sys.exit(1)
    
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start_web_server(self):
        """Start the web server in a separate thread"""
        def run_web():
            try:
                logger.info(f"Starting admin web server on {WEB_HOST}:{WEB_PORT}")
                run_admin_server()
            except Exception as e:
                logger.error(f"Web server error: {e}")
        
        self.web_thread = threading.Thread(target=run_web, daemon=True)
        self.web_thread.start()
        logger.info(f"Admin panel available at http://{WEB_HOST}:{WEB_PORT}/admin")
    
    async def start_bot(self):
        """Start the Telegram bot"""
        try:
            self.bot = EscrowBot()
            
            if await self.bot.initialize():
                logger.info("Starting Telegram bot...")
                self.running = True
                await self.bot.start_polling()
            else:
                logger.error("Failed to initialize bot")
                return False
                
        except Exception as e:
            logger.error(f"Bot startup error: {e}")
            return False
        finally:
            await self.stop_bot()
    
    async def stop_bot(self):
        """Stop the Telegram bot"""
        if self.bot:
            await self.bot.stop()
            self.bot = None
    
    def stop(self):
        """Stop the entire application"""
        self.running = False
        logger.info("Application stopping...")
    
    def run(self):
        """Run the complete application"""
        try:
            logger.info("=" * 50)
            logger.info("🛡️  ESCROW TELEGRAM BOT")
            logger.info("=" * 50)
            logger.info("Starting Escrow Bot application...")
            
            # Setup signal handlers
            self.setup_signal_handlers()
            
            # Start web server
            self.start_web_server()
            
            # Display startup information
            self.display_startup_info()
            
            # Start bot (this will block until shutdown)
            asyncio.run(self.start_bot())
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Application error: {e}")
            sys.exit(1)
        finally:
            self.stop()
            logger.info("Application stopped")
    
    def display_startup_info(self):
        """Display startup information"""
        logger.info("=" * 50)
        logger.info("🚀 APPLICATION STARTED SUCCESSFULLY")
        logger.info("=" * 50)
        logger.info(f"📱 Telegram Bot: Active")
        logger.info(f"🌐 Admin Panel: http://{WEB_HOST}:{WEB_PORT}/admin")
        logger.info(f"💾 Database: SQLite (escrow_bot.db)")
        logger.info(f"💳 UPI ID: Shouryahooda751-2@oksbi")
        logger.info("=" * 50)
        logger.info("Bot is ready to accept commands!")
        logger.info("Use /start in Telegram to begin")
        logger.info("=" * 50)

def main():
    """Main entry point"""
    try:
        app = EscrowBotApplication()
        app.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
