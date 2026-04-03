# ⚽ Cartola Analyzer

> Análise avançada para o **Cartola FC** — Score Anti-Mitada (SAM), escalação inteligente, confrontos, comparador e alertas de mercado. Feito com [Streamlit](https://streamlit.io).

---

## 🗂️ Estrutura do Projeto

```
cartola_analyzer/
├── app.py                    # Dashboard principal
├── requirements.txt          # Dependências Python
├── utils/
│   ├── api.py                # Comunicação com a API do Cartola FC
│   ├── confrontos.py         # Histórico e aproveitamento entre clubes
│   ├── score_mitada.py       # Cálculo do Score Anti-Mitada (SAM)
│   ├── comparador.py         # Radar chart e comparação de atletas
│   ├── exportacao.py         # Exportação CSV / Excel / JSON
│   └── alertas.py            # Detecção de oportunidades e riscos
└── pages/
    ├── 2_Escalacao.py        # Montagem de time por orçamento + formação
    ├── 3_Confrontos.py       # Análise de confrontos diretos
    ├── 4_Comparador.py       # Comparação lado a lado de atletas
    └── 5_Alertas.py          # Painel de alertas e gráficos de variação
```

---

## 🚀 Como Rodar

```bash
# 1. Clone o repositório
git clone https://github.com/aka-pnkz/cartola-analyzer.git
cd cartola-analyzer

# 2. (Opcional) Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Inicie o app
streamlit run app.py
```

---

## 📄 Páginas

| Página | Descrição |
|---|---|
| 🏠 **Dashboard** | KPIs gerais, distribuição por posição, Top 10 SAM, alertas rápidos |
| 📋 **Escalação** | Monta time ideal por orçamento e formação (4-3-3, 4-4-2, 3-5-2, 3-4-3) |
| ⚔️ **Confrontos** | Histórico de partidas, aproveitamento casa/fora, confrontos diretos |
| 🔍 **Comparador** | Radar chart comparativo de até 6 atletas lado a lado |
| 🔔 **Alertas** | Atletas em alta/queda, suspensos/lesionados, oportunidades de custo-benefício |

---

## 🧮 Score Anti-Mitada (SAM)

O SAM combina 5 fatores normalizados por posição em uma nota de 0 a 100:

| Fator | Peso |
|---|---|
| Média de pontos | 30% |
| Consistência | 20% |
| Custo-benefício (média/preço) | 20% |
| Casa/Fora | 15% |
| Tendência recente | 15% |

---

## 📦 Dependências

- `streamlit` — interface web
- `pandas` + `numpy` — manipulação de dados
- `plotly` — gráficos interativos
- `requests` — consumo da API do Cartola FC
- `openpyxl` — exportação Excel

---

## 🔗 API

Utiliza a API pública do Cartola FC (`https://api.cartola.globo.com`). Os dados são cacheados com TTL de 5 minutos via `@st.cache_data`.

---

## 📝 Licença

MIT — sinta-se livre para usar e modificar.
