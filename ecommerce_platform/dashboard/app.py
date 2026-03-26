import streamlit as st
import duckdb
import pandas as pd
import os
import glob
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

duckdb_path = os.getenv('WAREHOUSE_PATH', 'data/warehouse.duckdb')
dl_path = os.getenv('DEAD_LETTER_PATH', 'data/dead_letter')

@st.cache_data(ttl=300)
def load_data(query):
    conn = duckdb.connect(duckdb_path, read_only=True)
    df = conn.execute(query).df()
    conn.close()
    return df

st.sidebar.header("Filters")
# Default to last 365 days due to synthetic date ranges
default_start = datetime.today() - timedelta(days=365)
default_end = datetime.today()
start_date = st.sidebar.date_input("Start date", default_start)
end_date = st.sidebar.date_input("End date", default_end)

page = st.sidebar.radio("Navigation", ["Executive Summary", "Product Analytics", "User Funnel", "Data Quality"])

if page == "Executive Summary":
    st.title("Executive Summary")
    
    # KPIs
    kpi_query = f"""
    SELECT 
        sum(item_revenue) as total_revenue,
        count(distinct order_id) as total_orders,
        count(distinct user_key) as total_users,
        sum(item_revenue) / count(distinct order_id) as aov
    FROM main.fact_orders
    WHERE order_date >= '{start_date}' AND order_date <= '{end_date}'
    """
    try:
        kpi_df = load_data(kpi_query)
        if not kpi_df.empty:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Revenue", f"₹{kpi_df['total_revenue'].iloc[0]:,.2f}")
            col2.metric("Total Orders", f"{kpi_df['total_orders'].iloc[0]:,}")
            col3.metric("Total Users", f"{kpi_df['total_users'].iloc[0]:,}")
            col4.metric("Avg Order Value", f"₹{kpi_df['aov'].iloc[0]:,.2f}")
    except Exception as e:
        st.error(f"Could not load KPIs: {e}")
        
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Daily Revenue (Last 30 Days)")
        last_30 = datetime.today() - timedelta(days=30)
        daily_rev_query = f"""
        SELECT order_date, sum(item_revenue) as daily_revenue
        FROM main.fact_orders
        WHERE order_date >= '{last_30.strftime('%Y-%m-%d')}'
        GROUP BY 1 ORDER BY 1
        """
        try:
            daily_rev_df = load_data(daily_rev_query)
            fig1 = px.line(daily_rev_df, x='order_date', y='daily_revenue')
            st.plotly_chart(fig1, use_container_width=True)
        except Exception as e:
            st.error(e)
            
    with col2:
        st.subheader("Orders by Status")
        status_query = f"""
        SELECT status, count(distinct order_id) as num_orders
        FROM main.fact_orders
        WHERE order_date >= '{start_date}' AND order_date <= '{end_date}'
        GROUP BY 1
        """
        try:
            status_df = load_data(status_query)
            fig2 = px.pie(status_df, values='num_orders', names='status', hole=0.5)
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(e)

elif page == "Product Analytics":
    st.title("Product Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 10 Products by Revenue")
        top_prod_query = f"""
        SELECT p.name, sum(f.item_revenue) as revenue
        FROM main.fact_orders f
        JOIN main.dim_products p ON f.product_key = p.product_key
        WHERE f.order_date >= '{start_date}' AND f.order_date <= '{end_date}'
        GROUP BY 1 ORDER BY 2 DESC LIMIT 10
        """
        try:
            top_prod_df = load_data(top_prod_query)
            fig = px.bar(top_prod_df, x='revenue', y='name', orientation='h')
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(e)
            
    with col2:
        st.subheader("Revenue by Category")
        cat_query = f"""
        SELECT p.category, sum(f.item_revenue) as revenue
        FROM main.fact_orders f
        JOIN main.dim_products p ON f.product_key = p.product_key
        WHERE f.order_date >= '{start_date}' AND f.order_date <= '{end_date}'
        GROUP BY 1 ORDER BY 2 DESC
        """
        try:
            cat_df = load_data(cat_query)
            fig2 = px.bar(cat_df, x='category', y='revenue')
            st.plotly_chart(fig2, use_container_width=True)
        except Exception as e:
            st.error(e)
            
    st.markdown("---")
    st.subheader("Low Stock Alerts (< 20 units)")
    stock_query = "SELECT product_id, name, category, stock FROM main.dim_products WHERE stock < 20 ORDER BY stock ASC"
    try:
        stock_df = load_data(stock_query)
        st.dataframe(stock_df, use_container_width=True)
    except Exception as e:
        st.error(e)

elif page == "User Funnel":
    st.title("User Funnel Analytics")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Conversion Funnel")
        funnel_query = """
        SELECT event_type, count(distinct session_id) as sessions
        FROM main.fact_events
        WHERE event_type IN ('page_view', 'product_click', 'add_to_cart', 'purchase_complete')
        GROUP BY 1
        """
        try:
            funnel_df = load_data(funnel_query)
            # Reorder
            order = ['page_view', 'product_click', 'add_to_cart', 'purchase_complete']
            funnel_df['event_type'] = pd.Categorical(funnel_df['event_type'], categories=order, ordered=True)
            funnel_df = funnel_df.sort_values('event_type')
            fig = px.funnel(funnel_df, x='sessions', y='event_type')
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("Events data not fully available or generated correctly.")

    with col2:
        st.subheader("Top 5 Pages by Views")
        page_query = """
        SELECT page, count(*) as views
        FROM main.fact_events
        WHERE event_type = 'page_view'
        GROUP BY 1 ORDER BY 2 DESC LIMIT 5
        """
        try:
            page_df = load_data(page_query)
            st.dataframe(page_df, use_container_width=True)
        except Exception as e:
            st.error(e)

    st.markdown("---")
    st.subheader("Events Over Last 7 Days")
    last_7 = datetime.today() - timedelta(days=7)
    ev_time_query = f"""
    SELECT cast(ts as date) as ev_date, event_type, count(*) as count
    FROM main.fact_events
    WHERE cast(ts as date) >= '{last_7.strftime('%Y-%m-%d')}'
    GROUP BY 1, 2 ORDER BY 1
    """
    try:
        ev_time_df = load_data(ev_time_query)
        fig2 = px.area(ev_time_df, x='ev_date', y='count', color='event_type')
        st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(e)

elif page == "Data Quality":
    st.title("Data Quality & Dead Letter Queue")
    
    st.subheader("Last Run Validation Results")
    st.info("Data Quality tests are run via Great Expectations script scheduled in Airflow. This section would typically display a summarized dashboard from DataDocs, but currently shows custom output from the last DQ run if logged. Since we log stdout to Airflow, verify DQ success via Airflow tasks.")
    
    st.subheader("Dead Letter Queue (Rejected Records)")
    st.write("Records rejected during ingestion schema validation:")
    
    # Read dead letter files
    dl_files = glob.glob(f"{dl_path}/*.parquet") + glob.glob(f"{dl_path}/**/*.jsonl", recursive=True)
    
    if dl_files:
        st.write(f"Found {len(dl_files)} dead letter files.")
        for f in dl_files:
            file_name = os.path.basename(f)
            st.write(f"**{file_name}**")
            if f.endswith('.parquet'):
                dl_df = pd.read_parquet(f).head(10)
                st.dataframe(dl_df, use_container_width=True)
            elif f.endswith('.jsonl'):
                dl_df = pd.read_json(f, lines=True).head(10)
                st.dataframe(dl_df, use_container_width=True)
    else:
        st.success("No rejected records found in DLQ.")
