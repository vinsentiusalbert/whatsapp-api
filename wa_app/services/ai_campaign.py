import json

from pydantic import BaseModel

from wa_app.config import settings
from wa_app.services.myads import parse_control_numbers


class CampaignExtraction(BaseModel):
    campaignName: str | None = None
    senderName: str | None = None
    message: str | None = None
    msisdnFile: str | None = None
    msisdnFileName: str | None = None
    deliveryDate: str | None = None
    deliveryTime: str | None = None
    controlNumbers: list[str] | None = None


SYSTEM_PROMPT = """Anda mengekstrak data campaign SMS dari jawaban WhatsApp.
Pertahankan nilai draft lama kecuali pengguna memberi nilai pengganti.
Jangan mengarang nilai yang tidak pernah diberikan.
deliveryDate harus berupa YYYYMMDD dan deliveryTime berupa HHMM jika dapat dipahami.
controlNumbers harus berupa daftar nomor; jika pengguna mengatakan kosong, none, atau '-', gunakan [].
Kembalikan hanya struktur CampaignExtraction."""


def merge_extraction(
    message: str,
    current_draft: dict,
    expected_field: str,
    extracted: dict,
) -> dict:
    """Gabungkan hasil AI dan pastikan jawaban mengisi field yang ditanyakan."""
    updated_draft = {**current_draft, **extracted}
    if expected_field in extracted and extracted[expected_field] is not None:
        return updated_draft

    if expected_field == "controlNumbers":
        updated_draft[expected_field] = parse_control_numbers(message)
    else:
        updated_draft[expected_field] = message.strip()
    return updated_draft


def extract_campaign_draft(
    message: str,
    current_draft: dict,
    expected_field: str,
) -> dict:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY belum diisi")

    # Import lokal membuat mode manual tetap dapat digunakan tanpa OpenAI SDK/key.
    from openai import OpenAI

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.parse(
        model=settings.openai_model,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Draft saat ini:\n"
                    + json.dumps(current_draft, ensure_ascii=False)
                    + "\n\nField yang sedang ditanyakan dan wajib diisi dari jawaban terbaru: "
                    + expected_field
                    + "\n\nJawaban terbaru pengguna:\n"
                    + message
                ),
            },
        ],
        text_format=CampaignExtraction,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise RuntimeError("OpenAI tidak menghasilkan data campaign")
    extracted = {
        key: value
        for key, value in parsed.model_dump().items()
        if value is not None
    }
    return merge_extraction(message, current_draft, expected_field, extracted)
