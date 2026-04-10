"""
parser_kml.py — Parsing de arquivos KML de concepção de saneamento.

Extrai 3 camadas distintas de cada KML:
- areas_expansao_filtradas (polígonos)
- concepcao_linear_filtrada (linhas — redes/tubulações)
- concepcao_pontual_filtrada (pontos — equipamentos)
"""

import pandas as pd
import numpy as np
from lxml import etree
from io import BytesIO
from typing import Optional

NS = {'kml': 'http://www.opengis.net/kml/2.2'}

FOLDER_AREAS = 'areas_expansao_filtradas'
FOLDER_LINEAR = 'concepcao_linear_filtrada'
FOLDER_PONTUAL = 'concepcao_pontual_filtrada'


def carregar_kml(arquivo) -> etree._ElementTree:
    """Lê arquivo KML (path ou BytesIO) e retorna árvore XML."""
    if isinstance(arquivo, (str, bytes)):
        return etree.parse(arquivo)
    if isinstance(arquivo, BytesIO):
        arquivo.seek(0)
    return etree.parse(arquivo)


def extrair_coordenadas(placemark) -> list[tuple[float, float]]:
    """Extrai lista de (lon, lat) de qualquer geometria do placemark."""
    coordenadas = []
    elems = placemark.findall('.//{http://www.opengis.net/kml/2.2}coordinates')
    if not elems:
        elems = placemark.findall('.//coordinates')
    for elem_coords in elems:
        texto = elem_coords.text
        if not texto:
            continue
        for ponto in texto.strip().split():
            partes = ponto.strip().split(',')
            if len(partes) >= 2:
                try:
                    lon = float(partes[0])
                    lat = float(partes[1])
                    coordenadas.append((lon, lat))
                except ValueError:
                    continue
    return coordenadas


def calcular_centroide(coordenadas: list[tuple[float, float]]) -> tuple[float, float]:
    """Calcula centroide (lon, lat) médio de uma lista de coordenadas."""
    if not coordenadas:
        return (0.0, 0.0)
    arr = np.array(coordenadas)
    return (float(arr[:, 0].mean()), float(arr[:, 1].mean()))


def _extrair_dados_placemark(placemark) -> dict:
    """Extrai dados de um placemark (SimpleData ou Data/value, com ou sem namespace)."""
    dados = {}

    # Tentar SchemaData/SimpleData — com namespace KML
    sds = placemark.findall('.//{http://www.opengis.net/kml/2.2}SimpleData')
    if not sds:
        # Alguns exportadores (QGIS, ArcGIS) omitem namespace nos elementos de dados
        sds = placemark.findall('.//SimpleData')
    for sd in sds:
        nome = sd.get('name')
        valor = (sd.text or '').strip()
        if nome:
            dados[nome] = valor

    # Se SimpleData não encontrou nada, tentar formato Data/value
    if not dados:
        data_elems = placemark.findall('.//{http://www.opengis.net/kml/2.2}Data')
        if not data_elems:
            data_elems = placemark.findall('.//Data')
        for de in data_elems:
            nome = de.get('name')
            val_el = de.find('{http://www.opengis.net/kml/2.2}value')
            if val_el is None:
                val_el = de.find('value')
            if nome and val_el is not None:
                dados[nome] = (val_el.text or '').strip()

    return dados


def _extrair_placemarks_folder(arvore: etree._ElementTree, nome_folder: str) -> list[dict]:
    """Extrai todos os placemarks de um folder específico."""
    registros = []

    # Buscar folders com namespace KML; fallback sem namespace
    folders = arvore.findall('.//kml:Folder', NS)
    if not folders:
        folders = arvore.findall('.//Folder')

    for folder in folders:
        nome = folder.find('kml:name', NS)
        if nome is None:
            nome = folder.find('name')
        if nome is None or nome.text != nome_folder:
            continue

        placemarks = folder.findall('kml:Placemark', NS)
        if not placemarks:
            placemarks = folder.findall('Placemark')

        for pm in placemarks:
            dados = _extrair_dados_placemark(pm)
            coords = extrair_coordenadas(pm)
            dados['_coordenadas'] = coords
            lon_c, lat_c = calcular_centroide(coords)
            dados['_centroide_lon'] = lon_c
            dados['_centroide_lat'] = lat_c
            dados['_num_vertices'] = len(coords)
            registros.append(dados)
    return registros


def extrair_areas_expansao(arvore: etree._ElementTree) -> pd.DataFrame:
    """Extrai áreas de expansão (polígonos) do KML."""
    registros = _extrair_placemarks_folder(arvore, FOLDER_AREAS)
    if not registros:
        return pd.DataFrame()
    return pd.DataFrame(registros)


def extrair_concepcao_linear(arvore: etree._ElementTree) -> pd.DataFrame:
    """Extrai concepção linear (redes/tubulações) do KML."""
    registros = _extrair_placemarks_folder(arvore, FOLDER_LINEAR)
    if not registros:
        return pd.DataFrame()
    df = pd.DataFrame(registros)
    # Guardar coordenadas do primeiro e último ponto para análise de declividade
    if '_coordenadas' in df.columns:
        df['_coord_inicio'] = df['_coordenadas'].apply(
            lambda c: c[0] if c else None
        )
        df['_coord_fim'] = df['_coordenadas'].apply(
            lambda c: c[-1] if c else None
        )
    return df


def extrair_concepcao_pontual(arvore: etree._ElementTree) -> pd.DataFrame:
    """Extrai concepção pontual (equipamentos) do KML."""
    registros = _extrair_placemarks_folder(arvore, FOLDER_PONTUAL)
    if not registros:
        return pd.DataFrame()
    return pd.DataFrame(registros)


def kml_para_dataframes(arquivo, nome_lote: Optional[str] = None) -> dict:
    """
    Converte KML em 3 DataFrames: areas, linear, pontual.

    Retorna dict com chaves 'areas', 'linear', 'pontual'.
    """
    arvore = carregar_kml(arquivo)

    df_areas = extrair_areas_expansao(arvore)
    df_linear = extrair_concepcao_linear(arvore)
    df_pontual = extrair_concepcao_pontual(arvore)

    if nome_lote:
        for df in [df_areas, df_linear, df_pontual]:
            if not df.empty:
                df.insert(0, 'lote', nome_lote)

    return {
        'areas': df_areas,
        'linear': df_linear,
        'pontual': df_pontual,
    }


def consolidar_multiplos_kml(arquivos: list[tuple], nomes: list[str] = None) -> dict:
    """
    Consolida múltiplos KMLs em 3 DataFrames unificados.

    Args:
        arquivos: lista de paths ou BytesIO
        nomes: lista de nomes dos lotes (ex: ['Lote_13', 'Lote_14', ...])

    Retorna dict com 'areas', 'linear', 'pontual' consolidados.
    """
    todas_areas = []
    todos_linear = []
    todos_pontual = []

    for i, arq in enumerate(arquivos):
        nome = nomes[i] if nomes and i < len(nomes) else f'Arquivo_{i+1}'
        resultado = kml_para_dataframes(arq, nome_lote=nome)

        if not resultado['areas'].empty:
            todas_areas.append(resultado['areas'])
        if not resultado['linear'].empty:
            todos_linear.append(resultado['linear'])
        if not resultado['pontual'].empty:
            todos_pontual.append(resultado['pontual'])

    return {
        'areas': pd.concat(todas_areas, ignore_index=True) if todas_areas else pd.DataFrame(),
        'linear': pd.concat(todos_linear, ignore_index=True) if todos_linear else pd.DataFrame(),
        'pontual': pd.concat(todos_pontual, ignore_index=True) if todos_pontual else pd.DataFrame(),
    }
