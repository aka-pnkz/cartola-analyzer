import streamlit as st

from utils.score_mitada import build_atletas_df, PERFIS
from utils.alertas import gerar_alertas, filtrar_alertas

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

if df is None or df.empty:
    st.error("Sem dados disponíveis para gerar alertas.")
    st.stop()

alertas = gerar_alertas(df)

if alertas is None or alertas.empty:
    st.info("Nenhum alerta encontrado para o cenário atual.")
    st.stop()

tipos = ["Todos"] + sorted(alertas["tipo"].dropna().unique().tolist()) if "tipo" in alertas.columns else ["Todos"]
posicoes = ["Todas"] + sorted(alertas["posicao"].dropna().unique().tolist()) if "posicao" in alertas.columns else ["Todas"]
clubes = ["Todos"] + sorted(alertas["clube"].dropna().unique().tolist()) if "clube" in alertas.columns else ["Todos"]

f1, f2, f3 = st.columns(3)
tipo_sel = f1.selectbox("Tipo", tipos, index=0)
pos_sel = f2.selectbox("Posição", posicoes, index=0)
clube_sel = f3.selectbox("Clube", clubes, index=0)

alertas_filtrados = filtrar_alertas(
    alertas,
    tipo=tipo_sel,
    posicao=pos_sel,
    clube=clube_sel,
)

if alertas_filtrados is None or alertas_filtrados.empty:
    st.info("Nenhum alerta encontrado com os filtros atuais.")
    st.stop()

st.subheader("📋 Alertas gerados")

colunas = [
    "tipo",
    "mensagem",
    "nome",
    "clube",
    "posicao",
    "status",
    "status_anterior",
    "rodada_referencia",
    "mudou_nesta_consulta",
    "contexto_status",
    "detectado_em",
    "desde_quando_esta_assim",
    "preco",
    "media",
    "score_pct",
]
colunas = [c for c in colunas if c in alertas_filtrados.columns]

st.dataframe(
    alertas_filtrados[colunas],
    use_container_width=True,
    hide_index=True,
    column_config={
        "detectado_em": st.column_config.DatetimeColumn(
            "Detectado em",
            format="DD/MM/YYYY HH:mm",
        ),
        "desde_quando_esta_assim": st.column_config.DatetimeColumn(
            "Desde quando",
            format="DD/MM/YYYY HH:mm",
        ),
    },
)
