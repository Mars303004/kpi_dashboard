import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import os

# ================== PAGE CONFIG ==================
st.set_page_config(layout="wide", page_title="Performance Dashboard")

# ================== TAB SELECTION ==================
tabs = st.tabs(["KPI Dashboard", "Strategic Initiatives"])

# ================== TAB 1: KPI DASHBOARD ==================
with tabs[0]:
    file_path = "Dashboard 7.csv"
    df = pd.read_csv(file_path)

    required_cols = ['Perspective', 'Kode KPI', 'KPI', 'Target Tahunan', 'Measurement Type',
                     'Target Jan', 'Actual Jan', 'Achv Jan', 'Target Feb', 'Actual Feb', 'Achv Feb']
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Kolom '{col}' tidak ditemukan di data.")
            st.stop()

    df['Achv Feb Num'] = pd.to_numeric(df['Achv Feb'].str.replace('%','').str.replace(',','.'), errors='coerce')

    def get_status(achv):
        if pd.isna(achv):
            return 'Hitam'
        elif achv < 70:
            return 'Merah'
        elif 70 <= achv <= 99:
            return 'Kuning'
        else:
            return 'Hijau'
    df['Status'] = df['Achv Feb Num'].apply(get_status)

    COLOR_RED = "#b42020"
    COLOR_BLUE = "#0f098e"
    COLOR_WHITE = "#ffffff"
    COLOR_GREEN = "#1bb934"
    COLOR_YELLOW = "#ffe600"
    COLOR_BLACK = "#222222"

    status_color_map = {
        "Merah": COLOR_RED,
        "Kuning": COLOR_YELLOW,
        "Hijau": COLOR_GREEN,
        "Hitam": COLOR_BLACK
    }
    status_order = ['Hitam', 'Hijau', 'Kuning', 'Merah']

    def get_status_counts(data):
        return {
            "Merah": (data['Status'] == "Merah").sum(),
            "Kuning": (data['Status'] == "Kuning").sum(),
            "Hijau": (data['Status'] == "Hijau").sum(),
            "Hitam": (data['Status'] == "Hitam").sum()
        }

    global_counts = get_status_counts(df)
    fig_global = go.Figure()
    for status in status_order:
        fig_global.add_trace(go.Bar(
            x=[status],
            y=[global_counts[status]],
            name=status,
            marker_color=status_color_map[status],
            text=[global_counts[status]],
            textposition='auto'
        ))

    fig_global.update_layout(
        title="Total KPI Status (Global)",
        yaxis_title="Jumlah KPI",
        xaxis_title="Status",
        barmode='stack',
        plot_bgcolor=COLOR_WHITE,
        paper_bgcolor=COLOR_WHITE,
        font=dict(color=COLOR_BLUE, size=16),
        margin=dict(l=20, r=20, t=40, b=20),
        height=350
    )

    perspectives = df['Perspective'].dropna().unique().tolist()
    perspective_counts = {p: get_status_counts(df[df['Perspective'] == p]) for p in perspectives}
    fig_persp = go.Figure()
    for status in status_order:
        fig_persp.add_trace(go.Bar(
            x=perspectives,
            y=[perspective_counts[p][status] for p in perspectives],
            name=status,
            marker_color=status_color_map[status],
            text=[perspective_counts[p][status] for p in perspectives],
            textposition='auto'
        ))

    fig_persp.update_layout(
        barmode='stack',
        title="KPI Status per Perspective",
        yaxis_title="Jumlah KPI",
        xaxis_title="Perspective",
        plot_bgcolor=COLOR_WHITE,
        paper_bgcolor=COLOR_WHITE,
        font=dict(color=COLOR_BLUE, size=16),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(fig_global, use_container_width=True)
    with col2:
        st.plotly_chart(fig_persp, use_container_width=True)

    st.markdown("<h3 style='color:#b42020;'>Filter Perspective (klik salah satu):</h3>", unsafe_allow_html=True)

    cols = st.columns(2)
    if 'selected_persp' not in st.session_state:
        st.session_state.selected_persp = perspectives[0]
    def select_persp(p):
        st.session_state.selected_persp = p
    for i, p in enumerate(perspectives):
        col = cols[i % 2]
        is_selected = (st.session_state.selected_persp == p)
        btn_label = f"✔ {p}" if is_selected else p
        if col.button(btn_label, key=p, on_click=select_persp, args=(p,)):
            pass

    selected_perspective = st.session_state.selected_persp
    filtered_df = df[df['Perspective'] == selected_perspective]

    st.markdown(f"<h3 style='color:#b42020;'>Daftar KPI untuk Perspective: {selected_perspective}</h3>", unsafe_allow_html=True)
    def style_row(row):
        color = status_color_map.get(row['Status'], '#ffffff')
        font_color = 'white' if row['Status'] in ['Merah', 'Hijau', 'Hitam'] else 'black'
        return [f'background-color: {color}; color: {font_color};'] * len(row)

    display_cols = ['Kode KPI', 'KPI', 'Target Tahunan', 'Actual Jan', 'Target Feb', 'Actual Feb', 'Measurement Type', 'Status']
    table_df = filtered_df[display_cols].copy()
    st.dataframe(table_df.style.apply(style_row, axis=1), use_container_width=True)

    st.markdown("<h3 style='color:#b42020;'>Pilih KPI untuk lihat detail chart:</h3>", unsafe_allow_html=True)
    selected_kpi_code = None
    cols_per_row = 4
    for i in range(0, len(table_df), cols_per_row):
        cols_buttons = st.columns(cols_per_row)
        for j, row in enumerate(table_df.iloc[i:i+cols_per_row].itertuples()):
            if cols_buttons[j].button(f"Show Chart {row[1]}", key=f"btn_{row[1]}"):
                selected_kpi_code = row[1]

    if selected_kpi_code:
        kpi_row = filtered_df[filtered_df['Kode KPI'] == selected_kpi_code].iloc[0]
        actual_feb = kpi_row['Actual Feb']
        if pd.isna(actual_feb) or str(actual_feb).strip().upper() == 'NA':
            st.info("Belum ada data yang tersedia untuk KPI ini.")
        else:
            target_tahunan = kpi_row['Target Tahunan']
            x_data = [col for col in df.columns if col.startswith('Actual')]
            y_data = kpi_row[x_data].values.tolist()
            x_clean = [col.replace('Actual ', '') for col in x_data]

            fig_detail = go.Figure()
            if kpi_row.get('YTD Achievement Type', '') == 'SUM':
                target_feb = kpi_row['Target Feb']
                if pd.notna(target_feb):
                    fig_detail.add_trace(go.Scatter(
                        x=x_clean, y=[target_feb] * len(x_clean),
                        mode='lines', name='Target Feb',
                        line=dict(color='yellow', dash='dash')
                    ))

            fig_detail.add_trace(go.Scatter(
                x=x_clean, y=[target_tahunan] * len(x_clean),
                mode='lines', name='Target Tahunan',
                line=dict(color='green', dash='dash')
            ))
            fig_detail.add_trace(go.Scatter(
                x=x_clean, y=y_data,
                mode='lines+markers', name='Kinerja Bulanan',
                line=dict(color='#0f098e')
            ))
            fig_detail.update_layout(xaxis_title='Bulan', yaxis_title='Nilai', height=400)
            st.plotly_chart(fig_detail, use_container_width=True)

    st.markdown("## 📌 Daftar KPI dengan Status Hitam (Data tidak lengkap)")
    df_hitam = df[df['Status'] == 'Hitam'][['Kode KPI', 'KPI']]
    if df_hitam.empty:
        st.info("Tidak ada KPI dengan status Hitam.")
    else:
        st.dataframe(df_hitam.reset_index(drop=True), use_container_width=True)

# ================== TAB 2: STRATEGIC INITIATIVES ==================
with tabs[1]:
    st.title("Strategic Initiatives")

    si_path = "Strategic initiatives 10.csv"
    if not os.path.exists(si_path):
        st.warning(f"File SI tidak ditemukan: {si_path}")
        st.stop()

    si_df = pd.read_csv(si_path)
    si_df.columns = si_df.columns.str.strip().str.lower()

    si_status_colors = {
        'Unspecified Timeline': '#fbc4dc',
        'Unspecified DoD': '#f6b8f3',
        'Not Started': '#dcdcdc',
        'Achieved': '#009245',
        'Done': '#a9e7fa',
        'Delay': '#ff5a5a',
        'At Risk': '#ff914d',
        'On Track': '#a7f4cb',
    }
    status_order = list(si_status_colors.keys())

    program_list = si_df['program'].dropna().unique().tolist()
    if 'selected_program' not in st.session_state:
        st.session_state.selected_program = program_list[0]

    def select_program(p):
        st.session_state.selected_program = p

    # DONUT CHART: semua tampil dulu, 3 per baris
    cols_per_row = 3
    for i in range(0, len(program_list), cols_per_row):
        row = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(program_list):
                program = program_list[idx]
                with row[j]:
                    st.button(f"{program}", key=f"btn_{program}", on_click=select_program, args=(program,))
                    prog_df = si_df[si_df['program'] == program]
                    counts = prog_df['status'].value_counts().reindex(status_order).fillna(0)
                    donut = px.pie(
                        names=counts.index,
                        values=counts.values,
                        hole=0.6,
                        color=counts.index,
                        color_discrete_map=si_status_colors,
                    )
                    donut.update_traces(textinfo='none')
                    donut.update_layout(
                        showlegend=True,
                        height=300,
                        margin=dict(t=10, b=10)
                    )
                    st.plotly_chart(donut, use_container_width=True)

    # TABEL DITAMPILKAN TERAKHIR SETELAH SEMUA DONUT
    selected_program = st.session_state.selected_program
    st.markdown(f"### Total Strategic Initiatives untuk {selected_program}: **{len(si_df[si_df['program'] == selected_program])}**")
    prog_df = si_df[si_df['program'] == selected_program]
    table_df = prog_df[['no', 'nama si', 'related kpi', 'pic', 'status', '% completed dod', 'deadline', 'milestone']].copy()

  def style_si_row(row):
    color = si_status_colors.get(row['status'], 'white')
    if row['status'] in ['On Track', 'Unspecified Timeline', 'Not Started']:
        font_color = 'black'
    else:
        font_color = 'white'
    return [f'background-color: {color}; color: {font_color};'] * len(row)
    st.dataframe(table_df.style.apply(style_si_row, axis=1), use_container_width=True)
