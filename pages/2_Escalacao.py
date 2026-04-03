"""
Página 2 — Escalação Inteligente
Monta time ideal respeitando orçamento e formação com base no SAM.
"""
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.score_mitada import build_atletas_df, calcular_sam, recomendados_por_faixa, top_por_posicao
from utils.exportacao import download_button_data

st.set_page_config(page_title="Escalação | Cartola Analyzer", page_icon="📋", layout="wide")
st.title("📋 Escalação Inteligente")

@st.cache_data(ttl=300, show_spinner=False)
def load():
    return calcular_sam(build_atletas_df())

with st.spinner("Carregando atletas..."):
    df = load()

if df.empty:
    st.error("Sem dados disponíveis.")
    st.stop()

# ── filtros ─────────────────────────────────────────────────────────────────
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
    formacao = st.selectbox("🔢 Formação", ["4-3-3", "4-4-2", "3-5-2", "3-4-3"])
    apenas_provaveis = st.toggle("✅ Apenas atletas prováveis", value=True)
    posicao_filtro = st.multiselect(
        "📌 Filtrar posição", df["posicao"].unique().tolist(), default=[]
    )
    preco_max = st.number_input("💵 Preço máximo por atleta", min_value=1.0, max_value=100.0, value=30.0, step=0.5)

# ── recomendação automática ─────────────────────────────────────────────────
st.subheader(f"🤖 Time Recomendado — {formacao} | Orçamento: C$ {orcamento:.0f}")

df_filtrado = df.copy()
if apenas_provaveis:
    df_filtrado = df_filtrado[df_filtrado["status_id"] == 2]

escalacao = recomendados_por_faixa(df_filtrado, orcamento, formacao)

if escalacao.empty:
    st.warning("Não foi possível montar escalação com os critérios selecionados.")
else:
    total_gasto = escalacao["preco"].sum()
    total_media = escalacao["media"].sum()

    m1, m2, m3 = st.columns(3)
    m1.metric("💸 Gasto Total", f"C$ {total_gasto:.1f}", f"{orcamento - total_gasto:.1f} restante")
    m2.metric("📈 Soma das Médias", f"{total_media:.1f} pts")
    qtd_jogadores = len(escalacao[escalacao["posicao"] != "Técnico"]) if not escalacao.empty else 0
    qtd_tecnicos = len(escalacao[escalacao["posicao"] == "Técnico"]) if not escalacao.empty else 0
    m3.metric("👥 Escalação", f"{qtd_jogadores} jogadores + {qtd_tecnicos} técnico")

    cols_show = ["nome", "clube", "posicao", "status", "preco", "media", "sam_pct"]
    cols_show = [c for c in cols_show if c in escalacao.columns]
    st.dataframe(escalacao[cols_show].rename(columns={
        "nome": "Atleta", "clube": "Clube", "posicao": "Posição",
        "status": "Status", "preco": "Preço (C$)", "media": "Média", "sam_pct": "SAM (%)",
    }), use_container_width=True, hide_index=True)

    fig = px.bar(
        escalacao, x="nome", y="preco", color="posicao",
        labels={"nome": "", "preco": "Preço (C$)"},
        color_discrete_sequence=["#01696f","#d19900","#a12c7b","#da7101","#006494","#437a22"],
        title="Distribuição de Preços na Escalação",
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

    data, fname, mime = download_button_data(escalacao[cols_show], "xlsx")
    st.download_button("📥 Baixar Escalação (Excel)", data=data, file_name="escalacao.xlsx", mime=mime)

st.divider()

# ── explorador manual por posição ─────────────────────────────────────────
st.subheader("🔎 Explorador por Posição")
pos_sel = st.selectbox("Posição", df["posicao"].unique())
top_n = st.slider("Top N", 5, 30, 15)

df_pos = df.copy()
if posicao_filtro:
    df_pos = df_pos[df_pos["posicao"].isin(posicao_filtro)]
df_pos = df_pos[df_pos["preco"] <= preco_max]
resultado = top_por_posicao(df_pos, pos_sel, top_n)

if resultado.empty:
    st.info("Nenhum atleta encontrado com esses filtros.")
else:
    st.dataframe(resultado[["nome","clube","status","preco","media","variacao","jogos","sam_pct"]].rename(
        columns={"nome":"Atleta","clube":"Clube","status":"Status","preco":"Preço","media":"Média",
                 "variacao":"Variação","jogos":"Jogos","sam_pct":"SAM (%)"}
    ), use_container_width=True, hide_index=True)
