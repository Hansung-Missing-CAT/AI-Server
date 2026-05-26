CREATE TABLE IF NOT EXISTS public.tips (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    status      TEXT NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'done', 'failed')),
    image_urls  TEXT[] NOT NULL DEFAULT '{}',
    results     JSONB,
    progress    INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    error_msg   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tips_user_created ON public.tips(user_id, created_at DESC);

DROP TRIGGER IF EXISTS set_tips_updated_at ON public.tips;
CREATE TRIGGER set_tips_updated_at
BEFORE UPDATE ON public.tips
FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();
