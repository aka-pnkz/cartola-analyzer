"""
Comparação lado a lado de atletas do Cartola FC.
Gera radar chart e tabela de métricas comparativas.
"""
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from typing import Optional


METRICAS = ["media", "preco", "custo_beneficio", "variacao", "jogos", "sam_pct"]
LABELS   = ["Média", "Preço", "Custo-Benefício", "Variação", "Jogos", "SAM (%)"]


def comparar_atletas(df: pd.DataFrame, ids: list[int]) -> pd.DataFrame:
    """Filtra os atletas selecionados e retorna subconjunto com métricas."""
    return df[df["id"].isin(ids)].copy()


def radar_chart(df_comp: pd.DataFrame) -> go.Figure:
    """Gera radar chart comparativo entre atletas."""
    metricas_disp = [m for m in METRICAS if m in df_comp.columns]
    labels_disp = [LABELS[METRICAS.index(m)] for m in metricas_disp]

    df_norm = df_comp[metricas_disp].copy()
    for col in metricas_disp:
        mn, mx = df_norm[col].min(), df_norm[col].max()
        if mx > mn:
            df_norm[col] = (df_norm[col] - mn) / (mx - mn)
        else:
            df_norm[col] = 0.5

    colors = [
        "#01696f", "#d19900", "#a12c7b", "#da7101",
        "#006494", "#437a22", "#7a39bb", "#a13544",
    ]

    fig = go.Figure()
    for i, (_, row) in enumerate(df_comp.iterrows()):
        vals = df_norm.loc[row.name, metricas_disp].tolist()
        vals += [vals[0]]
        cat = labels_disp + [labels_disp[0]]
        fig.add_trace(go.Scatterpolar(
            r=vals,
            theta=cat,
            fill="toself",
            name=row["nome"],
            line_color=colors[i % len(colors)],
            opacity=0.7,
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], showticklabels=False),
        ),
        showlegend=True,
        title="Comparativo de Atletas — Radar",
        margin=dict(t=60, b=20, l=20, r=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif"),
    )
    return fig


def tabela_comparativa(df_comp: pd.DataFrame) -> pd.DataFrame:
    """Retorna tabela formatada para exibição."""
    cols = ["nome", "clube", "posicao", "status", "preco", "media",
            "variacao", "jogos", "custo_beneficio", "sam_pct"]
    cols_disp = [c for c in cols if c in df_comp.columns]
    tb = df_comp[cols_disp].copy()
    tb.columns = [c.replace("_", " ").title() for c in cols_disp]
    return tb
