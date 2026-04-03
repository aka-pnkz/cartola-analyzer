"""
Página 4 — Comparador de Atletas
Compare até 6 atletas lado a lado com radar chart e tabela.
"""
import streamlit as st
import pandas as pd

from utils.score_mitada import build_atletas_df, calcular_sam
from utils.comparador import comparar_atletas, radar_chart, tabela_comparativa
from utils.exportacao import download_button_data

st.set_page_config(page_title="Comparador | Cartola Analyzer", page_icon="🔍", layout="wide")
st.title("🔍 Comparador de Atletas")

@st.cache_data(ttl=300, show_spinner=False)
def load():
    return calcular_sam(build_atletas_df())

with st.spinner("Carregando atletas..."):
    df = load()

if df.empty:
    st.error("Sem dados disponíveis.")
    st.stop()

# ── seleção de atletas ────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Seleção")
    posicao = st.selectbox("Filtrar por posição", ["Todas"] + df["posicao"].unique().tolist())
    clube = st.selectbox("Filtrar por clube", ["Todos"] + sorted(df["clube"].unique().tolist()))
    preco_range = st.slider(
        "Faixa de preço (C$)",
        float(df["preco"].min()), float(df["preco"].max()),
        (float(df["preco"].min()), float(df["preco"].max())),
        step=0.5
    )

df_filt = df.copy()
if posicao != "Todas":
    df_filt = df_filt[df_filt["posicao"] == posicao]
if clube != "Todos":
    df_filt = df_filt[df_filt["clube"] == clube]
df_filt = df_filt[(df_filt["preco"] >= preco_range[0]) & (df_filt["preco"] <= preco_range[1])]

atletas_opcoes = df_filt["nome"].tolist()
selecionados = st.multiselect(
    "Selecione até 6 atletas para comparar:",
    options=atletas_opcoes,
    default=atletas_opcoes[:2] if len(atletas_opcoes) >= 2 else atletas_opcoes,
    max_selections=6,
)

if len(selecionados) < 2:
    st.info("Selecione ao menos 2 atletas para comparar.")
    st.stop()

ids_sel = df_filt[df_filt["nome"].isin(selecionados)]["id"].tolist()
df_comp = comparar_atletas(df, ids_sel)

# ── radar chart ───────────────────────────────────────────────────────────
col_radar, col_table = st.columns([1.2, 1])
with col_radar:
    st.subheader("📡 Radar de Métricas")
    fig = radar_chart(df_comp)
    st.plotly_chart(fig, use_container_width=True)

with col_table:
    st.subheader("📊 Tabela Comparativa")
    tb = tabela_comparativa(df_comp)
    st.dataframe(tb.T, use_container_width=True)

st.divider()

# ── detalhes dos scouts ───────────────────────────────────────────────────
st.subheader("🎯 Detalhes dos Scouts")
scout_cols = ["nome", "gols", "assistencias", "faltas", "amarelos", "vermelhos", "defesas_dificeis", "finalizacoes"]
scout_cols_disp = [c for c in scout_cols if c in df_comp.columns]
st.dataframe(
    df_comp[scout_cols_disp].rename(columns={
        "nome": "Atleta", "gols": "Gols", "assistencias": "Assistências",
        "faltas": "Faltas", "amarelos": "Amarelos", "vermelhos": "Vermelhos",
        "defesas_dificeis": "Defesas Difíceis", "finalizacoes": "Finalizações",
    }),
    use_container_width=True, hide_index=True,
)

# ── exportar comparação ───────────────────────────────────────────────────
st.markdown("---")
data, fname, mime = download_button_data(df_comp, "xlsx")
st.download_button("📥 Baixar Comparação (Excel)", data=data, file_name="comparacao_atletas.xlsx", mime=mime)
