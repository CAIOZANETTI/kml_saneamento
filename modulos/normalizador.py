"""
normalizador.py — Limpeza e padronização dos dados extraídos do KML.

Trata inconsistências como espaços em nomes, tipagem numérica,
e padronização de termos.
"""

import pandas as pd
import numpy as np


# ── Funções de normalização de valores ──────────────────────────────

def _str(valor) -> str:
    """Converte valor para string, tratando NaN/None."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return ''
    return str(valor)


def normalizar_layer(valor) -> str:
    """Padroniza campo layer: 'Agua ' → 'Água', etc."""
    valor = _str(valor)
    if not valor:
        return ''
    v = valor.strip().lower()
    if v in ('agua e esgoto', 'água e esgoto'):
        return 'Água e Esgoto'
    if v in ('agua', 'água'):
        return 'Água'
    if v == 'esgoto':
        return 'Esgoto'
    return valor.strip()


def normalizar_tipo(valor) -> str:
    """Padroniza tipo: 'AGUA' → 'Água', 'ESGOTO' → 'Esgoto'."""
    valor = _str(valor)
    if not valor:
        return ''
    v = valor.strip().upper()
    if v == 'AGUA':
        return 'Água'
    if v == 'ESGOTO':
        return 'Esgoto'
    return valor.strip()


def normalizar_material(valor) -> str:
    """Padroniza material mantendo siglas de engenharia."""
    valor = _str(valor)
    if not valor:
        return ''
    v = valor.strip().upper()
    mapa = {
        'PVC': 'PVC',
        'PVC-O': 'PVC-O',
        'PEAD': 'PEAD',
        'FOFO': 'FoFo',
        'DEFOFO': 'DEFoFo',
        'CONCRETO': 'Concreto',
        'FERRO FUNDIDO': 'FoFo',
        'FF': 'FoFo',
    }
    return mapa.get(v, valor.strip())


def normalizar_metodo(valor) -> str:
    """Padroniza método construtivo."""
    valor = _str(valor)
    if not valor:
        return ''
    v = valor.strip().upper()
    mapa = {
        'VCA': 'VCA',
        'MND': 'MND',
        'A DEFINIR': 'A Definir',
        'TRAVESSIA SUBTERRÂNEA': 'Travessia Subterrânea',
        'TRAVESSIA AÉREA': 'Travessia Aérea',
        'TRAVESSIA TRELIÇADA': 'Travessia Treliçada',
    }
    return mapa.get(v, valor.strip())


def normalizar_fonte(valor) -> str:
    """Padroniza campo fonte (empresa de projeto)."""
    valor = _str(valor)
    if not valor:
        return ''
    v = valor.strip().upper()
    if 'ARCADIS' in v and 'PARAMETRIZADO' in v:
        return 'Arcadis - Parametrizado'
    if 'ARCADIS' in v:
        return 'Arcadis'
    if 'COBRAPE' in v or 'COB ' in v:
        return 'Cobrape'
    if 'CONSORCIO' in v or 'CONSÓRCIO' in v:
        return 'Consórcio AC'
    return valor.strip()


def _converter_float(valor) -> float:
    """Converte valor para float, retornando NaN se inválido."""
    if valor is None or valor == '' or valor == 'None':
        return np.nan
    try:
        return float(valor)
    except (ValueError, TypeError):
        return np.nan


def _converter_int(valor):
    """Converte valor para int nullable, retornando pd.NA se inválido."""
    if valor is None or valor == '' or valor == 'None':
        return pd.NA
    try:
        return int(float(valor))
    except (ValueError, TypeError):
        return pd.NA


# ── Normalização de DataFrames completos ────────────────────────────

def normalizar_linear(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza DataFrame de concepção linear."""
    if df.empty:
        return df

    df = df.copy()

    # Normalizar textos
    if 'tipo' in df.columns:
        df['tipo'] = df['tipo'].apply(normalizar_tipo)
    if 'material' in df.columns:
        df['material'] = df['material'].apply(normalizar_material)
    if 'metodo_construtivo' in df.columns:
        df['metodo_construtivo'] = df['metodo_construtivo'].apply(normalizar_metodo)
    if 'fonte' in df.columns:
        df['fonte'] = df['fonte'].apply(normalizar_fonte)

    # Converter numéricos
    colunas_float = [
        'extensao_calculada_m', 'estaca_inicial_m', 'estaca_final_m',
        'prof_media_m',
    ]
    colunas_int = [
        'diametro_nominal_mm', 'estruturante', 'esteira_sabesp', 'invest_obr',
    ]

    for col in colunas_float:
        if col in df.columns:
            df[col] = df[col].apply(_converter_float)

    for col in colunas_int:
        if col in df.columns:
            df[col] = df[col].apply(_converter_int).astype('Int64')

    return df


def normalizar_pontual(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza DataFrame de concepção pontual."""
    if df.empty:
        return df

    df = df.copy()

    # Normalizar textos
    if 'tipo' in df.columns:
        df['tipo'] = df['tipo'].apply(normalizar_tipo)
    if 'fonte' in df.columns:
        df['fonte'] = df['fonte'].apply(normalizar_fonte)

    # Converter numéricos
    colunas_float = [
        'vazao_atual_l_s', 'vazao_projetada_l_s', 'vazao_total_l_s',
        'volume_atual_m3', 'volume_projetado_m3', 'volume_total_m3',
        'altura_manometrica_mca', 'altura_torre_m', 'potencia_cv',
        'latitude', 'longitude',
    ]
    colunas_int = ['estruturante', 'esteira_sabesp', 'invest_obr']

    for col in colunas_float:
        if col in df.columns:
            df[col] = df[col].apply(_converter_float)

    for col in colunas_int:
        if col in df.columns:
            df[col] = df[col].apply(_converter_int).astype('Int64')

    return df


def normalizar_areas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza DataFrame de áreas de expansão."""
    if df.empty:
        return df

    df = df.copy()

    # Normalizar textos
    if 'layer' in df.columns:
        df['layer'] = df['layer'].apply(normalizar_layer)

    # Converter numéricos
    colunas_float = ['area', 'qtd_domicilios', 'ibge']
    colunas_int = [
        'consolidado', 'anexo_ii', 'condominio', 'global',
        'projeto_sas', 'projeto_ses', 'esgoto_individual',
        'area_com_impedimento', 'soleira_negativa', 'agua_individual',
        'area_atendida', 'abast_sist_integrado', 'inativo',
        'complexidade_ambiental', 'obra_execucao', 'concepcao',
        'atendido_agua', 'atendido_esgoto', 'global_agua', 'global_esgoto',
        'formal_caract_rural',
    ]

    for col in colunas_float:
        if col in df.columns:
            df[col] = df[col].apply(_converter_float)

    for col in colunas_int:
        if col in df.columns:
            df[col] = df[col].apply(_converter_int).astype('Int64')

    return df


def normalizar_todos(dados: dict) -> dict:
    """Normaliza os 3 DataFrames de uma vez."""
    return {
        'areas': normalizar_areas(dados.get('areas', pd.DataFrame())),
        'linear': normalizar_linear(dados.get('linear', pd.DataFrame())),
        'pontual': normalizar_pontual(dados.get('pontual', pd.DataFrame())),
    }
