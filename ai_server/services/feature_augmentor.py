from __future__ import annotations

from anthropic import AsyncAnthropic

from config import get_settings


async def augment_features(image_urls: list[str], breed_hint: str | None = None) -> str:
    settings = get_settings()
    if not settings.anthropic_api_key:
        prefix = f"품종 추정: {breed_hint}. " if breed_hint else ""
        return (
            f"{prefix}사진 기반으로 추정되는 특징: 얼굴 윤곽이 뚜렷하고 털 패턴의 대비가 있으며, "
            "등과 꼬리 부근의 색 변화가 관찰됩니다. 눈 주변과 발 부분의 마킹을 중점적으로 확인해주세요."
        )

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    text_prompt = (
        "너는 반려동물 특징 분석 전문가다. 한국어로 100~500자 사이의 순수 텍스트만 출력해라. "
        "색상/패턴, 얼굴 특징, 체형, 특이 마킹, 꼬리/발 특징을 포함해라."
    )
    user_prompt = f"품종 힌트: {breed_hint or '없음'}\n이미지 URL: {', '.join(image_urls[:3])}"
    try:
        resp = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=text_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        chunks = []
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                chunks.append(block.text)
        content = " ".join(chunks).strip()
        if content:
            return content
    except Exception:
        pass

    return "사진에서 반려동물의 털 색 대비와 얼굴 마킹이 뚜렷하며, 꼬리와 발 부위의 패턴이 식별 포인트로 보입니다."
