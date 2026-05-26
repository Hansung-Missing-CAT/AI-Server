CREATE OR REPLACE FUNCTION public.increment_pet_views(
    p_pet_id UUID,
    p_delta INTEGER DEFAULT 1
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    UPDATE public.missing_pets
    SET views = COALESCE(views, 0) + GREATEST(COALESCE(p_delta, 1), 1)
    WHERE id = p_pet_id;
END;
$$;
