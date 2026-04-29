# Smart BI — Contexto do Projeto

## O que é
Aplicação web em **Streamlit + Python** que permite usuários sem conhecimento técnico fazer upload de planilhas Excel e gerar dashboards interativos com gráficos e exportação em PDF.

## Stack
- **Frontend/App:** Streamlit
- **Processamento de dados:** Polars
- **Gráficos:** Plotly
- **Banco de dados:** Supabase (PostgreSQL)
- **Export:** ReportLab (PDF), LaTeX, HTML
- **Arquitetura:** Clean Architecture (domain / use_cases / infrastructure / presentation)

## Estrutura do projeto
```
app.py                        # Entry point principal
domain/
  entities.py                 # DataSchema, Column, ColumnType, VisualizationType, VisualizationConfig, Analysis, Slide
  value_objects.py            # FilterCondition, AggregationConfig, ExportOptions
use_cases/
  data_service.py             # Leitura de Excel, casting de tipos, cache de dados, validate_and_cast_types
  analysis_service.py         # CRUD de análises e slides
  export_service.py           # Export HTML e LaTeX
infrastructure/
  chart_factory.py            # Geração de gráficos Plotly (ChartFactory)
  pdf_generator.py            # Geração de PDF via ReportLab
presentation/
  widgets.py                  # render_column_mapper, render_widget_palette, render_visualization_config_dialog, _configure_*
  canvas.py                   # render_canvas, render_slide_navigator, render_table, render_metric_card
  sidebar.py                  # render_sidebar
  components.py               # Modais: settings, export, welcome, notifications
utils/
  session_state.py            # get_state, set_state, init_session_state
data/                         # Análises persistidas em JSON (local)
```

## Fluxo principal do usuário
1. Upload de arquivo `.xlsx`
2. Tela de mapeamento de colunas → sistema exibe os tipos **já detectados automaticamente** pelo `DataService`; usuário confirma ou ajusta (Numérico, Data/Hora, Categoria, Texto)
3. Sistema aplica casting de tipos via `validate_and_cast_types` e gera o `DataSchema`
4. Usuário adiciona visualizações (gráficos) ao canvas via paleta de widgets
5. Configura cada gráfico (categoria, métricas, agregação, paleta de cores, mostrar valores, legenda, grade)
6. Exporta em PDF

## Estado atual das tarefas

### ✅ Concluído
- Módulo de upload de Excel
- Tela de login/cadastro
- Integração com banco de dados (Supabase)
- Validação de tipagem (`validate_and_cast_types`) — suporta NUMERIC, DATETIME, CATEGORICAL, TEXT
- Mapeador de colunas (`render_column_mapper`) — usa tipos detectados pelo DataService como default, NÃO renomeia colunas
- `VisualizationConfig` com `y_column` (singular) + `y_columns` (lista, multi-métrica) + `show_values`
- Gráfico de Colunas (`COLUMN_CHART`) — barras verticais, multi-Y, agregação real
- Gráfico de Barras (`BAR_CHART`) — barras horizontais, multi-Y, agregação real
- Linha, Área, Pizza — com paleta de cores, mostrar valores e agregação real
- Tabela — salva todas as colunas selecionadas em `y_columns` (sem limite de 3)
- `ChartFactory` com helper `_aggregate()` central para groupby + agg em todos os gráficos

### 🔧 Em andamento / Pendente
- [ ] **Filtros Globais** — filtros por coluna aplicados a todos os gráficos do slide
- [ ] **Campo de Criação de Medidas** — colunas calculadas (ex: Receita / Qtd = Ticket Médio)
- [ ] **Tabelas Interativas** — ordenação e paginação no frontend
- [ ] **requirements.txt** — está vazio, precisa ser gerado
- [ ] **Integração das branches** — Victor está responsável

## Contratos e convenções críticas

### Mapeador de colunas
- `render_column_mapper(df, schema=None)` retorna `{nome_original: label_string}` onde label ∈ `["Numérico", "Data/Hora", "Categoria", "Texto"]`
- **NÃO renomeia colunas** — nomes originais são sempre preservados
- `_render_mapping_screen` converte os labels para `ColumnType` e chama `validate_and_cast_types(df, {col: ColumnType})`
- `DataSchema.from_polars` é chamado APÓS o casting para refletir os tipos corretos
- Estado temporário no Streamlit: `temp_df`, `temp_schema`, `pending_upload_name`, `pending_file_name`

### VisualizationConfig
- `y_column: Optional[str]` — coluna única (linha, área, pizza, scatter, box, heatmap)
- `y_columns: List[str]` — lista de métricas (colunas/barras multi-Y, tabela)
- `show_values: bool = False` — exibe rótulos nos gráficos
- `color_scheme: str = "default"` — paleta Plotly (default, pastel, dark, vivid, safe, d3, set1, set2)
- `aggregation: str` — chave em inglês: "sum", "mean", "count", "min", "max"
- `to_dict` / `from_dict` serializam todos os campos acima

### VisualizationType (enum)
```
LINE_CHART, BAR_CHART, PIE_CHART, SCATTER_PLOT, HISTOGRAM,
AREA_CHART, TABLE, METRIC_CARD, HEATMAP, BOX_PLOT, COLUMN_CHART
```
- `COLUMN_CHART` = barras verticais (ex-BAR_CHART)
- `BAR_CHART` = barras horizontais (`orientation="h"`)

### ChartFactory
- `create_chart(df, config)` faz dispatch por `VisualizationType`
- `_aggregate(df, x_col, y_cols, agg, group_col=None)` — helper central de groupby+agg usado por todos os gráficos que precisam de agregação
- `_colors(config)` — retorna a paleta de cores do config
- Gráficos sem agregação (raw data): SCATTER_PLOT, HISTOGRAM, BOX_PLOT

### render_table (canvas.py)
- Lê colunas de `config.y_columns` (lista completa, prioridade)
- Fallback para `[x_column, y_column, color_column]` (configs antigas)
- Exibe até 200 linhas, sem agregação (tabela é visualização de dados brutos)

### Widgets — constantes compartilhadas (widgets.py)
```python
_AGG_OPTIONS = {"sum": "Soma", "mean": "Média", "count": "Contagem", "min": "Mínimo", "max": "Máximo"}
_COLOR_SCHEMES = ["default", "pastel", "dark", "vivid", "safe", "d3", "set1", "set2"]
_MAPPER_OPTIONS = ["Numérico", "Data/Hora", "Categoria", "Texto"]
_COLUMN_TYPE_TO_LABEL = {ColumnType.NUMERIC: "Numérico", ColumnType.DATETIME: "Data/Hora", ...}
```

## Observações importantes
- Persistência local em JSON na pasta `data/` (FileAnalysisRepository)
- Free tier: Supabase + Streamlit Cloud (custo zero para MVP)
- Agregações PT-BR na UI mas armazenadas em inglês no JSON ("sum", "mean" etc.)
- `show_values` no `VisualizationConfig` controla rótulos em TODOS os tipos de gráfico
