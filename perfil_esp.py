import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Player Profile", layout="wide")

# ============================
# ESTILOS CSS (Blanco y Azul)
# ============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@700;900&family=Barlow:wght@400;600&family=Space+Mono&display=swap');

[data-testid="stAppViewContainer"] { background: #ffffff; }
section[data-testid="stSidebar"] { background: #ffffff; border-right: 1px solid rgba(0,0,0,0.08); }

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

.section-title {
    font-family: 'Barlow Condensed', sans-serif;
    font-size: 20px;
    letter-spacing: 2px;
    border-bottom: 2px solid rgba(0,168,204,0.25);
    margin-top: 35px;
    margin-bottom: 15px;
}

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

# ============================
# FUNCIONES DE CARGA Y CÁLCULO
# ============================

@st.cache_data
def load_data():
    try:
        df = pd.read_excel("jugadores_stats_latinos.xls")
        df.columns = df.columns.str.strip()
        # Nombres de columnas actualizados según tu Excel
        cols_numericas = [
            'Maxima velocidad', 
            'Distancia Total(m)', 
            'Distancia de sprint(m)', # Nombre exacto sin espacio
            'Conteo de sprints', 
            'Max Acc (g)', 
            'Calor(Kcal)'
        ] 
        for c in cols_numericas:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error cargando datos principales: {e}")
        return pd.DataFrame()

@st.cache_data
def load_antropometria():
    try:
        df_ant = pd.read_excel("jugadores_stats_latinos.xls", sheet_name="Antropometria")
        df_ant.columns = df_ant.columns.str.strip()
        return df_ant
    except: return pd.DataFrame()

@st.cache_data
def load_fuerza():
    try:
        df_fuerza = pd.read_excel("jugadores_stats_latinos.xls", sheet_name="Fuerza")
        df_fuerza.columns = df_fuerza.columns.str.strip()
        return df_fuerza
    except: return pd.DataFrame()

@st.cache_data
def load_saltabilidad():
    try:
        df_salt = pd.read_excel("jugadores_stats_latinos.xls", sheet_name="Saltabilidad")
        df_salt.columns = df_salt.columns.str.strip()
        return df_salt
    except: return pd.DataFrame()

# Funciones de apoyo
def calcular_imc(peso, altura): return peso / (altura ** 2) if altura > 0 else 0
def estimar_masa_muscular(peso, altura, grasa): return peso * (100 - grasa) / 100 * 0.45
def get_estado_fisico(imc):
    if imc < 18.5: return "Bajo peso"
    if imc < 25: return "Normal"
    if imc < 30: return "Sobrepeso"
    return "Obesidad"

# ======================
# FLUJO PRINCIPAL
# ======================
df = load_data()
df_ant = load_antropometria()
df_fuerza = load_fuerza()
df_salt = load_saltabilidad()

if df.empty:
    st.warning("Asegúrate de que 'jugadores_stats_latinos.xls' esté en la carpeta del script.")
    st.stop()

# Sidebar
jugador = st.sidebar.selectbox("Seleccionar Jugador", df['Deportista'].unique())
p = df[df['Deportista'] == jugador].iloc[0]

# Header
st.markdown(f"""
<div class="player-header">
    <div class="player-name">{p['Deportista'].upper()}</div>
    <div class="player-meta">
        {p.get('Posicion','-')} • {p.get('Nacionalidad','-')} • {p.get('Equipo','Club')} <br>
        {p.get('Altura (mts)',0)} m • {p.get('Peso (kg)',0)} kg
    </div>
</div>
""", unsafe_allow_html=True)

# Performance y Radar
col_metrics, col_radar = st.columns([1, 1.2])

with col_metrics:
    st.markdown('<div class="section-title">Performance Física</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    
    # Usamos .get() para evitar errores si la columna falta
    metrics = [
        ("Velocidad Máx", f"{p.get('Maxima velocidad', 0):.2f} km/h"),
        ("Distancia Total", f"{p.get('Distancia Total(m)', 0):.0f} m"),
        ("Sprints (Cant)", f"{p.get('Conteo de sprints', 0):.0f}"),
        ("Dist. Sprint", f"{p.get('Distancia de sprint(m)', 0):.0f} m"),
        ("Aceleración", f"{p.get('Max Acc (g)', 0):.2f} g"),
        ("Carga", f"{p.get('Calor(Kcal)', 0):.0f} kcal"),
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
    categories = ['Velocidad','Resistencia','Sprints','Aceleración','Carga']
    values = [
        p.get('Maxima velocidad', 0), 
        p.get('Distancia Total(m)', 0)/100, 
        p.get('Conteo de sprints', 0), 
        p.get('Max Acc (g)', 0)*100, 
        p.get('Calor(Kcal)', 0)/10
    ]
    fig = go.Figure(go.Scatterpolar(r=values, theta=categories, fill='toself', line_color='#00a8cc'))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=360, paper_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)

# ======================
# COMPARATIVA PLANTEL
# ======================
st.markdown('<div class="section-title">Comparativa Plantel</div>', unsafe_allow_html=True)

# Selección segura de columnas
columnas_interes = {
    'Deportista': 'Jugador',
    'Maxima velocidad': 'Vel. Máx (km/h)',
    'Distancia Total(m)': 'Dist. Total (m)',
    'Distancia de sprint(m)': 'Dist. Sprint (m)', # CORREGIDO
    'Conteo de sprints': 'Sprints (Cant)',
    'Max Acc (g)': 'Aceleración (g)'
}

# Filtramos solo las que existen para evitar KeyError
cols_finales = [c for c in columnas_interes.keys() if c in df.columns]
comp = df[cols_finales].copy()
comp.rename(columns=columnas_interes, inplace=True)

# Mezclar con Fuerza si existe
if not df_fuerza.empty:
    f_merge = df_fuerza[['Deportista', 'Squat (kg)', 'Press banca (kg)']].copy()
    f_merge.columns = ['Jugador', 'Squat (kg)', 'Press (kg)']
    comp = comp.merge(f_merge, on='Jugador', how='left')

st.dataframe(comp.style.format(precision=2), use_container_width=True, hide_index=True)