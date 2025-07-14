"""
Configuration settings for Property Management System
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class"""

    # Database settings
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'database.db')
    DATABASE_BACKUP_PATH = os.path.join(os.path.dirname(__file__), 'backups')

    # Application settings
    APP_NAME = "Property Management System"
    APP_VERSION = "1.0.0"
    TIMEZONE = "Asia/Kuala_Lumpur"

    # Business rules
    DEFAULT_LEASE_EXPIRY_WARNING_DAYS = 30
    DEFAULT_PAYMENT_DUE_WARNING_DAYS = 7

    # Service ticket priorities
    TICKET_PRIORITIES = ['low', 'normal', 'high', 'urgent']
    TICKET_CATEGORIES = [
        'Maintenance',
        'Billing',
        'Inquiries',
        'Complaints',
        'Emergency'
    ]

    # Payment methods
    PAYMENT_METHODS = [
        'bank_transfer',
        'credit_card',
        'debit_card',
        'cash',
        'check'
    ]

    # Unit statuses
    UNIT_STATUSES = [
        'available',
        'occupied',
        'maintenance',
        'renovation'
    ]

    # Lease statuses
    LEASE_STATUSES = [
        'active',
        'expired',
        'terminated',
        'pending'
    ]

    # Service ticket statuses
    TICKET_STATUSES = [
        'open',
        'assigned',
        'in_progress',
        'resolved',
        'closed'
    ]

    # Agent roles
    AGENT_ROLES = [
        'Manager',
        'Supervisor',
        'Technician',
        'Clerk',
        'Administrator'
    ]

    # Currency settings
    CURRENCY_SYMBOL = 'RM'
    CURRENCY_CODE = 'MYR'

    # Date formats
    DATE_FORMAT = '%Y-%m-%d'
    DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    DISPLAY_DATE_FORMAT = '%d/%m/%Y'
    DISPLAY_DATETIME_FORMAT = '%d/%m/%Y %H:%M'

    # Reporting settings
    REPORTS_PATH = os.path.join(os.path.dirname(__file__), 'reports')

    @classmethod
    def ensure_directories(cls):
        """Ensure required directories exist"""
        directories = [
            cls.DATABASE_BACKUP_PATH,
            cls.REPORTS_PATH
        ]

        for directory in directories:
            os.makedirs(directory, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    DATABASE_PATH = ':memory:'  # Use in-memory database for testing

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
