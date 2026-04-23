# SmartXL - Dashboard Builder

A modern, clean architecture dashboard builder application that allows users to create professional dashboards from Excel data. Designed for deployment on Streamlit Community Cloud.

## Features

- **User Authentication**: Secure login and registration with JWT tokens
- **Excel Data Loading**: Support for XLSX and XLS file formats using Polars (no pandas)
- **S3 Storage**: Files stored in S3-compatible storage (Supabase, AWS, MinIO)
- **Visualization Creation**: Multiple chart types including:
  - Bar charts
  - Line charts
  - Pie charts
  - Area charts
  - Scatter plots
  - Histograms
  - Box plots
  - Tables
  - Metric cards
- **Dashboard Management**: Organize visualizations in dashboards
- **Export Options**: Export to PDF, HTML, and LaTeX formats
- **PostgreSQL Integration**: Persistent storage with Supabase/PostgreSQL
- **Streamlit Cloud Ready**: Configured for easy deployment

## Architecture

This application follows Clean Architecture principles with:

- **Domain Layer**: Core business entities and value objects
- **Use Cases Layer**: Application services and business logic
- **Infrastructure Layer**: External services and implementations
- **Presentation Layer**: Streamlit UI components

## Deployment

### Streamlit Community Cloud

1. Fork this repository to your GitHub account

2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in

3. Create a new app and select your repository

4. Set the main file path to `app.py`

5. Configure secrets in the Streamlit Cloud dashboard:
   - Go to your app settings > Secrets
   - Paste the contents of `.streamlit/secrets.toml.example`
   - Fill in your actual credentials

6. Deploy!

### Required Secrets Configuration

Create a `.streamlit/secrets.toml` file with the following structure:

```toml
# Database (Supabase recommended)
[database]
url = "postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# S3 Storage (Supabase Storage or AWS S3)
[storage]
endpoint_url = "https://YOUR_PROJECT.supabase.co/storage/v1/s3"
access_key = "YOUR_ACCESS_KEY"
secret_key = "YOUR_SECRET_KEY"
bucket_name = "smartxl-files"

# JWT Authentication
[jwt]
secret_key = "your-secure-random-string"
```

## Local Development

### Option 1: Direct Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/gurgel-bi.git
cd gurgel-bi
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure secrets:
```bash
# Copy the example file
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit with your credentials
```

5. Run the application:
```bash
streamlit run app.py
```

### Option 2: Docker

1. Clone and navigate to the repository

2. Create `.streamlit/secrets.toml` with your credentials

3. Run with Docker Compose:
```bash
docker-compose up -d
```

4. Access at: http://localhost:8501

## Configuration Reference

### Secrets (secrets.toml)

| Section | Key | Description |
|---------|-----|-------------|
| `database` | `url` | PostgreSQL connection string |
| `database` | `pool_size` | Connection pool size |
| `storage` | `endpoint_url` | S3 endpoint (Supabase/AWS) |
| `storage` | `access_key` | S3 access key |
| `storage` | `secret_key` | S3 secret key |
| `storage` | `bucket_name` | S3 bucket name |
| `jwt` | `secret_key` | JWT signing key |
| `jwt` | `algorithm` | JWT algorithm (HS256) |
| `session` | `timeout_hours` | Session timeout |
| `security` | `password_min_length` | Minimum password length |

## Database Schema

The application uses the following PostgreSQL tables:

- **users**: User accounts and authentication
- **files**: Uploaded file metadata with S3 paths
- **file_sheets**: Sheets within Excel files
- **sheet_columns**: Column metadata and data types
- **dashboards**: User dashboards
- **visualizations**: Chart configurations (stored as JSONB)

See `init.sql` for the complete schema definition.

## Usage

1. **Register/Login**: Create an account or log in
2. **Create Dashboard**: Click "Nova Análise" to start
3. **Upload Data**: Upload an Excel file (.xlsx or .xls)
4. **Add Visualizations**: Select chart types and configure columns
5. **Save**: Dashboard auto-saves to PostgreSQL
6. **Export**: Export to PDF, HTML, or LaTeX

## Project Structure

```
gurgel-bi/
├── app.py                    # Main application entry point
├── config.py                 # Configuration management
├── .streamlit/
│   ├── secrets.toml          # Secrets (not in git)
│   └── secrets.toml.example  # Template
├── domain/                   # Domain layer
│   ├── entities.py           # Business entities
│   ├── value_objects.py      # Value objects
│   └── repositories.py       # Repository interfaces
├── use_cases/                # Application services
│   ├── auth_service.py
│   ├── file_service.py
│   ├── dashboard_service.py
│   ├── data_service.py
│   └── export_service.py
├── infrastructure/           # External implementations
│   ├── database.py
│   ├── models.py
│   ├── auth/
│   ├── repositories/
│   ├── storage/
│   │   └── s3_client.py      # S3 storage client
│   ├── chart_factory.py
│   └── pdf_generator.py
├── presentation/             # UI components
│   ├── login.py
│   ├── sidebar.py
│   ├── canvas.py
│   ├── widget_palette.py
│   └── components.py
├── utils/                    # Utility functions
├── init.sql                  # Database schema
├── requirements.txt
└── README.md
```

## Technology Stack

- **Frontend**: Streamlit
- **Data Processing**: Polars (no pandas dependency)
- **Database**: PostgreSQL (via SQLAlchemy)
- **Storage**: S3-compatible (Supabase Storage, AWS S3, MinIO)
- **Authentication**: JWT with bcrypt
- **Visualization**: Plotly
- **Export**: ReportLab (PDF), Jinja2 (templates)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Formatting

```bash
black .
ruff check .
```

### Type Checking

```bash
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Streamlit](https://streamlit.io/) for the amazing UI framework
- [Polars](https://pola.rs/) for fast data processing
- [Plotly](https://plotly.com/) for interactive visualizations
- [SQLAlchemy](https://www.sqlalchemy.org/) for database abstraction
- [Supabase](https://supabase.com/) for PostgreSQL and S3 storage
