<p>
<img src="./public/img/image.png"  style="display: flex; justify-content: center; width:80px; align-items:center; border: 5px solid #ccc; border-radius:50px"/>

# Agregadores 12A2

</p>

<div data-badges align="center">

<img src="https://img.shields.io/badge/LangChain-22C55E?style=for-the-badge&logo=langchain&logoColor=white" alt="LangChain" />
<img src="https://img.shields.io/badge/chatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white" alt="ChatGPT" />
<img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit" />
<img src="https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite" />
<img src="https://img.shields.io/github/stars/agregadores-i2a2/i2a2?style=for-the-badge" alt="GitHub stars" />

</div>

## 🖥️ Como rodar este projeto 🖥️

### Configuração do Ambiente

- Instalar os pacotes, pode ser utilizado o requeriments.txt para instalar todas
  as dependências;
- Colocar a chave API;
- Mudar no arquivo app.py o endereço do arquivo em

  ```
  if st.button ("Importar Dados Banco"):
          zip_path = st.text_input("Caminho completo do ZIP", value="Sua pasta/Arquivos/202401_NFs.zip")
          extract_to = st.text_input("Diretório de extração", value="Sua pasta/Arquivos/arq/")
  ```

- Para chamar o projeto, dentro da pasta:
  ```sh
  streamlit run app.py
  ```

### Execução do Teste/Aplicação

- A execução do passo anterior irá abrir a página web;
- Selecionar o modelo e clicar em Carregar Modelo;
- Colocar os arquivos na pasta;
- Importar o banco de dados;

