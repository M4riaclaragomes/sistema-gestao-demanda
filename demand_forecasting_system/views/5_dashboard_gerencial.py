import streamlit as st
import pandas as pd
import plotly.express as px
import os
import sys

def render():
    st.title("📊 Módulo 5: Dashboard Gerencial")
    st.markdown("Visão executiva do desempenho do portfólio de produtos.")

    if 'df_dados' not in st.session_state or st.session_state['df_dados'] is None:
        st.warning("⚠️ Nenhuma base de dados tratada encontrada. Por favor, volte ao Módulo 1 e carregue os dados.")
        return

    df = st.session_state['df_dados']
    df.columns = [c.lower() for c in df.columns]
    
    # 1. CÁLCULO DE KPIs
    total_vendas = df['quantidade_vendida'].sum()
    num_skus = df['sku'].nunique()
    media_diaria = df['quantidade_vendida'].mean()
    top_sku = df.groupby('sku')['quantidade_vendida'].sum().idxmax()
    
    # 2. RENDERIZAÇÃO DOS CARTÕES (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Volume Total Vendido", f"{total_vendas:,.0f}".replace(",", "."))
    with col2:
        st.metric("Total de Produtos (SKUs)", num_skus)
    with col3:
        st.metric("Média de Vendas (Diária)", f"{media_diaria:,.1f}".replace(",", "."))
    with col4:
        st.metric("Produto Campeão", top_sku)
        
    st.markdown("---")
    
    # 3. GRÁFICOS DE DISTRIBUIÇÃO
    col_chart1, col_chart2 = st.columns(2)
    
    df_prod = df.groupby('sku')['quantidade_vendida'].sum().reset_index()
    df_prod = df_prod.sort_values(by='quantidade_vendida', ascending=False)
    
    with col_chart1:
        st.subheader("Vendas Totais por Produto")
        fig_bar = px.bar(
            df_prod, 
            x='sku', 
            y='quantidade_vendida', 
            color='sku',
            text_auto='.2s'
        )
        fig_bar.update_layout(showlegend=False, xaxis_title="", yaxis_title="Quantidade")
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_chart2:
        st.subheader("Participação no Portfólio (Market Share)")
        fig_pie = px.pie(
            df_prod, 
            names='sku', 
            values='quantidade_vendida', 
            hole=0.4
        )
        st.plotly_chart(fig_pie, use_container_width=True)
        
    st.markdown("---")
    
    # 4. GRÁFICO TEMPORAL DE EVOLUÇÃO
    st.subheader("📈 Evolução Temporal de Vendas (Agrupamento Mensal)")
    
    # Garantir que a coluna de data é do tipo datetime
    df['data'] = pd.to_datetime(df['data'])
    
    # Agrupar por mês e ano para o gráfico não ficar com demasiadas linhas cruzadas
    df['mes_ano'] = df['data'].dt.to_period('M').dt.to_timestamp()
    df_tempo = df.groupby(['mes_ano', 'sku'])['quantidade_vendida'].sum().reset_index()
    
    fig_line = px.line(
        df_tempo, 
        x='mes_ano', 
        y='quantidade_vendida', 
        color='sku', 
        markers=True
    )
    fig_line.update_layout(
        hovermode="x unified",
        xaxis_title="Período",
        yaxis_title="Volume Mensal Vendido",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig_line, use_container_width=True)
