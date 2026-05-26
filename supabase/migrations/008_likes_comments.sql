CREATE TABLE IF NOT EXISTS public.pet_likes (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id     UUID NOT NULL REFERENCES public.missing_pets(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (pet_id, user_id)
);

CREATE TABLE IF NOT EXISTS public.pet_comments (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pet_id     UUID NOT NULL REFERENCES public.missing_pets(id) ON DELETE CASCADE,
    user_id    UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
    content    TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pet_comments_pet_created ON public.pet_comments(pet_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pet_comments_user ON public.pet_comments(user_id);

CREATE OR REPLACE FUNCTION public.increment_pet_likes_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.missing_pets SET likes_count = likes_count + 1 WHERE id = NEW.pet_id;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.decrement_pet_likes_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.missing_pets SET likes_count = GREATEST(likes_count - 1, 0) WHERE id = OLD.pet_id;
    RETURN OLD;
END;
$$;

CREATE OR REPLACE FUNCTION public.increment_pet_comments_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.missing_pets SET comments_count = comments_count + 1 WHERE id = NEW.pet_id;
    RETURN NEW;
END;
$$;

CREATE OR REPLACE FUNCTION public.decrement_pet_comments_count()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.missing_pets SET comments_count = GREATEST(comments_count - 1, 0) WHERE id = OLD.pet_id;
    RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS pet_likes_after_insert ON public.pet_likes;
CREATE TRIGGER pet_likes_after_insert
AFTER INSERT ON public.pet_likes
FOR EACH ROW EXECUTE FUNCTION public.increment_pet_likes_count();

DROP TRIGGER IF EXISTS pet_likes_after_delete ON public.pet_likes;
CREATE TRIGGER pet_likes_after_delete
AFTER DELETE ON public.pet_likes
FOR EACH ROW EXECUTE FUNCTION public.decrement_pet_likes_count();

DROP TRIGGER IF EXISTS pet_comments_after_insert ON public.pet_comments;
CREATE TRIGGER pet_comments_after_insert
AFTER INSERT ON public.pet_comments
FOR EACH ROW EXECUTE FUNCTION public.increment_pet_comments_count();

DROP TRIGGER IF EXISTS pet_comments_after_delete ON public.pet_comments;
CREATE TRIGGER pet_comments_after_delete
AFTER DELETE ON public.pet_comments
FOR EACH ROW EXECUTE FUNCTION public.decrement_pet_comments_count();
