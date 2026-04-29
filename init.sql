CREATE TABLE users (
	user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
	username varchar(50) UNIQUE NOT NULL,
	email varchar(255) UNIQUE NOT NULL,
	password_hash TEXT NOT NULL,
	created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
)


CREATE TABLE files (
    -- Primary Key
    file_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Foreign Key: Links to the users table
    -- ON DELETE CASCADE ensures if a user is deleted, their files are too
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- File Metadata
    file_name TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size_kb BIGINT NOT NULL,

    -- Recommended: Audit timestamp
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE file_sheets (
    sheet_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES files(file_id) ON DELETE CASCADE,
    sheet_name TEXT NOT NULL
);


CREATE TABLE sheet_columns (
    column_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sheet_id UUID NOT NULL REFERENCES file_sheets(sheet_id) ON DELETE CASCADE,
    column_name TEXT NOT NULL,
    data_type VARCHAR(20) NOT NULL -- e.g., 'Int64', 'Float64', 'String'
);


CREATE TABLE dashboards (
    dashboard_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);


CREATE TABLE visualizations (
    viz_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dashboard_id UUID NOT NULL REFERENCES dashboards(dashboard_id) ON DELETE CASCADE,
    sheet_id UUID NOT NULL REFERENCES file_sheets(sheet_id),
    viz_type VARCHAR(50) NOT NULL, -- e.g., 'bar', 'scatter', 'pie'
    config JSONB NOT NULL,         -- Stores axis, colors, and layout
    created_at TIMESTAMPTZ DEFAULT NOW()
);


-- Explicit index on email (though UNIQUE already creates a b-tree index)
CREATE INDEX idx_users_email ON users(email);

-- Index for faster lookups when querying a specific user's files
CREATE INDEX idx_files_user_id ON files(user_id);

-- Speed up looking up sheets for a specific file
CREATE INDEX idx_file_sheets_file_id ON file_sheets(file_id);

-- Speed up looking up columns for a specific sheet
CREATE INDEX idx_sheet_columns_sheet_id ON sheet_columns(sheet_id);

-- GIN index for high-performance JSONB searching (if you ever need to query by config)
CREATE INDEX idx_visualizations_config ON visualizations USING GIN (config);
