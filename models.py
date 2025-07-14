"""
Data models and utility classes for Property Management System
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json

@dataclass
class Tenant:
    """Tenant data model"""
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    email: str = ""
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Tenant':
        return cls(**data)

@dataclass
class Property:
    """Property data model"""
    id: Optional[int] = None
    name: str = ""
    address_line1: str = ""
    address_line2: Optional[str] = None
    city: str = ""
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: str = ""
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def full_address(self) -> str:
        parts = [self.address_line1]
        if self.address_line2:
            parts.append(self.address_line2)
        parts.extend([self.city, self.state, self.postal_code])
        return ", ".join(filter(None, parts))

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Property':
        return cls(**data)

@dataclass
class Unit:
    """Unit data model"""
    id: Optional[int] = None
    property_id: int = 0
    unit_number: str = ""
    floor: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    square_feet: Optional[int] = None
    status: str = "available"
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def description(self) -> str:
        parts = []
        if self.bedrooms:
            parts.append(f"{self.bedrooms}BR")
        if self.bathrooms:
            parts.append(f"{self.bathrooms}BA")
        if self.square_feet:
            parts.append(f"{self.square_feet}sqft")
        return " / ".join(parts)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Unit':
        return cls(**data)

@dataclass
class Lease:
    """Lease data model"""
    id: Optional[int] = None
    tenant_id: int = 0
    unit_id: int = 0
    start_date: str = ""
    end_date: str = ""
    rent_amount: float = 0.0
    security_deposit: Optional[float] = None
    status: str = "active"
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def days_until_expiry(self) -> Optional[int]:
        if not self.end_date:
            return None
        try:
            end_date = datetime.strptime(self.end_date, '%Y-%m-%d').date()
            today = date.today()
            return (end_date - today).days
        except ValueError:
            return None

    @property
    def is_expiring_soon(self, days: int = 30) -> bool:
        days_left = self.days_until_expiry
        return days_left is not None and 0 <= days_left <= days

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Lease':
        return cls(**data)

@dataclass
class Agent:
    """Agent data model"""
    id: Optional[int] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unknown Agent"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Agent':
        return cls(**data)

@dataclass
class ServiceTicket:
    """Service ticket data model"""
    id: Optional[int] = None
    lease_id: int = 0
    raised_by: int = 0
    assigned_to: Optional[int] = None
    category: str = ""
    subcategory: Optional[str] = None
    description: str = ""
    status: str = "open"
    priority: str = "normal"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def is_open(self) -> bool:
        return self.status in ['open', 'assigned', 'in_progress']

    @property
    def priority_level(self) -> int:
        priority_map = {'low': 1, 'normal': 2, 'high': 3, 'urgent': 4}
        return priority_map.get(self.priority, 2)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'ServiceTicket':
        return cls(**data)

@dataclass
class Payment:
    """Payment data model"""
    id: Optional[int] = None
    lease_id: int = 0
    payment_type: str = ""
    billing_period: Optional[str] = None
    due_date: Optional[str] = None
    amount: float = 0.0
    method: Optional[str] = None
    paid_on: Optional[str] = None
    reference_number: Optional[str] = None
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    @property
    def is_paid(self) -> bool:
        return self.paid_on is not None

    @property
    def is_overdue(self) -> bool:
        if not self.due_date or self.is_paid:
            return False
        try:
            due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
            return date.today() > due_date
        except ValueError:
            return False

    @property
    def days_overdue(self) -> Optional[int]:
        if not self.is_overdue:
            return None
        try:
            due_date = datetime.strptime(self.due_date, '%Y-%m-%d').date()
            return (date.today() - due_date).days
        except ValueError:
            return None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Payment':
        return cls(**data)

@dataclass
class TicketComment:
    """Ticket comment data model"""
    id: Optional[int] = None
    ticket_id: int = 0
    author_id: int = 0
    author_type: str = ""
    comment_text: str = ""
    created_at: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'TicketComment':
        return cls(**data)

@dataclass
class TicketConversation:
    """Ticket conversation data model"""
    id: Optional[int] = None
    ticket_id: int = 0
    author_type: str = ""
    author_id: int = 0
    message_text: str = ""
    sent_at: Optional[str] = None
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'TicketConversation':
        return cls(**data)

class DataValidator:
    """Data validation utilities"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Basic Malaysian phone number validation"""
        import re
        # Malaysian phone patterns: 01X-XXXXXXX, +601X-XXXXXXX, etc.
        patterns = [
            r'^01[0-9]-[0-9]{7,8}$',  # 01X-XXXXXXX
            r'^01[0-9][0-9]{7,8}$',   # 01XXXXXXXX
            r'^\+601[0-9]-[0-9]{7,8}$',  # +601X-XXXXXXX
            r'^\+601[0-9][0-9]{7,8}$'    # +601XXXXXXXX
        ]
        return any(re.match(pattern, phone) for pattern in patterns)

    @staticmethod
    def validate_date(date_str: str, format_str: str = '%Y-%m-%d') -> bool:
        """Validate date string format"""
        try:
            datetime.strptime(date_str, format_str)
            return True
        except ValueError:
            return False

    @staticmethod
    def validate_amount(amount: Any) -> bool:
        """Validate monetary amount"""
        try:
            float_amount = float(amount)
            return float_amount >= 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_postal_code(postal_code: str, country: str = 'Malaysia') -> bool:
        """Validate postal code based on country"""
        import re
        if country.lower() == 'malaysia':
            # Malaysian postal codes are 5 digits
            return re.match(r'^\d{5}$', postal_code) is not None
        else:
            # Generic validation - at least 3 characters
            return len(postal_code.strip()) >= 3

    @staticmethod
    def validate_unit_number(unit_number: str) -> bool:
        """Validate unit number format"""
        # Unit numbers should be non-empty and alphanumeric
        return bool(unit_number.strip()) and len(unit_number.strip()) <= 20

class ReportGenerator:
    """Generate various reports"""

    @staticmethod
    def generate_lease_expiry_report(leases: List[Dict], days_ahead: int = 30) -> Dict:
        """Generate lease expiry report"""
        expiring_leases = []
        total_rent_at_risk = 0.0

        for lease_data in leases:
            lease = Lease.from_dict(lease_data)
            if lease.is_expiring_soon(days_ahead):
                expiring_leases.append(lease_data)
                total_rent_at_risk += lease.rent_amount

        return {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period_days': days_ahead,
            'total_expiring': len(expiring_leases),
            'total_rent_at_risk': total_rent_at_risk,
            'leases': expiring_leases
        }

    @staticmethod
    def generate_payment_summary(payments: List[Dict], period: str = 'current_month') -> Dict:
        """Generate payment summary report"""
        paid_payments = []
        pending_payments = []
        overdue_payments = []

        total_collected = 0.0
        total_pending = 0.0
        total_overdue = 0.0

        for payment_data in payments:
            payment = Payment.from_dict(payment_data)

            if payment.is_paid:
                paid_payments.append(payment_data)
                total_collected += payment.amount
            elif payment.is_overdue:
                overdue_payments.append(payment_data)
                total_overdue += payment.amount
            else:
                pending_payments.append(payment_data)
                total_pending += payment.amount

        return {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'period': period,
            'summary': {
                'total_collected': total_collected,
                'total_pending': total_pending,
                'total_overdue': total_overdue,
                'collection_rate': (total_collected / (total_collected + total_pending + total_overdue) * 100) if (total_collected + total_pending + total_overdue) > 0 else 0
            },
            'counts': {
                'paid': len(paid_payments),
                'pending': len(pending_payments),
                'overdue': len(overdue_payments)
            },
            'details': {
                'paid_payments': paid_payments,
                'pending_payments': pending_payments,
                'overdue_payments': overdue_payments
            }
        }

    @staticmethod
    def generate_occupancy_report(properties: List[Dict], units: List[Dict], leases: List[Dict]) -> Dict:
        """Generate property occupancy report"""
        occupancy_data = []

        for property_data in properties:
            property_units = [u for u in units if u['property_id'] == property_data['id']]
            occupied_units = 0

            for unit in property_units:
                unit_leases = [l for l in leases if l['unit_id'] == unit['id'] and l['status'] == 'active']
                if unit_leases:
                    occupied_units += 1

            total_units = len(property_units)
            occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

            occupancy_data.append({
                'property_id': property_data['id'],
                'property_name': property_data['name'],
                'total_units': total_units,
                'occupied_units': occupied_units,
                'vacant_units': total_units - occupied_units,
                'occupancy_rate': occupancy_rate
            })

        # Overall statistics
        total_units_all = sum(p['total_units'] for p in occupancy_data)
        total_occupied_all = sum(p['occupied_units'] for p in occupancy_data)
        overall_occupancy = (total_occupied_all / total_units_all * 100) if total_units_all > 0 else 0

        return {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_occupancy_rate': overall_occupancy,
            'total_units': total_units_all,
            'total_occupied': total_occupied_all,
            'total_vacant': total_units_all - total_occupied_all,
            'properties': occupancy_data
        }

    @staticmethod
    def generate_service_ticket_report(tickets: List[Dict]) -> Dict:
        """Generate service ticket analysis report"""
        if not tickets:
            return {
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_tickets': 0,
                'summary': {},
                'recommendations': []
            }

        # Analyze ticket data
        priorities = {}
        categories = {}
        statuses = {}

        for ticket in tickets:
            priority = ticket.get('priority', 'normal')
            category = ticket.get('category', 'Unknown')
            status = ticket.get('status', 'open')

            priorities[priority] = priorities.get(priority, 0) + 1
            categories[category] = categories.get(category, 0) + 1
            statuses[status] = statuses.get(status, 0) + 1

        # Generate recommendations
        recommendations = []
        if priorities.get('urgent', 0) > 0:
            recommendations.append(f"Address {priorities['urgent']} urgent tickets immediately")
        if priorities.get('high', 0) > 2:
            recommendations.append("Consider additional maintenance staff for high priority tickets")
        if categories.get('Maintenance', 0) > len(tickets) * 0.6:
            recommendations.append("Review preventive maintenance schedule")

        return {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_tickets': len(tickets),
            'summary': {
                'by_priority': priorities,
                'by_category': categories,
                'by_status': statuses
            },
            'recommendations': recommendations
        }

    @staticmethod
    def generate_tenant_demographics_report(tenants: List[Dict]) -> Dict:
        """Generate tenant demographics report"""
        if not tenants:
            return {
                'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'total_tenants': 0,
                'demographics': {}
            }

        age_groups = {'18-25': 0, '26-35': 0, '36-45': 0, '46-55': 0, '55+': 0, 'Unknown': 0}
        contact_completeness = {'email_only': 0, 'phone_only': 0, 'both': 0, 'neither': 0}

        for tenant in tenants:
            # Age analysis
            if tenant.get('date_of_birth'):
                age = Utils.calculate_age(tenant['date_of_birth'])
                if age:
                    if age <= 25:
                        age_groups['18-25'] += 1
                    elif age <= 35:
                        age_groups['26-35'] += 1
                    elif age <= 45:
                        age_groups['36-45'] += 1
                    elif age <= 55:
                        age_groups['46-55'] += 1
                    else:
                        age_groups['55+'] += 1
                else:
                    age_groups['Unknown'] += 1
            else:
                age_groups['Unknown'] += 1

            # Contact completeness
            has_email = bool(tenant.get('email'))
            has_phone = bool(tenant.get('phone'))

            if has_email and has_phone:
                contact_completeness['both'] += 1
            elif has_email:
                contact_completeness['email_only'] += 1
            elif has_phone:
                contact_completeness['phone_only'] += 1
            else:
                contact_completeness['neither'] += 1

        return {
            'report_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_tenants': len(tenants),
            'demographics': {
                'age_groups': age_groups,
                'contact_completeness': contact_completeness
            }
        }

class Utils:
    """General utility functions"""

    @staticmethod
    def format_currency(amount: float, currency: str = 'RM') -> str:
        """Format amount as currency"""
        return f"{currency} {amount:,.2f}"

    @staticmethod
    def format_date(date_str: str, input_format: str = '%Y-%m-%d', output_format: str = '%d/%m/%Y') -> str:
        """Format date string"""
        try:
            date_obj = datetime.strptime(date_str, input_format)
            return date_obj.strftime(output_format)
        except ValueError:
            return date_str

    @staticmethod
    def calculate_age(birth_date: str) -> Optional[int]:
        """Calculate age from birth date"""
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d').date()
            today = date.today()
            return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        except ValueError:
            return None

    @staticmethod
    def export_to_json(data: Any, filename: str) -> bool:
        """Export data to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False

    @staticmethod
    def import_from_json(filename: str) -> Optional[Any]:
        """Import data from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error importing from JSON: {e}")
            return None

    @staticmethod
    def calculate_lease_duration(start_date: str, end_date: str) -> Optional[int]:
        """Calculate lease duration in days"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            return (end - start).days
        except ValueError:
            return None

    @staticmethod
    def generate_reference_number(prefix: str = "REF", length: int = 6) -> str:
        """Generate a reference number"""
        import random
        import string
        suffix = ''.join(random.choices(string.digits, k=length))
        return f"{prefix}{suffix}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file operations"""
        import re
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        # Limit length
        if len(sanitized) > 200:
            sanitized = sanitized[:200]
        return sanitized

    @staticmethod
    def parse_address(address_string: str) -> Dict[str, str]:
        """Parse a full address string into components"""
        # Simple address parsing - can be enhanced
        parts = [part.strip() for part in address_string.split(',')]

        result = {
            'address_line1': '',
            'address_line2': '',
            'city': '',
            'state': '',
            'postal_code': '',
            'country': ''
        }

        if len(parts) >= 1:
            result['address_line1'] = parts[0]
        if len(parts) >= 2:
            result['city'] = parts[1]
        if len(parts) >= 3:
            result['state'] = parts[2]
        if len(parts) >= 4:
            result['country'] = parts[3]

        return result

    @staticmethod
    def mask_sensitive_data(data: str, mask_char: str = '*', show_last: int = 4) -> str:
        """Mask sensitive data like phone numbers or emails"""
        if not data or len(data) <= show_last:
            return data

        visible_part = data[-show_last:]
        masked_part = mask_char * (len(data) - show_last)
        return masked_part + visible_part

    @staticmethod
    def calculate_business_days(start_date: str, end_date: str) -> Optional[int]:
        """Calculate business days between two dates (excluding weekends)"""
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            end = datetime.strptime(end_date, '%Y-%m-%d').date()

            business_days = 0
            current_date = start

            while current_date <= end:
                if current_date.weekday() < 5:  # Monday = 0, Sunday = 6
                    business_days += 1
                current_date += timedelta(days=1)

            return business_days
        except ValueError:
            return None

class DataAnalyzer:
    """Advanced data analysis utilities"""

    @staticmethod
    def calculate_revenue_trends(payments: List[Dict], months: int = 12) -> Dict:
        """Calculate revenue trends over specified months"""
        from collections import defaultdict

        monthly_revenue = defaultdict(float)
        monthly_counts = defaultdict(int)

        for payment in payments:
            if payment.get('paid_on'):
                try:
                    payment_date = datetime.strptime(payment['paid_on'], '%Y-%m-%d %H:%M:%S')
                    month_key = payment_date.strftime('%Y-%m')
                    monthly_revenue[month_key] += payment['amount']
                    monthly_counts[month_key] += 1
                except ValueError:
                    continue

        # Sort by month and get last N months
        sorted_months = sorted(monthly_revenue.keys())[-months:]

        return {
            'monthly_revenue': {month: monthly_revenue[month] for month in sorted_months},
            'monthly_counts': {month: monthly_counts[month] for month in sorted_months},
            'trend_analysis': {
                'total_months': len(sorted_months),
                'average_monthly_revenue': sum(monthly_revenue[m] for m in sorted_months) / len(sorted_months) if sorted_months else 0,
                'highest_month': max(sorted_months, key=lambda m: monthly_revenue[m]) if sorted_months else None,
                'lowest_month': min(sorted_months, key=lambda m: monthly_revenue[m]) if sorted_months else None
            }
        }

    @staticmethod
    def analyze_tenant_retention(leases: List[Dict]) -> Dict:
        """Analyze tenant retention patterns"""
        tenant_lease_counts = {}
        total_leases = len(leases)

        for lease in leases:
            tenant_id = lease.get('tenant_id')
            if tenant_id:
                tenant_lease_counts[tenant_id] = tenant_lease_counts.get(tenant_id, 0) + 1

        retention_stats = {
            'single_lease': 0,
            'multiple_leases': 0,
            'max_leases_per_tenant': 0,
            'retention_rate': 0.0
        }

        if tenant_lease_counts:
            retention_stats['single_lease'] = sum(1 for count in tenant_lease_counts.values() if count == 1)
            retention_stats['multiple_leases'] = sum(1 for count in tenant_lease_counts.values() if count > 1)
            retention_stats['max_leases_per_tenant'] = max(tenant_lease_counts.values())
            retention_stats['retention_rate'] = (retention_stats['multiple_leases'] / len(tenant_lease_counts)) * 100

        return retention_stats

    @staticmethod
    def identify_maintenance_patterns(tickets: List[Dict]) -> Dict:
        """Identify patterns in maintenance requests"""
        category_frequency = {}
        property_issues = {}
        seasonal_patterns = {}

        for ticket in tickets:
            # Category analysis
            category = ticket.get('category', 'Unknown')
            category_frequency[category] = category_frequency.get(category, 0) + 1

            # Property analysis
            property_name = ticket.get('property_name', 'Unknown')
            if property_name not in property_issues:
                property_issues[property_name] = {}
            property_issues[property_name][category] = property_issues[property_name].get(category, 0) + 1

            # Seasonal analysis (if created_at is available)
            if ticket.get('created_at'):
                try:
                    created_date = datetime.strptime(ticket['created_at'], '%Y-%m-%d %H:%M:%S')
                    month = created_date.strftime('%m')
                    seasonal_patterns[month] = seasonal_patterns.get(month, 0) + 1
                except ValueError:
                    continue

        return {
            'category_frequency': category_frequency,
            'property_issues': property_issues,
            'seasonal_patterns': seasonal_patterns,
            'recommendations': DataAnalyzer._generate_maintenance_recommendations(category_frequency, property_issues)
        }

    @staticmethod
    def _generate_maintenance_recommendations(category_freq: Dict, property_issues: Dict) -> List[str]:
        """Generate maintenance recommendations based on patterns"""
        recommendations = []

        if category_freq:
            most_common = max(category_freq, key=category_freq.get)
            if category_freq[most_common] > len(category_freq) * 0.5:
                recommendations.append(f"Focus on preventive maintenance for {most_common} issues")

        # Property-specific recommendations
        for property_name, issues in property_issues.items():
            if len(issues) > 3:
                recommendations.append(f"Review maintenance protocols for {property_name}")

        return recommendations
