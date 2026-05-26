CREATE TABLE IF NOT EXISTS public.breed_mapping (
    cat_api_name TEXT PRIMARY KEY,
    kr_name      TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS public.districts (
    name       TEXT PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
