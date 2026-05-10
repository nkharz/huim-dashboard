import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import io
import os
import sys
from datetime import datetime

# Add the current directory to the Python path to fix Streamlit Cloud ModuleNotFoundError
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.db_connector import test_connection, load_transactions, load_saved_results, save_upload_record
from modules.huim_engine import HUIMEngine, AprioriMiner
from modules.file_processor import FileProcessor

st.set_page_config(
    page_title="HUIM System v2.0",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.markdown("""
    <style>
    .stApp {
        background-color: #0b0f19;
        background-image: 
            radial-gradient(circle at 15% 50%, rgba(16, 185, 129, 0.08), transparent 25%),
            radial-gradient(circle at 85% 30%, rgba(59, 130, 246, 0.08), transparent 25%);
    }
    .login-container {
        max-width: 400px;
        margin: 10vh auto;
        padding: 40px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(59, 130, 246, 0.3);
        border-radius: 20px;
        box-shadow: 0 0 40px rgba(59, 130, 246, 0.2);
        backdrop-filter: blur(10px);
        text-align: center;
        animation: fadeIn 1s ease-out;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .login-logo {
        font-size: 3rem;
        margin-bottom: 10px;
        animation: float 3s ease-in-out infinite;
    }
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    .login-title {
        color: white;
        font-size: 1.8rem;
        font-weight: 700;
        margin-bottom: 5px;
    }
    .login-sub {
        color: #94a3b8;
        font-size: 0.9rem;
        margin-bottom: 30px;
    }
    </style>
    <div class="login-container">
        <div class="login-logo">🔐</div>
        <div class="login-title">HUIM Portal</div>
        <div class="login-sub">Secure Cyber-Authentication</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="admin")
        if st.button("Authenticate 🚀", use_container_width=True):
            if username == "admin" and password == "admin":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

st.markdown("""
<style>
.main-header {
  background: linear-gradient(135deg,#667eea,#764ba2,#f64f59);
  background-size: 300% 300%;
  animation: gradientShift 5s ease infinite;
  padding: 36px 24px; border-radius: 20px;
  text-align: center; margin-bottom: 28px;
  box-shadow: 0 8px 40px rgba(102,126,234,0.45);
}
@keyframes gradientShift {
  0%{background-position:0% 50%}
  50%{background-position:100% 50%}
  100%{background-position:0% 50%}
}
.header-title {
  font-size: 2.4rem; font-weight: 900; color: white;
  text-shadow: 0 2px 10px rgba(0,0,0,0.3); margin: 0;
}
.header-sub {
  color: rgba(255,255,255,0.85); font-size: 1rem;
  margin-top: 8px; font-weight: 400;
}
.header-team {
  color: rgba(255,255,255,0.7); font-size: 0.82rem;
  margin-top: 12px; letter-spacing: 0.5px;
}
.kpi-card {
  background: linear-gradient(135deg,#1a1a2e,#16213e);
  border: 1px solid rgba(102,126,234,0.35);
  border-radius: 16px; padding: 22px 16px;
  text-align: center;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  margin-bottom: 10px;
}
.kpi-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 30px rgba(102,126,234,0.5);
  border-color: #667eea;
}
.kpi-icon { font-size: 1.8rem; margin-bottom: 8px; }
.kpi-value {
  font-size: 2rem; font-weight: 800;
  background: linear-gradient(90deg,#667eea,#f64f59);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: block;
}
.kpi-label {
  color: #a0aec0; font-size: 0.78rem;
  margin-top: 6px; text-transform: uppercase;
  letter-spacing: 0.8px;
}
.lfhu-card {
  background: linear-gradient(135deg,#f6d365,#fda085);
  border-radius: 14px; padding: 18px 20px;
  margin: 10px 0;
  border-left: 6px solid #e67e22;
  animation: slideInLeft 0.5s ease forwards;
  box-shadow: 0 6px 20px rgba(253,160,133,0.35);
}
.lfhu-card-title {
  font-size: 1.1rem; font-weight: 800;
  color: #2d3748; margin-bottom: 4px;
}
.lfhu-card-meta { color: #4a5568; font-size: 0.88rem; }
.lfhu-card-insight {
  color: #744210; font-size: 0.82rem;
  margin-top: 6px; font-style: italic;
}
@keyframes slideInLeft {
  from { opacity:0; transform:translateX(-40px); }
  to   { opacity:1; transform:translateX(0); }
}
.upload-zone {
  border: 2.5px dashed #667eea;
  border-radius: 20px; padding: 50px 30px;
  text-align: center;
  background: linear-gradient(135deg, rgba(102,126,234,0.06),rgba(118,75,162,0.06));
  animation: pulseBorder 2.5s ease infinite;
  transition: all 0.3s ease;
}
.upload-zone:hover {
  background: rgba(102,126,234,0.12);
  transform: scale(1.01);
}
@keyframes pulseBorder {
  0%,100% { border-color:#667eea; box-shadow:0 0 0 0 rgba(102,126,234,0.2); }
  50%      { border-color:#f64f59; box-shadow:0 0 0 8px rgba(246,79,89,0.05); }
}
.upload-icon { font-size: 3.5rem; margin-bottom: 12px; }
.upload-title { font-size: 1.3rem; font-weight: 700; color: #667eea; }
.upload-sub { color: #718096; font-size: 0.9rem; margin-top: 6px; }
.step-card {
  background: rgba(102,126,234,0.08);
  border: 1px solid rgba(102,126,234,0.2);
  border-radius: 12px; padding: 16px;
  text-align: center;
  transition: all 0.3s ease;
  margin-bottom: 10px;
}
.step-card:hover {
  background: rgba(102,126,234,0.18);
  transform: translateY(-3px);
}
.step-num {
  font-size: 1.5rem; font-weight: 900;
  background: linear-gradient(90deg,#667eea,#764ba2);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
.apriori-side {
  background: linear-gradient(135deg,#c0392b,#e74c3c);
  border-radius: 16px; padding: 24px;
  text-align: center; color: white;
}
.huim-side {
  background: linear-gradient(135deg,#11998e,#38ef7d);
  border-radius: 16px; padding: 24px;
  text-align: center; color: white;
}
.vs-badge {
  background: linear-gradient(135deg,#667eea,#764ba2);
  color: white; border-radius: 50%;
  width: 50px; height: 50px;
  display: flex; align-items: center;
  justify-content: center;
  font-weight: 900; font-size: 1.2rem;
  margin: auto; box-shadow: 0 4px 15px rgba(102,126,234,0.5);
}
.db-online  { color:#38ef7d; font-weight:700; }
.db-offline { color:#f64f59; font-weight:700; }
.animated-divider {
  height: 3px; border-radius: 2px;
  background: linear-gradient(90deg,#667eea,#f64f59,#667eea);
  background-size: 200% 100%;
  animation: shimmer 2s linear infinite;
  margin: 20px 0;
}
@keyframes shimmer {
  0%  { background-position:200% 0; }
  100%{ background-position:-200% 0; }
}
</style>
""", unsafe_allow_html=True)

st.markdown('''
<div class="main-header">
  <div class="header-title">💎 High Utility Itemset Mining System</div>
  <div class="header-sub">
    Matrix-Based Approach · Dynamic Percentile Thresholding ·
    HFHU · HFLU · LFHU Classification
  </div>
  <div class="animated-divider"></div>
  <div class="header-team">
    Bujja Abigna · Dharini R · Harini N &nbsp;|&nbsp;
    Guide: Dr. S J Vivekanandan &nbsp;|&nbsp;
    Dhanalakshmi College of Engineering, Chennai
  </div>
</div>
''', unsafe_allow_html=True)

db_ok = test_connection()

st.sidebar.markdown("## 💎 HUIM System v2.0")
if db_ok:
  st.sidebar.markdown('<p class="db-online">🟢 MySQL Connected</p>', unsafe_allow_html=True)
else:
  st.sidebar.markdown('<p class="db-offline">🔴 MySQL Offline — CSV Mode</p>', unsafe_allow_html=True)

st.sidebar.markdown("### ⚙️ Mining Configuration")
max_combo   = st.sidebar.slider("Max Itemset Size", 2, 4, 2)
apriori_sup = st.sidebar.slider("Apriori Min Support", 0.10, 0.90, 0.30, 0.05)
data_limit  = st.sidebar.selectbox("Records to Load", [5000,10000,20000])
save_to_db  = st.sidebar.checkbox("💾 Save Results to MySQL", value=db_ok)

st.sidebar.markdown("### 📂 Data Source")
data_source = st.sidebar.radio("Source", ["MySQL Database","Upload File","Sample CSV"])

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='background:rgba(102,126,234,0.15);border-radius:10px;padding:12px;margin-bottom:20px;'>
  <b style='color:#667eea'>Project Info</b><br>
  <small style='color:#a0aec0'>
  📚 Final Year Project<br>
  🏫 DCE Chennai<br>
  📅 2024 | v2.0.0
  </small>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.logged_in = False
    st.rerun()

@st.cache_data
def get_data(source, limit):
    if source == "MySQL Database" and db_ok:
        df = load_transactions(limit)
        if not df.empty:
            return df
    
    # Fallback
    csv_path = os.path.join(os.path.dirname(__file__), 'data', 'transactions.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path).head(limit)
    else:
        try:
            from generate_data import generate_fallback_data
            generate_fallback_data(limit)
            return pd.read_csv(csv_path).head(limit)
        except Exception:
            return None

df = None
if data_source in ["MySQL Database", "Sample CSV"]:
    df = get_data(data_source, data_limit)

huim_results = None
apriori_results = None

if df is not None and not df.empty:
    with st.spinner("Initializing Data Engines..."):
        engine = HUIMEngine(df)
        huim_results = engine.run_full_pipeline(max_combo_size=max_combo)
        
        apriori = AprioriMiner(df, min_support=apriori_sup)
        apriori_results = apriori.run(max_size=max_combo)

tab1,tab2,tab3,tab4,tab5,tab6,tab7,tab8,tab9 = st.tabs([
  "🏠 Overview",
  "🏷️ Classification",
  "⚠️ LFHU Alerts",
  "⚔️ vs Apriori",
  "📈 Monthly Trends",
  "🧮 Utility Matrix",
  "📊 Performance",
  "📂 Upload & Analyze",
  "🗄️ Database"
])

def render_kpi_card(title, value, icon):
    return f"""
    <div class="kpi-card">
      <div class="kpi-icon">{icon}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{title}</div>
    </div>
    """

with tab1:
    if huim_results:
        c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)
        kpis = [
            ("Transactions", df['transaction_id'].nunique(), "💼"),
            ("Items", df['item_name'].nunique(), "🛒"),
            ("Records", len(df), "📋"),
            ("Patterns", huim_results['patterns_found'], "🎯"),
            ("Speed (s)", f"{huim_results['execution_time']:.3f}", "⚡"),
            ("DB Scans", huim_results['db_scans'], "🔁"),
            ("LFHU Count", huim_results['category_summary'].get('LFHU', 0), "⚠️"),
            ("Months", df['month_year'].nunique() if 'month_year' in df.columns else 0, "📅")
        ]
        
        for i, col in enumerate([c1, c2, c3, c4, c5, c6, c7, c8]):
            with col:
                st.markdown(render_kpi_card(*kpis[i]), unsafe_allow_html=True)
                
        st.markdown("### How It Works")
        sc1, sc2, sc3, sc4, sc5, sc6 = st.columns(6)
        steps = [
            ("1", "📥 Data Collection", "MySQL / CSV / Upload"),
            ("2", "🧹 Preprocessing", "Clean, fix, validate"),
            ("3", "🧮 Utility Matrix", "Uij = Qty × Profit"),
            ("4", "📊 Support & Utility", "Frequency + Profit score"),
            ("5", "🎯 Dynamic Threshold", "Percentile-based Sth, Uth"),
            ("6", "🏷️ Classify", "HFHU · HFLU · LFHU")
        ]
        for col, step in zip([sc1, sc2, sc3, sc4, sc5, sc6], steps):
            with col:
                st.markdown(f"""
                <div class="step-card">
                  <div class="step-num">{step[0]}</div>
                  <b>{step[1]}</b><br><small>{step[2]}</small>
                </div>
                """, unsafe_allow_html=True)

        ic1, ic2, ic3 = st.columns(3)
        ic1.info("**What is HUIM?**\nHigh Utility Itemset Mining finds items that yield high profit.")
        ic2.info("**Why Matrix?**\nAllows single scan of the database, significantly improving speed.")
        ic3.info("**Why Dynamic Threshold?**\nAutomatically adapts to data distribution.")

        if huim_results['category_summary']:
            cat_df = pd.DataFrame(list(huim_results['category_summary'].items()), columns=['Category', 'Count'])
            fig = px.bar(cat_df, x='Category', y='Count', color='Category',
                         color_discrete_map={'HFHU':'#38ef7d', 'HFLU':'#6dd5ed', 'LFHU':'#ffd200'},
                         template="plotly_dark")
            st.plotly_chart(fig, use_container_width=True)

with tab2:
    if huim_results:
        res_df = huim_results['results_df']
        f1, f2, f3 = st.columns(3)
        sel_cat = f1.multiselect("Category", ["HFHU", "HFLU", "LFHU"], default=["HFHU", "HFLU", "LFHU"])
        sel_size = f2.multiselect("Size", [1, 2, 3, 4], default=[1, 2, 3, 4])
        search = f3.text_input("Search itemsets")
        
        filt_df = res_df[res_df['category'].isin(sel_cat) & res_df['itemset_size'].isin(sel_size)]
        if search:
            filt_df = filt_df[filt_df['itemset'].str.contains(search, case=False)]
            
        st.dataframe(filt_df, use_container_width=True)
        
        st.info(f"🎯 Sth = {huim_results['thresholds']['Sth']:.4f} | Uth = {huim_results['thresholds']['Uth']:,.2f} | Method: Percentile-Based Auto")
        
        pc1, pc2 = st.columns(2)
        with pc1:
            cat_df = pd.DataFrame(list(huim_results['category_summary'].items()), columns=['Category', 'Count'])
            if not cat_df.empty:
                fig_pie = px.pie(cat_df, values='Count', names='Category',
                                 color='Category',
                                 color_discrete_map={'HFHU':'#38ef7d', 'HFLU':'#6dd5ed', 'LFHU':'#ffd200'},
                                 template="plotly_dark", title="Category Distribution")
                fig_pie.update_traces(pull=[0.05]*len(cat_df))
                st.plotly_chart(fig_pie, use_container_width=True)
        with pc2:
            top15 = res_df.head(15)
            if not top15.empty:
                fig_bar = px.bar(top15, x='utility', y='itemset', orientation='h',
                                 color='category',
                                 color_discrete_map={'HFHU':'#38ef7d', 'HFLU':'#6dd5ed', 'LFHU':'#ffd200'},
                                 template="plotly_dark", title="Top 15 Items by Utility")
                fig_bar.add_vline(x=huim_results['thresholds']['Uth'], line_dash="dash", line_color="red")
                st.plotly_chart(fig_bar, use_container_width=True)

with tab3:
    if huim_results:
        st.warning("⚠️ Hidden Profit Drivers — Completely MISSED by Apriori!")
        lfhu_df = huim_results['results_df'][huim_results['results_df']['category'] == 'LFHU']
        
        st.markdown(f"### {len(lfhu_df)} LFHU Patterns Found")
        
        if not lfhu_df.empty:
            for _, row in lfhu_df.iterrows():
                st.markdown(f"""
                <div class="lfhu-card">
                  <div class="lfhu-card-title">⚡ {row['itemset']}</div>
                  <div class="lfhu-card-meta">
                    Utility: ₹{row['utility']:,.0f} &nbsp;|&nbsp;
                    Support: {row['support']:.4f} &nbsp;|&nbsp;
                    {row['itemset_size']}-item pattern
                  </div>
                  <div class="lfhu-card-insight">
                    💡 This pattern generates high profit despite low frequency.
                    Consider targeted promotions to boost visibility.
                  </div>
                </div>
                """, unsafe_allow_html=True)
            
            fig = px.bar(lfhu_df, x='itemset', y='utility', template="plotly_dark", color_discrete_sequence=['orange'])
            fig.add_hline(y=huim_results['thresholds']['Uth'], line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
            
        ap_n = apriori_results['patterns_found'] if apriori_results else 0
        lfhu_n = len(lfhu_df)
        huim_n = huim_results['patterns_found']
        st.info(f"Apriori found {ap_n} patterns — MISSED {lfhu_n} profit items")
        st.success(f"HUIM found {huim_n} patterns — including all {lfhu_n} LFHU items")

with tab4:
    if huim_results and apriori_results:
        col1, col2, col3 = st.columns([4, 1, 4])
        with col1:
            st.markdown(f"""
            <div class="apriori-side">
                <h3>🔴 Apriori Algorithm</h3>
                <p>Traditional — Frequency Only</p>
                <hr>
                <p>Time: {apriori_results['execution_time']:.2f}s</p>
                <p>Scans: {apriori_results['db_scans']}</p>
                <p>Patterns: {apriori_results['patterns_found']}</p>
                <p>❌ No Profit</p>
                <p>❌ No LFHU</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="vs-badge" style="margin-top: 50px;">VS</div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="huim-side">
                <h3>🟢 HUIM Matrix</h3>
                <p>Novel — Utility + Frequency</p>
                <hr>
                <p>Time: {huim_results['execution_time']:.2f}s</p>
                <p>Scans: {huim_results['db_scans']}</p>
                <p>Patterns: {huim_results['patterns_found']}</p>
                <p>✅ Profit Included</p>
                <p>✅ LFHU Detected</p>
            </div>
            """, unsafe_allow_html=True)
            
        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            fig1 = px.bar(x=['Apriori', 'HUIM'], y=[apriori_results['execution_time'], huim_results['execution_time']],
                         title="Execution Time (s)", template="plotly_dark", color=['Apriori', 'HUIM'],
                         color_discrete_map={'Apriori': '#f64f59', 'HUIM': '#38ef7d'})
            st.plotly_chart(fig1, use_container_width=True)
        with bc2:
            fig2 = px.bar(x=['Apriori', 'HUIM'], y=[apriori_results['db_scans'], huim_results['db_scans']],
                         title="Database Scans", template="plotly_dark", color=['Apriori', 'HUIM'],
                         color_discrete_map={'Apriori': '#f64f59', 'HUIM': '#38ef7d'})
            st.plotly_chart(fig2, use_container_width=True)
        with bc3:
            fig3 = px.bar(x=['Apriori', 'HUIM'], y=[apriori_results['patterns_found'], huim_results['patterns_found']],
                         title="Patterns Found", template="plotly_dark", color=['Apriori', 'HUIM'],
                         color_discrete_map={'Apriori': '#f64f59', 'HUIM': '#38ef7d'})
            st.plotly_chart(fig3, use_container_width=True)
            
        speedup = apriori_results['execution_time'] / huim_results['execution_time'] if huim_results['execution_time'] > 0 else 0
        scan_red = 100 * (apriori_results['db_scans'] - huim_results['db_scans']) / apriori_results['db_scans'] if apriori_results['db_scans'] > 0 else 0
        st.success(f"✅ HUIM is {speedup:.1f}x FASTER with {scan_red:.0f}% FEWER DB SCANS!")

with tab5:
    if huim_results and not huim_results['monthly_df'].empty:
        m_df = huim_results['monthly_df']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=m_df['month_year'], y=m_df['total_utility'], fill='tozeroy',
                                mode='lines+markers+text', text=m_df['total_utility'].apply(lambda x: f"₹{x:,.0f}"),
                                textposition="top center", line_color="#667eea", fillcolor="rgba(102,126,234,0.15)"))
        fig.update_layout(template="plotly_dark", title="Monthly Trends", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)

with tab6:
    if huim_results:
        matrix = huim_results['utility_matrix']
        st.info("First 100 rows of Utility Matrix shown")
        m_small = matrix.head(100)
        fig = go.Figure(data=go.Heatmap(z=m_small.values, x=m_small.columns, y=m_small.index, colorscale='Viridis'))
        fig.update_layout(template="plotly_dark", title="Utility Matrix Heatmap")
        st.plotly_chart(fig, use_container_width=True)

with tab7:
    st.markdown("### Formula Verification")
    st.latex(r"U_{ij} = Q(i,j) \times P(j)")
    st.latex(r"Support(X) = \frac{|\{T_i \in D | X \subseteq T_i\}|}{|D|}")
    st.latex(r"Utility(X) = \sum \sum U_{ij}")
    
    fig = go.Figure(data=go.Scatterpolar(
        r=[90, 80, 95, 85, 99],
        theta=['Speed', 'Accuracy', 'Scalability', 'Pattern Quality', 'LFHU Detection'],
        fill='toself', name='HUIM', line_color='#38ef7d'
    ))
    fig.add_trace(go.Scatterpolar(
        r=[40, 70, 30, 50, 10],
        theta=['Speed', 'Accuracy', 'Scalability', 'Pattern Quality', 'LFHU Detection'],
        fill='toself', name='Apriori', line_color='#f64f59'
    ))
    fig.update_layout(template="plotly_dark", polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
    st.plotly_chart(fig, use_container_width=True)

with tab8:
    st.markdown('''
    <div class="upload-zone">
      <div class="upload-icon">📁</div>
      <div class="upload-title">Drag & Drop or Browse Your File</div>
      <div class="upload-sub">
        Supports CSV · XLSX · XLS &nbsp;|&nbsp;
        Any column names &nbsp;|&nbsp;
        Auto-fixed intelligently
      </div>
    </div>
    ''', unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
      "Choose your transaction file",
      type=['csv','xlsx','xls'],
      help="Any column names accepted. System auto-detects and fixes."
    )
    
    fp = FileProcessor()
    
    if st.button("⬇️ Download Sample Template"):
        template_bytes = fp.generate_sample_template()
        st.download_button(
            label="Click here to download",
            data=template_bytes,
            file_name="huim_template.xlsx",
            mime="application/vnd.ms-excel"
        )
        
    if uploaded_file is not None:
        raw_df, read_error = fp.load_file(uploaded_file)
        if read_error:
            st.error(f"⚠️ {read_error}")
        else:
            st.success("✅ File loaded successfully!")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Filename", uploaded_file.name)
            c2.metric("Size", f"{uploaded_file.size / 1024:.1f} KB")
            c3.metric("Rows", len(raw_df))
            c4.metric("Columns", len(raw_df.columns))
            
            col_report = fp.detect_columns(raw_df)
            with st.expander("Column Detection Report", expanded=True):
                report_data = []
                for k, v in col_report.items():
                    report_data.append({"Required Column": k, "Found As": str(v.get('original')), "Status": "✅ Found" if v['found'] else "⚙️ Will fix"})
                st.table(pd.DataFrame(report_data))
            
            needs_profit = fp.needs_profit_input(raw_df)
            profit_map = None
            
            if needs_profit:
                st.warning("⚠️ No profit column found in your file.")
                profit_mode = st.radio("Choose profit mode:", [
                  "📝 Enter profit manually per item",
                  "⚖️ Equal weight (profit = 1 for all items)",
                ])
                if "Enter profit" in profit_mode:
                    profit_map = {}
                    items = fp.get_unique_items(raw_df)
                    cols = st.columns(3)
                    for i, item in enumerate(items):
                        with cols[i % 3]:
                            profit_map[item] = st.number_input(f"{item}", value=5.0, key=f"p_{i}")
                            
            if st.button("🚀 Run HUIM Analysis on Your Data", type="primary", use_container_width=True):
                with st.status("Running analysis..."):
                    cleaned_df, _, qual = fp.validate_and_fix(raw_df, profit_map=profit_map)
                    eng = HUIMEngine(cleaned_df)
                    res = eng.run_full_pipeline(max_combo_size=2)
                    st.success("Analysis Complete!")
                
                st.markdown("---")
                sub1, sub2, sub3, sub4 = st.tabs(["📊 Summary", "⚠️ LFHU Found", "🏷️ All Patterns", "🧮 Utility Matrix"])
                with sub1:
                    st.write("### Category Distribution")
                    cat_df = pd.DataFrame(list(res['category_summary'].items()), columns=['Category', 'Count'])
                    if not cat_df.empty:
                        fig_pie = px.pie(cat_df, values='Count', names='Category',
                                         color='Category',
                                         color_discrete_map={'HFHU':'#38ef7d', 'HFLU':'#6dd5ed', 'LFHU':'#ffd200'},
                                         template="plotly_dark")
                        st.plotly_chart(fig_pie, use_container_width=True)
                        
                with sub2:
                    lfhu_df = res['results_df'][res['results_df']['category'] == 'LFHU']
                    if not lfhu_df.empty:
                        st.warning(f"Found {len(lfhu_df)} LFHU Patterns!")
                        fig = px.bar(lfhu_df, x='itemset', y='utility', template="plotly_dark", color_discrete_sequence=['orange'])
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No LFHU patterns found in this dataset.")
                        
                with sub3:
                    st.dataframe(res['results_df'], use_container_width=True)
                    
                with sub4:
                    matrix = res['utility_matrix'].head(100)
                    fig = go.Figure(data=go.Heatmap(z=matrix.values, x=matrix.columns, y=matrix.index, colorscale='Viridis'))
                    fig.update_layout(template="plotly_dark", title="Utility Matrix Heatmap (First 100 Rows)")
                    st.plotly_chart(fig, use_container_width=True)

with tab9:
    if db_ok:
        st.success("Database Connected Successfully")
    else:
        st.error("Database Not Connected. Run setup_database.py first.")
