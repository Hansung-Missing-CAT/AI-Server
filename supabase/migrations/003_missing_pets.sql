CREATE TABLE IF NOT EXISTS public.missing_pets (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              TEXT NOT NULL,
    breed             TEXT NOT NULL,
    age               INTEGER,
    gender            TEXT CHECK (gender IN ('남', '여')),
    color             TEXT,
    location          TEXT,
    district          TEXT,
    detail_address    TEXT,
    last_seen         DATE,
    lost_time         TIME,
    reward            INTEGER DEFAULT 0 CHECK (reward >= 0),
    photo             TEXT,
    photos            TEXT[] NOT NULL DEFAULT '{}',
    description       TEXT,
    status            TEXT NOT NULL DEFAULT '실종' CHECK (status IN ('실종', '찾음')),
    reporter_id       UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    views             INTEGER NOT NULL DEFAULT 0 CHECK (views >= 0),
    likes_count       INTEGER NOT NULL DEFAULT 0 CHECK (likes_count >= 0),
    comments_count    INTEGER NOT NULL DEFAULT 0 CHECK (comments_count >= 0),
    latitude          DOUBLE PRECISION,
    longitude         DOUBLE PRECISION,
    embedding_status  TEXT NOT NULL DEFAULT 'pending' CHECK (embedding_status IN ('pending', 'done', 'failed')),
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_missing_pets_district ON public.missing_pets(district);
CREATE INDEX IF NOT EXISTS idx_missing_pets_status ON public.missing_pets(status);
CREATE INDEX IF NOT EXISTS idx_missing_pets_created_at ON public.missing_pets(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_missing_pets_lat_lng ON public.missing_pets(latitude, longitude);
CREATE INDEX IF NOT EXISTS idx_missing_pets_breed ON public.missing_pets(breed);
CREATE INDEX IF NOT EXISTS idx_missing_pets_name_trgm ON public.missing_pets USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_missing_pets_breed_trgm ON public.missing_pets USING GIN (breed gin_trgm_ops);

CREATE OR REPLACE FUNCTION public.set_updated_at()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS set_missing_pets_updated_at ON public.missing_pets;
CREATE TRIGGER set_missing_pets_updated_at
BEFORE UPDATE ON public.missing_pets
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
