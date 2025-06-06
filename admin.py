from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
from database import Database
from utils import format_amount, get_trust_rating_display
from config import DATABASE_PATH, DEAL_STATUS, WEB_HOST, WEB_PORT

app = Flask(__name__)
db = Database()

@app.route('/')
def index():
    """Admin dashboard home"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    """Main admin dashboard"""
    # Get statistics
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Total users
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Total deals
        cursor.execute("SELECT COUNT(*) FROM deals")
        total_deals = cursor.fetchone()[0]
        
        # Pending payments
        cursor.execute("SELECT COUNT(*) FROM deals WHERE status = ?", (DEAL_STATUS["PAYMENT_PENDING"],))
        pending_payments = cursor.fetchone()[0]
        
        # Open disputes
        cursor.execute("SELECT COUNT(*) FROM disputes WHERE status = 'open'")
        open_disputes = cursor.fetchone()[0]
        
        # Recent deals
        cursor.execute("""
            SELECT d.*, u.username as party_a_username 
            FROM deals d 
            JOIN users u ON d.party_a_id = u.user_id 
            ORDER BY d.created_at DESC 
            LIMIT 10
        """)
        recent_deals = cursor.fetchall()
    
    stats = {
        'total_users': total_users,
        'total_deals': total_deals,
        'pending_payments': pending_payments,
        'open_disputes': open_disputes
    }
    
    return render_template('admin.html', stats=stats, recent_deals=recent_deals, format_amount=format_amount)

@app.route('/admin/deals')
def admin_deals():
    """View all deals"""
    status_filter = request.args.get('status', 'all')
    
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        if status_filter == 'all':
            cursor.execute("""
                SELECT d.*, u.username as party_a_username 
                FROM deals d 
                JOIN users u ON d.party_a_id = u.user_id 
                ORDER BY d.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT d.*, u.username as party_a_username 
                FROM deals d 
                JOIN users u ON d.party_a_id = u.user_id 
                WHERE d.status = ?
                ORDER BY d.created_at DESC
            """, (status_filter,))
        
        deals = cursor.fetchall()
    
    return render_template('admin.html', deals=deals, status_filter=status_filter, format_amount=format_amount)

@app.route('/admin/users')
def admin_users():
    """View all users"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.*, 
                   COUNT(d.deal_id) as total_deals,
                   COUNT(CASE WHEN d.status = 'completed' THEN 1 END) as completed_deals
            FROM users u 
            LEFT JOIN deals d ON (u.user_id = d.party_a_id OR u.user_id = d.party_b_id)
            GROUP BY u.user_id
            ORDER BY u.created_at DESC
        """)
        users = cursor.fetchall()
    
    return render_template('admin.html', users=users, get_trust_rating_display=get_trust_rating_display)

@app.route('/admin/disputes')
def admin_disputes():
    """View all disputes"""
    disputes = db.get_open_disputes()
    return render_template('admin.html', disputes=disputes, format_amount=format_amount)

@app.route('/admin/pending')
def admin_pending():
    """View pending payment confirmations"""
    pending_deals = db.get_pending_confirmations()
    return render_template('admin.html', pending_deals=pending_deals, format_amount=format_amount)

@app.route('/admin/api/confirm_payment/<int:deal_id>', methods=['POST'])
def api_confirm_payment(deal_id):
    """API endpoint to confirm payment"""
    try:
        if db.confirm_payment(deal_id):
            return jsonify({'success': True, 'message': 'Payment confirmed successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to confirm payment'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/api/reject_payment/<int:deal_id>', methods=['POST'])
def api_reject_payment(deal_id):
    """API endpoint to reject payment"""
    try:
        if db.update_deal_status(deal_id, DEAL_STATUS["CANCELLED"]):
            return jsonify({'success': True, 'message': 'Payment rejected and deal cancelled'})
        else:
            return jsonify({'success': False, 'message': 'Failed to reject payment'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/api/resolve_dispute/<int:dispute_id>', methods=['POST'])
def api_resolve_dispute(dispute_id):
    """API endpoint to resolve dispute"""
    resolution = request.json.get('resolution', '')
    
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE disputes 
                SET status = 'resolved', resolution = ?, resolved_at = CURRENT_TIMESTAMP
                WHERE dispute_id = ?
            """, (resolution, dispute_id))
            conn.commit()
            
            if cursor.rowcount > 0:
                return jsonify({'success': True, 'message': 'Dispute resolved successfully'})
            else:
                return jsonify({'success': False, 'message': 'Dispute not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

def run_admin_server():
    """Run the admin web server"""
    app.run(host=WEB_HOST, port=WEB_PORT, debug=False)

if __name__ == '__main__':
    run_admin_server()
