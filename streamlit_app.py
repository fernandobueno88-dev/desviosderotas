import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Biomata Analytics", layout="wide")

st.title("🚛 Biomata Analytics")
st.subheader("Módulo: KM Morto por Troca de Turno")

arquivo = st.file_uploader("📂 Envie o relatório de macros da Maxtrack", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)
    df.columns = df.columns.str.strip()

    st.success("Arquivo carregado com sucesso!")

    colunas = df.columns.tolist()

    st.sidebar.header("⚙️ Configuração das colunas")

    coluna_data = st.sidebar.selectbox("Coluna de Data", colunas, index=colunas.index("Data") if "Data" in colunas else 0)
    coluna_frota = st.sidebar.selectbox("Coluna de Frota", colunas, index=colunas.index("Frota") if "Frota" in colunas else 0)
    coluna_motorista = st.sidebar.selectbox("Coluna de Motorista", colunas, index=colunas.index("Nome do motorista") if "Nome do motorista" in colunas else 0)
    coluna_macro = st.sidebar.selectbox("Coluna de Macro", colunas, index=colunas.index("Tela") if "Tela" in colunas else 0)
    coluna_referencia = st.sidebar.selectbox("Coluna de Referência", colunas, index=colunas.index("Referência") if "Referência" in colunas else 0)
    coluna_local = st.sidebar.selectbox("Coluna de Local", colunas, index=colunas.index("Local") if "Local" in colunas else 0)
    coluna_km = st.sidebar.selectbox("Coluna de Odômetro / KM", colunas, index=colunas.index("Odômetro") if "Odômetro" in colunas else 0)
    coluna_latitude = st.sidebar.selectbox("Coluna de Latitude", colunas, index=colunas.index("Latitude") if "Latitude" in colunas else 0)
    coluna_longitude = st.sidebar.selectbox("Coluna de Longitude", colunas, index=colunas.index("Longitude") if "Longitude" in colunas else 0)

    df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=True)
    df[coluna_km] = pd.to_numeric(df[coluna_km], errors="coerce") / 1000
    df[coluna_latitude] = pd.to_numeric(df[coluna_latitude], errors="coerce")
    df[coluna_longitude] = pd.to_numeric(df[coluna_longitude], errors="coerce")

    df = df.dropna(subset=[coluna_data, coluna_km])

    df[coluna_macro] = df[coluna_macro].astype(str).str.upper().str.strip()
    df[coluna_referencia] = df[coluna_referencia].astype(str).str.upper().str.strip()
    df[coluna_local] = df[coluna_local].astype(str).str.upper().str.strip()

    st.sidebar.header("🔎 Filtros")

    data_min = df[coluna_data].min().date()
    data_max = df[coluna_data].max().date()

    periodo = st.sidebar.date_input(
        "Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )

    if len(periodo) == 2:
        inicio, fim = periodo
        df = df[
            (df[coluna_data].dt.date >= inicio) &
            (df[coluna_data].dt.date <= fim)
        ]

    frotas = sorted(df[coluna_frota].dropna().astype(str).unique())
    frota_selecionada = st.sidebar.multiselect("Frota", frotas)

    if frota_selecionada:
        df = df[df[coluna_frota].astype(str).isin(frota_selecionada)]

    df = df.sort_values([coluna_frota, coluna_data]).copy()

    df["KM anterior"] = df.groupby(coluna_frota)[coluna_km].shift(1)
    df["Referência anterior"] = df.groupby(coluna_frota)[coluna_referencia].shift(1)
    df["Macro anterior"] = df.groupby(coluna_frota)[coluna_macro].shift(1)
    df["Data anterior"] = df.groupby(coluna_frota)[coluna_data].shift(1)

    df["KM Rodado Evento"] = df[coluna_km] - df["KM anterior"]
    df.loc[df["KM Rodado Evento"] < 0, "KM Rodado Evento"] = 0
    df.loc[df["KM Rodado Evento"] > 300, "KM Rodado Evento"] = 0

    referencias_troca = (
        df[coluna_referencia].str.contains("TELÊMACO - MANDAÇAIA", na=False)
        | df[coluna_referencia].str.contains("TELEMACO - MANDACAIA", na=False)
        | df[coluna_referencia].str.contains("ROTA - TELEMACO/PUMA", na=False)
        | df[coluna_referencia].str.contains("RDV - CLIENTE", na=False)
    )

    macros_troca = df[coluna_macro].isin([
        "FIM DE JORNADA",
        "TROCA DE MOTORISTA"
    ])

    regra_troca = referencias_troca & macros_troca

    regra_garagem = df[coluna_referencia].str.contains("GARAGEM - BBM", na=False)

    regra_mecanica = (
        df[coluna_referencia].str.contains(
            "MECANICA|MECÂNICA|OFICINA|MANUTENCAO|MANUTENÇÃO|BORRACHARIA",
            na=False,
            regex=True
        )
        | df[coluna_local].str.contains(
            "MECANICA|MECÂNICA|OFICINA|MANUTENCAO|MANUTENÇÃO|BORRACHARIA",
            na=False,
            regex=True
        )
    )

    df["Tipo KM Morto"] = "Não conta"
    df.loc[regra_troca, "Tipo KM Morto"] = "Troca em ponto operacional"
    df.loc[regra_garagem, "Tipo KM Morto"] = "Retorno Garagem BBM"
    df.loc[regra_mecanica, "Tipo KM Morto"] = "Mecânica / Oficina"

    df_km = df[df["Tipo KM Morto"] != "Não conta"].copy()

    eventos_total = len(df_km)
    km_total = df_km["KM Rodado Evento"].sum()
    km_troca = df_km[df_km["Tipo KM Morto"] == "Troca em ponto operacional"]["KM Rodado Evento"].sum()
    km_garagem = df_km[df_km["Tipo KM Morto"] == "Retorno Garagem BBM"]["KM Rodado Evento"].sum()
    km_mecanica = df_km[df_km["Tipo KM Morto"] == "Mecânica / Oficina"]["KM Rodado Evento"].sum()

    st.divider()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("🚛 Eventos", f"{eventos_total}")
    col2.metric("🛣️ KM Total", f"{km_total:,.0f} km".replace(",", "."))
    col3.metric("🏁 KM Trocas", f"{km_troca:,.0f} km".replace(",", "."))
    col4.metric("🏢 KM Garagem", f"{km_garagem:,.0f} km".replace(",", "."))
    col5.metric("🔧 KM Mecânica", f"{km_mecanica:,.0f} km".replace(",", "."))

    st.divider()

    st.subheader("🚛 Ranking de prefixos que mais vêm na base")

    ranking_base = (
        df_km[df_km["Tipo KM Morto"] == "Retorno Garagem BBM"]
        .groupby(coluna_frota)
        .agg(
            Eventos=("Tipo KM Morto", "count"),
            KM_Total=("KM Rodado Evento", "sum")
        )
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_base, use_container_width=True)

    if not ranking_base.empty:
        fig_base = px.bar(
            ranking_base,
            x=coluna_frota,
            y="KM_Total",
            title="KM morto por retorno à Garagem BBM"
        )
        st.plotly_chart(fig_base, use_container_width=True)

    st.subheader("📊 Ranking geral por frota")

    ranking_frota = (
        df_km.groupby([coluna_frota, "Tipo KM Morto"])
        .agg(
            Eventos=("Tipo KM Morto", "count"),
            KM_Total=("KM Rodado Evento", "sum")
        )
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_frota, use_container_width=True)

    if not ranking_frota.empty:
        fig_frota = px.bar(
            ranking_frota,
            x=coluna_frota,
            y="KM_Total",
            color="Tipo KM Morto",
            title="KM morto por frota"
        )
        st.plotly_chart(fig_frota, use_container_width=True)

    st.subheader("🔧 Ranking da mecânica / oficina")

    ranking_mecanica = (
        df_km[df_km["Tipo KM Morto"] == "Mecânica / Oficina"]
        .groupby([coluna_frota, coluna_referencia])
        .agg(
            Eventos=("Tipo KM Morto", "count"),
            KM_Total=("KM Rodado Evento", "sum")
        )
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_mecanica, use_container_width=True)

    st.subheader("👤 Ranking por motorista")

    ranking_motorista = (
        df_km.groupby([coluna_motorista, "Tipo KM Morto"])
        .agg(
            Eventos=("Tipo KM Morto", "count"),
            KM_Total=("KM Rodado Evento", "sum")
        )
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_motorista, use_container_width=True)

    st.subheader("📍 Ranking por referência")

    ranking_ref = (
        df_km.groupby([coluna_referencia, "Tipo KM Morto"])
        .agg(
            Eventos=("Tipo KM Morto", "count"),
            KM_Total=("KM Rodado Evento", "sum")
        )
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_ref, use_container_width=True)

    st.subheader("🗺️ Mapa de calor separado por tipo")

    df_mapa = df_km.dropna(subset=[coluna_latitude, coluna_longitude]).copy()

    if not df_mapa.empty:
        fig_mapa = px.density_mapbox(
            df_mapa,
            lat=coluna_latitude,
            lon=coluna_longitude,
            z="KM Rodado Evento",
            radius=15,
            center={
                "lat": df_mapa[coluna_latitude].mean(),
                "lon": df_mapa[coluna_longitude].mean()
            },
            zoom=8,
            mapbox_style="open-street-map",
            facet_col="Tipo KM Morto",
            title="Mapa de calor por tipo de KM morto"
        )
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.warning("Não foi possível gerar o mapa. Verifique Latitude e Longitude.")

    st.subheader("📍 Mapa de pontos por categoria")

    if not df_mapa.empty:
        fig_pontos = px.scatter_mapbox(
            df_mapa,
            lat=coluna_latitude,
            lon=coluna_longitude,
            color="Tipo KM Morto",
            size="KM Rodado Evento",
            hover_name=coluna_frota,
            hover_data=[
                coluna_motorista,
                coluna_macro,
                coluna_referencia,
                coluna_local,
                "KM Rodado Evento"
            ],
            zoom=8,
            center={
                "lat": df_mapa[coluna_latitude].mean(),
                "lon": df_mapa[coluna_longitude].mean()
            },
            mapbox_style="open-street-map",
            title="Pontos classificados: Garagem, Troca e Mecânica"
        )
        st.plotly_chart(fig_pontos, use_container_width=True)

    st.subheader("📋 Eventos encontrados")

    colunas_mostrar = [
        coluna_data,
        coluna_frota,
        coluna_motorista,
        coluna_macro,
        coluna_referencia,
        coluna_local,
        coluna_km,
        "KM anterior",
        "KM Rodado Evento",
        "Tipo KM Morto",
        "Referência anterior",
        "Macro anterior",
        coluna_latitude,
        coluna_longitude
    ]

    st.dataframe(df_km[colunas_mostrar], use_container_width=True)

    arquivo_exportar = df_km.to_csv(index=False, sep=";").encode("utf-8-sig")

    st.download_button(
        label="⬇️ Baixar eventos em CSV",
        data=arquivo_exportar,
        file_name="eventos_km_morto.csv",
        mime="text/csv"
    )

else:
    st.info("Envie o relatório de macros para começar.")
