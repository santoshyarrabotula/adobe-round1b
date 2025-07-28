import os
import json
from pathlib import Path
from datetime import datetime
import re
import fitz  # PyMuPDF
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer, util
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

# Download punkt if not already available (safe for Docker use)
nltk.download("punkt")

# === Setup Paths ===
input_base = Path("/app/input")
output_base = Path("/app/output")
output_base.mkdir(parents=True, exist_ok=True)
subfolders = [f for f in input_base.iterdir() if f.is_dir()]
if not subfolders:
    raise FileNotFoundError("❌ No test case folder found in /app/input")
input_dir = subfolders[0]
test_case_name = input_dir.name

# === Load Context ===
context_file = input_dir / "input_context.json"
with open(context_file, "r", encoding="utf-8") as f:
    context = json.load(f)

persona = context["persona"]["role"]
job = context["job_to_be_done"]["task"]
query = f"{persona} - {job}"

# === Load Model ===
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
query_embedding = model.encode(query, convert_to_tensor=True)

# === Boosting Keywords ===
job_terms = [w.lower() for w in re.findall(r"\w+", persona + " " + job)
             if w.lower() not in ENGLISH_STOP_WORDS and len(w) > 3]

# === Heading Detection Function ===
def detect_headings(pdf_path):
    with fitz.open(pdf_path) as doc:
        heading_candidates = []
        for page_num, page in enumerate(doc, start=1):
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                for line in block["lines"]:
                    text = " ".join(span["text"].strip() for span in line["spans"])
                    if not text or re.fullmatch(r"\d+", text):
                        continue
                    largest_font = max(span["size"] for span in line["spans"])
                    is_bold = any("bold" in span["font"].lower() or "black" in span["font"].lower()
                                  for span in line["spans"])
                    heading_candidates.append({
                        "text": text.strip(),
                        "font_size": largest_font,
                        "bold": is_bold,
                        "page": page_num
                    })

        if not heading_candidates:
            return []

        # Normalize font size ranks
        sizes = sorted(set(c["font_size"] for c in heading_candidates), reverse=True)
        size_to_rank = {size: idx + 1 for idx, size in enumerate(sizes)}
        for c in heading_candidates:
            c["rank"] = size_to_rank[c["font_size"]]

        # Keep top-ranked headings (rank <= 4)
        headings = [h for h in heading_candidates if h["rank"] <= 4]
        return headings

# === Extract & Save Headings Automatically ===
doc_headings = {}
for doc in context["documents"]:
    pdf_path = input_dir / doc["filename"]
    headings = detect_headings(pdf_path)
    doc_headings[doc["filename"]] = headings

# === Extract Chunks ===
chunks = []
for doc in context["documents"]:
    filename = doc["filename"]
    file_path = input_dir / filename
    with fitz.open(file_path) as pdf:
        for page_num, page in enumerate(pdf, start=1):
            blocks = page.get_text("blocks")
            for block in blocks:
                text = block[4].strip()
                if len(text.split()) >= 30:
                    lowered = text.lower()
                    boost = sum(1 for kw in job_terms if kw in lowered)
                    chunks.append({
                        "document": filename,
                        "text": text,
                        "page_number": page_num,
                        "boost": boost
                    })

# === Rank Chunks ===
all_texts = [c["text"] for c in chunks]
embeddings = model.encode(all_texts, convert_to_tensor=True)
cosine_scores = util.cos_sim(query_embedding, embeddings)[0]
boosted_scores = [(float(score) + 0.05 * chunks[i]["boost"], i) for i, score in enumerate(cosine_scores)]
boosted_scores.sort(reverse=True)

# === Extract Section Title from Headings ===
def extract_section_title(page_number, doc_headings, doc_name):
    candidates = [h for h in doc_headings.get(doc_name, []) if h["page"] == page_number]
    if candidates:
        return candidates[0]["text"].strip()
    return f"Page {page_number}"

# === Generate Output ===
seen = set()
rank = 1
output = {
    "metadata": {
        "input_documents": [doc["filename"] for doc in context["documents"]],
        "persona": persona,
        "job_to_be_done": job,
        "processing_timestamp": datetime.now().isoformat()
    },
    "extracted_sections": [],
    "subsection_analysis": []
}

for score, idx in boosted_scores:
    chunk = chunks[idx]
    key = (chunk["document"], chunk["page_number"])
    if key in seen:
        continue
    seen.add(key)

    section_title = extract_section_title(chunk["page_number"], doc_headings, chunk["document"])
    refined_text = re.sub(r"\s+", " ", chunk["text"].replace("\n", " ")).strip()

    output["extracted_sections"].append({
        "document": chunk["document"],
        "section_title": section_title,
        "importance_rank": rank,
        "page_number": chunk["page_number"]
    })
    output["subsection_analysis"].append({
        "document": chunk["document"],
        "refined_text": refined_text,
        "page_number": chunk["page_number"]
    })

    rank += 1
    if rank > 5:
        break

# === Save Output ===
output_path = output_base / f"{test_case_name}.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Output written to: {output_path}")
