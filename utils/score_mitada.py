"""
Cálculo do Score Anti-Mitada (SAM) para atletas do Cartola FC.
Combina: média de pontos, consistência, preço/custo-benefício,
casa/fora e tendência recente.
"""
import pandas as pd
import numpy as np
from typing import Optional
from utils.api import (
    get_atletas_mercado,
    POSICAO_MAP,
    STATUS_MAP,
    get_clubes_mapa_nome,
)

W_MEDIA        = 0.30
W_CONSISTENCIA = 0.20
W_CUSTO        = 0.20
W_CASA_FORA    = 0.15
W_TENDENCIA    = 0.15


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)


def build_atletas_df() -> pd.DataFrame:
    """Baixa o mercado e retorna um DataFrame limpo com todos os atletas."""
    data = get_atletas_mercado()
    if not data:
        return pd.DataFrame()

    atletas = data.get("atletas", [])

    # tenta primeiro buscar nomes via endpoint /clubes
    clubes = get_clubes_mapa_nome()

    # fallback: usa o dicionário de clubes que já vem no /atletas/mercado
    if not clubes:
        clubes_raw = data.get("clubes", {})
        clubes = {
            int(k): v.get("nome_curto", v.get("abreviacao", str(k)))
            for k, v in clubes_raw.items()
        }

    rows = []
    for a in atletas:
        scouts = a.get("scout", {})
        gols = scouts.get("G", 0) or 0
        assistencias = scouts.get("A", 0) or 0
        faltas_cometidas = scouts.get("FC", 0) or 0
        cartao_amarelo = scouts.get("CA", 0) or 0
        cartao_vermelho = scouts.get("CV", 0) or 0
        defesas_dificeis = scouts.get("DD", 0) or 0
        finalizacoes = scouts.get("FT", 0) or 0

        clube_id = a.get("clube_id")

        rows.append({
            "id": a.get("atleta_id"),
            "nome": a.get("apelido", "?"),
            "clube_id": clube_id,
            "clube": clubes.get(clube_id, str(clube_id)),
            "posicao_id": a.get("posicao_id"),
            "posicao": POSICAO_MAP.get(a.get("posicao_id"), "?"),
            "status_id": a.get("status_id"),
            "status": STATUS_MAP.get(a.get("status_id"), "?"),
            "preco": a.get("preco_num", 0) or 0,
            "variacao": a.get("variacao_num", 0) or 0,
            "media": a.get("media_num", 0) or 0,
            "jogos": a.get("jogos_num", 0) or 0,
            "pontos_rodada": a.get("pontos_num", 0) or 0,
            "gols": gols,
            "assistencias": assistencias,
            "faltas": faltas_cometidas,
            "amarelos": cartao_amarelo,
            "vermelhos": cartao_vermelho,
            "defesas_dificeis": defesas_dificeis,
            "finalizacoes": finalizacoes,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df[df["preco"] > 0].copy()
    df["custo_beneficio"] = df["media"] / df["preco"].replace(0, np.nan)
    df["custo_beneficio"] = df["custo_beneficio"].fillna(0)
    return df


def calcular_sam(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o Score Anti-Mitada (SAM) para cada atleta.
    Retorna o DataFrame com coluna 'sam' adicionada.
    """
    if df.empty:
        return df

    df = df.copy()

    for col in ["media", "custo_beneficio", "variacao"]:
        df[f"{col}_norm"] = df.groupby("posicao_id")[col].transform(_minmax)

    df["consistencia_norm"] = _minmax(-df["variacao"].abs())
    df["tendencia_norm"] = _minmax(df["variacao"])
    df["casa_fora_norm"] = _minmax(df["variacao"])

    df["sam"] = (
        W_MEDIA        * df["media_norm"] +
        W_CONSISTENCIA * df["consistencia_norm"] +
        W_CUSTO        * df["custo_beneficio_norm"] +
        W_CASA_FORA    * df["casa_fora_norm"] +
        W_TENDENCIA    * df["tendencia_norm"]
    ).round(4)

    df["sam_pct"] = (df["sam"] * 100).round(1)
    df = df.sort_values("sam", ascending=False).reset_index(drop=True)
    df["ranking"] = df.index + 1
    return df


def top_por_posicao(df: pd.DataFrame, posicao: str, top_n: int = 10) -> pd.DataFrame:
    return df[df["posicao"] == posicao].head(top_n)


def recomendados_por_faixa(df: pd.DataFrame, orcamento: float, formacao: str = "4-3-3") -> pd.DataFrame:
    """
    Sugere escalação dentro de um orçamento respeitando a formação.
    Inclui 11 jogadores + 1 técnico.
    Formações suportadas: '4-3-3', '4-4-2', '3-5-2', '3-4-3'.
    """
    formacoes = {
        "4-3-3": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 3, "Atacante": 3},
        "4-4-2": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 4, "Atacante": 2},
        "3-5-2": {"Goleiro": 1, "Lateral": 1, "Zagueiro": 2, "Meia": 5, "Atacante": 2},
        "3-4-3": {"Goleiro": 1, "Lateral": 1, "Zagueiro": 2, "Meia": 4, "Atacante": 3},
    }

    slots = formacoes.get(formacao, formacoes["4-3-3"])

    selecionados = []
    gasto = 0.0
    df_sorted = df.sort_values("sam", ascending=False)

    # 11 jogadores
    for posicao, qtd in slots.items():
        candidatos = df_sorted[
            (df_sorted["posicao"] == posicao) &
            (df_sorted["status_id"] == 2) &
            (~df_sorted["id"].isin([a["id"] for a in selecionados]))
        ].head(qtd * 10)

        for _, row in candidatos.iterrows():
            if len([a for a in selecionados if a["posicao"] == posicao]) >= qtd:
                break
            if gasto + row["preco"] <= orcamento:
                selecionados.append(row.to_dict())
                gasto += row["preco"]

    # 1 técnico
    tecnicos = df_sorted[
        (df_sorted["posicao"] == "Técnico") &
        (df_sorted["status_id"] == 2) &
        (~df_sorted["id"].isin([a["id"] for a in selecionados]))
    ].head(10)

    for _, row in tecnicos.iterrows():
        if gasto + row["preco"] <= orcamento:
            selecionados.append(row.to_dict())
            gasto += row["preco"]
            break

    result = pd.DataFrame(selecionados)

    if not result.empty:
        result["gasto_acumulado"] = result["preco"].cumsum()

    return result
