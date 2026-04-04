import streamlit as st
import plotly.express as px

from utils.api import get_mercado_status, STATUS_MERCADO_NOME
from utils.score_mitada import build_atletas_df
from utils.alertas import detectar_alertas

st.set_page_config(
    page_title="Cartola Analyzer",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.main {
    background-color: #f7f6f2;
}
.kpi-card {
    background: #ffffff;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    box-shadow: 0 1px 4px rgba(40,37,29,.08);
    text-align: center;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    color: #01696f;
}
.kpi-label {
    font-size: 0.85rem;
    color: #7a7974;
    margin-top: .25rem;
}
.alerta-success {
    background: #d4dfcc;
    border-left: 4px solid #437a22;
    padding: .6rem 1rem;
    border-radius: 6px;
    margin: .3rem 0;
}
.alerta-warning {
    background: #e7d7c4;
    border-left: 4px solid #da7101;
    padding: .6rem 1rem;
    border-radius: 6px;
    margin: .3rem 0;
}
.alerta-error {
    background: #e0ced7;
    border-left: 4px solid #a12c7b;
    padding: .6rem 1rem;
    border-radius: 6px;
    margin: .3rem 0;
}
.alerta-info {
    background: #cedcd8;
    border-left: 4px solid #01696f;
    padding: .6rem 1rem;
    border-radius: 6px;
    margin: .3rem 0;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚽ Cartola Analyzer")
    st.markdown("---")
    st.markdown("""
**Navegação**
- 🏠 Dashboard
- 📋 Escalação
- ⚔️ Confrontos
- 🔍 Comparador
- 🔔 Alertas
""")

@st.cache_data(ttl=300, show_spinner=False)
def load_data():
    return build_atletas_df()

status_raw = get_mercado_status() or {}

with st.spinner("🔄 Carregando dados do mercado..."):
    df_all = load_data()

st.title("⚽ Cartola Analyzer — Dashboard")

rodada_atual = status_raw.get("rodada_atual", "?") if isinstance(status_raw, dict) else "?"
status_mercado_id = status_raw.get("status_mercado") if isinstance(status_raw, dict) else None
status_mercado = STATUS_MERCADO_NOME.get(status_mercado_id, str(status_mercado_id or "?"))

if df_all.empty:
    st.error("⚠️ Não foi possível carregar os dados do mercado.")
    st.info("Verifique se a API do Cartola está retornando atletas e se o arquivo utils/score_mitada.py está atualizado.")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)

kpis = [
    (col1, len(df_all), "Total de Atletas"),
    (col2, f"#{rodada_atual}", "Rodada Atual"),
    (col3, status_mercado, "Status do Mercado"),
    (col4, f"{df_all['media'].mean():.1f}", "Média Geral"),
    (col5, f"C$ {df_all['preco'].median():.2f}", "Preço Mediano"),
]

for col, valor, label in kpis:
    with col:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-value">{valor}</div>
                <div class="kpi-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

col_a, col_b = st.columns([1, 1.6])

with col_a:
    st.subheader("📊 Atletas por Posição")

    pos_count = df_all.groupby("posicao").size().reset_index(name="count")

    if pos_count.empty:
        st.info("Sem dados suficientes para o gráfico de posições.")
    else:
        fig_pie = px.pie(
            pos_count,
            names="posicao",
            values="count",
            color_discrete_sequence=[
                "#01696f",
                "#d19900",
                "#a12c7b",
                "#da7101",
                "#006494",
                "#437a22",
            ],
            hole=0.42,
        )
        fig_pie.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with col_b:
    st.subheader("📈 Média por Posição — Top 5 Atletas")

    top5_pos = (
        df_all.sort_values(["posicao", "media"], ascending=[True, False])
        .groupby("posicao", group_keys=False)
        .head(5)
        .reset_index(drop=True)
    )

    if top5_pos.empty or not {"nome", "media", "posicao"}.issubset(top5_pos.columns):
        st.warning("Não foi possível montar o gráfico de médias por posição.")
    else:
        fig_bar = px.bar(
            top5_pos,
            x="nome",
            y="media",
            color="posicao",
            barmode="group",
            color_discrete_sequence=[
                "#01696f",
                "#d19900",
                "#a12c7b",
                "#da7101",
                "#006494",
                "#437a22",
            ],
            labels={"nome": "Atleta", "media": "Média de Pontos"},
        )

        fig_bar.update_layout(
            showlegend=True,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis_tickangle=-35,
        )

        st.plotly_chart(fig_bar, use_container_width=True)

st.subheader("🏆 Top 10 Atletas por Média")

top10 = (
    df_all.sort_values("media", ascending=False)
    .head(10)[["nome", "clube", "posicao", "status", "preco", "media", "variacao"]]
    .copy()
)

top10.columns = [
    "Atleta",
    "Clube",
    "Posição",
    "Status",
    "Preço (C$)",
    "Média",
    "Variação",
]

st.dataframe(top10, use_container_width=True, hide_index=True)

st.subheader("🔔 Alertas Rápidos")

alertas = detectar_alertas(df_all)

if alertas is None or alertas.empty:
    st.info("Nenhum alerta encontrado.")
else:
    for alerta in alertas[:8]:
        st.markdown(
            f'<div class="alerta-{alerta.tipo}"><strong>{alerta.titulo}</strong> — {alerta.mensagem}</div>',
            unsafe_allow_html=True,
        )
