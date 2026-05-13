CREATE TABLE IF NOT EXISTS ingestion_job_records (
    job_id TEXT PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    source_ids JSONB NOT NULL,
    status TEXT NOT NULL,
    document_count INTEGER NOT NULL,
    structured_record_count INTEGER NOT NULL,
    eval_case_count INTEGER NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    error_message TEXT,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    source_uri TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS structured_records (
    record_key TEXT PRIMARY KEY,
    record_type TEXT NOT NULL,
    source_uri TEXT,
    metadata JSONB NOT NULL,
    payload JSONB NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluation_cases (
    case_id TEXT PRIMARY KEY,
    task_type TEXT NOT NULL,
    question TEXT NOT NULL,
    metadata JSONB NOT NULL,
    payload JSONB NOT NULL
);

