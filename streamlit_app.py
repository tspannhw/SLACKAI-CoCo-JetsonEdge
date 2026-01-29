import streamlit as st
from snowflake.snowpark.context import get_active_session
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Jetson Edge Monitor",
    page_icon="🖥️",
    layout="wide"
)

@st.cache_resource
def get_session():
    return get_active_session()

@st.cache_data(ttl=60)
def load_data(_session, host_filter: str, start_date: datetime, end_date: datetime):
    query = """
        SELECT 
            ROW_ID, HOST, IP_ADDRESS, MAC_ADDRESS, TS_UTC,
            CPU_TEMP_C, CPU_USAGE_PCT, MEM_USAGE_PCT, DISK_USAGE_PCT,
            EDGE_AI_SUMMARY, IMAGE_PATH, IMAGE_CAPTURED, IMAGE_AI_SUMMARY
        FROM DEMO.DEMO.JETSON_EDGE_STREAM
        WHERE TS_UTC BETWEEN '{start}' AND '{end}'
    """.format(start=start_date, end=end_date)
    
    if host_filter and host_filter != "All":
        query += f" AND HOST = '{host_filter}'"
    
    query += " ORDER BY TS_UTC DESC LIMIT 10000"
    return _session.sql(query).to_pandas()

@st.cache_data(ttl=300)
def get_hosts(_session):
    df = _session.sql("SELECT DISTINCT HOST FROM DEMO.DEMO.JETSON_EDGE_STREAM").to_pandas()
    return ["All"] + df["HOST"].tolist()

session = get_session()

st.title("Jetson Edge Monitoring Dashboard")

col1, col2, col3 = st.columns(3)
with col1:
    hosts = get_hosts(session)
    selected_host = st.selectbox("Host", hosts)
with col2:
    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=7))
with col3:
    end_date = st.date_input("End Date", datetime.now())

start_dt = datetime.combine(start_date, datetime.min.time())
end_dt = datetime.combine(end_date, datetime.max.time())

df = load_data(session, selected_host, start_dt, end_dt)

if df.empty:
    st.warning("No data found for the selected filters.")
    st.stop()

st.subheader("Key Metrics")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Records", len(df))
m2.metric("Avg CPU Temp", f"{df['CPU_TEMP_C'].mean():.1f}°C")
m3.metric("Avg CPU Usage", f"{df['CPU_USAGE_PCT'].mean():.1f}%")
m4.metric("Avg Memory Usage", f"{df['MEM_USAGE_PCT'].mean():.1f}%")

st.subheader("System Metrics Over Time")
chart_df = df[["TS_UTC", "CPU_TEMP_C", "CPU_USAGE_PCT", "MEM_USAGE_PCT", "DISK_USAGE_PCT"]].copy()
chart_df = chart_df.sort_values("TS_UTC")

tab1, tab2, tab3, tab4 = st.tabs(["CPU Temp", "CPU Usage", "Memory Usage", "Disk Usage"])

with tab1:
    st.line_chart(chart_df.set_index("TS_UTC")["CPU_TEMP_C"])
with tab2:
    st.line_chart(chart_df.set_index("TS_UTC")["CPU_USAGE_PCT"])
with tab3:
    st.line_chart(chart_df.set_index("TS_UTC")["MEM_USAGE_PCT"])
with tab4:
    st.line_chart(chart_df.set_index("TS_UTC")["DISK_USAGE_PCT"])

st.subheader("AI Summaries & Images")

ai_df = df[df["EDGE_AI_SUMMARY"].notna() | df["IMAGE_AI_SUMMARY"].notna() | df["IMAGE_PATH"].notna()]

if ai_df.empty:
    st.info("No AI summaries or images available for the selected data.")
else:
    for idx, row in ai_df.head(20).iterrows():
        with st.expander(f"📷 {row['TS_UTC']} - {row['HOST']}", expanded=False):
            col_left, col_right = st.columns(2)
            
            with col_left:
                if row["EDGE_AI_SUMMARY"] and str(row["EDGE_AI_SUMMARY"]).strip():
                    st.markdown("**Edge AI Summary**")
                    st.write(row["EDGE_AI_SUMMARY"])
                
                if row["IMAGE_AI_SUMMARY"] and str(row["IMAGE_AI_SUMMARY"]).strip():
                    st.markdown("**Image AI Summary**")
                    st.write(row["IMAGE_AI_SUMMARY"])
            
            with col_right:
                if row["IMAGE_PATH"] and str(row["IMAGE_PATH"]).strip():
                    st.markdown("**Image Path**")
                    st.code(row["IMAGE_PATH"])
                    if row["IMAGE_CAPTURED"]:
                        st.success("Image captured")

st.subheader("Data Table")
display_cols = ["TS_UTC", "HOST", "IP_ADDRESS", "CPU_TEMP_C", "CPU_USAGE_PCT", "MEM_USAGE_PCT", "DISK_USAGE_PCT", "EDGE_AI_SUMMARY", "IMAGE_PATH"]
st.dataframe(df[display_cols], use_container_width=True)

st.subheader("Export Data")
csv = df.to_csv(index=False)
st.download_button(
    label="Download CSV",
    data=csv,
    file_name=f"jetson_edge_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
    mime="text/csv"
)
