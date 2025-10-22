"""
Cortex Cost Calculator - Streamlit in Snowflake
Hosted directly in Snowflake for seamless data access
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from snowflake.snowpark.context import get_active_session
import plotly.graph_objects as go
import plotly.express as px

# Get Snowflake session
session = get_active_session()

st.set_page_config(
    page_title="Cortex Cost Calculator",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# Utility Functions
# ============================================================================

def fetch_data_from_views(lookback_days=30):
    """Fetch data from historical snapshot table (with fallback to live view)"""
    # Try snapshot table first (faster)
    snapshot_query = f"""
    SELECT 
        date,
        service_type,
        daily_unique_users,
        total_operations,
        total_credits,
        credits_per_user,
        credits_per_operation,
        avg_daily_cost_per_user,
        projected_monthly_cost_per_user,
        projected_monthly_total_credits,
        credits_7d_ago,
        credits_wow_growth_pct
    FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_USAGE_HISTORY
    WHERE date >= DATEADD('day', -{lookback_days}, CURRENT_DATE())
    ORDER BY date DESC
    """
    
    try:
        df = session.sql(snapshot_query).to_pandas()
        if not df.empty:
            return df
    except:
        pass
    
    # Fallback to live view if snapshot is empty or doesn't exist
    live_query = f"""
    SELECT 
        date,
        service_type,
        daily_unique_users,
        total_operations,
        total_credits,
        credits_per_user,
        credits_per_operation,
        ROUND(credits_per_user, 4) AS avg_daily_cost_per_user,
        ROUND(credits_per_user * 30, 2) AS projected_monthly_cost_per_user,
        ROUND(total_credits * 30, 2) AS projected_monthly_total_credits,
        NULL AS credits_7d_ago,
        NULL AS credits_wow_growth_pct
    FROM SNOWFLAKE_EXAMPLE.CORTEX_USAGE.V_CORTEX_COST_EXPORT
    WHERE date >= DATEADD('day', -{lookback_days}, CURRENT_DATE())
    ORDER BY date DESC
    """
    return session.sql(live_query).to_pandas()

def calculate_30day_totals(df):
    """Calculate rolling 30-day totals for cost estimation"""
    if df.empty:
        return pd.DataFrame()
    
    # Sort by date ascending for rolling calculations
    df_sorted = df.sort_values('DATE')
    
    # Calculate 30-day rolling totals by service type
    df_sorted['credits_30d_total'] = df_sorted.groupby('SERVICE_TYPE')['TOTAL_CREDITS'].transform(
        lambda x: x.rolling(window=30, min_periods=1).sum()
    )
    
    df_sorted['operations_30d_total'] = df_sorted.groupby('SERVICE_TYPE')['TOTAL_OPERATIONS'].transform(
        lambda x: x.rolling(window=30, min_periods=1).sum()
    )
    
    df_sorted['users_30d_avg'] = df_sorted.groupby('SERVICE_TYPE')['DAILY_UNIQUE_USERS'].transform(
        lambda x: x.rolling(window=30, min_periods=1).mean()
    )
    
    # Calculate 30-day average cost per user
    df_sorted['cost_per_user_30d'] = df_sorted['credits_30d_total'] / df_sorted['users_30d_avg']
    df_sorted['cost_per_user_30d'] = df_sorted['cost_per_user_30d'].fillna(0)
    
    return df_sorted.sort_values('DATE', ascending=False)

def calculate_growth_projection(df, growth_rate, projection_months=12, credit_cost=3.00):
    """Calculate cost projections based on growth rate"""
    baseline = df.groupby('SERVICE_TYPE').agg({
        'TOTAL_CREDITS': 'sum',
        'DAILY_UNIQUE_USERS': 'mean'
    }).reset_index()
    
    projections = []
    for month in range(1, projection_months + 1):
        for _, service in baseline.iterrows():
            growth_factor = (1 + growth_rate) ** month
            projected_credits = service['TOTAL_CREDITS'] * growth_factor
            projected_users = service['DAILY_UNIQUE_USERS'] * growth_factor
            projected_cost = projected_credits * credit_cost
            
            projections.append({
                'month': month,
                'service_type': service['SERVICE_TYPE'],
                'projected_credits': projected_credits,
                'projected_users': projected_users,
                'projected_cost_usd': projected_cost,
                'cost_per_user_usd': projected_cost / projected_users if projected_users > 0 else 0,
                'growth_rate': growth_rate
            })
    
    return pd.DataFrame(projections)

def format_currency(value):
    """Format value as currency"""
    return f"${value:,.2f}"

def format_number(value):
    """Format value as number with commas"""
    return f"{value:,.0f}"

# ============================================================================
# Main Application
# ============================================================================

def load_data_from_csv(uploaded_file):
    """Load and validate data from uploaded CSV file"""
    try:
        df = pd.read_csv(uploaded_file)
        
        # Expected columns from extract_metrics_for_calculator.sql
        required_cols = ['DATE', 'SERVICE_TYPE', 'TOTAL_CREDITS']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            st.error(f"CSV missing required columns: {', '.join(missing_cols)}")
            return None
        
        # Standardize column names (handle case variations)
        df.columns = df.columns.str.upper()
        
        # Convert date column
        df['DATE'] = pd.to_datetime(df['DATE'])
        
        return df
    except Exception as e:
        st.error(f"Error loading CSV: {str(e)}")
        return None

def create_credit_summary(df, credit_cost=3.00):
    """Create credit estimate summary for sales team"""
    summary = df.groupby('SERVICE_TYPE').agg({
        'TOTAL_CREDITS': 'sum',
        'DAILY_UNIQUE_USERS': 'mean',
        'DATE': ['min', 'max']
    }).reset_index()
    
    summary.columns = ['Service', 'Total Credits', 'Avg Daily Users', 'Start Date', 'End Date']
    summary['Days of Data'] = (summary['End Date'] - summary['Start Date']).dt.days + 1
    summary['Avg Credits/Day'] = summary['Total Credits'] / summary['Days of Data']
    summary['Est. Credits/Month'] = summary['Avg Credits/Day'] * 30
    summary['Est. Cost/Month'] = summary['Est. Credits/Month'] * credit_cost
    
    return summary[['Service', 'Total Credits', 'Avg Credits/Day', 'Est. Credits/Month', 'Est. Cost/Month']]

def main():
    st.title("📊 Cortex Cost Calculator")
    st.markdown("""
    Estimate and project costs for Snowflake Cortex services based on actual usage data.
    **For Solution Engineers:** Upload customer CSV files or query your own account views.
    """)
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Data source selection
        data_source = st.radio(
            "Data Source",
            options=["Query Views (Same Account)", "Upload Customer CSV"],
            help="Query views for your own data, or upload CSV from customer account"
        )
        
        if data_source == "Query Views (Same Account)":
            lookback_days = st.slider(
                "Historical Data Period (days)",
                min_value=7,
                max_value=90,
                value=30,
                help="Number of days of historical data to analyze"
            )
        else:
            st.markdown("### 📁 Upload Customer Data")
            uploaded_file = st.file_uploader(
                "Upload CSV from extract_metrics_for_calculator.sql",
                type=['csv'],
                help="CSV file exported from customer's Snowflake account"
            )
        
        credit_cost = st.number_input(
            "Cost per Credit (USD)",
            value=3.00,
            min_value=0.01,
            step=0.10,
            help="Adjust based on your Snowflake pricing"
        )
        
        variance_pct = st.slider(
            "Projection Variance (%)",
            min_value=5,
            max_value=25,
            value=10,
            help="Variance range for cost estimates"
        ) / 100
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
    
    # Load data based on source
    df = None
    if data_source == "Query Views (Same Account)":
        try:
            with st.spinner("Loading data from views..."):
                df = fetch_data_from_views(lookback_days)
        except Exception as e:
            st.error(f"Error querying views: {str(e)}")
            st.info("Make sure monitoring views are deployed in SNOWFLAKE_EXAMPLE.CORTEX_USAGE")
            return
    else:
        if 'uploaded_file' in locals() and uploaded_file is not None:
            with st.spinner("Loading CSV file..."):
                df = load_data_from_csv(uploaded_file)
        else:
            st.info("👆 Please upload a CSV file from the customer's account")
            st.markdown("""
            **To get customer data:**
            1. Run `@sql/extract_metrics_for_calculator.sql` in customer's Snowflake
            2. Download results as CSV
            3. Upload here
            """)
            return
    
    if df is None or df.empty:
        st.warning("No data available. Please check your data source.")
        return
    
    # Normalize column names
    df.columns = df.columns.str.upper()
    if 'DATE' not in df.columns:
        df['DATE'] = pd.to_datetime(df['USAGE_DATE']) if 'USAGE_DATE' in df.columns else pd.to_datetime(df.iloc[:, 0])
    
    # Create tabs
    tab1, tab2, tab3 = st.tabs([
        "📈 Historical Analysis",
        "🔮 Cost Projections",
        "📋 Summary Report"
    ])
    
    with tab1:
        show_historical_analysis(df, credit_cost)
    
    with tab2:
        show_cost_projections(df, credit_cost, variance_pct)
    
    with tab3:
        show_summary_report(df, credit_cost, variance_pct)

def show_historical_analysis(df, credit_cost):
    """Display historical analysis tab"""
    st.header("Historical Usage Analysis")
    
    # Summary statistics
    total_credits = df['TOTAL_CREDITS'].sum()
    total_cost = total_credits * credit_cost
    avg_daily_credits = df.groupby('DATE')['TOTAL_CREDITS'].sum().mean()
    avg_daily_users = df['DAILY_UNIQUE_USERS'].mean()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Credits", format_number(total_credits))
    with col2:
        st.metric("Total Cost", format_currency(total_cost))
    with col3:
        st.metric("Avg Daily Credits", format_number(avg_daily_credits))
    with col4:
        st.metric("Avg Daily Users", format_number(avg_daily_users))
    
    st.divider()
    
    # 30-Day Rolling Totals
    st.subheader("📊 30-Day Rolling Totals (Most Recent)")
    st.caption("Rolling 30-day windows for cost estimation")
    
    # Calculate 30-day totals
    df_with_30d = calculate_30day_totals(df)
    
    if not df_with_30d.empty:
        # Get most recent 30-day totals by service
        latest_30d = df_with_30d.groupby('SERVICE_TYPE').last().reset_index()
        latest_30d['COST_30D_USD'] = latest_30d['credits_30d_total'] * credit_cost
        latest_30d['COST_PER_USER_30D_USD'] = latest_30d['cost_per_user_30d'] * credit_cost
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        total_30d_credits = latest_30d['credits_30d_total'].sum()
        total_30d_cost = total_30d_credits * credit_cost
        avg_30d_users = latest_30d['users_30d_avg'].mean()
        avg_cost_per_user_30d = total_30d_cost / avg_30d_users if avg_30d_users > 0 else 0
        
        with col1:
            st.metric("30-Day Total Credits", format_number(total_30d_credits))
        with col2:
            st.metric("30-Day Total Cost", format_currency(total_30d_cost))
        with col3:
            st.metric("30-Day Avg Users", format_number(avg_30d_users))
        with col4:
            st.metric("Avg Cost/User (30d)", format_currency(avg_cost_per_user_30d))
        
        # Service-level 30-day breakdown
        st.caption("30-Day Totals by Service")
        service_30d_display = latest_30d[['SERVICE_TYPE', 'credits_30d_total', 'COST_30D_USD', 
                                           'operations_30d_total', 'users_30d_avg', 'COST_PER_USER_30D_USD']].copy()
        service_30d_display.columns = ['Service', '30d Credits', '30d Cost', '30d Operations', '30d Avg Users', 'Cost/User (30d)']
        
        st.dataframe(
            service_30d_display.style.format({
                '30d Credits': '{:,.0f}',
                '30d Cost': '${:,.2f}',
                '30d Operations': '{:,.0f}',
                '30d Avg Users': '{:.1f}',
                'Cost/User (30d)': '${:,.2f}'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    st.divider()
    
    # Service breakdown
    st.subheader("Service Breakdown")
    service_agg = df.groupby('SERVICE_TYPE').agg({
        'TOTAL_CREDITS': 'sum',
        'DAILY_UNIQUE_USERS': 'mean',
        'TOTAL_OPERATIONS': 'sum'
    }).reset_index()
    service_agg['TOTAL_COST_USD'] = service_agg['TOTAL_CREDITS'] * credit_cost
    service_agg = service_agg.sort_values('TOTAL_CREDITS', ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(
            service_agg.style.format({
                'TOTAL_CREDITS': '{:,.0f}',
                'TOTAL_COST_USD': '${:,.2f}',
                'DAILY_UNIQUE_USERS': '{:.0f}',
                'TOTAL_OPERATIONS': '{:,.0f}'
            }),
            use_container_width=True
        )
    
    with col2:
        fig = px.pie(
            service_agg,
            values='TOTAL_CREDITS',
            names='SERVICE_TYPE',
            title='Credits by Service'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    
    # Usage trends
    st.subheader("Usage Trends")
    
    daily_totals = df.groupby(['DATE', 'SERVICE_TYPE'])['TOTAL_CREDITS'].sum().reset_index()
    
    fig = px.line(
        daily_totals,
        x='DATE',
        y='TOTAL_CREDITS',
        color='SERVICE_TYPE',
        title='Daily Credits Usage by Service'
    )
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

def show_cost_projections(df, credit_cost, variance_pct):
    """Display cost projections tab"""
    st.header("Cost Projections")
    
    # ========================================================================
    # Cost per User Calculator - MOVED TO TOP
    # ========================================================================
    st.subheader("💰 Cost per User Calculator")
    st.markdown("**Estimate per-user costs based on usage patterns**")
    
    show_cost_per_user_calculator(df, credit_cost)
    
    st.divider()
    st.divider()
    
    # ========================================================================
    # Growth-Based Cost Projections
    # ========================================================================
    st.header("📈 Growth-Based Cost Projections")
    
    col1, col2 = st.columns(2)
    
    with col1:
        projection_months = st.slider(
            "Projection Period (months)",
            min_value=3,
            max_value=24,
            value=12
        )
    
    with col2:
        growth_rate = st.slider(
            "Monthly Growth Rate (%)",
            min_value=0,
            max_value=100,
            value=25
        ) / 100
    
    # Calculate projection
    projection_df = calculate_growth_projection(df, growth_rate, projection_months, credit_cost)
    
    # Summary metrics
    monthly_totals = projection_df.groupby('month')['projected_cost_usd'].sum().reset_index()
    
    month_1_cost = monthly_totals[monthly_totals['month'] == 1]['projected_cost_usd'].iloc[0] if len(monthly_totals) > 0 else 0
    month_12_cost = monthly_totals[monthly_totals['month'] == 12]['projected_cost_usd'].iloc[0] if len(monthly_totals) >= 12 else 0
    total_year_cost = monthly_totals['projected_cost_usd'].sum()
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Month 1 Cost", format_currency(month_1_cost))
    with col2:
        st.metric("Month 12 Cost", format_currency(month_12_cost))
    with col3:
        st.metric("Total Year Cost", format_currency(total_year_cost))
    with col4:
        variance_range = f"±{format_currency(total_year_cost * variance_pct)}"
        st.metric("Variance Range", variance_range)
    
    st.divider()
    
    # Projection chart
    fig = go.Figure()
    
    monthly_totals['lower_bound'] = monthly_totals['projected_cost_usd'] * (1 - variance_pct)
    monthly_totals['upper_bound'] = monthly_totals['projected_cost_usd'] * (1 + variance_pct)
    
    fig.add_trace(go.Scatter(
        x=monthly_totals['month'],
        y=monthly_totals['upper_bound'],
        mode='lines',
        name=f'Upper (+{variance_pct*100:.0f}%)',
        line=dict(width=0),
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_totals['month'],
        y=monthly_totals['lower_bound'],
        mode='lines',
        name=f'Lower (-{variance_pct*100:.0f}%)',
        line=dict(width=0),
        fillcolor='rgba(41, 181, 232, 0.2)',
        fill='tonexty',
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=monthly_totals['month'],
        y=monthly_totals['projected_cost_usd'],
        mode='lines+markers',
        name='Projected Cost',
        line=dict(color='#29B5E8', width=3)
    ))
    
    fig.update_layout(
        title='Cost Projection with Variance Range',
        xaxis_title='Month',
        yaxis_title='Projected Cost (USD)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed table
    st.subheader("Monthly Breakdown")
    st.dataframe(
        monthly_totals.style.format({
            'projected_cost_usd': '${:,.2f}',
            'lower_bound': '${:,.2f}',
            'upper_bound': '${:,.2f}'
        }),
        use_container_width=True
    )

def show_cost_per_user_calculator(df, credit_cost):
    """
    Simplified calculator for cost per user estimation
    Shows: persona name, user count, requests per day, cost per request
    """
    
    # Calculate historical baseline metrics from usage data  
    df_with_30d = calculate_30day_totals(df)
    
    # Get most recent 30-day totals for reference
    if not df_with_30d.empty:
        latest_30d = df_with_30d.groupby('SERVICE_TYPE').last().reset_index()
        latest_30d['requests_per_day'] = latest_30d['operations_30d_total'] / 30
        latest_30d['users_in_env'] = latest_30d['users_30d_avg']
        latest_30d['cost_per_request'] = (latest_30d['credits_30d_total'] * credit_cost) / latest_30d['operations_30d_total']
    else:
        # Fallback if 30-day calculation fails
        latest_30d = df.groupby('SERVICE_TYPE').agg({
            'TOTAL_OPERATIONS': 'sum',
            'DAILY_UNIQUE_USERS': 'mean',
            'TOTAL_CREDITS': 'sum'
        }).reset_index()
        num_days = len(df['DATE'].unique())
        latest_30d['requests_per_day'] = latest_30d['TOTAL_OPERATIONS'] / num_days if num_days > 0 else 0
        latest_30d['users_in_env'] = latest_30d['DAILY_UNIQUE_USERS']
        latest_30d['cost_per_request'] = (latest_30d['TOTAL_CREDITS'] * credit_cost) / latest_30d['TOTAL_OPERATIONS']
    
    # ========================================================================
    # Historical Usage Reference Table - MOVED TO TOP AS GUIDE
    # ========================================================================
    st.markdown("#### 📊 Historical Usage Reference (from your data)")
    st.caption("Use these metrics as a guide for your cost estimates below")
    
    reference_table = []
    for _, service in latest_30d.iterrows():
        reference_table.append({
            'Service': service['SERVICE_TYPE'],
            'Users in Environment': f"{service['users_in_env']:.0f}",
            'Requests per Day': f"{service['requests_per_day']:,.0f}",
            'Cost per Request': f"${service['cost_per_request']:.6f}"
        })
    
    reference_df = pd.DataFrame(reference_table)
    st.dataframe(reference_df, use_container_width=True, hide_index=True)
    
    st.divider()
    
    # ========================================================================
    # User Persona Configuration
    # ========================================================================
    st.markdown("#### 👤 Define User Personas and Estimate Costs")
    
    # Initialize session state for user personas if not exists
    if 'user_personas_simple' not in st.session_state:
        st.session_state.user_personas_simple = [
            {'name': 'Power User', 'count': 10, 'requests_per_day': 50},
            {'name': 'Regular User', 'count': 30, 'requests_per_day': 20}
        ]
    
    # User persona inputs
    personas_to_remove = []
    for idx, persona in enumerate(st.session_state.user_personas_simple):
        col1, col2, col3, col4 = st.columns([2, 1, 1, 0.5])
        
        with col1:
            persona['name'] = st.text_input(
                "Persona Name",
                value=persona['name'],
                key=f"simple_persona_name_{idx}",
                placeholder="e.g., Power User, Analyst, Executive"
            )
        
        with col2:
            persona['count'] = st.number_input(
                "Number of Users",
                min_value=1,
                value=persona['count'],
                step=1,
                key=f"simple_count_{idx}"
            )
        
        with col3:
            persona['requests_per_day'] = st.number_input(
                "Requests per Day",
                min_value=1,
                value=persona['requests_per_day'],
                step=5,
                key=f"simple_req_{idx}",
                help="Average requests per user per day"
            )
        
        with col4:
            if len(st.session_state.user_personas_simple) > 1:
                if st.button("🗑️", key=f"simple_remove_{idx}", help="Remove"):
                    personas_to_remove.append(idx)
    
    # Remove personas marked for deletion
    for idx in sorted(personas_to_remove, reverse=True):
        st.session_state.user_personas_simple.pop(idx)
        st.rerun()
    
    # Add new persona button
    if st.button("➕ Add Another Persona"):
        st.session_state.user_personas_simple.append({
            'name': f'User Type {len(st.session_state.user_personas_simple) + 1}',
            'count': 10,
            'requests_per_day': 20
        })
        st.rerun()
    
    st.divider()
    
    # ========================================================================
    # Calculate Costs per Persona
    # ========================================================================
    st.markdown("#### 💵 Cost Estimates by Persona")
    
    # Calculate weighted average cost per request across all services
    total_ops = latest_30d['requests_per_day'].sum() * 30  # Monthly operations
    total_cost_30d = sum(
        (row['requests_per_day'] * 30 * row['cost_per_request']) 
        for _, row in latest_30d.iterrows()
    )
    avg_cost_per_request = total_cost_30d / total_ops if total_ops > 0 else 0
    
    # Calculate costs for each persona
    persona_results = []
    for persona in st.session_state.user_personas_simple:
        monthly_requests = persona['requests_per_day'] * 30
        cost_per_user_monthly = monthly_requests * avg_cost_per_request
        total_cost_monthly = cost_per_user_monthly * persona['count']
        
        persona_results.append({
            'Persona': persona['name'],
            'Users': persona['count'],
            'Requests/Day': persona['requests_per_day'],
            'Requests/Month': f"{monthly_requests:,}",
            'Cost/Request': f"${avg_cost_per_request:.6f}",
            'Cost/User/Month': f"${cost_per_user_monthly:,.2f}",
            'Total Monthly Cost': f"${total_cost_monthly:,.2f}"
        })
    
    results_df = pd.DataFrame(persona_results)
    st.dataframe(results_df, use_container_width=True, hide_index=True)
    
    # Summary metrics
    total_users = sum(p['count'] for p in st.session_state.user_personas_simple)
    total_monthly_cost = sum(
        p['requests_per_day'] * 30 * avg_cost_per_request * p['count'] 
        for p in st.session_state.user_personas_simple
    )
    total_monthly_requests = sum(
        p['requests_per_day'] * 30 * p['count'] 
        for p in st.session_state.user_personas_simple
    )
    avg_cost_per_user = total_monthly_cost / total_users if total_users > 0 else 0
    
    st.divider()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Users", f"{total_users:,}")
    with col2:
        st.metric("Total Monthly Requests", f"{total_monthly_requests:,.0f}")
    with col3:
        st.metric("Avg Cost per User", f"${avg_cost_per_user:,.2f}")
    with col4:
        st.metric("Total Monthly Cost", f"${total_monthly_cost:,.2f}")

def show_summary_report(df, credit_cost, variance_pct):
    """Display summary report tab"""
    st.header("Executive Summary Report")
    
    # Historical summary
    st.markdown("## 📊 Current State")
    
    total_credits = df['TOTAL_CREDITS'].sum()
    total_cost = total_credits * credit_cost
    days_of_data = len(df['DATE'].unique())
    avg_daily_cost = total_cost / days_of_data if days_of_data > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Analysis Period", f"{days_of_data} days")
        st.metric("Total Historical Cost", format_currency(total_cost))
    
    with col2:
        st.metric("Avg Daily Cost", format_currency(avg_daily_cost))
        st.metric("Total Credits Used", format_number(total_credits))
    
    with col3:
        service_count = df['SERVICE_TYPE'].nunique()
        st.metric("Active Services", service_count)
        avg_users = df['DAILY_UNIQUE_USERS'].mean()
        st.metric("Avg Daily Users", format_number(avg_users))
    
    st.divider()
    
    # Projection
    st.markdown("## 🔮 12-Month Projection (25% Growth)")
    
    projection_df = calculate_growth_projection(df, 0.25, 12, credit_cost)
    monthly_totals = projection_df.groupby('month')['projected_cost_usd'].sum()
    total_year_cost = monthly_totals.sum()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Projected Annual Cost", format_currency(total_year_cost))
    
    with col2:
        lower = total_year_cost * (1 - variance_pct)
        upper = total_year_cost * (1 + variance_pct)
        st.metric(f"Range (±{variance_pct*100:.0f}%)", f"{format_currency(lower)} - {format_currency(upper)}")
    
    with col3:
        avg_monthly = total_year_cost / 12
        st.metric("Avg Monthly Cost", format_currency(avg_monthly))
    
    st.divider()
    
    # Service breakdown
    st.markdown("## 💼 Service Breakdown")
    
    service_agg = df.groupby('SERVICE_TYPE').agg({
        'TOTAL_CREDITS': 'sum',
        'DAILY_UNIQUE_USERS': 'mean',
        'TOTAL_OPERATIONS': 'sum'
    }).reset_index()
    service_agg['TOTAL_COST_USD'] = service_agg['TOTAL_CREDITS'] * credit_cost
    service_agg['PCT_OF_TOTAL'] = service_agg['TOTAL_CREDITS'] / service_agg['TOTAL_CREDITS'].sum() * 100
    service_agg = service_agg.sort_values('TOTAL_CREDITS', ascending=False)
    
    st.dataframe(
        service_agg.style.format({
            'TOTAL_CREDITS': '{:,.0f}',
            'TOTAL_COST_USD': '${:,.2f}',
            'PCT_OF_TOTAL': '{:.1f}%',
            'DAILY_UNIQUE_USERS': '{:.0f}',
            'TOTAL_OPERATIONS': '{:,.0f}'
        }),
        use_container_width=True
    )
    
    # Export options
    st.divider()
    st.markdown("## 📥 Export Data")
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download Historical Data (CSV)",
        data=csv,
        file_name=f"cortex_usage_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

if __name__ == "__main__":
    main()
