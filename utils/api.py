"""
Módulo de comunicação com a API do Cartola FC.
Fornece funções para buscar atletas, mercado, rodadas e ligas.
"""
import requests
import streamlit as st
from typing import Optional

BASE_URL = "https://api.cartola.globo.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (CartolaPy/1.0)",
    "Accept": "application/json",
}

# ── helpers ──────────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict = None) -> Optional[dict | list]:
    """GET genérico com tratamento de erros."""
    try:
        resp = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"Erro HTTP {resp.status_code}: {e}")
    except requests.exceptions.ConnectionError:
        st.error("Sem conexão com a internet.")
    except requests.exceptions.Timeout:
        st.error("Timeout ao conectar com a API do Cartola.")
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
    return None


# ── endpoints públicos ────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def get_mercado_status() -> Optional[dict]:
    """Retorna o status atual do mercado (rodada, status, etc.)."""
    return _get("/mercado/status")


@st.cache_data(ttl=300)
def get_atletas_mercado() -> Optional[dict]:
    """Retorna todos os atletas disponíveis no mercado com estatísticas."""
    return _get("/atletas/mercado")


@st.cache_data(ttl=3600)
def get_partidas(rodada: int) -> Optional[dict]:
    """Retorna as partidas de uma rodada específica."""
    return _get(f"/partidas/{rodada}")


@st.cache_data(ttl=3600)
def get_clubes() -> Optional[dict]:
    """Retorna todos os clubes do campeonato."""
    return _get("/clubes")


@st.cache_data(ttl=3600)
def get_posicoes() -> Optional[dict]:
    """Retorna as posições (goleiro, lateral, etc.)."""
    return _get("/posicoes")


@st.cache_data(ttl=300)
def get_pontuados(rodada: int) -> Optional[dict]:
    """Retorna atletas que pontuaram em uma rodada específica."""
    return _get(f"/atletas/pontuados/{rodada}")


@st.cache_data(ttl=3600)
def get_scouts() -> Optional[dict]:
    """Retorna a definição de cada scout (G, A, FT, etc.)."""
    return _get("/scouts")


@st.cache_data(ttl=600)
def get_liga(slug: str) -> Optional[dict]:
    """Retorna informações de uma liga pelo slug."""
    return _get(f"/auth/liga/{slug}")


# ── mapeamentos auxiliares ───────────────────────────────────────────────────

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
    7: "🚫 Nulo",
}

STATUS_MERCADO_NOME = {
    1: "Aberto",
    2: "Fechado",
    3: "Em atualização",
    4: "Final de temporada",
}

@st.cache_data(ttl=3600)
def get_clubes_mapa_nome() -> dict[int, str]:
    """
    Retorna um mapa {clube_id: nome do clube}.
    """
    clubes = get_clubes() or {}
    return {
        int(k): v.get("nome", str(k))
        for k, v in clubes.items()
    }

@st.cache_data(ttl=3600)
def get_clubes_mapa_curto() -> dict[int, str]:
    """
    Retorna um mapa {clube_id: nome curto/abreviação do clube}.
    """
    clubes = get_clubes() or {}
    return {
        int(k): v.get("nome_curto", v.get("abreviacao", str(k)))
        for k, v in clubes.items()
    }
