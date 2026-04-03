"""
Exportação de dados do Cartola Analyzer para CSV, XLSX e JSON.
"""
import io
import json
import pandas as pd


def to_csv(df: pd.DataFrame) -> bytes:
    """Retorna DataFrame serializado como CSV UTF-8 com BOM (abre bem no Excel BR)."""
    return df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")


def to_excel(dfs: dict[str, pd.DataFrame]) -> bytes:
    """
    Recebe um dicionário {nome_aba: DataFrame} e retorna um arquivo XLSX
    com múltiplas abas.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df in dfs.items():
            df.to_excel(writer, sheet_name=sheet_name[:31], index=False)
    return output.getvalue()


def to_json(df: pd.DataFrame) -> str:
    """Serializa DataFrame como JSON orientado a registros."""
    return df.to_json(orient="records", force_ascii=False, indent=2)


def download_button_data(df: pd.DataFrame, fmt: str = "csv") -> tuple[bytes | str, str, str]:
    """
    Retorna (data, file_name, mime_type) prontos para st.download_button.
    fmt: 'csv' | 'xlsx' | 'json'
    """
    if fmt == "csv":
        return to_csv(df), "cartola_export.csv", "text/csv"
    elif fmt == "xlsx":
        return to_excel({"Dados": df}), "cartola_export.xlsx", \
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif fmt == "json":
        return to_json(df).encode(), "cartola_export.json", "application/json"
    raise ValueError(f"Formato desconhecido: {fmt}")
