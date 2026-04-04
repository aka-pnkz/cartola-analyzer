"""
Cálculo do Score Anti-Mitada (SAM) para atletas do Cartola FC.
"""
import pandas as pd
import numpy as np
from utils.api import get_atletas_mercado, POSICAO_MAP, STATUS_MAP, get_clubes_mapa_curto

W_MEDIA = 0.30
W_CONSISTENCIA = 0.20
W_CUSTO = 0.20
W_CASA_FORA = 0.15
W_TENDENCIA = 0.15


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)


def calcular_sam(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula o Score Anti-Mitada (SAM) para um DataFrame de atletas.
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
        W_MEDIA * df["media_norm"] +
        W_CONSISTENCIA * df["consistencia_norm"] +
        W_CUSTO * df["custo_beneficio_norm"] +
        W_CASA_FORA * df["casa_fora_norm"] +
        W_TENDENCIA * df["tendencia_norm"]
    ).round(4)

    df["sam_pct"] = (df["sam"] * 100).round(1)
    df = df.sort_values("sam", ascending=False).reset_index(drop=True)
    df["ranking"] = df.index + 1
    return df


def build_atletas_df() -> pd.DataFrame:
    data = get_atletas_mercado()
    if not data:
        return pd.DataFrame()

    atletas = data.get("atletas", [])
    clubes = get_clubes_mapa_curto()

    if not clubes:
        clubes_raw = data.get("clubes", {})
        clubes = {
            int(k): v.get("nome", v.get("nome_curto", v.get("abreviacao", str(k))))
            for k, v in clubes_raw.items()
        }

    rows = []
    for a in atletas:
        scouts = a.get("scout", {})
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
            "gols": scouts.get("G", 0) or 0,
            "assistencias": scouts.get("A", 0) or 0,
            "faltas": scouts.get("FC", 0) or 0,
            "amarelos": scouts.get("CA", 0) or 0,
            "vermelhos": scouts.get("CV", 0) or 0,
            "defesas_dificeis": scouts.get("DD", 0) or 0,
            "finalizacoes": scouts.get("FT", 0) or 0,
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df[df["preco"] > 0].copy()
    df["custo_beneficio"] = df["media"] / df["preco"].replace(0, np.nan)
    df["custo_beneficio"] = df["custo_beneficio"].fillna(0)

    return calcular_sam(df)


def recomendados_por_faixa(df: pd.DataFrame, orcamento: float, formacao: str = "4-3-3") -> pd.DataFrame:
    formacoes = {
        "4-3-3": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 3, "Atacante": 3, "Técnico": 1},
        "4-4-2": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 4, "Atacante": 2, "Técnico": 1},
        "3-5-2": {"Goleiro": 1, "Lateral": 0, "Zagueiro": 3, "Meia": 5, "Atacante": 2, "Técnico": 1},
        "3-4-3": {"Goleiro": 1, "Lateral": 0, "Zagueiro": 3, "Meia": 4, "Atacante": 3, "Técnico": 1},
    }

    slots = formacoes.get(formacao, formacoes["4-3-3"])

    def montar_time(df_base: pd.DataFrame) -> pd.DataFrame:
        df_sorted = df_base.sort_values(
            ["status_id", "sam", "media"],
            ascending=[True, False, False]
        ).copy()

        if df_sorted.empty:
            return pd.DataFrame()

        def custo_minimo_restante(df_ref, faltantes, ids_ignorados):
            total = 0.0
            for pos, qtd in faltantes.items():
                if qtd <= 0:
                    continue

                pool = df_ref[
                    (df_ref["posicao"] == pos) &
                    (~df_ref["id"].isin(ids_ignorados))
                ].sort_values("preco", ascending=True)

                if len(pool) < qtd:
                    return None

                total += pool.head(qtd)["preco"].sum()

            return float(total)

        selecionados = []
        ids_sel = set()
        gasto = 0.0
        faltantes = slots.copy()
        ordem_posicoes = ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"]

        for posicao in ordem_posicoes:
            qtd = slots.get(posicao, 0)
            if qtd == 0:
                continue

            candidatos = df_sorted[
                (df_sorted["posicao"] == posicao) &
                (~df_sorted["id"].isin(ids_sel))
            ].copy()

            escolhidos_pos = 0

            for _, row in candidatos.iterrows():
                if escolhidos_pos >= qtd:
                    break

                preco_atual = float(row["preco"])
                faltantes_teste = faltantes.copy()
                faltantes_teste[posicao] -= 1
                ids_teste = ids_sel | {row["id"]}
                custo_restante = custo_minimo_restante(df_sorted, faltantes_teste, ids_teste)

                if custo_restante is None:
                    continue

                if gasto + preco_atual + custo_restante <= orcamento:
                    selecionados.append(row.to_dict())
                    ids_sel.add(row["id"])
                    gasto += preco_atual
                    escolhidos_pos += 1
                    faltantes[posicao] -= 1

            if escolhidos_pos < qtd:
                return pd.DataFrame()

        result = pd.DataFrame(selecionados)

        if not result.empty:
            result["gasto_acumulado"] = result["preco"].cumsum()

        if len(result[result["posicao"] != "Técnico"]) != 11 or len(result[result["posicao"] == "Técnico"]) != 1:
            return pd.DataFrame()

        ordem = {
            "Goleiro": 1,
            "Lateral": 2,
            "Zagueiro": 3,
            "Meia": 4,
            "Atacante": 5,
            "Técnico": 6,
        }

        return result.sort_values(
            by=["posicao"],
            key=lambda s: s.map(ordem)
        ).reset_index(drop=True)

    # tentativa 1: apenas prováveis
    df_provaveis = df[df["status_id"] == 2].copy()
    resultado = montar_time(df_provaveis)

    if not resultado.empty:
        return resultado

    # tentativa 2: prováveis + dúvidas, suspensos e lesionados continuam fora
    df_fallback = df[df["status_id"].isin([2, 3])].copy()
    resultado = montar_time(df_fallback)

    if not resultado.empty:
        return resultado

    # tentativa 3: qualquer atleta válido de mercado
    df_final = df[~df["status_id"].isin([5, 6, 7])].copy()
    return montar_time(df_final)
