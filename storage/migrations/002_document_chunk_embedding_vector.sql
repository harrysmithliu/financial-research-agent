ALTER TABLE document_chunks
ADD COLUMN IF NOT EXISTS embedding_vector vector(512);
