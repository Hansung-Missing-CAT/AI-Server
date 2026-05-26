CREATE TABLE IF NOT EXISTS public.pet_embeddings (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id       UUID NOT NULL REFERENCES public.missing_pets(id) ON DELETE CASCADE,
    embedding    VECTOR(768) NOT NULL,
    feature_text TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (pet_id)
);

CREATE INDEX IF NOT EXISTS idx_pet_embeddings_embedding_hnsw
ON public.pet_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
