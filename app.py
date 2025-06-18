import os
import streamlit as st
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import initialize_agent, AgentType
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from funcoes.arquivos import (
    process_csv,
    import_base,
    load_embedding,
    add_to_vector_store,
    load_llm,
)

SQLITE_DB_PATH = 'trabalho.db'

@st.cache_resource
def carregar_modelo_e_ferramentas(model_name):
    """Carrega o modelo LLM e as ferramentas necessárias."""
    try:
        llm = load_llm(model_name)
        db = SQLDatabase.from_uri(f"sqlite:///{SQLITE_DB_PATH}")
        toolkit = SQLDatabaseToolkit(db=db, llm=llm)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", '''
Você é um **Analista de Dados Sênior**, especialista em **Notas Fiscais Eletrônicas (NF-e)**, com domínio em **SQL, Python e análise de dados empresariais**.

Sua missão é **responder perguntas analíticas** com **clareza, precisão e objetividade**, baseando-se em um **banco de dados relacional** contendo informações de **notas fiscais e seus itens**, com foco em **indicadores estratégicos para tomada de decisão**.

Todas as respostas devem ser em **português (pt-BR)**, utilizando **linguagem clara e executiva**, ideal para apresentação à **diretoria da empresa**.

---

### 🎯 Instruções de Resposta

1. Seja direto e claro. Evite jargões técnicos excessivos.
2. Utilize **etapas numeradas** para explicar sua lógica de forma resumida.
3. Sempre que possível, estruture a resposta com **Markdown** para facilitar a visualização no chat.
4. Utilize **tabelas Markdown** nos resultados e envolva-as com blocos de código:

\```markdown
| Coluna 1 | Coluna 2 |
|----------|----------|
\```

5. Sempre que fizer sentido, **sugira visualizações complementares** como gráficos de barras, rankings ou séries temporais.

---

### 📌 Formatações e Padrões a seguir

- **Valores Monetários**: R$ 1.234,56  
- **Produtos/Serviços**: Exibir descrição e valor unitário.  
- **Fornecedores**: Mostrar como:
  
  > Razão Social | Valor Total | Quantidade de Notas

- **Clientes (Destinatários)**: Mostrar por volume financeiro total.
- **CFOPs**: Exibir os mais recorrentes, com descrição e quantidade.

---

### 💡 Exemplos de Perguntas Esperadas

- Qual o fornecedor com maior número de notas?
- Qual o item mais caro por valor unitário?
- Quais os produtos que mais geraram receita?
- Qual o valor total movimentado em janeiro de 2024?
- Quais são os principais CFOPs utilizados?
                            '''),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        agent = initialize_agent(
            tools=toolkit.get_tools(),
            llm=llm,
            prompt=prompt,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True
        )
        return llm, agent
    except Exception as e:
        st.error(f"Erro ao carregar modelo: {str(e)}")
        return None, None

# Configuração inicial
st.set_page_config(page_title="Chat Executivo Contábil", layout="wide")

# Inicialização de estados
if "messages" not in st.session_state:
    st.session_state.messages = []
if "modelo_carregado" not in st.session_state:
    st.session_state.modelo_carregado = False
if "llm" not in st.session_state:
    st.session_state.llm = None
if "agent_executor" not in st.session_state:
    st.session_state.agent_executor = None

# Título da página
st.title("📊 Chat Executivo")



# Importação de dados
with st.sidebar:

    st.title('Configurações')

    st.markdown("# Sobre")
    st.text('Analise de notas')
    st.text('''
Sistema voltado para executivos com o objetivo de trazer insides com as melhores respostas e as melhores analises para tomada de desições estrategicas
''')


    # # Carregar Chave API
    # api_key = st.text_input("Insira sua chave:", type="password")

    # Seleção do modelo
    model_name = st.sidebar.selectbox("Escolha o modelo OpenAi", options=[
        "gpt-3.5-turbo",
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
    ])

    # Botão de carregamento do modelo
    if st.session_state.modelo_carregado:
        botao_texto = "✅ Modelo Carregado"
    else:
        botao_texto = "❌ Carregar Modelo"

    if st.sidebar.button(botao_texto):
        with st.spinner("🔄 Carregando modelo e ferramentas..."):
            llm, agent = carregar_modelo_e_ferramentas(model_name)
            if llm and agent:
                st.session_state.llm = llm
                st.session_state.agent_executor = agent
                st.session_state.modelo_carregado = True
                st.success("Modelo carregado com sucesso!")
            else:
                st.error("Falha ao carregar o modelo.")

    st.text('Carregar Banco de dados')
    if st.button("Importar Dados Banco"):
        zip_path = st.text_input("Caminho completo do ZIP", value="E:/Projeto_IA_Master/Chat_Rag_Openai/Arquivos/202401_NFs.zip")
        extract_to = st.text_input("Diretório de extração", value="E:/Projeto_IA_Master/Chat_Rag_Openai/Arquivos/arq/")
        try:
            if import_base(zip_path, extract_to):
                st.success("Base importada com sucesso!")
            else:
                st.error("Falha ao importar base de dados.")
        except Exception as e:
            st.error(f"Erro durante importação: {str(e)}")


    # # Upload de arquivos CSV
    # uploaded_files = st.sidebar.file_uploader(
    #     "Upload de arquivos CSV para legislação",
    #     accept_multiple_files=True, 
    #     type=['csv']
    # )

    # if uploaded_files:
    #     vector_store = load_embedding()
    #     for file in uploaded_files:
    #         try:
    #             chunks = process_csv(file)
    #             vector_store = add_to_vector_store(chunks, vector_store)
    #         except Exception as e:
    #             st.error(f"Erro ao processar arquivo {file.name}: {str(e)}")
    #     if vector_store:
    #         try:
    #             vector_store.persist()
    #             st.sidebar.success("Arquivos processados e vetorizados com sucesso!")
    #         except Exception as e:
    #             st.error(f"Erro ao persistir vector store: {str(e)}")




# Inicializa a sessão se necessário
if "messages" not in st.session_state:
    st.session_state.messages = []

# Campo de entrada
user_input = st.chat_input("👉 Digite sua pergunta fiscal...")

# 1. Exibe todo o histórico (mensagens anteriores) de forma cronológica
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 2. Se houver nova pergunta, processa
if user_input:
    # 2.1 Mostra a nova pergunta (em tempo real)
    with st.chat_message("user"):
        st.markdown(user_input)

    # 2.2 Cria um espaço temporário para exibir "processando" e depois substituir pela resposta
    placeholder_resposta = st.empty()

    # 2.3 Gera a resposta
    if not st.session_state.get("modelo_carregado", False):
        resposta_texto = "⚠️ Modelo não carregado. Por favor, carregue um modelo na barra lateral."
        with placeholder_resposta.container():
            with st.chat_message("assistant"):
                st.markdown(resposta_texto)
    else:
        with placeholder_resposta.container():
            with st.chat_message("assistant"):
                with st.spinner("💬 Processando..."):
                    try:
                        resposta = st.session_state.agent_executor.invoke({"input": user_input})
                        resposta_texto = resposta.get("output", "❌ Não foi possível gerar uma resposta.")
                    except Exception as e:
                        resposta_texto = f"❌ Erro: {str(e)}"
                        st.error(resposta_texto)

                # Substitui o spinner pela resposta
                st.markdown(resposta_texto)

    # 2.4 Atualiza o histórico (somente depois de mostrar tudo corretamente)
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append({"role": "assistant", "content": resposta_texto})



# # Campo de entrada do usuário
# user_input = st.chat_input("👉 Digite sua pergunta fiscal...")

# # Exibição do histórico de mensagens anteriores
# for msg in st.session_state.messages:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# # Processamento da nova pergunta
# if user_input:
#     # Exibe a pergunta atual imediatamente
#     with st.chat_message("user"):
#         st.markdown(user_input)
#     st.session_state.messages.append({"role": "user", "content": user_input})
    
#     # Processa a resposta
#     with st.chat_message("assistant"):
#         if not st.session_state.modelo_carregado:
#             st.warning("⚠️ Modelo não carregado. Por favor, carregue um modelo na barra lateral.")
#             resposta_texto = "⚠️ Modelo não carregado. Por favor, carregue um modelo na barra lateral."
#         else:
#             with st.spinner("💬 Processando..."):
#                 try:
#                     resposta = st.session_state.agent_executor.invoke({"input": user_input})
#                     resposta_texto = resposta.get("output", "❌ Não foi possível gerar uma resposta.")
#                     st.markdown(resposta_texto)
#                 except Exception as e:
#                     resposta_texto = f"❌ Erro: {str(e)}"
#                     st.error(resposta_texto)
#         # Adiciona a resposta ao histórico
#         st.session_state.messages.append({"role": "assistant", "content": resposta_texto})
