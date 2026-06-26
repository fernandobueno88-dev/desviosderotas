import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="KM Morto Biomata", layout="wide")

st.title("🚛 Painel de KM Morto - Biomata")

arquivo = st.file_uploader("Envie o relatório de macros da Maxtrack", type=["xlsx"])

if arquivo:
    df = pd.read_excel(arquivo)

    st.subheader("Prévia do relatório")
    st.dataframe(df.head())

    st.subheader("Colunas encontradas")
    st.write(df.columns.tolist())

else:
    st.info("Envie o relatório de macros para começar.")
