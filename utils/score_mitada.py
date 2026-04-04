import pandas as pd
import numpy as np

from utils.api import (
    get_atletas_mercado,
    POSICAO_MAP,
    STATUS_MAP,
    get_clubes_mapa_curto,
)

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

PERFIS = {
    "Equilibrado": {
        "ataque": 0.22,
        "defesa": 0.20,
        "base": 0.18,
        "consistencia": 0.16,
        "custo_beneficio": 0.12,
        "tendencia": 0.07,
        "disciplina": 0.05,
    },
    "Ofensivo": {
        "ataque": 0.38,
        "defesa": 0.08,
        "base": 0.16,
        "consistencia": 0.12,
        "custo_beneficio": 0.10,
        "tendencia": 0.10,
        "disciplina": 0.06,
    },
    "Defensivo": {
        "ataque": 0.08,
        "defesa": 0.38,
        "base": 0.18,
        "consistencia": 0.14,
        "custo_beneficio": 0.10,
        "tendencia": 0.06,
        "disciplina": 0.06,
    },
    "Anti-mitada": {
        "ataque": 0.12,
        "defesa": 0.18,
        "base": 0.26,
        "consistencia": 0.22,
        "custo_beneficio": 0.12,
        "tendencia": 0.04,
        "disciplina": 0.06,
    },
    "Valorização": {
        "ataque": 0.12,
        "defesa": 0.12,
        "base": 0.14,
        "consistencia": 0.12,
        "custo_beneficio": 0.24,
        "tendencia": 0.20,
        "disciplina": 0.06,
    },
}


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
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


def _elegivel_para_escalar(row: pd.Series) -> bool:
    status_id = row.get("status_id")
    preco = float(row.get("preco", 0) or 0)

    if preco <= 0:
        return False

    if status_id in [5, 6]:
        return False

    return True


def _prioridade_status(status_id):
    mapa = {
        2: 0,
        3: 1,
        7: 2,
        None: 3,
    }
    return mapa.get(status_id, 3)


def _normalizar_por_posicao(df: pd.DataFrame, coluna_ou_serie) -> pd.Series:
    if isinstance(coluna_ou_serie, str):
        serie = df[coluna_ou_serie]
    else:
        serie = pd.Series(coluna_ou_serie, index=df.index)

    aux = pd.DataFrame({
        "posicao_id": df["posicao_id"],
        "_valor": serie.fillna(0),
    })

    return aux.groupby("posicao_id")["_valor"].transform(_minmax)


def calcular_metricas_taticas(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    for c in [
        "gols", "assistencias", "finalizacoes", "faltas",
        "amarelos", "vermelhos", "defesas_dificeis",
        "desarmes", "saldo_gols", "faltas_sofridas",
        "finalizacoes_defendidas", "finalizacoes_fora"
    ]:
        if c not in df.columns:
            df[c] = 0

    df["ataque_bruto"] = (
        df["gols"] * 8.0 +
        df["assistencias"] * 5.0 +
        df["finalizacoes"] * 1.2 +
        df["finalizacoes_defendidas"] * 1.2 +
        df["finalizacoes_fora"] * 0.8
    )

    df["defesa_bruto"] = (
        df["desarmes"] * 1.5 +
        df["defesas_dificeis"] * 1.3 +
        df["saldo_gols"] * 5.0
    )

    df["base_bruto"] = (
        df["desarmes"] * 1.5 +
        df["faltas_sofridas"] * 0.5 +
        df["finalizacoes_defendidas"] * 1.2 +
        df["finalizacoes_fora"] * 0.8 +
        df["defesas_dificeis"] * 1.3
    )

    df["disciplina_bruto"] = (
        df["amarelos"] * 1.0 +
        df["vermelhos"] * 3.0 +
        df["faltas"] * 0.3
    )

    df["custo_beneficio"] = (df["media"] / df["preco"].replace(0, np.nan)).fillna(0)

    df["ataque_norm"] = _normalizar_por_posicao(df, "ataque_bruto")
    df["defesa_norm"] = _normalizar_por_posicao(df, "defesa_bruto")
    df["base_norm"] = _normalizar_por_posicao(df, "base_bruto")
    df["disciplina_norm"] = _normalizar_por_posicao(df, -df["disciplina_bruto"])
    df["consistencia_norm"] = _normalizar_por_posicao(df, -df["variacao"].abs())
    df["custo_beneficio_norm"] = _normalizar_por_posicao(df, "custo_beneficio")
    df["tendencia_norm"] = _normalizar_por_posicao(df, "variacao")
    df["media_norm"] = _normalizar_por_posicao(df, "media")

    return df


def calcular_score_perfil(df: pd.DataFrame, perfil: str = "Equilibrado") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = calcular_metricas_taticas(df)
    pesos = PERFIS.get(perfil, PERFIS["Equilibrado"])

    df["score"] = (
        pesos["ataque"] * df["ataque_norm"] +
        pesos["defesa"] * df["defesa_norm"] +
        pesos["base"] * df["base_norm"] +
        pesos["consistencia"] * ((df["consistencia_norm"] + df["media_norm"]) / 2) +
        pesos["custo_beneficio"] * df["custo_beneficio_norm"] +
        pesos["tendencia"] * df["tendencia_norm"] +
        pesos["disciplina"] * df["disciplina_norm"]
    ).round(4)

    df["score_pct"] = (df["score"] * 100).round(1)
    df = df.sort_values(["score", "media"], ascending=[False, False]).reset_index(drop=True)
    df["ranking"] = df.index + 1

    return df


def build_atletas_df(perfil: str = "Equilibrado") -> pd.DataFrame:
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
            "defesas_dificeis": int(scouts.get("DE", scouts.get("DD", 0)) or 0),
            "desarmes": int(scouts.get("DS", 0) or 0),
            "saldo_gols": int(scouts.get("SG", 0) or 0),
            "faltas_sofridas": int(scouts.get("FS", 0) or 0),
            "finalizacoes": int(scouts.get("FT", 0) or 0),
            "finalizacoes_defendidas": int(scouts.get("FD", 0) or 0),
            "finalizacoes_fora": int(scouts.get("FF", 0) or 0),
        })

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    df = df[df["preco"] > 0].copy()
    df["elegivel"] = df.apply(_elegivel_para_escalar, axis=1)

    return calcular_score_perfil(df, perfil=perfil)


def resumo_posicoes_debug(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    return (
        df.groupby(["posicao_id", "posicao"])
        .agg(
            qtd=("id", "count"),
            elegiveis=("elegivel", "sum"),
            menor_preco=("preco", "min"),
            maior_preco=("preco", "max"),
            media_score=("score", "mean"),
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
        aceit = pool[pool["elegivel"] == True].copy()

        diag["posicoes"][pos] = {
            "necessarios": int(qtd),
            "provaveis": int(len(prov)),
            "aceitaveis": int(len(aceit)),
            "mais_barato_provavel": float(prov["preco"].min()) if not prov.empty else None,
            "mais_barato_aceitavel": float(aceit["preco"].min()) if not aceit.empty else None,
            "melhor_score": float(aceit["score"].max()) if not aceit.empty else None,
        }

    return diag


def _montar_base_mais_barata(df: pd.DataFrame, slots: dict) -> pd.DataFrame:
    escolhidos = []
    ids_sel = set()

    for posicao in ORDEM_POS:
        qtd = slots.get(posicao, 0)
        if qtd <= 0:
            continue

        pool = df[
            (df["posicao"] == posicao) &
            (df["elegivel"] == True) &
            (~df["id"].isin(ids_sel))
        ].sort_values(["preco", "score"], ascending=[True, False])

        if len(pool) < qtd:
            return pd.DataFrame()

        escolha = pool.head(qtd).copy()
        escolhidos.append(escolha)
        ids_sel.update(escolha["id"].tolist())

    if not escolhidos:
        return pd.DataFrame()

    return pd.concat(escolhidos, ignore_index=True)


def _aplicar_upgrades(base: pd.DataFrame, universo: pd.DataFrame, orcamento: float) -> pd.DataFrame:
    time = base.copy()
    gasto_atual = float(time["preco"].sum())

    if gasto_atual > float(orcamento):
        return pd.DataFrame()

    saldo = float(orcamento) - gasto_atual

    while True:
        melhor_delta_score = 0
        melhor_troca = None

        for idx, atual in time.iterrows():
            pos = atual["posicao"]
            atuais_ids = set(time["id"].tolist())

            candidatos = universo[
                (universo["posicao"] == pos) &
                (universo["elegivel"] == True) &
                (~universo["id"].isin(atuais_ids - {atual["id"]}))
            ].copy()

            if candidatos.empty:
                continue

            candidatos["delta_preco"] = candidatos["preco"] - atual["preco"]
            candidatos["delta_score"] = candidatos["score"] - atual["score"]

            candidatos = candidatos[
                (candidatos["delta_preco"] <= saldo) &
                (candidatos["delta_score"] > 0)
            ].copy()

            if candidatos.empty:
                continue

            candidatos["eficiencia_upgrade"] = (
                candidatos["delta_score"] / candidatos["delta_preco"].replace(0, 0.0001)
            )

            melhor_candidato = candidatos.sort_values(
                ["delta_score", "eficiencia_upgrade", "score"],
                ascending=[False, False, False]
            ).iloc[0]

            if float(melhor_candidato["delta_score"]) > melhor_delta_score:
                melhor_delta_score = float(melhor_candidato["delta_score"])
                melhor_troca = (idx, melhor_candidato)

        if melhor_troca is None:
            break

        idx, novo = melhor_troca
        antigo_preco = float(time.loc[idx, "preco"])
        novo_preco = float(novo["preco"])
        saldo -= (novo_preco - antigo_preco)

        for col in time.columns:
            if col in novo.index:
                time.loc[idx, col] = novo[col]

    return time


def recomendados_por_faixa(df: pd.DataFrame, orcamento: float, formacao: str = "4-3-3") -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    slots = FORMACOES.get(formacao, FORMACOES["4-3-3"])
    universo = df.copy()

    universo["_prioridade_status"] = universo["status_id"].apply(_prioridade_status)
    universo = universo.sort_values(
        ["_prioridade_status", "score", "media"],
        ascending=[True, False, False]
    )

    base = _montar_base_mais_barata(universo, slots)
    if base.empty:
        return pd.DataFrame()

    if float(base["preco"].sum()) > float(orcamento):
        return pd.DataFrame()

    time_final = _aplicar_upgrades(base, universo, orcamento)
    if time_final.empty:
        return pd.DataFrame()

    jogadores = len(time_final[time_final["posicao"] != "Técnico"])
    tecnicos = len(time_final[time_final["posicao"] == "Técnico"])

    if jogadores != 11 or tecnicos != 1:
        return pd.DataFrame()

    time_final = time_final.sort_values(
        by=["posicao"],
        key=lambda s: s.map(ORDEM_MAP)
    ).reset_index(drop=True)

    time_final["gasto_acumulado"] = time_final["preco"].cumsum()
    return time_final


def top_por_perfil(df: pd.DataFrame, posicao: str = None, n: int = 10) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    base = df[df["elegivel"] == True].copy()

    if posicao:
        base = base[base["posicao"] == posicao].copy()

    return base.sort_values(["score", "media"], ascending=[False, False]).head(n)
