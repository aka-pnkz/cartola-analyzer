"""
Módulo de comunicação com a API do Cartola FC.
"""
import requests
import streamlit as st
from typing import Optional

BASE_URL = "https://api.cartola.globo.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (CartolaPy/1.0)",
    "Accept": "application/json",
}


def _get(endpoint: str, params: dict = None) -> Optional[dict | list]:
    try:
        resp = requests.get(
            f"{BASE_URL}{endpoint}",
            headers=HEADERS,
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro HTTP: {e}")
    except requests.exceptions.ConnectionError:
        st.error("Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        st.error("Timeout ao conectar com a API do Cartola.")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
    return None


@st.cache_data(ttl=300)
def get_mercado_status() -> Optional[dict]:
    return _get("/mercado/status")


@st.cache_data(ttl=300)
def get_atletas_mercado() -> Optional[dict]:
    return _get("/atletas/mercado")


@st.cache_data(ttl=3600)
def get_partidas(rodada: int) -> Optional[dict]:
    return _get(f"/partidas/{rodada}")


@st.cache_data(ttl=3600)
def get_clubes() -> Optional[dict]:
    return _get("/clubes")


POSICAO_MAP = {
    1: "Goleiro",
    2: "Lateral",
    3: "Zagueiro",
    4: "Meia",
    5: "Atacante",
    6: "Técnico",
}

STATUS_MAP = {
    2: "✅ Provável",
    3: "⚠️ Dúvida",
    5: "❌ Suspenso",
    6: "🤕 Lesionado",
    7: "🟡 Disponível",
}

STATUS_MERCADO_NOME = {
    1: "Aberto",
    2: "Fechado",
    3: "Em atualização",
    4: "Final de temporada",
}


@st.cache_data(ttl=3600)
def get_clubes_mapa_curto() -> dict[int, str]:
    clubes = get_clubes() or {}
    return {
        int(k): v.get("nome", v.get("nome_curto", v.get("abreviacao", str(k))))
        for k, v in clubes.items()
    }
