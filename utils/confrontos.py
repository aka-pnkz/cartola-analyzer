import pandas as pd
import plotly.express as px

from utils.api import get_partidas


def _serie_segura(df: pd.DataFrame, coluna: str, default=0.0) -> pd.Series:
    if coluna in df.columns:
        return pd.to_numeric(df[coluna], errors="coerce").fillna(default)
    return pd.Series([default] * len(df), index=df.index)


def _texto_seguro(valor, fallback="-"):
    if valor is None:
        return fallback
    if isinstance(valor, float) and pd.isna(valor):
        return fallback
    texto = str(valor).strip()
    return texto if texto else fallback


def montar_forca_por_clube(df_atletas: pd.DataFrame) -> pd.DataFrame:
    if df_atletas is None or df_atletas.empty:
        return pd.DataFrame()

    base = df_atletas.copy()

    for col in [
        "score", "media", "ataque_bruto", "defesa_bruto",
        "base_bruto", "preco", "elegivel", "id"
    ]:
        if col not in base.columns:
            if col in ["elegivel"]:
                base[col] = False
            elif col in ["id"]:
                base[col] = range(1, len(base) + 1)
            else:
                base[col] = 0.0

    if "clube_id" not in base.columns:
        base["clube_id"] = range(1, len(base) + 1)

    if "clube" not in base.columns:
        base["clube"] = "Clube"

    agg = (
        base.groupby(["clube_id", "clube"], as_index=False)
        .agg(
            atletas=("id", "count"),
            elegiveis=("elegivel", "sum"),
            score_medio=("score", "mean"),
            media_media=("media", "mean"),
            ataque_medio=("ataque_bruto", "mean"),
            defesa_media=("defesa_bruto", "mean"),
            base_media=("base_bruto", "mean"),
            preco_medio=("preco", "mean"),
        )
    )

    agg["forca_ofensiva"] = (
        agg["ataque_medio"] * 0.55 +
        agg["score_medio"] * 0.25 +
        agg["media_media"] * 0.20
    )

    agg["forca_defensiva"] = (
        agg["defesa_media"] * 0.50 +
        agg["base_media"] * 0.25 +
        agg["score_medio"] * 0.25
    )

    agg["potencial_sg"] = (
        agg["defesa_media"] * 0.60 +
        agg["base_media"] * 0.40
    )

    agg["risco_sofrer"] = agg["forca_ofensiva"]

    return agg


def _classificar_alerta_confronto(row) -> str:
    diff_ataque = abs(float(row.get("indice_ataque_casa", 0)) - float(row.get("indice_ataque_fora", 0)))
    maior_sg = max(float(row.get("indice_sg_casa", 0)), float(row.get("indice_sg_fora", 0)))
    maior_ataque = max(float(row.get("indice_ataque_casa", 0)), float(row.get("indice_ataque_fora", 0)))

    if maior_sg >= 1.8:
        return "🛡️ Bom para SG"
    if diff_ataque <= 0.15:
        return "⚖️ Jogo equilibrado"
    if maior_ataque >= 1.8:
        return "🔥 Bom para ataque"
    return "📊 Confronto neutro"


def montar_tabela_confrontos(df_atletas: pd.DataFrame) -> pd.DataFrame:
    if df_atletas is None or df_atletas.empty:
        return pd.DataFrame()

    partidas = get_partidas()
    if not partidas:
        return pd.DataFrame()

    partidas_lista = partidas.get("partidas", [])
    if not partidas_lista:
        return pd.DataFrame()

    clubes_forca = montar_forca_por_clube(df_atletas)
    if clubes_forca.empty:
        return pd.DataFrame()

    mapa = clubes_forca.set_index("clube_id").to_dict("index")
    rows = []

    for p in partidas_lista:
        clube_casa_id = p.get("clube_casa_id")
        clube_visitante_id = p.get("clube_visitante_id")

        casa = mapa.get(clube_casa_id)
        fora = mapa.get(clube_visitante_id)

        if not casa or not fora:
            continue

        aproveitamento_casa = (
            casa["forca_ofensiva"] * 0.45 +
            fora["risco_sofrer"] * 0.35 +
            casa["score_medio"] * 0.20
        )

        aproveitamento_fora = (
            fora["forca_ofensiva"] * 0.38 +
            casa["risco_sofrer"] * 0.32 +
            fora["score_medio"] * 0.15
        )

        sg_casa = (
            casa["potencial_sg"] * 0.60 -
            fora["forca_ofensiva"] * 0.20
        )

        sg_fora = (
            fora["potencial_sg"] * 0.50 -
            casa["forca_ofensiva"] * 0.25
        )

        rows.append({
            "partida_data": p.get("partida_data"),
            "clube_casa_id": clube_casa_id,
            "clube_visitante_id": clube_visitante_id,
            "casa": _texto_seguro(casa.get("clube")),
            "fora": _texto_seguro(fora.get("clube")),
            "indice_ataque_casa": round(float(aproveitamento_casa), 3),
            "indice_ataque_fora": round(float(aproveitamento_fora), 3),
            "indice_sg_casa": round(float(sg_casa), 3),
            "indice_sg_fora": round(float(sg_fora), 3),
            "forca_ofensiva_casa": round(float(casa.get("forca_ofensiva", 0)), 3),
            "forca_ofensiva_fora": round(float(fora.get("forca_ofensiva", 0)), 3),
            "forca_defensiva_casa": round(float(casa.get("forca_defensiva", 0)), 3),
            "forca_defensiva_fora": round(float(fora.get("forca_defensiva", 0)), 3),
        })

    tabela = pd.DataFrame(rows)
    if tabela.empty:
        return tabela

    tabela["favorito_ataque"] = tabela.apply(
        lambda x: x["casa"] if x["indice_ataque_casa"] >= x["indice_ataque_fora"] else x["fora"],
        axis=1,
    )
    tabela["favorito_sg"] = tabela.apply(
        lambda x: x["casa"] if x["indice_sg_casa"] >= x["indice_sg_fora"] else x["fora"],
        axis=1,
    )
    tabela["jogo"] = tabela["casa"] + " x " + tabela["fora"]
    tabela["alerta"] = tabela.apply(_classificar_alerta_confronto, axis=1)

    return tabela.sort_values(
        ["indice_ataque_casa", "indice_ataque_fora"],
        ascending=[False, False]
    ).reset_index(drop=True)


def melhores_confrontos(df_confrontos: pd.DataFrame) -> dict:
    if df_confrontos is None or df_confrontos.empty:
        return {}

    melhor_ataque_idx = df_confrontos[["indice_ataque_casa", "indice_ataque_fora"]].max(axis=1).idxmax()
    melhor_sg_idx = df_confrontos[["indice_sg_casa", "indice_sg_fora"]].max(axis=1).idxmax()

    row_ataque = df_confrontos.loc[melhor_ataque_idx]
    row_sg = df_confrontos.loc[melhor_sg_idx]

    return {
        "melhor_ataque_jogo": row_ataque.get("jogo", "-"),
        "melhor_time_ataque": row_ataque.get("favorito_ataque", "-"),
        "melhor_sg_jogo": row_sg.get("jogo", "-"),
        "melhor_time_sg": row_sg.get("favorito_sg", "-"),
    }


def grafico_indices_confronto(df_confrontos: pd.DataFrame):
    if df_confrontos is None or df_confrontos.empty:
        return None

    linhas = []

    for _, row in df_confrontos.iterrows():
        linhas.append({
            "jogo": row["jogo"],
            "time": row["casa"],
            "tipo": "Ataque",
            "indice": row["indice_ataque_casa"],
        })
        linhas.append({
            "jogo": row["jogo"],
            "time": row["fora"],
            "tipo": "Ataque",
            "indice": row["indice_ataque_fora"],
        })
        linhas.append({
            "jogo": row["jogo"],
            "time": row["casa"],
            "tipo": "SG",
            "indice": row["indice_sg_casa"],
        })
        linhas.append({
            "jogo": row["jogo"],
            "time": row["fora"],
            "tipo": "SG",
            "indice": row["indice_sg_fora"],
        })

    base = pd.DataFrame(linhas)

    fig = px.bar(
        base,
        x="jogo",
        y="indice",
        color="tipo",
        barmode="group",
        hover_data=["time"],
        title="Índices de ataque e SG por confronto",
    )

    fig.update_layout(
        xaxis_title="Confronto",
        yaxis_title="Índice",
        legend_title="Tipo",
        margin=dict(l=20, r=20, t=50, b=20),
    )

    return fig


def sugerir_atletas_por_confronto(df_atletas: pd.DataFrame, confronto_row: pd.Series) -> pd.DataFrame:
    if df_atletas is None or df_atletas.empty or confronto_row is None or len(confronto_row) == 0:
        return pd.DataFrame()

    casa = confronto_row.get("casa")
    fora = confronto_row.get("fora")

    atletas = df_atletas[df_atletas["clube"].isin([casa, fora])].copy()
    if atletas.empty:
        return pd.DataFrame()

    if "score" not in atletas.columns:
        atletas["score"] = 0.0
    if "ataque_norm" not in atletas.columns:
        atletas["ataque_norm"] = 0.0
    if "defesa_norm" not in atletas.columns:
        atletas["defesa_norm"] = 0.0

    atletas["fit_confronto"] = atletas["score"]

    atletas.loc[atletas["clube"] == confronto_row.get("favorito_ataque"), "fit_confronto"] += (
        atletas["ataque_norm"] * 0.20
    )
    atletas.loc[atletas["clube"] == confronto_row.get("favorito_sg"), "fit_confronto"] += (
        atletas["defesa_norm"] * 0.15
    )

    atletas = atletas.sort_values(
        ["fit_confronto", "score", "media"],
        ascending=[False, False, False]
    )

    colunas = [
        "nome",
        "clube",
        "posicao",
        "status",
        "preco",
        "media",
        "score_pct",
        "fit_confronto",
        "ataque_bruto",
        "defesa_bruto",
        "base_bruto",
    ]
    colunas = [c for c in colunas if c in atletas.columns]

    return atletas[colunas].head(12).reset_index(drop=True)


# Wrappers de compatibilidade
def get_tabela_confrontos(df_atletas: pd.DataFrame) -> pd.DataFrame:
    return montar_tabela_confrontos(df_atletas)


def analisar_confrontos(df_atletas: pd.DataFrame) -> pd.DataFrame:
    return montar_tabela_confrontos(df_atletas)


def get_melhores_confrontos(df_confrontos: pd.DataFrame) -> dict:
    return melhores_confrontos(df_confrontos)


def get_grafico_confrontos(df_confrontos: pd.DataFrame):
    return grafico_indices_confronto(df_confrontos)


def get_sugestoes_confronto(df_atletas: pd.DataFrame, confronto_row: pd.Series) -> pd.DataFrame:
    return sugerir_atletas_por_confronto(df_atletas, confronto_row)
