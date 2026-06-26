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

    st.success("Arquivo carregado com sucesso!")

    df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=True)
    df[coluna_km] = pd.to_numeric(df[coluna_km], errors="coerce") / 1000
    df[coluna_latitude] = pd.to_numeric(df[coluna_latitude], errors="coerce")
    df[coluna_longitude] = pd.to_numeric(df[coluna_longitude], errors="coerce")

    df = df.dropna(subset=[coluna_data, coluna_km])

    df[coluna_macro] = df[coluna_macro].astype(str).str.upper().str.strip()
    df[coluna_referencia] = df[coluna_referencia].astype(str).str.upper().str.strip()
    df[coluna_local] = df[coluna_local].astype(str).str.upper().str.strip()
    df[coluna_frota] = df[coluna_frota].astype(str).str.strip()

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

    frotas = sorted(df[coluna_frota].dropna().unique())
    frota_selecionada = st.sidebar.multiselect("Frota", frotas)

    if frota_selecionada:
        df = df[df[coluna_frota].isin(frota_selecionada)]

    df = df.sort_values([coluna_frota, coluna_data]).copy()

    macros_descarga = [
        "FIM DE VIAGEM",
        "DESCARGA",
        "FIM DE DESCARGA",
        "AGUARDANDO DESCARGA"
    ]

    macros_troca = [
        "FIM DE JORNADA",
        "TROCA DE MOTORISTA"
    ]

    referencias_troca = (
        "TELÊMACO - MANDAÇAIA|"
        "TELEMACO - MANDACAIA|"
        "ROTA - TELEMACO/PUMA|"
        "RDV - CLIENTE"
    )

    referencias_biomata = "GARAGEM - BBM"

    palavras_mecanica = (
        "MECANICA|MECÂNICA|OFICINA|MANUTENCAO|MANUTENÇÃO|BORRACHARIA|"
        "AUTO ELETRICA|AUTO ELÉTRICA|LOPES|LOBASCZ|MECANICO|MECÂNICO|"
        "MANUT|PNEU|PNEUS|LAVADOR|POSTO"
    )

    eventos = []

    for frota, grupo in df.groupby(coluna_frota):
        ultima_descarga = None

        for _, linha in grupo.iterrows():
            macro = linha[coluna_macro]
            referencia = linha[coluna_referencia]
            local = linha[coluna_local]

            if macro in macros_descarga:
                ultima_descarga = linha
                continue

            tipo = None

            if referencia.find("GARAGEM - BBM") >= 0:
                tipo = "Retorno Biomata"

            elif (
                pd.Series([referencia]).str.contains(referencias_troca, regex=True, na=False).iloc[0]
                and macro in macros_troca
            ):
                tipo = "Troca em ponto operacional"

            elif (
                pd.Series([referencia]).str.contains(palavras_mecanica, regex=True, na=False).iloc[0]
                or pd.Series([local]).str.contains(palavras_mecanica, regex=True, na=False).iloc[0]
            ):
                tipo = "Mecânica / Oficina"

            if tipo and ultima_descarga is not None:
                km_morto = linha[coluna_km] - ultima_descarga[coluna_km]

                if km_morto < 0 or km_morto > 300:
                    continue

                eventos.append({
                    "Data Descarga": ultima_descarga[coluna_data],
                    "Macro Descarga": ultima_descarga[coluna_macro],
                    "Referência Descarga": ultima_descarga[coluna_referencia],
                    "KM Descarga": ultima_descarga[coluna_km],

                    "Data Evento": linha[coluna_data],
                    "Frota": linha[coluna_frota],
                    "Motorista": linha[coluna_motorista],
                    "Macro Evento": linha[coluna_macro],
                    "Referência Evento": linha[coluna_referencia],
                    "Local Evento": linha[coluna_local],
                    "KM Evento": linha[coluna_km],
                    "KM Morto": km_morto,
                    "Tipo KM Morto": tipo,
                    "Latitude": linha[coluna_latitude],
                    "Longitude": linha[coluna_longitude],
                })

                ultima_descarga = None

    df_km = pd.DataFrame(eventos)

    if df_km.empty:
        st.warning("Nenhum evento de KM morto encontrado com as regras atuais.")
        st.stop()

    eventos_total = len(df_km)
    km_total = df_km["KM Morto"].sum()
    km_troca = df_km[df_km["Tipo KM Morto"] == "Troca em ponto operacional"]["KM Morto"].sum()
    km_biomata = df_km[df_km["Tipo KM Morto"] == "Retorno Biomata"]["KM Morto"].sum()
    km_mecanica = df_km[df_km["Tipo KM Morto"] == "Mecânica / Oficina"]["KM Morto"].sum()

    st.divider()

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("🚛 Eventos", f"{eventos_total}")
    col2.metric("🛣️ KM Total", f"{km_total:,.0f} km".replace(",", "."))
    col3.metric("🏁 KM Trocas", f"{km_troca:,.0f} km".replace(",", "."))
    col4.metric("🏢 KM Biomata", f"{km_biomata:,.0f} km".replace(",", "."))
    col5.metric("🔧 KM Mecânica", f"{km_mecanica:,.0f} km".replace(",", "."))

    st.divider()

    st.subheader("🚛 Ranking de prefixos que mais retornam para a Biomata")

    ranking_biomata = (
        df_km[df_km["Tipo KM Morto"] == "Retorno Biomata"]
        .groupby("Frota")
        .agg(Eventos=("Tipo KM Morto", "count"), KM_Total=("KM Morto", "sum"))
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_biomata, use_container_width=True)

    if not ranking_biomata.empty:
        fig_biomata = px.bar(
            ranking_biomata,
            x="Frota",
            y="KM_Total",
            title="KM morto por retorno à Biomata"
        )
        st.plotly_chart(fig_biomata, use_container_width=True)

    st.subheader("📊 Ranking geral por frota")

    ranking_frota = (
        df_km.groupby(["Frota", "Tipo KM Morto"])
        .agg(Eventos=("Tipo KM Morto", "count"), KM_Total=("KM Morto", "sum"))
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_frota, use_container_width=True)

    fig_frota = px.bar(
        ranking_frota,
        x="Frota",
        y="KM_Total",
        color="Tipo KM Morto",
        title="KM morto por frota"
    )
    st.plotly_chart(fig_frota, use_container_width=True)

    st.subheader("👤 Ranking por motorista")

    ranking_motorista = (
        df_km.groupby(["Motorista", "Tipo KM Morto"])
        .agg(Eventos=("Tipo KM Morto", "count"), KM_Total=("KM Morto", "sum"))
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_motorista, use_container_width=True)

    st.subheader("📍 Ranking por referência")

    ranking_ref = (
        df_km.groupby(["Referência Evento", "Tipo KM Morto"])
        .agg(Eventos=("Tipo KM Morto", "count"), KM_Total=("KM Morto", "sum"))
        .reset_index()
        .sort_values("KM_Total", ascending=False)
    )

    st.dataframe(ranking_ref, use_container_width=True)

    st.subheader("🗺️ Mapa de calor geral")

    df_mapa = df_km.dropna(subset=["Latitude", "Longitude"]).copy()
    df_mapa = df_mapa[df_mapa["KM Morto"] > 0]

    if not df_mapa.empty:
        fig_mapa = px.density_mapbox(
            df_mapa,
            lat="Latitude",
            lon="Longitude",
            z="KM Morto",
            radius=18,
            center={
                "lat": df_mapa["Latitude"].mean(),
                "lon": df_mapa["Longitude"].mean()
            },
            zoom=8,
            mapbox_style="open-street-map",
            title="Mapa de calor por KM morto"
        )
        st.plotly_chart(fig_mapa, use_container_width=True)

    st.subheader("📍 Mapa de pontos por categoria")

    df_pontos = df_mapa.copy()
    df_pontos["Tamanho Ponto"] = df_pontos["KM Morto"].clip(lower=1, upper=80)

    if not df_pontos.empty:
        fig_pontos = px.scatter_mapbox(
            df_pontos,
            lat="Latitude",
            lon="Longitude",
            color="Tipo KM Morto",
            size="Tamanho Ponto",
            hover_name="Frota",
            hover_data=[
                "Motorista",
                "Macro Descarga",
                "Referência Descarga",
                "Macro Evento",
                "Referência Evento",
                "Local Evento",
                "KM Morto"
            ],
            zoom=8,
            center={
                "lat": df_pontos["Latitude"].mean(),
                "lon": df_pontos["Longitude"].mean()
            },
            mapbox_style="open-street-map",
            title="Pontos classificados: Biomata, Troca e Mecânica"
        )
        st.plotly_chart(fig_pontos, use_container_width=True)

    st.subheader("📋 Eventos encontrados")

    st.dataframe(df_km, use_container_width=True)

    arquivo_exportar = df_km.to_csv(index=False, sep=";").encode("utf-8-sig")

    st.download_button(
        label="⬇️ Baixar eventos em CSV",
        data=arquivo_exportar,
        file_name="eventos_km_morto.csv",
        mime="text/csv"
    )

else:
    st.info("Envie o relatório de macros para começar.")
