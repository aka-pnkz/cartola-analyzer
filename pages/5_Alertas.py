import streamlit as st
import pandas as pd

from utils.score_mitada import build_atletas_df, PERFIS
from utils.alertas import gerar_alertas

st.set_page_config(
    page_title="Alertas | Cartola Analyzer",
    page_icon="🚨",
    layout="wide",
)

st.title("🚨 Alertas Inteligentes")

with st.sidebar:
    st.header("⚙️ Configurações")
    perfil = st.selectbox(
        "🎯 Perfil tático",
        list(PERFIS.keys()),
        index=0,
    )

df = build_atletas_df(perfil=perfil)

if df.empty:
    st.error("Sem dados disponíveis para gerar alertas.")
    st.stop()

alertas = gerar_alertas(df)

if alertas.empty:
    st.info("Nenhum alerta encontrado para o cenário atual.")
    st.stop()

st.subheader("📋 Alertas gerados")

colunas = [
    "tipo",
    "mensagem",
    "nome",
    "clube",
    "posicao",
    "status",
    "preco",
    "media",
    "score_pct",
    "evento_em",
    "criado_em",
]
colunas = [c for c in colunas if c in alertas.columns]

st.dataframe(
    alertas[colunas],
    use_container_width=True,
    hide_index=True,
    column_config={
        "evento_em": st.column_config.DatetimeColumn(
            "Evento em",
            format="DD/MM/YYYY HH:mm",
        ),
        "criado_em": st.column_config.DatetimeColumn(
            "Criado em",
            format="DD/MM/YYYY HH:mm",
        ),
    },
)
