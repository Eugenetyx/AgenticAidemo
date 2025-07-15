import sqlite3

# Path to your SQLite database file
DB_PATH = 'database.db'


# SQL schema as a multi-line string
SCHEMA_SQL = '''
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS maintenance_tickets;
DROP TABLE IF EXISTS complaint_tickets;
DROP TABLE IF EXISTS billing_tickets;
DROP TABLE IF EXISTS payments;
DROP TABLE IF EXISTS chat_rooms;
DROP TABLE IF EXISTS conversation_messages;
DROP TABLE IF EXISTS leases;
DROP TABLE IF EXISTS rooms;
DROP TABLE IF EXISTS units;
DROP TABLE IF EXISTS agents;
DROP TABLE IF EXISTS properties;
DROP TABLE IF EXISTS tenants;

-- Tenants
CREATE TABLE tenants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
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
    name            TEXT    NOT NULL,
    address_line1   TEXT    NOT NULL,
    address_line2   TEXT,
    city            TEXT    NOT NULL,
    state           TEXT,
    postal_code     TEXT,
    country         TEXT    NOT NULL,
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Units (e.g. entire apartment or house, contains multiple rooms)
CREATE TABLE units (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    property_id     INTEGER NOT NULL REFERENCES properties(id) ON DELETE CASCADE,
    unit_number     TEXT    NOT NULL,
    floor           TEXT,
    bedrooms        INTEGER,
    bathrooms       REAL,
    square_feet     INTEGER,
    status          TEXT    DEFAULT 'available',
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Rooms (individual rentable rooms within a unit)
CREATE TABLE rooms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    unit_id         INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    room_name       TEXT    NOT NULL,   -- e.g. 'Bedroom A', 'Master Bedroom'
    room_type       TEXT,               -- e.g. 'single', 'double'
    size_sq_ft      INTEGER,
    status          TEXT    DEFAULT 'available',
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Agents (property managers, leasing staff)
CREATE TABLE agents (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name      TEXT,
    last_name       TEXT,
    email           TEXT    UNIQUE,
    phone           TEXT,
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Leases (connected to tenant, specific room, and agent)
CREATE TABLE leases (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id        INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    room_id          INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    agent_id         INTEGER        REFERENCES agents(id) ON DELETE SET NULL,
    start_date       DATETIME NOT NULL,
    end_date         DATETIME NOT NULL,
    rent_amount      REAL    NOT NULL,
    security_deposit REAL,
    status           TEXT    DEFAULT 'active',
    created_at       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Maintenance history (past or scheduled jobs)
CREATE TABLE maintenance_tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    lease_id       INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
    subcategory    TEXT,
    scheduled_for  DATETIME,
    completed_on   DATETIME
);

-- Complaint history
CREATE TABLE complaint_tickets (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    lease_id       INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
    severity       TEXT    NOT NULL,
    complaint_type TEXT,
    filed_on       DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    resolved_on    DATETIME,
    resolution     TEXT
);

-- Payments (transaction ledger)
CREATE TABLE payments (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    lease_id           INTEGER NOT NULL REFERENCES leases(id) ON DELETE CASCADE,
    payment_type       TEXT    NOT NULL,
    transaction_type   TEXT    NOT NULL CHECK(transaction_type IN ('charge','refund','credit')),
    due_date           DATETIME,
    amount             REAL    NOT NULL,
    method             TEXT,
    paid_on            DATETIME,
    created_at         DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
);

-- Chat Rooms
CREATE TABLE chat_rooms (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id       INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    created_at      DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours')),
    last_updated    DATETIME,
    status          TEXT    DEFAULT 'open'
);

-- Conversation Messages
CREATE TABLE conversation_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_room_id    INTEGER NOT NULL REFERENCES chat_rooms(id) ON DELETE CASCADE,
    author_type     TEXT    NOT NULL CHECK (author_type IN ('tenant','agent','bot')),
    author_id       INTEGER,
    message_text    TEXT    NOT NULL,
    sent_at         DATETIME DEFAULT (strftime('%Y-%m-%d %H:%M:%S','now','+8 hours'))
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