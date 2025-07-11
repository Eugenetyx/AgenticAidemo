import sqlite3

# Path to your SQLite database file
DB_PATH = 'database.db'

# SQL schema as a multi-line string
SCHEMA_SQL = '''
PRAGMA foreign_keys = ON;

-- Drop old tables if they exist
DROP TABLE IF EXISTS ticket_conversations;
DROP TABLE IF EXISTS ticket_comments;
DROP TABLE IF EXISTS maintenance_tickets;
DROP TABLE IF EXISTS complaint_tickets;
DROP TABLE IF EXISTS billing_tickets;
DROP TABLE IF EXISTS service_tickets;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS leases;
DROP TABLE IF EXISTS units;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS properties;
DROP TABLE IF EXISTS tenants;
DROP TABLE IF EXISTS transaction_audit;  -- In case audit table existed

-- Tenants
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

-- Properties
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

-- Units
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

-- Leases
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

-- Agents
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

-- Service Tickets (base table)
CREATE TABLE service_tickets (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    lease_id        INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
    raised_by       INTEGER        REFERENCES tenants(id) ON DELETE SET NULL,
    assigned_to     INTEGER        REFERENCES agents(id) ON DELETE SET NULL,
    category        TEXT     NOT NULL,
    description     TEXT     NOT NULL,
    status          TEXT     DEFAULT 'open',
    priority        TEXT     DEFAULT 'normal',
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    updated_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Maintenance Tickets
CREATE TABLE maintenance_tickets (
    ticket_id       INTEGER PRIMARY KEY REFERENCES service_tickets(id) ON DELETE CASCADE,
    subcategory     TEXT,
    scheduled_for   DATETIME,
    technician_id   INTEGER REFERENCES agents(id) ON DELETE SET NULL
);

-- Complaint Tickets
CREATE TABLE complaint_tickets (
    ticket_id       INTEGER PRIMARY KEY REFERENCES service_tickets(id) ON DELETE CASCADE,
    severity        TEXT    NOT NULL,
    complaint_type  TEXT,
    resolved_on     DATETIME
);

-- Billing Tickets
CREATE TABLE billing_tickets (
    ticket_id       INTEGER PRIMARY KEY REFERENCES service_tickets(id) ON DELETE CASCADE,
    invoice_number  TEXT    NOT NULL,
    amount_disputed REAL,
    resolution_date DATETIME
);

-- Ticket Comments (official notes)
CREATE TABLE ticket_comments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    ticket_id       INTEGER NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
    author_id       INTEGER NOT NULL,
    author_type     TEXT    NOT NULL CHECK(author_type IN ('tenant','agent','system')),
    comment_text    TEXT    NOT NULL,
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Ticket Conversations (chat log)
CREATE TABLE ticket_conversations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    ticket_id       INTEGER NOT NULL REFERENCES service_tickets(id) ON DELETE CASCADE,
    author_type     TEXT    NOT NULL CHECK(author_type IN ('tenant','agent','system')),
    author_id       INTEGER NOT NULL,
    message_text    TEXT    NOT NULL,
    sent_at         DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Payments (transactions)
CREATE TABLE payments (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp          DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    lease_id           INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
    payment_type       TEXT    NOT NULL,
    transaction_type   TEXT    NOT NULL CHECK(transaction_type IN ('charge','refund','credit')),
    billing_period     TEXT,
    due_date           DATETIME,
    amount             REAL    NOT NULL,
    method             TEXT,
    paid_on            DATETIME,
    reference_number   TEXT,
    created_at         DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Optional: Audit table for payment changes
CREATE TABLE transaction_audit (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    payment_id          INTEGER NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    changed_by_type     TEXT    NOT NULL CHECK(changed_by_type IN ('agent','system')),
    changed_by_id       INTEGER NOT NULL,
    change_timestamp    DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    change_note         TEXT    NOT NULL
);
'''

def initialize_database():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()
    print('Database schema created successfully.')

if __name__ == '__main__':
    initialize_database()
