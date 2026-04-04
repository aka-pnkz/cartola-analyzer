"""
Cálculo do Score Anti-Mitada (SAM) para atletas do Cartola FC.
Versão revisada com depuração de posições, diagnóstico de escalação
e fallback mais flexível para montagem do time.
"""

import pandas as pd
import numpy as np

from utils.api import (
    get_atletas_mercado,
    POSICAO_MAP,
    STATUS_MAP,
    get_clubes_mapa_curto,
)

W_MEDIA = 0.30
W_CONSISTENCIA = 0.20
W_CUSTO = 0.20
W_CASA_FORA = 0.15
W_TENDENCIA = 0.15

FORMACOES = {
    "4-3-3": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 3, "Atacante": 3, "Técnico": 1},
    "4-4-2": {"Goleiro": 1, "Lateral": 2, "Zagueiro": 2, "Meia": 4, "Atacante": 2, "Técnico": 1},
    "3-5-2": {"Goleiro": 1, "Lateral": 0, "Zagueiro": 3, "Meia": 5, "Atacante": 2, "Técnico": 1},
    "3-4-3": {"Goleiro": 1, "Lateral": 0, "Zagueiro": 3, "Meia": 4, "Atacante": 3, "Técnico": 1},
}

ORDEM_POS = ["Goleiro", "Lateral", "Zagueiro", "Meia", "Atacante", "Técnico"]

ORDEM_MAP = {
    "Goleiro": 1,
    "Lateral": 2,
    "Zagueiro": 3,
    "Meia": 4,
    "Atacante": 5,
    "Técnico": 6,
}


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(0.5, index=series.index)
    return (series - mn) / (mx - mn)


def _resolver_posicao(atleta: dict) -> tuple[int, str]:
    pos_id = atleta.get("posicao_id")

    pos_obj = atleta.get("posicao")
    if isinstance(pos_obj, dict):
        nome = pos_obj.get("nome") or pos_obj.get("abreviacao")
        if nome:
            return pos_id, nome

    return pos_id, POSICAO_MAP.get(pos_id, f"Posição {pos_id}")


def calcular_sam(df: pd.DataFrame) -> pd.DataFrame:
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
    df = df.sort_values(["sam", "media"], ascending=[False, False]).reset_index(drop=True)
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
        posicao_id, posicao_nome = _resolver_posicao(a)

        rows.append({
            "id": a.get("atleta_id"),
            "nome": a.get("apelido", "?"),
            "clube_id": clube_id,
            "clube": clubes.get(clube_id, str(clube_id)),
            "posicao_id": posicao_id,
            "posicao": posicao_nome,
            "status_id": a.get("status_id"),
            "status": STATUS_MAP.get(a.get("status_id"), f"Status {a.get('status_id')}"),
            "preco": float(a.get("preco_num", 0) or 0),
            "variacao": float(a.get("variacao_num", 0) or 0),
            "media": float(a.get("media_num", 0) or 0),
            "jogos": int(a.get("jogos_num", 0) or 0),
            "pontos_rodada": float(a.get("pontos_num", 0) or 0),
            "gols": int(scouts.get("G", 0) or 0),
            "assistencias": int(scouts.get("A", 0) or 0),
            "faltas": int(scouts.get("FC", 0) or 0),
            "amarelos": int(scouts.get("CA", 0) or 0),
            "vermelhos": int(scouts.get("CV", 0) or 0),
            "defesas_dificeis": int(scouts.get("DD", 0) or 0),
            "finalizacoes": int(scouts.get("FT", 0) or 0),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df[df["preco"] > 0].copy()
    df["custo_beneficio"] = (df["media"] / df["preco"].replace(0, np.nan)).fillna(0)

    return calcular_sam(df)


def resumo_posicoes_debug(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    return (
        df.groupby(["posicao_id", "posicao"])
        .agg(
            qtd=("id", "count"),
            menor_preco=("preco", "min"),
            maior_preco=("preco", "max"),
        )
        .reset_index()
        .sort_values(["posicao_id", "posicao"])
    )


def diagnostico_escalacao(df: pd.DataFrame, orcamento: float, formacao: str = "4-3-3") -> dict:
    slots = FORMACOES.get(formacao, FORMACOES["4-3-3"])
    diag = {
        "orcamento": float(orcamento),
        "formacao": formacao,
        "posicoes": {},
    }

    for pos, qtd in slots.items():
        pool = df[df["posicao"] == pos].copy()
        prov = pool[pool["status_id"] == 2].copy()
        aceit = pool[pool["preco"] > 0].copy()

        diag["posicoes"][pos] = {
            "necessarios": int(qtd),
            "provaveis": int(len(prov)),
            "aceitaveis": int(len(aceit)),
            "mais_barato_provavel": float(prov["preco"].min()) if not prov.empty else None,
            "mais_barato_aceitavel": float(aceit["preco"].min()) if not aceit.empty else None,
        }

    return diag


def _montar_guloso_com_reserva(
    df_base: pd.DataFrame,
    orcamento: float,
    slots: dict,
    status_prioridade: bool = True,
) -> pd.DataFrame:
    df_ref = df_base.copy()

    if status_prioridade and "status_id" in df_ref.columns:
        prioridade = df_ref["status_id"].map({
            2: 0,
            3: 1,
            7: 2,
            5: 3,
            6: 4,
        }).fillna(5)

        df_ref = (
            df_ref.assign(_prioridade_status=prioridade)
            .sort_values(["_prioridade_status", "sam", "media"], ascending=[True, False, False])
        )
    else:
        df_ref = df_ref.sort_values(["sam", "media"], ascending=[False, False])

    def custo_minimo_restante(faltantes: dict, ids_ignorados: set) -> float | None:
        total = 0.0

        for pos, qtd in faltantes.items():
            if qtd <= 0:
                continue

            pool = df_ref[
                (df_ref["posicao"] == pos) &
                (~df_ref["id"].isin(ids_ignorados)) &
                (df_ref["preco"] > 0)
            ].sort_values("preco", ascending=True)

            if len(pool) < qtd:
                return None

            total += float(pool.head(qtd)["preco"].sum())

        return total

    selecionados = []
    ids_sel = set()
    gasto = 0.0
    faltantes = slots.copy()

    for posicao in ORDEM_POS:
        qtd = slots.get(posicao, 0)
        if qtd <= 0:
            continue

        candidatos = df_ref[
            (df_ref["posicao"] == posicao) &
            (~df_ref["id"].isin(ids_sel)) &
            (df_ref["preco"] > 0)
        ]

        escolhidos = 0

        for _, row in candidatos.iterrows():
            if escolhidos >= qtd:
                break

            faltantes_teste = faltantes.copy()
            faltantes_teste[posicao] -= 1
            ids_teste = ids_sel | {row["id"]}
            restante = custo_minimo_restante(faltantes_teste, ids_teste)

            if restante is None:
                continue

            preco = float(row["preco"])

            if gasto + preco + restante <= float(orcamento):
                selecionados.append(row.to_dict())
                ids_sel.add(row["id"])
                gasto += preco
                escolhidos += 1
                faltantes[posicao] -= 1

        if escolhidos < qtd:
            return pd.DataFrame()

    result = pd.DataFrame(selecionados)
    if result.empty:
        return result

    result["gasto_acumulado"] = result["preco"].cumsum()

    jogadores = len(result[result["posicao"] != "Técnico"])
    tecnicos = len(result[result["posicao"] == "Técnico"])

    if jogadores != 11 or tecnicos != 1:
        return pd.DataFrame()

    return result.sort_values(
        by=["posicao"],
        key=lambda s: s.map(ORDEM_MAP)
    ).reset_index(drop=True)


def recomendados_por_faixa(df: pd.DataFrame, orcamento: float, formacao: str = "4-3-3") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    slots = FORMACOES.get(formacao, FORMACOES["4-3-3"])

    tentativas = [
        df[df["status_id"] == 2].copy(),
        df[df["status_id"].isin([2, 3, 7])].copy(),
        df[df["preco"] > 0].copy(),
    ]

    for tentativa in tentativas:
        result = _montar_guloso_com_reserva(
            tentativa,
            orcamento,
            slots,
            status_prioridade=True,
        )
        if not result.empty:
            return result

    return pd.DataFrame()
