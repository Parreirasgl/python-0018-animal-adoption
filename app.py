import streamlit as st
import sqlite3
import pandas as pd
import math  # Importado para a raiz quadrada (sqrt)

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
    
    # Tabela de Adotantes
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
    
    # Tabela de Animais
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
                    # Ignora se a coluna já existe
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

def replace_table_from_csv(table_name, uploaded_file):
    """Apaga todos os dados de uma tabela e os substitui por um CSV."""
    
    # Define as colunas obrigatórias para cada tabela
    if table_name == 'animais':
        required_cols = ['nome', 'tamanho', 'codigo_tamanho', 'moradia', 'codigo_moradia']
    elif table_name == 'adotantes':
        required_cols = ['nome', 'tamanho', 'codigo_tamanho', 'moradia', 'codigo_moradia', 'peso_tamanho', 'peso_moradia']
    else:
        st.error(f"Tabela '{table_name}' desconhecida.")
        return

    try:
        df = pd.read_csv(uploaded_file)
        
        # 1. Validação: Verifica se todas as colunas necessárias existem no CSV
        if not all(col in df.columns for col in required_cols):
            st.error(f"Erro: O CSV não contém todas as colunas necessárias. Faltando: {set(required_cols) - set(df.columns)}")
            st.info(f"Colunas necessárias: {required_cols}")
            st.info(f"Colunas encontradas: {list(df.columns)}")
            return
            
        # 2. Seleciona apenas as colunas necessárias (ignora 'id' ou extras)
        df_to_insert = df[required_cols]

        # 3. Transação: Apaga os dados antigos e insere os novos
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # 3.1 Apaga dados antigos
            cursor.execute(f"DELETE FROM {table_name}")
            st.warning(f"Dados antigos da tabela '{table_name}' apagados.")
            
            # 3.2 Insere dados novos usando a função 'to_sql' do pandas
            df_to_insert.to_sql(table_name, conn, if_exists='append', index=False)
            
            conn.commit()
            st.success(f"Tabela '{table_name}' substituída com sucesso! {len(df_to_insert)} registros inseridos.")
            
        except Exception as e:
            conn.rollback() # Desfaz a operação em caso de erro
            st.error(f"Falha na transação com o banco de dados: {e}")
        finally:
            conn.close()

    except Exception as e:
        st.error(f"Erro ao ler o arquivo CSV: {e}")


# --- Funções de Cálculo de Score ---

def calculate_scores(adotante, animais_df):
    """Calcula a similaridade de cosseno ponderada para cada animal."""
    
    scores_list = []
    
    try:
        # 1. Preparar vetores do Adotante (B e P)
        vetor_b_str = adotante['codigo_tamanho'] + adotante['codigo_moradia']
        vetor_p_str = adotante['peso_tamanho'] + adotante['peso_moradia']
        
        # Converte strings '10010' e '33388' para listas de inteiros
        B = [int(digit) for digit in vetor_b_str]
        P = [int(digit) for digit in vetor_p_str]
        
        # 2. Calcular o Termo 2 do Denominador (lado do Adotante)
        # √Σ(Bi * Pi)²
        sum_Bi_Pi_sq = 0
        for i in range(len(B)):
            sum_Bi_Pi_sq += (B[i] * P[i])**2
        
        denominador_termo2 = math.sqrt(sum_Bi_Pi_sq)

        # 3. Iterar sobre cada Animal para calcular o score
        for _, animal in animais_df.iterrows():
            
            # 3.1 Preparar vetor do Animal (A)
            vetor_a_str = animal['codigo_tamanho'] + animal['codigo_moradia']
            A = [int(digit) for digit in vetor_a_str]
            
            # Garantia de que os vetores têm o mesmo tamanho
            if len(A) != len(B):
                st.error(f"Incompatibilidade de vetores entre adotante {adotante['nome']} e animal {animal['nome']}.")
                continue
                
            numerador = 0
            sum_Ai_Pi_sq = 0 # Para o Termo 1 do Denominador
            
            # 3.2 Calcular Numerador e Termo 1 do Denominador
            # Numerador = Σ(Ai * Bi * Pi)
            # Termo 1 = √Σ(Ai * Pi)²
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
                score = 0.0 # Evita divisão por zero
            else:
                score = numerador / denominador_completo
                
            scores_list.append({'nome': animal['nome'], 'score': score})

        # 4. Ordenar a lista final
        sorted_scores = sorted(scores_list, key=lambda x: x['score'], reverse=True)
        
        return sorted_scores

    except Exception as e:
        st.error(f"Erro ao calcular scores: {e}")
        return []


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

# --- PÁGINA DE UPLOAD CSV (CORRIGIDA) ---

def page_upload_csv():
    """Página para substituir dados da tabela por um arquivo CSV."""
    st.title("Acrescentar arquivos CSV")
    st.warning("ATENÇÃO: Fazer o upload de um arquivo aqui apagará TODOS os dados atuais da tabela correspondente e os substituirá pelo conteúdo do CSV.")

    st.markdown("---")
    
    # Seção para ANIMAIS
    st.subheader("Substituir Tabela de Animais")
    st.info("O CSV deve conter as colunas: nome, tamanho, codigo_tamanho, moradia, codigo_moradia")
    uploader_animais = st.file_uploader("Selecione um CSV para a tabela 'animais'", type="csv", key="uploader_animais")
    
    if uploader_animais:
        # Adiciona um botão de confirmação antes da ação destrutiva
        if st.button("Confirmar Substituição - ANIMAIS"):
            replace_table_from_csv("animais", uploader_animais)
            # --- LINHA REMOVIDA DAQUI ---
            st.rerun()

    st.markdown("---")

    # Seção para ADOTANTES
    st.subheader("Substituir Tabela de Adotantes")
    st.info("O CSV deve conter as colunas: nome, tamanho, codigo_tamanho, moradia, codigo_moradia, peso_tamanho, peso_moradia")
    uploader_adotantes = st.file_uploader("Selecione um CSV para a tabela 'adotantes'", type="csv", key="uploader_adotantes")
    
    if uploader_adotantes:
         # Adiciona um botão de confirmação
        if st.button("Confirmar Substituição - ADOTANTES"):
            replace_table_from_csv("adotantes", uploader_adotantes)
            # --- LINHA REMOVIDA DAQUI ---
            st.rerun()


# --- PÁGINA DE COMPATIBILIDADE ---

def page_compatibilidade():
    """Página para calcular e exibir animais compatíveis com um adotante."""
    st.title("Animais Compatíveis")
    
    search_name = st.text_input("Digite o nome do Adotante para buscar compatibilidade:")
    
    if not search_name:
        st.info("Digite o nome de um adotante cadastrado para ver os animais compatíveis.")
        return

    # 1. Buscar o adotante
    adotante = find_data_by_name("adotantes", search_name)
    
    if not adotante:
        st.error(f"Adotante com nome '{search_name}' não encontrado.")
        return
        
    st.success(f"Calculando compatibilidade para: **{adotante['nome']}**")
    st.write(f"Preferências: {adotante['tamanho']} (peso {adotante['peso_tamanho'][0]}), {adotante['moradia']} (peso {adotante['peso_moradia'][0]})")
    
    # 2. Buscar TODOS os animais
    animais_df = get_all_data("animais")
    if animais_df.empty:
        st.warning("Nenhum animal cadastrado no banco de dados.")
        return
        
    # 3. Calcular os scores
    sorted_scores = calculate_scores(adotante, animais_df)
    
    if not sorted_scores:
        st.info("Cálculo concluído, mas nenhum score foi gerado.")
        return

    # 4. Aplicar a lógica de exibição (Top 10 + empates)
    
    resultado_final = []
    
    if len(sorted_scores) <= 10:
        # Regra: Menos de 10 animais, mostra todos
        resultado_final = sorted_scores
    else:
        # Regra: Mais de 10 animais, pega o score do 10º
        score_do_decimo = sorted_scores[9]['score'] # Índice 9 é o 10º item
        
        # Filtra: todos com score >= ao 10º
        resultado_final = [s for s in sorted_scores if s['score'] >= score_do_decimo]

    # 5. Exibir os resultados
    st.subheader(f"Lista de {len(resultado_final)} Animais Mais Compatíveis:")
    
    # Converte para DataFrame para exibição bonita
    df_resultado = pd.DataFrame(resultado_final)
    # Ajusta o índice para começar em 1 (ranking)
    df_resultado.index = df_resultado.index + 1
    
    st.dataframe(
        df_resultado.style.format({'score': '{:.4f}'}), # Formata o score
        use_container_width=True
    )


# --- Execução Principal da Aplicação ---

# Inicializa o DB (e faz a migração se necessário)
init_db()

st.sidebar.title("Navegação da Aplicação")
st.sidebar.info("Sistema de Gerenciamento de Adoções")

# Dicionário de páginas com a nova ordem
paginas = {
    "Ver tabela de adotantes": "page_ver_adotantes",
    "Ver tabela de animais": "page_ver_animais",
    "Acrescentar arquivos CSV": "page_upload_csv", # NOVA PÁGINA
    "Formulário do adotante": "page_form_adotante",
    "Formulário do animal": "page_form_animal",
    "Editar dados do adotante": "page_edit_adotante",
    "Editar dados do animal": "page_edit_animal",
    "Animais compatíveis": "page_compatibilidade" # MOVDA PARA O FIM
}

escolha = st.sidebar.radio("Escolha uma página:", list(paginas.keys()))

# Roteamento (atualizado para a nova ordem)
if escolha == "Ver tabela de adotantes":
    page_ver_tabela("adotantes", "Ver Tabela de Adotantes")

elif escolha == "Ver tabela de animais":
    page_ver_tabela("animais", "Ver Tabela de Animais")

elif escolha == "Acrescentar arquivos CSV": # NOVO ROTEAMENTO
    page_upload_csv()

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

elif escolha == "Animais compatíveis":
    page_compatibilidade()