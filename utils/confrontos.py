"""
Análise de confrontos diretos entre clubes do Cartola FC.
Calcula aproveitamento, média de gols, desempenho em casa/fora.
"""
import pandas as pd
import numpy as np
from typing import Optional
from utils.api import get_partidas, get_clubes


def _safe_get(d: dict, *keys, default=None):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k, default)
    return d


# ── construção do DataFrame de partidas ──────────────────────────────────────

def build_partidas_df(rodadas: list[int]) -> pd.DataFrame:
    """Agrega partidas de múltiplas rodadas em um DataFrame."""
    clubes_raw = get_clubes() or {}

    clubes = {
       int(k): v.get("nome", v.get("abreviacao", str(k)))
       for k, v in clubes_raw.items()
    }

    rows = []
    for rodada in rodadas:
        data = get_partidas(rodada)
        if not data:
            continue

        partidas = data.get("partidas", [])
        for partida in partidas:
            clube_casa_id = partida.get("clube_casa_id")
            clube_visitante_id = partida.get("clube_visitante_id")

            rows.append({
                "rodada": rodada,
                "clube_casa_id": clube_casa_id,
                "clube_casa": clubes.get(clube_casa_id, str(clube_casa_id)),
                "clube_visitante_id": clube_visitante_id,
                "clube_visitante": clubes.get(clube_visitante_id, str(clube_visitante_id)),
                "placar_casa": partida.get("placar_oficial_mandante"),
                "placar_visitante": partida.get("placar_oficial_visitante"),
                "valida": partida.get("valida", False),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df["placar_casa"] = pd.to_numeric(df["placar_casa"], errors="coerce")
    df["placar_visitante"] = pd.to_numeric(df["placar_visitante"], errors="coerce")

    return df


# ── confrontos diretos ────────────────────────────────────────────────────────

def historico_confronto(df: pd.DataFrame, clube_a: str, clube_b: str) -> pd.DataFrame:
    """Filtra partidas onde os dois clubes se enfrentaram."""
    mask = (
        ((df["clube_casa"] == clube_a) & (df["clube_visitante"] == clube_b)) |
        ((df["clube_casa"] == clube_b) & (df["clube_visitante"] == clube_a))
    )
    return df[mask].copy()


def resumo_confronto(hist: pd.DataFrame, clube_a: str, clube_b: str) -> dict:
    """Calcula vitórias, empates, derrotas e médias de gols."""
    if hist.empty:
        return {}

    v_a = v_b = empates = 0
    gols_a = gols_b = 0

    for _, row in hist.iterrows():
        if pd.isna(row["placar_casa"]) or pd.isna(row["placar_visitante"]):
            continue
        if row["clube_casa"] == clube_a:
            ga, gb = row["placar_casa"], row["placar_visitante"]
        else:
            ga, gb = row["placar_visitante"], row["placar_casa"]

        gols_a += ga
        gols_b += gb
        if ga > gb:
            v_a += 1
        elif gb > ga:
            v_b += 1
        else:
            empates += 1

    jogos = v_a + v_b + empates
    return {
        "clube_a": clube_a,
        "clube_b": clube_b,
        "jogos": jogos,
        f"vitórias_{clube_a}": v_a,
        "empates": empates,
        f"vitórias_{clube_b}": v_b,
        f"aproveitamento_{clube_a}": round((v_a * 3 + empates) / (jogos * 3) * 100, 1) if jogos else 0,
        f"gols_{clube_a}": gols_a,
        f"gols_{clube_b}": gols_b,
        "média_gols_por_jogo": round((gols_a + gols_b) / jogos, 2) if jogos else 0,
    }


def desempenho_casa_fora(df: pd.DataFrame, clube: str) -> dict:
    """Calcula desempenho em casa e fora para um clube."""
    casa = df[df["clube_casa"] == clube].dropna(subset=["placar_casa", "placar_visitante"])
    fora = df[df["clube_visitante"] == clube].dropna(subset=["placar_casa", "placar_visitante"])

    def stats(subset, gols_favor_col, gols_contra_col):
        if subset.empty:
            return {"jogos": 0, "v": 0, "e": 0, "d": 0, "gf": 0, "gc": 0}
        gf = subset[gols_favor_col].sum()
        gc = subset[gols_contra_col].sum()
        v = (subset[gols_favor_col] > subset[gols_contra_col]).sum()
        e = (subset[gols_favor_col] == subset[gols_contra_col]).sum()
        d = (subset[gols_favor_col] < subset[gols_contra_col]).sum()
        return {"jogos": len(subset), "v": int(v), "e": int(e), "d": int(d), "gf": int(gf), "gc": int(gc)}

    return {
        "casa": stats(casa, "placar_casa", "placar_visitante"),
        "fora": stats(fora, "placar_visitante", "placar_casa"),
    }
