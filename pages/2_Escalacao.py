import streamlit as st
from utils.score_mitada import build_atletas_df, recomendados_por_faixa

st.set_page_config(page_title="Escalação | Cartola Analyzer", page_icon="📋", layout="wide")
st.title("📋 Escalação Inteligente")

df = build_atletas_df()
if df.empty:
    st.error("Sem dados disponíveis.")
    st.stop()

with st.sidebar:
    st.header("⚙️ Configurações")

    orcamento = st.number_input(
        "💰 Orçamento (C$)",
        min_value=50.0,
        max_value=200.0,
        value=122.28,
        step=0.01,
        format="%.2f",
    )
    orcamento = round(orcamento, 2)

    formacao = st.selectbox("🔢 Formação", ["4-3-3", "4-4-2", "3-5-2", "3-4-3"])

escalacao = recomendados_por_faixa(df, orcamento, formacao)

if escalacao.empty:
    st.warning(
        "Não foi possível montar uma escalação completa com 11 jogadores + 1 técnico "
        "dentro do orçamento e da formação selecionada."
    )
else:
    qtd_jogadores = len(escalacao[escalacao["posicao"] != "Técnico"])
    qtd_tecnicos = len(escalacao[escalacao["posicao"] == "Técnico"])

    col1, col2, col3 = st.columns(3)
    col1.metric("💸 Gasto total", f"C$ {escalacao['preco'].sum():.2f}")
    col2.metric("📈 Média somada", f"{escalacao['media'].sum():.1f}")
    col3.metric("👥 Escalação", f"{qtd_jogadores} jogadores + {qtd_tecnicos} técnico")

    st.dataframe(
        escalacao[["nome", "clube", "posicao", "status", "preco", "media", "sam_pct"]],
        use_container_width=True,
        hide_index=True,
    )
