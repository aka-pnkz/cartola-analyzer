import streamlit as st
from utils.confrontos import build_partidas_df
from utils.api import get_mercado_status

st.set_page_config(page_title="Confrontos | Cartola Analyzer", page_icon="⚔️", layout="wide")
st.title("⚔️ Análise de Confrontos")

status_raw = get_mercado_status() or {}
rodada_atual = status_raw.get("rodada_atual", 10) if isinstance(status_raw, dict) else 10

rodadas = list(range(max(1, int(rodada_atual) - 5), int(rodada_atual) + 1))
df = build_partidas_df(rodadas)

if df.empty:
    st.error("Sem dados de partidas disponíveis.")
    st.stop()

st.dataframe(
    df[["rodada", "clube_casa", "placar_casa", "placar_visitante", "clube_visitante"]],
    use_container_width=True,
    hide_index=True,
)
