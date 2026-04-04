import streamlit as st
import pandas as pd

from utils.score_mitada import build_atletas_df, PERFIS, top_por_perfil
from utils.alertas import detectar_alertas, filtrar_alertas

st.set_page_config(
    page_title="Cartola Analyzer",
    page_icon="⚽",
    layout="wide",
)

st.title("⚽ Cartola Analyzer")
st.caption("Análise tática, comparação e alertas para decisões mais inteligentes.")

with st.sidebar:
    st.header("⚙️ Configurações")
    perfil = st.selectbox(
        "🎯 Perfil tático",
        list(PERFIS.keys()),
        index=0,
    )

df = build_atletas_df(perfil=perfil)

if df is None or df.empty:
    st.error("Não foi possível carregar os dados do mercado.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Atletas", int(len(df)))
c2.metric("Elegíveis", int(df["elegivel"].sum()) if "elegivel" in df.columns else 0)
c3.metric("Preço médio", f"C$ {df['preco'].mean():.2f}" if "preco" in df.columns else "N/A")
c4.metric("Score médio", f"{df['score_pct'].mean():.1f}" if "score_pct" in df.columns else "N/A")

st.subheader("🏆 Top 15 do perfil")

posicao_top = st.selectbox(
    "Filtrar por posição",
    ["Todas", "Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"],
    index=0,
)

pos_filtro = None if posicao_top == "Todas" else posicao_top
top_df = top_por_perfil(df, posicao=pos_filtro, n=15)

if top_df is None or top_df.empty:
    st.info("Nenhum atleta encontrado para o filtro atual.")
else:
    colunas_top = [
        "nome",
        "clube",
        "posicao",
        "status",
        "preco",
        "media",
        "score_pct",
        "ataque_bruto",
        "defesa_bruto",
        "base_bruto",
    ]
    colunas_top = [c for c in colunas_top if c in top_df.columns]

    st.dataframe(
        top_df[colunas_top],
        use_container_width=True,
        hide_index=True,
    )

st.subheader("🚨 Alertas do mercado")

alertas = detectar_alertas(df)

if alertas is None or alertas.empty:
    st.info("Nenhum alerta encontrado no momento.")
else:
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
    else:
        colunas_alertas = [
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
        colunas_alertas = [c for c in colunas_alertas if c in alertas_filtrados.columns]

        st.dataframe(
            alertas_filtrados[colunas_alertas],
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
