import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

# Configuração da página do navegador
st.set_page_config(
    page_title="Personal Finance Pro",
    page_icon="💰",
    layout="wide",
)

# Inicialização do Banco de Dados SQLite local
DB_NAME = "financas_pro_v2.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Perfil e Renda
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            renda_mensal REAL,
            tema TEXT DEFAULT 'Escuro'
        )
    ''')
    
    # Cartões de Crédito
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS credit_cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            limite REAL NOT NULL,
            vencimento INTEGER NOT NULL
        )
    ''')
    
    # Métodos de Pagamento Dinâmicos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payment_methods (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    ''')
    
    # Categorias de Despesa Dinâmicas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL
        )
    ''')
    
    # Transações (Receitas e Despesas)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            valor REAL NOT NULL,
            data TEXT NOT NULL,
            categoria TEXT NOT NULL,
            metodo TEXT,
            cartao TEXT,
            status TEXT DEFAULT 'Pago',
            parcela_info TEXT
        )
    ''')
    
    # Planejamento Orçamentário
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planning (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT NOT NULL,
            orcado REAL NOT NULL
        )
    ''')
    
    # Dados padrão iniciais se as tabelas estiverem vazias
    cursor.execute("SELECT COUNT(*) FROM user_profile")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO user_profile (nome, renda_mensal, tema) VALUES (?, ?, ?)", ("Usuário", 0.0, "Escuro"))
        
    cursor.execute("SELECT COUNT(*) FROM payment_methods")
    if cursor.fetchone()[0] == 0:
        default_methods = ["Pix", "Dinheiro", "Débito", "Boleto", "Cartão de Crédito"]
        for m in default_methods:
            cursor.execute("INSERT INTO payment_methods (nome) VALUES (?)", (m,))
            
    cursor.execute("SELECT COUNT(*) FROM expense_categories")
    if cursor.fetchone()[0] == 0:
        default_cats = ["Alimentação", "Moradia", "Transporte", "Educação", "Saúde", "Lazer", "Outros"]
        for c in default_cats:
            cursor.execute("INSERT INTO expense_categories (nome) VALUES (?)", (c,))

    conn.commit()
    conn.close()

init_db()

# Funções auxiliares
def get_user_profile():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome, renda_mensal, tema FROM user_profile LIMIT 1")
    res = cursor.fetchone()
    conn.close()
    return res if res else ("Usuário", 0.0, "Escuro")

def update_user_profile(nome, renda, tema):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE user_profile SET nome = ?, renda_mensal = ?, tema = ? WHERE id = 1", (nome, renda, tema))
    conn.commit()
    conn.close()

def get_cards():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM credit_cards", conn)
    conn.close()
    return df

def get_payment_methods():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM payment_methods")
    res = [row[0] for row in cursor.fetchall()]
    conn.close()
    return res

def get_expense_categories():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM expense_categories")
    res = [row[0] for row in cursor.fetchall()]
    conn.close()
    return res

def get_transactions():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM transactions ORDER BY data DESC", conn)
    conn.close()
    return df

# Menu Lateral
user_nome, user_renda, user_tema = get_user_profile()
st.sidebar.title(f"💰 Olá, {user_nome}!")
menu = st.sidebar.radio(
    "Navegação", 
    [
        "Dashboard", 
        "Receitas", 
        "Despesas", 
        "Contas Futuras", 
        "Cartões de Crédito", 
        "Planejamento Mensal", 
        "Simulação", 
        "Insights", 
        "Configuração"
    ]
)

df_tx = get_transactions()
df_cards = get_cards()

# ================= 1. DASHBOARD =================
if menu == "Dashboard":
    st.title("📊 Dashboard Financeiro")
    
    receitas_extras = df_tx[(df_tx['tipo'] == 'Receita') & (df_tx['status'] == 'Pago')]['valor'].sum() if not df_tx.empty else 0
    total_receitas = user_renda + receitas_extras
    total_despesas = df_tx[(df_tx['tipo'] == 'Despesa') & (df_tx['status'] == 'Pago')]['valor'].sum() if not df_tx.empty else 0
    saldo = total_receitas - total_despesas
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Saldo Atual", f"R$ {saldo:,.2f}")
    col2.metric("Renda Total", f"R$ {total_receitas:,.2f}")
    col3.metric("Despesas Pagas", f"R$ {total_despesas:,.2f}")
    col4.metric("Qtd. Cartões", f"{len(df_cards)}")
    
    st.divider()
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("Despesas por Categoria")
        if not df_tx.empty:
            df_desp = df_tx[(df_tx['tipo'] == 'Despesa') & (df_tx['status'] == 'Pago')]
            if not df_desp.empty:
                st.bar_chart(df_desp.groupby('categoria')['valor'].sum())
            else:
                st.write("Sem despesas pagas registradas.")
        else:
            st.write("Sem dados.")
            
    with col_g2:
        st.subheader("Balanço Geral")
        if not df_tx.empty:
            st.bar_chart(df_tx.groupby('tipo')['valor'].sum())
        else:
            st.write("Sem dados.")

# ================= 2. RECEITAS =================
elif menu == "Receitas":
    st.title("💵 Gerenciar Receitas")
    
    with st.form("form_receita"):
        col1, col2 = st.columns(2)
        with col1:
            descricao = st.text_input("Descrição da Receita (ex: Salário Extra, Freelance)")
            valor = st.number_input("Valor (R$)", min_value=0.01, format="%.2f")
        with col2:
            categoria = st.selectbox("Categoria", ["Salário", "Investimentos", "Freelance", "Outros"])
            data = st.date_input("Data de Recebimento", datetime.today())
            status = st.selectbox("Status", ["Pago", "Pendente"])
            
        submitted = st.form_submit_button("Adicionar Receita")
        if submitted:
            if descricao:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO transactions (tipo, descricao, valor, data, categoria, status, parcela_info)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', ("Receita", descricao, valor, str(data), categoria, status, "1/1"))
                conn.commit()
                conn.close()
                st.success("Receita adicionada com sucesso!")
                st.rerun()
            else:
                st.error("Preencha a descrição.")

    st.divider()
    st.subheader("Histórico de Receitas")
    if not df_tx.empty:
        df_rec = df_tx[df_tx['tipo'] == 'Receita']
        if not df_rec.empty:
            st.dataframe(df_rec, use_container_width=True)
            tx_id = st.selectbox("ID para excluir receita", options=df_rec['id'].tolist(), key="del_rec")
            if st.button("Excluir Receita"):
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
                conn.commit()
                conn.close()
                st.success("Excluído com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma receita registrada.")
    else:
        st.info("Nenhum dado.")

# ================= 3. DESPESAS =================
elif menu == "Despesas":
    st.title("💸 Gerenciar Despesas")
    
    cats = get_expense_categories()
    methods = get_payment_methods()
    lista_cartoes = ["Nenhum / Dinheiro"] + df_cards['nome'].tolist() if not df_cards.empty else ["Nenhum / Dinheiro"]
    
    with st.form("form_despesa"):
        col1, col2 = st.columns(2)
        with col1:
            descricao = st.text_input("Descrição da Despesa (ex: Supermercado, Aluguel)")
            valor = st.number_input("Valor Total (R$)", min_value=0.01, format="%.2f")
            categoria = st.selectbox("Categoria", cats)
        with col2:
            metodo = st.selectbox("Método de Pagamento", methods)
            cartao = st.selectbox("Cartão de Crédito (se aplicável)", lista_cartoes)
            data = st.date_input("Data", datetime.today())
            status = st.selectbox("Status", ["Pago", "Pendente"])
            parcelas = st.number_input("Parcelas", min_value=1, max_value=48, value=1)
            
        submitted = st.form_submit_button("Adicionar Despesa")
        if submitted:
            if descricao:
                conn = sqlite3.connect(DB_NAME)
                cursor = conn.cursor()
                if parcelas > 1:
                    v_parc = valor / parcelas
                    for i in range(1, parcelas + 1):
                        d_p = datetime.strptime(str(data), "%Y-%m-%d") + relativedelta(months=i-1)
                        p_info = f"{i}/{parcelas}"
                        cursor.execute('''
                            INSERT INTO transactions (tipo, descricao, valor, data, categoria, metodo, cartao, status, parcela_info)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', ("Despesa", f"{descricao} ({p_info})", v_parc, d_p.strftime("%Y-%m-%d"), categoria, metodo, cartao, status, p_info))
                else:
                    cursor.execute('''
                        INSERT INTO transactions (tipo, descricao, valor, data, categoria, metodo, cartao, status, parcela_info)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', ("Despesa", descricao, valor, str(data), categoria, metodo, cartao, status, "1/1"))
                conn.commit()
                conn.close()
                st.success("Despesa adicionada com sucesso!")
                st.rerun()
            else:
                st.error("Preencha a descrição.")

    st.divider()
    st.subheader("Histórico de Despesas")
    if not df_tx.empty:
        df_desp = df_tx[df_tx['tipo'] == 'Despesa']
        if not df_desp.empty:
            st.dataframe(df_desp, use_container_width=True)
            tx_id = st.selectbox("ID para excluir despesa", options=df_desp['id'].tolist(), key="del_desp")
            if st.button("Excluir Despesa"):
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
                conn.commit()
                conn.close()
                st.success("Excluído com sucesso!")
                st.rerun()
        else:
            st.info("Nenhuma despesa registrada.")

# ================= 4. CONTAS FUTURAS =================
elif menu == "Contas Futuras":
    st.title("⏳ Contas Futuras que Vão Vencer")
    
    if not df_tx.empty:
        hoje = str(date.today())
        df_futuras = df_tx[(df_tx['status'] == 'Pendente') & (df_tx['data'] >= hoje)]
        
        if not df_futuras.empty:
            st.warning("Aqui estão suas próximas contas pendentes:")
            st.dataframe(df_futuras, use_container_width=True)
            
            pago_id = st.selectbox("Marcar ID como 'Pago'", options=df_futuras['id'].tolist())
            if st.button("Confirmar Pagamento"):
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("UPDATE transactions SET status = 'Pago' WHERE id = ?", (pago_id,))
                conn.commit()
                conn.close()
                st.success("Conta marcada como Paga!")
                st.rerun()
        else:
            st.success("Nenhuma conta pendente para os próximos dias! 🟢")
    else:
        st.info("Sem transações cadastradas.")

# ================= 5. CARTÕES DE CRÉDITO =================
elif menu == "Cartões de Crédito":
    st.title("💳 Gerenciamento de Cartões de Crédito")
    
    with st.form("form_cartao"):
        col1, col2, col3 = st.columns(3)
        with col1:
            nome_cartao = st.text_input("Nome do Cartão (ex: Nubank, Visa)")
        with col2:
            limite = st.number_input("Limite Total (R$)", min_value=0.0, format="%.2f")
        with col3:
            vencimento = st.number_input("Dia do Vencimento", min_value=1, max_value=31, value=10)
            
        btn_add_card = st.form_submit_button("Cadastrar Cartão")
        if btn_add_card:
            if nome_cartao:
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("INSERT INTO credit_cards (nome, limite, vencimento) VALUES (?, ?, ?)", (nome_cartao, limite, int(vencimento)))
                conn.commit()
                conn.close()
                st.success("Cartão cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Informe o nome do cartão.")
                
    st.divider()
    st.subheader("Seus Cartões, Limites e Vencimentos")
    
    if not df_cards.empty:
        cards_info = []
        for _, card in df_cards.iterrows():
            c_nome = card['nome']
            c_limite = card['limite']
            c_venc = card['vencimento']
            
            # Calcular uso atual do cartão
            usado = 0.0
            if not df_tx.empty:
                gasto_cartao = df_tx[(df_tx['cartao'] == c_nome) & (df_tx['tipo'] == 'Despesa') & (df_tx['status'] == 'Pago')]
                usado = gasto_cartao['valor'].sum()
                
            restante = c_limite - usado
            cards_info.append({
                "ID": card['id'],
                "Cartão": c_nome,
                "Vencimento (Dia)": c_venc,
                "Limite Total": f"R$ {c_limite:,.2f}",
                "Usado": f"R$ {usado:,.2f}",
                "Restante": f"R$ {restante:,.2f}"
            })
            
        st.dataframe(pd.DataFrame(cards_info), use_container_width=True)
        
        card_del = st.selectbox("Selecione o ID do cartão para excluir", options=df_cards['id'].tolist())
        if st.button("Excluir Cartão"):
            conn = sqlite3.connect(DB_NAME)
            conn.cursor().execute("DELETE FROM credit_cards WHERE id = ?", (card_del,))
            conn.commit()
            conn.close()
            st.success("Cartão excluído!")
            st.rerun()
    else:
        st.info("Nenhum cartão cadastrado.")

# ================= 6. PLANEJAMENTO MENSAL =================
elif menu == "Planejamento Mensal":
    st.title("📋 Planejamento Orçamentário")
    
    cats = get_expense_categories()
    
    with st.form("form_planejamento"):
        cat_escolhida = st.selectbox("Categoria", cats)
        valor_orcado = st.number_input("Valor Orçado Máximo (R$)", min_value=0.0, format="%.2f")
        btn_orc = st.form_submit_button("Salvar Orçamento")
        if btn_orc:
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM planning WHERE categoria = ?", (cat_escolhida,))
            cursor.execute("INSERT INTO planning (categoria, orcado) VALUES (?, ?)", (cat_escolhida, valor_orcado))
            conn.commit()
            conn.close()
            st.success("Orçamento salvo!")
            st.rerun()
            
    st.divider()
    conn = sqlite3.connect(DB_NAME)
    df_plan = pd.read_sql_query("SELECT * FROM planning", conn)
    conn.close()
    
    if not df_plan.empty:
        st.subheader("Acompanhamento de Gastos vs Orçamento")
        for _, row in df_plan.iterrows():
            cat = row['categoria']
            orc = row['orcado']
            gasto_atual = df_tx[(df_tx['categoria'] == cat) & (df_tx['tipo'] == 'Despesa')]['valor'].sum() if not df_tx.empty else 0
            
            st.write(f"**{cat}** (Orçado: R$ {orc:,.2f} | Gasto: R$ {gasto_atual:,.2f})")
            prog = min(gasto_atual / orc if orc > 0 else 0, 1.0)
            st.progress(prog)
    else:
        st.info("Nenhum orçamento planejado ainda.")

# ================= 7. SIMULAÇÃO =================
elif menu == "Simulação":
    st.title("🔮 Simulação Financeira")
    st.write("Simule o impacto de guardar dinheiro ou de novas receitas/despesas.")
    
    col1, col2 = st.columns(2)
    with col1:
        meses = st.slider("Meses de Planejamento", 1, 60, 12)
        poupanca_mensal = st.number_input("Quanto pretende guardar por mês? (R$)", min_value=0.0, value=500.0, format="%.2f")
    with col2:
        taxa_juros = st.number_input("Rendimento Anual Estimado (%)", min_value=0.0, value=8.0)
        
    if st.button("Simular Crescimento"):
        total_acumulado = 0
        taxa_mensal = (taxa_juros / 100) / 12
        for _ in range(meses):
            total_acumulado = (total_acumulado + poupanca_mensal) * (1 + taxa_mensal)
            
        st.success(f"Em {meses} meses, guardando R$ {poupanca_mensal:,.2f}/mês a {taxa_juros}% ao ano, você acumulará aproximadamente:")
        st.metric("Montante Esperado", f"R$ {total_acumulado:,.2f}")

# ================= 8. INSIGHTS =================
elif menu == "Insights":
    st.title("🧠 Insights de Saúde Financeira")
    
    if df_tx.empty:
        st.info("Adicione transações para gerar insights.")
    else:
        receitas_totais = user_renda + df_tx[(df_tx['tipo'] == 'Receita') & (df_tx['status'] == 'Pago')]['valor'].sum()
        despesas_totais = df_tx[(df_tx['tipo'] == 'Despesa') & (df_tx['status'] == 'Pago')]['valor'].sum()
        
        if receitas_totais > 0:
            comp = (despesas_totais / receitas_totais) * 100
            st.write(f"- Você está comprometendo **{comp:.1f}%** da sua renda com despesas.")
            if comp > 80:
                st.error("Alerta Vermelho 🔴: Seus gastos estão muito altos em relação à sua renda.")
            elif comp > 50:
                st.warning("Alerta Amarelo 🟡: Cuidado para não comprometer sua margem de economia.")
            else:
                st.success("Excelente 🟢: Sua taxa de gastos está controlada!")
        else:
            st.warning("Cadastre sua renda na aba 'Configuração' para análises mais precisas.")

# ================= 9. CONFIGURAÇÃO =================
elif menu == "Configuração":
    st.title("⚙️ Configurações do Sistema")
    
    with st.form("form_config"):
        st.subheader("Perfil e Renda")
        novo_nome = st.text_input("Seu Nome", value=user_nome)
        nova_renda = st.number_input("Renda Mensal Fixa (R$)", min_value=0.0, value=float(user_renda), format="%.2f")
        novo_tema = st.selectbox("Tema do Aplicativo", ["Escuro", "Claro"], index=0 if user_tema=="Escuro" else 1)
        
        btn_conf = st.form_submit_button("Salvar Configurações")
        if btn_conf:
            update_user_profile(novo_nome, nova_renda, novo_tema)
            st.success("Configurações salvas com sucesso!")
            st.rerun()
            
    st.divider()
    col_c1, col_c2 = st.columns(2)
    
    with col_c1:
        st.subheader("Cadastrar Nova Categoria de Despesa")
        nova_cat = st.text_input("Nome da Categoria")
        if st.button("Adicionar Categoria"):
            if nova_cat:
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("INSERT INTO expense_categories (nome) VALUES (?)", (nova_cat,))
                conn.commit()
                conn.close()
                st.success("Categoria adicionada!")
                st.rerun()
                
    with col_c2:
        st.subheader("Cadastrar Novo Método de Pagamento")
        novo_metodo = st.text_input("Nome do Método (ex: Pix, Cartão X)")
        if st.button("Adicionar Método"):
            if novo_metodo:
                conn = sqlite3.connect(DB_NAME)
                conn.cursor().execute("INSERT INTO payment_methods (nome) VALUES (?)", (novo_metodo,))
                conn.commit()
                conn.close()
                st.success("Método adicionado!")
                st.rerun()