from pathlib import Path
import pandas as pd

HIST_DIR = Path("data")
HIST_FILE = HIST_DIR / "status_atletas.csv"


def _garantir_pasta():
    HIST_DIR.mkdir(parents=True, exist_ok=True)


def snapshot_status_atletas(df_atletas: pd.DataFrame, rodada_atual=None) -> pd.DataFrame:
    if df_atletas is None or df_atletas.empty:
        return pd.DataFrame()

    base = df_atletas.copy()

    colunas = {
        "id": "atleta_id",
        "nome": "nome",
        "clube": "clube",
        "posicao": "posicao",
        "status_id": "status_id",
        "status": "status",
    }

    for origem in colunas.keys():
        if origem not in base.columns:
            base[origem] = None

    snap = base[list(colunas.keys())].rename(columns=colunas)
    snap["rodada"] = rodada_atual
    snap["coletado_em"] = pd.Timestamp.now()

    return snap


def carregar_historico_status() -> pd.DataFrame:
    _garantir_pasta()

    if not HIST_FILE.exists():
        return pd.DataFrame()

    try:
        hist = pd.read_csv(HIST_FILE)
    except Exception:
        return pd.DataFrame()

    if hist.empty:
        return hist

    if "coletado_em" in hist.columns:
        hist["coletado_em"] = pd.to_datetime(hist["coletado_em"], errors="coerce")

    return hist


def salvar_snapshot_status(snapshot_df: pd.DataFrame) -> None:
    if snapshot_df is None or snapshot_df.empty:
        return

    _garantir_pasta()
    historico = carregar_historico_status()

    combinado = pd.concat([historico, snapshot_df], ignore_index=True)
    combinado.to_csv(HIST_FILE, index=False)


def obter_ultimo_snapshot(historico: pd.DataFrame) -> pd.DataFrame:
    if historico is None or historico.empty:
        return pd.DataFrame()

    if "coletado_em" not in historico.columns:
        return pd.DataFrame()

    ultima_data = historico["coletado_em"].max()
    ultimo = historico[historico["coletado_em"] == ultima_data].copy()

    return ultimo.reset_index(drop=True)


def comparar_status(snapshot_atual: pd.DataFrame, snapshot_anterior: pd.DataFrame) -> pd.DataFrame:
    if snapshot_atual is None or snapshot_atual.empty:
        return pd.DataFrame()

    atual = snapshot_atual.copy()

    if snapshot_anterior is None or snapshot_anterior.empty:
        atual["status_anterior"] = None
        atual["status_id_anterior"] = None
        atual["mudou_status"] = False
        atual["novo_no_historico"] = True
        return atual

    anterior = snapshot_anterior.copy()

    anterior = anterior[[
        "atleta_id",
        "status_id",
        "status",
        "rodada",
        "coletado_em",
    ]].rename(columns={
        "status_id": "status_id_anterior",
        "status": "status_anterior",
        "rodada": "rodada_anterior",
        "coletado_em": "coletado_em_anterior",
    })

    merged = atual.merge(anterior, on="atleta_id", how="left")

    merged["novo_no_historico"] = merged["status_id_anterior"].isna()
    merged["mudou_status"] = (
        merged["status_id"].fillna(-1) != merged["status_id_anterior"].fillna(-1)
    )

    return merged


def enriquecer_com_historico(snapshot_comparado: pd.DataFrame, historico: pd.DataFrame) -> pd.DataFrame:
    if snapshot_comparado is None or snapshot_comparado.empty:
        return pd.DataFrame()

    base = snapshot_comparado.copy()

    if historico is None or historico.empty:
        base["primeira_vez_visto_em"] = base["coletado_em"]
        base["ultima_mudanca_status_em"] = base["coletado_em"]
        base["rodada_primeiro_registro"] = base["rodada"]
        return base

    hist = historico.copy()
    hist["coletado_em"] = pd.to_datetime(hist["coletado_em"], errors="coerce")

    primeira = (
        hist.groupby("atleta_id", as_index=False)
        .agg(
            primeira_vez_visto_em=("coletado_em", "min"),
            rodada_primeiro_registro=("rodada", "min"),
        )
    )

    ultima_mesmo_status = (
        hist.sort_values(["atleta_id", "coletado_em"])
        .groupby(["atleta_id", "status_id"], as_index=False)
        .agg(ultima_mudanca_status_em=("coletado_em", "max"))
    )

    base = base.merge(primeira, on="atleta_id", how="left")
    base = base.merge(
        ultima_mesmo_status,
        on=["atleta_id", "status_id"],
        how="left",
    )

    base["primeira_vez_visto_em"] = pd.to_datetime(base["primeira_vez_visto_em"], errors="coerce")
    base["ultima_mudanca_status_em"] = pd.to_datetime(base["ultima_mudanca_status_em"], errors="coerce")

    base["primeira_vez_visto_em"] = base["primeira_vez_visto_em"].fillna(base["coletado_em"])
    base["ultima_mudanca_status_em"] = base["ultima_mudanca_status_em"].fillna(base["coletado_em"])

    return base


def atualizar_e_analisar_status(df_atletas: pd.DataFrame, rodada_atual=None) -> pd.DataFrame:
    snapshot_atual = snapshot_status_atletas(df_atletas, rodada_atual=rodada_atual)
    historico = carregar_historico_status()
    snapshot_anterior = obter_ultimo_snapshot(historico)

    comparado = comparar_status(snapshot_atual, snapshot_anterior)
    enriquecido = enriquecer_com_historico(comparado, historico)

    salvar_snapshot_status(snapshot_atual)

    return enriquecido
