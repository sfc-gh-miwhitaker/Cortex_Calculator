"""
Cortex AI Cost Calculator - Streamlit in Snowflake
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
    page_title="Cortex AI Cost Calculator",
    page_icon="📊",
    layout="wide"
)

# ============================================================================
# Utility Functions
# ============================================================================

def fetch_data_from_views(lookback_days=30):
    """Fetch data directly from Snowflake views"""
    query = f"""
    SELECT 
        usage_date AS date,
        service_type,
        daily_unique_users,
        total_operations,
        total_credits,
        credits_per_user,
        credits_per_operation
    FROM SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE.V_CORTEX_DAILY_SUMMARY
    WHERE usage_date >= DATEADD('day', -{lookback_days}, CURRENT_DATE())
    ORDER BY usage_date DESC
    """
    return session.sql(query).to_pandas()

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
    st.title("📊 Cortex AI Cost Calculator")
    st.markdown("""
    Estimate and project costs for Snowflake Cortex AI services based on actual usage data.
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
            st.info("Make sure monitoring views are deployed in SNOWFLAKE_EXAMPLE.CORTEX_AI_USAGE")
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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Historical Analysis",
        "🔮 Cost Projections",
        "📊 Scenario Comparison",
        "📋 Summary Report"
    ])
    
    with tab1:
        show_historical_analysis(df, credit_cost)
    
    with tab2:
        show_cost_projections(df, credit_cost, variance_pct)
    
    with tab3:
        show_scenario_comparison(df, credit_cost)
    
    with tab4:
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

def show_scenario_comparison(df, credit_cost):
    """Display scenario comparison tab"""
    st.header("Scenario Comparison")
    
    projection_months = st.slider(
        "Projection Period (months)",
        min_value=3,
        max_value=24,
        value=12,
        key="scenario_months"
    )
    
    # Define scenarios
    scenarios = {
        'Conservative (10%)': 0.10,
        'Moderate (25%)': 0.25,
        'Aggressive (50%)': 0.50,
        'Rapid (100%)': 1.00
    }
    
    # Calculate all scenarios
    fig = go.Figure()
    
    comparison_data = []
    
    for scenario_name, growth_rate in scenarios.items():
        projection_df = calculate_growth_projection(df, growth_rate, projection_months, credit_cost)
        monthly_totals = projection_df.groupby('month')['projected_cost_usd'].sum().reset_index()
        
        fig.add_trace(go.Scatter(
            x=monthly_totals['month'],
            y=monthly_totals['projected_cost_usd'],
            mode='lines+markers',
            name=scenario_name,
            line=dict(width=2)
        ))
        
        # Get month 12 cost
        month_12_cost = monthly_totals[monthly_totals['month'] == projection_months]['projected_cost_usd'].iloc[-1] if len(monthly_totals) > 0 else 0
        total_cost = monthly_totals['projected_cost_usd'].sum()
        
        comparison_data.append({
            'Scenario': scenario_name,
            f'Month {projection_months} Cost': format_currency(month_12_cost),
            'Total Year Cost': format_currency(total_cost)
        })
    
    fig.update_layout(
        title='Cost Projections: Scenario Comparison',
        xaxis_title='Month',
        yaxis_title='Projected Cost (USD)',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Scenario Summary")
    st.table(pd.DataFrame(comparison_data))

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
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Historical Data")
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download Historical Data (CSV)",
            data=csv,
            file_name=f"cortex_usage_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.markdown("### Credit Summary for Sales")
        credit_summary = create_credit_summary(df, credit_cost)
        summary_csv = credit_summary.to_csv(index=False)
        st.download_button(
            label="Download Credit Estimate (CSV)",
            data=summary_csv,
            file_name=f"credit_estimate_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            help="Pre-formatted summary for sales/pricing team"
        )
    
    st.markdown("### Preview: Credit Estimate Summary")
    st.dataframe(
        credit_summary.style.format({
            'Total Credits': '{:,.0f}',
            'Avg Credits/Day': '{:,.1f}',
            'Est. Credits/Month': '{:,.0f}',
            'Est. Cost/Month': '${:,.2f}'
        }),
        use_container_width=True
    )

if __name__ == "__main__":
    main()

