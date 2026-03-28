import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# Page Configuration
st.set_page_config(
    page_title="E-commerce Analytics :: Demo Mode",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stDataFrame {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# sidebar header
st.sidebar.title("🛠️ Project Control")
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

if DEMO_MODE:
    st.sidebar.success("✅ Demo Mode Enabled")
    st.sidebar.info("Reading from cached Parquet files (data/demo/)")
else:
    st.sidebar.warning("⚠️ Demo Mode Disabled")

# Cached Data Loading Operations
@st.cache_data
def load_demo_data(file_path):
    if os.path.exists(file_path):
        return pd.read_parquet(file_path)
    else:
        st.error(f"Data file not found: {file_path}")
        return pd.DataFrame()

# Load all datasets
df_sales = load_demo_data('data/demo/mart_sales_dashboard.parquet')
df_products = load_demo_data('data/demo/mart_product_analytics.parquet')
df_funnel = load_demo_data('data/demo/mart_conversion_funnel.parquet')
df_users = load_demo_data('data/demo/mart_user_insights.parquet')

# Navigation
st.sidebar.subheader("Navigation")
page = st.sidebar.radio(
    "Go to",
    ["Executive Summary", "Product Analytics", "User Funnel", "User Insights"]
)

if page == "Executive Summary":
    st.title("📊 Executive Summary")
    
    # KPIs
    if not df_sales.empty:
        col1, col2, col3, col4 = st.columns(4)
        total_rev = df_sales['total_revenue'].sum()
        total_orders = df_sales['total_orders'].sum()
        avg_order_val = total_rev / total_orders if total_orders > 0 else 0
        total_customers = df_users['user_id'].nunique() if not df_users.empty else 0
        
        col1.metric("Total Revenue", f"₹{total_rev:,.2f}")
        col2.metric("Total Orders", f"{total_orders:,}")
        col3.metric("Avg Order Value", f"₹{avg_order_val:,.2f}")
        col4.metric("Total Customers", f"{total_customers:,}")
        
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Revenue Trend")
        if not df_sales.empty:
            fig_rev = px.line(df_sales, x='date_day', y='total_revenue', 
                             title='Daily Revenue', line_shape='spline')
            fig_rev.update_layout(hovermode="x unified")
            st.plotly_chart(fig_rev, use_container_width=True)
            
    with col2:
        st.subheader("Daily Orders")
        if not df_sales.empty:
            fig_orders = px.bar(df_sales, x='date_day', y='total_orders', 
                               title='Daily Orders', color_discrete_sequence=['#ff7f0e'])
            st.plotly_chart(fig_orders, use_container_width=True)

elif page == "Product Analytics":
    st.title("📦 Product Analytics")
    
    if not df_products.empty:
        # Top Products by Purchases
        st.subheader("Top 10 Products by Sales")
        top_10 = df_products.sort_values('purchases', ascending=False).head(10)
        fig_top = px.bar(top_10, x='purchases', y='name', orientation='h', 
                        title='Top Products', color='purchases',
                        color_continuous_scale='Viridis')
        fig_top.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_top, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Revenue by Category")
            # Assuming revenue = purchases * some price (not simple here, but let's use purchases for now or if we had price)
            # Since we don't have price, let's show Purchases by Category
            cat_perf = df_products.groupby('category')[['views', 'adds_to_cart', 'purchases']].sum().reset_index()
            fig_cat = px.pie(cat_perf, values='purchases', names='category', title='Purchases by Category', hole=0.4)
            st.plotly_chart(fig_cat, use_container_width=True)
            
        with col2:
            st.subheader("Add to Cart Rate by Category")
            import numpy as np
            cat_perf['cart_rate'] = np.where(cat_perf['views'] > 0, (cat_perf['adds_to_cart'] / cat_perf['views'] * 100), 0)
            fig_rate = px.bar(cat_perf, x='category', y='cart_rate', title='Add to Cart Rate (%)')
            st.plotly_chart(fig_rate, use_container_width=True)

elif page == "User Funnel":
    st.title("🌪️ Conversion Funnel")
    
    if not df_funnel.empty:
        st.subheader("Active Session Funnel")
        # Assuming df_funnel has funnel_step and unique_sessions
        fig_funnel = go.Figure(go.Funnel(
            x = df_funnel['funnel_step'],
            y = df_funnel['unique_sessions'],
            textinfo = "value+percent initial"
        ))
        fig_funnel.update_layout(title="Customer Journey Consolidation")
        st.plotly_chart(fig_funnel, use_container_width=True)
        
        st.markdown("---")
        st.subheader("Detailed Funnel Metrics")
        st.dataframe(df_funnel, use_container_width=True)

elif page == "User Insights":
    st.title("👤 User Insights")
    
    if not df_users.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Top Users by Lifetime Value")
            top_users = df_users.sort_values('lifetime_value', ascending=False).head(10)
            fig_ltv = px.bar(top_users, x='lifetime_value', y='user_id', orientation='h',
                            title='Top 10 Users (LTV)')
            st.plotly_chart(fig_ltv, use_container_width=True)
            
        st.subheader("Orders Distribution by State")
        if not df_users.empty:
            state_dist = df_users.groupby('state')['total_orders'].sum().reset_index()
            fig_state = px.bar(state_dist, x='state', y='total_orders', 
                              title="Orders by State (India)", color='total_orders')
            st.plotly_chart(fig_state, use_container_width=True)
        else:
            st.info("No user state data available.")
            
        st.subheader("User Demographic Table")
        st.dataframe(df_users.sort_values('lifetime_value', ascending=False), use_container_width=True)

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("Data Engineering Project v1.0")
st.sidebar.caption("Built with Streamlit & DuckDB (Demo Mode)")
