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
    coluna_km = st.sidebar.selectbox("Coluna de Hodômetro / KM", colunas, index=colunas.index("Hodômetro") if "Hodômetro" in colunas else 0)

    df[coluna_data] = pd.to_datetime(df[coluna_data], errors="coerce", dayfirst=True)
    df[coluna_km] = pd.to_numeric(df[coluna_km], errors="coerce")

    df = df.dropna(subset=[coluna_data, coluna_km])

    df[coluna_macro] = df[coluna_macro].astype(str).str.upper().str.strip()
    df[coluna_referencia] = df[coluna_referencia].astype(str).str.upper().str.strip()

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

    # Ordenar para calcular km entre eventos
    df = df.sort_values([coluna_frota, coluna_data]).copy()

    df["KM anterior"] = df.groupby(coluna_frota)[coluna_km].shift(1)
    df["Referência anterior"] = df.groupby(coluna_frota)[coluna_referencia].shift(1)
    df["Macro anterior"] = df.groupby(coluna_frota)[coluna_macro].shift(1)
    df["Data anterior"] = df.groupby(coluna_frota)[coluna_data].shift(1)

    df["KM Rodado Evento"] = df[coluna_km] - df["KM anterior"]

    df.loc[df["KM Rodado Evento"] < 0, "KM Rodado Evento"] = 0
    df.loc[df["KM Rodado Evento"] > 300, "KM Rodado Evento"] = 0

    regra_mandacaia = (
        df[coluna_referencia].str.contains("TELÊMACO - MANDAÇAIA", na=False)
        & df[coluna_macro].isin(["FIM DE JORNADA", "TROCA DE MOTORISTA"])
    )

    regra_garagem = df[coluna_referencia].str.contains("GARAGEM - BBM", na=False)

    df["Tipo KM Morto"] = "Não conta"
    df.loc[regra_mandacaia, "Tipo KM Morto"] = "Troca em Mandaçaia"
    df.loc[regra_garagem, "Tipo KM Morto"] = "Retorno Garagem BBM"

    df_km = df[df["Tipo KM Morto"] != "Não conta"].copy()

    eventos_total = len(df_km)
    km_total = df_km["KM Rodado Evento"].sum()
    km_mandacaia = df_km[df_km["Tipo KM Morto"] == "Troca em Mandaçaia"]["KM Rodado Evento"].sum()
    km_garagem = df_km[df_km["Tipo KM Morto"] == "Retorno Garagem BBM"]["KM Rodado Evento"].sum()

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("🚛 Eventos KM Morto", f"{eventos_total}")
    col2.metric("🛣️ KM Morto Total", f"{km_total:,.0f} km".replace(",", "."))
    col3.metric("🏁 KM Mandaçaia", f"{km_mandacaia:,.0f} km".replace(",", "."))
    col4.metric("🏢 KM Garagem BBM", f"{km_garagem:,.0f} km".replace(",", "."))

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

    st.subheader("📋 Eventos encontrados")

    colunas_mostrar = [
        coluna_data,
        coluna_frota,
        coluna_motorista,
        coluna_macro,
        coluna_referencia,
        coluna_km,
        "KM anterior",
        "KM Rodado Evento",
        "Tipo KM Morto",
        "Referência anterior",
        "Macro anterior"
    ]

    st.dataframe(df_km[colunas_mostrar], use_container_width=True)

else:
    st.info("Envie o relatório de macros para começar.")
