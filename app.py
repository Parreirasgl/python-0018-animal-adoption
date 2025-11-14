import streamlit as st
import sqlite3
import pandas as pd
import math

# --- Configuração do Banco de Dados ---
DB_NAME = "adocoes.db"

# --- Mapeamentos ---

# Característica 'tipo' é um FILTRO, não entra no score.
TIPO_OPTIONS = ['cão', 'gato']

# Dicionário mestre das 10 CARACTERÍSTICAS que entram no score.
CARACTERISTICAS = {
    'tamanho': {
        'map': {'pequeno': '100', 'médio': '010', 'grande': '001'},
        'q_adotante': 'Que tamanho de animal você prefere?',
        'q_animal': 'Porte do animal:'
    },
    'moradia': {
        'map': {'casa': '10', 'apartamento': '01'},
        'q_adotante': 'Qual tipo da sua moradia?',
        'q_animal': 'Moradia ideal:'
    },
    'pelo': {
        'map': {'longos': '10', 'curtos': '01'},
        'q_adotante': 'Que tipo de pelo você prefere?',
        'q_animal': 'Pelagem:'
    },
    'sexo': {
        'map': {'macho': '10', 'fêmea': '01'},
        'q_adotante': 'Você prefere animal macho ou fêmea?',
        'q_animal': 'Sexo:'
    },
    'queda': {
        'map': {'sim': '10', 'não': '01'},
        'q_adotante': 'Queda de pelo te incomoda? (sim=incomoda, não=ok)',
        'q_animal': 'Apresenta queda de pelo:'
    },
    'crianca': {
        'map': {'sim': '10', 'não': '01'},
        'q_adotante': 'O animal deve ser amigável com criança?',
        'q_animal': 'Amigável com criança:'
    },
    'brincalhao': {
        'map': {'sim': '10', 'não': '01'},
        'q_adotante': 'O animal deve ser brincalhão?',
        'q_animal': 'Brincalhão:'
    },
    'ativo': {
        'map': {'sim': '10', 'não': '01'},
        'q_adotante': 'O animal deve ter muita disposição?',
        'q_animal': 'Muito ativo:'
    },
    'guarda': {
        'map': {'sim': '10', 'não': '01'},
        'q_adotante': 'O animal precisa servir para guarda?',
        'q_animal': 'Serve para guarda:'
    },
    'late': {
        'map': {'sim': '10', 'não': '01'},
        'q_adotante': 'É positivo o animal latir?',
        'q_animal': 'Tende a latir:'
    }
}

# Gera listas de opções a partir dos mapas
for k in CARACTERISTICAS:
    CARACTERISTICAS[k]['options'] = list(CARACTERISTICAS[k]['map'].keys())

# Nomes das colunas no DB (baseado nas 10 características)
COLUNAS_FEATURES = list(CARACTERISTICAS.keys())
COLUNAS_CODIGO = [f"codigo_{k}" for k in COLUNAS_FEATURES]
COLUNAS_PESO = [f"peso_{k}" for k in COLUNAS_FEATURES]

# Colunas totais para cada tabela (adicionando 'tipo' manualmente)
COLUNAS_ANIMAIS = ['id', 'nome', 'tipo'] + COLUNAS_FEATURES + COLUNAS_CODIGO
COLUNAS_ADOTANTES = ['id', 'nome', 'contato', 'tipo'] + COLUNAS_FEATURES + COLUNAS_CODIGO + COLUNAS_PESO

# Colunas necessárias para CSV (sem ID)
CSV_COLS_ANIMAIS = [col for col in COLUNAS_ANIMAIS if col != 'id']
CSV_COLS_ADOTANTES = [col for col in COLUNAS_ADOTANTES if col != 'id']


def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Inicializa o banco de dados e executa a migração, adicionando colunas
    que não existem sem apagar dados.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- Tabela Adotantes ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS adotantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    );
    ''')
    
    # Pega colunas existentes
    cursor.execute("PRAGMA table_info(adotantes)")
    existing_cols_adotantes = [col['name'] for col in cursor.fetchall()]

    # Define colunas necessárias (Nome já existe)
    # Adiciona 'contato' e 'tipo' manualmente
    required_cols_adotantes = {
        "contato": "TEXT",
        "tipo": "TEXT DEFAULT 'cão'" # Valor padrão 'cão'
    }
    
    # Adiciona as 10 features, códigos e pesos
    for feature in COLUNAS_FEATURES:
        map = CARACTERISTICAS[feature]['map']
        default_peso = str(5) * len(list(map.values())[0]) 
        
        required_cols_adotantes[feature] = "TEXT"
        required_cols_adotantes[f"codigo_{feature}"] = "TEXT"
        required_cols_adotantes[f"peso_{feature}"] = f"TEXT DEFAULT '{default_peso}'"

    # Adiciona colunas faltantes para Adotantes
    for col, type in required_cols_adotantes.items():
        if col not in existing_cols_adotantes:
            try:
                cursor.execute(f"ALTER TABLE adotantes ADD COLUMN {col} {type}")
                st.info(f"Coluna '{col}' adicionada à tabela 'adotantes'.")
            except sqlite3.OperationalError as e:
                st.warning(f"Não foi possível adicionar coluna {col}: {e}")

    # --- Tabela Animais ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS animais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE
    );
    ''')

    # Pega colunas existentes
    cursor.execute("PRAGMA table_info(animais)")
    existing_cols_animais = [col['name'] for col in cursor.fetchall()]

    # Define colunas necessárias (Nome já existe)
    # Adiciona 'tipo' manualmente
    required_cols_animais = {
        "tipo": "TEXT DEFAULT 'cão'" # Valor padrão 'cão'
    }
    # Adiciona as 10 features e códigos
    for feature in COLUNAS_FEATURES:
        required_cols_animais[feature] = "TEXT"
        required_cols_animais[f"codigo_{feature}"] = "TEXT"

    # Adiciona colunas faltantes para Animais
    for col, type in required_cols_animais.items():
        if col not in existing_cols_animais:
            try:
                cursor.execute(f"ALTER TABLE animais ADD COLUMN {col} {type}")
                st.info(f"Coluna '{col}' adicionada à tabela 'animais'.")
            except sqlite3.OperationalError as e:
                st.warning(f"Não foi possível adicionar coluna {col}: {e}")
    
    conn.commit()
    conn.close()

# --- Funções CRUD (Create, Read, Update, Delete) ---

def add_data(table_name, data):
    """Adiciona um novo registro ao banco de dados usando um dicionário de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cols = []
        params = []
        
        # Adiciona nome e tipo (ambas as tabelas)
        cols.append('nome')
        params.append(data['nome'])
        cols.append('tipo')
        params.append(data['tipo'])
        
        # Adiciona contato (só adotantes)
        if table_name == 'adotantes':
            cols.append('contato')
            params.append(data['contato'])

        # Processa as 10 características do score
        for feature in COLUNAS_FEATURES:
            valor = data[feature]
            codigo = CARACTERISTICAS[feature]['map'][valor]
            
            cols.append(feature)
            cols.append(f"codigo_{feature}")
            params.append(valor)
            params.append(codigo)
            
            # Adiciona pesos se for adotante
            if table_name == 'adotantes':
                peso = data[f"peso_{feature}"]
                peso_str = str(peso) * len(codigo) # ex: 8 * '100' -> '888'
                
                cols.append(f"peso_{feature}")
                params.append(peso_str)

        # Constrói a query
        cols_str = ", ".join(cols)
        placeholders = ", ".join(["?"] * len(params))
        query = f"INSERT INTO {table_name} ({cols_str}) VALUES ({placeholders})"

        cursor.execute(query, params)
        
        new_id = cursor.lastrowid
        conn.commit()
        st.success(f"Registro '{data['nome']}' (ID: {new_id}) adicionado com sucesso à tabela '{table_name}'!")
    
    except sqlite3.IntegrityError:
        st.error(f"Erro: O nome '{data['nome']}' já existe na tabela '{table_name}'.")
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")
    finally:
        conn.close()

def get_all_data(table_name):
    """Busca todos os registros de uma tabela e retorna como DataFrame."""
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        # Garante a ordem correta das colunas
        if table_name == 'animais':
            df = df.reindex(columns=COLUNAS_ANIMAIS, fill_value=None)
        elif table_name == 'adotantes':
            df = df.reindex(columns=COLUNAS_ADOTANTES, fill_value=None)
            
        return df
    except Exception as e:
        st.error(f"Erro ao ler dados: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def find_data_by_name(table_name, nome):
    """Encontra um registro específico pelo nome (usado na pág. compatibilidade)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE nome = ?", (nome,))
    data = cursor.fetchone()
    conn.close()
    return data 

def find_data_by_id(table_name, id):
    """Encontra um registro específico pelo ID (usado na pág. editar)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (id,))
    data = cursor.fetchone()
    conn.close()
    return data

def update_data(table_name, id, data):
    """Atualiza um registro existente no banco de dados."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        set_parts = []
        params = []

        # Adiciona nome e tipo (ambas as tabelas)
        set_parts.append('nome = ?')
        params.append(data['nome'])
        set_parts.append('tipo = ?')
        params.append(data['tipo'])
        
        # Adiciona contato (só adotantes)
        if table_name == 'adotantes':
            set_parts.append('contato = ?')
            params.append(data['contato'])

        # Processa as 10 características do score
        for feature in COLUNAS_FEATURES:
            valor = data[feature]
            codigo = CARACTERISTICAS[feature]['map'][valor]
            
            set_parts.append(f"{feature} = ?")
            set_parts.append(f"codigo_{feature} = ?")
            params.append(valor)
            params.append(codigo)
            
            # Adiciona pesos se for adotante
            if table_name == 'adotantes':
                peso = data[f"peso_{feature}"]
                peso_str = str(peso) * len(codigo) # ex: 8 * '100' -> '888'
                
                set_parts.append(f"peso_{feature} = ?")
                params.append(peso_str)
        
        # Adiciona o ID no final para o WHERE
        params.append(id)
        
        # Constrói a query
        set_str = ", ".join(set_parts)
        query = f"UPDATE {table_name} SET {set_str} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        st.success(f"Registro '{data['nome']}' (ID: {id}) atualizado com sucesso!")
        
    except sqlite3.IntegrityError:
         st.error(f"Erro: O nome '{data['nome']}' já existe na tabela '{table_name}'.")
    except Exception as e:
        st.error(f"Ocorreu um erro ao atualizar: {e}")
    finally:
        conn.close()

def replace_table_from_csv(table_name, uploaded_file):
    """
    Apaga todos os dados de uma tabela e os substitui por um CSV.
    Retorna (True, 'mensagem de sucesso') ou (False, 'mensagem de erro').
    """
    
    if table_name == 'animais':
        required_cols = CSV_COLS_ANIMAIS
    elif table_name == 'adotantes':
        required_cols = CSV_COLS_ADOTANTES
    else:
        return (False, f"Tabela '{table_name}' desconhecida.")

    try:
        df = pd.read_csv(uploaded_file, dtype=str) # Lê tudo como string
        
        if not all(col in df.columns for col in required_cols):
            missing_cols = set(required_cols) - set(df.columns)
            message = f"Erro: O CSV não contém todas as colunas necessárias. Faltando: {missing_cols}"
            st.info(f"Colunas necessárias: {required_cols}")
            st.info(f"Colunas encontradas: {list(df.columns)}")
            return (False, message)
            
        df_to_insert = df[required_cols]

        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(f"DELETE FROM {table_name}")
            df_to_insert.to_sql(table_name, conn, if_exists='append', index=False)
            conn.commit()
            message = f"Tabela '{table_name}' substituída com sucesso! {len(df_to_insert)} registros inseridos."
            return (True, message)
            
        except Exception as e:
            conn.rollback() 
            message = f"Falha na transação com o banco de dados: {e}"
            return (False, message)
        finally:
            conn.close()

    except Exception as e:
        message = f"Erro ao ler o arquivo CSV: {e}"
        return (False, message)


# --- Funções de Cálculo de Score ---

def calculate_scores(adotante, animais_filtrados_df):
    """Calcula a similaridade de cosseno ponderada para cada animal."""
    
    scores_list = []
    
    try:
        # 1. Preparar vetores do Adotante (B e P) - SOMENTE 10 FEATURES
        vetor_b_str = ""
        vetor_p_str = ""
        for feature in COLUNAS_FEATURES: # Itera sobre as 10
            vetor_b_str += adotante[f"codigo_{feature}"]
            vetor_p_str += adotante[f"peso_{feature}"]
        
        B = [int(digit) for digit in vetor_b_str]
        P = [int(digit) for digit in vetor_p_str]
        
        # 2. Calcular o Termo 2 do Denominador (lado do Adotante)
        sum_Bi_Pi_sq = 0
        for i in range(len(B)):
            sum_Bi_Pi_sq += (B[i] * P[i])**2
        
        denominador_termo2 = math.sqrt(sum_Bi_Pi_sq)

        # 3. Iterar sobre cada Animal para calcular o score
        for _, animal in animais_filtrados_df.iterrows():
            
            # 3.1 Preparar vetor do Animal (A) - SOMENTE 10 FEATURES
            vetor_a_str = ""
            for feature in COLUNAS_FEATURES: # Itera sobre as 10
                vetor_a_str += animal[f"codigo_{feature}"]
            A = [int(digit) for digit in vetor_a_str]
            
            if len(A) != len(B):
                st.error(f"Incompatibilidade de vetores (A:{len(A)}, B:{len(B)}) entre adotante {adotante['nome']} e animal {animal['nome']}.")
                continue
                
            numerador = 0
            sum_Ai_Pi_sq = 0 
            
            # 3.2 Calcular Numerador e Termo 1 do Denominador
            for i in range(len(A)):
                ai = A[i]
                bi = B[i]
                pi = P[i]
                
                numerador += (ai * bi * pi)
                sum_Ai_Pi_sq += (ai * pi)**2
            
            denominador_termo1 = math.sqrt(sum_Ai_Pi_sq)
            
            # 3.3 Calcular Score Final
            denominador_completo = denominador_termo1 * denominador_termo2
            
            if denominador_completo == 0:
                score = 0.0
            else:
                score = numerador / denominador_completo
                
            scores_list.append({'nome': animal['nome'], 'score': score})

        # 4. Ordenar a lista final
        sorted_scores = sorted(scores_list, key=lambda x: x['score'], reverse=True)
        
        return sorted_scores

    except Exception as e:
        st.error(f"Erro ao calcular scores: {e}")
        st.exception(e)
        return []


# --- Funções de Conversão (para Download) ---

@st.cache_data
def convert_df_to_csv(df):
    """Converte um DataFrame para CSV em memória, pronto para download."""
    if 'contato' in df.columns:
         df = df.reindex(columns=CSV_COLS_ADOTANTES, fill_value=None)
    else:
         df = df.reindex(columns=CSV_COLS_ANIMAIS, fill_value=None)
         
    return df.to_csv(index=False).encode('utf-8')


# --- Definições das Páginas ---

def page_ver_tabela(table_name, title):
    """Página para visualizar o conteúdo de uma tabela."""
    st.title(title)
    df = get_all_data(table_name)
    if df.empty:
        st.info("A tabela está vazia.")
    else:
        st.dataframe(df)

def page_formulario(table_name, title):
    """Página de formulário para adicionar novos registros."""
    st.title(title)
    
    with st.form(key=f"form_{table_name}"):
        st.subheader("Por favor, preencha os dados:")
        
        data = {}
        
        if table_name == 'adotantes':
            data['nome'] = st.text_input("Nome:")
            data['contato'] = st.text_input("Contato (Telefone/Email):")
            data['tipo'] = st.selectbox("Qual tipo de animal mais te interessa?", options=TIPO_OPTIONS, key="form_tipo")
        else: # 'animais'
            data['nome'] = st.text_input("Nome do animal:")
            data['tipo'] = st.selectbox("Tipo de animal:", options=TIPO_OPTIONS, key="form_tipo")

        st.markdown("---")
        st.subheader("Características de Compatibilidade (10)")

        # Gera os widgets para as 10 características do score
        for feature, props in CARACTERISTICAS.items():
            
            if table_name == 'adotantes':
                q = props['q_adotante']
            else:
                q = props['q_animal']
                
            data[feature] = st.selectbox(q, options=props['options'])
            
            if table_name == 'adotantes':
                data[f"peso_{feature}"] = st.slider(f"Peso (0-10) para: '{props['q_adotante']}'", 0, 10, 5, key=f"peso_{feature}")
            
            st.divider()

        
        submitted = st.form_submit_button("Enviar")
        
        if submitted:
            if not data['nome']:
                st.warning("O campo 'nome' é obrigatório.")
            else:
                add_data(table_name, data)

def page_editar_dados(table_name, title):
    """Página para editar registros existentes."""
    st.title(title)
    
    search_id = st.number_input(
        f"Digite o ID ({table_name}) para buscar e editar:",
        min_value=1,
        step=1,
        value=None,
        key=f"search_{table_name}"
    )
    
    if not search_id:
        st.info("Digite um ID para iniciar a busca.")
        return

    db_data = find_data_by_id(table_name, search_id)
    
    id_key = f"edit_id_{table_name}"

    if db_data:
        # Carrega dados no session_state na primeira busca
        if id_key not in st.session_state or st.session_state[id_key] != db_data['id']:
            st.session_state[id_key] = db_data['id']
            st.session_state[f"edit_nome_{table_name}"] = db_data['nome']
            st.session_state[f"edit_tipo_{table_name}"] = db_data['tipo']
            
            if table_name == 'adotantes':
                st.session_state[f"edit_contato_{table_name}"] = db_data['contato']
            
            # Carrega as 10 features e pesos (se adotante)
            for feature in COLUNAS_FEATURES:
                st.session_state[f"edit_{feature}_{table_name}"] = db_data[feature]
                if table_name == 'adotantes':
                    peso_str = db_data[f"peso_{feature}"]
                    st.session_state[f"edit_peso_{feature}_{table_name}"] = int(peso_str[0]) if peso_str else 5

            st.rerun() 

        st.info(f"Editando dados de: {st.session_state[f'edit_nome_{table_name}']} (ID: {st.session_state[id_key]})")
        
        with st.form(key=f"edit_form_{table_name}"):
            st.subheader("Atualize os campos necessários:")
            
            form_data = {}
            
            # --- Campos Principais (Nome, Contato, Tipo) ---
            if table_name == 'adotantes':
                form_data['nome'] = st.text_input("Nome", key=f"edit_nome_{table_name}")
                form_data['contato'] = st.text_input("Contato", key=f"edit_contato_{table_name}")
                
                try:
                    index_tipo = TIPO_OPTIONS.index(st.session_state[f"edit_tipo_{table_name}"])
                except (ValueError, KeyError):
                    index_tipo = 0
                form_data['tipo'] = st.selectbox("Tipo de animal:", options=TIPO_OPTIONS, index=index_tipo, key=f"edit_tipo_{table_name}")
            
            else: # 'animais'
                form_data['nome'] = st.text_input("Nome", key=f"edit_nome_{table_name}")
                
                try:
                    index_tipo = TIPO_OPTIONS.index(st.session_state[f"edit_tipo_{table_name}"])
                except (ValueError, KeyError):
                    index_tipo = 0
                form_data['tipo'] = st.selectbox("Tipo de animal:", options=TIPO_OPTIONS, index=index_tipo, key=f"edit_tipo_{table_name}")


            st.markdown("---")
            st.subheader("Características de Compatibilidade (10)")
            
            auto_codes = {}

            # --- Campos de 10 Características ---
            for feature, props in CARACTERISTICAS.items():
                
                key = f"edit_{feature}_{table_name}"
                if table_name == 'adotantes':
                    q = props['q_adotante']
                else:
                    q = props['q_animal']

                try:
                    index = props['options'].index(st.session_state[key])
                except (ValueError, KeyError):
                    index = 0
                
                form_data[feature] = st.selectbox(q, options=props['options'], index=index, key=key)
                
                if table_name == 'adotantes':
                    peso_key = f"edit_peso_{feature}_{table_name}"
                    form_data[f"peso_{feature}"] = st.slider(f"Peso (0-10) para: '{q}'", 0, 10, key=peso_key)

                auto_codes[feature] = CARACTERISTICAS[feature]['map'].get(st.session_state[key], "Inválido")
                st.divider()


            st.markdown("---")
            st.subheader("Campos automáticos (não editáveis)")
            
            cols_auto = st.columns(3)
            col_index = 0
            for feature, code in auto_codes.items():
                with cols_auto[col_index]:
                    st.text_input(f"Código {feature}", value=code, disabled=True)
                col_index = (col_index + 1) % 3


            submitted = st.form_submit_button("Atualizar")

            if submitted:
                # Lê os valores do session_state para enviar ao update
                data_to_update = {}
                data_to_update['nome'] = st.session_state[f"edit_nome_{table_name}"]
                data_to_update['tipo'] = st.session_state[f"edit_tipo_{table_name}"]
                
                if table_name == 'adotantes':
                    data_to_update['contato'] = st.session_state[f"edit_contato_{table_name}"]

                for feature in COLUNAS_FEATURES:
                    data_to_update[feature] = st.session_state[f"edit_{feature}_{table_name}"]
                    if table_name == 'adotantes':
                         data_to_update[f"peso_{feature}"] = st.session_state[f"edit_peso_{feature}_{table_name}"]

                update_data(
                    table_name,
                    st.session_state[id_key],
                    data_to_update
                )

                # Limpa o state após a atualização
                keys_to_clear = [id_key, f"edit_nome_{table_name}", f"edit_tipo_{table_name}"]
                if table_name == 'adotantes':
                    keys_to_clear.append(f"edit_contato_{table_name}")
                
                for feature in COLUNAS_FEATURES:
                    keys_to_clear.append(f"edit_{feature}_{table_name}")
                    if table_name == 'adotantes':
                        keys_to_clear.append(f"edit_peso_{feature}_{table_name}")

                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                
                st.query_params.clear()
                st.rerun()

    else:
        if search_id:
            st.warning(f"Nenhum registro encontrado com o ID: {search_id}")
            
        keys_to_clear = [id_key, f"edit_nome_{table_name}", f"edit_tipo_{table_name}"]
        if table_name == 'adotantes':
            keys_to_clear.append(f"edit_contato_{table_name}")
        
        for feature in COLUNAS_FEATURES:
            keys_to_clear.append(f"edit_{feature}_{table_name}")
            if table_name == 'adotantes':
                keys_to_clear.append(f"edit_peso_{feature}_{table_name}")

        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# --- PÁGINA DE UPLOAD CSV ---

def page_upload_csv():
    """Página para substituir dados da tabela por um arquivo CSV."""
    st.title("Acrescentar arquivos CSV")

    if "csv_message" in st.session_state:
        message_type, message_text = st.session_state["csv_message"]
        if message_type == "success":
            st.success(message_text)
        elif message_type == "error":
            st.error(message_text)
        del st.session_state["csv_message"]

    st.warning("ATENÇÃO: Fazer o upload de um arquivo aqui apagará TODOS os dados atuais da tabela correspondente e os substituirá pelo conteúdo do CSV.")

    st.markdown("---")
    
    st.subheader("Substituir Tabela de Animais")
    st.info(f"O CSV deve conter as colunas: {', '.join(CSV_COLS_ANIMAIS)}")
    uploader_animais = st.file_uploader("Selecione um CSV para a tabela 'animais'", type="csv", key="uploader_animais")
    
    if uploader_animais:
        if st.button("Confirmar Substituição - ANIMAIS"):
            success, message = replace_table_from_csv("animais", uploader_animais)
            if success:
                st.session_state["csv_message"] = ("success", message)
            else:
                st.session_state["csv_message"] = ("error", message)
            st.rerun()

    st.markdown("---")

    st.subheader("Substituir Tabela de Adotantes")
    st.info(f"O CSV deve conter as colunas: {', '.join(CSV_COLS_ADOTANTES)}")
    uploader_adotantes = st.file_uploader("Selecione um CSV para a tabela 'adotantes'", type="csv", key="uploader_adotantes")
    
    if uploader_adotantes:
         if st.button("Confirmar Substituição - ADOTANTES"):
            success, message = replace_table_from_csv("adotantes", uploader_adotantes)
            if success:
                st.session_state["csv_message"] = ("success", message)
            else:
                st.session_state["csv_message"] = ("error", message)
            st.rerun()


# --- PÁGINA DE DOWNLOAD CSV ---

def page_baixar_csv():
    """Página para baixar as tabelas 'animais' e 'adotantes' como CSV."""
    st.title("Baixar arquivos CSV")

    st.markdown("---")
    st.subheader("Baixar Tabela de Animais")
    df_animais = get_all_data("animais")
    if df_animais.empty:
        st.info("Tabela 'animais' está vazia. Nada para baixar.")
    else:
        csv_animais = convert_df_to_csv(df_animais)
        st.download_button(
            label="Baixar 'animais.csv'",
            data=csv_animais,
            file_name='animais.csv',
            mime='text/csv',
        )

    st.markdown("---")
    st.subheader("Baixar Tabela de Adotantes")
    df_adotantes = get_all_data("adotantes")
    if df_adotantes.empty:
        st.info("Tabela 'adotantes' está vazia. Nada para baixar.")
    else:
        csv_adotantes = convert_df_to_csv(df_adotantes)
        st.download_button(
            label="Baixar 'adotantes.csv'",
            data=csv_adotantes,
            file_name='adotantes.csv',
            mime='text/csv',
        )


# --- PÁGINA DE COMPATIBILIDADE ---

def page_compatibilidade():
    """Página para calcular e exibir animais compatíveis com um adotante."""
    st.title("Animais Compatíveis")
    
    # --- MUDANÇA: Buscar por ID ---
    search_id = st.number_input(
        "Digite o ID do Adotante para buscar compatibilidade:",
        min_value=1,
        step=1,
        value=None
    )
    
    if not search_id:
        st.info("Digite o ID de um adotante cadastrado para ver os animais compatíveis.")
        return

    # 1. Buscar o adotante por ID
    adotante = find_data_by_id("adotantes", search_id)
    
    if not adotante:
        st.error(f"Adotante com ID '{search_id}' não encontrado.")
        return
    
    # -------------------------------------------------------------
    # --- Lógica de FILTRAR ANIMAIS PELO TIPO ---
    # -------------------------------------------------------------
    tipo_preferido = adotante['tipo']
    st.success(f"Calculando compatibilidade para: **{adotante['nome']}** (ID: {adotante['id']})")
    st.info(f"Preferência de animal: **{tipo_preferido.upper()}**. Mostrando apenas animais desse tipo.")

    
    # Exibe as preferências do adotante
    with st.expander("Ver preferências e pesos do Adotante"):
        st.write(f"**Tipo (Filtro): {adotante['tipo']}**")
        st.divider()
        cols = st.columns(3)
        i = 0
        for feature in COLUNAS_FEATURES: # Itera sobre as 10
            with cols[i % 3]:
                st.write(f"**{feature.capitalize()}**: {adotante[feature]}")
                st.caption(f"Peso: {adotante[f'peso_{feature}'][0]}")
            i += 1
            
    # 2. Buscar TODOS os animais e FILTRAR
    all_animais_df = get_all_data("animais")
    if all_animais_df.empty:
        st.warning("Nenhum animal cadastrado no banco de dados.")
        return
        
    # FILTRA o DataFrame
    animais_filtrados_df = all_animais_df[all_animais_df['tipo'] == tipo_preferido].copy()
    
    if animais_filtrados_df.empty:
        st.warning(f"Nenhum animal do tipo '{tipo_preferido}' encontrado no banco de dados.")
        return
        
    # 3. Calcular os scores APENAS para os animais filtrados
    sorted_scores = calculate_scores(adotante, animais_filtrados_df)
    
    if not sorted_scores:
        st.info("Cálculo concluído, mas nenhum score foi gerado.")
        return

    # 4. Aplicar a lógica de exibição (Top 10 + empates)
    resultado_final = []
    
    if len(sorted_scores) <= 10:
        resultado_final = sorted_scores
    else:
        score_do_decimo = sorted_scores[9]['score']
        resultado_final = [s for s in sorted_scores if s['score'] >= score_do_decimo]

    # 5. Exibir os resultados
    st.subheader(f"Lista de {len(resultado_final)} Animais Mais Compatíveis (Tipo: {tipo_preferido}):")
    
    df_resultado = pd.DataFrame(resultado_final)
    df_resultado.index = df_resultado.index + 1
    
    st.dataframe(
        df_resultado.style.format({'score': '{:.4f}'}),
        use_container_width=True
    )


# --- Execução Principal da Aplicação ---

init_db()

st.sidebar.title("Navegação da Aplicação")
st.sidebar.info("Sistema de Gerenciamento de Adoções")

paginas = {
    "Ver tabela de adotantes": "page_ver_adotantes",
    "Ver tabela de animais": "page_ver_animais",
    "Acrescentar arquivos CSV": "page_upload_csv",
    "Baixar arquivos CSV": "page_baixar_csv",
    "Acrescentar um adotante": "page_form_adotante",
    "Acrescentar um animal": "page_form_animal",
    "Editar dados do adotante": "page_edit_adotante",
    "Editar dados do animal": "page_edit_animal",
    "Animais compatíveis": "page_compatibilidade"
}

escolha = st.sidebar.radio("Escolha uma página:", list(paginas.keys()))

if escolha == "Ver tabela de adotantes":
    page_ver_tabela("adotantes", "Ver Tabela de Adotantes")

elif escolha == "Ver tabela de animais":
    page_ver_tabela("animais", "Ver Tabela de Animais")

elif escolha == "Acrescentar arquivos CSV":
    page_upload_csv()

elif escolha == "Baixar arquivos CSV":
    page_baixar_csv()

elif escolha == "Acrescentar um adotante":
    page_formulario("adotantes", "Acrescentar um Adotante")

elif escolha == "Acrescentar um animal":
    page_formulario("animais", "Acrescentar um Animal")

elif escolha == "Editar dados do adotante":
    page_editar_dados("adotantes", "Editar Dados do Adotante")

elif escolha == "Editar dados do animal":
    page_editar_dados("animais", "Editar Dados do Animal")

elif escolha == "Animais compatíveis":
    page_compatibilidade()