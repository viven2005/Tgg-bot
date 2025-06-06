import threading
import asyncio
from bot import EscrowBot
from admin import run_admin_server
import logging

logger = logging.getLogger(__name__)

def run_bot():
    """Run the Telegram bot in an async event loop"""
    try:
        bot = EscrowBot()
        asyncio.run(bot.initialize())
        asyncio.run(bot.start_polling())
    except Exception as e:
        logger.error(f"Bot error: {e}")

def run_web_server():
    """Run the Flask web server"""
    try:
        run_admin_server()
    except Exception as e:
        logger.error(f"Web server error: {e}")

def main():
    """Main function to run both bot and web server"""
    # Configure logging
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    
    logger.info("Starting Escrow Bot with Admin Panel...")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    logger.info("Web server started on http://0.0.0.0:5000")
    
    # Run bot in main thread
    run_bot()

if __name__ == "__main__":
    main()
