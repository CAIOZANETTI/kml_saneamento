"""
relatorios.py — Gráficos Plotly e mapas pydeck para visualização.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pydeck as pdk

# Cores padrão
COR_AGUA = '#1E88E5'
COR_ESGOTO = '#6D4C41'
COR_AMBOS = '#43A047'
CORES_STATUS = {
    'Adequada': '#43A047',
    'Insuficiente': '#FB8C00',
    'Contra-fluxo': '#E53935',
}
CORES_PV = {
    'Adequado (≤100m)': '#43A047',
    'Aceitável (100-150m)': '#FB8C00',
    'Excede norma (>150m)': '#E53935',
}
CORES_ETE = {
    'Compatível': '#43A047',
    'Rede insuficiente': '#FB8C00',
    'ETE subdimensionada': '#E53935',
    'Sem dados': '#9E9E9E',
}

LAYOUT_PADRAO = dict(
    font=dict(family='sans-serif', size=12),
    margin=dict(l=20, r=20, t=40, b=20),
    height=400,
    plot_bgcolor='white',
)


def _aplicar_layout(fig, titulo=''):
    fig.update_layout(**LAYOUT_PADRAO, title=titulo)
    return fig


# ── Gráficos de Redes ──────────────────────────────────────────────

def grafico_extensao_por_subtipo(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.bar(
        resumo, x='extensao_m', y='subtipo', color='tipo',
        orientation='h', text='extensao_m',
        color_discrete_map={'Água': COR_AGUA, 'Esgoto': COR_ESGOTO},
    )
    fig.update_traces(texttemplate='%{text:,.0f}m', textposition='outside')
    return _aplicar_layout(fig, 'Extensão por Subtipo (m)')


def grafico_extensao_por_diametro(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    resumo = resumo.sort_values('diametro_nominal_mm')
    fig = px.bar(
        resumo, x='extensao_m', y='diametro_nominal_mm',
        orientation='h', text='extensao_m',
    )
    fig.update_traces(texttemplate='%{text:,.0f}m', textposition='outside',
                      marker_color=COR_AGUA)
    fig.update_yaxes(type='category', title='DN (mm)')
    return _aplicar_layout(fig, 'Extensão por Diâmetro (m)')


def grafico_extensao_por_material(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.pie(
        resumo, values='extensao_m', names='material',
        hole=0.4,
    )
    fig.update_traces(textinfo='label+percent', textposition='outside')
    return _aplicar_layout(fig, 'Extensão por Material')


def grafico_extensao_por_municipio(resumo: pd.DataFrame, top_n: int = 15) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    top = resumo.head(top_n).sort_values('extensao_m')
    fig = px.bar(
        top, x='extensao_m', y='nm_mun',
        orientation='h', text='extensao_m',
    )
    fig.update_traces(texttemplate='%{text:,.0f}m', textposition='outside',
                      marker_color=COR_AGUA)
    return _aplicar_layout(fig, f'Extensão por Município — Top {top_n} (m)')


def grafico_extensao_por_metodo(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.bar(
        resumo, x='metodo_construtivo', y='extensao_m', text='qtd_trechos',
    )
    fig.update_traces(texttemplate='%{text} trechos', textposition='outside',
                      marker_color=COR_ESGOTO)
    return _aplicar_layout(fig, 'Extensão por Método Construtivo (m)')


# ── Gráficos de Equipamentos ──────────────────────────────────────

def grafico_equipamentos_por_tipo(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.bar(
        resumo, x='quantidade', y='subtipo',
        orientation='h', text='quantidade',
    )
    fig.update_traces(textposition='outside', marker_color=COR_ESGOTO)
    return _aplicar_layout(fig, 'Equipamentos por Tipo')


# ── Gráficos de Áreas ─────────────────────────────────────────────

def grafico_areas_por_prioridade(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.bar(
        resumo, x='prioridade', y='domicilios', text='quantidade',
        color='prioridade',
    )
    fig.update_traces(texttemplate='%{text} áreas', textposition='outside')
    return _aplicar_layout(fig, 'Domicílios por Prioridade')


def grafico_areas_por_servico(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    cores = {'Água': COR_AGUA, 'Esgoto': COR_ESGOTO, 'Água e Esgoto': COR_AMBOS}
    fig = px.pie(
        resumo, values='quantidade', names='layer',
        hole=0.4, color='layer', color_discrete_map=cores,
    )
    fig.update_traces(textinfo='label+percent+value', textposition='outside')
    return _aplicar_layout(fig, 'Áreas por Tipo de Serviço')


def grafico_areas_por_recorte(df_areas: pd.DataFrame) -> go.Figure:
    if df_areas.empty or 'recorte' not in df_areas.columns:
        return go.Figure()
    contagem = df_areas['recorte'].value_counts().reset_index()
    contagem.columns = ['recorte', 'quantidade']
    fig = px.pie(contagem, values='quantidade', names='recorte', hole=0.4)
    fig.update_traces(textinfo='label+percent+value', textposition='outside')
    return _aplicar_layout(fig, 'Áreas por Recorte')


def grafico_domicilios_por_municipio(resumo: pd.DataFrame, top_n: int = 15) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    top = resumo.head(top_n).sort_values('domicilios')
    fig = px.bar(
        top, x='domicilios', y='nm_mun',
        orientation='h', text='domicilios',
    )
    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside',
                      marker_color=COR_AMBOS)
    return _aplicar_layout(fig, f'Domicílios por Município — Top {top_n}')


# ── Gráficos de Elevação / Declividade ─────────────────────────────

def grafico_perfil_longitudinal(coords: list, elevacoes: list,
                                  info: dict = None) -> go.Figure:
    """Gráfico de perfil longitudinal de um trecho."""
    if not coords or not elevacoes:
        return go.Figure()

    # Calcular distância acumulada
    distancias = [0]
    for i in range(1, len(coords)):
        lon1, lat1 = coords[i-1]
        lon2, lat2 = coords[i]
        # Haversine simplificado
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)
        a = np.sin(dlat/2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        dist = 6371000 * c
        distancias.append(distancias[-1] + dist)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=distancias, y=elevacoes,
        mode='lines+markers',
        fill='tozeroy',
        fillcolor='rgba(30, 136, 229, 0.1)',
        line=dict(color=COR_AGUA, width=2),
        marker=dict(size=6),
        name='Terreno',
    ))
    fig.update_xaxes(title='Distância (m)')
    fig.update_yaxes(title='Elevação (m)')

    titulo = 'Perfil Longitudinal'
    if info:
        titulo += f" — {info.get('subtipo', '')} {info.get('nm_mun', '')}"

    return _aplicar_layout(fig, titulo)


def grafico_declividade_status(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.pie(
        resumo, values='qtd_trechos', names='declividade_status',
        hole=0.4,
        color='declividade_status',
        color_discrete_map=CORES_STATUS,
    )
    fig.update_traces(textinfo='label+percent+value', textposition='outside')
    return _aplicar_layout(fig, 'Status de Declividade — Esgoto')


def grafico_declividade_por_municipio(df_analise: pd.DataFrame) -> go.Figure:
    if df_analise.empty or 'declividade_status' not in df_analise.columns:
        return go.Figure()
    pivot = df_analise.groupby(['nm_mun', 'declividade_status']).size().reset_index(name='qtd')
    fig = px.bar(
        pivot, x='nm_mun', y='qtd', color='declividade_status',
        color_discrete_map=CORES_STATUS,
    )
    fig.update_xaxes(tickangle=45)
    return _aplicar_layout(fig, 'Declividade por Município')


# ── Gráficos de Verificações ──────────────────────────────────────

def grafico_espacamento_pv(resumo: pd.DataFrame) -> go.Figure:
    if resumo.empty:
        return go.Figure()
    fig = px.bar(
        resumo, x='pv_status', y='qtd_trechos', text='qtd_trechos',
        color='pv_status', color_discrete_map=CORES_PV,
    )
    fig.update_traces(textposition='outside')
    return _aplicar_layout(fig, 'Espaçamento de PV — NBR 9649')


def grafico_histograma_extensao_trechos(df: pd.DataFrame) -> go.Figure:
    if df.empty or 'extensao_calculada_m' not in df.columns:
        return go.Figure()
    esgoto = df[(df['tipo'] == 'Esgoto') & (df['subtipo'].isin(['Rede Coletora', 'Coletor Tronco']))]
    if esgoto.empty:
        return go.Figure()

    # Classificar trechos por faixa normativa
    ext = esgoto['extensao_calculada_m']
    ok = ext[ext <= 100]
    atencao = ext[(ext > 100) & (ext <= 150)]
    critico = ext[ext > 150]

    bins = dict(start=0, end=max(500, ext.max() + 10), size=10)

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=ok, xbins=bins,
        marker_color='#43A047', name='≤ 100m (adequado)',
        opacity=0.85,
    ))
    fig.add_trace(go.Histogram(
        x=atencao, xbins=bins,
        marker_color='#FB8C00', name='100-150m (aceitável)',
        opacity=0.85,
    ))
    fig.add_trace(go.Histogram(
        x=critico, xbins=bins,
        marker_color='#E53935', name='> 150m (excede norma)',
        opacity=0.85,
    ))
    fig.update_layout(barmode='stack')
    fig.add_vline(x=100, line_dash='dash', line_color='#FB8C00', line_width=2,
                  annotation_text='100m', annotation_position='top left',
                  annotation_font_size=10)
    fig.add_vline(x=150, line_dash='dash', line_color='#E53935', line_width=2,
                  annotation_text='150m', annotation_position='top left',
                  annotation_font_size=10)
    fig.update_xaxes(title='Extensão do trecho (m)', range=[0, 500], dtick=50)
    fig.update_yaxes(title='Quantidade de trechos')
    return _aplicar_layout(fig, 'Distribuição de Extensão — Rede Coletora')


def grafico_capacidade_ete(df_verif: pd.DataFrame) -> go.Figure:
    if df_verif.empty:
        return go.Figure()
    df = df_verif[df_verif['ete_status'] != 'Sem dados'].head(20).copy()
    if df.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=df['nm_mun'], x=df['vazao_ete_total_l_s'],
        name='Vazão ETE (L/s)', orientation='h',
        marker_color=COR_AMBOS,
    ))
    fig.add_trace(go.Bar(
        y=df['nm_mun'], x=df['vazao_manning_l_s'],
        name='Vazão Máx. Rede (Manning)', orientation='h',
        marker_color=COR_ESGOTO,
    ))
    fig.update_layout(barmode='group')
    return _aplicar_layout(fig, 'Capacidade ETE × Vazão Rede (L/s)')


# ── Mapas pydeck ───────────────────────────────────────────────────

def _cor_tipo(tipo: str) -> list:
    if tipo == 'Água':
        return [30, 136, 229, 180]
    return [109, 76, 65, 180]


def _cor_subtipo_pontual(subtipo: str) -> list:
    cores = {
        'ETE': [229, 57, 53, 200],
        'ETA': [30, 136, 229, 200],
        'EEE': [255, 152, 0, 200],
        'Reservatório': [30, 136, 229, 160],
        'Poço Profundo': [67, 160, 71, 200],
        'Booster': [156, 39, 176, 160],
        'VRP': [255, 193, 7, 160],
        'Captação Superficial': [0, 150, 136, 200],
        'EEAT': [255, 152, 0, 160],
        'EEAB': [255, 87, 34, 160],
    }
    return cores.get(subtipo, [158, 158, 158, 160])


def mapa_redes(df: pd.DataFrame) -> pdk.Deck:
    """Mapa com redes coloridas por tipo (Água=azul, Esgoto=marrom)."""
    if df.empty or '_coordenadas' not in df.columns:
        return None

    dados_mapa = []
    for _, row in df.iterrows():
        coords = row.get('_coordenadas', [])
        if len(coords) < 2:
            continue
        dados_mapa.append({
            'path': [[c[0], c[1]] for c in coords],
            'color': _cor_tipo(row.get('tipo', '')),
            'nome': f"{row.get('subtipo', '')} — {row.get('nm_mun', '')}",
            'extensao': f"{row.get('extensao_calculada_m', 0):.0f}m",
        })

    if not dados_mapa:
        return None

    layer = pdk.Layer(
        'PathLayer',
        data=dados_mapa,
        get_path='path',
        get_color='color',
        width_min_pixels=2,
        width_max_pixels=5,
        pickable=True,
    )

    # Centroide geral
    todas_coords = []
    for d in dados_mapa:
        todas_coords.extend(d['path'])
    arr = np.array(todas_coords)
    center_lon = arr[:, 0].mean()
    center_lat = arr[:, 1].mean()

    view = pdk.ViewState(
        longitude=center_lon, latitude=center_lat,
        zoom=8, pitch=0,
    )
    return pdk.Deck(
        layers=[layer], initial_view_state=view,
        map_style='mapbox://styles/mapbox/light-v11',
        tooltip={'text': '{nome}\n{extensao}'},
    )


def mapa_equipamentos(df: pd.DataFrame) -> pdk.Deck:
    """Mapa com equipamentos pontuais coloridos por subtipo."""
    if df.empty:
        return None

    dados_mapa = []
    for _, row in df.iterrows():
        lat = row.get('_centroide_lat', row.get('latitude'))
        lon = row.get('_centroide_lon', row.get('longitude'))
        if pd.isna(lat) or pd.isna(lon):
            continue
        dados_mapa.append({
            'position': [float(lon), float(lat)],
            'color': _cor_subtipo_pontual(row.get('subtipo', '')),
            'nome': f"{row.get('subtipo', '')} — {row.get('nm_mun', '')}",
            'detalhe': row.get('nome', ''),
        })

    if not dados_mapa:
        return None

    layer = pdk.Layer(
        'ScatterplotLayer',
        data=dados_mapa,
        get_position='position',
        get_fill_color='color',
        get_radius=500,
        pickable=True,
    )

    arr = np.array([d['position'] for d in dados_mapa])
    view = pdk.ViewState(
        longitude=arr[:, 0].mean(), latitude=arr[:, 1].mean(),
        zoom=8, pitch=0,
    )
    return pdk.Deck(
        layers=[layer], initial_view_state=view,
        map_style='mapbox://styles/mapbox/light-v11',
        tooltip={'text': '{nome}\n{detalhe}'},
    )


def mapa_completo(df_linear: pd.DataFrame, df_pontual: pd.DataFrame,
                   df_areas: pd.DataFrame) -> pdk.Deck:
    """Mapa com todas as camadas: redes + equipamentos + áreas."""
    layers = []
    todas_coords = []

    # Camada de redes
    if not df_linear.empty and '_coordenadas' in df_linear.columns:
        dados_redes = []
        for _, row in df_linear.iterrows():
            coords = row.get('_coordenadas', [])
            if len(coords) < 2:
                continue
            path = [[c[0], c[1]] for c in coords]
            dados_redes.append({
                'path': path,
                'color': _cor_tipo(row.get('tipo', '')),
                'nome': f"{row.get('subtipo', '')} — {row.get('nm_mun', '')}",
                'extensao': f"{row.get('extensao_calculada_m', 0):.0f}m",
            })
            todas_coords.extend(path)

        if dados_redes:
            layers.append(pdk.Layer(
                'PathLayer', data=dados_redes,
                get_path='path', get_color='color',
                width_min_pixels=2, width_max_pixels=4,
                pickable=True,
            ))

    # Camada de equipamentos
    if not df_pontual.empty:
        dados_equip = []
        for _, row in df_pontual.iterrows():
            lat = row.get('_centroide_lat', row.get('latitude'))
            lon = row.get('_centroide_lon', row.get('longitude'))
            if pd.isna(lat) or pd.isna(lon):
                continue
            pos = [float(lon), float(lat)]
            dados_equip.append({
                'position': pos,
                'color': _cor_subtipo_pontual(row.get('subtipo', '')),
                'nome': f"{row.get('subtipo', '')} — {row.get('nm_mun', '')}",
            })
            todas_coords.append(pos)

        if dados_equip:
            layers.append(pdk.Layer(
                'ScatterplotLayer', data=dados_equip,
                get_position='position', get_fill_color='color',
                get_radius=600, pickable=True,
            ))

    if not todas_coords:
        return None

    arr = np.array(todas_coords)
    view = pdk.ViewState(
        longitude=arr[:, 0].mean(), latitude=arr[:, 1].mean(),
        zoom=7, pitch=0,
    )
    return pdk.Deck(
        layers=layers, initial_view_state=view,
        map_style='mapbox://styles/mapbox/light-v11',
        tooltip={'text': '{nome}\n{extensao}'},
    )
