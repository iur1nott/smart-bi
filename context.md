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
  entities.py                 # DataSchema, Column, ColumnType, VisualizationType, Analysis, Slide
  value_objects.py            # FilterCondition, AggregationConfig, ExportOptions
use_cases/
  data_service.py             # Leitura de Excel, casting de tipos, cache de dados
  analysis_service.py         # CRUD de análises e slides
  export_service.py           # Export HTML e LaTeX
infrastructure/
  chart_factory.py            # Geração de gráficos Plotly
  pdf_generator.py            # Geração de PDF via ReportLab
presentation/
  widgets.py                  # render_column_mapper, render_widget_palette, render_visualization_config_dialog
  canvas.py                   # render_canvas, render_slide_navigator
  sidebar.py                  # render_sidebar
  components.py               # Modais: settings, export, welcome, notifications
utils/
  session_state.py            # get_state, set_state, init_session_state
data/                         # Análises persistidas em JSON (local)
```

## Fluxo principal do usuário
1. Upload de arquivo `.xlsx`
2. Tela de mapeamento de colunas → usuário define o tipo de cada coluna (Numérico, Data/Hora, Categoria, Texto ou Ignorar)
3. Sistema aplica casting de tipos e gera o `DataSchema`
4. Usuário adiciona visualizações (gráficos) ao canvas via paleta de widgets
5. Configura cada gráfico (eixos, título, agregação)
6. Exporta em PDF

## Estado atual das tarefas (Sprint 3 + 4)

### ✅ Concluído
- Módulo de upload de Excel
- Tela de login/cadastro
- Integração com banco de dados (Supabase)
- Validação de tipagem (`validate_and_cast_types`)
- Mapeador de colunas (`render_column_mapper`) — nomes originais preservados

### 🔧 Em andamento / Pendente
- [ ] **Filtros Globais** — filtros por coluna aplicados a todos os gráficos do slide
- [ ] **Ajustes de customização nos gráficos** — cores, labels, formatação via UI
- [ ] **Campo de Criação de Medidas** — colunas calculadas (ex: Receita / Qtd = Ticket Médio)
- [ ] **Tabelas Interativas** — tabela com ordenação e paginação
- [ ] **Algoritmo de Mapeamento Dinâmico** — refinamentos no mapper (polido mas pode melhorar)
- [ ] **requirements.txt** — está vazio, precisa ser gerado
- [ ] **Integração das branches** — Victor está responsável

## Observações importantes
- O `render_column_mapper` retorna `{nome_original: ColumnType}` — NÃO renomeia colunas
- `validate_and_cast_types` recebe nomes originais diretamente
- `DataSchema.from_polars` é chamado APÓS o casting para refletir os tipos corretos
- Persistência local em JSON na pasta `data/` (FileAnalysisRepository)
- Free tier: Supabase + Streamlit Cloud (custo zero para MVP)
