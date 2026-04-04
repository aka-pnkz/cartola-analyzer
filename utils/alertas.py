import pandas as pd
from utils.historico_status import atualizar_e_analisar_status
from utils.api import get_rodada_atual


STATUS_ALERTA_IDS = {3, 5, 7}


def gerar_alertas(df: pd.DataFrame, referencia_evento=None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    rodada_atual = get_rodada_atual()
    historico_status = atualizar_e_analisar_status(df, rodada_atual=rodada_atual)

    base_hist = historico_status[[
        "atleta_id",
        "status_id",
        "status",
        "status_id_anterior",
        "status_anterior",
        "mudou_status",
        "novo_no_historico",
        "coletado_em",
        "primeira_vez_visto_em",
        "ultima_mudanca_status_em",
        "rodada",
        "rodada_anterior",
    ]].copy()

    base_hist = base_hist.rename(columns={
        "atleta_id": "id",
        "status": "status_hist",
        "status_id": "status_id_hist",
    })

    base = df.copy().merge(base_hist, on="id", how="left")

    agora = pd.Timestamp.now()
    alertas = []

    for _, row in base.iterrows():
        nome = row.get("nome", "Atleta")
        clube = row.get("clube", "-")
        posicao = row.get("posicao", "-")
        status = row.get("status", "-")
        status_id = row.get("status_id")
        preco = float(row.get("preco", 0) or 0)
        media = float(row.get("media", 0) or 0)
        score_pct = float(row.get("score_pct", 0) or 0)
        variacao = float(row.get("variacao", 0) or 0)
        ataque = float(row.get("ataque_bruto", 0) or 0)
        defesa = float(row.get("defesa_bruto", 0) or 0)
        base_scout = float(row.get("base_bruto", 0) or 0)
        disciplina = float(row.get("disciplina_bruto", 0) or 0)

        mudou_status = bool(row.get("mudou_status", False))
        status_anterior = row.get("status_anterior")
        novo_no_historico = bool(row.get("novo_no_historico", False))
        rodada_ref = row.get("rodada", rodada_atual)
        rodada_anterior = row.get("rodada_anterior")
        detectado_em = row.get("coletado_em", agora)
        desde_quando = row.get("ultima_mudanca_status_em", detectado_em)

        contexto_status = (
            "nova mudança detectada"
            if mudou_status else
            "status persistente"
        )

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
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
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
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
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
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
            })

        if base_scout >= 6 and score_pct >= 60:
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
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
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
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
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
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
            })

        if status_id in STATUS_ALERTA_IDS:
            if mudou_status or novo_no_historico:
                mensagem = f"{nome} entrou em status de atenção nesta coleta."
            else:
                mensagem = f"{nome} segue com status de atenção desde coleta anterior."

            alertas.append({
                "tipo": "🩺 Status relevante",
                "mensagem": mensagem,
                "nome": nome,
                "clube": clube,
                "posicao": posicao,
                "status": status,
                "preco": preco,
                "media": media,
                "score_pct": score_pct,
                "rodada_referencia": rodada_ref,
                "detectado_em": detectado_em,
                "desde_quando_esta_assim": desde_quando,
                "status_anterior": status_anterior,
                "mudou_nesta_consulta": mudou_status,
                "contexto_status": contexto_status,
            })

    alertas_df = pd.DataFrame(alertas)

    if alertas_df.empty:
        return alertas_df

    for col in ["detectado_em", "desde_quando_esta_assim"]:
        if col in alertas_df.columns:
            alertas_df[col] = pd.to_datetime(alertas_df[col], errors="coerce")

    return alertas_df.sort_values(
        ["mudou_nesta_consulta", "score_pct", "detectado_em"],
        ascending=[False, False, False]
    ).reset_index(drop=True)


def detectar_alertas(df: pd.DataFrame, referencia_evento=None) -> pd.DataFrame:
    return gerar_alertas(df, referencia_evento=referencia_evento)


def filtrar_alertas(
    alertas_df: pd.DataFrame,
    tipo: str | None = None,
    posicao: str | None = None,
    clube: str | None = None,
) -> pd.DataFrame:
    if alertas_df is None or alertas_df.empty:
        return pd.DataFrame()

    base = alertas_df.copy()

    if tipo and tipo != "Todos":
        base = base[base["tipo"] == tipo]

    if posicao and posicao != "Todas":
        base = base[base["posicao"] == posicao]

    if clube and clube != "Todos":
        base = base[base["clube"] == clube]

    return base.reset_index(drop=True)
