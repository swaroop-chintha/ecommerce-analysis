import streamlit as st
import duckdb
import pandas as pd
import os
import glob
import plotly.express as px

st.set_page_config(page_title="E-commerce Analytics", layout="wide")

st.sidebar.header("Configuration")
env_demo = os.getenv("DEMO_MODE", "false").lower() == "true"
demo_mode = st.sidebar.checkbox("🚀 Enable Demo Mode (Offline)", value=env_demo, help="Bypass Kafka/DuckDB and read precomputed data from Parquet files")

db_path = os.getenv('DB_PATH', 'data/ecommerce.db')
dl_path = os.getenv('DEAD_LETTER_PATH', 'data/dead_letter')
demo_path = os.getenv('DEMO_DATA_PATH', 'data/demo')

@st.cache_data(ttl=300)
def load_data(query_or_file, is_demo=False):
    if is_demo:
        if not os.path.exists(query_or_file):
            st.error(f"Demo file missing: {query_or_file}. Run export_demo_data.py first!")
            return pd.DataFrame()
        return pd.read_parquet(query_or_file)
    else:
        conn = duckdb.connect(db_path, read_only=True)
        df = conn.execute(query_or_file).df()
        conn.close()
        return df

st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Business Insights", "Executive Summary", "Product Analytics", "User Funnel", "Data Observability"])

if page == "Business Insights":
    st.title("Business Insights")
    st.markdown("""
    This section distills our key findings into actionable insights for stakeholders, leveraging our gold mart layer.
    
    ### 📈 Key Takeaways:
    - **Customer Retention**: The platform identifies strong engagement with repeat users contributing significantly to the Lifetime Value (LTV).
    - **Sales Engine**: Revenue is driven predominantly by top-category products, suggesting a highly targeted demographic. 
    - **Funnel Bottleneck**: High page views generate organic interest, but optimizing the 'checkout_start' drop-off is critical for boosting overall conversion.
    """)
    
    st.markdown("---")
    st.subheader("New vs. Repeat Customers")
    try:
        source = os.path.join(demo_path, 'mart_user_insights.parquet') if demo_mode else "SELECT * FROM mart_user_insights"
        users_df = load_data(source, demo_mode)
        
        if not users_df.empty:
            agg_df = users_df.groupby('user_segment')['lifetime_value'].sum().reset_index()
            fig = px.pie(agg_df, values='lifetime_value', names='user_segment', title="Lifetime Value: New vs Repeat Users", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
            
            # Show top 5 users
            st.subheader("Top 5 Customers by Lifetime Value")
            top_users = users_df.sort_values(by='lifetime_value', ascending=False).head(5)
            st.dataframe(top_users[['name', 'total_orders', 'lifetime_value', 'user_segment']], use_container_width=True)
    except Exception as e:
        st.error(f"Unable to load User Insights: {e}")

elif page == "Executive Summary":
    st.title("Executive Summary")
    
    st.markdown("### Overall Business KPIs")
    try:
        source = os.path.join(demo_path, 'mart_sales_dashboard.parquet') if demo_mode else "SELECT * FROM mart_sales_dashboard"
        df = load_data(source, demo_mode)
        
        if not df.empty:
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Revenue", f"₹{df['total_revenue'].sum():,.2f}")
            col2.metric("Total Orders", f"{df['total_orders'].sum():,}")
            col3.metric("Avg Order Value", f"₹{df['average_order_value'].mean():,.2f}")
            
            st.markdown("---")
            st.subheader("Daily Sales Trends")
            df = df.sort_values('date_day')
            fig1 = px.line(df, x='date_day', y='total_revenue', title='Daily Revenue')
            st.plotly_chart(fig1, use_container_width=True)
    except Exception as e:
        st.error(f"KPIs currently unavailable: {e}")

elif page == "Product Analytics":
    st.title("Product Analytics")
    try:
        source = os.path.join(demo_path, 'mart_product_analytics.parquet') if demo_mode else """
            SELECT p.product_name, p.category, sum(f.total_amount) as revenue
            FROM fact_orders f
            JOIN dim_products p ON f.product_id = p.product_id
            GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10
        """
        df = load_data(source, demo_mode)
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Top 10 Products by Revenue")
                # Enforce limit 10 aggressively for demo mode
                df_top = df.head(10)
                fig = px.bar(df_top, x='revenue', y='product_name', color='category', orientation='h')
                fig.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("Revenue by Category")
                cat_df = df.groupby('category')['revenue'].sum().reset_index()
                fig2 = px.pie(cat_df, values='revenue', names='category', hole=0.5)
                st.plotly_chart(fig2, use_container_width=True)
    except Exception as e:
        st.error(e)

elif page == "User Funnel":
    st.title("User Funnel Analytics")
    try:
        source = os.path.join(demo_path, 'mart_conversion_funnel.parquet') if demo_mode else "SELECT * FROM mart_conversion_funnel"
        df = load_data(source, demo_mode)
        
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Conversion Funnel")
                order = ['page_view', 'product_click', 'add_to_cart', 'checkout_start', 'purchase_complete']
                df['event_type'] = pd.Categorical(df['event_type'], categories=order, ordered=True)
                df = df.sort_values('event_type')
                
                fig = px.funnel(df, x='total_events', y='event_type', color='page')
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                st.subheader("Overall Conversion Rate")
                rate = df['overall_conversion_rate'].max()
                if pd.notnull(rate):
                    st.metric("Purchase / View Rate", f"{rate:.2f}%")
                else:
                    st.write("Not enough data to map complete conversion.")
    except Exception as e:
        st.error(f"Funnel unavailable: {e}")

elif page == "Data Observability":
    st.title("Data Observability & Dead Letter Queue")
    
    if demo_mode:
        st.info("Demonstrating offline capability. DLQ observation requires connecting directly to live log files or the warehouse.")
    else:
        st.subheader("Streaming Ingestion DLQ (Rejected Records)")
        dl_files = glob.glob(f"{dl_path}/*.jsonl")
        if dl_files:
            for f in dl_files:
                st.markdown(f"**{os.path.basename(f)}**")
                try:
                    dl_df = pd.read_json(f, lines=True).tail(20)
                    st.dataframe(dl_df, use_container_width=True)
                except Exception:
                    st.warning("Could not read records")
        else:
            st.success("No rejected streaming records found in the DLQ.")
