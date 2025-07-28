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

nltk.data.path.append("/root/nltk_data")

input_base = Path("/app/input")
output_base = Path("/app/output")
output_base.mkdir(parents=True, exist_ok=True)

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def process_test_case(input_dir):
    test_case_name = input_dir.name
    output_path = output_base / f"{test_case_name}.json"
    if output_path.exists():
        print(f"⚠️ Skipping {test_case_name}, output already exists.")
        return

    context_file = input_dir / "input_context.json"
    if not context_file.exists():
        print(f"❌ No input_context.json found in {test_case_name}, skipping.")
        return

    with open(context_file, "r", encoding="utf-8") as f:
        context = json.load(f)

    persona = context["persona"]["role"]
    job = context["job_to_be_done"]["task"]
    query = f"{persona} - {job}"
    query_embedding = model.encode(query, convert_to_tensor=True)
    job_terms = [w.lower() for w in re.findall(r"\w+", persona + " " + job)
                 if w.lower() not in ENGLISH_STOP_WORDS and len(w) > 3]

    doc_headings = {}
    for doc in context["documents"]:
        json_path = input_dir / (Path(doc["filename"]).stem + ".json")
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as jf:
                data = json.load(jf)
                doc_headings[doc["filename"]] = data.get("outline", [])

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

    all_texts = [c["text"] for c in chunks]
    embeddings = model.encode(all_texts, convert_to_tensor=True)
    cosine_scores = util.cos_sim(query_embedding, embeddings)[0]
    boosted_scores = [(float(score) + 0.05 * chunks[i]["boost"], i) for i, score in enumerate(cosine_scores)]
    boosted_scores.sort(reverse=True)

    def extract_section_title(text, doc_headings, doc_name, page_number):
        for h in doc_headings.get(doc_name, []):
            if h["page"] == page_number:
                return h["text"].strip()
        return "Unknown Section"

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

        section_title = extract_section_title(chunk["text"], doc_headings, chunk["document"], chunk["page_number"])
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

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"✅ Output written to: {output_path}")

# === Process All Subfolders ===
for input_dir in input_base.iterdir():
    if input_dir.is_dir():
        process_test_case(input_dir)
