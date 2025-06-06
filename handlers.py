import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import Database
from utils import (
    generate_upi_qr, format_amount, format_deal_info, 
    validate_username, validate_amount, get_trust_rating_display,
    create_payment_keyboard, create_delivery_keyboard, create_rating_keyboard
)
from config import COMMANDS, DEAL_STATUS, SUPPORT_CONTACT, ANIMATIONS, ADMIN_USER_ID

# Initialize database
db = Database()

# User state tracking
user_states = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Add user to database
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    welcome_message = f"""
🛡️ **Welcome to Escrow Bot!**

Hello {user.first_name}! I'm here to help you conduct secure transactions.

**What I can do:**
• Create secure escrow deals
• Handle UPI payments safely
• Track deal status
• Manage disputes
• Trust rating system

**Available Commands:**
/newdeal - Create a new escrow deal
/status - Check your current deals
/contact - Get support
/help - Show all commands

Ready to start your first deal? Use /newdeal to begin! 🚀
"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = "🤖 **Escrow Bot Commands:**\n\n"
    
    for command, description in COMMANDS.items():
        help_text += f"/{command} - {description}\n"
    
    help_text += f"\n📞 **Need Help?**\nContact: {SUPPORT_CONTACT}"
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def contact_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /contact command"""
    contact_message = f"""
📞 **Support Contact**

If you face any issues or need assistance, please contact:
{SUPPORT_CONTACT}

**Common Issues:**
• Payment not reflecting
• Dispute resolution
• Technical problems
• Account verification

Our support team will assist you promptly! 🙋‍♂️
"""
    
    await update.message.reply_text(contact_message, parse_mode='Markdown')

async def newdeal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newdeal command"""
    user_id = update.effective_user.id
    
    # Check if user exists in database
    user = db.get_user(user_id)
    if not user:
        await update.message.reply_text("❌ Please start the bot first using /start")
        return
    
    # Set user state for deal creation
    user_states[user_id] = {"state": "waiting_amount"}
    
    await update.message.reply_text(
        "💰 **Create New Escrow Deal**\n\n"
        "Please enter the deal amount (in ₹):\n"
        "Example: 500 or 1500.50",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command"""
    user_id = update.effective_user.id
    
    deals = db.get_user_deals(user_id)
    
    if not deals:
        await update.message.reply_text(
            "📭 **No Deals Found**\n\n"
            "You don't have any deals yet. Create your first deal with /newdeal!"
        )
        return
    
    status_message = "📊 **Your Deals:**\n\n"
    
    for deal in deals[:5]:  # Show last 5 deals
        status_message += format_deal_info(deal) + "\n"
    
    if len(deals) > 5:
        status_message += f"\n... and {len(deals) - 5} more deals"
    
    await update.message.reply_text(status_message, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages based on user state"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if user_id not in user_states:
        await update.message.reply_text(
            "❓ I don't understand. Use /help to see available commands."
        )
        return
    
    state_data = user_states[user_id]
    current_state = state_data["state"]
    
    if current_state == "waiting_amount":
        await handle_amount_input(update, context, message_text)
    elif current_state == "waiting_counterparty":
        await handle_counterparty_input(update, context, message_text)
    elif current_state == "waiting_description":
        await handle_description_input(update, context, message_text)
    elif current_state == "waiting_dispute_reason":
        await handle_dispute_reason(update, context, message_text)
    else:
        await update.message.reply_text(
            "❓ Unknown state. Please start over with /newdeal"
        )
        user_states.pop(user_id, None)

async def handle_amount_input(update: Update, context: ContextTypes.DEFAULT_TYPE, amount_str: str):
    """Handle amount input for new deal"""
    user_id = update.effective_user.id
    
    amount = validate_amount(amount_str)
    if amount is None:
        await update.message.reply_text(
            "❌ **Invalid Amount**\n\n"
            "Please enter a valid amount between ₹1 and ₹1,00,000\n"
            "Example: 500 or 1500.50"
        )
        return
    
    # Update state
    user_states[user_id]["amount"] = amount
    user_states[user_id]["state"] = "waiting_counterparty"
    
    await update.message.reply_text(
        f"✅ Amount set: {format_amount(amount)}\n\n"
        "👤 **Enter the other party's username:**\n"
        "Example: @john_doe or john_doe",
        parse_mode='Markdown'
    )

async def handle_counterparty_input(update: Update, context: ContextTypes.DEFAULT_TYPE, username: str):
    """Handle counterparty username input"""
    user_id = update.effective_user.id
    
    # Clean username
    username = username.lstrip('@').lower()
    
    if not validate_username(username):
        await update.message.reply_text(
            "❌ **Invalid Username**\n\n"
            "Please enter a valid Telegram username (5-32 characters, letters, numbers, and underscores only)\n"
            "Example: @john_doe or john_doe"
        )
        return
    
    # Check if it's not the same user
    current_user = db.get_user(user_id)
    if current_user and current_user['username'] and current_user['username'].lower() == username:
        await update.message.reply_text(
            "❌ **Invalid Counterparty**\n\n"
            "You cannot create a deal with yourself!"
        )
        return
    
    # Update state
    user_states[user_id]["counterparty"] = username
    user_states[user_id]["state"] = "waiting_description"
    
    await update.message.reply_text(
        f"✅ Counterparty set: @{username}\n\n"
        "📝 **Enter deal description:**\n"
        "Briefly describe what you're buying/selling",
        parse_mode='Markdown'
    )

async def handle_description_input(update: Update, context: ContextTypes.DEFAULT_TYPE, description: str):
    """Handle description input and create deal"""
    user_id = update.effective_user.id
    state_data = user_states[user_id]
    
    if len(description.strip()) < 10:
        await update.message.reply_text(
            "❌ **Description too short**\n\n"
            "Please provide a description of at least 10 characters"
        )
        return
    
    # Create deal
    deal_id = db.create_deal(
        party_a_id=user_id,
        party_b_username=state_data["counterparty"],
        amount=state_data["amount"],
        description=description.strip()
    )
    
    if not deal_id:
        await update.message.reply_text(
            "❌ **Error creating deal**\n\n"
            "Please try again or contact support"
        )
        user_states.pop(user_id, None)
        return
    
    # Update deal status to payment pending
    db.update_deal_status(deal_id, DEAL_STATUS["PAYMENT_PENDING"])
    
    # Generate QR code
    qr_bytes = generate_upi_qr(state_data["amount"], deal_id)
    
    deal_summary = f"""
🎯 **Deal Created Successfully!**

**Deal ID:** #{deal_id}
**Amount:** {format_amount(state_data["amount"])}
**Counterparty:** @{state_data["counterparty"]}
**Description:** {description}

💳 **Payment Instructions:**
1. Scan the QR code below OR
2. Pay to UPI ID: `{db.UPI_ID}`
3. Click "Payment Done" after payment

⚠️ **Important:** Only proceed with payment if you trust the counterparty!
"""
    
    keyboard = create_payment_keyboard()
    
    # Send deal summary
    await update.message.reply_text(deal_summary, parse_mode='Markdown')
    
    # Send QR code
    if qr_bytes:
        await update.message.reply_photo(
            photo=qr_bytes,
            caption=f"💳 **Scan to Pay {format_amount(state_data['amount'])}**\n\nDeal ID: #{deal_id}",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            f"📱 **Manual Payment**\n\nUPI ID: `{db.UPI_ID}`\nAmount: {format_amount(state_data['amount'])}",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    
    # Clear user state
    user_states.pop(user_id, None)

async def handle_dispute_reason(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str):
    """Handle dispute reason input"""
    user_id = update.effective_user.id
    state_data = user_states[user_id]
    
    if len(reason.strip()) < 10:
        await update.message.reply_text(
            "❌ **Reason too short**\n\n"
            "Please provide a detailed reason (at least 10 characters)"
        )
        return
    
    deal_id = state_data["deal_id"]
    
    # Create dispute
    dispute_id = db.create_dispute(deal_id, user_id, reason.strip())
    
    if dispute_id:
        await update.message.reply_text(
            f"🚨 **Dispute Created**\n\n"
            f"Dispute ID: #{dispute_id}\n"
            f"Deal ID: #{deal_id}\n\n"
            f"Our support team will review your dispute and contact you soon.\n\n"
            f"Contact: {SUPPORT_CONTACT}",
            parse_mode='Markdown'
        )
        
        # Notify admin (if different from user)
        if str(user_id) != ADMIN_USER_ID:
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_USER_ID,
                    text=f"🚨 **New Dispute**\n\nDispute ID: #{dispute_id}\nDeal ID: #{deal_id}\nRaised by: {update.effective_user.username or update.effective_user.first_name}\nReason: {reason}",
                    parse_mode='Markdown'
                )
            except:
                pass  # Admin notification failed, continue
    else:
        await update.message.reply_text(
            "❌ **Error creating dispute**\n\n"
            "Please try again or contact support directly"
        )
    
    # Clear user state
    user_states.pop(user_id, None)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline keyboard callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "payment_done":
        await handle_payment_done(update, context)
    elif data == "cancel_deal":
        await handle_cancel_deal(update, context)
    elif data == "confirm_delivery":
        await handle_confirm_delivery(update, context)
    elif data == "raise_dispute":
        await handle_raise_dispute_button(update, context)
    elif data.startswith("rate_"):
        rating = int(data.split("_")[1])
        await handle_trust_rating(update, context, rating)
    elif data.startswith("admin_"):
        await handle_admin_action(update, context, data)

async def handle_payment_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment done button"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Show loading animation
    await query.edit_message_caption(
        caption=f"{ANIMATIONS['loading']}\n\nPlease wait while we verify your payment...",
        parse_mode='Markdown'
    )
    
    # Notify admin for manual confirmation
    try:
        # Get the latest deal for this user
        deals = db.get_user_deals(user_id)
        if deals:
            latest_deal = deals[0]
            
            admin_message = f"""
🔔 **Payment Confirmation Required**

**Deal ID:** #{latest_deal['deal_id']}
**Amount:** {format_amount(latest_deal['amount'])}
**Payer:** @{query.from_user.username or query.from_user.first_name}
**Description:** {latest_deal['description']}

Please verify the payment and confirm below:
"""
            
            keyboard = InlineKeyboardButton("✅ Confirm Payment", callback_data=f"admin_confirm_{latest_deal['deal_id']}")
            admin_keyboard = InlineKeyboardMarkup([[keyboard]])
            
            await context.bot.send_message(
                chat_id=ADMIN_USER_ID,
                text=admin_message,
                reply_markup=admin_keyboard,
                parse_mode='Markdown'
            )
            
            await query.edit_message_caption(
                caption=f"{ANIMATIONS['waiting']}\n\nYour payment notification has been sent to our team. You'll be notified once confirmed!",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_caption(
                caption="❌ No active deal found. Please create a new deal.",
                parse_mode='Markdown'
            )
    except Exception as e:
        logging.error(f"Error in payment done handler: {e}")
        await query.edit_message_caption(
            caption="❌ Error processing payment confirmation. Please contact support.",
            parse_mode='Markdown'
        )

async def handle_admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE, action_data: str):
    """Handle admin actions"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Check if user is admin
    if str(user_id) != ADMIN_USER_ID:
        await query.answer("❌ Unauthorized access", show_alert=True)
        return
    
    if action_data.startswith("admin_confirm_"):
        deal_id = int(action_data.split("_")[2])
        
        # Confirm payment
        if db.confirm_payment(deal_id):
            deal = db.get_deal(deal_id)
            
            await query.edit_message_text(
                text=f"✅ **Payment Confirmed**\n\nDeal #{deal_id} payment has been confirmed and funds are now in escrow.",
                parse_mode='Markdown'
            )
            
            # Notify buyer
            try:
                success_message = f"""
{ANIMATIONS['success']}

**Deal #{deal_id}** payment confirmed! 
Funds are now safely held in escrow.

💡 **Next Steps:**
• Wait for delivery from @{deal['party_b_username']}
• Once delivered, use the buttons below to proceed

**What happens next?**
• Seller will be notified
• After delivery, confirm to release payment
• Rate your experience
"""
                
                delivery_keyboard = create_delivery_keyboard()
                
                await context.bot.send_message(
                    chat_id=deal['party_a_id'],
                    text=success_message,
                    reply_markup=delivery_keyboard,
                    parse_mode='Markdown'
                )
                
                # Notify seller if we have their user ID
                if deal['party_b_id']:
                    seller_message = f"""
🔔 **New Escrow Deal for You!**

**Deal ID:** #{deal['deal_id']}
**Amount:** {format_amount(deal['amount'])}
**Buyer:** @{db.get_user(deal['party_a_id'])['username'] or 'Unknown'}
**Description:** {deal['description']}

💰 Payment has been confirmed and is safely held in escrow!
Proceed with delivery as agreed.

Contact buyer for coordination: @{db.get_user(deal['party_a_id'])['username'] or 'Unknown'}
"""
                    
                    await context.bot.send_message(
                        chat_id=deal['party_b_id'],
                        text=seller_message,
                        parse_mode='Markdown'
                    )
            except Exception as e:
                logging.error(f"Error notifying parties: {e}")
        else:
            await query.answer("❌ Error confirming payment", show_alert=True)

async def handle_confirm_delivery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle delivery confirmation"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get latest deal for this user
    deals = db.get_user_deals(user_id)
    if not deals:
        await query.answer("❌ No deals found", show_alert=True)
        return
    
    latest_deal = deals[0]
    
    if latest_deal['status'] != DEAL_STATUS["PAYMENT_CONFIRMED"]:
        await query.answer("❌ Invalid deal status", show_alert=True)
        return
    
    # Confirm delivery
    if db.confirm_delivery(latest_deal['deal_id']):
        await query.edit_message_text(
            text=f"✅ **Delivery Confirmed!**\n\nDeal #{latest_deal['deal_id']} has been marked as delivered.\n\nPlease rate your experience:",
            reply_markup=create_rating_keyboard(),
            parse_mode='Markdown'
        )
    else:
        await query.answer("❌ Error confirming delivery", show_alert=True)

async def handle_raise_dispute_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle raise dispute button"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get latest deal for this user
    deals = db.get_user_deals(user_id)
    if not deals:
        await query.answer("❌ No deals found", show_alert=True)
        return
    
    latest_deal = deals[0]
    
    # Set user state for dispute creation
    user_states[user_id] = {
        "state": "waiting_dispute_reason",
        "deal_id": latest_deal['deal_id']
    }
    
    await query.edit_message_text(
        text=f"🚨 **Raising Dispute for Deal #{latest_deal['deal_id']}**\n\nPlease describe the issue in detail:",
        parse_mode='Markdown'
    )

async def handle_trust_rating(update: Update, context: ContextTypes.DEFAULT_TYPE, rating: int):
    """Handle trust rating submission"""
    query = update.callback_query
    user_id = query.from_user.id
    
    # Get latest deal for this user
    deals = db.get_user_deals(user_id)
    if not deals:
        await query.answer("❌ No deals found", show_alert=True)
        return
    
    latest_deal = deals[0]
    
    # Determine who to rate (the other party)
    if latest_deal['party_a_id'] == user_id:
        # Rating party B
        rated_user = db.get_user_by_username(latest_deal['party_b_username'])
        if rated_user:
            rated_id = rated_user['user_id']
        else:
            await query.answer("❌ Cannot find counterparty", show_alert=True)
            return
    else:
        # Rating party A
        rated_id = latest_deal['party_a_id']
    
    # Add trust rating
    if db.add_trust_rating(latest_deal['deal_id'], user_id, rated_id, rating):
        # Complete the deal
        db.update_deal_status(latest_deal['deal_id'], DEAL_STATUS["COMPLETED"])
        
        stars = "⭐" * rating
        await query.edit_message_text(
            text=f"🎉 **Deal Completed!**\n\nThank you for rating: {stars} {rating}/5\n\nDeal #{latest_deal['deal_id']} is now complete!",
            parse_mode='Markdown'
        )
        
        # Notify the other party about completion
        try:
            other_party_id = rated_id
            completion_message = f"""
🎉 **Deal Completed!**

Deal #{latest_deal['deal_id']} has been completed successfully!
You received a {stars} {rating}/5 rating.

Thank you for using Escrow Bot! 🤝
"""
            
            await context.bot.send_message(
                chat_id=other_party_id,
                text=completion_message,
                parse_mode='Markdown'
            )
        except:
            pass  # Notification failed, but deal is still complete
    else:
        await query.answer("❌ Error submitting rating", show_alert=True)

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - admin only"""
    user_id = update.effective_user.id
    
    if str(user_id) != ADMIN_USER_ID:
        await update.message.reply_text("❌ Unauthorized access")
        return
    
    # Get pending confirmations and disputes
    pending_payments = db.get_pending_confirmations()
    open_disputes = db.get_open_disputes()
    
    admin_message = f"""
🔧 **Admin Panel**

**Pending Payment Confirmations:** {len(pending_payments)}
**Open Disputes:** {len(open_disputes)}

**Quick Actions:**
• View pending payments: /admin_payments
• View disputes: /admin_disputes
• View web panel: http://localhost:5000/admin

**System Status:** ✅ Active
"""
    
    await update.message.reply_text(admin_message, parse_mode='Markdown')

# Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logging.error(f"Exception while handling an update: {context.error}")
    
    if update and hasattr(update, 'effective_message'):
        try:
            await update.effective_message.reply_text(
                "❌ An error occurred. Please try again or contact support."
            )
        except:
            pass
