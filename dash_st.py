import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import calendar

# Configuração da página
st.set_page_config(
    page_title="Açaí Fitness Analytics",
    page_icon="🍇",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Aplicar tema e estilo personalizado
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .st-emotion-cache-1v0mbdj.e115fcil1 {
        width: 100%;
        padding: 2rem 1rem;
        border-radius: 0.75rem;
        background-color: black;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        margin-bottom: 1.5rem;
    }
    .st-emotion-cache-1wbqh2d.e1nzilvr5 {
        font-size: 1.25rem;
        font-weight: 700;
        color: #5a5c69;
    }
    .metric-card {
        background-color: black;
        border-radius: 0.5rem;
        padding: 1.5rem;
        box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);
        transition: transform 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-0.25rem);
    }
    div[data-testid="stSidebarNav"] {
        background-color: #4e73df;
        padding-top: 2rem;
    }
    div[data-testid="stSidebarNav"] > ul {
        padding-top: 1rem;
    }
    div[data-testid="stSidebarNav"] span {
        color: black;
    }
    .st-emotion-cache-16txtl3.ezrtsby2 {
        padding-top: 2rem;
    }
    .sidebar-title {
        color: black;
        font-size: 1.2rem;
        font-weight: 800;
        padding: 0 1rem 1rem 1rem;
        margin: 0;
        text-align: center;
    }
    hr {
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Logo e título no sidebar
with st.sidebar:
    st.markdown('<p class="sidebar-title">🍇 AÇAÍ FITNESS</p>', unsafe_allow_html=True)
    st.markdown('<hr>', unsafe_allow_html=True)

# Carregar os dados
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("vendas_acai_5_anos_completo.csv", on_bad_lines='skip', sep=",")
        
        # Renomear colunas
        df.columns = [
            "Data", "Produto", "Categoria", "Localizacao", "Canal", "Qtd_Vendida",
            "Preco_Unitario", "Valor_Total", "Custo_Materiais", "Custo_Entrega",
            "Receita_Liquida", "Receita_Loja", "Desconto_Cliente", "Taxa_Plataforma",
            "Lucro_Liquido", "Funcionarios", "Comissao_Func", "Tempo_Preparo",
            "Distancia_Entrega", "Clientes_Unicos", "Pessoas_Atendidas",
            "Tempo_Entrega", "Valor_Ticket_Medio", "Cliente_Novo", "Capacidade_Max",
            "Promocao", "Desconto_Promocao", "Qtde_Desconto"
        ]
        
        # Garantir que as colunas monetárias sejam corretamente convertidas
        money_cols = ["Preco_Unitario", "Valor_Total", "Custo_Materiais", "Custo_Entrega",
                    "Receita_Liquida", "Receita_Loja", "Desconto_Cliente", "Taxa_Plataforma",
                    "Lucro_Liquido", "Comissao_Func", "Valor_Ticket_Medio", "Desconto_Promocao"]
        
        for col in money_cols:
            # Primeiro converter para string e substituir vírgulas por pontos
            df[col] = df[col].astype(str).str.replace(",", ".")
            # Substituir valores 'True' ou 'False' por '0' antes de converter para float
            df[col] = df[col].replace({'True': '0', 'False': '0'})
            # Agora converter para float
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(float)
        
        # Converter colunas booleanas corretamente
        bool_cols = ["Cliente_Novo", "Promocao"]
        for col in bool_cols:
            df[col] = df[col].astype(str).str.strip().str.lower() == 'true'
        
        # Converter outras colunas numéricas diretamente
        int_cols = ["Qtd_Vendida", "Clientes_Unicos", "Pessoas_Atendidas",
                    "Funcionarios", "Capacidade_Max", "Qtde_Desconto", 
                    "Tempo_Preparo", "Tempo_Entrega", "Distancia_Entrega"]
        
        for col in int_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        
        # Converter data
        df["Data"] = pd.to_datetime(df["Data"])
        
        # Criar colunas adicionais para análise
        df['Ano'] = df['Data'].dt.year
        df['Mes'] = df['Data'].dt.month
        df['Mes_Nome'] = df['Data'].dt.month_name()
        df['Dia_Semana'] = df['Data'].dt.day_name()
        df['Semana'] = df['Data'].dt.isocalendar().week
        df['Dia'] = df['Data'].dt.day
        
        # Calcular métricas adicionais
        df['Rentabilidade'] = (df['Lucro_Liquido'] / df['Valor_Total']) * 100
        df['Taxa_Retorno'] = df['Cliente_Novo'].apply(lambda x: 0 if x else 1)
        
        # Calcular eficiência operacional (Valor produzido por minuto de preparo)
        df['Eficiencia_Operacional'] = df['Valor_Total'] / df['Tempo_Preparo'].replace(0, 1)
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.error("Não foi possível carregar os dados. Verifique o arquivo CSV.")
else:
    # Filtros laterais
    st.sidebar.header("Filtros")
    
    # Filtro de período
    period_options = ["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Último ano", "Tudo"]
    selected_period = st.sidebar.selectbox("Período", period_options, index=2)
    
    # Calcular datas com base no período selecionado
    today = df["Data"].max()
    
    if selected_period == "Últimos 7 dias":
        start_date = today - timedelta(days=7)
    elif selected_period == "Últimos 30 dias":
        start_date = today - timedelta(days=30)
    elif selected_period == "Últimos 90 dias":
        start_date = today - timedelta(days=90)
    elif selected_period == "Último ano":
        start_date = today - timedelta(days=365)
    else:
        start_date = df["Data"].min()
    
    # Opção para filtrar data personalizada
    custom_date = st.sidebar.checkbox("Data personalizada")
    
    if custom_date:
        start_date = st.sidebar.date_input("Data inicial", value=start_date)
        end_date = st.sidebar.date_input("Data final", value=today)
    else:
        end_date = today
    
    # Outros filtros
    produtos = st.sidebar.multiselect("Produtos", options=sorted(df["Produto"].unique()), default=sorted(df["Produto"].unique()))
    categorias = st.sidebar.multiselect("Categorias", options=sorted(df["Categoria"].unique()), default=sorted(df["Categoria"].unique()))
    lojas = st.sidebar.multiselect("Lojas", options=sorted(df["Localizacao"].unique()), default=sorted(df["Localizacao"].unique()))
    canais = st.sidebar.multiselect("Canais de Venda", options=sorted(df["Canal"].unique()), default=sorted(df["Canal"].unique()))
    
    # Aplicar filtros
    filtered_df = df[
        (df["Data"] >= pd.to_datetime(start_date)) & 
        (df["Data"] <= pd.to_datetime(end_date)) & 
        (df["Produto"].isin(produtos)) & 
        (df["Categoria"].isin(categorias)) & 
        (df["Localizacao"].isin(lojas)) &
        (df["Canal"].isin(canais))
    ]
    
    # Título principal do dashboard
    st.title("Dashboard Açaí Fitness - Análise de Vendas")
    
    # Mostrar o período selecionado
    st.markdown(f"**Período analisado:** {start_date.strftime('%d/%m/%Y')} até {end_date.strftime('%d/%m/%Y')}")
    
    # KPIs principais na parte superior
    col1, col2, col3, col4 = st.columns(4)
    
    # KPI 1: Total de Vendas
    total_vendas = filtered_df["Valor_Total"].sum()
    
    # Comparação com período anterior de mesmo tamanho
    days_diff = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days
    previous_start = pd.to_datetime(start_date) - timedelta(days=days_diff)
    previous_end = pd.to_datetime(start_date) - timedelta(days=1)
    
    previous_df = df[
        (df["Data"] >= previous_start) & 
        (df["Data"] <= previous_end) & 
        (df["Produto"].isin(produtos)) & 
        (df["Categoria"].isin(categorias)) & 
        (df["Localizacao"].isin(lojas)) &
        (df["Canal"].isin(canais))
    ]
    
    previous_vendas = previous_df["Valor_Total"].sum() if not previous_df.empty else 0
    
    vendas_diff = ((total_vendas - previous_vendas) / previous_vendas * 100) if previous_vendas > 0 else 0
    vendas_diff_icon = "📈" if vendas_diff >= 0 else "📉"
    
    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3 style="color: #4e73df; margin-bottom: 0.5rem; font-size: 1rem;">Total de Vendas</h3>
                <p style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">R$ {total_vendas:,.2f}</p>
                <p style="color: {'green' if vendas_diff >= 0 else 'red'}; font-size: 0.875rem;">
                    {vendas_diff_icon} {abs(vendas_diff):.1f}% em relação ao período anterior
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # KPI 2: Lucro Líquido
    total_lucro = filtered_df["Lucro_Liquido"].sum()
    previous_lucro = previous_df["Lucro_Liquido"].sum() if not previous_df.empty else 0
    
    lucro_diff = ((total_lucro - previous_lucro) / previous_lucro * 100) if previous_lucro > 0 else 0
    lucro_diff_icon = "📈" if lucro_diff >= 0 else "📉"
    
    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3 style="color: #1cc88a; margin-bottom: 0.5rem; font-size: 1rem;">Lucro Líquido</h3>
                <p style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">R$ {total_lucro:,.2f}</p>
                <p style="color: {'green' if lucro_diff >= 0 else 'red'}; font-size: 0.875rem;">
                    {lucro_diff_icon} {abs(lucro_diff):.1f}% em relação ao período anterior
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # KPI 3: Ticket Médio
    ticket_medio = filtered_df["Valor_Total"].sum() / filtered_df["Clientes_Unicos"].sum() if filtered_df["Clientes_Unicos"].sum() > 0 else 0
    previous_ticket = previous_df["Valor_Total"].sum() / previous_df["Clientes_Unicos"].sum() if not previous_df.empty and previous_df["Clientes_Unicos"].sum() > 0 else 0
    
    ticket_diff = ((ticket_medio - previous_ticket) / previous_ticket * 100) if previous_ticket > 0 else 0
    ticket_diff_icon = "📈" if ticket_diff >= 0 else "📉"
    
    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3 style="color: #36b9cc; margin-bottom: 0.5rem; font-size: 1rem;">Ticket Médio</h3>
                <p style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">R$ {ticket_medio:,.2f}</p>
                <p style="color: {'green' if ticket_diff >= 0 else 'red'}; font-size: 0.875rem;">
                    {ticket_diff_icon} {abs(ticket_diff):.1f}% em relação ao período anterior
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # KPI 4: Novos Clientes
    novos_clientes = filtered_df[filtered_df["Cliente_Novo"] == True]["Clientes_Unicos"].sum()
    previous_novos = previous_df[previous_df["Cliente_Novo"] == True]["Clientes_Unicos"].sum() if not previous_df.empty else 0
    
    novos_diff = ((novos_clientes - previous_novos) / previous_novos * 100) if previous_novos > 0 else 0
    novos_diff_icon = "📈" if novos_diff >= 0 else "📉"
    
    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <h3 style="color: #f6c23e; margin-bottom: 0.5rem; font-size: 1rem;">Novos Clientes</h3>
                <p style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.25rem;">{novos_clientes:,}</p>
                <p style="color: {'green' if novos_diff >= 0 else 'red'}; font-size: 0.875rem;">
                    {novos_diff_icon} {abs(novos_diff):.1f}% em relação ao período anterior
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Gráficos na primeira linha
    st.markdown("## 📈 Tendências de Vendas")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        # Agrupar por data para tendência diária
        daily_sales = filtered_df.groupby("Data").agg({
            "Valor_Total": "sum",
            "Lucro_Liquido": "sum"
        }).reset_index()
        
        # Criar gráfico de linha com Plotly
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=daily_sales["Data"], 
            y=daily_sales["Valor_Total"],
            mode="lines",
            name="Vendas",
            line=dict(color="#4e73df", width=3),
            hovertemplate="Data: %{x}<br>Vendas: R$ %{y:,.2f}<extra></extra>"
        ))
        
        fig.add_trace(go.Scatter(
            x=daily_sales["Data"], 
            y=daily_sales["Lucro_Liquido"],
            mode="lines",
            name="Lucro",
            line=dict(color="#1cc88a", width=3),
            hovertemplate="Data: %{x}<br>Lucro: R$ %{y:,.2f}<extra></extra>"
        ))
        
        fig.update_layout(
            # title="Vendas e Lucro Diário",
            # titlefont=dict(size=16),
            title=dict(
                text="Vendas e Lucro Diário",
                font=dict(size=16)
            ),
                    xaxis_title="Data",
            yaxis_title="Valor (R$)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            hovermode="x unified"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with chart_col2:
        # Análise por dia da semana
        weekday_analysis = filtered_df.groupby("Dia_Semana").agg({
            "Valor_Total": "sum",
            "Qtd_Vendida": "sum"
        }).reset_index()
        
        # Ordenar dias da semana corretamente
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_ptbr = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        dias_map = dict(zip(dias_ordem, dias_ptbr))
        
        weekday_analysis['Dia_Semana_PT'] = weekday_analysis['Dia_Semana'].map(dias_map)
        weekday_analysis = weekday_analysis.sort_values(by='Dia_Semana', key=lambda x: pd.Categorical(x, categories=dias_ordem, ordered=True))
        
        # Criar gráfico de barras
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=weekday_analysis["Dia_Semana_PT"],
            y=weekday_analysis["Valor_Total"],
            name="Vendas",
            marker_color="#4e73df",
            hovertemplate="Dia: %{x}<br>Vendas: R$ %{y:,.2f}<extra></extra>"
        ))
        
        fig.add_trace(go.Scatter(
            x=weekday_analysis["Dia_Semana_PT"],
            y=weekday_analysis["Qtd_Vendida"],
            name="Quantidade",
            mode="lines+markers",
            marker=dict(color="#f6c23e", size=10),
            line=dict(color="#f6c23e", width=3),
            yaxis="y2",
            hovertemplate="Dia: %{x}<br>Qtd: %{y:,.0f}<extra></extra>"
        ))
        
        fig.update_layout(
            title="Desempenho por Dia da Semana",
            #titlefont=dict(size=16),
            title_font=dict(size=16),  # Note o underscore entre title e font
            xaxis_title="Dia da Semana",
            yaxis=dict(
                title="Vendas (R$)",
                title_font=dict(color="#4e73df"),
                tickfont=dict(color="#4e73df")
            ),
            yaxis2=dict(
                title="Quantidade Vendida",
                title_font=dict(color="#f6c23e"),
                tickfont=dict(color="#f6c23e"),
                anchor="x",
                overlaying="y",
                side="right"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Segunda linha de gráficos
    st.markdown("## 🔍 Análise de Produtos e Canais")
    chart2_col1, chart2_col2 = st.columns(2)
    
    with chart2_col1:
        # Top produtos mais vendidos
        product_analysis = filtered_df.groupby(["Produto", "Categoria"]).agg({
            "Valor_Total": "sum",
            "Qtd_Vendida": "sum",
            "Lucro_Liquido": "sum"
        }).reset_index()
        
        product_analysis["Margem"] = (product_analysis["Lucro_Liquido"] / product_analysis["Valor_Total"]) * 100
        product_analysis = product_analysis.sort_values("Valor_Total", ascending=False).head(10)
        
        # Criar gráfico de barras com cores por categoria
        fig = px.bar(
            product_analysis,
            x="Produto",
            y="Valor_Total",
            color="Categoria",
            text=product_analysis["Valor_Total"].apply(lambda x: f"R$ {x:,.0f}"),
            hover_data=["Qtd_Vendida", "Margem"],
            color_discrete_sequence=px.colors.qualitative.Pastel,
            labels={"Valor_Total": "Total de Vendas (R$)", "Produto": "", "Margem": "Margem de Lucro (%)"}
        )
        
        fig.update_layout(
            title="Top 10 Produtos por Vendas",
            #titlefont=dict(size=16),
            title_font=dict(size=16),  # Note o underscore entre title e font
            showlegend=True,
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(tickangle=45)
        )
        
        fig.update_traces(textposition="outside")
        
        st.plotly_chart(fig, use_container_width=True)
    
    with chart2_col2:
        # Análise por canal de vendas
        canal_analysis = filtered_df.groupby("Canal").agg({
            "Valor_Total": "sum",
            "Clientes_Unicos": "sum",
            "Lucro_Liquido": "sum"
        }).reset_index()
        
        canal_analysis["Margem"] = (canal_analysis["Lucro_Liquido"] / canal_analysis["Valor_Total"]) * 100
        canal_analysis["Ticket_Medio"] = canal_analysis["Valor_Total"] / canal_analysis["Clientes_Unicos"]
        canal_analysis = canal_analysis.sort_values("Valor_Total", ascending=False)
        
        # Criar gráfico de pizza
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            subplot_titles=("Distribuição de Vendas por Canal", "Ticket Médio por Canal")
        )
        
        # Gráfico de pizza
        fig.add_trace(
            go.Pie(
                labels=canal_analysis["Canal"],
                values=canal_analysis["Valor_Total"],
                hole=0.4,
                textinfo="percent+label",
                marker=dict(colors=px.colors.qualitative.Set2),
                textposition="inside",
                hovertemplate="Canal: %{label}<br>Vendas: R$ %{value:,.2f}<br>Porcentagem: %{percent}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Gráfico de barras para ticket médio
        fig.add_trace(
            go.Bar(
                x=canal_analysis["Canal"],
                y=canal_analysis["Ticket_Medio"],
                text=canal_analysis["Ticket_Medio"].apply(lambda x: f"R$ {x:,.2f}"),
                textposition="auto",
                marker_color=px.colors.qualitative.Set2,
                hovertemplate="Canal: %{x}<br>Ticket Médio: R$ %{y:,.2f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title="Análise por Canal de Vendas",
            #titlefont=dict(size=16),
            title_font=dict(size=16),  # Note o underscore entre title e font
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Terceira linha de insights
    st.markdown("## 💡 Insights e Recomendações")
    insight_cols = st.columns(3)
    
    with insight_cols[0]:
        # Eficiência operacional
        st.markdown("### Eficiência Operacional")
        
        # Calcular eficiência por loja
        loja_eficiencia = filtered_df.groupby("Localizacao").agg({
            "Tempo_Preparo": "mean",
            "Lucro_Liquido": "sum",
            "Valor_Total": "sum",
            "Eficiencia_Operacional": "mean"
        }).reset_index()
        
        loja_eficiencia["Margem"] = (loja_eficiencia["Lucro_Liquido"] / loja_eficiencia["Valor_Total"]) * 100
        loja_eficiencia = loja_eficiencia.sort_values("Eficiencia_Operacional", ascending=False)
        
        # Criar gráfico de radar
        categories = loja_eficiencia["Localizacao"].tolist()
        
        # Normalizar dados para o gráfico de radar
        eficiencia_norm = (loja_eficiencia["Eficiencia_Operacional"] / loja_eficiencia["Eficiencia_Operacional"].max()) * 100
        tempo_norm = (1 - (loja_eficiencia["Tempo_Preparo"] / loja_eficiencia["Tempo_Preparo"].max())) * 100
        margem_norm = (loja_eficiencia["Margem"] / loja_eficiencia["Margem"].max()) * 100
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=eficiencia_norm,
            theta=categories,
            fill='toself',
            name='Eficiência',
            line=dict(color="#4e73df")
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=tempo_norm,
            theta=categories,
            fill='toself',
            name='Rapidez',
            line=dict(color="#1cc88a")
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=margem_norm,
            theta=categories,
            fill='toself',
            name='Margem',
            line=dict(color="#f6c23e")
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            template="plotly_white",
            margin=dict(l=20, r=20, t=20, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendação operacional
        mais_eficiente = loja_eficiencia.iloc[0]["Localizacao"]
        menos_eficiente = loja_eficiencia.iloc[-1]["Localizacao"]
        
        st.info(f"💡 **Dica Operacional:** A loja {mais_eficiente} demonstra a maior eficiência operacional. Considere analisar seus processos e implementar as melhores práticas na loja {menos_eficiente} para melhorar o desempenho.")
    
    with insight_cols[1]:
        # Análise de sazonalidade
        st.markdown("### Padrões de Sazonalidade")
        
        # Análise mensal se tiver pelo menos 60 dias de dados
        if (filtered_df["Data"].max() - filtered_df["Data"].min()).days >= 60:
            monthly_data = filtered_df.groupby(["Ano", "Mes"]).agg({
                "Valor_Total": "sum",
                "Qtd_Vendida": "sum"
            }).reset_index()
            
            # Criar nomes de meses para a exibição
            months = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 
                    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
            
            monthly_data["Mes_Nome"] = monthly_data["Mes"].map(months)
            monthly_data["Periodo"] = monthly_data["Ano"].astype(str) + "-" + monthly_data["Mes_Nome"]
            
            # Criar gráfico de linha
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=monthly_data["Periodo"],
                y=monthly_data["Valor_Total"],
                mode="lines+markers",
                name="Vendas",
                line=dict(color="#4e73df", width=3),
                marker=dict(size=8),
                hovertemplate="Período: %{x}<br>Vendas: R$ %{y:,.2f}<extra></extra>"
            ))
            
            # Adicionar linha de tendência
            z = np.polyfit(np.arange(len(monthly_data)), monthly_data["Valor_Total"], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=monthly_data["Periodo"],
                y=p(np.arange(len(monthly_data))),
                mode="lines",
                name="Tendência",
                line=dict(color="red", width=2, dash="dash"),
                hovertemplate="Período: %{x}<br>Tendência: R$ %{y:,.2f}<extra></extra>"
            ))
            
            fig.update_layout(
                title="Tendência Mensal de Vendas",
                #titlefont=dict(size=16),
                title_font=dict(size=16),  # Note o underscore entre title e font
                xaxis_title="Período",
                yaxis_title="Vendas (R$)",
                template="plotly_white",
                xaxis=dict(tickangle=45),
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Identificar meses de alta e baixa
            alto_mes = monthly_data.loc[monthly_data["Valor_Total"].idxmax()]
            baixo_mes = monthly_data.loc[monthly_data["Valor_Total"].idxmin()]
            
            st.info(f"💡 **Padrão Sazonal:** As vendas tendem a ser mais altas em {alto_mes['Mes_Nome']} e mais baixas em {baixo_mes['Mes_Nome']}. Considere ajustar campanhas promocionais e estoques de acordo com esses períodos.")
        
        else:
            # Mostrar padrão semanal se não tiver dados mensais suficientes
            weekly_data = filtered_df.groupby("Dia_Semana").agg({
                "Valor_Total": "sum",
                "Qtd_Vendida": "sum"
            }).reset_index()
            
            # Ordenar dias da semana corretamente
            dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            dias_ptbr = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
            dias_map = dict(zip(dias_ordem, dias_ptbr))
            
            weekly_data['Dia_Semana_PT'] = weekly_data['Dia_Semana'].map(dias_map)
            weekly_data = weekly_data.sort_values(by='Dia_Semana', key=lambda x: pd.Categorical(x, categories=dias_ordem, ordered=True))
            
            # Criar gráfico de barras
            fig = px.bar(
                weekly_data,
                x="Dia_Semana_PT",
                y="Valor_Total",
                text=weekly_data["Valor_Total"].apply(lambda x: f"R$ {x:,.0f}"),
                color_discrete_sequence=["#4e73df"],
                labels={"Valor_Total": "Total de Vendas (R$)", "Dia_Semana_PT": "Dia da Semana"}
            )
            
            fig.update_layout(
                title="Padrão Semanal de Vendas",
                #titlefont=dict(size=16),
                title_font=dict(size=16),  # Note o underscore entre title e font
                showlegend=False,
                template="plotly_white",
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            fig.update_traces(textposition="outside")
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Identificar dias de alta e baixa
            alto_dia = weekly_data.loc[weekly_data["Valor_Total"].idxmax()]["Dia_Semana_PT"]
            baixo_dia = weekly_data.loc[weekly_data["Valor_Total"].idxmin()]["Dia_Semana_PT"]
            
            st.info(f"💡 **Padrão Semanal:** As vendas tendem a ser mais altas na {alto_dia} e mais baixas na {baixo_dia}. Considere ajustar a escala de funcionários e promoções para estes dias.")
    
    with insight_cols[2]:
        # Análise de promoções e descontos
        st.markdown("### Impacto de Promoções")
        
        # Comparar vendas com e sem promoção
        promo_analysis = filtered_df.groupby("Promocao").agg({
            "Valor_Total": "sum",
            "Qtd_Vendida": "sum",
            "Clientes_Unicos": "sum",
            "Lucro_Liquido": "sum"
        }).reset_index()
        
        promo_analysis["Ticket_Medio"] = promo_analysis["Valor_Total"] / promo_analysis["Clientes_Unicos"]
        promo_analysis["Margem"] = (promo_analysis["Lucro_Liquido"] / promo_analysis["Valor_Total"]) * 100
        promo_analysis["Status"] = promo_analysis["Promocao"].map({True: "Com Promoção", False: "Sem Promoção"})
        
        # Criar gráfico de comparação
        fig = make_subplots(
            rows=2, cols=1,
            specs=[[{"type": "bar"}], [{"type": "bar"}]],
            subplot_titles=("Volume de Vendas", "Indicadores de Desempenho"),
            vertical_spacing=0.2
        )
        
        # Volume de vendas
        fig.add_trace(
            go.Bar(
                x=promo_analysis["Status"],
                y=promo_analysis["Valor_Total"],
                name="Valor de Vendas",
                marker_color="#4e73df",
                text=promo_analysis["Valor_Total"].apply(lambda x: f"R$ {x:,.0f}"),
                textposition="auto",
                hovertemplate="Status: %{x}<br>Vendas: R$ %{y:,.2f}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Ticket médio e margem
        fig.add_trace(
            go.Bar(
                x=promo_analysis["Status"],
                y=promo_analysis["Ticket_Medio"],
                name="Ticket Médio",
                marker_color="#1cc88a",
                text=promo_analysis["Ticket_Medio"].apply(lambda x: f"R$ {x:,.0f}"),
                textposition="auto",
                hovertemplate="Status: %{x}<br>Ticket Médio: R$ %{y:,.2f}<extra></extra>"
            ),
            row=2, col=1
        )
        
        fig.add_trace(
            go.Bar(
                x=promo_analysis["Status"],
                y=promo_analysis["Margem"],
                name="Margem (%)",
                marker_color="#f6c23e",
                text=promo_analysis["Margem"].apply(lambda x: f"{x:.1f}%"),
                textposition="auto",
                hovertemplate="Status: %{x}<br>Margem: %{y:.1f}%<extra></extra>"
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            title="Análise de Impacto das Promoções",
            ##titlefont=dict(size=16),
            title_font=dict(size=16),  # Note o underscore entre title e font
            showlegend=True,
            template="plotly_white",
            height=500,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendação sobre promoções
        if len(promo_analysis) == 2:
            com_promo = promo_analysis[promo_analysis["Promocao"] == True]
            sem_promo = promo_analysis[promo_analysis["Promocao"] == False]
            
            if not com_promo.empty and not sem_promo.empty:
                diff_vendas = ((com_promo["Valor_Total"].values[0] / sem_promo["Valor_Total"].values[0]) - 1) * 100
                diff_margem = com_promo["Margem"].values[0] - sem_promo["Margem"].values[0]
                
                if diff_vendas > 20 and diff_margem > -5:
                    recomendacao = "As promoções estão gerando um aumento significativo nas vendas sem comprometer muito a margem de lucro. Recomenda-se continuar com a estratégia promocional."
                elif diff_vendas > 20 and diff_margem < -10:
                    recomendacao = "As promoções aumentam o volume de vendas, mas estão impactando negativamente a margem. Considere ajustar os percentuais de desconto."
                else:
                    recomendacao = "O impacto das promoções não está sendo tão expressivo. Considere revisar a estratégia promocional para melhorar a efetividade."
                
                st.info(f"💡 **Análise Promocional:** {recomendacao}")
    
    # Quarta linha - Mapa de calor de vendas
    st.markdown("## 🗓️ Padrões Temporais de Vendas")
    
    # Verificar se há dados suficientes para análise diária (pelo menos 2 semanas)
    if (filtered_df["Data"].max() - filtered_df["Data"].min()).days >= 14:
        # Preparar dados para o mapa de calor
        # Extrair o dia da semana e a hora
        if "Hora" not in filtered_df.columns and "Data" in filtered_df.columns:
            #filtered_df["Dia_Num"] = filtered_df["Data"].dt.dayofweek  # 0 = Segunda, 6 = Domingo
            filtered_df = filtered_df.copy()
            filtered_df.loc[:, "Dia_Num"] = filtered_df["Data"].dt.dayofweek  # 0 = Segunda, 6 = Domingo
        
        # Criar um dataframe diário
        # Agregar por dia da semana
        heatmap_data = filtered_df.groupby(["Dia_Num", "Dia_Semana"]).agg({
            "Valor_Total": "sum",
            "Qtd_Vendida": "sum"
        }).reset_index()
        
        # Ordenar dias da semana corretamente
        dias_ordem = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_num = [0, 1, 2, 3, 4, 5, 6]
        dias_ptbr = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        
        dias_num_map = dict(zip(dias_ordem, dias_num))
        dias_ptbr_map = dict(zip(dias_ordem, dias_ptbr))
        
        heatmap_data["Dia_Num"] = heatmap_data["Dia_Semana"].map(dias_num_map)
        #heatmap_data["Dia_Semana_PT"] = heatmap_data["Dia_Semana"].map(dias_ptbr_map)
        heatmap_data.loc[:, "Dia_Semana_PT"] = heatmap_data["Dia_Semana"].map(dias_ptbr_map)
        
        # Reordenar os dados
        heatmap_data = heatmap_data.sort_values("Dia_Num")
        
        # Dados mensais para o segundo mapa de calor
        if (filtered_df["Data"].max() - filtered_df["Data"].min()).days >= 60:
            monthly_heatmap = filtered_df.groupby(["Ano", "Mes"]).agg({
                "Valor_Total": "sum",
                "Qtd_Vendida": "sum"
            }).reset_index()
            
            # Criar nomes de meses para a exibição
            months = {1: "Jan", 2: "Fev", 3: "Mar", 4: "Abr", 5: "Mai", 6: "Jun", 
                    7: "Jul", 8: "Ago", 9: "Set", 10: "Out", 11: "Nov", 12: "Dez"}
            
            monthly_heatmap["Mes_Nome"] = monthly_heatmap["Mes"].map(months)
            
            # Criar dois gráficos lado a lado
            heatmap_col1, heatmap_col2 = st.columns(2)
            
            with heatmap_col1:
                # Criar mapa de calor semanal
                #heatmap_data["Vendas"] = "Total"  # Cria uma coluna única com valor constante
                fig = px.density_heatmap(
                    heatmap_data,
                    x="Dia_Semana_PT",
                    z="Valor_Total",
                    color_continuous_scale="Viridis",
                    labels={"Valor_Total": "Vendas (R$)", "Dia_Semana_PT": ""},
                    text_auto=".2s"
                )
                # fig = px.density_heatmap(
                #     heatmap_data,
                #     x="Dia_Semana_PT",
                #     y=["Vendas Semanais"],  # Y fictício para ter apenas uma linha
                #     z="Valor_Total",
                #     color_continuous_scale="Viridis",
                #     labels={"Valor_Total": "Vendas (R$)", "Dia_Semana_PT": ""},
                #     text_auto=".2s"
                # )
                
                fig.update_layout(
                    title="Distribuição de Vendas por Dia da Semana",
                    #titlefont=dict(size=16),
                    title_font=dict(size=16),  # Note o underscore entre title e font
                    showlegend=False,
                    height=250,
                    yaxis=dict(showticklabels=False),  # Esconder o eixo Y
                    margin=dict(l=20, r=20, t=40, b=20),
                    coloraxis_colorbar=dict(title="Vendas (R$)")
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            with heatmap_col2:
                # Criar mapa de calor mensal
                fig = px.density_heatmap(
                    monthly_heatmap,
                    x="Mes_Nome",
                    y="Ano",
                    z="Valor_Total",
                    color_continuous_scale="Viridis",
                    labels={"Valor_Total": "Vendas (R$)", "Mes_Nome": "", "Ano": "Ano"},
                    text_auto=".2s"
                )
                
                fig.update_layout(
                    title="Distribuição de Vendas por Mês e Ano",
                    #titlefont=dict(size=16),
                    title_font=dict(size=16),  # Note o underscore entre title e font
                    showlegend=False,
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20),
                    coloraxis_colorbar=dict(title="Vendas (R$)")
                )
                
                st.plotly_chart(fig, use_container_width=True)
        else:
            # Se não houver dados suficientes para análise mensal, mostrar apenas o mapa semanal em largura total
            fig = px.density_heatmap(
                heatmap_data,
                x="Dia_Semana_PT",
                y=["Vendas Semanais"],  # Y fictício para ter apenas uma linha
                z="Valor_Total",
                color_continuous_scale="Viridis",
                labels={"Valor_Total": "Vendas (R$)", "Dia_Semana_PT": ""},
                text_auto=".2s"
            )
            
            fig.update_layout(
                title="Distribuição de Vendas por Dia da Semana",
                #titlefont=dict(size=16),
                title_font=dict(size=16),  # Note o underscore entre title e font
                showlegend=False,
                height=250,
                yaxis=dict(showticklabels=False),  # Esconder o eixo Y
                margin=dict(l=20, r=20, t=40, b=20),
                coloraxis_colorbar=dict(title="Vendas (R$)")
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Quinta linha - Análise de Clientes e Métricas Principais
    st.markdown("## 👥 Análise de Clientes")
    client_col1, client_col2 = st.columns(2)
    
    with client_col1:
        # Análise de novos clientes vs. recorrentes
        clientes_analysis = filtered_df.groupby("Cliente_Novo").agg({
            "Clientes_Unicos": "sum",
            "Valor_Total": "sum",
            "Lucro_Liquido": "sum"
        }).reset_index()
        
        clientes_analysis["Tipo_Cliente"] = clientes_analysis["Cliente_Novo"].map({True: "Novos", False: "Recorrentes"})
        clientes_analysis["Ticket_Medio"] = clientes_analysis["Valor_Total"] / clientes_analysis["Clientes_Unicos"]
        
        # Calcular percentuais
        total_clientes = clientes_analysis["Clientes_Unicos"].sum()
        clientes_analysis["Percentual"] = (clientes_analysis["Clientes_Unicos"] / total_clientes) * 100
        
        # Criar gráfico de pizza com métricas
        colors = ['#1cc88a', '#4e73df']
        
        fig = make_subplots(
            rows=1, cols=2,
            specs=[[{"type": "domain"}, {"type": "xy"}]],
            subplot_titles=("Distribuição de Clientes", "Ticket Médio por Tipo")
        )
        
        # Gráfico de pizza
        fig.add_trace(
            go.Pie(
                labels=clientes_analysis["Tipo_Cliente"],
                values=clientes_analysis["Clientes_Unicos"],
                hole=0.7,
                textinfo="percent",
                marker=dict(colors=colors),
                textposition="inside",
                hovertemplate="Tipo: %{label}<br>Quantidade: %{value:,.0f}<br>Percentual: %{percent}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Adicionar texto ao centro do gráfico de pizza
        fig.add_annotation(
            text=f"{total_clientes:,.0f}<br>Clientes",
            font=dict(size=14, color="black", family="Arial"),
            showarrow=False,
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            xanchor="center", yanchor="middle"
        )
        # fig.add_annotation(
        #     x=0.5, y=0.5,
        #     text=f"{total_clientes:,.0f}<br>Clientes",
        #     font=dict(size=14, color="black", family="Arial"),
        #     showarrow=False,
        #     xref="x domain", yref="y domain",
        #     row=1, col=1
        # )
        
        # Gráfico de barras
        fig.add_trace(
            go.Bar(
                x=clientes_analysis["Tipo_Cliente"],
                y=clientes_analysis["Ticket_Medio"],
                marker_color=colors,
                text=clientes_analysis["Ticket_Medio"].apply(lambda x: f"R$ {x:,.2f}"),
                textposition="auto",
                hovertemplate="Tipo: %{x}<br>Ticket Médio: R$ %{y:,.2f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        fig.update_layout(
            title="Análise de Clientes Novos vs. Recorrentes",
            #titlefont=dict(size=16),
            title_font=dict(size=16),  # Note o underscore entre title e font
            showlegend=False,
            template="plotly_white",
            margin=dict(l=20, r=20, t=60, b=20),
            height=350
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendação de clientes
        if len(clientes_analysis) == 2:
            novos = clientes_analysis[clientes_analysis["Cliente_Novo"] == True]
            recorrentes = clientes_analysis[clientes_analysis["Cliente_Novo"] == False]
            
            if not novos.empty and not recorrentes.empty:
                prop_novos = novos["Clientes_Unicos"].values[0] / total_clientes * 100
                diff_ticket = (recorrentes["Ticket_Medio"].values[0] / novos["Ticket_Medio"].values[0] - 1) * 100
                
                if prop_novos > 40:
                    base_rec = "A proporção de novos clientes está alta (acima de 40%)."
                elif prop_novos < 15:
                    base_rec = "A proporção de novos clientes está baixa (menos de 15%)."
                else:
                    base_rec = "A proporção entre novos clientes e recorrentes está equilibrada."
                
                if diff_ticket > 20:
                    ticket_rec = "Os clientes recorrentes têm um ticket médio significativamente maior que os novos."
                    acao = "Desenvolva estratégias de fidelização para converter mais clientes novos em recorrentes."
                elif diff_ticket < -10:
                    ticket_rec = "Os clientes novos têm um ticket médio maior que os recorrentes."
                    acao = "Analise por que os clientes recorrentes estão gastando menos e desenvolva ofertas especiais para aumentar seu consumo."
                else:
                    ticket_rec = "O ticket médio é similar entre clientes novos e recorrentes."
                    acao = "Continue investindo em estratégias balanceadas de aquisição e retenção."
                
                st.info(f"💡 **Análise de Base de Clientes:** {base_rec} {ticket_rec} {acao}")
    
    with client_col2:
        # Análise de frequência e recorrência
        
        # Verificar se há dados de valor de ticket médio ou calculá-lo
        # if "Valor_Ticket_Medio" in filtered_df.columns:
        #     ticket_data = filtered_df.groupby("Localizacao")["Valor_Ticket_Medio"].mean().reset_index()
        # else:
            # Calcular o ticket médio por localização
        ticket_data = filtered_df.groupby("Localizacao").agg({
                "Valor_Total": "sum",
                "Clientes_Unicos": "sum"
            }).reset_index()

            
            
            #ticket_data["Valor_Ticket_Medio"] = ticket_data["Valor_Total"] / ticket_data["Clientes_Unicos"]
            # Criar coluna de ticket médio
        ticket_data["Valor_Ticket_Medio"] = ticket_data.apply(
                lambda row: row["Valor_Total"] / row["Clientes_Unicos"] if row["Clientes_Unicos"] > 0 else 0, 
                axis=1
            )
                    
        # Ordenar por ticket médio
        #ticket_data = ticket_data.sort_values("Valor_Ticket_Medio", ascending=False)
        # Ordenar por ticket médio
        ticket_data = ticket_data.sort_values("Valor_Ticket_Medio", ascending=False)
        
        # Criar gráfico de barras
        fig = px.bar(
            ticket_data,
            x="Localizacao",
            y="Valor_Ticket_Medio",
            text=ticket_data["Valor_Ticket_Medio"].apply(lambda x: f"R$ {x:,.2f}"),
            color="Valor_Ticket_Medio",
            color_continuous_scale="Viridis",
            labels={"Valor_Ticket_Medio": "Ticket Médio (R$)", "Localizacao": "Loja"}
        )
        
        # Adicionar linha para média geral
        media_geral = ticket_data["Valor_Ticket_Medio"].mean()
        
        fig.add_shape(
            type="line",
            x0=-0.5,
            y0=media_geral,
            x1=len(ticket_data) - 0.5,
            y1=media_geral,
            line=dict(color="red", width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=len(ticket_data) / 2,
            y=media_geral * 1.1,
            text=f"Média Geral: R$ {media_geral:.2f}",
            showarrow=False,
            font=dict(color="red")
        )
        
        fig.update_layout(
            title="Ticket Médio por Loja",
            #titlefont=dict(size=16),
            title_font=dict(size=16),  # Note o underscore entre title e font
            showlegend=False,
            template="plotly_white",
            margin=dict(l=20, r=20, t=40, b=20),
            height=350,
            coloraxis_colorbar=dict(title="Ticket Médio (R$)")
        )
        
        fig.update_traces(textposition="outside")
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Recomendação de ticket médio
        # Recomendação de ticket médio
        if not ticket_data.empty:
            highest_location = ticket_data.iloc[0]["Localizacao"]
            lowest_location = ticket_data.iloc[-1]["Localizacao"]
            highest_ticket = ticket_data.iloc[0]["Valor_Ticket_Medio"]
            lowest_ticket = ticket_data.iloc[-1]["Valor_Ticket_Medio"]
            
            # Adicione um valor mínimo para evitar divisão por zero
            if lowest_ticket <= 0.01:
                lowest_ticket = 0.01  # Estabelecer um valor mínimo
            
            diff_percent = ((highest_ticket / lowest_ticket) - 1) * 100
            
            if diff_percent > 30:
                st.info(f"💡 **Análise de Ticket Médio:** Há uma variação de {diff_percent:.1f}% entre o maior e o menor ticket médio. A loja {highest_location} tem as melhores práticas de venda com ticket de R$ {highest_ticket:.2f}. Considere aplicar técnicas de venda cruzada e upselling na loja {lowest_location} para aumentar seu ticket médio atual.")
            else:
                st.info(f"💡 **Análise de Ticket Médio:** A diferença entre o maior e o menor ticket médio é de {diff_percent:.1f}%, indicando uma relativa consistência entre as lojas. Continue monitorando e ajustando estratégias para manter essa uniformidade.")
        else:
            # Para o caso raro onde o DataFrame está vazio
            st.info("💡 **Análise de Ticket Médio:** Os filtros aplicados não retornaram dados suficientes para análise de ticket médio. Tente ajustar os filtros para incluir mais dados.")
            
    # Sexta linha - Recomendações finais e métricas de eficiência
    st.markdown("## 📊 Resumo de Performance e Recomendações")
    
    # Calcular métricas de performance
    rentabilidade_media = filtered_df["Rentabilidade"].mean()
    eficiencia_media = filtered_df["Eficiencia_Operacional"].mean()
    
    margem_geral = (filtered_df["Lucro_Liquido"].sum() / filtered_df["Valor_Total"].sum()) * 100
    
    # Calcular custo médio de aquisição (se possível)
    try:
        # custo_aquisicao = filtered_df[filtered_df["Cliente_Novo"] == True]["Valor_Total"].sum() / filtered_df[filtered_df["Cliente_Novo"] == True]["Clientes_Unicos"].sum()
        # Use:
        novos_clientes_df = filtered_df[filtered_df["Cliente_Novo"] == True]
        total_valor_novos = novos_clientes_df["Valor_Total"].sum()
        total_clientes_novos = novos_clientes_df["Clientes_Unicos"].sum()

        # Verificar divisão por zero
        if total_clientes_novos > 0:
            custo_aquisicao = total_valor_novos / total_clientes_novos
        else:
            custo_aquisicao = 0  # Ou qualquer outro valor padrão que faça sentido
    except:
        custo_aquisicao = 0
    
    # Linha de métricas de performance
    perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
    
    with perf_col1:
        st.metric(
            label="Margem Média", 
            value=f"{margem_geral:.2f}%",
            delta=f"{margem_geral - 15:.2f}pp" if margem_geral > 15 else f"{margem_geral - 15:.2f}pp",
            delta_color="normal"
        )
    
    with perf_col2:
        st.metric(
            label="Rentabilidade Média", 
            value=f"{rentabilidade_media:.2f}%",
            delta=f"{rentabilidade_media - 10:.2f}pp" if rentabilidade_media > 10 else f"{rentabilidade_media - 10:.2f}pp",
            delta_color="normal"
        )
    
    with perf_col3:
        st.metric(
            label="Eficiência Operacional", 
            value=f"R$ {eficiencia_media:.2f}/min",
            delta=f"{eficiencia_media - 50:.2f}" if eficiencia_media > 50 else f"{eficiencia_media - 50:.2f}",
            delta_color="normal"
        )
    
    with perf_col4:
        if custo_aquisicao > 0:
            st.metric(
                label="Custo Médio Aquisição", 
                value=f"R$ {custo_aquisicao:.2f}",
                delta=None
            )
        else:
            st.metric(
                label="Taxa de Novos Clientes", 
                value=f"{(filtered_df[filtered_df['Cliente_Novo'] == True]['Clientes_Unicos'].sum() / filtered_df['Clientes_Unicos'].sum() * 100):.2f}%",
                delta=None
            )
    
    # Resumo e recomendações finais
    st.markdown("### 💎 Principais Insights e Recomendações")
    
    # Criar insights baseados nos dados
    insights = []
    
    # Insight 1 - Produtos
    try:
        top_produto = filtered_df.groupby("Produto")["Valor_Total"].sum().nlargest(1).index[0]
        top_categoria = filtered_df.groupby("Categoria")["Valor_Total"].sum().nlargest(1).index[0]
        insights.append(f"O produto mais vendido é **{top_produto}** da categoria **{top_categoria}**. Considere destacá-lo em campanhas e garantir sempre disponibilidade em estoque.")
    except:
        pass
    
    # Insight 2 - Vendas por Dia/Período
    try:
        if "Dia_Semana" in filtered_df.columns:
            top_dia = filtered_df.groupby("Dia_Semana")["Valor_Total"].sum().nlargest(1).index[0]
            dias_ptbr_map = {
                'Monday': 'Segunda-feira', 
                'Tuesday': 'Terça-feira', 
                'Wednesday': 'Quarta-feira', 
                'Thursday': 'Quinta-feira', 
                'Friday': 'Sexta-feira', 
                'Saturday': 'Sábado', 
                'Sunday': 'Domingo'
            }
            top_dia_pt = dias_ptbr_map.get(top_dia, top_dia)
            insights.append(f"O dia com maior volume de vendas é **{top_dia_pt}**. Considere aumentar a equipe e estoques neste dia para maximizar as vendas.")
    except:
        pass
    
    # Insight 3 - Canal mais rentável
    try:
        canal_rentability = filtered_df.groupby("Canal").agg({
            "Valor_Total": "sum",
            "Lucro_Liquido": "sum"
        }).reset_index()
        
        canal_rentability["Margem"] = (canal_rentability["Lucro_Liquido"] / canal_rentability["Valor_Total"]) * 100
        top_canal_margin = canal_rentability.loc[canal_rentability["Margem"].idxmax()]
        
        insights.append(f"O canal **{top_canal_margin['Canal']}** apresenta a maior margem de lucro ({top_canal_margin['Margem']:.1f}%). Avalie a possibilidade de direcionar mais recursos para este canal de vendas.")
    except:
        pass
    
    # Insight 4 - Eficiência Operacional
    try:
        tempo_medio_preparo = filtered_df["Tempo_Preparo"].mean()
        loja_mais_rapida = filtered_df.groupby("Localizacao")["Tempo_Preparo"].mean().nsmallest(1)
        loja_mais_rapida_nome = loja_mais_rapida.index[0]
        loja_mais_rapida_tempo = loja_mais_rapida.values[0]
        
        insights.append(f"A loja **{loja_mais_rapida_nome}** tem o menor tempo médio de preparo ({loja_mais_rapida_tempo:.1f} min vs. média geral de {tempo_medio_preparo:.1f} min). Analise seus processos para aplicar nas demais unidades.")
    except:
        pass
    
    # Insight 5 - Promoções
    try:
        if "Promocao" in filtered_df.columns:
            promo_df = filtered_df[filtered_df["Promocao"] == True]
            sem_promo_df = filtered_df[filtered_df["Promocao"] == False]
            
            if not promo_df.empty and not sem_promo_df.empty:
                promo_lucro = promo_df["Lucro_Liquido"].sum() / promo_df["Valor_Total"].sum() * 100
                sem_promo_lucro = sem_promo_df["Lucro_Liquido"].sum() / sem_promo_df["Valor_Total"].sum() * 100
                
                if promo_lucro > sem_promo_lucro:
                    insights.append(f"Surpreendentemente, as vendas com promoção têm maior margem ({promo_lucro:.1f}%) do que as sem promoção ({sem_promo_lucro:.1f}%). Isto sugere que as promoções estão atraindo maior volume sem comprometer a lucratividade.")
                else:
                    diff = sem_promo_lucro - promo_lucro
                    if diff > 10:
                        nivel = "significativamente"
                    else:
                        nivel = "levemente"
                    
                    insights.append(f"As vendas sem promoção são {nivel} mais rentáveis ({sem_promo_lucro:.1f}% vs {promo_lucro:.1f}%). Considere ajustar os percentuais de desconto para melhorar a margem das vendas promocionais.")
    except:
        pass
    
    # Apresentar insights em formato de cartões
    if insights:
        st.markdown("#### Principais Insights:")
        
        for i, insight in enumerate(insights):
            st.markdown(f"""
            <div style="background-color: white; border-left: 4px solid #4e73df; padding: 15px; border-radius: 4px; margin-bottom: 15px; box-shadow: 0 0.15rem 1.75rem 0 rgba(58, 59, 69, 0.15);">
                <p style="margin: 0; color: #5a5c69;">{i+1}. {insight}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Histórico de dados
    if st.checkbox("Mostrar dados filtrados"):
        st.dataframe(filtered_df.style.background_gradient(cmap='Blues', subset=['Valor_Total', 'Lucro_Liquido']))
    
    # Exportar dados
    with st.expander("Exportar dados"):
        col_exp1, col_exp2 = st.columns(2)
        
        with col_exp1:
            st.download_button(
                label="📥 Baixar dados filtrados (CSV)",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"acai_fitness_dados_{start_date.strftime('%Y-%m-%d')}_a_{end_date.strftime('%Y-%m-%d')}.csv",
                mime='text/csv',
            )
        
        with col_exp2:
            st.download_button(
                label="📥 Baixar dados filtrados (Excel)",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f"acai_fitness_dados_{start_date.strftime('%Y-%m-%d')}_a_{end_date.strftime('%Y-%m-%d')}.csv",
                mime='text/csv',
            )
    
    # Footer
    st.markdown("""
    <div style="text-align: center; margin-top: 40px; padding: 20px; color: #6c757d; font-size: 0.8rem;">
        <p>Açaí Fitness Analytics Dashboard v2.0 | Atualizado em: {}</p>
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)