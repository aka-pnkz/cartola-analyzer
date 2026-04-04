import requests
import streamlit as st

BASE_URL = "https://api.cartolafc.globo.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

POSICAO_MAP = {
    1: "Goleiro",
    2: "Lateral",
    3: "Zagueiro",
    4: "Meia",
    5: "Atacante",
    6: "Técnico",
}

STATUS_MAP = {
    2: "Provável",
    3: "Dúvida",
    5: "Suspenso",
    6: "Nulo",
    7: "Contundido",
}

CLUBES_CACHE = {}


@st.cache_data(ttl=300, show_spinner=False)
def _get_json(path: str):
    url = f"{BASE_URL}{path}"

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


@st.cache_data(ttl=300, show_spinner=False)
def get_atletas_mercado():
    data = _get_json("/atletas/mercado")
    if isinstance(data, dict):
        return data
    return {}


@st.cache_data(ttl=300, show_spinner=False)
def get_partidas():
    data = _get_json("/partidas")
    if isinstance(data, dict):
        return data
    return {}


@st.cache_data(ttl=300, show_spinner=False)
def get_status_mercado():
    data = _get_json("/mercado/status")
    if isinstance(data, dict):
        return data
    return {}


@st.cache_data(ttl=300, show_spinner=False)
def get_clubes_mapa_curto():
    data = get_atletas_mercado()
    if not data:
        return {}

    clubes_raw = data.get("clubes", {})
    if not isinstance(clubes_raw, dict):
        return {}

    clubes = {}
    for k, v in clubes_raw.items():
        try:
            clube_id = int(k)
        except Exception:
            continue

        if isinstance(v, dict):
            clubes[clube_id] = (
                v.get("nome_curto")
                or v.get("abreviacao")
                or v.get("nome")
                or str(clube_id)
            )

    return clubes


@st.cache_data(ttl=300, show_spinner=False)
def get_rodada_atual():
    status = get_status_mercado()
    if not status:
        return None
    return status.get("rodada_atual")


@st.cache_data(ttl=300, show_spinner=False)
def get_fechamento_mercado():
    status = get_status_mercado()
    if not status:
        return None
    return status.get("fechamento")


def limpar_cache_api():
    _get_json.clear()
    get_atletas_mercado.clear()
    get_partidas.clear()
    get_status_mercado.clear()
    get_clubes_mapa_curto.clear()
    get_rodada_atual.clear()
    get_fechamento_mercado.clear()
