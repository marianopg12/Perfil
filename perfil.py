import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Player Profile", layout="wide")

# ============================
# WHITE AND BLUE, clean style
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Barlow:wght@400;600&family=Space+Mono&display=swap');

[data-testid="stAppViewContainer"] { background: #ffffff; }
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid rgba(0,0,0,0.08); }

/* HEADER */
.player-header {
    background: #f7f9fc;
    padding: 20px;
    border-radius: 10px;
    border-left: 6px solid #00a8cc;
    margin-bottom: 25px;
}

.player-name {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 36px;
    letter-spacing: 2px;
    font-weight: 900;
    margin: 0;
}

.player-meta {
    color: #6b7280;
    font-size: 14px;
}

/* ATTRIBUTE BOX (same as catalog) */
.attribute-box {
    background: #f7f9fc;
    border: 1px solid rgba(0,0,0,0.06);
    border-top: 2px solid #00a8cc;
    border-radius: 8px;
    padding: 12px 8px;
    text-align: center;
    margin-bottom: 10px;
}

.attribute-label {
    font-family: 'Space Mono', monospace;
    font-size: 9px;
    letter-spacing: 1px;
    color: #6b7280;
}

.attribute-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 26px;
    font-weight: 700;
}

/* SECTIONS */
.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 20px;
    letter-spacing: 2px;
    border-bottom: 2px solid rgba(0,168,204,0.25);
    margin-top: 35px;
    margin-bottom: 15px;
}

/* Bio boxes */
.bio-box {
    background: #f0f9ff;
    border: 1px solid rgba(0,168,204,0.15);
    border-radius: 8px;
    padding: 12px;
    text-align: center;
}
.bio-label {
    font-family: 'Space Mono', monospace;
    font-size: 8px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 1px;
}
.bio-value {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 22px;
    font-weight: 700;
    color: #111;
}
.bio-unit {
    font-size: 11px;
    color: #6b7280;
}
</style>
""", unsafe_allow_html=True)

# ======================
# LOAD ANTHROPOMETRY DATA
# ======================
@st.cache_data
def load_antropometria():
    try:
        df_ant = pd.read_excel("jugadores_stats.xls", sheet_name="Antropometria")
        df_ant.columns = df_ant.columns.str.strip()
        return df_ant
    except:
        return pd.DataFrame()

df_ant = load_antropometria()

# ======================
# LOAD STRENGTH DATA
# ======================
@st.cache_data
def load_fuerza():
    try:
        df_fuerza = pd.read_excel("jugadores_stats.xls", sheet_name="Fuerza")
        df_fuerza.columns = df_fuerza.columns.str.strip()
        return df_fuerza
    except:
        return pd.DataFrame()

df_fuerza = load_fuerza()

# ======================
# LOAD JUMPABILITY DATA
# ======================
@st.cache_data
def load_saltabilidad():
    try:
        df_salt = pd.read_excel("jugadores_stats.xls", sheet_name="Saltabilidad")
        df_salt.columns = df_salt.columns.str.strip()
        return df_salt
    except:
        return pd.DataFrame()

df_salt = load_saltabilidad()

# ======================
# BIOMETRY FUNCTIONS
# ======================
def calculate_bmi(weight, height):
    if height > 0:
        return weight / (height ** 2)
    return 0

def calculate_body_fat_jackson_pollock(triceps_skinfold, subscapular_skinfold, age, sex='m'):
    sum_folds = triceps_skinfold + subscapular_skinfold
    if sum_folds <= 0 or age is None or age <= 0:
        return None
    
    if sex == 'm':
        density = 1.112 - 0.00043499 * sum_folds + 0.00000055 * (sum_folds ** 2) - 0.00028826 * age
    else:
        density = 1.097 - 0.00046971 * sum_folds + 0.00000056 * (sum_folds ** 2) - 0.00012828 * age
    
    body_fat = (495 / density) - 450
    return max(3, min(50, body_fat))

def estimate_body_fat(bmi, age):
    return max(5, min(40, (1.20 * bmi) + (0.23 * age) - 10.8))

def get_body_fat(player, weight, age=None):
    if df_ant.empty:
        return None, None
    
    row = df_ant[df_ant['Deportista'] == player]
    if row.empty:
        return None, None
    
    row = row.iloc[0]
    grasa_pct = row.get('grasa porcentaje')
    if pd.notna(grasa_pct) and grasa_pct > 0:
        return float(grasa_pct), "excel"
    
    pliegue_tri = row.get('pliegue tricipital')
    pliegue_sub = row.get('pliegue subescapular')
    edad_calc = age if age is not None else row.get('Edad', 25)
    
    if pd.notna(pliegue_tri) and pd.notna(pliegue_sub) and (pliegue_tri + pliegue_sub) > 0:
        body_fat_calc = calculate_body_fat_jackson_pollock(pliegue_tri, pliegue_sub, edad_calc)
        if body_fat_calc:
            return body_fat_calc, "skinfold"
    
    return None, "estimated"

def estimate_muscle_mass(weight, height, body_fat):
    bmi = calculate_bmi(weight, height)
    return weight * (100 - body_fat) / 100 * 0.45

def get_physical_status(bmi):
    if bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obesity"

# ======================
# LOAD DATA
# ======================
@st.cache_data
def load_data():
    df = pd.read_excel("jugadores_stats.xls")
    df.columns = df.columns.str.strip()

    cols = ['Maxima velocidad','Distancia Total(m)','Conteo de sprints','Max Acc (g)','Calor(Kcal)']
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)

    return df

df = load_data()

if df.empty:
    st.warning("Loading data...")
    st.stop()

# ======================
# SIDEBAR - PLAYER SELECTION
# ======================
st.sidebar.markdown("### Player Selection")
report_mode = st.sidebar.checkbox("All Players (Report Mode)")

if report_mode:
    selected_players = df['Deportista'].unique().tolist()
else:
    selected_players = [st.sidebar.selectbox("Select Player", df['Deportista'].unique())]

# PDF Export button
if st.sidebar.button("Export to PDF"):
    st.sidebar.info("Press Ctrl + P → Save as PDF")

st.markdown("---")

# ======================
# CSS FOR PAGE BREAKS IN PDF
# ======================
st.markdown("""
<style>
@media print {
    .page-break {
        page-break-before: always;
    }
}
</style>
""", unsafe_allow_html=True)

# ======================
# DISPLAY PLAYER(S)
# ======================
for idx, player_name in enumerate(selected_players):
    if idx > 0:
        st.markdown('<div class="page-break"></div>', unsafe_allow_html=True)
    p = df[df['Deportista']==player_name].iloc[0]
    
    photo_path = p.get('Photo')
    if pd.notna(photo_path) and photo_path:
        photo_path = str(photo_path).replace('\\', '/')
    else:
        photo_path = None

    # ======================
    # HEADER
    # ======================
    st.markdown("""
    <style>
    div[data-testid="stImage"] {
        margin-top: -25px;
    }
    </style>
    """, unsafe_allow_html=True)

    col_info, col_photo = st.columns([4, 1])

    with col_info:
        st.markdown(f"""
    <div class="player-header">
    <div class="player-name">{p['Deportista'].upper()}</div>
    <div class="player-meta">
    {p['Posicion']} • {p['Nacionalidad']} • {p.get('Equipo','Club')} <br>
    {p['Altura (mts)']} m • {p['Peso (kg)']} kg
    </div>
    </div>
    """, unsafe_allow_html=True)

    with col_photo:
        if photo_path:
            try:
                st.image(photo_path, width=150)
            except:
                st.write("")

    # ======================
    # LAYOUT
    # ======================
    col_metrics, col_radar = st.columns([1,1.2])

    with col_metrics:

        st.markdown('<div class="section-title">Physical Performance</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        metrics = [
            ("Speed", f"{p['Maxima velocidad']:.2f} km/h"),
            ("Resistance", f"{p['Distancia Total(m)']:.0f} m"),
            ("Sprints", f"{p['Conteo de sprints']:.0f}"),
            ("Acceleration", f"{p['Max Acc (g)']:.2f} g"),
            ("Load", f"{p['Calor(Kcal)']:.0f} kcal"),
        ]

        for i, (label, value) in enumerate(metrics):
            box = c1 if i % 2 == 0 else c2
            box.markdown(f"""
            <div class="attribute-box">
                <div class="attribute-label">{label}</div>
                <div class="attribute-value" style="font-size:20px">{value.split()[0]}</div>
                <div style="font-size:11px;color:#6b7280">{" ".join(value.split()[1:])}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_radar:

        categories = ['Speed','Resistance','Sprints','Acceleration','Load']
        values = [
            p['Maxima velocidad'],
            p['Distancia Total(m)'] / 100,
            p['Conteo de sprints'],
            p['Max Acc (g)'] * 100,
            p['Calor(Kcal)'] / 10
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself'
        ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            showlegend=False,
            margin=dict(t=30,b=30,l=30,r=30),
            height=360,
            paper_bgcolor='rgba(0,0,0,0)'
        )

        st.plotly_chart(fig, use_container_width=True, key=f"radar_{player_name}")

    # ======================
    # BIOMETRY
    # ======================
    st.markdown('<div class="section-title">Biometry & Body Composition</div>', unsafe_allow_html=True)

    weight = float(p.get('Peso (kg)', 70))
    height = float(p.get('Altura (mts)', 1.70))

    bmi = calculate_bmi(weight, height)

    age = p.get('Edad')
    if pd.isna(age):
        age = None

    body_fat, fat_source = get_body_fat(player_name, weight, age)

    if body_fat is None:
        age_calc = age if age is not None else 25
        body_fat = estimate_body_fat(bmi, age_calc)
        fat_source = "estimated"

    muscle = estimate_muscle_mass(weight, height, body_fat)
    status = get_physical_status(bmi)

    col_bio1, col_bio2, col_bio3, col_bio4, col_bio5 = st.columns(5)

    col_bio1.markdown(f"""
    <div class="bio-box">
        <div class="bio-label">Age</div>
        <div class="bio-value">{int(age) if age is not None else ''}</div>
        <div class="bio-unit">years</div>
    </div>
    """, unsafe_allow_html=True)

    col_bio2.markdown(f"""
    <div class="bio-box">
        <div class="bio-label">BMI</div>
        <div class="bio-value">{bmi:.1f}</div>
        <div class="bio-unit">kg/m²</div>
    </div>
    """, unsafe_allow_html=True)

    col_bio3.markdown(f"""
    <div class="bio-box">
        <div class="bio-label">Body Fat</div>
        <div class="bio-value">{body_fat:.1f}%</div>
        <div class="bio-unit">{fat_source}</div>
    </div>
    """, unsafe_allow_html=True)

    col_bio4.markdown(f"""
    <div class="bio-box">
        <div class="bio-label">Muscle Mass</div>
        <div class="bio-value">{muscle:.1f}</div>
        <div class="bio-unit">kg</div>
    </div>
    """, unsafe_allow_html=True)

    col_bio5.markdown(f"""
    <div class="bio-box">
        <div class="bio-label">Status</div>
        <div class="bio-value" style="font-size:18px">{status}</div>
        <div class="bio-unit">physical</div>
    </div>
    """, unsafe_allow_html=True)

    # ======================
    # STRENGTH
    # ======================
    if not df_fuerza.empty:
        row_fuerza = df_fuerza[df_fuerza['Deportista'] == player_name]
        if not row_fuerza.empty:
            row_f = row_fuerza.iloc[0]
            st.markdown('<div class="section-title">Max Strength - 1RM</div>', unsafe_allow_html=True)
            
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            squat = row_f.get('Squat (kg)')
            press = row_f.get('Press banca (kg)')
            deadlift = row_f.get('Peso muerto (kg)')
            curl = row_f.get('Curl biceps (kg)')
            
            col_f1.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">Squat</div>
                <div class="bio-value">{squat if pd.notna(squat) else '-'} <span class="bio-unit">kg</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            col_f2.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">Bench Press</div>
                <div class="bio-value">{press if pd.notna(press) else '-'} <span class="bio-unit">kg</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            col_f3.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">Deadlift</div>
                <div class="bio-value">{deadlift if pd.notna(deadlift) else '-'} <span class="bio-unit">kg</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            col_f4.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">Bicep Curl</div>
                <div class="bio-value">{curl if pd.notna(curl) else '-'} <span class="bio-unit">kg</span></div>
            </div>
            """, unsafe_allow_html=True)

    # ======================
    # JUMPABILITY
    # ======================
    if not df_salt.empty:
        row_salt = df_salt[df_salt['Deportista'] == player_name]
        if not row_salt.empty:
            row_s = row_salt.iloc[0]
            st.markdown('<div class="section-title">Jump Ability</div>', unsafe_allow_html=True)
            
            col_s1, col_s2, col_s3 = st.columns(3)
            
            cmj = row_s.get('CMJ')
            sj = row_s.get('SJ')
            dj = row_s.get('DJ')
            
            col_s1.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">CMJ</div>
                <div class="bio-value">{cmj if pd.notna(cmj) else '-'} <span class="bio-unit">cm</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            col_s2.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">SJ</div>
                <div class="bio-value">{sj if pd.notna(sj) else '-'} <span class="bio-unit">cm</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            col_s3.markdown(f"""
            <div class="bio-box">
                <div class="bio-label">DJ</div>
                <div class="bio-value">{dj if pd.notna(dj) else '-'} <span class="bio-unit">cm</span></div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

# ======================
# SQUAD COMPARISON
# ======================
st.markdown('<div class="section-title">Squad Comparison</div>', unsafe_allow_html=True)

comp = df[['Deportista','Maxima velocidad','Distancia Total(m)','Conteo de sprints','Max Acc (g)']].copy()
comp.columns = ['Player', 'Speed (km/h)', 'Distance (m)', 'Sprints', 'Acceleration (g)']

if not df_fuerza.empty:
    fuerza_cols = df_fuerza[['Deportista', 'Squat (kg)', 'Press banca (kg)', 'Peso muerto (kg)', 'Curl biceps (kg)']].copy()
    fuerza_cols.columns = ['Player', 'Squat (kg)', 'Bench Press (kg)', 'Deadlift (kg)', 'Bicep Curl (kg)']
    comp = comp.merge(fuerza_cols, on='Player', how='left')

st.dataframe(
    comp.style.format(precision=2),
    use_container_width=True,
    hide_index=True
)
