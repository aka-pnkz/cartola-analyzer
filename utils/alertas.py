"""
Sistema de alertas e notificações para o Cartola Analyzer.
Detecta atletas em alta, queda de preço, suspensos e boas oportunidades.
"""
import pandas as pd
from dataclasses import dataclass, field
from typing import Literal


AlertType = Literal["success", "warning", "error", "info"]


@dataclass
class Alerta:
    tipo: AlertType
    titulo: str
    mensagem: str
    atleta_id: int | None = None
    atleta_nome: str | None = None


def detectar_alertas(df: pd.DataFrame) -> list[Alerta]:
    """
    Analisa o DataFrame de atletas e retorna lista de alertas relevantes.
    """
    alertas: list[Alerta] = []

    if df.empty:
        alertas.append(Alerta("info", "Sem dados", "Nenhum dado de atletas disponível."))
        return alertas

    # ── atletas em alta (valorização > 5 C$) ──────────────────────────────
    em_alta = df[df["variacao"] >= 5].sort_values("variacao", ascending=False).head(10)
    for _, row in em_alta.iterrows():
        alertas.append(Alerta(
            tipo="success",
            titulo=f"📈 {row['nome']} em alta",
            mensagem=f"Valorizou +{row['variacao']:.1f} C$ | Média: {row['media']:.1f} pts | Clube: {row['clube']}",
            atleta_id=row["id"],
            atleta_nome=row["nome"],
        ))

    # ── atletas em queda (desvalorização > 3 C$) ──────────────────────────
    em_queda = df[df["variacao"] <= -3].sort_values("variacao").head(10)
    for _, row in em_queda.iterrows():
        alertas.append(Alerta(
            tipo="warning",
            titulo=f"📉 {row['nome']} em queda",
            mensagem=f"Desvalorizou {row['variacao']:.1f} C$ | Média: {row['media']:.1f} pts | Clube: {row['clube']}",
            atleta_id=row["id"],
            atleta_nome=row["nome"],
        ))

    # ── atletas suspensos ou lesionados ────────────────────────────────────
    problemas = df[df["status_id"].isin([5, 6])]
    for _, row in problemas.iterrows():
        alertas.append(Alerta(
            tipo="error",
            titulo=f"{row['status']} {row['nome']}",
            mensagem=f"Posição: {row['posicao']} | Clube: {row['clube']} | Preço: {row['preco']:.1f} C$",
            atleta_id=row["id"],
            atleta_nome=row["nome"],
        ))

    # ── oportunidades (SAM alto + preço baixo) ─────────────────────────────
    if "sam_pct" in df.columns:
        oportunidades = df[
            (df["sam_pct"] >= 70) &
            (df["preco"] <= df["preco"].median()) &
            (df["status_id"] == 2)
        ].sort_values("sam_pct", ascending=False).head(5)

        for _, row in oportunidades.iterrows():
            alertas.append(Alerta(
                tipo="info",
                titulo=f"💡 Oportunidade: {row['nome']}",
                mensagem=(
                    f"SAM: {row['sam_pct']:.1f}% | Preço: {row['preco']:.1f} C$ | "
                    f"Média: {row['media']:.1f} pts | {row['posicao']} — {row['clube']}"
                ),
                atleta_id=row["id"],
                atleta_nome=row["nome"],
            ))

    return alertas


def filtrar_alertas(alertas: list[Alerta], tipos: list[AlertType]) -> list[Alerta]:
    return [a for a in alertas if a.tipo in tipos]
