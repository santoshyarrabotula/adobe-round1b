# 🧠 Persona-Driven Document Intelligence – Adobe Hackathon Round 1B

This project solves **Round 1B** of the **Adobe India Hackathon 2025**:  
> 📄 Extract context-aware, persona-driven summaries from PDF documents using NLP and heading-based document segmentation.

The system uses semantic search, heading detection, and persona-tuned retrieval to identify and extract the **top 5 most relevant sections** across a set of input PDFs, based on a **persona** and their **task ("job to be done")**.

---

## 📦 Features

- ✅ **Persona-Tuned Retrieval** — Queries are dynamically generated from the persona + task.
- 🧠 **Semantic Understanding** — Uses `sentence-transformers` for deep similarity matching.
- 🏷️ **Heading-Based Sectioning** — Identifies real section titles based on font size and style.
- 🗃️ **Batch Processing** — Processes all test cases in `/app/input/`, skipping if output exists.
- 📄 **PDF Parsing** — Extracts text from PDFs using `PyMuPDF`.
- 🐳 **Fully Dockerized** — Just mount `input/` and `output/`, and run via Docker.
- 💡 **Automatic JSON Output** — Saves structured output per test case in `/app/output/`.

---

## 📁 Project Structure

adobe-round1b/
├── Dockerfile # Builds and runs the complete pipeline
├── main.py # Main logic to extract relevant sections
├── requirements.txt # Python dependencies
├── app/
│ ├── input/
│ │ └── travel_planner/
│ │ ├── input_context.json
│ │ ├── *.pdf # Multiple related PDF files
│ └── output/
│ └── travel_planner.json (generated)
├── .gitignore

yaml
Copy
Edit

> 📌 You can add more folders like `food_lover/` under `input/`, and the system will process all subfolders automatically.

---

## 🚀 Getting Started

### 1. 🐳 Build Docker Image

```bash
docker build -t adobe-hackathon-round1b .
2. 🏃 Run the Container
bash
Copy
Edit
docker run --rm \
  -v "${PWD}/app/input:/app/input" \
  -v "${PWD}/app/output:/app/output" \
  adobe-hackathon-round1b
✅ Output will be generated as:

bash
Copy
Edit
app/output/travel_planner.json