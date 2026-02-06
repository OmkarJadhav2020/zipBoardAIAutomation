import streamlit as st
import subprocess
import sys
import os
import pandas as pd
import sqlite3
import time

# Page Config
st.set_page_config(
    page_title="Autonmous Controller",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for "Lit" look (Dark mode optimizations)
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 4px 14px 0 rgba(0,0,0,0.2);
        transition: 0.2s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #4CAF50;
    }
    h1 {
        background: -webkit-linear-gradient(45deg, #00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
</style>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.header("⚡ System Control")
    st.caption("v2.1 Premium")
    if st.button("🔄 Refresh Data"):
        st.rerun()

# Header
st.title("🚀 Autonomous AI System")
st.markdown("### _Review, Analyze, and Report Pipeline_")
st.divider()

# Metrics Section - Real-time stats
if os.path.exists("ai_automation.db"):
    try:
        conn = sqlite3.connect("ai_automation.db")
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='articles'")
        if cursor.fetchone()[0] == 1:
            total_articles = pd.read_sql("SELECT COUNT(*) FROM articles", conn).iloc[0,0]
            analyzed_articles = pd.read_sql("SELECT COUNT(*) FROM articles WHERE gap_analysis IS NOT NULL", conn).iloc[0,0]
        else:
            total_articles = 0
            analyzed_articles = 0
        conn.close()
    except Exception as e:
        total_articles = 0
        analyzed_articles = 0
        # st.error(f"DB Error: {e}")
else:
    total_articles = 0
    analyzed_articles = 0

# Display Metrics
m1, m2, m3, m4 = st.columns(4)
m1.metric("📂 Total Articles", total_articles)
m2.metric("🧠 Analyzed", analyzed_articles, f"{analyzed_articles/total_articles*100:.1f}%" if total_articles else "0%")
m3.metric("⚡ System Status", "Online")
m4.metric("📅 Last Update", time.strftime("%H:%M"))

st.markdown("---")

# Process Runner
def run_process_with_log(script_name, log_container, status_label):
    """Runs script and updates UI using st.status"""
    with log_container.status(status_label, expanded=True) as status:
        st.write(f"🚀 Launching {script_name}...")
        
        cmd = [sys.executable, script_name]
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                encoding='utf-8',
                cwd=os.getcwd() # Run in current dir
            )
            
            output_area = st.empty()
            full_log = ""
            
            for line in iter(process.stdout.readline, ''):
                full_log += line
                # Keep log concise
                output_area.code(full_log[-3000:], language='bash') 
                
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                status.update(label=f"✅ {script_name} Completed!", state="complete", expanded=False)
                st.toast(f"{script_name} finished successfully!", icon="🎉")
            else:
                status.update(label=f"❌ {script_name} Failed (Exit Code: {return_code})", state="error")
                st.error("Check logs above for details.")
        except Exception as e:
            status.update(label="❌ Execution Error", state="error")
            st.error(f"Failed to run script: {e}")

# Main Controls Layout
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("1. 📡 Collection")
    st.caption("Scrape Help Center data")
    if st.button("Start Scraper", type="primary", key="btn_scrape"):
        run_process_with_log("1_collect_data.py", st, "Fetching Data...")

with c2:
    st.subheader("2. 🧠 Analysis")
    st.caption("Run Multi-Model AI Agent")
    if st.button("Start AI Agent", type="primary", key="btn_analyze"):
        run_process_with_log("2_analyze_content.py", st, "Running AI Models...")

with c3:
    st.subheader("3. 📊 Reporting")
    st.caption("Generate Excel Audit")
    if st.button("Generate Report", type="primary", key="btn_report"):
        run_process_with_log("3_generate_report.py", st, "Building Report...")
        
        time.sleep(1) # Wait for file write
        files = [f for f in os.listdir('.') if f.startswith('AI_Audit_Report') and f.endswith('.xlsx')]
        if files:
            latest = max(files, key=os.path.getctime)
            with open(latest, "rb") as f:
                st.download_button("📥 Download Report", f, file_name=latest, use_container_width=True)

st.divider()

# Strategic Insights Preview
st.subheader("💡 Strategic Gap Analysis (Top 5)")
if os.path.exists("ai_automation.db"):
    conn = sqlite3.connect("ai_automation.db")
    try:
        df_gaps = pd.read_sql("SELECT gap_id, category, priority, description, suggested_title, rationale FROM gap_insights", conn)
        if not df_gaps.empty:
            st.dataframe(
                df_gaps, 
                column_config={
                    "priority": st.column_config.TextColumn(
                        "Priority",
                        help="Impact level",
                        validate="^(High|Medium|Low)$"
                    )
                },
                use_container_width=True,
                hide_index=True
            )
        else:
             st.info("No insights generated yet. Run Step 4.")
    except Exception as e:
        st.write("Gap table not ready.")
    conn.close()

st.divider()

# Data Preview Expander
with st.expander("📂 Live Database Preview (Last 50 Articles)", expanded=False):
    if os.path.exists("ai_automation.db"):
        conn = sqlite3.connect("ai_automation.db")
        try:
            df = pd.read_sql("SELECT id, title, category_id, article_custom_id, gap_analysis FROM articles ORDER BY id DESC LIMIT 50", conn)
            st.dataframe(df, use_container_width=True)
        except:
            st.write("No data found yet.")
        conn.close()
    else:
        st.write("Database not initialized yet.")
