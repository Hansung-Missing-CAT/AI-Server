CREATE TABLE IF NOT EXISTS public.users (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    name            TEXT,
    phone           TEXT,
    avatar_url      TEXT,
    is_online       BOOLEAN NOT NULL DEFAULT FALSE,
    last_seen_at    TIMESTAMPTZ,
    agree_marketing BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.users (id, name, phone, avatar_url, agree_marketing)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data ->> 'name', NEW.email),
        NEW.raw_user_meta_data ->> 'phone',
        NEW.raw_user_meta_data ->> 'avatar_url',
        COALESCE((NEW.raw_user_meta_data ->> 'agree_marketing')::BOOLEAN, FALSE)
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
AFTER INSERT ON auth.users
FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
