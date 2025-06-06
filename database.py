import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import DATABASE_PATH, DEAL_STATUS

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    trust_rating REAL DEFAULT 0.0,
                    total_deals INTEGER DEFAULT 0,
                    successful_deals INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Deals table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS deals (
                    deal_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_a_id INTEGER,
                    party_b_username TEXT,
                    party_b_id INTEGER,
                    amount REAL,
                    description TEXT,
                    status TEXT DEFAULT 'created',
                    payment_confirmed BOOLEAN DEFAULT FALSE,
                    delivery_confirmed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (party_a_id) REFERENCES users (user_id)
                )
            ''')
            
            # Trust ratings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trust_ratings (
                    rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER,
                    rater_id INTEGER,
                    rated_id INTEGER,
                    rating INTEGER,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals (deal_id),
                    FOREIGN KEY (rater_id) REFERENCES users (user_id),
                    FOREIGN KEY (rated_id) REFERENCES users (user_id)
                )
            ''')
            
            # Disputes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS disputes (
                    dispute_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER,
                    raised_by INTEGER,
                    reason TEXT,
                    status TEXT DEFAULT 'open',
                    resolved_by INTEGER,
                    resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    FOREIGN KEY (deal_id) REFERENCES deals (deal_id),
                    FOREIGN KEY (raised_by) REFERENCES users (user_id)
                )
            ''')
            
            conn.commit()
    
    def add_user(self, user_id: int, username: str, first_name: str, last_name: str = None) -> bool:
        """Add a new user or update existing user info"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO users 
                    (user_id, username, first_name, last_name, created_at)
                    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, username, first_name, last_name))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False
    
    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting user: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information by username"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting user by username: {e}")
            return None
    
    def create_deal(self, party_a_id: int, party_b_username: str, amount: float, description: str) -> Optional[int]:
        """Create a new deal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO deals (party_a_id, party_b_username, amount, description, status)
                    VALUES (?, ?, ?, ?, ?)
                ''', (party_a_id, party_b_username, amount, description, DEAL_STATUS["CREATED"]))
                deal_id = cursor.lastrowid
                conn.commit()
                return deal_id
        except Exception as e:
            print(f"Error creating deal: {e}")
            return None
    
    def get_deal(self, deal_id: int) -> Optional[Dict[str, Any]]:
        """Get deal information"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM deals WHERE deal_id = ?', (deal_id,))
                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"Error getting deal: {e}")
            return None
    
    def get_user_deals(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all deals for a user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM deals 
                    WHERE party_a_id = ? OR party_b_id = ?
                    ORDER BY created_at DESC
                ''', (user_id, user_id))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting user deals: {e}")
            return []
    
    def update_deal_status(self, deal_id: int, status: str) -> bool:
        """Update deal status"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE deals 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE deal_id = ?
                ''', (status, deal_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error updating deal status: {e}")
            return False
    
    def confirm_payment(self, deal_id: int) -> bool:
        """Confirm payment for a deal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE deals 
                    SET payment_confirmed = TRUE, 
                        status = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE deal_id = ?
                ''', (DEAL_STATUS["PAYMENT_CONFIRMED"], deal_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error confirming payment: {e}")
            return False
    
    def confirm_delivery(self, deal_id: int) -> bool:
        """Confirm delivery for a deal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE deals 
                    SET delivery_confirmed = TRUE, 
                        status = ?, 
                        updated_at = CURRENT_TIMESTAMP
                    WHERE deal_id = ?
                ''', (DEAL_STATUS["DELIVERED"], deal_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"Error confirming delivery: {e}")
            return False
    
    def create_dispute(self, deal_id: int, raised_by: int, reason: str) -> Optional[int]:
        """Create a dispute for a deal"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO disputes (deal_id, raised_by, reason)
                    VALUES (?, ?, ?)
                ''', (deal_id, raised_by, reason))
                dispute_id = cursor.lastrowid
                
                # Update deal status to disputed
                cursor.execute('''
                    UPDATE deals 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE deal_id = ?
                ''', (DEAL_STATUS["DISPUTED"], deal_id))
                
                conn.commit()
                return dispute_id
        except Exception as e:
            print(f"Error creating dispute: {e}")
            return None
    
    def add_trust_rating(self, deal_id: int, rater_id: int, rated_id: int, rating: int, comment: str = None) -> bool:
        """Add a trust rating"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO trust_ratings (deal_id, rater_id, rated_id, rating, comment)
                    VALUES (?, ?, ?, ?, ?)
                ''', (deal_id, rater_id, rated_id, rating, comment))
                
                # Update user's trust rating
                cursor.execute('''
                    SELECT AVG(rating) as avg_rating, COUNT(*) as total_ratings
                    FROM trust_ratings 
                    WHERE rated_id = ?
                ''', (rated_id,))
                result = cursor.fetchone()
                avg_rating, total_ratings = result
                
                cursor.execute('''
                    UPDATE users 
                    SET trust_rating = ?
                    WHERE user_id = ?
                ''', (avg_rating, rated_id))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Error adding trust rating: {e}")
            return False
    
    def get_pending_confirmations(self) -> List[Dict[str, Any]]:
        """Get deals pending payment confirmation"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM deals 
                    WHERE status = ? 
                    ORDER BY created_at ASC
                ''', (DEAL_STATUS["PAYMENT_PENDING"],))
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting pending confirmations: {e}")
            return []
    
    def get_open_disputes(self) -> List[Dict[str, Any]]:
        """Get open disputes"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT d.*, deals.amount, deals.description, u.username as raised_by_username
                    FROM disputes d
                    JOIN deals ON d.deal_id = deals.deal_id
                    JOIN users u ON d.raised_by = u.user_id
                    WHERE d.status = 'open'
                    ORDER BY d.created_at ASC
                ''')
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"Error getting open disputes: {e}")
            return []
