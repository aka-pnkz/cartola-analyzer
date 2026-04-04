from datetime import datetime
import pandas as pd


def gerar_alertas(df: pd.DataFrame, referencia_evento=None) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    agora = pd.Timestamp.now()

    if referencia_evento is None:
        evento_em = agora
    else:
        evento_em = pd.to_datetime(referencia_evento, errors="coerce")
        if pd.isna(evento_em):
            evento_em = agora

    alertas = []

    for _, row in df.iterrows():
        nome = row.get("nome", "Atleta")
        clube = row.get("clube", "-")
        posicao = row.get("posicao", "-")
        status = row.get("status", "-")
        preco = float(row.get("preco", 0) or 0)
        media = float(row.get("media", 0) or 0)
        score_pct = float(row.get("score_pct", 0) or 0)
        variacao = float(row.get("variacao", 0) or 0)
        ataque = float(row.get("ataque_bruto", 0) or 0)
        defesa = float(row.get("defesa_bruto", 0) or 0)
        base = float(row.get("base_bruto", 0) or 0)
        disciplina = float(row.get("disciplina_bruto", 0) or 0)

        if score_pct >= 75:
            alertas.append({
                "tipo": "🔥 Oportunidade",
                "mensagem": f"{nome} está com score alto para o perfil atual.",
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "evento_em": evento_em,
                "criado_em": agora,
            })

        if ataque >= max(defesa * 2, 8):
            alertas.append({
                "tipo": "⚔️ Perfil ofensivo",
                "mensagem": f"{nome} tem forte viés ofensivo.",
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "evento_em": evento_em,
                "criado_em": agora,
            })

        if defesa >= max(ataque * 1.5, 6):
            alertas.append({
                "tipo": "🛡️ Perfil defensivo",
                "mensagem": f"{nome} oferece segurança defensiva.",
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "evento_em": evento_em,
                "criado_em": agora,
            })

        if base >= 6 and score_pct >= 60:
            alertas.append({
                "tipo": "📈 Scout de base",
                "mensagem": f"{nome} pontua bem sem depender tanto de gol.",
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "evento_em": evento_em,
                "criado_em": agora,
            })

        if disciplina >= 3:
            alertas.append({
                "tipo": "🚨 Risco disciplinar",
                "mensagem": f"{nome} apresenta risco por cartões/faltas.",
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "evento_em": evento_em,
                "criado_em": agora,
            })

        if variacao > 0.8 and score_pct >= 55:
            alertas.append({
                "tipo": "💹 Tendência positiva",
                "mensagem": f"{nome} está em tendência de valorização/alta.",
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "evento_em": evento_em,
                "criado_em": agora,
            })

    alertas_df = pd.DataFrame(alertas)

    if alertas_df.empty:
        return alertas_df

    alertas_df["evento_em"] = pd.to_datetime(alertas_df["evento_em"], errors="coerce")
    alertas_df["criado_em"] = pd.to_datetime(alertas_df["criado_em"], errors="coerce")

    return alertas_df.sort_values(["score_pct", "criado_em"], ascending=[False, False]).reset_index(drop=True)


def detectar_alertas(df: pd.DataFrame, referencia_evento=None) -> pd.DataFrame:
    return gerar_alertas(df, referencia_evento=referencia_evento)


def filtrar_alertas(
    alertas_df: pd.DataFrame,
    tipo: str | None = None,
    posicao: str | None = None,
    clube: str | None = None,
) -> pd.DataFrame:
    if alertas_df.empty:
        return alertas_df

    base = alertas_df.copy()

    if tipo and tipo != "Todos":
        base = base[base["tipo"] == tipo]

    if posicao and posicao != "Todos":
        base = base[base["posicao"] == posicao]

    if clube and clube != "Todos":
        base = base[base["clube"] == clube]

    return base.reset_index(drop=True)
