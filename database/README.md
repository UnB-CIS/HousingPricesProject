# Documentação da Pasta `database`

A pasta `database` contém os componentes principais responsáveis pela definição, conexão e manipulação de dados em um banco de dados MongoDB. Esses arquivos são responsáveis por configurar a comunicação com o banco, realizar operações CRUD (criar, ler, atualizar, excluir) e fornecer a lógica de acesso aos dados de maneira centralizada e eficiente. A seguir, estão as descrições dos arquivos e suas respectivas funções dentro da pasta.

## Estrutura da Pasta

- `config.py`: Contém as configurações principais para a conexão com o banco de dados.
- `connection.py`: Estabelece a conexão com o MongoDB e gerencia sessões.
- `main.py`: Arquivo principal que inicializa e gerencia a interação com o banco de dados.
- `repository.py`: Contém as funções para manipulação dos dados (operações CRUD).
- `__init__.py`: Arquivo responsável por tornar a pasta `database` um pacote Python, permitindo a importação dos módulos.

## Configuração do Banco de Dados

Para configurar e conectar ao MongoDB Atlas, siga os passos abaixo:

1. **Criar uma Conta no MongoDB Atlas**:
   - Acesse [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) e crie uma conta.

2. **Criar um Cluster**:
   - Após criar a conta, crie um novo cluster no MongoDB Atlas. Siga as instruções fornecidas pela plataforma para configurar o cluster.

3. **Obter as Credenciais de Conexão**:
   - No MongoDB Atlas, vá para a seção de segurança e configure um novo usuário de banco de dados. Anote o nome de usuário e a senha.
   - Obtenha a URI de conexão do cluster. A URI geralmente tem o formato:
     ```
     mongodb+srv://<username>:<password>@cluster0.mongodb.net/<dbname>?retryWrites=true&w=majority
     ```

4. **Configurar Variáveis de Ambiente**:
   - Crie um arquivo `.env` na raiz do seu projeto e adicione as seguintes variáveis de ambiente:
     ```env
     MONGO_DB_USER=<seu_nome_de_usuario>
     MONGO_DB_PASS=<sua_senha>
     MONGO_DB_CLUSTER=cluster0.mongodb.net
     ```

5. **Configurar o Arquivo `config.py`**:
   - O arquivo `config.py` usa as variáveis de ambiente para construir a URI de conexão:
     ```python
     import os

     DB_USER = os.environ["MONGO_DB_USER"]
     DB_PASSWORD = os.environ["MONGO_DB_PASS"]
     DB_CLUSTER = os.environ["MONGO_DB_CLUSTER", "cluster0.mongodb.net"]
     DB_URI = f"mongodb+srv://{DB_USER}:{DB_PASSWORD}@{DB_CLUSTER}/?retryWrites=true&w=majority"
     ```

### `config.py`

Este arquivo contém as configurações necessárias para a conexão com o banco de dados MongoDB. As variáveis de ambiente são usadas para armazenar informações sensíveis, como o nome de usuário e a senha do banco de dados, garantindo segurança na manipulação dessas credenciais. O URI de conexão com o MongoDB é construído com as informações do usuário e senha fornecidas.

#### Variáveis e Funções:
- **`DB_USER`**: Obtém o nome de usuário do MongoDB a partir da variável de ambiente `MONGO_DB_USER`.
- **`DB_PASSWORD`**: Obtém a senha do MongoDB a partir da variável de ambiente `MONGO_DB_PASS`.
- **`DB_CLUSTER`**: Define o nome do cluster do MongoDB, no caso, `cluster0.mongodb.net`.
- **`DB_URI`**: Concatena o nome de usuário, senha e o cluster para formar a URI de conexão com o MongoDB. Esta URI é usada para estabelecer a conexão com o banco de dados.

### `connection.py`

Este arquivo define a classe `MongoDBConnection`, que gerencia a conexão com o banco de dados MongoDB. A classe é responsável por estabelecer a conexão com o banco usando a URI fornecida e também por fechar a conexão quando não for mais necessária.

#### Classe:
- **`MongoDBConnection`**: Classe principal que lida com a conexão com o MongoDB.

##### Métodos:
- **Parâmetros**: 
  - `uri`: A URI de conexão com o MongoDB, geralmente definida em `config.py`.
- **`connect(self)`**: Estabelece a conexão com o banco de dados MongoDB usando a URI fornecida.
  - **Retorno**: Retorna o cliente MongoDB (`MongoClient`), que é usado para interagir com o banco de dados.
- **`close(self)`**: Fecha a conexão com o MongoDB, se a conexão estiver ativa.

### `repository.py`

Este arquivo define a classe `Property`, que é responsável pela manipulação dos dados de imóveis no banco de dados MongoDB. Ele fornece métodos para inserir um único imóvel ou múltiplos imóveis na coleção `property_listings`.

#### Classe:
- **`Property`**: Classe responsável pela inserção de dados de imóveis no banco de dados.

##### Métodos:
- **`__init__(self, client)`**: Inicializa a classe com o cliente MongoDB fornecido.
  - **Parâmetros**: 
    - `client`: O cliente MongoDB que é usado para acessar o banco de dados.
- **`insert_property(self, property)`**: Insere um único imóvel na coleção `property_listings` do banco de dados.
  - **Parâmetros**:
    - `property`: Um dicionário contendo os dados do imóvel a ser inserido.
  - **Retorno**: Retorna o ID do imóvel inserido.
- **`insert_multiple_properties(self, properties_list)`**: Insere múltiplos imóveis na coleção `property_listings`.
  - **Parâmetros**:
    - `properties_list`: Uma lista de dicionários, cada um contendo os dados de um imóvel.
  - **Retorno**: Retorna uma lista de IDs dos imóveis inseridos.

---

### `main.py`

Este arquivo inicializa a conexão com o banco de dados MongoDB e gerencia a inserção de dados de imóveis usando a classe `Property` do arquivo `repository.py`. Ele também inclui um caso de teste para inserção de múltiplos imóveis na coleção `property_listings`.

#### Funcionalidade:
- Estabelece a conexão com o banco de dados MongoDB usando a classe `MongoDBConnection` do arquivo `connection.py`.
- Cria uma instância da classe `Property` para manipular dados de imóveis.
- Insere múltiplos imóveis na coleção `property_listings`.
- **Observação**: O código inclui testes para inserção de dados no banco de dados.

O arquivo termina fechando a conexão com o banco de dados após a operação.