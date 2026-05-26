CREATE OR REPLACE FUNCTION public.search_similar_pets(
    query_embedding VECTOR(768),
    breed_filter TEXT DEFAULT NULL,
    lat DOUBLE PRECISION DEFAULT NULL,
    lng DOUBLE PRECISION DEFAULT NULL,
    radius_m DOUBLE PRECISION DEFAULT NULL,
    match_count INTEGER DEFAULT 3
)
RETURNS TABLE (
    pet_id UUID,
    pet_name TEXT,
    pet_breed TEXT,
    pet_location TEXT,
    pet_photo TEXT,
    similarity_score DOUBLE PRECISION
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        mp.id AS pet_id,
        mp.name AS pet_name,
        mp.breed AS pet_breed,
        mp.location AS pet_location,
        mp.photo AS pet_photo,
        1 - (pe.embedding <=> query_embedding) AS similarity_score
    FROM public.pet_embeddings pe
    JOIN public.missing_pets mp ON mp.id = pe.pet_id
    WHERE
        (breed_filter IS NULL OR mp.breed = breed_filter)
        AND (
            lat IS NULL OR lng IS NULL OR radius_m IS NULL
            OR (
                6371000 * acos(
                    LEAST(
                        1,
                        cos(radians(lat)) * cos(radians(mp.latitude)) *
                        cos(radians(mp.longitude) - radians(lng)) +
                        sin(radians(lat)) * sin(radians(mp.latitude))
                    )
                )
            ) <= radius_m
        )
    ORDER BY pe.embedding <=> query_embedding
    LIMIT match_count;
$$;
