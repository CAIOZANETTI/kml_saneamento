"""
elevacao.py — Consulta de elevação via API Open-Meteo / OpenTopoData.

Inspirado no projeto kml-earthworks (github.com/CAIOZANETTI/kml-earthworks).
Os KMLs não possuem elevação (apenas lon, lat). Este módulo obtém a
elevação do terreno via DEM para análise de declividade em redes de esgoto.
"""

import time
import numpy as np
import pandas as pd
import requests

_METEO_URL = "https://api.open-meteo.com/v1/elevation"
_TOPO_URL = "https://api.opentopodata.org/v1/srtm30m"
_BATCH_SIZE = 100
_METEO_RETRIES = [0, 0.5]
_TOPO_RETRIES = [0, 1, 3]
_TOPO_DELAY = 0.8


def consultar_open_meteo(lats: list[float], lons: list[float]) -> list[float | None]:
    """Consulta elevação via Open-Meteo (Copernicus DEM GLO-90, ~4m precisão)."""
    params = {
        'latitude': ','.join(str(l) for l in lats),
        'longitude': ','.join(str(l) for l in lons),
    }
    for i, delay in enumerate(_METEO_RETRIES):
        if delay > 0:
            time.sleep(delay)
        try:
            resp = requests.get(_METEO_URL, params=params, timeout=(3, 8))
            if resp.status_code == 429:
                wait = _extrair_tempo_espera(resp.text)
                time.sleep(wait)
                continue
            resp.raise_for_status()
            elevacoes = resp.json().get('elevation', [])
            if len(elevacoes) == len(lats):
                return [e if e is not None else None for e in elevacoes]
        except Exception:
            if i == len(_METEO_RETRIES) - 1:
                return [None] * len(lats)
    return [None] * len(lats)


def _extrair_tempo_espera(texto: str) -> float:
    """Tenta extrair tempo de espera de resposta 429."""
    import re
    match = re.search(r'(\d+)\s*minute', texto)
    if match:
        return int(match.group(1)) * 60
    match = re.search(r'(\d+)\s*second', texto)
    if match:
        return int(match.group(1))
    return 60


def consultar_opentopodata(lats: list[float], lons: list[float]) -> list[float | None]:
    """Consulta elevação via OpenTopoData (SRTM30m, fallback)."""
    locations = '|'.join(f'{lat},{lon}' for lat, lon in zip(lats, lons))
    for i, delay in enumerate(_TOPO_RETRIES):
        if delay > 0:
            time.sleep(delay)
        try:
            resp = requests.post(
                _TOPO_URL,
                data={'locations': locations},
                timeout=(3, 10),
            )
            resp.raise_for_status()
            results = resp.json().get('results', [])
            return [r.get('elevation') for r in results]
        except Exception:
            if i == len(_TOPO_RETRIES) - 1:
                return [None] * len(lats)
    return [None] * len(lats)


def consultar_elevacao_batch(
    coordenadas: list[tuple[float, float]],
    progresso_callback=None,
) -> list[float | None]:
    """
    Consulta elevação para lista de (lat, lon).
    Usa Open-Meteo como primário e OpenTopoData como fallback.

    Args:
        coordenadas: lista de (lat, lon)
        progresso_callback: função(pct: float) chamada com progresso 0-100

    Returns:
        lista de elevações em metros (None se falhou)
    """
    if not coordenadas:
        return []

    n = len(coordenadas)
    elevacoes = [None] * n
    cooldown_meteo = False

    for inicio in range(0, n, _BATCH_SIZE):
        fim = min(inicio + _BATCH_SIZE, n)
        batch = coordenadas[inicio:fim]
        lats = [c[0] for c in batch]
        lons = [c[1] for c in batch]

        resultado = None

        # Tentar Open-Meteo primeiro
        if not cooldown_meteo:
            resultado = consultar_open_meteo(lats, lons)
            if all(r is None for r in resultado):
                cooldown_meteo = True
                resultado = None

        # Fallback para OpenTopoData
        if resultado is None or all(r is None for r in resultado):
            time.sleep(_TOPO_DELAY)
            resultado = consultar_opentopodata(lats, lons)

        for j, elev in enumerate(resultado):
            elevacoes[inicio + j] = elev

        if progresso_callback:
            progresso_callback(fim / n * 100)

    return elevacoes


def enriquecer_linear_com_elevacao(
    df: pd.DataFrame,
    progresso_callback=None,
) -> pd.DataFrame:
    """
    Adiciona elevação de montante e jusante nos trechos lineares.

    Usa as coordenadas do primeiro e último ponto de cada trecho.
    """
    if df.empty or '_coord_inicio' not in df.columns:
        return df

    df = df.copy()

    # Coletar todas as coordenadas únicas (início e fim de cada trecho)
    coords_unicas = {}
    for _, row in df.iterrows():
        ci = row.get('_coord_inicio')
        cf = row.get('_coord_fim')
        if ci and isinstance(ci, tuple):
            key = (round(ci[1], 7), round(ci[0], 7))  # (lat, lon)
            coords_unicas[key] = None
        if cf and isinstance(cf, tuple):
            key = (round(cf[1], 7), round(cf[0], 7))  # (lat, lon)
            coords_unicas[key] = None

    # Consultar elevação
    lista_coords = list(coords_unicas.keys())
    if not lista_coords:
        return df

    elevacoes = consultar_elevacao_batch(lista_coords, progresso_callback)

    for coord, elev in zip(lista_coords, elevacoes):
        coords_unicas[coord] = elev

    # Atribuir ao DataFrame
    elev_montante = []
    elev_jusante = []
    for _, row in df.iterrows():
        ci = row.get('_coord_inicio')
        cf = row.get('_coord_fim')

        em = None
        if ci and isinstance(ci, tuple):
            key = (round(ci[1], 7), round(ci[0], 7))
            em = coords_unicas.get(key)

        ej = None
        if cf and isinstance(cf, tuple):
            key = (round(cf[1], 7), round(cf[0], 7))
            ej = coords_unicas.get(key)

        elev_montante.append(em)
        elev_jusante.append(ej)

    df['elevacao_montante_m'] = elev_montante
    df['elevacao_jusante_m'] = elev_jusante

    return df


def enriquecer_pontual_com_elevacao(
    df: pd.DataFrame,
    progresso_callback=None,
) -> pd.DataFrame:
    """Adiciona elevação nos equipamentos pontuais usando centroide."""
    if df.empty:
        return df

    df = df.copy()

    coords = []
    for _, row in df.iterrows():
        lat = row.get('_centroide_lat', row.get('latitude'))
        lon = row.get('_centroide_lon', row.get('longitude'))
        if pd.notna(lat) and pd.notna(lon):
            coords.append((float(lat), float(lon)))
        else:
            coords.append(None)

    coords_validas = [(c[0], c[1]) for c in coords if c is not None]
    if not coords_validas:
        return df

    elevacoes = consultar_elevacao_batch(coords_validas, progresso_callback)

    idx_elev = 0
    elev_lista = []
    for c in coords:
        if c is not None:
            elev_lista.append(elevacoes[idx_elev])
            idx_elev += 1
        else:
            elev_lista.append(None)

    df['elevacao_m'] = elev_lista
    return df
