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

    st.sidebar.header("⚙️ Configuração das colunas")

    colunas = df.columns.tolist()

    coluna_data = st.sidebar.selectbox("Coluna de Data", colunas)
    coluna_frota = st.sidebar.selectbox("Coluna de Frota", colunas)
    coluna_motorista = st.sidebar.selectbox("Coluna de Motorista", colunas)
    coluna_macro = st.sidebar.selectbox("Coluna de Macro", colunas)
    coluna_referencia = st.sidebar.selectbox("Coluna de Referência", colunas)
    coluna_km = st.sidebar.selectbox("Coluna de Hodômetro / KM", colunas)

    df[coluna_macro] = df[coluna_macro].astype(str).str.upper().str.strip()
    df[coluna_referencia] = df[coluna_referencia].astype(str).str.upper().str.strip()

    regra_mandacaia = (
        df[coluna_referencia].str.contains("TELÊMACO - MANDAÇAIA", na=False)
        & df[coluna_macro].isin(["FIM DE JORNADA", "TROCA DE MOTORISTA"])
    )

    regra_garagem = (
        df[coluna_referencia].str.contains("GARAGEM - BBM", na=False)
    )

    df["Tipo KM Morto"] = "Não conta"
    df.loc[regra_mandacaia, "Tipo KM Morto"] = "Troca em Mandaçaia"
    df.loc[regra_garagem, "Tipo KM Morto"] = "Retorno Garagem BBM"

    df_km = df[df["Tipo KM Morto"] != "Não conta"].copy()

    df_km[coluna_km] = pd.to_numeric(df_km[coluna_km], errors="coerce")

    st.divider()

    col1, col2, col3 = st.columns(3)

    col1.metric("🚛 Eventos KM Morto", len(df_km))
    col2.metric("🏁 Troca Mandaçaia", len(df_km[df_km["Tipo KM Morto"] == "Troca em Mandaçaia"]))
    col3.metric("🏢 Garagem BBM", len(df_km[df_km["Tipo KM Morto"] == "Retorno Garagem BBM"]))

    st.divider()

    st.subheader("📊 Ranking por Frota")

    ranking_frota = (
        df_km.groupby([coluna_frota, "Tipo KM Morto"])
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    st.dataframe(ranking_frota, use_container_width=True)

    if not ranking_frota.empty:
        grafico_frota = px.bar(
            ranking_frota,
            x=coluna_frota,
            y="Quantidade",
            color="Tipo KM Morto",
            title="Eventos de KM Morto por Frota"
        )
        st.plotly_chart(grafico_frota, use_container_width=True)

    st.subheader("👤 Ranking por Motorista")

    ranking_motorista = (
        df_km.groupby([coluna_motorista, "Tipo KM Morto"])
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    st.dataframe(ranking_motorista, use_container_width=True)

    st.subheader("📍 Ranking por Referência")

    ranking_ref = (
        df_km.groupby([coluna_referencia, "Tipo KM Morto"])
        .size()
        .reset_index(name="Quantidade")
        .sort_values("Quantidade", ascending=False)
    )

    st.dataframe(ranking_ref, use_container_width=True)

    st.subheader("📋 Eventos encontrados")

    st.dataframe(df_km, use_container_width=True)

    arquivo_exportar = df_km.to_csv(index=False, sep=";").encode("utf-8")

    st.download_button(
        label="⬇️ Baixar eventos em CSV",
        data=arquivo_exportar,
        file_name="eventos_km_morto.csv",
        mime="text/csv"
    )

else:
    st.info("Envie o relatório de macros para começar.")
