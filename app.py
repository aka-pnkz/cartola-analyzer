"""
Cartola Analyzer — Página Principal (app.py)
Aplicativo Streamlit para análise avançada do Cartola FC.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.api import get_mercado_status, get_atletas_mercado, POSICAO_MAP, STATUS_MAP
from utils.score_mitada import build_atletas_df, calcular_sam
from utils.alertas import detectar_alertas
from utils.exportacao import download_button_data

# ── configuração da página ─────────────────────────────────────────────────
st.set_page_config(
    page_title="Cartola Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Cartola Analyzer — Análise avançada para o Cartola FC.",
    },
)

# ── CSS customizado ────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f7f6f2; }
    h1 { font-size: 2rem !important; font-weight: 700; }
    h2 { font-size: 1.4rem !important; font-weight: 600; }
    .kpi-card {
        background: #ffffff;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 1px 4px rgba(40,37,29,.08);
        text-align: center;
    }
    .kpi-value { font-size: 2rem; font-weight: 700; color: #01696f; }
    .kpi-label { font-size: 0.85rem; color: #7a7974; margin-top: .25rem; }
    .alerta-success { background:#d4dfcc; border-left:4px solid #437a22; padding:.6rem 1rem; border-radius:6px; margin:.3rem 0; }
    .alerta-warning { background:#e7d7c4; border-left:4px solid #da7101; padding:.6rem 1rem; border-radius:6px; margin:.3rem 0; }
    .alerta-error   { background:#e0ced7; border-left:4px solid #a12c7b; padding:.6rem 1rem; border-radius:6px; margin:.3rem 0; }
    .alerta-info    { background:#cedcd8; border-left:4px solid #01696f; padding:.6rem 1rem; border-radius:6px; margin:.3rem 0; }
</style>
""", unsafe_allow_html=True)


# ── sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://s.glbimg.com/es/ge/f/original/2014/03/14/cartola_logo.png",
             width=160, use_container_width=False)
    st.markdown("## ⚽ Cartola Analyzer")
    st.markdown("---")
    st.markdown("""
**Navegação**
- 🏠 **Dashboard** — visão geral
- 📋 **Escalação** — monte seu time
- ⚔️ **Confrontos** — análise de partidas
- 🔍 **Comparador** — compare atletas
- 🔔 **Alertas** — oportunidades e riscos
""")
    st.markdown("---")
    st.caption("Dados atualizados a cada 5 min via API Cartola.")


# ── carregamento de dados ─────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    df = build_atletas_df()
    if df.empty:
        return df
    return calcular_sam(df)

status_raw = get_mercado_status()
with st.spinner("🔄 Carregando dados do mercado..."):
    df_all = load_data()

# ── cabeçalho ─────────────────────────────────────────────────────────────
st.title("⚽ Cartola Analyzer — Dashboard")

rodada_atual = status_raw.get("rodada_atual", "?") if isinstance(status_raw, dict) else "?"

STATUS_MERCADO_NOME = {
    1: "Aberto",
    2: "Fechado",
    3: "Em atualização",
    4: "Final de temporada",
}

status_mercado_id = status_raw.get("status_mercado") if isinstance(status_raw, dict) else None
status_mercado = STATUS_MERCADO_NOME.get(status_mercado_id, str(status_mercado_id or "?"))

if df_all.empty:
    st.error("⚠️ Não foi possível carregar os dados. Verifique sua conexão.")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
kpis = [
    (col1, len(df_all), "Total de Atletas"),
    (col2, f"#{rodada_atual}", "Rodada Atual"),
    (col3, status_mercado, "Status do Mercado"),
    (col4, f"{df_all['media'].mean():.1f}", "Média Geral"),
    (col5, f"C$ {df_all['preco'].median():.1f}", "Preço Mediano"),
]
for col, val, label in kpis:
    with col:
        st.markdown(
            f'<div class="kpi-card"><div class="kpi-value">{val}</div><div class="kpi-label">{label}</div></div>',
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── distribuição por posição ───────────────────────────────────────────────
col_a, col_b = st.columns([1, 1.6])

with col_a:
    st.subheader("📊 Atletas por Posição")
    pos_count = df_all.groupby("posicao").size().reset_index(name="count")
    fig_pie = px.pie(
        pos_count, names="posicao", values="count",
        color_discrete_sequence=["#01696f","#d19900","#a12c7b","#da7101","#006494","#437a22"],
        hole=0.42,
    )
    fig_pie.update_layout(margin=dict(t=10, b=10, l=10, r=10), paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("📈 Média por Posição — Top 5 Atletas")
    top5_pos = (
        df_all.groupby("posicao")
              .apply(lambda x: x.nlargest(5, "media"))
              .reset_index(drop=True)
    )
    fig_bar = px.bar(
        top5_pos, x="nome", y="media", color="posicao", barmode="group",
        color_discrete_sequence=["#01696f","#d19900","#a12c7b","#da7101","#006494","#437a22"],
        labels={"nome": "Atleta", "media": "Média de Pontos"},
    )
    fig_bar.update_layout(
        showlegend=True, margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis_tickangle=-35,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ── top 10 geral por SAM ───────────────────────────────────────────────────
st.subheader("🏆 Top 10 — Score Anti-Mitada (SAM)")
top10 = df_all.head(10)[["ranking", "nome", "clube", "posicao", "status", "preco", "media", "variacao", "sam_pct"]]
top10.columns = ["#", "Atleta", "Clube", "Posição", "Status", "Preço (C$)", "Média", "Variação", "SAM (%)"]
st.dataframe(top10, use_container_width=True, hide_index=True)

# ── alertas rápidos ────────────────────────────────────────────────────────
st.subheader("🔔 Alertas Rápidos")
alertas = detectar_alertas(df_all)[:8]
for alerta in alertas:
    st.markdown(
        f'<div class="alerta-{alerta.tipo}"><strong>{alerta.titulo}</strong> — {alerta.mensagem}</div>',
        unsafe_allow_html=True,
    )

# ── exportação ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("⬇️ Exportar Dados")
col_e1, col_e2, col_e3 = st.columns(3)
for col, fmt, label in [(col_e1, "csv", "CSV"), (col_e2, "xlsx", "Excel"), (col_e3, "json", "JSON")]:
    data, fname, mime = download_button_data(df_all, fmt)
    col.download_button(f"📥 Baixar {label}", data=data, file_name=fname, mime=mime)
