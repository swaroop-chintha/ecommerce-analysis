import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import os

# ─── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="E-Commerce Analytics Dashboard",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Design System — Dark Mode Glassmorphism ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { font-family: 'Inter', sans-serif !important; }

.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1400px;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0f23 0%, #1a1a3e 100%);
}
[data-testid="stSidebar"] * { color: #e0e0e0 !important; }
[data-testid="stSidebar"] .stRadio label {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 14px !important;
    margin-bottom: 4px;
    transition: all 0.2s ease;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(102,126,234,0.15);
    border-color: rgba(102,126,234,0.4);
}

.kpi-card {
    background: linear-gradient(135deg, #1e1e3f 0%, #2a2a5c 100%);
    border: 1px solid rgba(102,126,234,0.2);
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0,0,0,0.3);
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    position: relative;
    overflow: hidden;
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 16px 16px 0 0;
}
.kpi-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(102,126,234,0.2);
}
.kpi-card.revenue::before { background: linear-gradient(90deg, #667eea, #764ba2); }
.kpi-card.orders::before { background: linear-gradient(90deg, #f093fb, #f5576c); }
.kpi-card.aov::before { background: linear-gradient(90deg, #4facfe, #00f2fe); }
.kpi-card.customers::before { background: linear-gradient(90deg, #43e97b, #38f9d7); }
.kpi-card.conversion::before { background: linear-gradient(90deg, #fa709a, #fee140); }

.kpi-icon { font-size: 2rem; margin-bottom: 4px; }
.kpi-label {
    font-size: 0.75rem; font-weight: 500; color: #8b8bb5;
    text-transform: uppercase; letter-spacing: 1.2px; margin-bottom: 6px;
}
.kpi-value { font-size: 1.65rem; font-weight: 700; color: #ffffff; line-height: 1.2; }
.kpi-delta {
    font-size: 0.8rem; font-weight: 600; margin-top: 6px;
    padding: 2px 10px; border-radius: 20px; display: inline-block;
}
.kpi-delta.positive { color: #43e97b; background: rgba(67,233,123,0.1); }
.kpi-delta.negative { color: #f5576c; background: rgba(245,87,108,0.1); }

.section-header {
    background: linear-gradient(135deg, #1e1e3f 0%, #2a2a5c 100%);
    border: 1px solid rgba(102,126,234,0.15);
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 20px;
}
.section-title { font-size: 1.5rem; font-weight: 700; color: #ffffff; margin: 0; }
.section-subtitle { font-size: 0.85rem; color: #8b8bb5; margin-top: 4px; }

.chart-card {
    background: linear-gradient(135deg, #1e1e3f 0%, #252550 100%);
    border: 1px solid rgba(102,126,234,0.12);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.chart-card-title {
    font-size: 0.95rem; font-weight: 600; color: #c4c4e0;
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 1px solid rgba(102,126,234,0.1);
}

.stApp { background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 50%, #0f0f23 100%); }
[data-testid="stMetric"] { background: transparent; }

.demo-banner {
    background: linear-gradient(90deg, rgba(102,126,234,0.15), rgba(118,75,162,0.15));
    border: 1px solid rgba(102,126,234,0.3);
    border-radius: 10px;
    padding: 10px 16px; text-align: center; margin-bottom: 16px;
}
.demo-banner span { color: #a5b4fc; font-size: 0.8rem; font-weight: 500; }

h1, h2, h3 { color: #ffffff !important; }
p, li { color: #c4c4e0; }
.stMarkdown hr { border-color: rgba(102,126,234,0.15); }

.stTabs [data-baseweb="tab-list"] {
    gap: 4px; background: rgba(255,255,255,0.03); border-radius: 10px; padding: 4px;
}
.stTabs [data-baseweb="tab"] { border-radius: 8px; color: #8b8bb5; font-weight: 500; }
.stTabs [aria-selected="true"] { background: rgba(102,126,234,0.2) !important; color: #a5b4fc !important; }
</style>
""", unsafe_allow_html=True)

# ─── Plotly Theme Helper ─────────────────────────────────────────────────────
_BASE_LAYOUT = dict(
    font=dict(family="Inter, sans-serif", color="#c4c4e0"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(l=40, r=20, t=50, b=40),
    hoverlabel=dict(bgcolor="#1e1e3f", font_size=13, font_family="Inter"),
)
_GRID = dict(gridcolor="rgba(102,126,234,0.08)", zerolinecolor="rgba(102,126,234,0.1)")

GRADIENT_COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe',
                    '#00f2fe', '#43e97b', '#38f9d7', '#fa709a', '#fee140']

def styled(fig, **kw):
    """Apply dark theme + per-chart overrides. Won't duplicate axis/legend keys."""
    merged = {**_BASE_LAYOUT, **kw}
    merged.setdefault('xaxis', _GRID.copy())
    merged.setdefault('yaxis', _GRID.copy())
    fig.update_layout(**merged)
    return fig

# ─── Data Loading ────────────────────────────────────────────────────────────
DEMO_MODE = os.getenv('DEMO_MODE', 'false').lower() == 'true'

@st.cache_data
def load_data(fp):
    if os.path.exists(fp):
        return pd.read_parquet(fp)
    st.error(f"⚠️ Data file not found: {fp}")
    return pd.DataFrame()

df_sales = load_data('data/demo/mart_sales_dashboard.parquet')
df_products = load_data('data/demo/mart_product_analytics.parquet')
df_funnel = load_data('data/demo/mart_conversion_funnel.parquet')
df_users = load_data('data/demo/mart_user_insights.parquet')

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛍️ Analytics Hub")
    if DEMO_MODE:
        st.success("✅ Demo Mode Active")
        st.caption("📦 Reading from cached Parquet files")
    else:
        st.warning("⚠️ Demo Mode Disabled")

    st.markdown("---")
    page = st.radio("📍 Navigation",
                     ["Executive Summary", "Product Analytics", "User Funnel", "User Insights"],
                     label_visibility="collapsed")
    st.markdown("---")

    if page == "Product Analytics" and not df_products.empty:
        st.markdown("### 🎛️ Filters")
        all_cats = df_products['category'].unique().tolist()
        selected_cats = st.multiselect("Category", all_cats, default=all_cats, key="cf")
        sort_by = st.selectbox("Sort By", ['purchases', 'views', 'adds_to_cart', 'price'], key="sf")

    elif page == "User Insights" and not df_users.empty:
        st.markdown("### 🎛️ Filters")
        all_states = sorted(df_users['state'].unique().tolist())
        selected_states = st.multiselect("State", all_states, default=all_states, key="stf")
        min_orders = st.slider("Min Orders", 0, int(df_users['total_orders'].max()), 0, key="of")

    elif page == "Executive Summary" and not df_sales.empty:
        st.markdown("### 🎛️ Filters")
        mn = df_sales['date_day'].min().date()
        mx = df_sales['date_day'].max().date()
        date_range = st.date_input("Date Range", value=(mn, mx), min_value=mn, max_value=mx, key="df")

    st.markdown("---")
    st.caption("E-Commerce Analytics v2.0")
    st.caption("Built with Streamlit & Plotly")

# ─── Helpers ─────────────────────────────────────────────────────────────────
def sdiv(a, b, d=0):
    return a / b if b else d

def fmt_cur(v):
    if v >= 1e7: return f"₹{v/1e7:.2f} Cr"
    if v >= 1e5: return f"₹{v/1e5:.2f} L"
    if v >= 1e3: return f"₹{v/1e3:.1f}K"
    return f"₹{v:,.0f}"

def fmt_num(v):
    if v >= 1e7: return f"{v/1e7:.2f} Cr"
    if v >= 1e5: return f"{v/1e5:.2f} L"
    if v >= 1e3: return f"{v/1e3:.1f}K"
    return f"{v:,.0f}"

def kpi(icon, label, value, delta=None, pos=True, cls="revenue"):
    dh = ""
    if delta is not None:
        c = "positive" if pos else "negative"
        a = "↑" if pos else "↓"
        dh = f'<div class="kpi-delta {c}">{a} {delta}</div>'
    return f'''<div class="kpi-card {cls}">
        <div class="kpi-icon">{icon}</div>
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>{dh}</div>'''

def header(title, sub=""):
    s = f'<div class="section-subtitle">{sub}</div>' if sub else ""
    st.markdown(f'<div class="section-header"><div class="section-title">{title}</div>{s}</div>',
                unsafe_allow_html=True)

def card_start(title):
    st.markdown(f'<div class="chart-card"><div class="chart-card-title">{title}</div>', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
if page == "Executive Summary":
    header("📊 Executive Summary", "Real-time business performance overview")

    if not df_sales.empty:
        f = df_sales.copy()
        if 'df' in st.session_state:
            dr = st.session_state.df
            if isinstance(dr, tuple) and len(dr) == 2:
                f = f[(f['date_day'].dt.date >= dr[0]) & (f['date_day'].dt.date <= dr[1])]

        tot_rev = f['total_revenue'].sum()
        tot_ord = int(f['total_orders'].sum())
        aov = sdiv(tot_rev, tot_ord)
        tot_cust = df_users['user_id'].nunique() if not df_users.empty else 0

        mid = len(f) // 2
        if mid > 0:
            h1, h2 = f.iloc[:mid], f.iloc[mid:]
            rg = sdiv(h2['total_revenue'].sum() - h1['total_revenue'].sum(), h1['total_revenue'].sum()) * 100
            og = sdiv(h2['total_orders'].sum() - h1['total_orders'].sum(), h1['total_orders'].sum()) * 100
        else:
            rg = og = 0

        if not df_funnel.empty:
            fs = df_funnel.sort_values('unique_sessions', ascending=False)
            cr = sdiv(fs['unique_sessions'].iloc[-1], fs['unique_sessions'].iloc[0]) * 100
        else:
            cr = 0

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(kpi("💰", "Total Revenue", fmt_cur(tot_rev), f"{abs(rg):.1f}%", rg >= 0, "revenue"), unsafe_allow_html=True)
        c2.markdown(kpi("📦", "Total Orders", fmt_num(tot_ord), f"{abs(og):.1f}%", og >= 0, "orders"), unsafe_allow_html=True)
        c3.markdown(kpi("🎯", "Avg Order Value", fmt_cur(aov), cls="aov"), unsafe_allow_html=True)
        c4.markdown(kpi("🔄", "Conversion Rate", f"{cr:.1f}%", cls="conversion"), unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Revenue Trend + Monthly
        col1, col2 = st.columns([2, 1])
        with col1:
            card_start("📈 Revenue Trend")
            cd = f.copy().sort_values('date_day')
            cd['ma7'] = cd['total_revenue'].rolling(7, min_periods=1).mean()
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=cd['date_day'], y=cd['total_revenue'], mode='lines',
                                      name='Daily Revenue', line=dict(color='rgba(102,126,234,0.3)', width=1),
                                      fill='tozeroy', fillcolor='rgba(102,126,234,0.05)',
                                      hovertemplate='%{x|%d %b %Y}<br>Revenue: ₹%{y:,.0f}<extra></extra>'))
            fig.add_trace(go.Scatter(x=cd['date_day'], y=cd['ma7'], mode='lines',
                                      name='7-Day Avg', line=dict(color='#667eea', width=2.5),
                                      hovertemplate='%{x|%d %b %Y}<br>7d Avg: ₹%{y:,.0f}<extra></extra>'))
            styled(fig, height=380, hovermode="x unified",
                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                               bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5")))
            st.plotly_chart(fig, use_container_width=True)
            card_end()

        with col2:
            card_start("📊 Monthly Revenue")
            m = f.copy()
            m['month'] = m['date_day'].dt.to_period('M').astype(str)
            ma = m.groupby('month').agg(revenue=('total_revenue', 'sum'), orders=('total_orders', 'sum')).reset_index()
            fig_m = px.bar(ma, x='month', y='revenue', color='revenue',
                            color_continuous_scale=['#667eea', '#764ba2'])
            styled(fig_m, height=380, showlegend=False, coloraxis_showscale=False)
            fig_m.update_traces(hovertemplate='%{x}<br>Revenue: ₹%{y:,.0f}<extra></extra>')
            fig_m.update_xaxes(tickangle=45)
            st.plotly_chart(fig_m, use_container_width=True)
            card_end()

        # Category & Top Products
        col1, col2 = st.columns(2)
        with col1:
            card_start("🏷️ Revenue by Category")
            if not df_products.empty and 'price' in df_products.columns:
                cr_df = df_products.groupby('category').apply(
                    lambda x: (x['purchases'] * x['price']).sum()).reset_index(name='est_revenue')
                fig_c = px.pie(cr_df, values='est_revenue', names='category', hole=0.55,
                                color_discrete_sequence=GRADIENT_COLORS)
                styled(fig_c, height=340, legend=dict(orientation="v", yanchor="middle", y=0.5,
                                                       bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5")))
                fig_c.update_traces(textinfo='percent+label', textfont_size=11,
                                     hovertemplate='%{label}<br>Revenue: ₹%{value:,.0f}<br>Share: %{percent}<extra></extra>')
                st.plotly_chart(fig_c, use_container_width=True)
            card_end()

        with col2:
            card_start("🏆 Top 5 Products by Revenue")
            if not df_products.empty and 'price' in df_products.columns:
                df_products['est_revenue'] = df_products['purchases'] * df_products['price']
                t5 = df_products.nlargest(5, 'est_revenue')
                fig_t = px.bar(t5, y='name', x='est_revenue', orientation='h',
                                color='est_revenue', color_continuous_scale=['#4facfe', '#667eea'],
                                text=t5['est_revenue'].apply(fmt_cur))
                styled(fig_t, height=340, showlegend=False, coloraxis_showscale=False,
                       yaxis=dict(categoryorder='total ascending', gridcolor="rgba(0,0,0,0)"))
                fig_t.update_traces(textposition='outside', textfont_size=11,
                                     hovertemplate='%{y}<br>Revenue: ₹%{x:,.0f}<extra></extra>')
                st.plotly_chart(fig_t, use_container_width=True)
            card_end()
    else:
        st.warning("No sales data available.")


# ═══════════════════════════════════════════════════════════════════════════════
# PRODUCT ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "Product Analytics":
    header("📦 Product Analytics", "Deep-dive into product performance and category trends")

    if not df_products.empty:
        fp = df_products.copy()
        if 'cf' in st.session_state:
            fp = fp[fp['category'].isin(st.session_state.cf)]
        sc = st.session_state.get('sf', 'purchases')

        if fp.empty:
            st.info("No products match the selected filters.")
        else:
            card_start("🏆 Top 15 Products")
            t15 = fp.nlargest(15, sc)
            fig = px.bar(t15, y='name', x=sc, orientation='h', color='category',
                          color_discrete_sequence=GRADIENT_COLORS,
                          custom_data=['views', 'adds_to_cart', 'purchases', 'category'])
            styled(fig, height=520,
                   yaxis=dict(categoryorder='total ascending', gridcolor="rgba(0,0,0,0)"),
                   legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                               bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5")))
            fig.update_traces(hovertemplate='<b>%{y}</b><br>Category: %{customdata[3]}<br>'
                              'Views: %{customdata[0]:,}<br>Cart Adds: %{customdata[1]:,}<br>'
                              'Purchases: %{customdata[2]:,}<extra></extra>')
            st.plotly_chart(fig, use_container_width=True)
            card_end()

            col1, col2 = st.columns(2)
            with col1:
                card_start("📊 Category Performance Comparison")
                ca = fp.groupby('category').agg(views=('views','sum'), cart_adds=('adds_to_cart','sum'),
                                                 purchases=('purchases','sum')).reset_index()
                fig = go.Figure()
                for metric, clr in [('views','#667eea'),('cart_adds','#f093fb'),('purchases','#43e97b')]:
                    fig.add_trace(go.Bar(name=metric.replace('_',' ').title(), x=ca['category'], y=ca[metric],
                                          marker_color=clr,
                                          hovertemplate='%{x}<br>'+metric.title()+': %{y:,}<extra></extra>'))
                styled(fig, height=400, barmode='group',
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                   bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5")))
                st.plotly_chart(fig, use_container_width=True)
                card_end()

            with col2:
                card_start("🔄 Conversion Rates by Category")
                ca['v2c'] = ca.apply(lambda r: sdiv(r['cart_adds'], r['views']) * 100, axis=1).round(1)
                ca['c2p'] = ca.apply(lambda r: sdiv(r['purchases'], r['cart_adds']) * 100, axis=1).round(1)
                fig = go.Figure()
                fig.add_trace(go.Bar(name='View → Cart %', x=ca['category'], y=ca['v2c'],
                                      marker_color='#4facfe',
                                      text=ca['v2c'].apply(lambda v: f"{v:.1f}%"), textposition='outside',
                                      hovertemplate='%{x}<br>View→Cart: %{y:.1f}%<extra></extra>'))
                fig.add_trace(go.Bar(name='Cart → Purchase %', x=ca['category'], y=ca['c2p'],
                                      marker_color='#43e97b',
                                      text=ca['c2p'].apply(lambda v: f"{v:.1f}%"), textposition='outside',
                                      hovertemplate='%{x}<br>Cart→Purchase: %{y:.1f}%<extra></extra>'))
                styled(fig, height=400, barmode='group',
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                   bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5")))
                st.plotly_chart(fig, use_container_width=True)
                card_end()

            card_start("🔍 Product Performance Map — Views vs Purchases")
            if 'price' in fp.columns:
                fig = px.scatter(fp, x='views', y='purchases', size='adds_to_cart', color='category',
                                  hover_name='name', size_max=30, color_discrete_sequence=GRADIENT_COLORS,
                                  custom_data=['name', 'category', 'price'])
                styled(fig, height=450,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                   bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5")))
                fig.update_traces(hovertemplate='<b>%{customdata[0]}</b><br>Category: %{customdata[1]}<br>'
                                  'Price: ₹%{customdata[2]:,.0f}<br>Views: %{x:,}<br>Purchases: %{y:,}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)
            card_end()
    else:
        st.warning("No product data available.")


# ═══════════════════════════════════════════════════════════════════════════════
# USER FUNNEL
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "User Funnel":
    header("🔄 Conversion Funnel", "Customer journey analysis from browse to purchase")

    if not df_funnel.empty:
        fs = df_funnel.sort_values('unique_sessions', ascending=False).reset_index(drop=True)
        stages = fs['funnel_step'].tolist()
        vals = [int(v) for v in fs['unique_sessions'].tolist()]

        card_start("🌊 Customer Journey Funnel")
        colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#fa709a']
        fig = go.Figure(go.Funnel(
            y=stages, x=vals, textposition="inside", textinfo="value+percent initial",
            textfont=dict(size=14, color="white", family="Inter"),
            marker=dict(color=colors[:len(stages)], line=dict(width=2, color="rgba(255,255,255,0.2)")),
            connector=dict(line=dict(color="rgba(102,126,234,0.3)", dash="dot", width=2))
        ))
        styled(fig, height=420, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        card_end()

        # Drop-off metrics
        card_start("📉 Stage-by-Stage Drop-off Analysis")
        cols = st.columns(len(stages))
        for i, col in enumerate(cols):
            pct = sdiv(vals[i], vals[0]) * 100
            with col:
                if i == 0:
                    delta_html = f'<div class="kpi-delta positive">{pct:.1f}% of total</div>'
                else:
                    dp = sdiv(vals[i-1] - vals[i], vals[i-1]) * 100
                    delta_html = f'<div class="kpi-delta negative">↓ {dp:.1f}% drop</div>'
                st.markdown(f'''<div class="kpi-card {'revenue' if i==0 else 'orders'}">
                    <div class="kpi-label">{stages[i].replace('_',' ').title()}</div>
                    <div class="kpi-value">{fmt_num(vals[i])}</div>{delta_html}</div>''',
                    unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Drop-off bar chart
        dl, dv = [], []
        for i in range(1, len(stages)):
            dl.append(f"{stages[i-1].replace('_',' ').title()} → {stages[i].replace('_',' ').title()}")
            dv.append(sdiv(vals[i-1] - vals[i], vals[i-1]) * 100)

        fig = px.bar(x=dl, y=dv, color=dv, color_continuous_scale=['#43e97b', '#fee140', '#f5576c'],
                      text=[f"{v:.1f}%" for v in dv])
        styled(fig, height=300, showlegend=False, coloraxis_showscale=False,
               xaxis=dict(title="Transition"), yaxis=dict(title="Drop-off %"))
        fig.update_traces(textposition='outside', textfont_size=13)
        st.plotly_chart(fig, use_container_width=True)
        card_end()

        # Detailed table
        card_start("📋 Detailed Funnel Metrics")
        dd = []
        for i in range(len(stages)):
            pi = sdiv(vals[i], vals[0]) * 100
            if i == 0:
                do = "—"
            else:
                da = vals[i-1] - vals[i]
                dp = sdiv(da, vals[i-1]) * 100
                do = f"−{da:,} ({dp:.1f}%)"
            dd.append({'Stage': stages[i].replace('_',' ').title(), 'Sessions': f"{vals[i]:,}",
                        '% of Initial': f"{pi:.1f}%", 'Drop-off': do})
        st.dataframe(pd.DataFrame(dd), use_container_width=True, hide_index=True)
        card_end()
    else:
        st.warning("No funnel data available.")


# ═══════════════════════════════════════════════════════════════════════════════
# USER INSIGHTS
# ═══════════════════════════════════════════════════════════════════════════════
elif page == "User Insights":
    header("👤 User Insights", "Customer demographics, behavior, and lifetime value analysis")

    if not df_users.empty:
        fu = df_users.copy()
        if 'stf' in st.session_state:
            fu = fu[fu['state'].isin(st.session_state.stf)]
        if 'of' in st.session_state:
            fu = fu[fu['total_orders'] >= st.session_state.of]

        if fu.empty:
            st.info("No users match the selected filters.")
        else:
            active = fu[fu['total_orders'] > 0]
            avg_ltv = active['lifetime_value'].mean() if not active.empty else 0
            avg_ord = active['total_orders'].mean() if not active.empty else 0
            rr = sdiv(len(active[active['total_orders'] > 1]), len(active)) * 100

            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(kpi("👥", "Total Users", fmt_num(len(fu)), cls="customers"), unsafe_allow_html=True)
            c2.markdown(kpi("💎", "Avg LTV", fmt_cur(avg_ltv), cls="revenue"), unsafe_allow_html=True)
            c3.markdown(kpi("📦", "Avg Orders", f"{avg_ord:.1f}", cls="orders"), unsafe_allow_html=True)
            c4.markdown(kpi("🔁", "Repeat Rate", f"{rr:.1f}%", cls="conversion"), unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                card_start("🏆 Top 10 Users by Lifetime Value")
                t10 = fu.nlargest(10, 'lifetime_value')
                t10['label'] = 'User #' + t10['user_id'].astype(str)
                fig = px.bar(t10, y='label', x='lifetime_value', orientation='h',
                              color='lifetime_value', color_continuous_scale=['#667eea', '#f093fb'],
                              text=t10['lifetime_value'].apply(fmt_cur),
                              custom_data=['city', 'state', 'total_orders'])
                styled(fig, height=400, showlegend=False, coloraxis_showscale=False,
                       yaxis=dict(categoryorder='total ascending', gridcolor="rgba(0,0,0,0)"))
                fig.update_traces(textposition='outside', textfont_size=11,
                                  hovertemplate='<b>%{y}</b><br>LTV: ₹%{x:,.0f}<br>'
                                  'City: %{customdata[0]}<br>State: %{customdata[1]}<br>'
                                  'Orders: %{customdata[2]}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)
                card_end()

            with col2:
                card_start("🗺️ Orders by State")
                sa = fu.groupby('state').agg(total_orders=('total_orders','sum'), users=('user_id','count'),
                                              avg_ltv=('lifetime_value','mean')).reset_index()
                sa = sa.sort_values('total_orders', ascending=True)
                fig = px.bar(sa, y='state', x='total_orders', orientation='h',
                              color='total_orders', color_continuous_scale=['#4facfe', '#00f2fe', '#43e97b'],
                              custom_data=['users', 'avg_ltv'])
                styled(fig, height=400, showlegend=False, coloraxis_showscale=False,
                       yaxis=dict(gridcolor="rgba(0,0,0,0)"))
                fig.update_traces(hovertemplate='<b>%{y}</b><br>Orders: %{x:,}<br>'
                                  'Users: %{customdata[0]:,}<br>Avg LTV: ₹%{customdata[1]:,.0f}<extra></extra>')
                st.plotly_chart(fig, use_container_width=True)
                card_end()

            col1, col2 = st.columns(2)
            with col1:
                card_start("📊 Orders vs LTV Distribution")
                smp = active.sample(min(2000, len(active)), random_state=42) if len(active) > 0 else active
                fig = px.scatter(smp, x='total_orders', y='lifetime_value', color='state',
                                  opacity=0.6, color_discrete_sequence=GRADIENT_COLORS,
                                  hover_data={'city': True, 'total_orders': True, 'lifetime_value': ':,.0f'})
                styled(fig, height=400,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
                                   bgcolor="rgba(0,0,0,0)", font=dict(color="#8b8bb5", size=9)))
                fig.update_traces(marker=dict(size=5))
                st.plotly_chart(fig, use_container_width=True)
                card_end()

            with col2:
                card_start("🏙️ Top Cities by Customer Count")
                ca = fu.groupby('city').agg(users=('user_id','count'), avg_orders=('total_orders','mean'),
                                             avg_ltv=('lifetime_value','mean')).reset_index().nlargest(12, 'users')
                fig = px.bar(ca, x='city', y='users', color='avg_ltv',
                              color_continuous_scale=['#667eea', '#f093fb'],
                              text='users', custom_data=['avg_orders', 'avg_ltv'])
                styled(fig, height=400, showlegend=False, coloraxis_showscale=False)
                fig.update_traces(textposition='outside', textfont_size=11,
                                  hovertemplate='<b>%{x}</b><br>Users: %{y:,}<br>'
                                  'Avg Orders: %{customdata[0]:.1f}<br>Avg LTV: ₹%{customdata[1]:,.0f}<extra></extra>')
                fig.update_xaxes(tickangle=45)
                st.plotly_chart(fig, use_container_width=True)
                card_end()

            card_start("📋 User Demographics & Metrics")
            disp = fu.sort_values('lifetime_value', ascending=False).head(100).rename(columns={
                'user_id': 'User ID', 'city': 'City', 'state': 'State',
                'total_orders': 'Orders', 'lifetime_value': 'Lifetime Value (₹)'
            })
            st.dataframe(disp, use_container_width=True, hide_index=True,
                          column_config={"Lifetime Value (₹)": st.column_config.NumberColumn(format="₹%.2f")})
            card_end()
    else:
        st.warning("No user data available.")


# ─── Demo Banner ─────────────────────────────────────────────────────────────
if DEMO_MODE:
    st.markdown('''<div class="demo-banner">
        <span>🔬 Demo Mode — Powered by precomputed Parquet files • No live database connections</span>
    </div>''', unsafe_allow_html=True)
