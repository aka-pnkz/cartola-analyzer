import pandas as pd
from utils.api import get_partidas, get_clubes


def build_partidas_df(rodadas: list[int]) -> pd.DataFrame:
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

        for partida in data.get("partidas", []):
            casa_id = partida.get("clube_casa_id")
            vis_id = partida.get("clube_visitante_id")

            rows.append({
                "rodada": rodada,
                "clube_casa_id": casa_id,
                "clube_casa": clubes.get(casa_id, str(casa_id)),
                "clube_visitante_id": vis_id,
                "clube_visitante": clubes.get(vis_id, str(vis_id)),
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
