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
DB_NAME = "financas_completo.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabela de Perfil e Renda Mensal
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            renda_mensal REAL
        )
    ''')
    
    # Tabela de Cartões de Crédito
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            limite REAL NOT NULL,
            fechamento INTEGER
        )
    ''')
    
    # Tabela de Transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            categoria TEXT NOT NULL,
            cartao TEXT,
            parcela_info TEXT
        )
    ''')
    
    # Tabela de Metas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor_alvo REAL NOT NULL,
            valor_atual REAL NOT NULL
        )
    ''')
    
    # Garante um perfil padrão se não existir
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user_profile (nome, renda_mensal) VALUES (?, ?)", ("Usuário", 0.0))
        
    conn.commit()
    conn.close()

init_db()

# Funções auxiliares de Banco de Dados
def get_user_profile():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, renda_mensal FROM user_profile LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res if res else ("Usuário", 0.0)

def update_user_profile(nome, renda):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_profile SET nome = ?, renda_mensal = ? WHERE id = 1", (nome, renda))
    conn.commit()
    conn.close()

def get_cards():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM credit_cards", conn)
    conn.close()
    return df

def add_card(nome, limite, fechamento):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO credit_cards (nome, limite, fechamento) VALUES (?, ?, ?)", (nome, limite, fechamento))
    conn.commit()
    conn.close()

def delete_card(card_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM credit_cards WHERE id = ?", (card_id,))
    conn.commit()
    conn.close()

def add_transaction(tipo, descricao, valor, data, categoria, cartao, parcelas=1):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    data_obj = datetime.strptime(str(data), "%Y-%m-%d")
    
    if parcelas > 1:
        valor_parcela = valor / parcelas
        for i in range(1, parcelas + 1):
            data_p = data_obj + relativedelta(months=i-1)
            p_info = f"{i}/{parcelas}"
            cursor.execute('''
                INSERT INTO transactions (tipo, descricao, valor, data, categoria, cartao, parcela_info)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (tipo, f"{descricao} (Parc {p_info})", valor_parcela, data_p.strftime("%Y-%m-%d"), categoria, cartao, p_info))
    else:
        cursor.execute('''
            INSERT INTO transactions (tipo, descricao, valor, data, categoria, cartao, parcela_info)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tipo, descricao, valor, data_obj.strftime("%Y-%m-%d"), categoria, cartao, "1/1"))
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

# Menu Lateral
user_nome, user_renda = get_user_profile()
st.sidebar.title(f"💰 Olá, {user_nome}!")
menu = st.sidebar.radio("Navegação", ["Dashboard", "Perfil & Renda", "Cartões de Crédito", "Lançamentos", "Metas"])

df_tx = get_transactions()
df_cards = get_cards()

# ================= TELA 1: DASHBOARD =================
if menu == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    renda_cadastrada = user_renda
    receitas_extras = df_tx[df_tx['tipo'] == 'Receita']['valor'].sum() if not df_tx.empty else 0
    total_receitas = renda_cadastrada + receitas_extras
    total_despesas = df_tx[df_tx['tipo'] == 'Despesa']['valor'].sum() if not df_tx.empty else 0
    saldo = total_receitas - total_despesas
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Atual", f"R$ {saldo:,.2f}")
    col2.metric("Renda Total", f"R$ {total_receitas:,.2f}")
    col3.metric("Total Despesas", f"R$ {total_despesas:,.2f}")
    col4.metric("Qtd. Cartões", f"{len(df_cards)}")
    
    st.divider()
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Despesas por Categoria")
        if not df_tx.empty:
            df_desp = df_tx[df_tx['tipo'] == 'Despesa']
            if not df_desp.empty:
                cat_sum = df_desp.groupby('categoria')['valor'].sum()
                st.bar_chart(cat_sum)
            else:
                st.write("Sem despesas registradas.")
        else:
            st.write("Sem dados.")
            
    with col_g2:
        st.subheader("Gastos por Cartão de Crédito")
        if not df_tx.empty:
            df_cartao = df_tx[df_tx['cartao'].notna() & (df_tx['cartao'] != "Nenhum / Dinheiro")]
            if not df_cartao.empty:
                card_sum = df_cartao.groupby('cartao')['valor'].sum()
                st.bar_chart(card_sum)
            else:
                st.write("Nenhum gasto vinculado a cartão.")
        else:
            st.write("Sem dados.")

# ================= TELA 2: PERFIL & RENDA =================
elif menu == "Perfil & Renda":
    st.title("👤 Configuração do Usuário e Renda")
    
    with st.form("form_perfil"):
        novo_nome = st.text_input("Seu Nome", value=user_nome)
        nova_renda = st.number_input("Renda Mensal Fixa (R$)", min_value=0.0, value=float(user_renda), format="%.2f")
        
        btn_salvar = st.form_submit_button("Salvar Alterações")
        if btn_salvar:
            update_user_profile(novo_nome, nova_renda)
            st.success("Perfil atualizado com sucesso!")
            st.rerun()

# ================= TELA 3: CARTÕES DE CRÉDITO =================
elif menu == "Cartões de Crédito":
    st.title("💳 Gerenciar Cartões de Crédito")
    
    with st.form("form_cartao"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome_cartao = st.text_input("Nome do Cartão (ex: Nubank, Visa)")
        with col2:
            limite = st.number_input("Limite (R$)", min_value=0.0, format="%.2f")
        with col3:
            fechamento = st.number_input("Dia de Fechamento", min_value=1, max_value=31, value=10)
            
        btn_add_card = st.form_submit_button("Adicionar Cartão")
        if btn_add_card:
            if nome_cartao:
                add_card(nome_cartao, limite, int(fechamento))
                st.success("Cartão adicionado com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome do cartão.")
                
    st.divider()
    st.subheader("Seus Cartões Cadastrados")
    if not df_cards.empty:
        st.dataframe(df_cards, use_container_width=True)
        
        cartao_para_excluir = st.selectbox("Selecione o ID do cartão para excluir", options=df_cards['id'].tolist())
        if st.button("Excluir Cartão Selecionado"):
            delete_card(cartao_para_excluir)
            st.success("Cartão excluído!")
            st.rerun()
    else:
        st.info("Nenhum cartão cadastrado ainda.")

# ================= TELA 4: LANÇAMENTOS =================
elif menu == "Lançamentos":
    st.title("📝 Gerenciar Lançamentos")
    
    lista_cartoes = ["Nenhum / Dinheiro"] + df_cards['nome'].tolist() if not df_cards.empty else ["Nenhum / Dinheiro"]
    
    with st.form("form_lancamento"):
        col1, col2 = st.columns(2)
        with col1:
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            descricao = st.text_input("Descrição (ex: Supermercado, Freela)")
            valor = st.number_input("Valor Total (R$)", min_value=0.01, format="%.2f")
        with col2:
            categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Educação", "Saúde", "Lazer", "Salário", "Investimentos", "Outros"])
            cartao_usado = st.selectbox("Cartão de Crédito", lista_cartoes)
            data = st.date_input("Data", datetime.today())
            parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=48, value=1)
            
        submitted = st.form_submit_button("Adicionar Lançamento")
        if submitted:
            if descricao:
                add_transaction(tipo, descricao, valor, str(data), categoria, cartao_usado, int(parcelas))
                st.success("Lançamento adicionado com sucesso!")
                st.rerun()
            else:
                st.error("Por favor, preencha a descrição.")

    st.divider()
    st.subheader("Histórico de Movimentações")
    if not df_tx.empty:
        st.dataframe(df_tx, use_container_width=True)
        
        tx_para_excluir = st.selectbox("Selecione o ID da transação para excluir", options=df_tx['id'].tolist())
        if st.button("Excluir Lançamento Selecionado"):
            delete_transaction(tx_para_excluir)
            st.success(f"Lançamento ID {tx_para_excluir} excluído!")
            st.rerun()
    else:
        st.write("Nenhum lançamento encontrado.")

# ================= TELA 5: METAS =================
elif menu == "Metas":
    st.title("🎯 Metas Financeiras")
    
    with st.form("form_meta"):
        nome_meta = st.text_input("Nome da Meta (ex: Viagem, Reserva de Emergência)")
        valor_alvo = st.number_input("Valor Alvo (R$)", min_value=1.0, format="%.2f")
        valor_atual = st.number_input("Valor já Guardado (R$)", min_value=0.0, format="%.2f")
        
        btn_meta = st.form_submit_button("Criar Meta")
        if btn_meta:
            if nome_meta:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO goals (nome, valor_alvo, valor_atual) VALUES (?, ?, ?)", (nome_meta, valor_alvo, valor_atual))
                conn.commit()
                conn.close()
                st.success("Meta criada com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome da meta.")

    st.divider()
    conn = sqlite3.connect(DB_NAME)
    df_metas = pd.read_sql_query("SELECT * FROM goals", conn)
    conn.close()
    
    if not df_metas.empty:
        for _, row in df_metas.iterrows():
            st.subheader(f"🎯 {row['nome']}")
            progresso = min(row['valor_atual'] / row['valor_alvo'], 1.0)
            st.progress(progresso)
            st.write(f"Guardado: R$ {row['valor_atual']:,.2f} / Alvo: R$ {row['valor_alvo']:,.2f} ({progresso*100:.1f}%)")
    else:
        st.write("Nenhuma meta cadastrada.")