import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Abrigo de Animais", page_icon="dog")

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

# Estabelece as opções apresentadas nos formulários
# Meu_dicionario.keys() retorna todas as keys de um dicionário
# O uso de list sobre as keys as coloca em uma lista
TAMANHO_OPTIONS = list(TAMANHO_MAP.keys())
MORADIA_OPTIONS = list(MORADIA_MAP.keys())

def get_db_connection():
    """estabelece uma conexão com um banco de dados SQLite ou cria um se não existir"""

    # sqlite3.connect() estabelece uma conexão com o arquivo do SQLite (enderço entre parênteses) 
    # Também retorna um objeto Connection, capaz de interagir com o banco de dados 
    conn = sqlite3.connect(DB_NAME)

    # Cria um objeto Row para o atributo row_factory de conn
    # Isso que faz com que as queries feitas pelo objeto conn retornem num formato especial
    # Nesse formato dá para acessar o cruzamento de linha e colunas usando o nome da coluna
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados e cria as tabelas (se eles não existirem)."""

    # Estabelece uma conexão com um banco de dados SQLite ou cria um se não existir
    conn = get_db_connection()

    # conn.cursor() é um método do objeto de conexão
    # Ele cria e retorna um objeto "cursor"
    # O cursor é capaz de fazer chamadas SQL e navegar pelos resultados
    cursor = conn.cursor()
    
    # Cria tabela de Adotantes, se ainda não foi criada
    # Autoincrement faz valor ser automático crescendo de 1 em 1
    # Not null indica que coluna não pode ficar vazia
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS adotantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL UNIQUE,
        tamanho TEXT NOT NULL,
        codigo_tamanho TEXT NOT NULL,
        moradia TEXT NOT NULL,
        codigo_moradia TEXT NOT NULL
    );
    ''')
    
    # Cria tabela de Animais, se ainda não foi criada
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

    # Salva as mudanças de modo permanente no banco de dados
    conn.commit()
    # Fecha a conexão com o banco de dados
    # É uma boa prática
    conn.close()

# --- Funções CRUD (Create, Read, Update, Delete) ---

def add_data(table_name, nome, tamanho, moradia):
    """Adiciona um novo registro (adotante ou animal) ao banco de dados."""

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        codigo_tamanho = TAMANHO_MAP[tamanho]
        codigo_moradia = MORADIA_MAP[moradia]

        # Inserir na tabela uma linha, tendo em tais colunas tais valores 
        # No casos os valores não são definidos diretamente, mas por variáveis
        # AS interregações são placeholders para os valores reais (isso protege contra SQL injection)
        cursor.execute(
            f"INSERT INTO {table_name} (nome, tamanho, codigo_tamanho, moradia, codigo_moradia) VALUES (?, ?, ?, ?, ?)",
            (nome, tamanho, codigo_tamanho, moradia, codigo_moradia)
        )
        conn.commit()
        st.success(f"Registro '{nome}' adicionado com sucesso à tabela '{table_name}'!")

        # A outros erros de integridade, além de valor duplicado, como valor NULL para coluna NOT NULL
        # Para qualquer erro de integridade vai falar que nome já existe
    except sqlite3.IntegrityError:
        st.error(f"Erro: O nome '{nome}' já existe na tabela '{table_name}'.")
        # A exceção impede o programa de quebrar. 
        # Seria possível só essa exceção, mas a exceção acima é útil para o usuário
        # O "e" é a mensagem de erro que o Python daria ao quebrar
    except Exception as e:
        st.error(f"Ocorreu um erro: {e}")

    finally:
        conn.close()

def get_all_data(table_name):
    """Busca todos os registros de uma tabela e retorna como DataFrame."""

    conn = get_db_connection()

    # Tenta usar o pandas para executar SQL quê ler toda a tabela (do banco de dados da conectado)
    # O pandas faz as querries e cria o dataframe
    # Se fosse usar o objeto cursor, ele teria de ser usado várias vezes, 
    # e mesmo assim seria preciso usar pandas para criar o dataframe
    try:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        return df
    
    # O que fazer em caso de erro
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

    # Af fazer consulta SELECT, o resultado fica armazenado no cursor. 
    # O fetchone() pega apenas a primeira linha armazenada no cursor.
    data = cursor.fetchone()

    conn.close()
    # Retorna um objeto sqlite3.Row (similar a um dicionário) ou None
    return data

def update_data(table_name, id, nome, tamanho, moradia):
    """Atualiza um registro existente no banco de dados."""

    # Estabelece conexão com o banco de dados
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # A função já recebeu o nome e as opções
        # Agora obtém os códigos das opções a partir das opções
        codigo_tamanho = TAMANHO_MAP[tamanho]
        codigo_moradia = MORADIA_MAP[moradia]
        
        # Atualiza a tabela
        # Não atualiza diretamente, coloca ?, para evitar ataque via SQL
        cursor.execute(
            f"UPDATE {table_name} SET nome = ?, tamanho = ?, codigo_tamanho = ?, moradia = ?, codigo_moradia = ? WHERE id = ?",
            (nome, tamanho, codigo_tamanho, moradia, codigo_moradia, id)
        )

        #Salva as alterações
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

    # Exibe o título relativo à tabela que você quer visualizar
    st.title(title)

    # Coloca dados da tabela que você quer visualizar num dataframe
    df = get_all_data(table_name)
    if df.empty:
        st.info("A tabela está vazia.")

    # Exibe dataframe
    else:
        st.dataframe(df)

def page_formulario(table_name, title, q_nome, q_tamanho, q_moradia):
    """Página de formulário para adicionar novos registros."""

    st.title(title)

    # Cria um formulário Streamlit com uma chave única baseada no nome da tabela
    # A chave permite que o formulário seja identificado pelo Streamlit
    # A chave pode ser qualquer string
    # with st.form() permite interagir com widgets de entrada no seu interior sem reexecutar o script.
    with st.form(key=f"form_{table_name}"):

        st.subheader("Por favor, preencha os dados:")

        # Cria caixa de texto; a descrição da caixa é colocada entre parênteses
        nome = st.text_input(q_nome)
        # Cria caixa de seleção; as opções são colocadas em uma lista
        tamanho = st.selectbox(q_tamanho, options=TAMANHO_OPTIONS)
        moradia = st.selectbox(q_moradia, options=MORADIA_OPTIONS)

        # Cria um botão de envio (entre parênteses o que está escrito nele)
        # Quando clicado, submitted passa a ser True 
        # O botão de submeter não submete nada, só possibilita o código do if
        submitted = st.form_submit_button("Enviar")
        if submitted:
            if not nome:
                st.warning("O campo 'nome' é obrigatório.")
            else:
        # Os dados vão ser submetidos (acrescentados ao banco de dados) aqui
                add_data(table_name, nome, tamanho, moradia)

def page_editar_dados(table_name, title):
    """Página para editar registros existentes."""
    st.title(title)
    
    # st.text_input() cria caixa para input
    # input é recolhido com um Enter
    # Entre parênteses colocar: ("descriçao da caixa", key="indentificação da caixa")
    search_name = st.text_input(f"Digite um nome da tabela ({table_name}) para buscar e editar:", key=f"search_{table_name}")
    
    if not search_name:
        st.info("Digite um nome para iniciar a busca.")
        return
    
    # Esse é uma uma função definda acima
    # Pesquisa o DB e devolve a primeira linha cujo nome coincide com search_name
    data = find_data_by_name(table_name, search_name)
    
    # Define nome de atributos para o session_state
    id_key = f"edit_id_{table_name}"
    nome_key = f"edit_nome_{table_name}"
    tamanho_key = f"edit_tamanho_{table_name}"
    moradia_key = f"edit_moradia_{table_name}"

    if data:
        # Se for uma nova busca (ou a primeira), carrega os dados no session_state
        # Guarda os dados da linha que será alterada em atributos do session_state
        if id_key not in st.session_state or st.session_state[id_key] != data['id']:
            st.session_state[id_key] = data['id']
            st.session_state[nome_key] = data['nome']
            st.session_state[tamanho_key] = data['tamanho']
            st.session_state[moradia_key] = data['moradia']
            # Força o rerender para atualizar os widgets do formulário
            st.rerun()

        # Aparece na tela o nome da pessoa ou animal que se está editando
        st.info(f"Editando dados de: {st.session_state[nome_key]} (ID: {st.session_state[id_key]})")
        
        # Criar um form para editar os dados da pessoa ou animal
        with st.form(key=f"edit_form_{table_name}"):

            # Título do form
            st.subheader("Atualize os campos necessários:")
            
            # variável_options traz lista de opções da variável
            # Pega-se o índice da opções que estão na linha da tabela
            try:
                tamanho_index = TAMANHO_OPTIONS.index(st.session_state[tamanho_key])
            except ValueError:
                tamanho_index = 0 # Default para 'pequeno' se algo der errado
                
            try:
                moradia_index = MORADIA_OPTIONS.index(st.session_state[moradia_key])
            except ValueError:
                moradia_index = 0 # Default para 'casa'

            # Mostra formulário com as opções que estão na tabela
            # O index indica qual opção mostrar no formulário
            # Como essas funções de entrada têm key, elas alimentam o session_state com a key
            nome = st.text_input("Nome", key=nome_key)
            tamanho = st.selectbox("Tamanho", options=TAMANHO_OPTIONS, index=tamanho_index, key=tamanho_key)
            moradia = st.selectbox("Moradia", options=MORADIA_OPTIONS, index=moradia_index, key=moradia_key)

            st.markdown("---")
            st.subheader("Campos automáticos (não editáveis)")
            
            # Mostra os códigos one-hot baseados nos valores ATUAIS do formulário
            # dicionário.get(key, valor padrão) pega um valor do dicionário
            # Ela pega o valor associado ao key, e se não achar pega o valor padrão
            st.text_input("Código Tamanho (auto)", 
                           value=TAMANHO_MAP.get(st.session_state[tamanho_key], "Inválido"), 
                           disabled=True)
            st.text_input("Código Moradia (auto)", 
                           value=MORADIA_MAP.get(st.session_state[moradia_key], "Inválido"), 
                           disabled=True)

            submitted = st.form_submit_button("Atualizar")

            if submitted:
                # Função update_data foi definida acima
                # Na submissão, usa os valores do session_state
                update_data(
                    table_name,
                    st.session_state[id_key],
                    st.session_state[nome_key],
                    st.session_state[tamanho_key],
                    st.session_state[moradia_key]
                )
                # Limpa o state após a atualização para permitir nova busca
                keys_to_clear = [id_key, nome_key, tamanho_key, moradia_key]
                for key in keys_to_clear:
                    if key in st.session_state:
                        del st.session_state[key]
                # Limpa a caixa de busca e recarrega
                st.query_params.clear()
                st.rerun()

    else:
        st.warning(f"Nenhum registro encontrado com o nome: '{search_name}'")
        # Limpa o state se o nome não for encontrado
        keys_to_clear = [id_key, nome_key, tamanho_key, moradia_key]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]


# --- Execução Principal da Aplicação ---

# Inicializa o DB na primeira execução, e fecha conexão
# Se já existe DB, só verifica e fecha conexão
init_db()

st.sidebar.title("Navegação da Aplicação")
st.sidebar.info("Sistema de Gerenciamento de Adoções")

# Define um dicionário páginas 
# O key é o título da página
# O valor é uma tupla com o nome de uma tabela e o título da página
paginas = {
    "Ver tabela de adotantes": ("adotantes", "Ver Tabela de Adotantes"),
    "Ver tabela de animais": ("animais", "Ver Tabela de Animais"),
    "Formulário do adotante": ("adotantes", "Formulário do Adotante"),
    "Formulário do animal": ("animais", "Formulário do Animal"),
    "Editar dados do adotante": ("adotantes", "Editar Dados do Adotante"),
    "Editar dados do animal": ("animais", "Editar Dados do Animal")
}

# Cria menu de escolha de página usando keys do dicionário páginas
# Resultado é armazenado na variável escolha
escolha = st.sidebar.radio("Escolha uma página:", list(paginas.keys()))

# Roteamento das páginas
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