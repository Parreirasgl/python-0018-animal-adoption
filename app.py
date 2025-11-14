import streamlit as st
import sqlite3
import pandas as pd

# --- Configuração do Banco de Dados ---
DB_NAME = "adocoes.db"

# --- Mapeamentos One-Hot Consistentes ---
TAMANHO_MAP = {
    'pequeno': '100',
    'médio': '010',
    'grande': '001'
}
MORADIA_MAP = {
    'casa': '10',
    'apartamento': '01'
}

# Opções para os formulários
TAMANHO_OPTIONS = list(TAMANHO_MAP.keys())
MORADIA_OPTIONS = list(MORADIA_MAP.keys())

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados e cria as tabelas se não existirem."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tabela de Adotantes (COM NOVAS COLUNAS DE PESO)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS adotantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        tamanho TEXT NOT NULL,
        codigo_tamanho TEXT NOT NULL,
        moradia TEXT NOT NULL,
        codigo_moradia TEXT NOT NULL,
        peso_tamanho TEXT NOT NULL,
        peso_moradia TEXT NOT NULL
    );
    ''')
    
    # Tabela de Animais (INALTERADA)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS animais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        tamanho TEXT NOT NULL,
        codigo_tamanho TEXT NOT NULL,
        moradia TEXT NOT NULL,
        codigo_moradia TEXT NOT NULL
    );
    ''')
    
    conn.commit()
    conn.close()

# --- Funções CRUD (Create, Read, Update, Delete) ---

def add_data(table_name, nome, tamanho, moradia, peso_tamanho=None, peso_moradia=None):
    """Adiciona um novo registro ao banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        codigo_tamanho = TAMANHO_MAP[tamanho]
        codigo_moradia = MORADIA_MAP[moradia]
        
        if table_name == 'adotantes':
            # Processa os pesos para o formato de string repetida
            peso_tamanho_str = str(peso_tamanho) * len(codigo_tamanho)
            peso_moradia_str = str(peso_moradia) * len(codigo_moradia)
            
            query = f"INSERT INTO {table_name} (nome, tamanho, codigo_tamanho, moradia, codigo_moradia, peso_tamanho, peso_moradia) VALUES (?, ?, ?, ?, ?, ?, ?)"
            params = (nome, tamanho, codigo_tamanho, moradia, codigo_moradia, peso_tamanho_str, peso_moradia_str)
        
        else: # 'animais'
            query = f"INSERT INTO {table_name} (nome, tamanho, codigo_tamanho, moradia, codigo_moradia) VALUES (?, ?, ?, ?, ?)"
            params = (nome, tamanho, codigo_tamanho, moradia, codigo_moradia)

        cursor.execute(query, params)
        conn.commit()
        st.success(f"Registro '{nome}' adicionado com sucesso à tabela '{table_name}'!")
    
    except sqlite3.IntegrityError:
        st.error(f"Erro: O nome '{nome}' já existe na tabela '{table_name}'.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
    finally:
        conn.close()

def get_all_data(table_name):
    """Busca todos os registros de uma tabela e retorna como DataFrame."""
    conn = get_db_connection()
    try:
        # Verifica se a tabela 'adotantes' já tem as colunas de peso
        if table_name == 'adotantes':
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(adotantes)")
            columns = [col['name'] for col in cursor.fetchall()]
            if 'peso_tamanho' not in columns or 'peso_moradia' not in columns:
                # Se não tiver, adiciona (migração simples)
                st.warning("Atualizando esquema do banco de dados para adotantes...")
                try:
                    cursor.execute("ALTER TABLE adotantes ADD COLUMN peso_tamanho TEXT DEFAULT '555'")
                    cursor.execute("ALTER TABLE adotantes ADD COLUMN peso_moradia TEXT DEFAULT '55'")
                    conn.commit()
                    st.info("Esquema atualizado. Registros antigos têm peso '5' por padrão.")
                except sqlite3.OperationalError as e:
                    # Ignora se a coluna já existe (acontece em concorrência)
                    if "duplicate column name" not in str(e):
                        raise e

        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        return df
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def find_data_by_name(table_name, nome):
    """Encontra um registro específico pelo nome."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE nome = ?", (nome,))
    data = cursor.fetchone()
    conn.close()
    return data 

def update_data(table_name, id, nome, tamanho, moradia, peso_tamanho=None, peso_moradia=None):
    """Atualiza um registro existente no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        codigo_tamanho = TAMANHO_MAP[tamanho]
        codigo_moradia = MORADIA_MAP[moradia]
        
        if table_name == 'adotantes':
            # Processa os pesos
            peso_tamanho_str = str(peso_tamanho) * len(codigo_tamanho)
            peso_moradia_str = str(peso_moradia) * len(codigo_moradia)
            
            query = f"UPDATE {table_name} SET nome = ?, tamanho = ?, codigo_tamanho = ?, moradia = ?, codigo_moradia = ?, peso_tamanho = ?, peso_moradia = ? WHERE id = ?"
            params = (nome, tamanho, codigo_tamanho, moradia, codigo_moradia, peso_tamanho_str, peso_moradia_str, id)
        
        else: # 'animais'
            query = f"UPDATE {table_name} SET nome = ?, tamanho = ?, codigo_tamanho = ?, moradia = ?, codigo_moradia = ? WHERE id = ?"
            params = (nome, tamanho, codigo_tamanho, moradia, codigo_moradia, id)
        
        cursor.execute(query, params)
        conn.commit()
        st.success(f"Registro '{nome}' (ID: {id}) atualizado com sucesso!")
        
    except sqlite3.IntegrityError:
         st.error(f"Erro: O nome '{nome}' já existe na tabela '{table_name}'.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao atualizar: {e}")
    finally:
        conn.close()

# --- Definições das Páginas ---

def page_ver_tabela(table_name, title):
    """Página para visualizar o conteúdo de uma tabela."""
    st.title(title)
    df = get_all_data(table_name)
    if df.empty:
        st.info("A tabela está vazia.")
    else:
        st.dataframe(df)

def page_formulario(table_name, title, q_nome, q_tamanho, q_moradia):
    """Página de formulário para adicionar novos registros."""
    st.title(title)
    
    with st.form(key=f"form_{table_name}"):
        st.subheader("Por favor, preencha os dados:")
        
        nome = st.text_input(q_nome)
        
        # --- Tamanho ---
        tamanho = st.selectbox(q_tamanho, options=TAMANHO_OPTIONS)
        # SÓ MOSTRA SLIDER PARA ADOTANTES
        if table_name == 'adotantes':
            peso_tamanho = st.slider(f"Qual o peso (0-10) para: '{q_tamanho}'?", 0, 10, 5)
        
        # --- Moradia ---
        moradia = st.selectbox(q_moradia, options=MORADIA_OPTIONS)
        # SÓ MOSTRA SLIDER PARA ADOTANTES
        if table_name == 'adotantes':
            peso_moradia = st.slider(f"Qual o peso (0-10) para: '{q_moradia}'?", 0, 10, 5)

        
        submitted = st.form_submit_button("Enviar")
        
        if submitted:
            if not nome:
                st.warning("O campo 'nome' é obrigatório.")
            else:
                if table_name == 'adotantes':
                    add_data(table_name, nome, tamanho, moradia, peso_tamanho, peso_moradia)
                else: # 'animais'
                    add_data(table_name, nome, tamanho, moradia)

def page_editar_dados(table_name, title):
    """Página para editar registros existentes."""
    st.title(title)
    
    search_name = st.text_input(f"Digite o nome ({table_name}) para buscar e editar:", key=f"search_{table_name}")
    
    if not search_name:
        st.info("Digite um nome para iniciar a busca.")
        return

    data = find_data_by_name(table_name, search_name)
    
    # Define chaves únicas para o session_state
    id_key = f"edit_id_{table_name}"
    nome_key = f"edit_nome_{table_name}"
    tamanho_key = f"edit_tamanho_{table_name}"
    moradia_key = f"edit_moradia_{table_name}"
    
    # Novas chaves para pesos (só para adotantes)
    peso_tamanho_key = f"edit_peso_tamanho_{table_name}"
    # --- CORREÇÃO APLICADA AQUI ---
    peso_moradia_key = f"edit_peso_moradia_{table_name}"


    if data:
        # Se for uma nova busca (ou a primeira), carrega os dados no session_state
        if id_key not in st.session_state or st.session_state[id_key] != data['id']:
            st.session_state[id_key] = data['id']
            st.session_state[nome_key] = data['nome']
            st.session_state[tamanho_key] = data['tamanho']
            st.session_state[moradia_key] = data['moradia']
            
            # Carrega os pesos SÓ SE for adotante
            if table_name == 'adotantes':
                # Decodifica o peso: '888' -> 8, '55' -> 5
                st.session_state[peso_tamanho_key] = int(data['peso_tamanho'][0]) 
                st.session_state[peso_moradia_key] = int(data['peso_moradia'][0])

            st.rerun()

        st.info(f"Editando dados de: {st.session_state[nome_key]} (ID: {st.session_state[id_key]})")
        
        with st.form(key=f"edit_form_{table_name}"):
            st.subheader("Atualize os campos necessários:")
            
            try:
                tamanho_index = TAMANHO_OPTIONS.index(st.session_state[tamanho_key])
            except ValueError:
                tamanho_index = 0 
            try:
                moradia_index = MORADIA_OPTIONS.index(st.session_state[moradia_key])
            except ValueError:
                moradia_index = 0

            # Widgets bindeados ao session_state
            nome = st.text_input("Nome", key=nome_key)
            
            # --- Tamanho ---
            tamanho = st.selectbox("Tamanho", options=TAMANHO_OPTIONS, index=tamanho_index, key=tamanho_key)
            if table_name == 'adotantes':
                peso_tamanho = st.slider("Peso Tamanho", 0, 10, key=peso_tamanho_key)
            
            # --- Moradia ---
            moradia = st.selectbox("Moradia", options=MORADIA_OPTIONS, index=moradia_index, key=moradia_key)
            if table_name == 'adotantes':
                peso_moradia = st.slider("Peso Moradia", 0, 10, key=peso_moradia_key)


            st.markdown("---")
            st.subheader("Campos automáticos (não editáveis)")
            
            st.text_input("Código Tamanho (auto)", 
                           value=TAMANHO_MAP.get(st.session_state[tamanho_key], "Inválido"), 
                           disabled=True)
            st.text_input("Código Moradia (auto)", 
                           value=MORADIA_MAP.get(st.session_state[moradia_key], "Inválido"), 
                           disabled=True)

            submitted = st.form_submit_button("Atualizar")

            if submitted:
                # Na submissão, lê os valores do session_state
                if table_name == 'adotantes':
                    update_data(
                        table_name,
                        st.session_state[id_key],
                        st.session_state[nome_key],
                        st.session_state[tamanho_key],
                        st.session_state[moradia_key],
                        st.session_state[peso_tamanho_key], # Passa o peso
                        st.session_state[peso_moradia_key]  # Passa o peso
                    )
                else: # 'animais'
                     update_data(
                        table_name,
                        st.session_state[id_key],
                        st.session_state[nome_key],
                        st.session_state[tamanho_key],
                        st.session_state[moradia_key]
                    )

                # Limpa o state após a atualização
                keys_to_clear = [id_key, nome_key, tamanho_key, moradia_key, 
                                 peso_tamanho_key, peso_moradia_key]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.query_params.clear()
                st.rerun()

    else:
        st.warning(f"Nenhum registro encontrado com o nome: '{search_name}'")
        # Limpa o state se o nome não for encontrado
        keys_to_clear = [id_key, nome_key, tamanho_key, moradia_key, 
                         peso_tamanho_key, peso_moradia_key]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# --- Execução Principal da Aplicação ---

# Inicializa o DB (e faz a migração se necessário)
init_db()

st.sidebar.title("Navegação da Aplicação")
st.sidebar.info("Sistema de Gerenciamento de Adoções")

paginas = {
    "Ver tabela de adotantes": "page_ver_adotantes",
    "Ver tabela de animais": "page_ver_animais",
    "Formulário do adotante": "page_form_adotante",
    "Formulário do animal": "page_form_animal",
    "Editar dados do adotante": "page_edit_adotante",
    "Editar dados do animal": "page_edit_animal"
}

escolha = st.sidebar.radio("Escolha uma página:", list(paginas.keys()))

# Roteamento
if escolha == "Ver tabela de adotantes":
    page_ver_tabela("adotantes", "Ver Tabela de Adotantes")

elif escolha == "Ver tabela de animais":
    page_ver_tabela("animais", "Ver Tabela de Animais")

elif escolha == "Formulário do adotante":
    page_formulario(
        "adotantes", 
        "Formulário do Adotante",
        q_nome="Qual o seu nome?",
        q_tamanho="Qual o tamanho do animal desejado?",
        q_moradia="Em que tipo de moradia você habita?"
    )

elif escolha == "Formulário do animal":
    page_formulario(
        "animais",
        "Formulário do Animal",
        q_nome="Qual o nome do animal?",
        q_tamanho="Qual o tamanho do animal?",
        q_moradia="Qual a moradia ideal para o animal?"
    )

elif escolha == "Editar dados do adotante":
    page_editar_dados("adotantes", "Editar Dados do Adotante")

elif escolha == "Editar dados do animal":
    page_editar_dados("animais", "Editar Dados do Animal")