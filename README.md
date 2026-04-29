# Dashboard Financeiro Executivo

Aplicação em **Streamlit** para apresentação financeira executiva, com foco em clareza visual, leitura rápida de indicadores e evolução dos resultados ao longo do período analisado.

O projeto combina **Python + Streamlit + Plotly + HTML/CSS**, com separação por camadas para facilitar manutenção, evolução da interface e integração com dados vindos de planilhas.

## Visão Geral

O dashboard foi desenhado para apoiar apresentação executiva de resultados financeiros, trazendo:

- KPIs principais com formatação compacta de valores
- Receita, despesas, resultado líquido e margens
- Cards analíticos com insights automáticos
- Gráficos de evolução anual e mensal em pop-up
- Estrutura preparada para ingestão de dados vindos de planilhas

O objetivo final é transformar o projeto em um **app completo**, pronto para uso em apresentação e evolução contínua.

## Stack

- **Python**
- **Streamlit**
- **Plotly**
- **HTML/CSS** para refinamento visual
- **JSON** como conteúdo-base da interface
- Estrutura voltada para integração com **planilhas Excel**

## Funcionalidades Atuais

- Renderização do dashboard executivo em tela única
- Formatação monetária compacta em `M` e `K`
- Cards de receita e despesa com detalhamento expansível
- Bloco de resultado líquido e margens
- Insights e análise técnica gerados automaticamente
- Menu flutuante para acesso à evolução anual/mensal
- Janela pop-up para gráficos comparativos
- Estrutura modular para facilitar manutenção

## Estrutura do Projeto

```text
app.py
requirements.txt
assets/
  css/
    styles.css
  images/
components/
  dashboard_components.py
config/
  settings.py
data/
  dashboard_content.json
  Faturamento Allan.xlsx
  INFORMAÇÕES GERENCIAIS.xlsx
  Orçamento.xlsx
etl/
  loader.py
utils/
  analysis_generator.py
  dashboard_metrics.py
  evolution_charts.py
  number_formatter.py
```

### Descrição das Pastas

- `app.py`: ponto de entrada da aplicação Streamlit
- `components/`: composição e renderização dos blocos visuais do dashboard
- `config/`: parâmetros e configurações gerais do projeto
- `data/`: dados-base do dashboard e planilhas de referência
- `etl/`: carregamento e orquestração dos dados de origem
- `utils/`: regras de negócio, métricas, formatação e geração de análise
- `assets/`: estilos visuais e imagens da interface

## Arquivos Principais

### `app.py`

Responsável por iniciar a aplicação, carregar estilos, buscar o conteúdo e renderizar o dashboard final.

### `components/dashboard_components.py`

Central de composição visual. Contém:

- renderização dos cards principais
- estrutura do header
- botão flutuante do menu de evolução
- modal pop-up com gráficos
- montagem do HTML do dashboard

### `etl/loader.py`

Carrega o conteúdo do arquivo JSON, lê as planilhas e prepara os dados para exibição.

### `utils/dashboard_metrics.py`

Calcula métricas financeiras e auxilia no tratamento dos valores mostrados na tela.

### `utils/analysis_generator.py`

Gera análise técnica e insights automáticos a partir dos dados carregados.

### `utils/number_formatter.py`

Responsável pela formatação compacta dos valores monetários e numéricos.

### `utils/evolution_charts.py`

Gera os gráficos Plotly de evolução anual e mensal.

## Como Executar

### Pré-requisitos

- Python 3.13 ou compatível com o ambiente do projeto
- Ambiente virtual configurado
- Dependências instaladas a partir de `requirements.txt`

### Instalação

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Execução

```bash
run_app.ps1
```

Também é possível iniciar diretamente com:

```bash
streamlit run app.py
```

Se preferir rodar manualmente no PowerShell, use:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\run_app.ps1
```

## Dados e Evolução

Hoje o projeto já possui base funcional com conteúdo estruturado em JSON e leitura de dados local via ETL. O próximo passo do roadmap é consolidar os dados que chegam via planilhas para que o sistema:

- leia as planilhas automaticamente
- normalize os campos recebidos
- atualize o conteúdo do dashboard sem retrabalho manual
- mantenha consistência entre dados brutos e dados de apresentação

Isso deve evoluir o projeto de um dashboard estático para um **app financeiro dinâmico**.

## Direção de Produto

O projeto deve continuar evoluindo com foco em:

- experiência executiva de apresentação
- manutenção simples e incremental
- atualização automática do conteúdo
- visual premium e profissional
- prontidão para uso como app final

## Skills Foco

Áreas que mais importam para a continuação do projeto:

- integração de planilhas e ETL
- modelagem de dados financeiros
- Streamlit e construção de interface
- Plotly para visualização interativa
- arquitetura de código modular
- formatação monetária e padronização visual
- preparação do projeto para uso como app final

## Roadmap Sugerido

1. Integrar a leitura das planilhas recebidas
2. Normalizar e mapear os campos para o modelo do dashboard
3. Atualizar o conteúdo exibido com base em dados reais
4. Consolidar a navegação e os gráficos de evolução
5. Preparar o app para apresentação final e publicação

## Observações

- A aplicação foi pensada para ser incrementada sem refazer toda a base.
- O layout e a estrutura priorizam leitura rápida e apresentação executiva.
- O projeto já está em um ponto bom para evoluir de forma segura para uma solução mais automatizada.

## Licença

Uso interno / projeto em desenvolvimento.