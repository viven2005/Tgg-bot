import os
from typing import Dict, Any

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_bot_token_here")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID", "123456789")  # Admin's Telegram user ID
DATABASE_PATH = "escrow_bot.db"

# UPI Configuration
UPI_ID = "Shouryahooda751-2@oksbi"
UPI_NAME = "EscrowBot"

# Bot Commands
COMMANDS = {
    "start": "Start the bot",
    "newdeal": "Create a new escrow deal",
    "status": "Check current deal status",
    "contact": "Contact support",
    "help": "Show command list",
    "admin": "Admin panel (admin only)"
}

# Deal Status Constants
DEAL_STATUS = {
    "CREATED": "created",
    "PAYMENT_PENDING": "payment_pending",
    "PAYMENT_CONFIRMED": "payment_confirmed",
    "DELIVERED": "delivered",
    "COMPLETED": "completed",
    "DISPUTED": "disputed",
    "CANCELLED": "cancelled"
}

# Trust Rating Scale
TRUST_RATING_SCALE = {
    1: "⭐",
    2: "⭐⭐",
    3: "⭐⭐⭐",
    4: "⭐⭐⭐⭐",
    5: "⭐⭐⭐⭐⭐"
}

# Support Contact
SUPPORT_CONTACT = "@darx_zerox"

# Animation Messages
ANIMATIONS = {
    "loading": "🔄 Processing payment confirmation...",
    "success": "🎉 Payment confirmed successfully! ✅",
    "waiting": "⏳ Waiting for buyer payment..."
}

# Web server configuration
WEB_HOST = "0.0.0.0"
WEB_PORT = 5000
