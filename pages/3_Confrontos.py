import streamlit as st

from utils.score_mitada import build_atletas_df, PERFIS
from utils.confrontos import (
    montar_tabela_confrontos,
    melhores_confrontos,
    grafico_indices_confronto,
    sugerir_atletas_por_confronto,
)

st.set_page_config(
    page_title="Confrontos | Cartola Analyzer",
    page_icon="🆚",
    layout="wide",
)

st.title("🆚 Análise de Confrontos")

with st.sidebar:
    st.header("⚙️ Configurações")
    perfil = st.selectbox(
        "🎯 Perfil tático",
        list(PERFIS.keys()),
        index=0,
    )

df = build_atletas_df(perfil=perfil)

if df is None or df.empty:
    st.error("Sem dados disponíveis para análise de confrontos.")
    st.stop()

confrontos = montar_tabela_confrontos(df)

if confrontos is None or confrontos.empty:
    st.warning("Não foi possível carregar os confrontos da rodada.")
    st.stop()

resumo = melhores_confrontos(confrontos)

c1, c2 = st.columns(2)
with c1:
    st.metric(
        "🔥 Melhor cenário ofensivo",
        resumo.get("melhor_time_ataque", "-"),
        resumo.get("melhor_ataque_jogo", "-"),
    )
with c2:
    st.metric(
        "🛡️ Melhor cenário de SG",
        resumo.get("melhor_time_sg", "-"),
        resumo.get("melhor_sg_jogo", "-"),
    )

st.subheader("📋 Tabela de confrontos")

colunas_tabela = [
    "jogo",
    "favorito_ataque",
    "favorito_sg",
    "indice_ataque_casa",
    "indice_ataque_fora",
    "indice_sg_casa",
    "indice_sg_fora",
    "alerta",
]
colunas_tabela = [c for c in colunas_tabela if c in confrontos.columns]

st.dataframe(
    confrontos[colunas_tabela],
    use_container_width=True,
    hide_index=True,
)

st.subheader("📊 Gráfico dos confrontos")
fig = grafico_indices_confronto(confrontos)
if fig is not None:
    st.plotly_chart(fig, use_container_width=True)

st.subheader("🎯 Sugestões por confronto")

mapa_jogos = {row["jogo"]: idx for idx, row in confrontos.iterrows()}
jogo_sel = st.selectbox("Selecione um confronto", list(mapa_jogos.keys()), index=0)

row_sel = confrontos.loc[mapa_jogos[jogo_sel]]
sugestoes = sugerir_atletas_por_confronto(df, row_sel)

if sugestoes is None or sugestoes.empty:
    st.info("Sem sugestões disponíveis para esse confronto.")
else:
    st.dataframe(
        sugestoes,
        use_container_width=True,
        hide_index=True,
    )
