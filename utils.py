import qrcode
import io
import base64
from PIL import Image
from typing import Optional
from config import UPI_ID, UPI_NAME

def generate_upi_qr(amount: float, deal_id: int) -> bytes:
    """Generate UPI QR code for payment"""
    try:
        # Create UPI payment link
        upi_link = f"upi://pay?pa={UPI_ID}&pn={UPI_NAME}&am={amount}&tn=Escrow Deal {deal_id}"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_link)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer.getvalue()
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return None

def format_amount(amount: float) -> str:
    """Format amount for display"""
    return f"₹{amount:,.2f}"

def format_deal_info(deal: dict) -> str:
    """Format deal information for display"""
    status_emoji = {
        "created": "🆕",
        "payment_pending": "⏳",
        "payment_confirmed": "✅",
        "delivered": "📦",
        "completed": "🎉",
        "disputed": "⚠️",
        "cancelled": "❌"
    }
    
    emoji = status_emoji.get(deal['status'], "❓")
    amount = format_amount(deal['amount'])
    
    return f"""
{emoji} **Deal #{deal['deal_id']}**
Amount: {amount}
Party B: @{deal['party_b_username']}
Status: {deal['status'].replace('_', ' ').title()}
Description: {deal['description'][:100]}{'...' if len(deal['description']) > 100 else ''}
"""

def validate_username(username: str) -> bool:
    """Validate Telegram username format"""
    if not username:
        return False
    
    # Remove @ if present
    username = username.lstrip('@')
    
    # Check length (5-32 characters)
    if len(username) < 5 or len(username) > 32:
        return False
    
    # Check for valid characters (alphanumeric and underscores)
    if not username.replace('_', '').isalnum():
        return False
    
    return True

def validate_amount(amount_str: str) -> Optional[float]:
    """Validate and parse amount"""
    try:
        amount = float(amount_str)
        if amount <= 0:
            return None
        if amount > 100000:  # Max amount limit
            return None
        return round(amount, 2)
    except ValueError:
        return None

def get_trust_rating_display(rating: float, total_deals: int) -> str:
    """Get formatted trust rating display"""
    if total_deals == 0:
        return "New User (No ratings yet)"
    
    stars = "⭐" * int(rating)
    return f"{stars} {rating:.1f}/5.0 ({total_deals} deals)"

def create_payment_keyboard():
    """Create payment confirmation keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("💳 Payment Done", callback_data="payment_done")],
        [InlineKeyboardButton("❌ Cancel Deal", callback_data="cancel_deal")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_delivery_keyboard():
    """Create delivery confirmation keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Delivery", callback_data="confirm_delivery")],
        [InlineKeyboardButton("🚨 Raise Dispute", callback_data="raise_dispute")]
    ]
    return InlineKeyboardMarkup(keyboard)

def create_rating_keyboard():
    """Create trust rating keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = []
    for i in range(1, 6):
        stars = "⭐" * i
        keyboard.append([InlineKeyboardButton(f"{stars} {i}/5", callback_data=f"rate_{i}")])
    
    return InlineKeyboardMarkup(keyboard)

def create_admin_keyboard():
    """Create admin action keyboard"""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("✅ Confirm Payment", callback_data="admin_confirm")],
        [InlineKeyboardButton("❌ Reject Payment", callback_data="admin_reject")],
        [InlineKeyboardButton("📊 View Details", callback_data="admin_details")]
    ]
    return InlineKeyboardMarkup(keyboard)
