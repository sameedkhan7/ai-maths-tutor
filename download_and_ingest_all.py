import os
import urllib.request
import zipfile
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TARGET_PDF_DIR = BASE_DIR / "data" / "raw_pdfs"
TARGET_PDF_DIR.mkdir(parents=True, exist_ok=True)

# 📚 Class 10, 11, 12 Complete Books NCERT Official ZIP URLs
BOOKS_TO_DOWNLOAD = {
    "Class_10_Maths": "https://ncert.nic.in/textbook/pdf/jemh1dd.zip",
    "Class_11_Maths": "https://ncert.nic.in/textbook/pdf/kemh1dd.zip",
    "Class_12_Maths_Part1": "https://ncert.nic.in/textbook/pdf/lemh1dd.zip",
    "Class_12_Maths_Part2": "https://ncert.nic.in/textbook/pdf/lemh2dd.zip",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://ncert.nic.in/textbook.php"
}

def run_download_and_ingest():
    print("=" * 65)
    print("🚀 1-CLICK ALL NCERT MATHS DOWNLOAD + RAG INGEST (10th, 11th, 12th)")
    print("=" * 65)

    for book_name, url in BOOKS_TO_DOWNLOAD.items():
        temp_zip = BASE_DIR / f"{book_name}.zip"
        print(f"\n📥 Downloading {book_name}...")
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req) as resp, open(temp_zip, "wb") as f:
                f.write(resp.read())
            print(f"✅ Downloaded: {book_name}")

            print(f"📂 Extracting PDFs directly into: data/raw_pdfs/...")
            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                for file_info in zip_ref.infolist():
                    if file_info.filename.lower().endswith(".pdf"):
                        filename = os.path.basename(file_info.filename)
                        if filename:
                            source = zip_ref.open(file_info)
                            target = open(TARGET_PDF_DIR / f"{book_name}_{filename}", "wb")
                            with source, target:
                                target.write(source.read())
            print(f"✨ Extracted and saved to data/raw_pdfs!")

            if temp_zip.exists():
                os.remove(temp_zip)

        except Exception as e:
            print(f"❌ Error with {book_name}: {e}")

    # Step 2: Automatic RAG ingestion
    print("\n" + "=" * 65)
    print("⚡ ALL DOWNLOADED! NOW STARTING AUTO-INGESTION INTO RAG DATABASE...")
    print("=" * 65)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(BASE_DIR)
    subprocess.run(["python", "-m", "backend.rag.ingest"], env=env, cwd=str(BASE_DIR))

    print("\n🎉 MISSION COMPLETE! Class 10th, 11th & 12th are now in your RAG Vector DB!")

if __name__ == "__main__":
    run_download_and_ingest()
