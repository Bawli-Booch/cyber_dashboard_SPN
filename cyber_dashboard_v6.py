# streamlit_app.py — Cyber Cell Shahjahanpur Dashboard (No Sidebar Version)
import streamlit as st
import pandas as pd
import plotly.express as px
import requests, re, urllib.parse, datetime
from io import BytesIO
import uuid
from bs4 import BeautifulSoup

#remove streamlit header and footer

# --- Fully hide Streamlit branding: header, menu, footer, and "Manage app" link ---
hide_streamlit_style = """
    <style>
    /* Hide the main menu and footer */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Hide bottom-right floating "View app" / "Manage app" / "Made with Streamlit" link */
    [data-testid="stActionButton"] {display: none !important;}
    [data-testid="stAppViewContainer"] > div:first-child {padding-bottom: 0rem;}
    [data-testid="stStatusWidget"] {display: none !important;}
    .stAppDeployButton {display: none !important;}

    /* Hide Streamlit Cloud floating bar (deployed app bar) */
    [data-testid="stDecoration"] {display: none !important;}
    div[data-testid="stToolbar"] {display: none !important;}
    div[data-testid="stDecorationContainer"] {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

#hide_streamlit_ui
hide_streamlit_ui = """
    <style>
    /* Hide Streamlit header, menu, and footer */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Hide "Manage app" or "View app" button (Streamlit Cloud) */
    button[data-testid="manage-app-button"] {
        display: none !important;
    }
    /* Also hide any deploy or cloud status buttons */
    .stAppDeployButton, [data-testid="stActionButton"], [data-testid="stStatusWidget"], 
    [data-testid="stDecoration"], [data-testid="stToolbar"], [data-testid="stDecorationContainer"] {
        display: none !important;
    }
    </style>
"""
st.markdown(hide_streamlit_ui, unsafe_allow_html=True)


# -----------------------------------------------
# PAGE CONFIG & STYLES
# -----------------------------------------------
st.set_page_config(page_title="Cyber Cell Shahjahanpur v6 Data table below chart / graph", layout="wide", page_icon="🛰️")

with open("style_2.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# -----------------------------------------------
# HEADER
# -----------------------------------------------
st.markdown("""
<div class='hero fixed-top'>
  <div class='brand'>
    <div class='logo'></div>
    <div >
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------
# GLOBAL KPI GROUP DEFINITIONS
# -----------------------------------------------
MONEY_KPI ={

}
KPI_GROUPS = {
    "NCRP": [
        "NCRP past pendency",
        "NCRP new complaints Today",
        "NCRP new complaint above ₹5000",
        "Total amout lost ( in new complaints)",
        "NCRP complaint disposal Today",
        "Recomended for FIR Today",
        "Total amout put on hold  Today",
        "Money returned to victim  Today",
        "Number of bank Account blocked Today",
    ],
    "Device Blocked": [
        "Number of Mobile number for blocking Today",
        "Number of IMEI for blocking Today",
    ],
    "Offline Complaints": [
        "Total offline complaints received Today ( other than NCRP)",
        "Total offline complaints resolved Today ( other than NCRP)",
    ],
    "CEIR Portal": [
        "Number of mobiles entered in CEIR portal Today",
        "Number of mobiles traced Today",
        "Number of phones recovered Today",
    ],
    "Samanvyaya Portal": [
        "Number of events received on Samanvyay portal Today",
        "Number of events closed on Samanvyay portal Today",
    ],
    "Pratibimb Portal": [
        "Number of events on Pratibimb portal Today",
        "Number of events closed on Pratibimb portal Today",
    ],
}

#KPI group no money
KPI_GROUPS_NO_MONEY = {
    "NCRP": [
        "NCRP new complaints Today",
        "NCRP new complaint above ₹5000",
        "NCRP complaint disposal Today",
        "Recomended for FIR Today",
        "Number of bank Account blocked Today",
    ],
    "Device Blocked": [
        "Number of Mobile number for blocking Today",
        "Number of IMEI for blocking Today",
    ],
    "Offline Complaints": [
        "Total offline complaints received Today ( other than NCRP)",
        "Total offline complaints resolved Today ( other than NCRP)",
    ],
    "CEIR Portal": [
        "Number of mobiles entered in CEIR portal Today",
        "Number of mobiles traced Today",
        "Number of phones recovered Today",
    ],
    "Samanvyaya Portal": [
        "Number of events received on Samanvyay portal Today",
        "Number of events closed on Samanvyay portal Today",
    ],
    "Pratibimb Portal": [
        "Number of events on Pratibimb portal Today",
        "Number of events closed on Pratibimb portal Today",
    ],
}
# ============================================================
# 🔧 Global Table Display + Excel Export (for Nested KPI_GROUPS dict)
# ============================================================

#=============================================================
# Display the data table based on data and column name
#=============================================================
def display_table_with_download(
    dataframe: pd.DataFrame,
    filename: str,
    title: str = "Data Table",
    height: int = 400,
    kpi_groups: dict | list | set = None
):
    """
    Displays only Thana, Circle, Created_At + all KPI_GROUPS columns.
    Automatically handles nested KPI_GROUPS dicts.
    """
    st.markdown("---")

    global KPI_GROUPS
    if not kpi_groups:
        kpi_groups = KPI_GROUPS

    st.markdown(f"#### 📋 {title}")

    if dataframe is None or dataframe.empty:
        st.info("No data available to display.")
        return

    # --- Flatten KPI columns from nested dictionary ---
    all_kpis = []
    if isinstance(kpi_groups, dict):
        for group, kpis in kpi_groups.items():
            all_kpis.extend(kpis)
    elif isinstance(kpi_groups, (list, set)):
        all_kpis = list(kpi_groups)

    # --- Identify structural columns ---
    show_cols = []
    for col in ["Thana", "Circle", "Created_At", "created_at"]:
        if col in dataframe.columns:
            show_cols.append(col)

    # --- Add KPI columns present in dataframe ---
    for kpi in all_kpis:
        if kpi in dataframe.columns:
            show_cols.append(kpi)

    # Remove duplicates and invalids
    show_cols = [c for i, c in enumerate(show_cols) if c not in show_cols[:i] and c in dataframe.columns]

    # ---- handle long-form (melted) data safely ----
    if not show_cols:
        # If dataframe has typical melted structure like ["Circle", "KPI", "Value"], just show all columns
        expected_long = {"kpi", "value"} <= set(map(str.lower, dataframe.columns))
        if expected_long:
            show_cols = list(dataframe.columns)
        else:
            st.warning("⚠️ No matching KPI columns found in this dataset.")
            return

    
    df_filtered = dataframe[show_cols].copy()

    # Convert numeric columns to int (no decimals)
    for col in df_filtered.select_dtypes(include=['float', 'int']).columns:
        # Only convert if all values are finite
        if df_filtered[col].notna().all():
            df_filtered[col] = df_filtered[col].astype(int)

    # --- 🧾 Display formatted & center-aligned table ---




    # --- 🧾 Display formatted, center-aligned, and sortable HTML table ---
    try:
        # Copy and format numbers for display (strings with commas)
        df_display = df_filtered.copy()
        for col in df_display.select_dtypes(include=['float', 'int']).columns:
            df_display[col] = df_display[col].apply(lambda x: f"{int(x):,}")

        # Create a unique table id
        
        table_id = f"table_{uuid.uuid4().hex[:8]}"

        # Convert dataframe to HTML (no index)
        html_table = df_display.to_html(index=False, border=0, justify='center')

        # Inject the id attribute into the first <table ...> occurrence
        # safe replace: insert id right after '<table'
        html_table = html_table.replace("<table", f'<table id="{table_id}"', 1)


        
        # Render the final HTML table
        # --- Render HTML safely inside a scrollable, sortable, fully styled container ---
        try:
            scroll_height = height  # default 400

            # ✅ Safe inline JavaScript sorter
            sort_js = f"""
            <script>
            function sortTable_{table_id}(tableId, colIndex) {{
                const table = document.getElementById(tableId);
                const tbody = table.querySelector("tbody");
                const rows = Array.from(tbody.querySelectorAll("tr"));
                const isAsc = table.getAttribute("data-sort-dir") !== "asc";
                rows.sort((a, b) => {{
                    const A = a.children[colIndex].innerText.trim();
                    const B = b.children[colIndex].innerText.trim();
                    const numA = parseFloat(A.replace(/,/g, ''));
                    const numB = parseFloat(B.replace(/,/g, ''));
                    if (!isNaN(numA) && !isNaN(numB)) return isAsc ? numA - numB : numB - numA;
                    return isAsc ? A.localeCompare(B) : B.localeCompare(A);
                }});
                rows.forEach(r => tbody.appendChild(r));
                table.setAttribute("data-sort-dir", isAsc ? "asc" : "desc");
            }}
            </script>
            """

            # ✅ Make headers clickable
            soup = BeautifulSoup(html_table, "html.parser")
            header = soup.find("thead")
            if header:
                for idx, th in enumerate(header.find_all("th")):
                    th["onclick"] = f"sortTable_{table_id}('{table_id}', {idx})"
                    th["style"] = "cursor:pointer; user-select:none;"
            html_table_sorted = str(soup)

            # ✅ Custom colour palette + styling INSIDE iframe
            css_styles = f"""
            <style>
            table#{table_id} {{
                width: 100%;
                border-collapse: collapse;
                text-align: center;
                font-family: 'Segoe UI', sans-serif;
                font-size: 0.9rem;
                border: 5px solid #d0d0d0;
            }}
            table#{table_id} th {{
                background-color: #0b67b2;       /* Deep green header */
                color: white;
                font-weight: 600;
                padding: 8px;
                text-transform: capitalize;
            }}
            table#{table_id} td {{
                padding: 6px;
                border: 1px solid #e1e1e1;
                text-align: center;
                color: #333;
            }}
            table#{table_id} tr:nth-child(even) {{
                background-color: #f6fdf8;       /* very light green tint */
            }}
            table#{table_id} tr:nth-child(odd) {{
                background-color: #ffffff;
            }}
            table#{table_id} tr:hover {{
                background-color: #e4f5eb;       /* soft hover highlight */
            }}
            th:hover {{
                background-color: #3fa76d;
            }}
            </style>
            """

            # ✅ Combine everything
            html_block = f"""
            {css_styles}
            {sort_js}
            <div style="
                max-height:{scroll_height}px;
                overflow-y:auto;
                border:1px solid #ccc;
                border-radius:8px;
                padding:4px;
                background-color:white;">
                {html_table_sorted}
            </div>
            """

            # ✅ Render inside isolated iframe
            st.components.v1.html(html_block, height=scroll_height + 15, scrolling=True)

        except Exception as e:
            st.warning(f"⚠️ HTML render failed ({e}) — displaying fallback table.")
            st.dataframe(df_display, use_container_width=True, height=height)

    except Exception:
        st.markdown("html table not working")
        # Fallback to Streamlit dataframe if something goes wrong
        st.dataframe(df_filtered, use_container_width=True, height=height)


    # --- Excel export ---
    st.markdown("---")

    towrite = BytesIO()
    df_filtered.to_excel(towrite, index=False, sheet_name='Data')
    towrite.seek(0)
    record_count = len(df_filtered)

    # --- Center-aligned download button ---
    # Create 3 equal columns and place the button in the center one
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        # The actual button
        st.download_button(
            label=f"⬇️ Download {record_count:,} records as Excel",
            data=towrite,
            file_name=f"{filename}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key=f"download_{filename}_{uuid.uuid4().hex[:6]}"
        )

# -----------------------------------------------
# DATA FETCH FUNCTION
# -----------------------------------------------
@st.cache_data(ttl=300)
def fetch_sheet(url: str) -> pd.DataFrame:
    if not url or "docs.google.com/spreadsheets" not in url:
        raise ValueError("Provide a valid Google Sheet URL.")
    m = re.search(r"/d/([a-zA-Z0-9-_]+)", url)
    if not m:
        raise ValueError("Could not parse Sheet ID from URL.")
    sheet_id = m.group(1)
    parsed = urllib.parse.urlparse(url)
    qs = urllib.parse.parse_qs(parsed.query)
    gid = qs.get("gid", ["0"])[0]
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    resp = requests.get(csv_url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(BytesIO(resp.content))
    if df.empty:
        raise ValueError("Fetched sheet is empty.")
    return df

# -----------------------------------------------
# DEFAULT GOOGLE SHEET URL
# -----------------------------------------------
DEFAULT_SHEET = "https://docs.google.com/spreadsheets/d/1c7eu8Ou20wbZhKHSat8tXI3saZleHxKyvWhylSUZxl0/edit?gid=276393470#gid=276393470"
sheet_url = st.session_state.get("sheet_url", DEFAULT_SHEET)

# -----------------------------------------------
# FETCH DATA
# -----------------------------------------------
try:
    df_raw = fetch_sheet(sheet_url)
except Exception as e:
    st.error(f"Failed to fetch Google Sheet: {e}")
    st.stop()

df_raw.columns = [c.strip() for c in df_raw.columns]
DATE_COL = "Date"
STATION_COL = "Thana"
CIRCLE_COL = next((c for c in df_raw.columns if "circle" in c.lower()), None)
df_raw[DATE_COL] = pd.to_datetime(df_raw[DATE_COL], errors="coerce")
df_raw["date"] = df_raw[DATE_COL].dt.date

# -----------------------------------------------
# MAIN TABS (WITH BIGGER HEADINGS)
# -----------------------------------------------
st.markdown("""
<style>
button[data-baseweb="tab"] div[data-testid="stMarkdownContainer"] p {
    font-size:15px !important;
    font-weight:700 !important;
    color:#0b67b2 !important;
    
}
</style>
""", unsafe_allow_html=True)

#tabs inside main section for selected KPI
# --- TAB INITIALIZATION AND TAB MEMORY MANAGEMENT ---
tabs = ["Overview", "Circle Insights", "Thana Insights", "Leaderboards", "Export & Pivot", "Time series Analytics", "money tab"]

# Initialize session variable to remember active tab
if "active_tab" not in st.session_state:
    st.session_state.active_tab = tabs[0]

# Define helper function to store current tab
def keep_tab(index: int):
    """Stores current active tab index in session state"""
    st.session_state.active_tab = tabs[index]

# Create the tab components
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(tabs)

# --- OVERVIEW ---
# ============================================================
# 📊 OVERVIEW TAB – Daily Data Submissions & Performance Charts
# ============================================================

with tab1:
    keep_tab(0)
    
    df = df_raw.copy()

    # ------------------------------
    # Load and Prepare Data
    # ------------------------------
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    today = pd.Timestamp.now().normalize()
    yesterday = today - pd.Timedelta(days=1)
    st.write(f"📅 Showing records from **{yesterday.strftime('%d %b %Y ')}**")
    # Filter yesterday’s data
    yesterday_data = df[df['date'] == yesterday]

    # List of all 23 Police Stations
    ps_list = sorted(df['Thana'].dropna().unique())

    # Define KPI set
    KPI_GROUPS_DAILY = {
        "NCRP new complaints Today",
        "NCRP new complaint above ₹5000",
        "Recomended for FIR Today",
        "Number of bank Account blocked Today",
        "Number of Mobile number for blocking Today",
        "Number of IMEI for blocking Today",
        "Total offline complaints received Today ( other than NCRP)",
        "Total offline complaints resolved Today ( other than NCRP)",
        "Number of mobiles entered in CEIR portal Today",
        "Number of mobiles traced Today",
        "Number of phones recovered Today",
        "Number of events received on Samanvyay portal Today",
        "Number of events closed on Samanvyay portal Today",
        "Number of events on Pratibimb portal Today",
        "Number of events closed on Pratibimb portal Today",
    }

    sub_tabs = st.tabs([
        "Thana wise Submission Status",  
        "Thana-wise KPI Chart (Stacked)",
        "Thana-wise KPI Chart (Overall)",
        "KPI wise chart daily",
        "KPI wise chart cumulative"
    ])

    # ============================================================
    # 🟩 Thana wise Submission Status
    # ============================================================
    with sub_tabs[0]:
        ps_col = 'Thana'
        submitted_ps = sorted(yesterday_data[ps_col].dropna().unique())
        all_ps = sorted(df[ps_col].dropna().unique())
        not_submitted_ps = [ps for ps in all_ps if ps not in submitted_ps]

        # --- CSS layout for equal-height columns ---
        st.markdown("""
            <style>
            .list-box {border: 1px solid #e6e6e6; border-radius: 6px; padding: 10px; height: 320px; overflow-y: auto; background: #fff;}
            .ps-item { margin: 6px 0; font-size:14px; }
            .ps-green { color: green; font-weight:600; }
            .ps-red { color: red; font-weight:600; }
            .box-title { font-weight:700; margin-bottom:8px; }
            </style>
        """, unsafe_allow_html=True)

        left, right = st.columns(2)

        with left:
            st.markdown('<div class="box-title">🟩 Submitted PS</div>', unsafe_allow_html=True)
            html_sub = '<div class="list-box">'
            for ps in submitted_ps:
                html_sub += f'<div class="ps-item ps-green">✅ {ps}</div>'
            if not submitted_ps:
                html_sub += '<div class="ps-item">— None —</div>'
            html_sub += '</div>'
            st.markdown(html_sub, unsafe_allow_html=True)
            submitted_df = pd.DataFrame({ps_col: submitted_ps})
            st.download_button(
                "⬇️ Download Submitted PS (CSV)",
                data=submitted_df.to_csv(index=False).encode('utf-8'),
                file_name="submitted_ps_yesterday.csv",
                mime="text/csv",
            )

        with right:
            st.markdown('<div class="box-title">🟥 Not Submitted PS</div>', unsafe_allow_html=True)
            html_not = '<div class="list-box">'
            for ps in not_submitted_ps:
                html_not += f'<div class="ps-item ps-red">❌ {ps}</div>'
            if not not_submitted_ps:
                html_not += '<div class="ps-item">— None —</div>'
            html_not += '</div>'
            st.markdown(html_not, unsafe_allow_html=True)
            not_submitted_df = pd.DataFrame({ps_col: not_submitted_ps})
            st.download_button(
                "⬇️ Download Not Submitted PS (CSV)",
                data=not_submitted_df.to_csv(index=False).encode('utf-8'),
                file_name="not_submitted_ps_yesterday.csv",
                mime="text/csv",
            )

        st.markdown("---")
        st.metric("Total PS Submitted Yesterday", f"{len(submitted_ps)} / {len(ps_list)}")

    # ============================================================
    # 📊 Thana-wise KPI Chart (Stacked)
    # ============================================================
    with sub_tabs[1]:
        ps_col = 'Thana' if 'Thana' in df.columns else 'PoliceStation'
        base_df = yesterday_data.copy()
        valid_kpis = [k for k in KPI_GROUPS_DAILY if k in base_df.columns]
        agg_data = base_df.groupby(ps_col)[valid_kpis].sum().reset_index()

        fig_thana = px.bar(
            agg_data, x=ps_col, y=valid_kpis, barmode="stack",
            title=f"{ps_col}-wise Daily KPI Submissions",
            labels={'value': 'Count', ps_col: 'Police Station'}
        )
        st.plotly_chart(fig_thana, use_container_width=True)

        # 🧾 Table display below chart
        display_table_with_download(
            dataframe=agg_data,
            filename="daily_thana_wise_kpi",
            title="Daily Thana-wise KPI Data",
            kpi_groups=KPI_GROUPS_DAILY
        )

    # ============================================================
    # 📈 Thana-wise KPI Chart (Cumulative)
    # ============================================================
    with sub_tabs[2]:
        ps_col = 'Thana' if 'Thana' in df.columns else 'PoliceStation'
        base_df = df.copy()
        valid_kpis = [k for k in KPI_GROUPS_DAILY if k in base_df.columns]
        agg_data = base_df.groupby(ps_col)[valid_kpis].sum().reset_index()

        fig_thana_cum = px.bar(
            agg_data, x=ps_col, y=valid_kpis, barmode="stack",
            title=f"{ps_col}-wise Cumulative KPI Submissions",
            labels={'value': 'Count', ps_col: 'Police Station'}
        )
        st.plotly_chart(fig_thana_cum, use_container_width=True)

        # 🧾 Table display below chart
        display_table_with_download(
            dataframe=agg_data,
            filename="cumulative_thana_wise_kpi",
            title="Cumulative Thana-wise KPI Data",
            kpi_groups=KPI_GROUPS_DAILY
        )

    # ============================================================
    # 📊 KPI-wise Chart (Daily)
    # ============================================================
    with sub_tabs[3]:
        base_df = yesterday_data.copy()
        valid_kpis = [k for k in KPI_GROUPS_DAILY if k in base_df.columns]
        kpi_totals = base_df[valid_kpis].sum().reset_index()
        kpi_totals.columns = ['KPI', 'Total Count']

        fig_kpi_daily = px.bar(
            kpi_totals, x='KPI', y='Total Count', text_auto=True,
            title="KPI-wise Daily Totals"
        )
        st.plotly_chart(fig_kpi_daily, use_container_width=True)

        # 🧾 Table display below chart
        display_table_with_download(
            dataframe=kpi_totals,
            filename="kpi_wise_daily",
            title="KPI-wise Daily Totals",
            kpi_groups=['KPI', 'Total Count']
        )

    # ============================================================
    # 📈 KPI-wise Chart (Cumulative)
    # ============================================================
    with sub_tabs[4]:
        base_df = df.copy()
        valid_kpis = [k for k in KPI_GROUPS_DAILY if k in base_df.columns]
        kpi_totals = base_df[valid_kpis].sum().reset_index()
        kpi_totals.columns = ['KPI', 'Total Count']

        fig_kpi_cum = px.bar(
            kpi_totals, x='KPI', y='Total Count', text_auto=True,
            title="KPI-wise Cumulative Totals"
        )
        st.plotly_chart(fig_kpi_cum, use_container_width=True)

        # 🧾 Table display below chart
        display_table_with_download(
            dataframe=kpi_totals,
            filename="kpi_wise_cumulative",
            title="KPI-wise Cumulative Totals",
            kpi_groups=['KPI', 'Total Count']
        )



# --- CIRCLE INSIGHTS ---
# --- CIRCLE INSIGHTS (Single Expand with Scroll + Glow) ---
# ---------- tab2: Circle Insights (stable, no JS) ----------
with tab2:
    keep_tab(1)
    
    # ----- DATE RANGE -----
    # ensure df_raw['date'] is datetime
    df_raw["date"] = pd.to_datetime(df_raw["date"], errors="coerce")
    min_date = df_raw["date"].min().date()
    max_date = df_raw["date"].max().date()

    date_range = st.date_input(
        "📅 Date Range",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="filter_dates_circle",
    )
    if isinstance(date_range, (tuple, list)):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    # convert to timestamps for safe comparison
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)  # include full end day

    df = df_raw[(df_raw["date"] >= start_dt) & (df_raw["date"] <= end_dt)].copy()

    # ----- KPI GROUPS (source) -----
    kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())

    # ----- initialize session state selections -----
    if "selected_kpi_group" not in st.session_state:
        st.session_state.selected_kpi_group = kpi_groups[0]
    if "selected_circle" not in st.session_state:
        st.session_state.selected_circle = None
    if "circle_view_type" not in st.session_state:
        st.session_state.circle_view_type = "Cumulative"

    
    # ----- KPI GROUP BUTTONS: render in rows that wrap -----
    # ----- KPI GROUP BUTTONS: render in rows that wrap -----
    per_row = 6  # number of buttons per row before wrap
    for start in range(0, len(kpi_groups), per_row):
        row = kpi_groups[start : start + per_row]
        cols = st.columns(len(row))
        for i, grp in enumerate(row):
            label = grp

            # --- active button color logic ---
            # store selected group in session state
            if "selected_kpi_group" not in st.session_state:
                st.session_state.selected_kpi_group = kpi_groups[0]

            is_active = (st.session_state.selected_kpi_group == grp)
            btn_key = f"kpi_btn_{grp}"

            # create a custom CSS marker using Markdown to mark the active button
            active_class = "active-button" if is_active else ""
            
            # render the button
            if cols[i].button(label, key=btn_key):
                st.session_state.selected_kpi_group = grp
                st.session_state.selected_circle = None

    
    # ----- prepare KPI numeric cols for selected group -----
    selected_group = st.session_state.selected_kpi_group
    selected_kpis = [c for c in KPI_GROUPS_NO_MONEY[selected_group] if c in df.columns]
    if not selected_kpis:
        st.warning(f"No KPI columns present for group '{selected_group}'.")
        st.stop()

    for k in selected_kpis:
        df[k + "_num"] = pd.to_numeric(df[k], errors="coerce").fillna(0)

    # ----- Toggle view type (Cumulative or Breakup) -----
    view_type = st.radio("View Type", ["Cumulative", "KPI-wise Breakup"], index=0, horizontal=True)
    st.session_state.circle_view_type = view_type

    # ----- Circle-level aggregation -----
    if CIRCLE_COL is None or CIRCLE_COL not in df.columns:
        st.info("No Circle column found in the dataset.")
    else:
        agg_cols = [k + "_num" for k in selected_kpis]
        circle_group_df = df.groupby(CIRCLE_COL)[agg_cols].sum().reset_index()
        circle_group_df["Group Total"] = circle_group_df[agg_cols].sum(axis=1)

        if view_type == "Cumulative":
            fig = px.bar(
                circle_group_df,
                x=CIRCLE_COL,
                y="Group Total",
                text_auto=True,
                title=f"Cumulative total by Circle — {selected_group}"
            )
            fig.update_layout(showlegend=False, height=450)
            st.plotly_chart(fig, use_container_width=True)

            display_table_with_download(circle_group_df, "leaderboard_table", "Leaderboard overall Data", kpi_groups=[CIRCLE_COL,"Group Total"])

        else:
            melt = circle_group_df.melt(id_vars=[CIRCLE_COL], value_vars=agg_cols, var_name="KPI", value_name="Value")
            melt["KPI"] = melt["KPI"].str.replace("_num", "", regex=False)
            fig = px.bar(melt, x=CIRCLE_COL, y="Value", color="KPI", barmode="stack",
                         title=f"KPI-wise breakdown by Circle — {selected_group}")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
            #display the data table
            # --- Convert melted data back to wide format for display ---
            wide_table = melt.pivot(index=CIRCLE_COL, columns="KPI", values="Value").reset_index()

            # Add total column
            wide_table["Total"] = wide_table.select_dtypes(include=["number"]).sum(axis=1)

            # Display table with formatted columns
            display_table_with_download(
                dataframe=wide_table,
                filename="circle_kpi_breakdown_wide",
                title=f"Circle-wise KPI Breakdown — {selected_group}",
                kpi_groups=list(wide_table.columns)  # show all columns dynamically
            )

        # ----- Circle buttons (row(s) that wrap) -----
        st.markdown("### 🏢 Select Circle (for Thana drilldown)")
        circle_names = sorted(circle_group_df[CIRCLE_COL].dropna().unique())

        per_row_circle = 6
        for start in range(0, len(circle_names), per_row_circle):
            row = circle_names[start : start + per_row_circle]
            cols = st.columns(len(row))
            for i, cname in enumerate(row):
                label = cname
                if st.session_state.selected_circle == cname:
                    label = f"✅ {cname}"
                if cols[i].button(label, key=f"circle_btn_{cname}"):
                    st.session_state.selected_circle = cname

        # ----- Thana-level details for selected circle -----
        if st.session_state.selected_circle:
            sel = st.session_state.selected_circle
            st.markdown(f"### 🔍 Thana-level — {sel} (Group: {selected_group})")

            df_th = df[df[CIRCLE_COL] == sel]
            if STATION_COL not in df_th.columns:
                st.warning("Station (Thana) column not present.")
            else:
                thana_agg = df_th.groupby(STATION_COL)[agg_cols].sum().reset_index()
                thana_agg["Total"] = thana_agg[agg_cols].sum(axis=1)

                if view_type == "Cumulative":
                    fig_th = px.bar(thana_agg, x=STATION_COL, y="Total", text_auto=True,
                                    title=f"Cumulative Thana totals — {sel}")
                    fig_th.update_layout(showlegend=False, height=420)
                    st.plotly_chart(fig_th, use_container_width=True)

                    display_table_with_download(thana_agg, "leaderboard_table", "Leaderboard overall Data", kpi_groups=[STATION_COL,"Total"])
                else:
                    th_melt = thana_agg.melt(id_vars=[STATION_COL], value_vars=agg_cols, var_name="KPI", value_name="Value")
                    th_melt["KPI"] = th_melt["KPI"].str.replace("_num", "", regex=False)
                    fig_th = px.bar(th_melt, x=STATION_COL, y="Value", color="KPI", barmode="stack",
                                    title=f"KPI-wise breakup by Thana — {sel}")
                    fig_th.update_layout(height=480)
                    st.plotly_chart(fig_th, use_container_width=True)

                    #display the data table
                    # --- Convert melted data back to wide format for display ---
                    wide_table_th = th_melt.pivot(index=STATION_COL, columns="KPI", values="Value").reset_index()

                    # Add total column
                    wide_table_th["Total"] = wide_table_th.select_dtypes(include=["number"]).sum(axis=1)

                    # Display table with formatted columns
                    display_table_with_download(
                        dataframe=wide_table_th,
                        filename="circle_kpi_breakdown_wide",
                        title=f"For {sel} Circle-Thana wise KPI Breakdown — {selected_group}",
                        kpi_groups=list(wide_table_th.columns)  # show all columns dynamically
                    )

# --- thana wise insight ----
# --- THANA INSIGHTS (Global, Filter-based) ---
with tab3:
    keep_tab(2)

    # ----- DATE RANGE -----
    df_raw["date"] = pd.to_datetime(df_raw["date"], errors="coerce")
    min_date = df_raw["date"].min().date()
    max_date = df_raw["date"].max().date()

    date_range = st.date_input(
        "📅 Date Range",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="filter_dates_thana",
    )
    if isinstance(date_range, (tuple, list)):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    # convert safely
    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df = df_raw[(df_raw["date"] >= start_dt) & (df_raw["date"] <= end_dt)].copy()

    # ----- KPI GROUPS -----
    kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())

    # ----- initialize session state selections -----
    if "selected_kpi_group_thana" not in st.session_state:
        st.session_state.selected_kpi_group_thana = kpi_groups[0]
    if "thana_view_type" not in st.session_state:
        st.session_state.thana_view_type = "Cumulative"

    # ----- KPI GROUP BUTTONS: render in rows that wrap -----
    per_row = 6
    for start in range(0, len(kpi_groups), per_row):
        row = kpi_groups[start : start + per_row]
        cols = st.columns(len(row))
        for i, grp in enumerate(row):
            label = grp
            if cols[i].button(label, key=f"kpi_btn_thana_{grp}"):
                st.session_state.selected_kpi_group_thana = grp

    selected_group = st.session_state.selected_kpi_group_thana
    
    # ----- Prepare KPI numeric cols -----
    selected_kpis = [c for c in KPI_GROUPS_NO_MONEY[selected_group] if c in df.columns]
    if not selected_kpis:
        st.warning(f"No KPI columns present for group '{selected_group}'.")
        st.stop()

    for k in selected_kpis:
        df[k + "_num"] = pd.to_numeric(df[k], errors="coerce").fillna(0)

    # ----- Toggle view type -----
    view_type = st.radio("View Type", ["Cumulative_", "KPI-wise Breakup_"], index=0, horizontal=True)
    st.session_state.thana_view_type = view_type

    # ----- Thana-level aggregation -----
    if STATION_COL is None or STATION_COL not in df.columns:
        st.info("No Thana (Police Station) column found in the dataset.")
    else:
        agg_cols = [k + "_num" for k in selected_kpis]
        thana_group_df = df.groupby(STATION_COL)[agg_cols].sum().reset_index()
        thana_group_df["Group Total"] = thana_group_df[agg_cols].sum(axis=1)

        if view_type == "Cumulative_":
            fig = px.bar(
                thana_group_df,
                x=STATION_COL,
                y="Group Total",
                text_auto=True,
                title=f"Cumulative total by Thana — {selected_group}",
            )
            fig.update_layout(showlegend=False, height=450)
            st.plotly_chart(fig, use_container_width=True)

            display_table_with_download(thana_group_df, "leaderboard_table thana wise", "Leaderboard overall Data ", kpi_groups=[STATION_COL,"Group Total"]), 

        else:
            melt = thana_group_df.melt(id_vars=[STATION_COL], value_vars=agg_cols, var_name="KPI", value_name="Value")
            melt["KPI"] = melt["KPI"].str.replace("_num", "", regex=False)
            fig = px.bar(
                melt,
                x=STATION_COL,
                y="Value",
                color="KPI",
                barmode="stack",
                title=f"KPI-wise breakdown by Thana — {selected_group}",
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            #display the data table
            # --- Convert melted data back to wide format for display ---
            wide_table_th = melt.pivot(index=STATION_COL, columns="KPI", values="Value").reset_index()

            # Add total column
            wide_table_th["Total"] = wide_table_th.select_dtypes(include=["number"]).sum(axis=1)

            # Display table with formatted columns
            display_table_with_download(
                dataframe=wide_table_th,
                filename="circle_kpi_breakdown_wide",
                title=f"Thana wise KPI Breakdown — {selected_group}",
                kpi_groups=list(wide_table_th.columns)  # show all columns dynamically
            )


# --- LEADERBOARDS ---
with tab4:
    keep_tab(3)
    
    # ----- DATE RANGE -----
    df_raw["date"] = pd.to_datetime(df_raw["date"], errors="coerce")
    min_date = df_raw["date"].min().date()
    max_date = df_raw["date"].max().date()

    date_range = st.date_input(
        "📅 Date Range",
        (min_date, max_date),
        min_value=min_date,
        max_value=max_date,
        key="filter_dates_leaderboard",
    )
    if isinstance(date_range, (tuple, list)):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range

    start_dt = pd.to_datetime(start_date)
    end_dt = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    df = df_raw[(df_raw["date"] >= start_dt) & (df_raw["date"] <= end_dt)].copy()

    # ----- Check for Thana Column -----
    if STATION_COL not in df.columns:
        st.warning("No 'Thana' column found in the dataset.")
        st.stop()
    #show KPI selector buttons in to ribbon    
    def show_KPI_buttons():
        # ----- KPI GROUPS -----
        kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())

        if "selected_kpi_group_lb" not in st.session_state:
            st.session_state.selected_kpi_group_lb = kpi_groups[0]
        if "leaderboard_view_type" not in st.session_state:
            st.session_state.leaderboard_view_type = "Overall"

        # ----- KPI GROUP BUTTONS (wrap layout) -----
        per_row = 6
        for start in range(0, len(kpi_groups), per_row):
            row = kpi_groups[start : start + per_row]
            cols = st.columns(len(row))
            for i, grp in enumerate(row):
                label = grp
                if cols[i].button(label, key=f"kpi_btn_lb_{grp}"):
                    st.session_state.selected_kpi_group_lb = grp

        selected_group = st.session_state.selected_kpi_group_lb
        selected_kpis = [c for c in KPI_GROUPS_NO_MONEY[selected_group] if c in df.columns]

        for k in selected_kpis:
            df[k + "_num"] = pd.to_numeric(df[k], errors="coerce").fillna(0)

        return selected_kpis


    # ----- Toggle leaderboard type -----
    view_type = st.radio(
        "Leaderboard Type",
        ["Overall", "KPI Group-wise", "KPI Breakup"],
        horizontal=True,
        key="leaderboard_view_type",
    )
    
    # ----- 1️⃣ OVERALL LEADERBOARD -----
    if view_type == "Overall":
    
        # sum all KPI columns across all groups
        all_kpis = []
        for gcols in KPI_GROUPS_NO_MONEY.values():
            all_kpis.extend([c for c in gcols if c in df.columns])

        for k in all_kpis:
            df[k + "_num"] = pd.to_numeric(df[k], errors="coerce").fillna(0)

        df["Overall_Total"] = df[[k + "_num" for k in all_kpis]].sum(axis=1)
        overall_df = df.groupby(STATION_COL)["Overall_Total"].sum().reset_index().sort_values("Overall_Total", ascending=False)

        fig_overall = px.bar(
            overall_df,
            x="Overall_Total",
            y=STATION_COL,
            orientation="h",
            color="Overall_Total",
            color_continuous_scale="blues",
            title="Overall Leaderboard (All KPI Groups Combined)",
        )
        fig_overall.update_layout(height=600)
        st.plotly_chart(fig_overall, use_container_width=True)

        # Display table with formatted columns
        display_table_with_download(
            dataframe=overall_df,
            filename="circle_kpi_breakdown_wide",
            title=f"Thana wise Total ",
            kpi_groups=[STATION_COL,"Overall_Total"]  # show all columns dynamically
        )

   

    # ----- 2️⃣ KPI GROUP-WISE LEADERBOARD -----
    elif view_type == "KPI Group-wise":
        selected_kpis = show_KPI_buttons()
        agg_cols = [k + "_num" for k in selected_kpis]
        df["Group_Total"] = df[agg_cols].sum(axis=1)

        group_df = df.groupby(STATION_COL)["Group_Total"].sum().reset_index().sort_values("Group_Total", ascending=False)

        fig_group = px.bar(
            group_df,
            x="Group_Total",
            y=STATION_COL,
            orientation="h",
            color="Group_Total",
            color_continuous_scale="Blues",
            title=f"Leaderboard — {selected_group} (Cumulative)",
        )
        fig_group.update_layout(height=600)
        st.plotly_chart(fig_group, use_container_width=True)

        # Display table with formatted columns
        display_table_with_download(
            dataframe=group_df,
            filename="circle_kpi_breakdown_wide",
            title=f"KPI group wise Total ",
            kpi_groups=[STATION_COL,"Group_Total"]  # show all columns dynamically
        )




    # ----- 3️⃣ KPI BREAKUP LEADERBOARD -----
    elif view_type == "KPI Breakup":
    
        selected_kpis = show_KPI_buttons()

        for k in selected_kpis:
            st.markdown(f"#### 📍 {k}")
            lb = (
                df.groupby(STATION_COL)[k + "_num"]
                .sum()
                .reset_index()
                .sort_values(k + "_num", ascending=False)
            )

            fig_lb = px.bar(
                lb,
                x=k + "_num",
                y=STATION_COL,
                orientation="h",
                color=k + "_num",
                color_continuous_scale="Blues",
                title=f"Leaderboard — {k}",
            )
            fig_lb.update_layout(height=450)
            st.plotly_chart(fig_lb, use_container_width=True)

            # Display table with formatted columns
            display_table_with_download(
                dataframe=lb,
                filename="circle_kpi_breakdown_wide",
                title=f"KPI breakup  Total ",
                kpi_groups=[STATION_COL,k + "_num"]  # show all columns dynamically
            )

  

# --- EXPORT & PIVOT ---
with tab5:
    keep_tab(4)
    st.markdown("<h2 style='color:#0b67b2;'>Export & Pivot</h2>", unsafe_allow_html=True)
    pivot = df.pivot_table(index="date", columns=STATION_COL if STATION_COL in df.columns else None,
                           values=[k + "_num" for k in selected_kpis], aggfunc="sum", fill_value=0)
    st.dataframe(pivot, use_container_width=True)
    st.download_button("Download Pivot CSV. ", pivot.to_csv().encode("utf-8"), "cybercell_pivot.csv", "text/csv")

    

#time series analytics
with tab6:
    keep_tab(5)
    
    # ======================================
    # PREP DATA
    # ======================================
    df_raw["date"] = pd.to_datetime(df_raw["date"], errors="coerce")
    df = df_raw.copy()

    # detect columns
    thana_col = STATION_COL
    circle_col = CIRCLE_COL
    date_col = "date"

    # ensure numeric conversions
    for group, cols in KPI_GROUPS_NO_MONEY.items():
        for c in cols:
            if c in df.columns:
                df[c + "_num"] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    # ======================================
    # 4 SUB-TABS
    # ======================================
    sub1, sub2, sub3, sub4 = st.tabs([
        "🏢 Selected Thana",
        "🚓 All Thanas",
        "🟦 All Circles",
        "📊 Overall Trends"
    ])

    # ======================================
    # 1️⃣ SELECTED THANA
    # ======================================
    with sub1:
        
        if thana_col not in df.columns:
            st.warning("No Thana column found.")
        else:
            selected_thana = st.selectbox("Select Thana", sorted(df[thana_col].dropna().unique()), key="ts_thana_select")

            thana_df = df[df[thana_col] == selected_thana]
            # Keep only numeric columns for summation
            numeric_cols = thana_df.select_dtypes(include=["number"]).columns
            thana_df = thana_df.groupby(date_col)[numeric_cols].sum().reset_index()

            # KPI group buttons + "All"
            kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())
            group_cols = st.columns(len(kpi_groups) + 1)
            selected_group = st.session_state.get("ts_thana_kpi_group", "All")

            if group_cols[0].button("All", key="ts_thana_all"):
                selected_group = "All"
                st.session_state.ts_thana_kpi_group = "All"

            for i, grp in enumerate(kpi_groups):
                if group_cols[i + 1].button(grp, key=f"ts_thana_{grp}"):
                    selected_group = grp
                    st.session_state.ts_thana_kpi_group = grp

            # Prepare data
            if selected_group == "All":
                all_kpis = []
                for cols in KPI_GROUPS_NO_MONEY.values():
                    all_kpis.extend([c + "_num" for c in cols if c + "_num" in thana_df.columns])
                thana_df["Total"] = thana_df[all_kpis].sum(axis=1)
                fig = px.line(thana_df, x=date_col, y="Total", markers=True, title=f"{selected_thana} — Overall Performance Over Time")
            else:
                selected_kpis = [c + "_num" for c in KPI_GROUPS_NO_MONEY[selected_group] if c + "_num" in thana_df.columns]
                thana_df["Group_Total"] = thana_df[selected_kpis].sum(axis=1)
                fig = px.line(thana_df, x=date_col, y=selected_kpis, markers=True,
                              title=f"{selected_thana} — {selected_group} Performance Over Time")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            display_table_with_download(thana_df, "daily_thana_wise_time_series", "Daily Thana-wise Data")


    # ======================================
    # 2️⃣ ALL THANAS
    # ======================================
    with sub2:
      
        if thana_col not in df.columns:
            st.warning("No Thana column found.")
        else:
            # KPI group buttons
            kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())
            group_cols = st.columns(len(kpi_groups) + 1)
            selected_group = st.session_state.get("ts_allthana_kpi_group", "All")

            if group_cols[0].button("All", key="ts_allthana_all"):
                selected_group = "All"
                st.session_state.ts_allthana_kpi_group = "All"

            for i, grp in enumerate(kpi_groups):
                if group_cols[i + 1].button(grp, key=f"ts_allthana_{grp}"):
                    selected_group = grp
                    st.session_state.ts_allthana_kpi_group = grp

            # Aggregate data
            agg_dict = {}
            if selected_group == "All":
                for cols in KPI_GROUPS_NO_MONEY.values():
                    for c in cols:
                        if c + "_num" in df.columns:
                            agg_dict[c + "_num"] = "sum"
            else:
                for c in KPI_GROUPS_NO_MONEY[selected_group]:
                    if c + "_num" in df.columns:
                        agg_dict[c + "_num"] = "sum"

            df_sum = df.groupby([date_col, thana_col]).agg(agg_dict).reset_index()
            df_sum["Total"] = df_sum.drop(columns=[date_col, thana_col]).sum(axis=1)

            fig = px.line(df_sum, x=date_col, y="Total", color=thana_col,
                          markers=True, title=f"All Thanas — {selected_group} Trend Over Time")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            display_table_with_download(df_sum, "overall_thana_wise_time_series", "Daily overall-wise Data")


    # ======================================
    # 3️⃣ ALL CIRCLES
    # ======================================
    with sub3:
    
        if circle_col not in df.columns:
            st.warning("No Circle column found.")
        else:
            # KPI group buttons
            kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())
            group_cols = st.columns(len(kpi_groups) + 1)
            selected_group = st.session_state.get("ts_circle_kpi_group", "All")

            if group_cols[0].button("All", key="ts_circle_all"):
                selected_group = "All"
                st.session_state.ts_circle_kpi_group = "All"

            for i, grp in enumerate(kpi_groups):
                if group_cols[i + 1].button(grp, key=f"ts_circle_{grp}"):
                    selected_group = grp
                    st.session_state.ts_circle_kpi_group = grp

            # Aggregate data
            agg_dict = {}
            if selected_group == "All":
                for cols in KPI_GROUPS_NO_MONEY.values():
                    for c in cols:
                        if c + "_num" in df.columns:
                            agg_dict[c + "_num"] = "sum"
            else:
                for c in KPI_GROUPS_NO_MONEY[selected_group]:
                    if c + "_num" in df.columns:
                        agg_dict[c + "_num"] = "sum"

            df_sum = df.groupby([date_col, circle_col]).agg(agg_dict).reset_index()
            df_sum["Total"] = df_sum.drop(columns=[date_col, circle_col]).sum(axis=1)

            fig = px.line(df_sum, x=date_col, y="Total", color=circle_col,
                          markers=True, title=f"All Circles — {selected_group} Trend Over Time")
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)

            display_table_with_download(df_sum, "overall_circle_wise_time_series", "Daily overall circle-wise Data")


    # ======================================
    # 4️⃣ OVERALL TIME-SERIES
    # ======================================
    with sub4:
    
        # KPI group buttons
        kpi_groups = list(KPI_GROUPS_NO_MONEY.keys())
        group_cols = st.columns(len(kpi_groups) + 1)
        selected_group = st.session_state.get("ts_overall_kpi_group", "All")

        if group_cols[0].button("All", key="ts_overall_all"):
            selected_group = "All"
            st.session_state.ts_overall_kpi_group = "All"

        for i, grp in enumerate(kpi_groups):
            if group_cols[i + 1].button(grp, key=f"ts_overall_{grp}"):
                selected_group = grp
                st.session_state.ts_overall_kpi_group = grp

        if selected_group == "All":
            all_kpis = []
            for cols in KPI_GROUPS_NO_MONEY.values():
                all_kpis.extend([c + "_num" for c in cols if c + "_num" in df.columns])
            df["Total"] = df[all_kpis].sum(axis=1)
            overall_df = df.groupby(date_col)["Total"].sum().reset_index()
            fig = px.line(overall_df, x=date_col, y="Total", markers=True, title="Overall Performance Over Time")
        
            display_table_with_download(overall_df, "Overall Performance Over Time", "Overall Performance Over Time")
        
        else:
            selected_kpis = [c + "_num" for c in KPI_GROUPS_NO_MONEY[selected_group] if c + "_num" in df.columns]
            df["Group_Total"] = df[selected_kpis].sum(axis=1)
            group_df = df.groupby(date_col)[["Group_Total"] + selected_kpis].sum().reset_index()
            fig = px.line(group_df, x=date_col, y="Group_Total", markers=True, title=f"{selected_group} — Cumulative Over Time")

            display_table_with_download(group_df, f"{selected_group} — Cumulative Over Time", f"{selected_group} — Cumulative Over Time")

        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)



#money tab
# ============================================================
# 💰 MONEY TAB – Financial Metrics Dashboard
# ============================================================

with tab7:  # or use st.tab("💰 Money") if you use st.tabs() pattern
    keep_tab(6)
    
    # Detect PS column
    ps_col = 'Thana' if 'Thana' in df.columns else 'PoliceStation'

    # Define target columns (rename safely if needed)
    col_lost = "Total amout lost ( in new complaints)"
    col_hold = "Total amout put on hold  Today"
    col_released = "Money returned to victim  Today"

    # Ensure date column is datetime
    df['date'] = pd.to_datetime(df['date'], errors='coerce')

    # Tabs for four money visualizations
    money_subtabs = st.tabs([
        "📆 Daily Thana-wise",
        "📊 Cumulative Thana-wise",
        "📈 Time Series (Thana-wise)",
        "📉 Time Series (Cumulative)"
    ])

    # ============================================================
    # 1️⃣ DAILY THANA-WISE
    # ============================================================
    with money_subtabs[0]:
    
        # Yesterday's data
        today = pd.Timestamp.now().normalize()
        yesterday = today - pd.Timedelta(days=1)
        daily_df = df[df['date'] == yesterday].copy()

        # Keep only Thanas with at least one non-zero amount
        filtered = daily_df[
            (daily_df[[col_lost, col_hold, col_released]].fillna(0).sum(axis=1)) > 0
        ]

        if not filtered.empty:
            fig_daily = px.bar(
                filtered,
                x=ps_col,
                y=[col_lost, col_hold, col_released],
                barmode='group',
                title=f"Daily Thana-wise – {yesterday.strftime('%d-%b-%Y')}",
                labels={'value': 'Amount (₹)', ps_col: 'Police Station'}
            )
            st.plotly_chart(fig_daily, use_container_width=True)
        else:
            st.info("No daily financial data available for yesterday.")

        display_table_with_download(filtered, "daily_thana_wise_money", "Daily Thana-wise Data")


    # ============================================================
    # 2️⃣ CUMULATIVE THANA-WISE
    # ============================================================
    with money_subtabs[1]:
    
        cumulative_df = (
            df.groupby(ps_col)[[col_lost, col_hold, col_released]]
            .sum()
            .reset_index()
        )
        # Filter out 0 rows
        cumulative_df = cumulative_df[
            (cumulative_df[[col_lost, col_hold, col_released]].fillna(0).sum(axis=1)) > 0
        ]

        if not cumulative_df.empty:
            fig_cum = px.bar(
                cumulative_df,
                x=ps_col,
                y=[col_lost, col_hold, col_released],
                barmode='group',
                title="Cumulative Thana-wise Financial Overview",
                labels={'value': 'Amount (₹)', ps_col: 'Police Station'}
            )
            st.plotly_chart(fig_cum, use_container_width=True)
        else:
            st.info("No cumulative financial data available.")

        display_table_with_download(cumulative_df, "cumilative_thana_wise_money", "Cumulative Thana-wise Data")


    # ============================================================
    # 3️⃣ TIME SERIES (THANA-WISE)
    # ============================================================
    with money_subtabs[2]:
    
        available_thanas = sorted(df[ps_col].dropna().unique())
        selected_thana = st.selectbox("Select Thana:", available_thanas)

        thana_ts = (
            df[df[ps_col] == selected_thana]
            .groupby('date')[[col_lost, col_hold, col_released]]
            .sum()
            .reset_index()
        )

        if not thana_ts.empty:
            fig_thana_ts = px.line(
                thana_ts,
                x='date',
                y=[col_lost, col_hold, col_released],
                markers=True,
                title=f"Daily Financial Trend – {selected_thana}",
                labels={'value': 'Amount (₹)', 'date': 'Date'}
            )
            st.plotly_chart(fig_thana_ts, use_container_width=True)
        else:
            st.info(f"No time series data available for {selected_thana}.")

        display_table_with_download(thana_ts, "date_wise_thana_wise_money", "Date wise Thana-wise Data")


    # ============================================================
    # 4️⃣ TIME SERIES (CUMULATIVE DAILY TOTALS)
    # ============================================================
    with money_subtabs[3]:
    
        daily_totals = (
            df.groupby('date')[[col_lost, col_hold, col_released]]
            .sum()
            .reset_index()
            .sort_values('date')
        )

        if not daily_totals.empty:
            fig_total_ts = px.line(
                daily_totals,
                x='date',
                y=[col_lost, col_hold, col_released],
                markers=True,
                title="Cumulative Daily Financial Overview (All Thanas)",
                labels={'value': 'Amount (₹)', 'date': 'Date'}
            )
            st.plotly_chart(fig_total_ts, use_container_width=True)
        else:
            st.info("No cumulative time series financial data available.")

        display_table_with_download(daily_totals, "date_wise_money", "Date wise money KPI Data")

# -----------------------------------------------
# GOOGLE SHEET LINK AT BOTTOM
# -----------------------------------------------
st.markdown("---")

st.markdown("#### Google Sheet Link")
sheet_input = sheet_url
# --- Center-aligned download button ---
# Create 3 equal columns and place the button in the center one
c1, c2, c3 = st.columns([1, 1, 1])
with c2:
    # The actual button
    if st.button("Fetch / Refresh Data"):
        st.session_state.sheet_url = sheet_input.strip()
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# Footer
st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
st.markdown("<div class='footer'>© Cyber Cell Shahjahanpur · Data Intelligence Dashboard</div>", unsafe_allow_html=True)
st.markdown("---")
