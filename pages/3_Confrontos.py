"""
Página 3 — Análise de Confrontos
Histórico de partidas e aproveitamento entre clubes.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.confrontos import build_partidas_df, historico_confronto, resumo_confronto, desempenho_casa_fora
from utils.api import get_mercado_status

st.set_page_config(page_title="Confrontos | Cartola Analyzer", page_icon="⚔️", layout="wide")
st.title("⚔️ Análise de Confrontos")

status_raw = get_mercado_status() or {}
rodada_atual = status_raw.get("rodada", {}).get("rodada_atual", 10)

with st.sidebar:
    st.header("⚙️ Configurações")
    rodadas_range = st.slider("Rodadas analisadas", 1, int(rodada_atual), (max(1, int(rodada_atual)-10), int(rodada_atual)))
    st.info(f"Rodada atual: {rodada_atual}")

rodadas = list(range(rodadas_range[0], rodadas_range[1] + 1))

with st.spinner(f"Carregando partidas das rodadas {rodadas_range[0]}–{rodadas_range[1]}..."):
    df_partidas = build_partidas_df(rodadas)

if df_partidas.empty:
    st.warning("Sem dados de partidas para o período selecionado.")
    st.stop()

clubes_disp = sorted(set(df_partidas["clube_casa"].tolist() + df_partidas["clube_visitante"].tolist()))

# ── confronto direto ──────────────────────────────────────────────────────
st.subheader("⚔️ Confronto Direto")
col1, col2 = st.columns(2)
clube_a = col1.selectbox("Clube A", clubes_disp, index=0)
clube_b = col2.selectbox("Clube B", [c for c in clubes_disp if c != clube_a], index=0)

hist = historico_confronto(df_partidas, clube_a, clube_b)
resumo = resumo_confronto(hist, clube_a, clube_b)

if not resumo:
    st.info("Sem confrontos diretos no período selecionado.")
else:
    jogos = resumo["jogos"]
    v_a = resumo.get(f"vitórias_{clube_a}", 0)
    emp = resumo["empates"]
    v_b = resumo.get(f"vitórias_{clube_b}", 0)
    aprov_a = resumo.get(f"aproveitamento_{clube_a}", 0)
    ga = resumo.get(f"gols_{clube_a}", 0)
    gb = resumo.get(f"gols_{clube_b}", 0)

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Jogos", jogos)
    m2.metric(f"✅ Vitórias {clube_a}", v_a)
    m3.metric("🤝 Empates", emp)
    m4.metric(f"✅ Vitórias {clube_b}", v_b)
    m5.metric(f"Aproveitamento {clube_a}", f"{aprov_a}%")

    fig_pizza = go.Figure(go.Pie(
        labels=[f"Vitórias {clube_a}", "Empates", f"Vitórias {clube_b}"],
        values=[v_a, emp, v_b],
        marker_colors=["#01696f", "#d19900", "#a12c7b"],
        hole=0.4,
    ))
    fig_pizza.update_layout(
        title=f"{clube_a} × {clube_b} — {jogos} jogos",
        paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40,b=10,l=10,r=10)
    )
    col_p1, col_p2 = st.columns([1, 1])
    col_p1.plotly_chart(fig_pizza, use_container_width=True)

    col_p2.markdown("**Histórico de partidas**")
    hist_disp = hist[["rodada","clube_casa","placar_casa","placar_visitante","clube_visitante"]].copy()
    hist_disp.columns = ["Rodada","Casa","Gols Casa","Gols Fora","Visitante"]
    col_p2.dataframe(hist_disp, use_container_width=True, hide_index=True)

st.divider()

# ── desempenho casa/fora ──────────────────────────────────────────────────
st.subheader("🏟️ Desempenho Casa × Fora")
clube_sel = st.selectbox("Selecione o clube", clubes_disp, key="casa_fora")
desemp = desempenho_casa_fora(df_partidas, clube_sel)

def desemp_row(label, d):
    if d["jogos"] == 0:
        return {"Local": label, "Jogos": 0, "V": 0, "E": 0, "D": 0, "GF": 0, "GC": 0, "Aprov.": "0%"}
    pts = d["v"] * 3 + d["e"]
    aprov = round(pts / (d["jogos"] * 3) * 100, 1)
    return {"Local": label, "Jogos": d["jogos"], "V": d["v"], "E": d["e"], "D": d["d"],
            "GF": d["gf"], "GC": d["gc"], "Aprov.": f"{aprov}%"}

df_desemp = pd.DataFrame([desemp_row("🏠 Casa", desemp["casa"]), desemp_row("✈️ Fora", desemp["fora"])])
st.dataframe(df_desemp, use_container_width=True, hide_index=True)

st.divider()

st.subheader(f"📅 Partidas — Rodada {rodada_atual}")
rodada_df = df_partidas[df_partidas["rodada"] == int(rodada_atual)]
if rodada_df.empty:
    st.info("Sem dados para a rodada atual no período carregado.")
else:
    rodada_disp = rodada_df[["clube_casa","placar_casa","placar_visitante","clube_visitante"]].copy()
    rodada_disp.columns = ["Casa","Gols Casa","Gols Fora","Visitante"]
    st.dataframe(rodada_disp, use_container_width=True, hide_index=True)
