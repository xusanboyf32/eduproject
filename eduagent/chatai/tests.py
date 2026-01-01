# tests.py faylini SHU KOD BILAN almashtiring:
from google import genai

API_KEY = 'AIzaSyAj2b0xEJ1Ri3YpNWywjJX8xEGyPdO3kqM'

try:
    client = genai.Client(api_key=API_KEY)

    # 1-VARIANT: gemini-2.0-flash (BEPUL, ISHLASHI KERAK)
    response = client.models.generate_content(
        model="gemini-2.0-flash-001",  # ✅ TO'G'RI MODEL
        contents="Salom, menga javob ber o'zbekcha"
    )

    print("✅ ISHLAYAPTI! (gemini-2.0-flash)")
    print("Javob:", response.text)

except Exception as e:
    print("❌ XATO:", e)

    # 2-VARIANT: Agar yuqoridagi ishlamasa, boshqa model
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",  # ✅ IKKINCHI VARIANT
            contents="Salom"
        )
        print("\n✅ gemini-2.5-flash ISHLAYAPTI!")
        print("Javob:", response.text)
    except Exception as e2:
        print("❌ Ikkala model ham ishlamadi:", e2)



