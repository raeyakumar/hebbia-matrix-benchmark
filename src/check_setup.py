"""Check that the Gemini key is configured (never prints it) and list usable models.

models.list is a free metadata call; it makes no paid generation request.
Usage: python check_setup.py
"""
from config import MODEL, ROOT, gemini_key


def main():
    env = ROOT / ".env"
    print(f".env present: {env.exists()}")
    k = gemini_key()
    if not k:
        print("GEMINI_API_KEY: NOT SET -> copy .env.example to .env and paste the key after GEMINI_API_KEY=")
        return
    print(f"GEMINI_API_KEY: set ({len(k)} characters; value not shown)")
    from google import genai
    client = genai.Client(api_key=k)
    names = sorted(m.name.replace("models/", "") for m in client.models.list()
                   if "generateContent" in (m.supported_actions or []))
    flash_pro = [n for n in names if n.startswith("gemini") and ("flash" in n or "pro" in n)]
    print("generateContent models (gemini flash/pro):")
    for n in flash_pro:
        print("   ", n, "<- configured" if n == MODEL else "")
    if MODEL not in names:
        print(f"WARNING: configured model {MODEL!r} is not available to this key; set BENCH_MODEL in .env")


if __name__ == "__main__":
    main()
