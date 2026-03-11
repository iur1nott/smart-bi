# Dashboard Builder

A Streamlit web application that allows data analysts with little to no knowledge of Excel to build dashboards, tables, and write comments, similar to a simpler and more intuitive Power BI, with PDF export functionality.

## Features

- **XLSX File Upload**: Upload Excel files to start building dashboards
- **Automatic Column Type Detection**: Automatically identifies categorical and numerical columns
- **Multiple Visualization Types**:
  - Bar Charts
  - Line Charts
  - Pie Charts
  - Area Charts
  - Scatter Plots
  - Histograms
  - Box Plots
  - Heatmaps
  - Tables
  - Metric Cards
- **Slide Management**: Create and manage multiple slides/pages
- **Comments**: Add comments to any visualization
- **Export to PDF/LaTeX/HTML**: Export your dashboards to various formats
- **Analysis History**: Keep track of previous analyses
- **Settings**: Customize appearance and export options

## Architecture

This application follows Clean Architecture principles (SOLID and GRASP):

```
dashboard_builder/
├── app.py                    # Main Streamlit entry point
├── requirements.txt          # Python dependencies
├── domain/                   # Domain layer (entities, value objects)
│   ├── __init__.py
│   ├── entities.py          # Core business entities
│   └── value_objects.py     # Value objects
├── use_cases/               # Application layer
│   ├── __init__.py
│   ├── analysis_service.py  # Analysis management
│   ├── export_service.py    # PDF export service
│   └── data_service.py      # Data processing service
├── infrastructure/          # Infrastructure layer
│   ├── __init__.py
│   ├── chart_factory.py     # Chart creation
│   └── pdf_generator.py     # PDF generation
├── presentation/            # Presentation layer
│   ├── __init__.py
│   ├── sidebar.py          # Sidebar components
│   ├── canvas.py           # Main canvas/slide area
│   ├── widgets.py          # Visualization widgets
│   └── components.py       # UI components
├── utils/
│   ├── __init__.py
│   └── session_state.py    # Session state management
└── data/                    # Data storage directory
```

## Technology Stack

- **Streamlit**: Web framework for the UI
- **Polars**: High-performance DataFrame library for data processing
- **Plotly**: Interactive charting library
- **ReportLab**: PDF generation
- **LaTeX**: LaTeX document generation for export

## Installation

1. Create and activate the virtual environment:
   ```bash
   cd /home/z/my-project/dashboard_builder
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

```bash
./run.sh
```

Or directly with:
```bash
./venv/bin/streamlit run app.py --server.port 8501
```

The application will be available at http://localhost:8501

## Usage

1. **Start New Analysis**: Click "➕ New" in the sidebar to start a new analysis
2. **Upload XLSX File**: Select and upload an Excel file
3. **Add Visualizations**: Use the widget sidebar to add charts, tables, or metric cards
4. **Configure Charts**: Set X-axis, Y-axis, colors, and other options
5. **Add Comments**: Add comments to any visualization
6. **Manage Slides**: Add, delete, or navigate between slides
7. **Export**: Click "Export" to generate PDF, LaTeX, or HTML output

## Clean Architecture Layers

### Domain Layer
- **Entities**: Analysis, Slide, Visualization, UserSession
- **Value Objects**: ColumnType, VisualizationType, ExportFormat, ChartColors

### Use Cases Layer
- **AnalysisService**: Manages analysis sessions and slides
- **DataService**: Handles data loading, filtering, and aggregation
- **ExportService**: Handles export to various formats

### Infrastructure Layer
- **ChartFactory**: Creates Plotly charts
- **PDFGenerator**: Generates PDFs using ReportLab

### Presentation Layer
- **sidebar.py**: Main sidebar with actions, history, and settings
- **canvas.py**: Slide editing area
- **widgets.py**: Visualization configuration forms
- **components.py**: Reusable UI components

## License

MIT License
