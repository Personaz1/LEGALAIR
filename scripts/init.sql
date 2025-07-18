-- Legal ASI Database Schema
-- Version: 0.1.0-preGPU

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    file_size INTEGER NOT NULL,
    mime_type VARCHAR(100),
    storage_path TEXT NOT NULL,
    
    -- OCR results
    ocr_text TEXT,
    ocr_confidence FLOAT,
    ocr_processing_time FLOAT,
    
    -- Classification results
    document_type VARCHAR(50),
    classification_confidence FLOAT,
    classification_processing_time FLOAT,
    
    -- Overall processing status
    processing_status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Named entities table
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_text TEXT NOT NULL,
    entity_type VARCHAR(50) NOT NULL,
    start_position INTEGER NOT NULL,
    end_position INTEGER NOT NULL,
    confidence FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Processing jobs table
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL, -- 'ocr', 'classification', 'ner', 'full'
    status VARCHAR(20) DEFAULT 'pending',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    processing_time FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Annotation data table (for Label Studio integration)
CREATE TABLE annotations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    annotation_data JSONB NOT NULL,
    annotator_id VARCHAR(100),
    annotation_type VARCHAR(50), -- 'doc_type', 'entities', 'full'
    label_studio_task_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Model performance metrics
CREATE TABLE model_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    metric_type VARCHAR(50) NOT NULL, -- 'accuracy', 'f1', 'precision', 'recall'
    metric_value FLOAT NOT NULL,
    dataset_size INTEGER,
    evaluation_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Indexes for performance
CREATE INDEX idx_documents_hash ON documents(file_hash);
CREATE INDEX idx_documents_type ON documents(document_type);
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_created ON documents(created_at);

CREATE INDEX idx_entities_document ON entities(document_id);
CREATE INDEX idx_entities_type ON entities(entity_type);
CREATE INDEX idx_entities_text_gin ON entities USING gin(entity_text gin_trgm_ops);

CREATE INDEX idx_jobs_document ON processing_jobs(document_id);
CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_type ON processing_jobs(job_type);

CREATE INDEX idx_annotations_document ON annotations(document_id);
CREATE INDEX idx_annotations_type ON annotations(annotation_type);

-- Full-text search index for OCR text
CREATE INDEX idx_documents_ocr_text_gin ON documents USING gin(to_tsvector('russian', ocr_text));

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_annotations_updated_at BEFORE UPDATE ON annotations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Sample data for development
INSERT INTO documents (filename, file_hash, file_size, mime_type, storage_path, processing_status) VALUES
('sample_bill.pdf', 'hash123', 1024, 'application/pdf', '/data/raw/sample_bill.pdf', 'pending'),
('sample_fine.jpg', 'hash456', 2048, 'image/jpeg', '/data/raw/sample_fine.jpg', 'pending');

COMMIT; 