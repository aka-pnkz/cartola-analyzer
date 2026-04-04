import streamlit as st
from utils.score_mitada import build_atletas_df, PERFIS
from utils.comparador import (
    preparar_comparacao,
    gerar_radar_comparativo,
    tabela_comparativa,
    resumo_vencedores,
)

st.set_page_config(
    page_title="Comparador | Cartola Analyzer",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Comparador de Atletas")

with st.sidebar:
    st.header("⚙️ Configurações")
    perfil = st.selectbox(
        "🎯 Perfil tático",
        list(PERFIS.keys()),
        index=0,
    )

df = build_atletas_df(perfil=perfil)

if df is None or df.empty:
    st.error("Sem dados disponíveis para comparação.")
    st.stop()

opcoes = (
    df.sort_values(["posicao", "nome"])[["id", "nome", "posicao", "clube"]]
    .drop_duplicates()
    .reset_index(drop=True)
)

mapa_rotulos = {
    int(row["id"]): f"{row['nome']} - {row['posicao']} ({row['clube']})"
    for _, row in opcoes.iterrows()
}

ids_selecionados = st.multiselect(
    "Selecione até 6 atletas",
    options=list(mapa_rotulos.keys()),
    format_func=lambda x: mapa_rotulos[x],
    default=[],
    max_selections=6,
)

df_comp = preparar_comparacao(df, ids_selecionados)

if df_comp is None or df_comp.empty:
    st.info("Selecione ao menos 1 atleta para iniciar a comparação.")
    st.stop()

c1, c2 = st.columns([2, 1])

with c1:
    st.subheader("🕸️ Radar comparativo")
    fig = gerar_radar_comparativo(df_comp)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("🏅 Destaques")
    resumo = resumo_vencedores(df_comp)
    if resumo:
        for chave, valor in resumo.items():
            st.write(f"**{chave}:** {valor}")

st.subheader("📋 Tabela comparativa")
tabela = tabela_comparativa(df_comp)
st.dataframe(tabela, use_container_width=True, hide_index=True)
