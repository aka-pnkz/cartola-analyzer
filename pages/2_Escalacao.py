import streamlit as st
from utils.score_mitada import (
    build_atletas_df,
    recomendados_por_faixa,
    diagnostico_escalacao,
    resumo_posicoes_debug,
    PERFIS,
    top_por_perfil,
)

st.set_page_config(
    page_title="Escalação | Cartola Analyzer",
    page_icon="📋",
    layout="wide",
)

st.title("📋 Escalação Inteligente")

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

    formacao = st.selectbox(
        "🔢 Formação",
        ["4-3-3", "4-4-2", "3-5-2", "3-4-3"],
    )

    perfil = st.selectbox(
        "🎯 Perfil tático",
        list(PERFIS.keys()),
        index=0,
    )

    mostrar_diag = st.toggle("Mostrar diagnóstico", value=True)
    mostrar_debug = st.toggle("Mostrar debug de posições", value=False)
    mostrar_top = st.toggle("Mostrar top atletas", value=True)

df = build_atletas_df(perfil=perfil)

if df is None or df.empty:
    st.error("Sem dados disponíveis.")
    st.stop()

st.caption(f"Perfil ativo: **{perfil}**")

escalacao = recomendados_por_faixa(df, orcamento, formacao)

if escalacao is None or escalacao.empty:
    st.warning(
        "Não foi possível montar uma escalação completa com 11 jogadores + 1 técnico "
        "dentro do orçamento e da formação selecionada."
    )
else:
    qtd_jogadores = len(escalacao[escalacao["posicao"] != "Técnico"])
    gasto_total = float(escalacao["preco"].sum())
    media_total = float(escalacao["media"].sum())
    media_time = media_total / qtd_jogadores if qtd_jogadores else 0.0
    score_total = float(escalacao["score"].sum()) if "score" in escalacao.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💸 Gasto total", f"C$ {gasto_total:.2f}")
    c2.metric("📈 Média somada", f"{media_total:.1f}")
    c3.metric("📊 Média por atleta", f"{media_time:.2f}")
    c4.metric("🧠 Score total", f"{score_total:.2f}")

    st.subheader("✅ Time sugerido")

    colunas_desejadas = [
        "nome", "clube", "posicao", "status", "preco", "media",
        "score_pct", "ataque_bruto", "defesa_bruto", "base_bruto"
    ]
    colunas_exibir = [c for c in colunas_desejadas if c in escalacao.columns]

    st.dataframe(
        escalacao[colunas_exibir],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("📝 Motivo da escalação")
    for _, row in escalacao.iterrows():
        motivo = []
        if row.get("ataque_bruto", 0) > row.get("defesa_bruto", 0):
            motivo.append("força ofensiva")
        else:
            motivo.append("segurança defensiva")
        if row.get("base_bruto", 0) > 0:
            motivo.append("scout de base")
        if row.get("score_pct", 0) >= 70:
            motivo.append("score alto")
        if row.get("status_id", None) == 2:
            motivo.append("status provável")

        st.write(
            f"**{row['nome']} ({row['posicao']} - {row['clube']})**: "
            + ", ".join(motivo[:3])
        )

if mostrar_diag:
    diag = diagnostico_escalacao(df, orcamento, formacao)
    st.subheader("🩺 Diagnóstico da escalação")

    rows = []
    for pos, info in diag["posicoes"].items():
        rows.append({
            "Posição": pos,
            "Necessários": info["necessarios"],
            "Prováveis": info["provaveis"],
            "Aceitáveis": info["aceitaveis"],
            "Mais barato provável": info["mais_barato_provavel"],
            "Mais barato aceitável": info["mais_barato_aceitavel"],
            "Melhor score": info.get("melhor_score"),
        })

    st.dataframe(rows, use_container_width=True, hide_index=True)

if mostrar_top:
    st.subheader("🏆 Top atletas do perfil")
    posicao_top = st.selectbox(
        "Filtrar top por posição",
        ["Todas", "Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"],
        index=0,
    )
    pos_filtro = None if posicao_top == "Todas" else posicao_top
    top_df = top_por_perfil(df, posicao=pos_filtro, n=15)

    if top_df is not None and not top_df.empty:
        colunas_top = [
            "nome", "clube", "posicao", "status", "preco", "media",
            "score_pct", "ataque_bruto", "defesa_bruto", "base_bruto"
        ]
        colunas_top = [c for c in colunas_top if c in top_df.columns]

        st.dataframe(
            top_df[colunas_top],
            use_container_width=True,
            hide_index=True,
        )

if mostrar_debug:
    st.subheader("🧪 Debug de posições retornadas pela API")
    debug_df = resumo_posicoes_debug(df)
    st.dataframe(debug_df, use_container_width=True, hide_index=True)
