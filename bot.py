import logging
import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters
)
from config import BOT_TOKEN
from handlers import (
    start_command, help_command, contact_command, newdeal_command,
    status_command, admin_command, handle_message, handle_callback_query,
    error_handler
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class EscrowBot:
    def __init__(self):
        self.application = None
    
    def setup_handlers(self):
        """Setup all command and message handlers"""
        app = self.application
        
        # Command handlers
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(CommandHandler("contact", contact_command))
        app.add_handler(CommandHandler("newdeal", newdeal_command))
        app.add_handler(CommandHandler("status", status_command))
        app.add_handler(CommandHandler("admin", admin_command))
        
        # Callback query handler for inline keyboards
        app.add_handler(CallbackQueryHandler(handle_callback_query))
        
        # Message handler for text messages
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Error handler
        app.add_error_handler(error_handler)
    
    async def initialize(self):
        """Initialize the bot application"""
        try:
            # Create application
            self.application = Application.builder().token(BOT_TOKEN).build()
            
            # Setup handlers
            self.setup_handlers()
            
            # Initialize the application
            await self.application.initialize()
            
            logger.info("Bot initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            return False
    
    async def start_polling(self):
        """Start the bot with polling"""
        try:
            await self.application.start()
            await self.application.updater.start_polling(
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES
            )
            
            logger.info("Bot started and polling for updates...")
            
            # Keep the bot running
            await self.application.updater.idle()
            
        except Exception as e:
            logger.error(f"Error during polling: {e}")
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the bot gracefully"""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")

async def main():
    """Main function to run the bot"""
    bot = EscrowBot()
    
    if await bot.initialize():
        try:
            await bot.start_polling()
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, stopping bot...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        finally:
            await bot.stop()
    else:
        logger.error("Failed to initialize bot")

if __name__ == "__main__":
    asyncio.run(main())
