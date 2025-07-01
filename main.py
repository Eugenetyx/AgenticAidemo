#!/usr/bin/env python3
"""
Property Management System
Main application entry point
"""

import sqlite3
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import json

class DatabaseManager:
    """Handles all database operations"""

    def __init__(self, db_path: str = 'database.db'):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        """Get database connection with foreign keys enabled"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def init_database(self):
        """Initialize database with schema and sample data"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Execute the schema
        cursor.executescript("""
        -- drop old tables if they exist
        DROP TABLE IF EXISTS ticket_conversations;
        DROP TABLE IF EXISTS ticket_comments;
        DROP TABLE IF EXISTS service_tickets;
        DROP TABLE IF EXISTS payments;
        DROP TABLE IF EXISTS leases;
        DROP TABLE IF EXISTS units;
        DROP TABLE IF EXISTS agents;
        DROP TABLE IF EXISTS properties;
        DROP TABLE IF EXISTS tenants;

        -- tenants
        CREATE TABLE tenants (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            first_name      TEXT    NOT NULL,
            last_name       TEXT    NOT NULL,
            email           TEXT    UNIQUE NOT NULL,
            phone           TEXT,
            date_of_birth   TEXT,
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- properties
        CREATE TABLE properties (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            name            TEXT    NOT NULL,
            address_line1   TEXT    NOT NULL,
            address_line2   TEXT,
            city            TEXT    NOT NULL,
            state           TEXT,
            postal_code     TEXT,
            country         TEXT    NOT NULL,
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- units
        CREATE TABLE units (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            property_id     INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
            unit_number     TEXT    NOT NULL,
            floor           TEXT,
            bedrooms        INTEGER,
            bathrooms       REAL,
            square_feet     INTEGER,
            status          TEXT    DEFAULT 'available',
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- leases
        CREATE TABLE leases (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            tenant_id       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            unit_id         INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
            start_date      DATETIME NOT NULL,
            end_date        DATETIME NOT NULL,
            rent_amount     REAL    NOT NULL,
            security_deposit REAL,
            status          TEXT    DEFAULT 'active',
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- agents
        CREATE TABLE agents (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            first_name      TEXT,
            last_name       TEXT,
            role            TEXT,
            email           TEXT    UNIQUE,
            phone           TEXT,
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- service tickets
        CREATE TABLE service_tickets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            lease_id        INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
            raised_by       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE SET NULL,
            assigned_to     INTEGER REFERENCES agents(id) ON DELETE SET NULL,
            category        TEXT    NOT NULL,
            subcategory     TEXT,
            description     TEXT    NOT NULL,
            status          TEXT    DEFAULT 'open',
            priority        TEXT    DEFAULT 'normal',
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            updated_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- ticket comments
        CREATE TABLE ticket_comments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            ticket_id       INTEGER NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
            author_id       INTEGER NOT NULL,
            author_type     TEXT    NOT NULL,
            comment_text    TEXT    NOT NULL,
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- payments
        CREATE TABLE payments (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            lease_id        INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
            payment_type    TEXT    NOT NULL,
            billing_period  TEXT,
            due_date        DATETIME,
            amount          REAL    NOT NULL,
            method          TEXT,
            paid_on         DATETIME,
            reference_number TEXT,
            created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );

        -- ticket conversations
        CREATE TABLE ticket_conversations (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
            ticket_id       INTEGER NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
            author_type     TEXT    NOT NULL,
            author_id       INTEGER NOT NULL,
            message_text    TEXT    NOT NULL,
            sent_at         DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
        );
        """)

        # Insert sample data
        cursor.executescript("""
        -- Tenants
        INSERT INTO tenants (first_name, last_name, email, phone, date_of_birth) VALUES
        ('Alice', 'Tan',   'alice.tan@example.com',   '012-3456789', '1990-04-15'),
        ('Brian', 'Lee',   'brian.lee@example.com',   '013-2345678', '1985-11-22'),
        ('Clara', 'Wong',  'clara.wong@example.com',  '014-1234567', '1992-07-09'),
        ('David','Chong',  'david.chong@example.com', '015-9876543', '1988-02-28'),
        ('Elaine','Ng',    'elaine.ng@example.com',   '016-8765432', '1995-12-05');

        -- Properties
        INSERT INTO properties (name, address_line1, address_line2, city, state, postal_code, country) VALUES
        ('Sunset Apartments',  '10 Jalan Bukit',     NULL,            'Petaling Jaya', 'Selangor','46000','Malaysia'),
        ('Ocean View Condos',  '25 Jalan Pantai',    'Block B, Unit 12','Penang',      'Penang',  '10470','Malaysia'),
        ('Hilltop Villas',     '5 Jalan Bukit Tinggi',NULL,            'Kuala Lumpur','KL','50450','Malaysia'),
        ('Lakewood Homes',     '88 Lake Drive',       NULL,            'Ipoh',        'Perak',  '30000','Malaysia'),
        ('Riverdale Towers',   '123 Riverside Rd',    'Tower A, 15th Fl','Kuantan',   'Pahang', '25000','Malaysia');

        -- Units
        INSERT INTO units (property_id, unit_number, floor, bedrooms, bathrooms, square_feet) VALUES
        (1, 'A-01',  '1', 2, 1.5,  850),
        (1, 'B-03',  '2', 3, 2.0, 1200),
        (2, 'B-12', '12', 1, 1.0,  600),
        (3, 'V-05',  '1', 4, 3.0, 2000),
        (5, 'T-150','15', 2, 2.0,  900);

        -- Leases
        INSERT INTO leases (tenant_id, unit_id, start_date, end_date, rent_amount, security_deposit) VALUES
        (1, 1, '2025-01-01','2025-12-31', 1500.00, 1500.00),
        (2, 2, '2025-03-15','2026-03-14', 2100.00, 2100.00),
        (3, 3, '2025-05-01','2026-04-30',  800.00,  800.00),
        (4, 4, '2025-02-01','2025-07-31', 3200.00, 3200.00),
        (5, 5, '2025-06-01','2026-05-31', 1200.00, 1200.00);

        -- Agents
        INSERT INTO agents (first_name, last_name, role, email, phone) VALUES
        ('Farah','Iskandar','Manager',   'farah.iskandar@example.com','017-1234567'),
        ('Gavin','Lim',     'Technician','gavin.lim@example.com',    '018-2345678'),
        ('Han',  'Yeo',     'Clerk',     'han.yeo@example.com',      '019-3456789'),
        ('Irene','Chew',    'Supervisor','irene.chew@example.com',   '010-4567890'),
        ('Jamal','Omar',    'Technician','jamal.omar@example.com',   '011-5678901');

        -- Service Tickets
        INSERT INTO service_tickets (lease_id, raised_by, assigned_to, category, subcategory, description, priority) VALUES
        (1, 1, 2, 'Maintenance','Plumbing',   'Leaking faucet in kitchen',       'high'),
        (2, 2, 3, 'Billing',    'Invoice',    'Dispute on last month''s invoice', 'normal'),
        (3, 3, NULL,'Maintenance','Electrical','Living room light flickering',   'high'),
        (4, 4, 5, 'Inquiries',  'General',    'How to renew lease online?',      'low'),
        (5, 5, 4, 'Maintenance','Painting',   'Wall paint peeling in bedroom',   'normal');

        -- Ticket Comments
        INSERT INTO ticket_comments (ticket_id, author_id, author_type, comment_text) VALUES
        (1, 2, 'agent',  'I have scheduled a plumber for tomorrow.'),
        (1, 1, 'tenant', 'Thanks—please let me know the time.'),
        (2, 3, 'agent',  'Please provide the invoice number.'),
        (3, 3, 'agent',  'Electrician will arrive this afternoon.'),
        (4, 5, 'agent',  'You can renew via our website under "My Account."');

        -- Payments
        INSERT INTO payments (lease_id, payment_type, billing_period, due_date, amount, method, paid_on, reference_number) VALUES
        (1, 'rent',       '2025-06','2025-06-05',1500.00,'bank_transfer','2025-06-03 10:15:00','BTX123456'),
        (2, 'electricity','2025-05','2025-05-20', 120.50,'credit_card',  '2025-05-18 14:22:00','CC987654'),
        (3, 'water',      '2025-05','2025-05-25',  45.75,'bank_transfer', NULL,                NULL),
        (4, 'rent',       '2025-06','2025-06-01',3200.00,'credit_card',  '2025-05-30 09:00:00','CC112233'),
        (5, 'rent',       '2025-06','2025-06-07',1200.00,'bank_transfer','2025-06-06 11:45:00','BTX778899');

        -- Ticket Conversations
        INSERT INTO ticket_conversations (ticket_id, author_type, author_id, message_text) VALUES
        (1, 'agent',  2, 'Plumber ETA: 9am tomorrow.'),
        (1, 'tenant', 1, 'Okay, I''ll be home by then.'),
        (2, 'agent',  3, 'Awaiting invoice details.'),
        (5, 'agent',  4, 'Painting crew scheduled Friday.'),
        (3, 'agent',  3, 'Electric switch replaced.');
        """)

        conn.commit()
        conn.close()
        print("Database initialized successfully!")

class PropertyManager:
    """Main business logic for property management"""

    def __init__(self):
        self.db = DatabaseManager()

    # TENANT OPERATIONS
    def get_all_tenants(self) -> List[Dict]:
        """Get all tenants"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenants ORDER BY last_name, first_name")
        tenants = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tenants

    def get_tenant_by_id(self, tenant_id: int) -> Optional[Dict]:
        """Get tenant by ID"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tenants WHERE id = ?", (tenant_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_tenant(self, first_name: str, last_name: str, email: str,
                   phone: str = None, date_of_birth: str = None) -> int:
        """Add new tenant"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tenants (first_name, last_name, email, phone, date_of_birth)
            VALUES (?, ?, ?, ?, ?)
        """, (first_name, last_name, email, phone, date_of_birth))
        tenant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return tenant_id

    # PROPERTY OPERATIONS
    def get_all_properties(self) -> List[Dict]:
        """Get all properties with unit counts"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(u.id) as unit_count
            FROM properties p
            LEFT JOIN units u ON p.id = u.property_id
            GROUP BY p.id
            ORDER BY p.name
        """)
        properties = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return properties

    def get_units_by_property(self, property_id: int) -> List[Dict]:
        """Get all units for a property"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.*,
                   CASE WHEN l.id IS NOT NULL THEN 'occupied' ELSE u.status END as current_status,
                   t.first_name || ' ' || t.last_name as tenant_name
            FROM units u
            LEFT JOIN leases l ON u.id = l.unit_id AND l.status = 'active'
            LEFT JOIN tenants t ON l.tenant_id = t.id
            WHERE u.property_id = ?
            ORDER BY u.unit_number
        """, (property_id,))
        units = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return units

    # LEASE OPERATIONS
    def get_active_leases(self) -> List[Dict]:
        """Get all active leases with tenant and unit info"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT l.*,
                   t.first_name || ' ' || t.last_name as tenant_name,
                   t.email as tenant_email,
                   p.name as property_name,
                   u.unit_number
            FROM leases l
            JOIN tenants t ON l.tenant_id = t.id
            JOIN units u ON l.unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            WHERE l.status = 'active'
            ORDER BY l.end_date
        """)
        leases = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leases

    def get_expiring_leases(self, days_ahead: int = 30) -> List[Dict]:
        """Get leases expiring within specified days"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        end_date = datetime.now() + timedelta(days=days_ahead)
        cursor.execute("""
            SELECT l.*,
                   t.first_name || ' ' || t.last_name as tenant_name,
                   t.email as tenant_email,
                   p.name as property_name,
                   u.unit_number
            FROM leases l
            JOIN tenants t ON l.tenant_id = t.id
            JOIN units u ON l.unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            WHERE l.status = 'active' AND l.end_date <= ?
            ORDER BY l.end_date
        """, (end_date.strftime('%Y-%m-%d'),))
        leases = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leases

    # PAYMENT OPERATIONS
    def get_pending_payments(self) -> List[Dict]:
        """Get all pending payments"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*,
                   t.first_name || ' ' || t.last_name as tenant_name,
                   t.email as tenant_email,
                   pr.name as property_name,
                   u.unit_number
            FROM payments p
            JOIN leases l ON p.lease_id = l.id
            JOIN tenants t ON l.tenant_id = t.id
            JOIN units u ON l.unit_id = u.id
            JOIN properties pr ON u.property_id = pr.id
            WHERE p.paid_on IS NULL
            ORDER BY p.due_date
        """)
        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return payments

    def mark_payment_paid(self, payment_id: int, method: str, reference: str = None):
        """Mark a payment as paid"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE payments
            SET paid_on = strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'),
                method = ?,
                reference_number = ?
            WHERE id = ?
        """, (method, reference, payment_id))
        conn.commit()
        conn.close()

    # SERVICE TICKET OPERATIONS
    def get_open_tickets(self) -> List[Dict]:
        """Get all open service tickets"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT st.*,
                   t.first_name || ' ' || t.last_name as tenant_name,
                   a.first_name || ' ' || a.last_name as agent_name,
                   p.name as property_name,
                   u.unit_number
            FROM service_tickets st
            JOIN leases l ON st.lease_id = l.id
            JOIN tenants t ON l.tenant_id = t.id
            JOIN units u ON l.unit_id = u.id
            JOIN properties p ON u.property_id = p.id
            LEFT JOIN agents a ON st.assigned_to = a.id
            WHERE st.status IN ('open', 'in_progress')
            ORDER BY st.priority DESC, st.created_at
        """)
        tickets = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return tickets

    def create_service_ticket(self, lease_id: int, raised_by: int, category: str,
                             description: str, priority: str = 'normal',
                             subcategory: str = None) -> int:
        """Create new service ticket"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO service_tickets (lease_id, raised_by, category, subcategory, description, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (lease_id, raised_by, category, subcategory, description, priority))
        ticket_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return ticket_id

    def assign_ticket(self, ticket_id: int, agent_id: int):
        """Assign ticket to agent"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE service_tickets
            SET assigned_to = ?,
                status = 'assigned',
                updated_at = strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')
            WHERE id = ?
        """, (agent_id, ticket_id))
        conn.commit()
        conn.close()

    # REPORTING
    def get_financial_summary(self, month: str = None) -> Dict:
        """Get financial summary for a given month (YYYY-MM format)"""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        if month:
            date_filter = f"AND strftime('%Y-%m', p.due_date) = '{month}'"
        else:
            date_filter = f"AND strftime('%Y-%m', p.due_date) = strftime('%Y-%m', 'now')"

        cursor.execute(f"""
            SELECT
                COALESCE(SUM(CASE WHEN p.paid_on IS NOT NULL THEN p.amount ELSE 0 END), 0) as total_collected,
                COALESCE(SUM(CASE WHEN p.paid_on IS NULL THEN p.amount ELSE 0 END), 0) as total_pending,
                COUNT(CASE WHEN p.paid_on IS NOT NULL THEN 1 END) as payments_received,
                COUNT(CASE WHEN p.paid_on IS NULL THEN 1 END) as payments_pending
            FROM payments p
            WHERE 1=1 {date_filter}
        """)

        summary = dict(cursor.fetchone())
        conn.close()
        return summary


def main():
    """Main entry point"""
    print("Initializing Property Management System...")
    pm = PropertyManager()
    print("System ready!")


if __name__ == "__main__":
    main()
