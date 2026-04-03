"""
Página 5 — Alertas e Oportunidades
Mostra alertas dinâmicos baseados nos dados do mercado atual.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.score_mitada import build_atletas_df, calcular_sam
from utils.alertas import detectar_alertas, filtrar_alertas

st.set_page_config(page_title="Alertas | Cartola Analyzer", page_icon="🔔", layout="wide")
st.title("🔔 Alertas e Oportunidades")

@st.cache_data(ttl=300, show_spinner=False)
def load():
    return calcular_sam(build_atletas_df())

with st.spinner("Carregando dados..."):
    df = load()

if df.empty:
    st.error("Sem dados disponíveis.")
    st.stop()

# ── filtros de alerta ─────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Filtros de Alerta")
    mostrar = st.multiselect(
        "Tipos de alerta",
        options=["success", "warning", "error", "info"],
        default=["success", "warning", "error", "info"],
        format_func=lambda x: {"success":"📈 Alta","warning":"📉 Queda","error":"🚨 Problema","info":"💡 Oportunidade"}[x],
    )
    max_alertas = st.slider("Máx. alertas exibidos", 5, 50, 20)

todos_alertas = detectar_alertas(df)
alertas_filtrados = filtrar_alertas(todos_alertas, mostrar)[:max_alertas]

# ── sumário ───────────────────────────────────────────────────────────────
st.subheader(f"📋 {len(todos_alertas)} alertas detectados")
cont = {"success": 0, "warning": 0, "error": 0, "info": 0}
for a in todos_alertas:
    cont[a.tipo] += 1

c1, c2, c3, c4 = st.columns(4)
c1.metric("📈 Altas", cont["success"])
c2.metric("📉 Quedas", cont["warning"])
c3.metric("🚨 Problemas", cont["error"])
c4.metric("💡 Oportunidades", cont["info"])

st.markdown("---")

# ── lista de alertas ──────────────────────────────────────────────────────
COLOR_MAP = {
    "success": ("#d4dfcc", "#437a22"),
    "warning": ("#e7d7c4", "#da7101"),
    "error":   ("#e0ced7", "#a12c7b"),
    "info":    ("#cedcd8", "#01696f"),
}

for alerta in alertas_filtrados:
    bg, border = COLOR_MAP[alerta.tipo]
    st.markdown(
        f'''<div style="background:{bg};border-left:4px solid {border};padding:.75rem 1.1rem;border-radius:8px;margin:.4rem 0;">
        <strong>{alerta.titulo}</strong><br/><span style="font-size:.9rem;color:#555;">{alerta.mensagem}</span>
        </div>''',
        unsafe_allow_html=True,
    )

if not alertas_filtrados:
    st.success("✅ Nenhum alerta para os filtros selecionados.")

st.divider()

# ── gráfico: top 15 valorizações ─────────────────────────────────────────
st.subheader("📈 Top 15 Maiores Valorizações")
top_valorizacao = df.nlargest(15, "variacao")[["nome", "clube", "posicao", "variacao", "media"]]
fig = px.bar(
    top_valorizacao, x="variacao", y="nome", orientation="h",
    color="posicao", text="variacao",
    color_discrete_sequence=["#01696f","#d19900","#a12c7b","#da7101","#006494","#437a22"],
    labels={"variacao": "Variação (C$)", "nome": ""},
)
fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(autorange="reversed"))
st.plotly_chart(fig, use_container_width=True)

st.subheader("📉 Top 15 Maiores Desvalorizações")
top_desvalorizacao = df.nsmallest(15, "variacao")[["nome", "clube", "posicao", "variacao", "media"]]
fig2 = px.bar(
    top_desvalorizacao, x="variacao", y="nome", orientation="h",
    color="posicao", text="variacao",
    color_discrete_sequence=["#a12c7b","#da7101","#01696f","#d19900","#006494","#437a22"],
    labels={"variacao": "Variação (C$)", "nome": ""},
)
fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", yaxis=dict(autorange="reversed"))
st.plotly_chart(fig2, use_container_width=True)
