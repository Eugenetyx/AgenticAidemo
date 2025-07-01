"""
Streamlit Property Management System Dashboard
Interactive web interface for querying property data and document analysis
"""

import streamlit as st
import pandas as pd
import sqlite3
import json
import io
import os
import sys
import tempfile
import re
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional

# Import our existing modules
try:
    from main import PropertyManager, DatabaseManager
    from models import Utils, ReportGenerator, DataValidator, DataAnalyzer
    from config import Config
except ImportError:
    st.error("Please ensure main.py, models.py, and config.py are in the same directory")
    st.stop()

# Page configuration
st.set_page_config(
    page_title="Property Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #c3e6cb;
    }
    .error-message {
        background-color: #f8d7da;
        color: #721c24;
        padding: 0.75rem;
        border-radius: 0.25rem;
        border: 1px solid #f5c6cb;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .css-1d391kg {
        padding: 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 0px 24px;
        background-color: #f0f2f6;
        border-radius: 8px 8px 0px 0px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitPropertyApp:
    """Main Streamlit application class"""

    def __init__(self):
        self.pm = None
        self.initialize_session_state()
        self.initialize_database()

    def initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'api_key' not in st.session_state:
            st.session_state.api_key = ""
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
        if 'data_cache' not in st.session_state:
            st.session_state.data_cache = {}
        if 'chat_messages' not in st.session_state:
            st.session_state.chat_messages = []
        if 'selected_property' not in st.session_state:
            st.session_state.selected_property = None
        if 'selected_tenant' not in st.session_state:
            st.session_state.selected_tenant = None
        if 'theme_mode' not in st.session_state:
            st.session_state.theme_mode = "light"

    def initialize_database(self):
        """Initialize database connection"""
        try:
            self.pm = PropertyManager()
            st.session_state.db_connected = True
        except Exception as e:
            st.error(f"Database connection failed: {e}")
            st.session_state.db_connected = False

    def render_sidebar(self):
        """Render sidebar with configuration options"""
        st.sidebar.title("🔧 Configuration")

        # API Key input
        st.sidebar.subheader("🔑 API Configuration")
        api_key = st.sidebar.text_input(
            "Enter API Key (Optional)",
            value=st.session_state.api_key,
            type="password",
            help="Enter your OpenAI, Claude, or other AI API key for enhanced features"
        )
        st.session_state.api_key = api_key

        if api_key:
            st.sidebar.success("✅ API Key configured")

            # API Provider selection
            api_provider = st.sidebar.selectbox(
                "Select AI Provider:",
                ["OpenAI", "Anthropic Claude", "Custom"],
                help="Choose your AI service provider"
            )
            st.session_state.api_provider = api_provider

        # File upload section
        st.sidebar.subheader("📁 Document Upload")
        uploaded_files = st.sidebar.file_uploader(
            "Upload documents for analysis",
            accept_multiple_files=True,
            type=['csv', 'xlsx', 'json', 'txt', 'pdf'],
            help="Upload CSV, Excel, JSON, text or PDF files"
        )

        if uploaded_files:
            st.session_state.uploaded_files = uploaded_files
            st.sidebar.success(f"✅ {len(uploaded_files)} file(s) uploaded")

        # Database status and operations
        st.sidebar.subheader("🗄️ Database Management")
        if st.session_state.get('db_connected', False):
            st.sidebar.success("✅ Database Connected")

            # Quick stats
            try:
                tenants = self.pm.get_all_tenants()
                properties = self.pm.get_all_properties()
                leases = self.pm.get_active_leases()

                st.sidebar.metric("Tenants", len(tenants))
                st.sidebar.metric("Properties", len(properties))
                st.sidebar.metric("Active Leases", len(leases))

            except Exception as e:
                st.sidebar.error(f"Error loading stats: {e}")
        else:
            st.sidebar.error("❌ Database Not Connected")
            if st.sidebar.button("🔄 Reconnect Database"):
                self.initialize_database()

        # System preferences
        st.sidebar.subheader("⚙️ Preferences")

        # Currency setting
        currency = st.sidebar.selectbox(
            "Currency:",
            ["RM (Malaysian Ringgit)", "USD", "EUR", "SGD"],
            index=0
        )
        st.session_state.currency = currency.split()[0]

        # Date format
        date_format = st.sidebar.selectbox(
            "Date Format:",
            ["DD/MM/YYYY", "MM/DD/YYYY", "YYYY-MM-DD"],
            index=0
        )
        st.session_state.date_format = date_format

        # Clear cache and reset
        st.sidebar.subheader("🧹 System Maintenance")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🗑️ Clear Cache"):
                self.clear_cache()
                st.success("Cache cleared!")
        with col2:
            if st.button("🔄 Reset All"):
                self.reset_application()

    def render_main_header(self):
        """Render main application header"""
        # Logo and title
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<h1 class="main-header">🏢 Property Management System</h1>', unsafe_allow_html=True)

        # Status bar
        if st.session_state.get('db_connected', False):
            status_text = "🟢 System Online"
            try:
                tenants_count = len(self.pm.get_all_tenants())
                properties_count = len(self.pm.get_all_properties())
                status_text += f" | {tenants_count} Tenants | {properties_count} Properties"
            except:
                pass
        else:
            status_text = "🔴 System Offline"

        st.markdown(f"<div style='text-align: center; color: #666; margin-bottom: 1rem;'>{status_text}</div>", unsafe_allow_html=True)

        # Quick navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard",
            "🔍 Query Interface",
            "📋 Data Management",
            "📈 Analytics",
            "💬 AI Assistant"
        ])

        return tab1, tab2, tab3, tab4, tab5

    def render_dashboard(self, tab):
            """Render main dashboard"""
            with tab:
                if not st.session_state.get('db_connected', False):
                    st.error("Database not connected. Please check your database configuration.")
                    return

                # Dashboard header with refresh option
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.subheader("📊 System Overview")
                with col2:
                    if st.button("🔄 Refresh Dashboard"):
                        st.rerun()

                # Key metrics row
                try:
                    # Get all data
                    tenants = self.pm.get_all_tenants()
                    properties = self.pm.get_all_properties()
                    active_leases = self.pm.get_active_leases()
                    pending_payments = self.pm.get_pending_payments()
                    open_tickets = self.pm.get_open_tickets()
                    financial_summary = self.pm.get_financial_summary()

                    # Main metrics
                    col1, col2, col3, col4, col5 = st.columns(5)

                    with col1:
                        st.metric(
                            "👥 Total Tenants",
                            len(tenants),
                            help="Number of registered tenants"
                        )

                    with col2:
                        st.metric(
                            "🏠 Properties",
                            len(properties),
                            help="Total properties managed"
                        )

                    with col3:
                        st.metric(
                            "📋 Active Leases",
                            len(active_leases),
                            help="Currently active lease agreements"
                        )

                    with col4:
                        total_pending = sum(p['amount'] for p in pending_payments)
                        st.metric(
                            "💳 Pending Payments",
                            f"RM {total_pending:,.2f}",
                            help="Total amount in pending payments"
                        )

                    with col5:
                        st.metric(
                            "🎫 Open Tickets",
                            len(open_tickets),
                            help="Active service tickets"
                        )

                    st.divider()

                    # Financial overview section
                    st.subheader("💰 Financial Overview")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        collected = financial_summary.get('total_collected', 0)
                        st.metric(
                            "Monthly Collected",
                            f"RM {collected:,.2f}",
                            help="Total payments received this month"
                        )

                    with col2:
                        pending = financial_summary.get('total_pending', 0)
                        st.metric(
                            "Monthly Pending",
                            f"RM {pending:,.2f}",
                            help="Total payments pending this month"
                        )

                    with col3:
                        total_amount = collected + pending
                        if total_amount > 0:
                            collection_rate = (collected / total_amount) * 100
                            delta_color = "normal" if collection_rate >= 80 else "inverse"
                            st.metric(
                                "Collection Rate",
                                f"{collection_rate:.1f}%",
                                delta=f"Target: 85%",
                                delta_color=delta_color,
                                help="Percentage of payments collected"
                            )
                        else:
                            st.metric("Collection Rate", "0%")

                    with col4:
                        overdue_payments = [p for p in pending_payments if self.is_payment_overdue(p)]
                        overdue_amount = sum(p['amount'] for p in overdue_payments)
                        st.metric(
                            "Overdue Amount",
                            f"RM {overdue_amount:,.2f}",
                            delta=f"{len(overdue_payments)} payments",
                            delta_color="inverse" if overdue_amount > 0 else "normal",
                            help="Total overdue payment amount"
                        )

                    # Charts section
                    st.subheader("📈 Visual Analytics")

                    col1, col2 = st.columns(2)

                    with col1:
                        # Financial summary pie chart
                        if collected > 0 or pending > 0:
                            financial_data = pd.DataFrame({
                                'Category': ['Collected', 'Pending'],
                                'Amount': [collected, pending],
                                'Color': ['#2E8B57', '#FF6B6B']
                            })

                            fig_financial = px.pie(
                                financial_data,
                                values='Amount',
                                names='Category',
                                title="💰 Payment Status Distribution",
                                color='Category',
                                color_discrete_map={'Collected': '#2E8B57', 'Pending': '#FF6B6B'}
                            )
                            fig_financial.update_layout(height=400)
                            st.plotly_chart(fig_financial, use_container_width=True)
                        else:
                            st.info("No financial data available for this period")

                    with col2:
                        # Service tickets by priority
                        if open_tickets:
                            ticket_priorities = {}
                            for ticket in open_tickets:
                                priority = ticket.get('priority', 'normal')
                                ticket_priorities[priority] = ticket_priorities.get(priority, 0) + 1

                            # Create color mapping for priorities
                            priority_colors = {
                                'urgent': '#FF4444',
                                'high': '#FF8800',
                                'normal': '#4CAF50',
                                'low': '#2196F3'
                            }

                            priority_df = pd.DataFrame(
                                list(ticket_priorities.items()),
                                columns=['Priority', 'Count']
                            )

                            fig_tickets = px.bar(
                                priority_df,
                                x='Priority',
                                y='Count',
                                title="🎫 Service Tickets by Priority",
                                color='Priority',
                                color_discrete_map=priority_colors
                            )
                            fig_tickets.update_layout(height=400)
                            st.plotly_chart(fig_tickets, use_container_width=True)
                        else:
                            st.info("No open service tickets")

                    # Property occupancy overview
                    st.subheader("🏢 Property Occupancy Overview")

                    occupancy_data = []
                    for prop in properties:
                        units = self.pm.get_units_by_property(prop['id'])
                        total_units = len(units)
                        occupied_units = sum(1 for unit in units if unit.get('current_status') == 'occupied')
                        occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

                        occupancy_data.append({
                            'Property': prop['name'],
                            'Total Units': total_units,
                            'Occupied': occupied_units,
                            'Vacant': total_units - occupied_units,
                            'Occupancy Rate': occupancy_rate
                        })

                    if occupancy_data:
                        occupancy_df = pd.DataFrame(occupancy_data)

                        col1, col2 = st.columns(2)

                        with col1:
                            # Occupancy rate bar chart
                            fig_occupancy = px.bar(
                                occupancy_df,
                                x='Property',
                                y='Occupancy Rate',
                                title="Occupancy Rate by Property",
                                color='Occupancy Rate',
                                color_continuous_scale='RdYlGn'
                            )
                            fig_occupancy.update_layout(height=400)
                            st.plotly_chart(fig_occupancy, use_container_width=True)

                        with col2:
                            # Unit status breakdown
                            fig_units = px.bar(
                                occupancy_df,
                                x='Property',
                                y=['Occupied', 'Vacant'],
                                title="Unit Status by Property",
                                color_discrete_map={'Occupied': '#4CAF50', 'Vacant': '#FFC107'}
                            )
                            fig_units.update_layout(height=400)
                            st.plotly_chart(fig_units, use_container_width=True)

                    # Quick actions section
                    st.subheader("⚡ Quick Actions")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        if st.button("➕ Add New Tenant", use_container_width=True):
                            self.show_add_tenant_form()

                    with col2:
                        if st.button("🏠 Add New Property", use_container_width=True):
                            st.info("Property addition feature coming soon!")

                    with col3:
                        if st.button("📋 Create Lease", use_container_width=True):
                            st.info("Lease creation feature coming soon!")

                    with col4:
                        if st.button("🎫 Create Service Ticket", use_container_width=True):
                            st.info("Service ticket creation feature coming soon!")

                    # Alerts and notifications
                    self.show_dashboard_alerts(pending_payments, active_leases, open_tickets)

                except Exception as e:
                    st.error(f"Error loading dashboard data: {e}")
                    st.info("Please check your database connection and try refreshing the page.")

    def render_query_interface(self, tab):
            """Render natural language query interface"""
            with tab:
                st.subheader("🔍 Natural Language Query Interface")

                # Query input section
                st.write("Ask questions about your property data in natural language:")

                col1, col2 = st.columns([4, 1])

                with col1:
                    query = st.text_input(
                        "Enter your question:",
                        placeholder="e.g., 'Show me all tenants with pending payments' or 'Which properties have the highest occupancy?'",
                        help="Type your question in natural language",
                        key="main_query_input"
                    )

                with col2:
                    search_button = st.button("🔍 Search", type="primary", use_container_width=True)

                # Process query if button clicked
                if search_button and query:
                    self.process_natural_language_query(query)
                elif search_button and not query:
                    st.warning("Please enter a query")

                # Quick query suggestions
                st.subheader("💡 Quick Query Examples")

                # Organize examples by category
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write("**📊 Financial Queries**")
                    if st.button("💰 Show Financial Summary", key="fin_summary"):
                        self.show_financial_summary()

                    if st.button("💳 Pending Payments", key="pending_pay"):
                        self.show_pending_payments()

                    if st.button("📈 Revenue Analysis", key="revenue_analysis"):
                        st.info("Revenue analysis feature coming soon!")

                with col2:
                    st.write("**🏠 Property Queries**")
                    if st.button("🏠 List All Properties", key="all_props"):
                        self.show_all_properties()

                    if st.button("📊 Occupancy Analysis", key="occupancy"):
                        self.show_property_occupancy()

                    if st.button("🏢 Unit Details", key="unit_details"):
                        st.info("Unit details feature coming soon!")

                with col3:
                    st.write("**👥 Tenant & Lease Queries**")
                    if st.button("👥 Show All Tenants", key="all_tenants"):
                        self.show_all_tenants()

                    if st.button("⚠️ Expiring Leases", key="expiring_leases"):
                        self.show_expiring_leases()

                    if st.button("🎫 Open Service Tickets", key="open_tickets"):
                        self.show_open_tickets()

                # Query history section
                if st.session_state.query_history:
                    st.subheader("📜 Query History")

                    # Show last 10 queries
                    for i, (timestamp, query_text, result_type) in enumerate(reversed(st.session_state.query_history[-10:])):
                        with st.expander(f"🕒 {timestamp} - {query_text[:60]}{'...' if len(query_text) > 60 else ''}"):
                            col1, col2 = st.columns([3, 1])

                            with col1:
                                st.write(f"**Query:** {query_text}")
                                st.write(f"**Result Type:** {result_type}")
                                st.write(f"**Time:** {timestamp}")

                            with col2:
                                if st.button("🔄 Re-run", key=f"rerun_{i}"):
                                    self.process_natural_language_query(query_text)

                    # Clear history option
                    if st.button("🗑️ Clear Query History"):
                        st.session_state.query_history = []
                        st.success("Query history cleared!")

    def process_natural_language_query(self, query: str):
                """Process natural language query and return results"""
                query_lower = query.lower()
                timestamp = datetime.now().strftime("%H:%M:%S")

                try:
                    # Enhanced keyword-based query processing
                    if any(word in query_lower for word in ['tenant', 'tenants']):
                        if 'pending' in query_lower or 'payment' in query_lower:
                            self.show_tenants_with_pending_payments()
                            result_type = "Tenants with Pending Payments"
                        else:
                            self.show_all_tenants()
                            result_type = "All Tenants"

                    elif any(word in query_lower for word in ['property', 'properties']):
                        if 'occupancy' in query_lower or 'occupied' in query_lower:
                            self.show_property_occupancy()
                            result_type = "Property Occupancy"
                        else:
                            self.show_all_properties()
                            result_type = "All Properties"

                    elif any(word in query_lower for word in ['payment', 'payments']):
                        if 'pending' in query_lower:
                            self.show_pending_payments()
                            result_type = "Pending Payments"
                        else:
                            self.show_financial_summary()
                            result_type = "Financial Summary"

                    elif any(word in query_lower for word in ['lease', 'leases']):
                        if 'expir' in query_lower:
                            self.show_expiring_leases()
                            result_type = "Expiring Leases"
                        else:
                            self.show_active_leases()
                            result_type = "Active Leases"

                    elif any(word in query_lower for word in ['ticket', 'tickets', 'service']):
                        self.show_open_tickets()
                        result_type = "Service Tickets"

                    elif any(word in query_lower for word in ['financial', 'money', 'revenue', 'income']):
                        self.show_financial_summary()
                        result_type = "Financial Summary"

                    else:
                        st.info("I couldn't understand your query. Please try using keywords like 'tenants', 'properties', 'payments', 'leases', or 'tickets'.")
                        result_type = "Unrecognized Query"

                    # Add to query history
                    st.session_state.query_history.append((timestamp, query, result_type))

                except Exception as e:
                    st.error(f"Error processing query: {e}")

    def show_all_tenants(self):
                  """Display all tenants"""
                  st.subheader("👥 All Tenants")
                  try:
                      tenants = self.pm.get_all_tenants()
                      if tenants:
                          df = pd.DataFrame(tenants)
                          st.dataframe(df, use_container_width=True)

                          # Download button
                          csv = df.to_csv(index=False)
                          st.download_button(
                              label="📥 Download as CSV",
                              data=csv,
                              file_name=f"tenants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                              mime="text/csv"
                          )
                      else:
                          st.info("No tenants found")
                  except Exception as e:
                      st.error(f"Error loading tenants: {e}")

    def show_all_properties(self):
                  """Display all properties"""
                  st.subheader("🏠 All Properties")
                  try:
                      properties = self.pm.get_all_properties()
                      if properties:
                          df = pd.DataFrame(properties)
                          st.dataframe(df, use_container_width=True)

                          # Show units for each property
                          st.subheader("🏢 Units by Property")
                          for prop in properties:
                              with st.expander(f"{prop['name']} - {prop['unit_count']} units"):
                                  units = self.pm.get_units_by_property(prop['id'])
                                  if units:
                                      units_df = pd.DataFrame(units)
                                      st.dataframe(units_df, use_container_width=True)
                      else:
                          st.info("No properties found")
                  except Exception as e:
                      st.error(f"Error loading properties: {e}")

    def show_financial_summary(self):
                  """Display financial summary"""
                  st.subheader("💰 Financial Summary")
                  try:
                      summary = self.pm.get_financial_summary()

                      col1, col2, col3, col4 = st.columns(4)

                      with col1:
                          st.metric(
                              "Total Collected",
                              f"RM {summary.get('total_collected', 0):,.2f}",
                              help="Total payments received this month"
                          )

                      with col2:
                          st.metric(
                              "Total Pending",
                              f"RM {summary.get('total_pending', 0):,.2f}",
                              help="Total payments pending this month"
                          )

                      with col3:
                          st.metric(
                              "Payments Received",
                              summary.get('payments_received', 0),
                              help="Number of payments received"
                          )

                      with col4:
                          st.metric(
                              "Payments Pending",
                              summary.get('payments_pending', 0),
                              help="Number of payments pending"
                          )

                      # Collection rate
                      total_amount = summary.get('total_collected', 0) + summary.get('total_pending', 0)
                      if total_amount > 0:
                          collection_rate = (summary.get('total_collected', 0) / total_amount) * 100
                          st.progress(collection_rate / 100)
                          st.write(f"**Collection Rate:** {collection_rate:.1f}%")

                  except Exception as e:
                      st.error(f"Error loading financial summary: {e}")

    def show_pending_payments(self):
            """Display pending payments"""
            st.subheader("💳 Pending Payments")
            try:
                payments = self.pm.get_pending_payments()
                if payments:
                    df = pd.DataFrame(payments)

                    # Add overdue indicator
                    df['due_date'] = pd.to_datetime(df['due_date'])
                    df['days_overdue'] = (datetime.now() - df['due_date']).dt.days
                    df['status'] = df['days_overdue'].apply(
                        lambda x: 'Overdue' if x > 0 else 'Due Soon' if x > -7 else 'Current'
                    )

                    st.dataframe(df, use_container_width=True)

                    # Summary statistics
                    total_pending = df['amount'].sum()
                    overdue_amount = df[df['status'] == 'Overdue']['amount'].sum()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Pending", f"RM {total_pending:,.2f}")
                    with col2:
                        st.metric("Overdue Amount", f"RM {overdue_amount:,.2f}")

                else:
                    st.success("No pending payments!")
            except Exception as e:
                st.error(f"Error loading pending payments: {e}")

    def show_expiring_leases(self):
        """Display expiring leases"""
        st.subheader("⚠️ Expiring Leases (Next 30 Days)")
        try:
            leases = self.pm.get_expiring_leases(30)
            if leases:
                df = pd.DataFrame(leases)
                df['end_date'] = pd.to_datetime(df['end_date'])
                df['days_until_expiry'] = (df['end_date'] - datetime.now()).dt.days

                st.dataframe(df, use_container_width=True)

                # Alert for urgent renewals
                urgent_leases = df[df['days_until_expiry'] <= 7]
                if not urgent_leases.empty:
                    st.error(f"🚨 {len(urgent_leases)} lease(s) expiring within 7 days!")
            else:
                st.success("No leases expiring in the next 30 days")
        except Exception as e:
            st.error(f"Error loading expiring leases: {e}")

    def show_active_leases(self):
        """Display active leases"""
        st.subheader("📋 Active Leases")
        try:
            leases = self.pm.get_active_leases()
            if leases:
                df = pd.DataFrame(leases)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No active leases found")
        except Exception as e:
            st.error(f"Error loading active leases: {e}")

    def show_open_tickets(self):
        """Display open service tickets"""
        st.subheader("🎫 Open Service Tickets")
        try:
            tickets = self.pm.get_open_tickets()
            if tickets:
                df = pd.DataFrame(tickets)

                # Priority color coding
                priority_colors = {
                    'low': '🟢',
                    'normal': '🟡',
                    'high': '🟠',
                    'urgent': '🔴'
                }

                df['priority_icon'] = df['priority'].map(priority_colors)

                st.dataframe(df, use_container_width=True)

                # Ticket statistics
                priority_counts = df['priority'].value_counts()

                st.subheader("📊 Ticket Statistics")
                col1, col2, col3, col4 = st.columns(4)

                priorities = ['urgent', 'high', 'normal', 'low']
                colors = ['🔴', '🟠', '🟡', '🟢']

                for i, (priority, color) in enumerate(zip(priorities, colors)):
                    count = priority_counts.get(priority, 0)
                    with [col1, col2, col3, col4][i]:
                        st.metric(f"{color} {priority.title()}", count)
            else:
                st.success("No open service tickets!")
        except Exception as e:
            st.error(f"Error loading service tickets: {e}")

    def show_tenants_with_pending_payments(self):
        """Display tenants with pending payments"""
        st.subheader("👥💳 Tenants with Pending Payments")
        try:
            payments = self.pm.get_pending_payments()
            if payments:
                # Group by tenant
                tenant_payments = {}
                for payment in payments:
                    tenant_name = payment.get('tenant_name', 'Unknown')
                    if tenant_name not in tenant_payments:
                        tenant_payments[tenant_name] = []
                    tenant_payments[tenant_name].append(payment)

                for tenant_name, tenant_payment_list in tenant_payments.items():
                    total_amount = sum(p['amount'] for p in tenant_payment_list)

                    with st.expander(f"{tenant_name} - RM {total_amount:,.2f} pending"):
                        df = pd.DataFrame(tenant_payment_list)
                        st.dataframe(df[['payment_type', 'amount', 'due_date', 'property_name']],
                                   use_container_width=True)
            else:
                st.success("No tenants with pending payments!")
        except Exception as e:
            st.error(f"Error loading tenant payment data: {e}")

    def show_property_occupancy(self):
        """Display property occupancy statistics"""
        st.subheader("🏢 Property Occupancy Analysis")
        try:
            properties = self.pm.get_all_properties()
            occupancy_data = []

            for prop in properties:
                units = self.pm.get_units_by_property(prop['id'])
                total_units = len(units)
                occupied_units = sum(1 for unit in units if unit.get('current_status') == 'occupied')
                occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

                occupancy_data.append({
                    'Property': prop['name'],
                    'Total Units': total_units,
                    'Occupied Units': occupied_units,
                    'Vacant Units': total_units - occupied_units,
                    'Occupancy Rate': f"{occupancy_rate:.1f}%"
                })

            if occupancy_data:
                df = pd.DataFrame(occupancy_data)
                st.dataframe(df, use_container_width=True)

                # Occupancy rate chart
                fig = px.bar(
                    df,
                    x='Property',
                    y=['Occupied Units', 'Vacant Units'],
                    title="Unit Occupancy by Property"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No occupancy data available")

        except Exception as e:
            st.error(f"Error loading occupancy data: {e}")

    def render_data_management(self, tab):
        """Render data management interface"""
        with tab:
            st.subheader("📋 Data Management")

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📊 Raw Data Access")

                # Table selection
                table_options = [
                    'tenants', 'properties', 'units', 'leases',
                    'payments', 'service_tickets', 'agents'
                ]

                selected_table = st.selectbox("Select table to view:", table_options)

                if st.button("Load Table Data"):
                    self.show_table_data(selected_table)

            with col2:
                st.subheader("📁 Document Processing")

                if st.session_state.uploaded_files:
                    st.write(f"**Files uploaded:** {len(st.session_state.uploaded_files)}")

                    for file in st.session_state.uploaded_files:
                        with st.expander(f"📄 {file.name}"):
                            self.process_uploaded_file(file)
                else:
                    st.info("No files uploaded. Use the sidebar to upload documents.")

            # SQL Query Interface
            st.subheader("🔍 SQL Query Interface")
            st.warning("⚠️ Advanced users only. Be careful with SQL queries.")

            sql_query = st.text_area(
                "Enter SQL query:",
                placeholder="SELECT * FROM tenants LIMIT 10;",
                height=100
            )

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("Execute Query"):
                    if sql_query.strip():
                        self.execute_sql_query(sql_query)
                    else:
                        st.warning("Please enter a SQL query")

    def show_table_data(self, table_name: str):
        """Display raw table data"""
        try:
            conn = self.pm.db.get_connection()
            query = f"SELECT * FROM {table_name} LIMIT 100"
            df = pd.read_sql_query(query, conn)
            conn.close()

            st.subheader(f"📊 {table_name.title()} Data")
            st.dataframe(df, use_container_width=True)

            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"Error loading table data: {e}")

    def process_uploaded_file(self, file):
        """Process uploaded file and show analysis"""
        try:
            file_extension = file.name.split('.')[-1].lower()

            if file_extension == 'csv':
                df = pd.read_csv(file)
                st.write("**CSV File Preview:**")
                st.dataframe(df.head(), use_container_width=True)

                st.write(f"**Shape:** {df.shape[0]} rows, {df.shape[1]} columns")
                st.write("**Columns:**", list(df.columns))

            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(file)
                st.write("**Excel File Preview:**")
                st.dataframe(df.head(), use_container_width=True)

                st.write(f"**Shape:** {df.shape[0]} rows, {df.shape[1]} columns")

            elif file_extension == 'json':
                data = json.load(file)
                st.write("**JSON File Content:**")
                st.json(data)

            elif file_extension == 'txt':
                content = file.read().decode('utf-8')
                st.write("**Text File Content:**")
                st.text_area("File Content", content, height=200)

            elif file_extension == 'pdf':
                st.write("**PDF File Uploaded:**")
                st.info("PDF processing requires additional libraries. File uploaded successfully.")

        except Exception as e:
            st.error(f"Error processing file {file.name}: {e}")

    def execute_sql_query(self, query: str):
        """Execute SQL query and show results"""
        try:
            # Basic security check
            dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE']
            query_upper = query.upper()

            if any(keyword in query_upper for keyword in dangerous_keywords):
                st.error("❌ Dangerous SQL operations are not allowed. Use SELECT queries only.")
                return

            conn = self.pm.db.get_connection()
            df = pd.read_sql_query(query, conn)
            conn.close()

            st.success("✅ Query executed successfully!")
            st.dataframe(df, use_container_width=True)

            # Download option
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results",
                data=csv,
                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )

        except Exception as e:
            st.error(f"SQL Query Error: {e}")

    def render_analytics(self, tab):
        """Render analytics and reporting interface"""
        with tab:
            st.subheader("📈 Analytics & Reports")

            # Report type selection
            report_type = st.selectbox(
                "Select Report Type:",
                [
                    "Financial Summary",
                    "Occupancy Analysis",
                    "Lease Expiry Report",
                    "Payment Analysis",
                    "Service Ticket Analytics"
                ]
            )

            if report_type == "Financial Summary":
                self.render_financial_analytics()
            elif report_type == "Occupancy Analysis":
                self.render_occupancy_analytics()
            elif report_type == "Lease Expiry Report":
                self.render_lease_analytics()
            elif report_type == "Payment Analysis":
                self.render_payment_analytics()
            elif report_type == "Service Ticket Analytics":
                self.render_ticket_analytics()

    def render_financial_analytics(self):
        """Render detailed financial analytics"""
        st.subheader("💰 Financial Analytics")

        try:
            payments = self.pm.get_pending_payments()
            summary = self.pm.get_financial_summary()

            # Summary metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Monthly Collected", f"RM {summary.get('total_collected', 0):,.2f}")
            with col2:
                st.metric("Monthly Pending", f"RM {summary.get('total_pending', 0):,.2f}")
            with col3:
                collection_rate = (summary.get('total_collected', 0) /
                                 (summary.get('total_collected', 0) + summary.get('total_pending', 0)) * 100) if (summary.get('total_collected', 0) + summary.get('total_pending', 0)) > 0 else 0
                st.metric("Collection Rate", f"{collection_rate:.1f}%")

            # Payment analysis charts
            if payments:
                df_payments = pd.DataFrame(payments)

                col1, col2 = st.columns(2)

                with col1:
                    # Payment types distribution
                    payment_types = df_payments['payment_type'].value_counts()
                    fig_types = px.pie(
                        values=payment_types.values,
                        names=payment_types.index,
                        title="Pending Payments by Type"
                    )
                    st.plotly_chart(fig_types, use_container_width=True)

                with col2:
                    # Payment amounts by property
                    property_amounts = df_payments.groupby('property_name')['amount'].sum().sort_values(ascending=False)
                    fig_property = px.bar(
                        x=property_amounts.index,
                        y=property_amounts.values,
                        title="Pending Amounts by Property"
                    )
                    st.plotly_chart(fig_property, use_container_width=True)

        except Exception as e:
            st.error(f"Error generating financial analytics: {e}")

    def render_occupancy_analytics(self):
        """Render occupancy analytics"""
        st.subheader("🏢 Occupancy Analytics")

        try:
            properties = self.pm.get_all_properties()
            all_occupancy_data = []

            for prop in properties:
                units = self.pm.get_units_by_property(prop['id'])
                total_units = len(units)
                occupied_units = sum(1 for unit in units if unit.get('current_status') == 'occupied')
                occupancy_rate = (occupied_units / total_units * 100) if total_units > 0 else 0

                all_occupancy_data.append({
                    'Property': prop['name'],
                    'Total Units': total_units,
                    'Occupied Units': occupied_units,
                    'Vacant Units': total_units - occupied_units,
                    'Occupancy Rate': occupancy_rate
                })

            if all_occupancy_data:
                df_occupancy = pd.DataFrame(all_occupancy_data)

                # Occupancy rate chart
                fig_occupancy = px.bar(
                    df_occupancy,
                    x='Property',
                    y='Occupancy Rate',
                    title="Occupancy Rate by Property",
                    color='Occupancy Rate',
                    color_continuous_scale='RdYlGn'
                )
                st.plotly_chart(fig_occupancy, use_container_width=True)

                # Detailed breakdown
                st.dataframe(df_occupancy, use_container_width=True)

        except Exception as e:
            st.error(f"Error generating occupancy analytics: {e}")

    def render_lease_analytics(self):
        """Render lease expiry analytics"""
        st.subheader("📋 Lease Expiry Analytics")

        try:
            active_leases = self.pm.get_active_leases()

            if active_leases:
                df_leases = pd.DataFrame(active_leases)
                df_leases['end_date'] = pd.to_datetime(df_leases['end_date'])
                df_leases['days_until_expiry'] = (df_leases['end_date'] - datetime.now()).dt.days

                # Summary metrics
                expiring_30 = len(df_leases[df_leases['days_until_expiry'] <= 30])
                total_rent_at_risk = df_leases[df_leases['days_until_expiry'] <= 30]['rent_amount'].sum()

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Active Leases", len(df_leases))
                with col2:
                    st.metric("Expiring in 30 days", expiring_30)
                with col3:
                    st.metric("Rent at Risk (30d)", f"RM {total_rent_at_risk:,.2f}")

                # Detailed expiry list
                st.subheader("⚠️ Urgent Renewals (Next 30 Days)")
                urgent_renewals = df_leases[df_leases['days_until_expiry'] <= 30].sort_values('days_until_expiry')
                if not urgent_renewals.empty:
                    st.dataframe(urgent_renewals[['tenant_name', 'property_name', 'unit_number', 'end_date', 'days_until_expiry', 'rent_amount']], use_container_width=True)
                else:
                    st.success("No urgent lease renewals needed!")

        except Exception as e:
            st.error(f"Error generating lease analytics: {e}")

    def render_payment_analytics(self):
        """Render payment analytics"""
        st.subheader("💳 Payment Analytics")

        try:
            pending_payments = self.pm.get_pending_payments()

            if pending_payments:
                df_payments = pd.DataFrame(pending_payments)
                df_payments['due_date'] = pd.to_datetime(df_payments['due_date'])
                df_payments['days_overdue'] = (datetime.now() - df_payments['due_date']).dt.days

                # Summary metrics
                total_pending = df_payments['amount'].sum()
                overdue_amount = df_payments[df_payments['days_overdue'] > 0]['amount'].sum()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Pending", f"RM {total_pending:,.2f}")
                with col2:
                    st.metric("Overdue Amount", f"RM {overdue_amount:,.2f}")

                # Payment type analysis
                type_amounts = df_payments.groupby('payment_type')['amount'].sum()
                fig_types = px.bar(
                    x=type_amounts.index,
                    y=type_amounts.values,
                    title="Pending Amounts by Payment Type"
                )
                st.plotly_chart(fig_types, use_container_width=True)

        except Exception as e:
            st.error(f"Error generating payment analytics: {e}")

    def render_ticket_analytics(self):
        """Render service ticket analytics"""
        st.subheader("🎫 Service Ticket Analytics")

        try:
            tickets = self.pm.get_open_tickets()

            if tickets:
                df_tickets = pd.DataFrame(tickets)

                # Summary metrics
                total_tickets = len(df_tickets)
                high_priority = len(df_tickets[df_tickets['priority'].isin(['high', 'urgent'])])

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Open Tickets", total_tickets)
                with col2:
                    st.metric("High Priority", high_priority)

                # Priority distribution
                priority_counts = df_tickets['priority'].value_counts()
                fig_priority = px.pie(
                    values=priority_counts.values,
                    names=priority_counts.index,
                    title="Tickets by Priority"
                )
                st.plotly_chart(fig_priority, use_container_width=True)

        except Exception as e:
            st.error(f"Error generating ticket analytics: {e}")

    def render_ai_assistant(self, tab):
        """Render AI assistant interface"""
        with tab:
            st.subheader("💬 AI Property Management Assistant")

            if not st.session_state.api_key:
                st.warning("⚠️ Please configure your API key in the sidebar to unlock AI features.")

                with st.expander("🔧 AI Assistant Capabilities"):
                    st.markdown("""
                    **What the AI Assistant can do:**

                    🤖 **Data Analysis & Insights**
                    - Analyze payment patterns and identify trends
                    - Predict maintenance needs based on historical data
                    - Identify high-risk tenants or properties
                    - Generate financial forecasts and recommendations

                    📊 **Automated Reporting**
                    - Create executive summaries
                    - Generate property performance reports
                    - Analyze occupancy trends and optimization opportunities
                    - Provide market insights and comparisons

                    💡 **Smart Recommendations**
                    - Suggest rent optimization strategies
                    - Recommend maintenance schedules
                    - Identify cost-saving opportunities
                    - Propose tenant retention strategies
                    """)
                return

            st.success(f"🤖 AI Assistant Ready! Using {st.session_state.get('api_provider', 'OpenAI')}")

            # Chat interface
            if "chat_messages" not in st.session_state:
                st.session_state.chat_messages = [
                    {
                        "role": "assistant",
                        "content": "Hello! I'm your AI Property Management Assistant. I can help you analyze your property data, generate insights, and answer questions about your portfolio. What would you like to know?"
                    }
                ]

            # Display chat history
            for message in st.session_state.chat_messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Chat input
            if prompt := st.chat_input("Ask me anything about your property portfolio..."):
                # Add user message
                st.session_state.chat_messages.append({"role": "user", "content": prompt})

                with st.chat_message("user"):
                    st.markdown(prompt)

                # Generate AI response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = self.generate_ai_response(prompt)
                        st.markdown(response)

                # Add assistant response
                st.session_state.chat_messages.append({"role": "assistant", "content": response})

            # Example prompts
            st.subheader("💡 Example Questions")

            example_prompts = [
                "What are the top 3 properties with highest pending payments?",
                "Analyze tenant payment behavior patterns",
                "Which properties need immediate maintenance attention?",
                "Predict next month's revenue based on current trends",
                "What are the main factors affecting occupancy rates?",
                "How can we improve our rent collection efficiency?"
            ]

            col1, col2 = st.columns(2)

            for i, prompt in enumerate(example_prompts):
                with col1 if i % 2 == 0 else col2:
                    if st.button(f"💬 {prompt}", key=f"example_{i}"):
                        # Add to chat and process
                        st.session_state.chat_messages.append({"role": "user", "content": prompt})
                        response = self.generate_ai_response(prompt)
                        st.session_state.chat_messages.append({"role": "assistant", "content": response})
                        st.rerun()

            # Chat controls
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🗑️ Clear Chat History"):
                    st.session_state.chat_messages = []
                    st.rerun()

            with col2:
                if st.button("📥 Export Chat"):
                    chat_data = json.dumps(st.session_state.chat_messages, indent=2)
                    st.download_button(
                        label="Download Chat History",
                        data=chat_data,
                        file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

    # Utility methods for the Streamlit app

    def is_payment_overdue(self, payment: Dict) -> bool:
        """Check if a payment is overdue"""
        if payment.get('due_date'):
            try:
                due_date = datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
                return datetime.now().date() > due_date
            except ValueError:
                return False
        return False

    def calculate_days_overdue(self, payment: Dict) -> int:
        """Calculate days overdue for a payment"""
        if payment.get('due_date'):
            try:
                due_date = datetime.strptime(payment['due_date'], '%Y-%m-%d').date()
                today = datetime.now().date()
                days_diff = (today - due_date).days
                return max(0, days_diff)
            except ValueError:
                return 0
        return 0

    def show_dashboard_alerts(self, pending_payments, active_leases, open_tickets):
        """Show important alerts on dashboard"""
        alerts = []

        # Check for overdue payments
        overdue_payments = [p for p in pending_payments if self.is_payment_overdue(p)]
        if overdue_payments:
            total_overdue = sum(p['amount'] for p in overdue_payments)
            alerts.append({
                'type': 'error',
                'title': 'Overdue Payments',
                'message': f"{len(overdue_payments)} payments totaling RM {total_overdue:,.2f} are overdue"
            })

        # Check for expiring leases
        expiring_leases = []
        for lease in active_leases:
            try:
                end_date = datetime.strptime(lease['end_date'], '%Y-%m-%d').date()
                days_until_expiry = (end_date - datetime.now().date()).days
                if 0 <= days_until_expiry <= 30:
                    expiring_leases.append(lease)
            except ValueError:
                continue

        if expiring_leases:
            alerts.append({
                'type': 'warning',
                'title': 'Expiring Leases',
                'message': f"{len(expiring_leases)} leases expiring within 30 days"
            })

        # Check for urgent tickets
        urgent_tickets = [t for t in open_tickets if t.get('priority') == 'urgent']
        if urgent_tickets:
            alerts.append({
                'type': 'error',
                'title': 'Urgent Service Tickets',
                'message': f"{len(urgent_tickets)} urgent tickets require immediate attention"
            })

        # Display alerts
        if alerts:
            st.subheader("🚨 System Alerts")
            for alert in alerts:
                if alert['type'] == 'error':
                    st.error(f"**{alert['title']}:** {alert['message']}")
                elif alert['type'] == 'warning':
                    st.warning(f"**{alert['title']}:** {alert['message']}")
                else:
                    st.info(f"**{alert['title']}:** {alert['message']}")

    def generate_ai_response(self, prompt: str) -> str:
        """Generate AI response (enhanced placeholder)"""
        prompt_lower = prompt.lower()

        # Enhanced response logic based on keywords and context
        if "portfolio" in prompt_lower and "perform" in prompt_lower:
            try:
                # Get comprehensive data
                properties = self.pm.get_all_properties()
                financial_summary = self.pm.get_financial_summary()
                active_leases = self.pm.get_active_leases()

                total_properties = len(properties)
                total_revenue = financial_summary.get('total_collected', 0)
                occupancy_rate = self.calculate_overall_occupancy()

                return f"""**Portfolio Performance Analysis:**

**📊 Key Metrics:**
- **Properties:** {total_properties} managed properties
- **Monthly Revenue:** RM {total_revenue:,.2f}
- **Occupancy Rate:** {occupancy_rate:.1f}%
- **Active Leases:** {len(active_leases)}

**💡 Performance Insights:**
- Your portfolio shows {"strong" if occupancy_rate > 85 else "moderate" if occupancy_rate > 70 else "weak"} occupancy performance
- Revenue collection is {"excellent" if total_revenue > 10000 else "good" if total_revenue > 5000 else "needs improvement"}
- {"Consider rent optimization for underperforming properties" if occupancy_rate < 80 else "Maintain current strategies for optimal performance"}

**🎯 Recommendations:**
- Focus on {"improving occupancy rates" if occupancy_rate < 85 else "maintaining high occupancy"}
- {"Implement payment reminder systems" if financial_summary.get('total_pending', 0) > 5000 else "Continue current collection practices"}
- Regular property maintenance to ensure tenant satisfaction"""

            except Exception as e:
                return f"I encountered an error analyzing your portfolio: {e}"

        elif "payment" in prompt_lower or "financial" in prompt_lower:
            try:
                summary = self.pm.get_financial_summary()
                pending_payments = self.pm.get_pending_payments()

                collection_rate = 0
                if summary.get('total_collected', 0) + summary.get('total_pending', 0) > 0:
                    collection_rate = (summary.get('total_collected', 0) /
                                     (summary.get('total_collected', 0) + summary.get('total_pending', 0))) * 100

                overdue_count = len([p for p in pending_payments if self.is_payment_overdue(p)])

                return f"""**Financial Analysis & Insights:**

**💰 Current Financial Status:**
- **Monthly Collected:** RM {summary.get('total_collected', 0):,.2f}
- **Pending Payments:** RM {summary.get('total_pending', 0):,.2f}
- **Collection Rate:** {collection_rate:.1f}%
- **Overdue Payments:** {overdue_count} payments

**📈 Performance Assessment:**
Your collection rate of {collection_rate:.1f}% is {"excellent" if collection_rate > 90 else "good" if collection_rate > 80 else "needs improvement"}.

**🎯 Recommendations:**
{"- Implement automated payment reminders" if collection_rate < 85 else "- Continue current collection strategies"}
{"- Consider payment plan options for overdue accounts" if overdue_count > 0 else "- Maintain proactive tenant communication"}
- Monitor payment patterns for early intervention opportunities
- Consider incentives for early/on-time payments"""

            except Exception as e:
                return f"I encountered an error analyzing financial data: {e}"

        elif "maintenance" in prompt_lower or "service" in prompt_lower or "ticket" in prompt_lower:
            try:
                tickets = self.pm.get_open_tickets()

                if not tickets:
                    return "**Service & Maintenance Status:** ✅ Excellent! No open service tickets currently."

                urgent_count = len([t for t in tickets if t.get('priority') == 'urgent'])
                high_count = len([t for t in tickets if t.get('priority') == 'high'])

                # Analyze categories
                categories = {}
                for ticket in tickets:
                    cat = ticket.get('category', 'Unknown')
                    categories[cat] = categories.get(cat, 0) + 1

                most_common = max(categories, key=categories.get) if categories else "Unknown"

                return f"""**Service & Maintenance Analysis:**

**🎫 Current Ticket Status:**
- **Total Open Tickets:** {len(tickets)}
- **Urgent Priority:** {urgent_count} tickets
- **High Priority:** {high_count} tickets
- **Most Common Category:** {most_common} ({categories.get(most_common, 0)} tickets)

**⚠️ Priority Actions:**
{f"- Immediate attention needed for {urgent_count} urgent tickets" if urgent_count > 0 else "- No urgent tickets requiring immediate attention"}
{f"- Address {high_count} high-priority requests promptly" if high_count > 0 else "- All tickets are normal or low priority"}

**💡 Maintenance Insights:**
- {most_common} issues are most frequent - consider preventive measures
- {"High ticket volume suggests need for additional maintenance staff" if len(tickets) > 10 else "Ticket volume is manageable with current resources"}
- Regular preventive maintenance can reduce emergency repairs"""

            except Exception as e:
                return f"I encountered an error analyzing service tickets: {e}"

        else:
            return f"""**🤖 AI Assistant Ready to Help!**

I can analyze your property management data and provide insights on:

**📊 Available Analysis:**
- **Financial Performance:** Revenue trends, collection rates, payment patterns
- **Portfolio Analytics:** Occupancy rates, property performance comparisons
- **Tenant Insights:** Retention patterns, payment behavior, demographics
- **Maintenance Intelligence:** Service trends, cost optimization, preventive care
- **Predictive Modeling:** Revenue forecasts, occupancy predictions, risk assessment

**💬 Try asking me:**
- "How is our financial performance this month?"
- "Which properties need the most attention?"
- "What trends do you see in our payment data?"
- "Predict our revenue for next quarter"
- "What maintenance issues are most common?"

**🎯 I can also provide:**
- Strategic recommendations for growth
- Risk analysis and mitigation strategies
- Operational efficiency suggestions
- Market insights and competitive analysis

*What specific aspect of your property portfolio would you like me to analyze?*"""

    def calculate_overall_occupancy(self) -> float:
        """Calculate overall portfolio occupancy rate"""
        try:
            properties = self.pm.get_all_properties()
            total_units = 0
            occupied_units = 0

            for prop in properties:
                units = self.pm.get_units_by_property(prop['id'])
                total_units += len(units)
                occupied_units += sum(1 for unit in units if unit.get('current_status') == 'occupied')

            return (occupied_units / total_units * 100) if total_units > 0 else 0
        except:
            return 0

    def show_add_tenant_form(self):
        """Show form to add new tenant"""
        with st.form("add_tenant_form"):
            st.subheader("➕ Add New Tenant")

            col1, col2 = st.columns(2)

            with col1:
                first_name = st.text_input("First Name*", placeholder="Ahmad")
                email = st.text_input("Email*", placeholder="ahmad@example.com")
                date_of_birth = st.date_input("Date of Birth")

            with col2:
                last_name = st.text_input("Last Name*", placeholder="Rahman")
                phone = st.text_input("Phone", placeholder="012-3456789")

            submitted = st.form_submit_button("➕ Add Tenant", type="primary")

            if submitted:
                if first_name and last_name and email:
                    try:
                        # Validate email
                        if not DataValidator.validate_email(email):
                            st.error("Please enter a valid email address")
                            return

                        # Validate phone if provided
                        if phone and not DataValidator.validate_phone(phone):
                            st.warning("Phone number format might be invalid (expected Malaysian format)")

                        tenant_id = self.pm.add_tenant(
                            first_name=first_name,
                            last_name=last_name,
                            email=email,
                            phone=phone,
                            date_of_birth=date_of_birth.strftime('%Y-%m-%d') if date_of_birth else None
                        )

                        st.success(f"✅ Tenant added successfully! ID: {tenant_id}")

                    except Exception as e:
                        st.error(f"Error adding tenant: {e}")
                else:
                    st.error("Please fill in all required fields (*)")

    def clear_cache(self):
        """Clear application cache"""
        st.session_state.data_cache = {}
        st.session_state.query_history = []
        if 'chat_messages' in st.session_state:
            st.session_state.chat_messages = []

    def reset_application(self):
        """Reset all application state"""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    def run(self):
        """Main application runner"""
        # Render sidebar
        self.render_sidebar()

        # Render main content
        tab1, tab2, tab3, tab4, tab5 = self.render_main_header()

        # Render each tab
        self.render_dashboard(tab1)
        self.render_query_interface(tab2)
        self.render_data_management(tab3)
        self.render_analytics(tab4)
        self.render_ai_assistant(tab5)

        # Footer
        st.markdown("---")
        st.markdown(
            "<div style='text-align: center; color: #666;'>"
            "🏢 Property Management System v1.0 | "
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            "</div>",
            unsafe_allow_html=True
        )


def main():
    """Main application entry point"""
    try:
        app = StreamlitPropertyApp()
        app.run()
    except Exception as e:
        st.error(f"Application error: {e}")
        st.info("Please ensure all required files (main.py, models.py, config.py) are present and the database is properly initialized.")

        # Debug information
        with st.expander("🔧 Debug Information"):
            st.write("**Current working directory:**", os.getcwd())
            st.write("**Files in directory:**", os.listdir('.'))
            st.write("**Python path:**", sys.path[:3])


if __name__ == "__main__":
    main()
