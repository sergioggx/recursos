import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import json
from datetime import datetime, date
from groq import Groq

# --- CONFIGURACIÓN DE LA APP ---
st.set_page_config(page_title="StrideMetrics Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- INTERFAZ VISUAL MINIMALISTA (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    section[data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .metric-card {
        background-color: #161B22; padding: 20px; border-radius: 8px;
        border: 1px solid #30363D; text-align: left;
    }
    .metric-title { color: #8B949E; font-size: 13px; font-weight: 500; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { color: #FC4C02; font-size: 26px; font-weight: 700; }
    .stTabs [data-baseweb="tab"] { background-color: #161B22; border: 1px solid #30363D; color: #8B949E; padding: 8px 16px; }
    .stTabs [aria-selected="true"] { background-color: #FC4C02 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- BASE DE DATOS LOCAL SEGURA ---
def conectar_db():
    return sqlite3.connect("strava_demo.db")

def inicializar_db():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS carreras (
            id TEXT PRIMARY KEY, fecha TEXT, distancia REAL, tiempo REAL, desnivel REAL, tipo TEXT, notas TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS objetivos_avanzados (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT, metrica TEXT, valor_meta REAL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entrenamientos_creados (
            id INTEGER PRIMARY KEY AUTOINCREMENT, nombre_entrenamiento TEXT, deporte TEXT, descripcion TEXT
        )
    """)
    
    cursor.execute("SELECT COUNT(*) FROM carreras")
    if cursor.fetchone()[0] == 0:
        datos_demo = [
            ('1', '2026-05-01', 5.20, 27.5, 45, 'Suave', 'Buenas sensaciones al arrancar el mes.'),
            ('2', '2026-05-04', 8.00, 42.1, 110, 'Series', 'Series de 1000m en pista.'),
            ('3', '2026-05-08', 10.50, 54.3, 160, 'Fondo', 'Tirada larga a ritmo controlado.'),
            ('4', '2026-05-12', 6.10, 32.0, 35, 'Suave', 'Carrera de recuperación.'),
            ('5', '2026-05-15', 12.30, 65.2, 240, 'Montaña', 'Entrenamiento con desnivel en el parque natural.'),
            ('6', '2026-05-20', 5.00, 24.8, 30, 'Ritmo', 'Test de velocidad 5K.'),
            ('7', '2026-05-25', 15.00, 79.5, 310, 'Montaña', 'Tirada larga de trail de fin de semana.'),
            ('8', '2026-05-29', 8.50, 44.0, 95, 'Fondo', 'Ritmo alegre y constante.')
        ]
        cursor.executemany("INSERT INTO carreras VALUES (?, ?, ?, ?, ?, ?, ?)", datos_demo)
        cursor.execute("INSERT INTO objetivos_avanzados (nombre, metrica, valor_meta) VALUES ('Meta Mensual', 'Distancia Total (km)', 100.0)")
        conn.commit()
    conn.close()

inicializar_db()

# --- CARGAR TELEMETRÍA ---
conn = conectar_db()
df = pd.read_sql_query("SELECT * FROM carreras ORDER BY fecha ASC", conn)
df_objetivos = pd.read_sql_query("SELECT * FROM objetivos_avanzados", conn)
conn.close()

df['fecha'] = pd.to_datetime(df['fecha'])
df['Ritmo (min/km)'] = round(df['tiempo'] / df['distancia'], 2)
df['Velocidad (km/h)'] = round(df['distancia'] / (df['tiempo'] / 60), 2)

# --- HEADER ---
st.title("⚡ StrideMetrics Dashboard Engine")
st.markdown("<p style='color:#8B949E; font-size:14px;'>Consola centralizada para analítica deportiva avanzada y planeación con Inteligencia Artificial.</p>", unsafe_allow_html=True)
st.markdown("<hr style='border-color: #30363D;'>", unsafe_allow_html=True)

# --- PESTAÑAS RAÍZ ---
tab_dashboard, tab_ia, tab_planificador = st.tabs(["📊 Panel de Control", "🤖 Asistente Coach IA", "📅 Planificador de Sesiones"])

# =========================================================
# PESTAÑA 1: PANEL DE CONTROL ANALÍTICO
# =========================================================
with tab_dashboard:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Volumen Acumulado</div><div class="metric-value">{df["distancia"].sum():.1f} km</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Ritmo Promedio</div><div class="metric-value">{df["Ritmo (min/km)"].mean():.2f} min/km</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Ganancia Vertical</div><div class="metric-value">{df["desnivel"].sum():.0f} m+</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Sesiones Ejecutadas</div><div class="metric-value">{len(df)}</div></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        fig_vol = px.bar(df, x='fecha', y='distancia', title="Distribución de Volumen (km)", template="plotly_dark")
        fig_vol.update_traces(marker_color='#FC4C02')
        fig_vol.update_layout(plot_bgcolor='#161B22', paper_bgcolor='#161B22')
        st.plotly_chart(fig_vol, use_container_width=True)

    with g_col2:
        fig_rit = px.line(df, x='fecha', y='Ritmo (min/km)', title="Fluctuación Crónica del Ritmo", template="plotly_dark", markers=True)
        fig_rit.update_traces(line=dict(color='#00F2FE', width=3))
        # 🔥 CORRECCIÓN CRÍTICA AQUÍ: Se cambió "reverse" por "reversed"
        fig_rit.update_layout(plot_bgcolor='#161B22', paper_bgcolor='#161B22', yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_rit, use_container_width=True)

# =========================================================
# PESTAÑA 2: ASISTENTE COACH IA (GROQ COMPLETAMENTE PROTEGIDO)
# =========================================================
with tab_ia:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("🤖 Análisis de Rendimiento mediante Modelos de Lenguaje")
    st.caption("La IA procesará la matriz de datos de tu base de datos para extraer patrones deportivos ocultos.")

    import os
    groq_key = os.environ.get("GROQ_API_KEY", "")

    if not groq_key:
        st.warning("⚠️ No se ha detectado la clave API de Groq en las variables de entorno.")
        st.info("Para usar esta pestaña, recuerda ejecutar en tu terminal antes de lanzar la app:\n\n`export GROQ_API_KEY='tu_clave_aqui'`")
    else:
        if st.button("🧠 Ejecutar Auditoría Deportiva Completa"):
            # Serializamos los datos reales de la BD para inyectárselos como contexto puro a la IA
            matriz_datos = df[['fecha', 'distancia', 'tiempo', 'desnivel', 'tipo', 'Ritmo (min/km)']].to_json(orient="records")
            
            prompt_ingenieria = f"""
            Actúa como un Ingeniero de Datos Deportivos y Head Coach de atletas de alto rendimiento.
            Analiza el siguiente historial de entrenamientos en formato JSON y entrégame:
            1. Diagnóstico de consistencia y ritmo óptimo de trabajo.
            2. Detección de posibles riesgos de lesión o picos drásticos de carga.
            3. Recomendación exacta de qué tipo de sesión le hace falta al corredor para mejorar su umbral de velocidad.

            Datos del atleta:
            {matriz_datos}
            
            Sé conciso, profesional y estructurado en tu respuesta.
            """
            
            try:
                with st.spinner("Instanciando modelos de Groq y auditando variables biométricas..."):
                    client = Groq(api_key=groq_key)
                    completion = client.chat.completions.create(
                        model="llama3-8b-8192",
                        messages=[{"role": "user", "content": prompt_ingenieria}],
                        temperature=0.3,
                        max_tokens=1024
                    )
                    respuesta_ia = completion.choices[0].message.content
                st.markdown("<div style='background-color: #161B22; padding: 25px; border-radius: 8px; border: 1px solid #30363D;'>", unsafe_allow_html=True)
                st.markdown(respuesta_ia)
                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Fallo en la comunicación con la API de Groq: {e}")

# =========================================================
# PESTAÑA 3: PLANIFICADOR DE SESIONES TRADICIONALES
# =========================================================
with tab_planificador:
    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("📅 Constructor Estructurado de Sesiones")
    
    sub_tab_crear, sub_tab_ver = st.tabs(["➕ Diseñar Estructura", "📋 Ver Bloques Guardados"])
    
    with sub_tab_crear:
        with st.form("form_entrenamiento"):
            nombre_sesion = st.text_input("Identificador del Bloque:", placeholder="Ej: Series de Tolerancia al Lactato")
            deporte_tipo = st.selectbox("Especialidad:", ["Carrera", "Trail Montaña", "Ciclismo"])
            cuerpo_sesion = st.text_area("Cuerpo del Entrenamiento (Intervalos / Zonas):", placeholder="Ej: 15 min Z1 + 5x1000m en Z4 rec. 2 min + 10 min Z1")
            
            enviar_bloque = st.form_submit_button("💾 Archivar Bloque en BD")
            if enviar_bloque and nombre_sesion and cuerpo_sesion:
                conn = conectar_db()
                cursor = conn.cursor()
                cursor.execute("INSERT INTO entrenamientos_creados (nombre_entrenamiento, deporte, descripcion) VALUES (?, ?, ?)",
                               (nombre_sesion, deporte_tipo, cuerpo_sesion))
                conn.commit()
                conn.close()
                st.success("Estructura de entrenamiento sincronizada en la base de datos.")
                st.rerun()

    with sub_tab_ver:
        st.markdown("<br>", unsafe_allow_html=True)
        conn = conectar_db()
        df_entrenamientos_actualizado = pd.read_sql_query("SELECT * FROM entrenamientos_creados ORDER BY id DESC", conn)
        conn.close()

        if df_entrenamientos_actualizado.empty:
            st.info("No hay bloques de entrenamiento guardados todavía.")
        else:
            for _, row in df_entrenamientos_actualizado.iterrows():
                accent = "#FC4C02" if row['deporte'] == "Carrera" else "#00F2FE"
                st.markdown(f"""
                    <div style='background-color: #161B22; padding: 20px; border-radius: 10px; border-left: 5px solid {accent}; margin-bottom: 15px;'>
                        <strong style='font-size: 16px;'>{row['nombre_entrenamiento']}</strong> — <span style='color:{accent}; font-weight:bold;'>{row['deporte'].upper()}</span>
                        <p style='font-size:14px; color:#C9D1D9; white-space: pre-line; margin-top: 8px;'>{row['descripcion']}</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("Eliminar", key=f"del_{row['id']}", use_container_width=True):
                    conn = conectar_db()
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM entrenamientos_creados WHERE id = ?", (row['id'],))
                    conn.commit()
                    conn.close()
                    st.rerun()