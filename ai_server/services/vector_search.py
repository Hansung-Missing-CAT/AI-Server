from __future__ import annotations

from config import get_supabase


def _to_match(item: dict) -> dict:
    return {
        "petId": item.get("pet_id"),
        "similarity": round(float(item.get("similarity_score", 0)) * 100, 2),
        "pet": {
            "name": item.get("pet_name"),
            "breed": item.get("pet_breed"),
            "location": item.get("pet_location"),
            "photo": item.get("pet_photo"),
        },
    }


def search_similar_pets(
    query_vector: list[float],
    breed_filter: str | None,
    lat: float | None,
    lng: float | None,
    radius_m: int = 2000,
    match_count: int = 3,
) -> list[dict]:
    supabase = get_supabase()
    resp = supabase.rpc(
        "search_similar_pets",
        {
            "query_embedding": query_vector,
            "breed_filter": breed_filter,
            "lat": lat,
            "lng": lng,
            "radius_m": radius_m,
            "match_count": match_count,
        },
    ).execute()
    return [_to_match(x) for x in (resp.data or [])]


def upsert_embedding(pet_id: str, feature_text: str, embedding: list[float]) -> None:
    supabase = get_supabase()
    supabase.table("pet_embeddings").upsert(
        {"pet_id": pet_id, "feature_text": feature_text, "embedding": embedding},
        on_conflict="pet_id",
    ).execute()
    supabase.table("missing_pets").update({"embedding_status": "done"}).eq("id", pet_id).execute()
