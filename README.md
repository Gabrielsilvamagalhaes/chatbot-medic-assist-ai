# Documentacao do Medic Assist AI

Esta pasta organiza a proposta do **Medic Assist AI** em arquivos Markdown separados por topico, para facilitar consulta, manutencao e uso no projeto.

---

## Integrantes


| Nome               | RA         |
| ------------------ | ---------- |
| Gabriel Silva      | 1272313274 |
| Hanspeter Dietiker | 1272313332 |


---

## Topicos

1. [Visao geral](docs/01-visao-geral.md)
2. [Contextualizacao do problema](docs/02-contextualizacao-problema.md)
3. [Objetivos](docs/03-objetivos.md)
4. [Limite etico e seguranca](docs/04-limite-etico-seguranca.md)
5. [Dataset de referencia](docs/05-dataset-referencia.md)
6. [Campos e colunas alvo](docs/06-campos-colunas-alvo.md)
7. [Regras de mapeamento](docs/07-regras-mapeamento.md)
8. [Tecnicas de IA](docs/08-tecnicas-ia.md)
9. [Fluxo de funcionamento](docs/09-fluxo-funcionamento.md)
10. [Arquitetura proposta](docs/10-arquitetura-proposta.md)
11. [Entregas e resultados esperados](docs/11-entregas-resultados.md)
12. [Backlog Desenvolvimento](docs/12-backlog-desenvolvimento.md)
13. [Documento A3](docs/13-trabalho-a3.md)

## Descricao curta

O Medic Assist AI e um chatbot de apoio a triagem hospitalar que utiliza um modelo de aprendizado treinado com registros de pacientes para sugerir a area hospitalar mais adequada e o nivel de urgencia, sem realizar diagnostico ou prescricao de medicamentos.

---

## Estrutura do projeto

```text
intelligence-ia-a3/
├── dataset/
│   ├── raw/                         # Dataset original do Kaggle (CSV separado por ;)
│   └── processed/                   # Dataset tratado com colunas derivadas
├── docs/                            # Documentacao do projeto por topico
├── src/
│   ├── main.py                      # Entry point: inicia o chatbot
│   ├── preprocess_dataset.py        # Script de limpeza e rotulacao do dataset
│   └── chatbot/
│       ├── conversation.py          # Coleta de dados e exibicao de resultado
│       ├── messages.py              # Mensagens de seguranca e avisos
│       ├── recommended_area_rules.py  # Regras para area hospitalar recomendada
│       └── urgency_triage_rules.py  # Regras para nivel de urgencia
└── tests/                           # Testes automatizados com pytest
```

---

## Pre-requisitos

- **Python 3.10 ou superior** (minimo: 3.8)

Verifique sua versao:

```bash
python --version
```

---

## Instalacao

### 1. Clone o repositorio

```bash
git clone https://github.com/seu-usuario/intelligence-ia-a3.git
cd intelligence-ia-a3
```

### 2. Crie e ative um ambiente virtual (recomendado)

```bash
# Criar
python -m venv venv

# Ativar no Windows
venv\Scripts\activate

# Ativar no Linux/macOS
source venv/bin/activate
```

### 3. Instale as dependencias

```bash
pip install -r requirements.txt
```


| Pacote | Uso                                    |
| ------ | -------------------------------------- |
| pandas | Leitura e processamento do dataset CSV |
| pytest | Execucao dos testes automatizados      |


---

## Como rodar

### Chatbot (fluxo principal)

Inicia a conversa guiada com o paciente e exibe a area recomendada e o nivel de urgencia:

```bash
python src/main.py
```

O chatbot faz perguntas em 4 etapas:

1. Dados basicos: idade e genero
2. Condicao principal (lista de opcoes)
3. Sintomas adicionais: febre, dor intensa, dificuldade respiratoria, nivel de consciencia
4. Historico: duracao dos sintomas e doencas cronicas

Ao final, exibe a area hospitalar recomendada, o nivel de urgencia e um resumo estruturado para triagem humana.

---

### Pre-processamento do dataset

Gera o dataset rotulado com as colunas `area_recomendada` e `nivel_urgencia` a partir do dataset bruto:

```bash
python src/preprocess_dataset.py
```

- **Entrada:** `dataset/raw/hospital-data-analysis.csv`
- **Saida:** `dataset/processed/hospital-data-labeled.csv`

Execute este script antes de treinar qualquer modelo de IA.

---

### Testes automatizados

```bash
pytest tests/
```

Para ver detalhes de cada teste:

```bash
pytest tests/ -v
```


| Arquivo de teste             | O que cobre                                      |
| ---------------------------- | ------------------------------------------------ |
| `test_area_rules.py`         | Regras de roteamento por condicao e faixa etaria |
| `test_urgency_rules.py`      | Escalada de nivel de urgencia                    |
| `test_preprocess_dataset.py` | Integridade e colunas do dataset processado      |


---

## Variaveis de ambiente

O projeto **nao utiliza variaveis de ambiente**. Nenhum arquivo `.env` e necessario.

Todos os caminhos de arquivo sao relativos ao diretorio raiz do projeto e ja estao configurados nos scripts.

---

## Limitacoes e avisos

- O sistema **nao realiza diagnostico medico** e **nao prescreve medicamentos**.
- A recomendacao gerada e apenas um apoio para triagem inicial.
- A decisao clinica final deve ser tomada por profissionais de saude.
- Em casos de emergencia, ligue para o **SAMU: 192**.

