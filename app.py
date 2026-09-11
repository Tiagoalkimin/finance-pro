import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Configuração da página do navegador
st.set_page_config(
    page_title="Personal Finance Pro",
    page_icon="💰",
    layout="wide",
)

# Inicialização do Banco de Dados SQLite local
DB_NAME = "financas_streamlit.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            categoria TEXT NOT NULL,
            parcela_info TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor_alvo REAL NOT NULL,
            valor_atual REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Funções de Banco de Dados
def add_transaction(tipo, descricao, valor, data, categoria, parcelas=1):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_obj = datetime.strptime(str(data), "%Y-%m-%d")
    
    if parcelas > 1:
        valor_parcela = valor / parcelas
        for i in range(1, parcelas + 1):
            data_p = data_obj + relativedelta(months=i-1)
            p_info = f"{i}/{parcelas}"
            cursor.execute('''
                INSERT INTO transactions (tipo, descricao, valor, data, categoria, parcela_info)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tipo, f"{descricao} (Parc {p_info})", valor_parcela, data_p.strftime("%Y-%m-%d"), categoria, p_info))
    else:
        cursor.execute('''
            INSERT INTO transactions (tipo, descricao, valor, data, categoria, parcela_info)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tipo, descricao, valor, data_obj.strftime("%Y-%m-%d"), categoria, "1/1"))
    conn.commit()
    conn.close()

def get_transactions():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY data DESC", conn)
    conn.close()
    return df

def delete_transaction(tx_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    conn.close()

def add_goal(nome, alvo, atual):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO goals (nome, valor_alvo, valor_atual) VALUES (?, ?, ?)", (nome, alvo, atual))
    conn.commit()
    conn.close()

def get_goals():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM goals", conn)
    conn.close()
    return df

# Menu Lateral (Sidebar)
st.sidebar.title("💰 Finance Pro")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Lançamentos", "Metas", "Saúde & Insights"])

df = get_transactions()

# ================= TELA 1: DASHBOARD =================
if menu == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    if df.empty:
        st.info("Nenhum lançamento cadastrado ainda. Vá na aba 'Lançamentos' no menu lateral para começar!")
    else:
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        saldo = receitas - despesas
        economia = (saldo / receitas * 100) if receitas > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        col2.metric("Total Receitas", f"R$ {receitas:,.2f}")
        col3.metric("Total Despesas", f"R$ {despesas:,.2f}")
        col4.metric("Taxa de Economia", f"{economia:.1f}%")
        
        st.divider()
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("Despesas por Categoria")
            df_desp = df[df['tipo'] == 'Despesa']
            if not df_desp.empty:
                cat_sum = df_desp.groupby('categoria')['valor'].sum()
                st.bar_chart(cat_sum)
            else:
                st.write("Sem despesas registradas.")
                
        with col_g2:
            st.subheader("Receitas vs Despesas")
            resumo_tipo = df.groupby('tipo')['valor'].sum()
            st.bar_chart(resumo_tipo)

# ================= TELA 2: LANÇAMENTOS =================
elif menu == "Lançamentos":
    st.title("📝 Gerenciar Lançamentos")
    
    with st.form("form_lancamento"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            descricao = st.text_input("Descrição (ex: Supermercado, Salário)")
            valor = st.number_input("Valor Total (R$)", min_value=0.01, format="%.2f")
        with col2:
            categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Educação", "Saúde", "Lazer", "Salário", "Investimentos", "Outros"])
            data = st.date_input("Data", datetime.today())
            parcelas = st.number_input("Número de Parcelas (Automático)", min_value=1, max_value=48, value=1)
            
        submitted = st.form_submit_button("Adicionar Lançamento")
        if submitted:
            if descricao:
                add_transaction(tipo, descricao, valor, str(data), categoria, int(parcelas))
                st.success("Lançamento adicionado com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha a descrição.")

    st.divider()
    st.subheader("Histórico de Movimentações")
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        
        tx_para_excluir = st.selectbox("Selecione o ID da transação para excluir", options=df['id'].tolist())
        if st.button("Excluir Lançamento Selecionado"):
            delete_transaction(tx_para_excluir)
            st.success(f"Lançamento ID {tx_para_excluir} excluído!")
            st.rerun()
    else:
        st.write("Nenhum dado encontrado.")

# ================= TELA 3: METAS =================
elif menu == "Metas":
    st.title("🎯 Metas Financeiras")
    
    with st.form("form_meta"):
        nome_meta = st.text_input("Nome da Meta (ex: Comprar Notebook)")
        valor_alvo = st.number_input("Valor Alvo (R$)", min_value=1.0, format="%.2f")
        valor_atual = st.number_input("Valor já Guardado (R$)", min_value=0.0, format="%.2f")
        
        btn_meta = st.form_submit_button("Criar Meta")
        if btn_meta:
            if nome_meta:
                add_goal(nome_meta, valor_alvo, valor_atual)
                st.success("Meta criada com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome da meta.")

    st.divider()
    df_metas = get_goals()
    if not df_metas.empty:
        for _, row in df_metas.iterrows():
            st.subheader(f"🎯 {row['nome']}")
            progresso = min(row['valor_atual'] / row['valor_alvo'], 1.0)
            st.progress(progresso)
            st.write(f"Guardado: R$ {row['valor_atual']:,.2f} / Alvo: R$ {row['valor_alvo']:,.2f} ({progresso*100:.1f}%)")
    else:
        st.write("Nenhuma meta cadastrada.")

# ================= TELA 4: SAÚDE & INSIGHTS =================
elif menu == "Saúde & Insights":
    st.title("🧠 Saúde Financeira e Insights")
    
    if df.empty:
        st.info("Adicione movimentações para ver sua análise de saúde financeira.")
    else:
        receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        
        if receitas == 0:
            score = 0
        else:
            comprometimento = despesas / receitas
            score = max(0, min(100, (1 - comprometimento) * 100 + 20))
            
        if score > 70:
            st.success(f"Score de Saúde Financeira: {score:.0f}/100 - Excelente 🟢")
        elif score > 40:
            st.warning(f"Score de Saúde Financeira: {score:.0f}/100 - Atenção 🟡")
        else:
            st.error(f"Score de Saúde Financeira: {score:.0f}/100 - Situação Preocupante 🔴")
            
        st.subheader("💡 Insights Automáticos")
        if receitas > 0:
            st.write(f"- Você comprometeu **{(despesas/receitas)*100:.1f}%** da sua renda total com despesas.")
        
        df_desp = df[df['tipo'] == 'Despesa']
        if not df_desp.empty:
            maior_gasto = df_desp.groupby('categoria')['valor'].sum().idxmax()
            valor_maior = df_desp.groupby('categoria')['valor'].sum().max()
            st.write(f"- Sua maior categoria de gasto atual é **{maior_gasto}** (R$ {valor_maior:,.2f}).")