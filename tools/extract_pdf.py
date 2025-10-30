import sys
from PyPDF2 import PdfReader

def main():
    if len(sys.argv) < 3:
        print("Usage: extract_pdf.py <input.pdf> <output.txt>")
        sys.exit(1)
    inp = sys.argv[1]
    out = sys.argv[2]
    r = PdfReader(inp)
    with open(out, 'w', encoding='utf-8', errors='ignore') as f:
        for i, page in enumerate(r.pages):
            try:
                text = page.extract_text() or ''
            except Exception as e:
                text = f"[PAGE {i+1} ERROR] {e}"
            f.write(text)
            f.write(f"\n\n--- PAGE {i+1} ---\n\n")

if __name__ == '__main__':
    main()
