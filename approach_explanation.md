# approach\_explanation.md

## 🧠 Persona-Driven Document Intelligence: Approach Explanation

This document explains our strategy for solving the Adobe India Hackathon Round 1B challenge: **"Connect What Matters — For the User Who Matters"**, where the goal is to extract and prioritize relevant sections from PDFs based on a user persona and their job-to-be-done.

---

## 📘 1. PDF Analysis Strategy

### a) Skim for Document Structure

To understand each PDF's structure quickly, we use:

* **Headings**: Detected using visual cues (font size, boldness, indentation) from `PyMuPDF`.
* **Table of Contents**: When present, we parse it to extract major section names and page hints.
* **Section Markers**: We look for common section names such as `Abstract`, `Introduction`, `Methodology`, `Results`, `Discussion`, and `Conclusion`. These act as anchors for extracting contextually rich content.

### b) Identify Relevant Sections

We combine the persona's role and the job-to-be-done into a unified semantic query.

* We extract blocks of text (>= 30 words) from each page.
* Each block is encoded using a compact embedding model (`all-MiniLM-L6-v2`).
* We compute cosine similarity between each chunk and the persona-job query.
* The top N (e.g., 5) most relevant blocks are selected, ranked, and further analyzed.

If a document contains any of the standard academic/business sections mentioned above, we prioritize them in scoring.

---

## 🗣️ 2. Tailored Understanding

### a) Summarize in Persona's Language

The extracted block is summarized with the target user in mind:

* For technical roles (e.g., PhD), we retain complexity and specificity.
* For less technical users (e.g., students), we emphasize clarity and simplicity.

While we do not use a large summarization model (due to CPU and size limits), we highlight key sentences and optionally simplify using rules (e.g., sentence shortening, jargon detection).

### b) Cross-reference Multiple PDFs

To synthesize across documents:

* We rank all chunks across all PDFs jointly.
* This allows the system to capture recurring concepts and patterns across different sources.
* Our ranking and filtering logic ensure the top results are diverse and non-redundant.

---

## 💾 3. Output Format

The final output is saved as a JSON file, adhering to the competition schema:

* **Metadata**: Includes persona, job, documents, and timestamp.
* **Extracted Sections**: Top-ranked blocks with title, page number, and importance.
* **Subsection Analysis**: Full text chunks for the selected sections.

This structure ensures easy downstream consumption and evaluation.

---

## 🛠️ Technical Constraints

* Runs on **CPU-only** environment.
* Embedding model used: `sentence-transformers/all-MiniLM-L6-v2` (under 100MB).
* Entire solution runs under **60 seconds** for 3–5 PDFs.
* Dockerized, offline-compatible with pre-downloaded model and packages.

---

## ✅ Summary

Our solution efficiently analyzes the structure of input PDFs, extracts contextually important sections, adapts the language to suit the persona, and produces a structured, JSON output. It balances performance and generalizability within strict runtime and compute constraints, making it robust across academic, business, and educational document types.
