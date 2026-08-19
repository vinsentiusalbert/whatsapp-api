import json
import re

from wa_app.utils import normalize_phone


MYADS_FORM_MESSAGE = """Halo, Anda masuk ke pembuatan campaign MyAds SMS Broadcast.

Silakan balas dengan format berikut dan jangan mengubah nomor field:

1. Campaign Name: Promo Agustus
2. Sender Name: MyAds
3. Message: Dapatkan promo spesial hari ini.
4. MSISDN File: <salin nilai encrypted_file dari respons API Upload Content>
5. MSISDN File Name: Template_123.csv
6. Delivery Date: 20260818
7. Delivery Time: 0900
8. Control Numbers: 6281234567890,6281111111111

Catatan:
- Delivery Date harus YYYYMMDD
- Delivery Time harus HHMM (24 jam)
- Control Numbers boleh dikosongkan dengan tanda -
- MSISDN File bukan nama/path file dan bukan isi CSV. Upload dahulu file daftar
  nomor tujuan melalui API Upload Content, lalu salin nilai `encrypted_file`
  dari respons API tersebut secara lengkap tanpa tanda kutip.
- MSISDN File Name adalah nama file aslinya, contoh Template_123.csv.
- Ketik CANCEL untuk membatalkan
"""

MYADS_MODE_MESSAGE = """Pilih cara membuat campaign MyAds:

1. AI - jawab pertanyaan satu per satu
2. Manual - kirim form 8 field sekaligus

Balas dengan angka 1/2, atau ketik MYADS AI / MYADS MANUAL.
Ketik CANCEL untuk membatalkan."""

AI_FIELD_QUESTIONS = {
    "campaignName": "Apa nama campaign yang ingin dibuat?",
    "senderName": "Apa Sender Name yang ingin digunakan?",
    "message": "Apa isi pesan SMS campaign-nya?",
    "msisdnFile": """Masukkan nilai MSISDN File.

Cara mendapatkannya:
1. Siapkan file daftar nomor tujuan campaign.
2. Upload file tersebut melalui API MyAds Upload Content.
3. Dari respons API, cari field `encrypted_file`.
4. Salin seluruh nilainya ke sini tanpa tanda kutip.

Catatan: yang dikirim bukan file CSV, bukan nama/path file, dan bukan isi daftar nomornya. Contoh jawaban: eyJ...hasil_encrypted_file...""",
    "msisdnFileName": "Apa nama file MSISDN-nya? Contoh: Template_123.csv",
    "deliveryDate": "Kapan campaign dikirim? Gunakan format YYYYMMDD, contoh 20260818.",
    "deliveryTime": "Jam berapa campaign dikirim? Gunakan format HHMM, contoh 0900.",
    "controlNumbers": "Masukkan Control Numbers dipisahkan koma, atau balas '-' jika kosong.",
}

AI_REQUIRED_FIELDS = tuple(AI_FIELD_QUESTIONS)


def extract_numbered_field(text: str, number: int):
    pattern = rf"(?im)^\s*{number}\s*[\.\)\-:]?\s*(?:[^:\n]+:\s*)?(.*?)\s*$"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else None


def parse_control_numbers(value: str | None) -> list[str]:
    if value is None:
        return []
    value = value.strip()
    if not value or value.lower() in {"-", "none", "null", "kosong"}:
        return []
    return [phone for item in re.split(r"[,;\n]+", value)
            if (phone := normalize_phone(item))]


def parse_sms_broadcast_form(text: str):
    campaign_name = extract_numbered_field(text, 1)
    sender_name = extract_numbered_field(text, 2)
    sms_message = extract_numbered_field(text, 3)
    msisdn_file = extract_numbered_field(text, 4)
    msisdn_file_name = extract_numbered_field(text, 5)
    delivery_date = extract_numbered_field(text, 6)
    delivery_time = extract_numbered_field(text, 7)
    control_numbers = parse_control_numbers(extract_numbered_field(text, 8))
    errors = []

    required = (
        (campaign_name, "Field 1 Campaign Name wajib diisi"),
        (sender_name, "Field 2 Sender Name wajib diisi"),
        (sms_message, "Field 3 Message wajib diisi"),
        (msisdn_file, "Field 4 MSISDN File wajib diisi"),
        (msisdn_file_name, "Field 5 MSISDN File Name wajib diisi"),
        (delivery_date, "Field 6 Delivery Date wajib diisi"),
        (delivery_time, "Field 7 Delivery Time wajib diisi"),
    )
    errors.extend(message for value, message in required if not value)

    if campaign_name and len(campaign_name) > 100:
        errors.append("Campaign Name maksimal 100 karakter")
    if sender_name and len(sender_name) > 50:
        errors.append("Sender Name maksimal 50 karakter")
    if delivery_date and not re.fullmatch(r"\d{8}", delivery_date):
        errors.append("Delivery Date harus format YYYYMMDD, contoh 20260818")
    if delivery_time:
        if not re.fullmatch(r"\d{4}", delivery_time):
            errors.append("Delivery Time harus format HHMM, contoh 0900")
        elif int(delivery_time[:2]) > 23 or int(delivery_time[2:]) > 59:
            errors.append("Delivery Time tidak valid")
    errors.extend(
        f"Control Number terlalu panjang: {phone}"
        for phone in control_numbers if len(phone) > 15
    )

    if errors:
        return None, errors
    return {
        "campaignName": campaign_name,
        "channel": "SMS",
        "senderName": sender_name,
        "message": sms_message,
        "msisdnFile": msisdn_file,
        "msisdnFileName": msisdn_file_name,
        "mmsFile": "",
        "mmsSubject": "",
        "deliveries": [{"deliveryDate": delivery_date, "deliveryTime": delivery_time}],
        "controlNumbers": control_numbers,
    }, []


def format_payload_for_whatsapp(payload: dict) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


def validate_campaign_draft(draft: dict):
    """Validasi draft AI dan kembalikan field pertama yang perlu diperbaiki."""
    for field in AI_REQUIRED_FIELDS:
        if field not in draft or draft[field] is None or (
            field != "controlNumbers" and not str(draft[field]).strip()
        ):
            return field, AI_FIELD_QUESTIONS[field]

    if len(str(draft["campaignName"])) > 100:
        return "campaignName", "Campaign Name maksimal 100 karakter. Silakan masukkan nama lain."
    if len(str(draft["senderName"])) > 50:
        return "senderName", "Sender Name maksimal 50 karakter. Silakan masukkan nama lain."
    if not re.fullmatch(r"\d{8}", str(draft["deliveryDate"])):
        return "deliveryDate", AI_FIELD_QUESTIONS["deliveryDate"]
    delivery_time = str(draft["deliveryTime"])
    if not re.fullmatch(r"\d{4}", delivery_time):
        return "deliveryTime", AI_FIELD_QUESTIONS["deliveryTime"]
    if int(delivery_time[:2]) > 23 or int(delivery_time[2:]) > 59:
        return "deliveryTime", "Delivery Time tidak valid. Masukkan jam format HHMM, contoh 0900."
    for phone in draft["controlNumbers"]:
        if len(normalize_phone(phone)) > 15:
            return "controlNumbers", f"Control Number terlalu panjang: {phone}. Silakan perbaiki."
    return None, None


def build_campaign_from_draft(draft: dict) -> dict:
    return {
        "campaignName": str(draft["campaignName"]).strip(),
        "channel": "SMS",
        "senderName": str(draft["senderName"]).strip(),
        "message": str(draft["message"]).strip(),
        "msisdnFile": str(draft["msisdnFile"]).strip(),
        "msisdnFileName": str(draft["msisdnFileName"]).strip(),
        "mmsFile": "",
        "mmsSubject": "",
        "deliveries": [{
            "deliveryDate": str(draft["deliveryDate"]),
            "deliveryTime": str(draft["deliveryTime"]),
        }],
        "controlNumbers": [normalize_phone(phone) for phone in draft["controlNumbers"]],
    }
