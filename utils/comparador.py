import pandas as pd
import plotly.graph_objects as go

RADAR_METRICAS = [
    ("ataque_norm", "Ataque"),
    ("defesa_norm", "Defesa"),
    ("base_norm", "Base"),
    ("consistencia_norm", "Consistência"),
    ("custo_beneficio_norm", "Custo-benefício"),
    ("disciplina_norm", "Disciplina"),
]


def preparar_comparacao(df: pd.DataFrame, atletas_ids: list[int]) -> pd.DataFrame:
    if df is None or df.empty or not atletas_ids:
        return pd.DataFrame()

    comp = df[df["id"].isin(atletas_ids)].copy()
    if comp.empty:
        return comp

    return comp.sort_values(["score", "media"], ascending=[False, False]).reset_index(drop=True)


def gerar_radar_comparativo(df_comp: pd.DataFrame):
    if df_comp is None or df_comp.empty:
        return go.Figure()

    categorias = [m[1] for m in RADAR_METRICAS]
    fig = go.Figure()

    for _, row in df_comp.iterrows():
        valores = [float(row.get(m[0], 0) or 0) for m in RADAR_METRICAS]
        valores.append(valores[0])
        thetas = categorias + [categorias[0]]

        fig.add_trace(go.Scatterpolar(
            r=valores,
            theta=thetas,
            fill="toself",
            name=f"{row['nome']} ({row['clube']})",
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
            )
        ),
        showlegend=True,
        margin=dict(l=30, r=30, t=30, b=30),
    )

    return fig


def tabela_comparativa(df_comp: pd.DataFrame) -> pd.DataFrame:
    if df_comp is None or df_comp.empty:
        return pd.DataFrame()

    colunas = [
        "nome", "clube", "posicao", "status", "preco", "media", "score_pct",
        "ataque_bruto", "defesa_bruto", "base_bruto", "disciplina_bruto"
    ]
    colunas = [c for c in colunas if c in df_comp.columns]

    return df_comp[colunas].copy()


def resumo_vencedores(df_comp: pd.DataFrame) -> dict:
    if df_comp is None or df_comp.empty:
        return {}

    resumo = {}

    for coluna, rotulo in [
        ("score_pct", "Melhor score"),
        ("media", "Melhor média"),
        ("ataque_bruto", "Melhor ataque"),
        ("defesa_bruto", "Melhor defesa"),
        ("base_bruto", "Melhor base"),
    ]:
        if coluna in df_comp.columns:
            idx = df_comp[coluna].astype(float).idxmax()
            resumo[rotulo] = df_comp.loc[idx, "nome"]

    return resumo
