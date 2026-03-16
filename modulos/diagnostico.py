"""
diagnostico.py — Cálculos de engenharia, resumos e verificações normativas.

Inclui: extensões, contagens, declividade (NBR 9649), espaçamento PV,
capacidade ETE × Manning.
"""

import math
import numpy as np
import pandas as pd


# ── Resumos de Extensão (Linear) ───────────────────────────────────

def resumo_extensao_por_subtipo(df: pd.DataFrame) -> pd.DataFrame:
    """Extensão (m) agrupada por subtipo e tipo."""
    if df.empty or 'subtipo' not in df.columns:
        return pd.DataFrame()
    return df.groupby(['subtipo', 'tipo'])['extensao_calculada_m'].agg(
        ['sum', 'count']
    ).rename(columns={'sum': 'extensao_m', 'count': 'qtd_trechos'}).reset_index().sort_values(
        'extensao_m', ascending=False
    )


def resumo_extensao_por_material(df: pd.DataFrame) -> pd.DataFrame:
    """Extensão (m) agrupada por material."""
    if df.empty or 'material' not in df.columns:
        return pd.DataFrame()
    return df.groupby('material')['extensao_calculada_m'].agg(
        ['sum', 'count']
    ).rename(columns={'sum': 'extensao_m', 'count': 'qtd_trechos'}).reset_index().sort_values(
        'extensao_m', ascending=False
    )


def resumo_extensao_por_diametro(df: pd.DataFrame) -> pd.DataFrame:
    """Extensão (m) agrupada por diâmetro nominal."""
    if df.empty or 'diametro_nominal_mm' not in df.columns:
        return pd.DataFrame()
    return df.groupby('diametro_nominal_mm')['extensao_calculada_m'].agg(
        ['sum', 'count']
    ).rename(columns={'sum': 'extensao_m', 'count': 'qtd_trechos'}).reset_index().sort_values(
        'extensao_m', ascending=False
    )


def resumo_extensao_por_municipio(df: pd.DataFrame) -> pd.DataFrame:
    """Extensão (m) agrupada por município."""
    if df.empty or 'nm_mun' not in df.columns:
        return pd.DataFrame()
    return df.groupby('nm_mun')['extensao_calculada_m'].agg(
        ['sum', 'count']
    ).rename(columns={'sum': 'extensao_m', 'count': 'qtd_trechos'}).reset_index().sort_values(
        'extensao_m', ascending=False
    )


def resumo_extensao_por_metodo(df: pd.DataFrame) -> pd.DataFrame:
    """Extensão (m) agrupada por método construtivo."""
    if df.empty or 'metodo_construtivo' not in df.columns:
        return pd.DataFrame()
    return df.groupby('metodo_construtivo')['extensao_calculada_m'].agg(
        ['sum', 'count']
    ).rename(columns={'sum': 'extensao_m', 'count': 'qtd_trechos'}).reset_index().sort_values(
        'extensao_m', ascending=False
    )


# ── Resumos de Equipamentos (Pontual) ──────────────────────────────

def resumo_equipamentos(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem de equipamentos por subtipo."""
    if df.empty or 'subtipo' not in df.columns:
        return pd.DataFrame()
    return df.groupby('subtipo').size().reset_index(
        name='quantidade'
    ).sort_values('quantidade', ascending=False)


def resumo_etes(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela específica de ETEs com vazões e volumes."""
    if df.empty:
        return pd.DataFrame()
    etes = df[df['subtipo'] == 'ETE'].copy()
    if etes.empty:
        return pd.DataFrame()
    colunas = ['lote', 'nm_mun', 'nome', 'setor', 'vazao_atual_l_s',
               'vazao_projetada_l_s', 'vazao_total_l_s',
               'volume_atual_m3', 'volume_projetado_m3', 'volume_total_m3',
               'notas_tecnicas', 'id_empreendimento']
    return etes[[c for c in colunas if c in etes.columns]].reset_index(drop=True)


def resumo_reservatorios(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela específica de Reservatórios."""
    if df.empty:
        return pd.DataFrame()
    res = df[df['subtipo'] == 'Reservatório'].copy()
    if res.empty:
        return pd.DataFrame()
    colunas = ['lote', 'nm_mun', 'nome', 'tipo',
               'volume_atual_m3', 'volume_projetado_m3', 'volume_total_m3',
               'id_empreendimento']
    return res[[c for c in colunas if c in res.columns]].reset_index(drop=True)


def resumo_pocos(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela específica de Poços Profundos."""
    if df.empty:
        return pd.DataFrame()
    pocos = df[df['subtipo'] == 'Poço Profundo'].copy()
    if pocos.empty:
        return pd.DataFrame()
    colunas = ['lote', 'nm_mun', 'nome',
               'vazao_atual_l_s', 'vazao_projetada_l_s', 'vazao_total_l_s',
               'id_empreendimento']
    return pocos[[c for c in colunas if c in pocos.columns]].reset_index(drop=True)


def resumo_eee(df: pd.DataFrame) -> pd.DataFrame:
    """Tabela específica de EEE (Elevatórias de Esgoto)."""
    if df.empty:
        return pd.DataFrame()
    eee = df[df['subtipo'] == 'EEE'].copy()
    if eee.empty:
        return pd.DataFrame()
    colunas = ['lote', 'nm_mun', 'nome',
               'vazao_total_l_s', 'altura_manometrica_mca', 'potencia_cv',
               'id_empreendimento']
    return eee[[c for c in colunas if c in eee.columns]].reset_index(drop=True)


# ── Resumos de Áreas de Expansão ───────────────────────────────────

def resumo_areas_por_prioridade(df: pd.DataFrame) -> pd.DataFrame:
    """Áreas agrupadas por prioridade."""
    if df.empty or 'prioridade' not in df.columns:
        return pd.DataFrame()
    return df.groupby('prioridade').agg(
        quantidade=('prioridade', 'size'),
        domicilios=('qtd_domicilios', 'sum'),
        area_total_m2=('area', 'sum'),
    ).reset_index().sort_values('prioridade')


def resumo_areas_por_municipio(df: pd.DataFrame) -> pd.DataFrame:
    """Áreas agrupadas por município."""
    if df.empty or 'nm_mun' not in df.columns:
        return pd.DataFrame()
    return df.groupby('nm_mun').agg(
        quantidade=('nm_mun', 'size'),
        domicilios=('qtd_domicilios', 'sum'),
        area_total_m2=('area', 'sum'),
    ).reset_index().sort_values('domicilios', ascending=False)


def resumo_areas_por_servico(df: pd.DataFrame) -> pd.DataFrame:
    """Áreas agrupadas por tipo de serviço (layer)."""
    if df.empty or 'layer' not in df.columns:
        return pd.DataFrame()
    return df.groupby('layer').agg(
        quantidade=('layer', 'size'),
        domicilios=('qtd_domicilios', 'sum'),
        area_total_m2=('area', 'sum'),
    ).reset_index().sort_values('quantidade', ascending=False)


# ── Totalizadores ──────────────────────────────────────────────────

def total_domicilios(df: pd.DataFrame) -> int:
    if df.empty or 'qtd_domicilios' not in df.columns:
        return 0
    return int(df['qtd_domicilios'].sum())


def total_area_m2(df: pd.DataFrame) -> float:
    if df.empty or 'area' not in df.columns:
        return 0.0
    return float(df['area'].sum())


# ── Análise de Declividade (Esgoto por Gravidade) ──────────────────

# Declividade mínima NBR 9649 (%)
DECLIVIDADE_MINIMA_NBR = {
    100: 0.50, 110: 0.50, 150: 0.50,
    200: 0.35,
    250: 0.25,
    300: 0.20,
    400: 0.15, 500: 0.15, 600: 0.15,
}


def _obter_declividade_minima(dn_mm: int) -> float:
    """Retorna declividade mínima para um DN (%), baseado na NBR 9649."""
    if dn_mm <= 150:
        return 0.50
    if dn_mm <= 200:
        return 0.35
    if dn_mm <= 250:
        return 0.25
    if dn_mm <= 300:
        return 0.20
    return 0.15


def calcular_declividade_trecho(elev_montante: float, elev_jusante: float,
                                  extensao_m: float) -> float:
    """Calcula declividade em % (positivo = descendo)."""
    if extensao_m <= 0:
        return 0.0
    return (elev_montante - elev_jusante) / extensao_m * 100


def classificar_declividade(declividade_pct: float, dn_mm: int) -> str:
    """Classifica declividade conforme NBR 9649."""
    minimo = _obter_declividade_minima(dn_mm)
    if declividade_pct < 0:
        return 'Contra-fluxo'
    if declividade_pct < minimo:
        return 'Insuficiente'
    return 'Adequada'


def analisar_trechos_esgoto(df: pd.DataFrame) -> pd.DataFrame:
    """
    Analisa declividade de trechos de esgoto com elevação disponível.

    Requer colunas: elevacao_montante_m, elevacao_jusante_m,
    extensao_calculada_m, diametro_nominal_mm.
    """
    if df.empty:
        return df

    mascara = (
        (df['tipo'] == 'Esgoto') &
        df['elevacao_montante_m'].notna() &
        df['elevacao_jusante_m'].notna() &
        (df['extensao_calculada_m'] > 0)
    )
    esgoto = df[mascara].copy()
    if esgoto.empty:
        return esgoto

    esgoto['desnivel_m'] = esgoto['elevacao_montante_m'] - esgoto['elevacao_jusante_m']
    esgoto['declividade_pct'] = esgoto.apply(
        lambda r: calcular_declividade_trecho(
            r['elevacao_montante_m'], r['elevacao_jusante_m'], r['extensao_calculada_m']
        ), axis=1
    )
    esgoto['declividade_status'] = esgoto.apply(
        lambda r: classificar_declividade(
            r['declividade_pct'],
            int(r['diametro_nominal_mm']) if pd.notna(r.get('diametro_nominal_mm')) else 150
        ), axis=1
    )
    return esgoto


def resumo_declividade(df_analise: pd.DataFrame) -> pd.DataFrame:
    """Resumo de declividade: contagem e extensão por status."""
    if df_analise.empty or 'declividade_status' not in df_analise.columns:
        return pd.DataFrame()
    return df_analise.groupby('declividade_status').agg(
        qtd_trechos=('declividade_status', 'size'),
        extensao_m=('extensao_calculada_m', 'sum'),
    ).reset_index()


# ── Verificação de Espaçamento PV (NBR 9649) ──────────────────────

def verificar_espacamento_pv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verifica espaçamento entre PVs (extensão do trecho de rede coletora).
    NBR 9649: máx 100m (sem equip.) / 150m (com limpeza mecânica).
    """
    if df.empty:
        return df

    mascara = (
        (df['tipo'] == 'Esgoto') &
        (df['subtipo'].isin(['Rede Coletora', 'Coletor Tronco'])) &
        (df['extensao_calculada_m'] > 0)
    )
    esgoto = df[mascara].copy()
    if esgoto.empty:
        return esgoto

    def _classificar_pv(ext):
        if ext <= 100:
            return 'Adequado (≤100m)'
        if ext <= 150:
            return 'Aceitável (100-150m)'
        return 'Excede norma (>150m)'

    esgoto['pv_status'] = esgoto['extensao_calculada_m'].apply(_classificar_pv)
    return esgoto


def resumo_espacamento_pv(df_verif: pd.DataFrame) -> pd.DataFrame:
    """Resumo de espaçamento PV por status."""
    if df_verif.empty or 'pv_status' not in df_verif.columns:
        return pd.DataFrame()
    return df_verif.groupby('pv_status').agg(
        qtd_trechos=('pv_status', 'size'),
        extensao_m=('extensao_calculada_m', 'sum'),
    ).reset_index()


# ── Verificação ETE × Vazão da Rede (Manning) ─────────────────────

# Coeficientes de rugosidade de Manning
RUGOSIDADE_MANNING = {
    'PVC': 0.013,
    'PVC-O': 0.013,
    'PEAD': 0.012,
    'FoFo': 0.014,
    'DEFoFo': 0.013,
    'Concreto': 0.015,
}


def calcular_vazao_manning(dn_mm: int, material: str = 'PVC',
                            declividade_pct: float = 0.5) -> float:
    """
    Calcula vazão máxima (L/s) pela fórmula de Manning para seção plena circular.

    Q = (1/n) × A × R^(2/3) × S^(1/2)
    """
    d = dn_mm / 1000  # diâmetro em metros
    n = RUGOSIDADE_MANNING.get(material, 0.013)
    s = declividade_pct / 100  # declividade como fração

    if s <= 0:
        return 0.0

    a = math.pi * d**2 / 4  # área seção plena
    p = math.pi * d  # perímetro molhado
    r = a / p  # raio hidráulico

    q = (1 / n) * a * r**(2/3) * s**0.5  # m³/s
    return q * 1000  # L/s


def verificar_capacidade_ete(df_pontual: pd.DataFrame,
                              df_linear: pd.DataFrame) -> pd.DataFrame:
    """
    Verifica se a ETE suporta a vazão da rede conectada.

    Vincula ETE → Rede por id_empreendimento ou nm_mun.
    Calcula vazão máxima do maior DN que chega na ETE (Manning).
    """
    if df_pontual.empty or df_linear.empty:
        return pd.DataFrame()

    etes = df_pontual[df_pontual['subtipo'] == 'ETE'].copy()
    if etes.empty:
        return pd.DataFrame()

    esgoto = df_linear[df_linear['tipo'] == 'Esgoto'].copy()
    if esgoto.empty:
        return pd.DataFrame()

    resultados = []
    for _, ete in etes.iterrows():
        empr = str(ete.get('id_empreendimento', ''))
        mun = str(ete.get('nm_mun', ''))

        # Buscar rede vinculada
        if empr and empr != '' and empr != 'nan':
            rede = esgoto[esgoto['id_empreendimento'].astype(str) == empr]
        else:
            rede = esgoto[esgoto['nm_mun'].astype(str) == mun]

        if rede.empty:
            continue

        # Maior DN da rede
        dn_max = rede['diametro_nominal_mm'].dropna().astype(int).max() if not rede['diametro_nominal_mm'].dropna().empty else 150
        material_moda = rede['material'].mode().iloc[0] if not rede['material'].mode().empty else 'PVC'
        ext_total = rede['extensao_calculada_m'].sum()

        # Calcular Manning com declividade padrão 0.5%
        vazao_max = calcular_vazao_manning(dn_max, material_moda, 0.5)
        vazao_ete = ete.get('vazao_total_l_s', np.nan)

        # Classificar
        if pd.isna(vazao_ete) or pd.isna(vazao_max) or vazao_max == 0:
            status = 'Sem dados'
        elif vazao_max < vazao_ete * 0.8:
            status = 'Rede insuficiente'
        elif vazao_ete < vazao_max * 0.3:
            status = 'ETE subdimensionada'
        else:
            status = 'Compatível'

        resultados.append({
            'lote': ete.get('lote', ''),
            'nm_mun': mun,
            'nome_ete': ete.get('nome', ''),
            'vazao_ete_total_l_s': vazao_ete,
            'dn_chegada_mm': dn_max,
            'material_predominante': material_moda,
            'vazao_manning_l_s': round(vazao_max, 2),
            'extensao_rede_m': round(ext_total, 0),
            'qtd_trechos_rede': len(rede),
            'ete_status': status,
            'id_empreendimento': empr,
        })

    return pd.DataFrame(resultados) if resultados else pd.DataFrame()


# ── Resumo Textual ─────────────────────────────────────────────────

def gerar_resumo_textual(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                          df_areas: pd.DataFrame) -> str:
    """Gera resumo textual descritivo do dataset."""
    partes = []

    # Linear
    if not df_linear.empty:
        ext_total = df_linear['extensao_calculada_m'].sum()
        n_trechos = len(df_linear)
        n_mun = df_linear['nm_mun'].nunique()
        n_lotes = df_linear['lote'].nunique() if 'lote' in df_linear.columns else 0

        ext_agua = df_linear[df_linear['tipo'] == 'Água']['extensao_calculada_m'].sum()
        ext_esgoto = df_linear[df_linear['tipo'] == 'Esgoto']['extensao_calculada_m'].sum()

        mat_top = df_linear.groupby('material')['extensao_calculada_m'].sum().sort_values(ascending=False)
        mat_str = ', '.join(f'{m} ({v/ext_total*100:.0f}%)' for m, v in mat_top.head(3).items())

        partes.append(
            f"Escopo: {n_lotes} lotes com {n_trechos:,} trechos de rede "
            f"({ext_total/1000:,.1f} km) em {n_mun} municípios de SP."
        )
        partes.append(
            f"Redes: {ext_agua/1000:,.1f} km de distribuição (água) + "
            f"{ext_esgoto/1000:,.1f} km de esgoto. "
            f"Materiais: {mat_str}."
        )

    # Pontual
    if not df_pontual.empty:
        contagens = df_pontual['subtipo'].value_counts()
        itens = []
        for subtipo in ['EEE', 'Reservatório', 'Booster', 'Poço Profundo', 'ETE', 'VRP', 'ETA']:
            if subtipo in contagens.index:
                itens.append(f"{contagens[subtipo]} {subtipo}")
        if itens:
            partes.append(f"Equipamentos: {', '.join(itens)}.")

    # Áreas
    if not df_areas.empty:
        n_areas = len(df_areas)
        dom = total_domicilios(df_areas)
        area_km2 = total_area_m2(df_areas) / 1e6
        n_mun_areas = df_areas['nm_mun'].nunique()
        partes.append(
            f"Áreas de expansão: {n_areas} polígonos, "
            f"{dom:,} domicílios a atender, {area_km2:,.1f} km² em {n_mun_areas} municípios."
        )

    return '\n'.join(partes) if partes else "Nenhum dado disponível."
