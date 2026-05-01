# GeneRisk — AI-Powered Genomic Risk Intelligence System
**JNNCE Shivamogga | VTU Final Year Project | Batch B13**

> Likhith T S · Mohammed Saffi · Prekshith K L · Rahul K S  
> Guide: Mr. Sathyanarayana S, Asst. Prof., CS&E

---

## Complete File List (All Files — Nothing Missing)

```
generisk/
├── backend/
│   ├── edge_agent/
│   │   ├── __init__.py          ✅ Package init
│   │   ├── vcf_parser.py        ✅ VCF reading + local filtering
│   │   ├── clinvar_lookup.py    ✅ Local ClinVar SQLite queries
│   │   ├── prs_engine.py        ✅ Polygenic Risk Score + Indian correction
│   │   ├── shap_explainer.py    ✅ Gene attribution waterfall charts
│   │   ├── lifestyle_fusion.py  ✅ Genetics + lifestyle multimodal fusion
│   │   └── offload_router.py    ✅ Adaptive cloud tier routing
│   ├── cloud_worker/
│   │   ├── __init__.py          ✅ Package init
│   │   ├── main.py              ✅ FastAPI server (deploy on Railway)
│   │   ├── models.py            ✅ Pydantic request/response schemas
│   │   ├── rag_pipeline.py      ✅ LangChain + ChromaDB + Groq RAG
│   │   └── report_generator.py  ✅ PDF report generation
│   └── federated/
│       ├── server.py            ✅ Flower FL coordinator
│       ├── client.py            ✅ Hospital node simulation
│       └── run_simulation.py    ✅ One-command FL experiment
├── frontend/
│   ├── package.json             ✅ NPM dependencies
│   ├── next.config.js           ✅ Next.js config
│   ├── tailwind.config.js       ✅ Tailwind CSS
│   ├── postcss.config.js        ✅ PostCSS
│   └── src/
│       ├── app/
│       │   ├── layout.jsx       ✅ Root layout
│       │   ├── globals.css      ✅ Global styles
│       │   ├── page.jsx         ✅ Home page (upload + lifestyle form)
│       │   └── results/
│       │       └── page.jsx     ✅ Results dashboard (4 tabs)
│       └── lib/
│           └── api.js           ✅ API client utilities
├── data/
│   ├── setup_clinvar.py         ✅ Download + load ClinVar into SQLite
│   ├── setup_chromadb.py        ✅ Index OMIM + PubMed into ChromaDB
│   └── gwas_weights/
│       ├── type2_diabetes.csv   ✅ T2D GWAS effect sizes
│       └── all_diseases.csv     ✅ All disease weights + Indian corrections
├── tests/
│   └── test_pipeline.py         ✅ End-to-end test (no API keys needed)
├── .github/
│   └── workflows/ci.yml         ✅ GitHub Actions CI
├── Dockerfile                   ✅ Railway backend deployment
├── railway.toml                 ✅ Railway config
├── vercel.json                  ✅ Vercel frontend deployment
├── requirements.txt             ✅ All Python dependencies
├── .env.example                 ✅ API keys template
└── .gitignore                   ✅ Git ignore rules
```

---

## Setup in Order — Follow These Steps Exactly

### Step 1: Clone or create the project folder
```bash
mkdir generisk && cd generisk
# Copy all files into the correct folder structure above
```

### Step 2: Backend setup
```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# Install all dependencies
pip install -r requirements.txt

# Copy .env and fill in your free API keys
cp .env.example .env
```

### Step 3: Get free API keys (takes 10 minutes)

| Service | URL | Key to add in .env |
|---------|-----|--------------------|
| Groq (LLaMA 3 — FREE) | console.groq.com | GROQ_API_KEY |
| NCBI/PubMed (FREE) | ncbi.nlm.nih.gov/account | NCBI_API_KEY |
| OMIM (FREE for students) | omim.org/api | OMIM_API_KEY |
| MongoDB Atlas (FREE 512MB) | mongodb.com/atlas | MONGODB_URI |

### Step 4: Setup databases (run once)
```bash
# Download and index medical knowledge into ChromaDB (~90MB model download)
python data/setup_chromadb.py

# Download ClinVar (~100MB, takes 10 minutes)
python data/setup_clinvar.py
```

### Step 5: Test the full pipeline
```bash
python tests/test_pipeline.py
# Expected: "PIPELINE TEST COMPLETE" with all checks passing
```

### Step 6: Run backend locally
```bash
cd backend/cloud_worker
python main.py
# Visit http://localhost:8000/docs to see API documentation
```

### Step 7: Run frontend locally
```bash
cd frontend
npm install
npm run dev
# Visit http://localhost:3000
```

### Step 8: Run federated learning experiment (for paper results)
```bash
python backend/federated/run_simulation.py
# Runs 5 rounds across 3 simulated hospital nodes
# Output table goes in your IEEE paper Section 5
```

---

## Deployment

### Deploy Backend → Railway
1. Push code to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Select your repo
4. Add environment variables (copy from .env)
5. Railway auto-builds using Dockerfile
6. Copy the generated URL (e.g., https://generisk-api.railway.app)

### Deploy Frontend → Vercel
1. Go to vercel.com → New Project → Import from GitHub
2. Set Root Directory to `frontend`
3. Add environment variable: `NEXT_PUBLIC_API_URL` = your Railway URL
4. Deploy

### Your live URLs
- Frontend: `https://generisk.vercel.app`
- Backend API docs: `https://generisk-api.railway.app/docs`

---

## Team Division

| Member | Module | Run to test |
|--------|--------|-------------|
| Likhith T S | Edge Agent (VCF + PRS + ClinVar) | `python backend/edge_agent/vcf_parser.py` |
| Mohammed Saffi | RAG + LLM Pipeline | `python backend/cloud_worker/rag_pipeline.py` |
| Prekshith K L | SHAP + Fusion + Report | `python backend/edge_agent/shap_explainer.py` |
| Rahul K S | FastAPI + Frontend + Deployment | `python backend/cloud_worker/main.py` |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: vcf` | `pip install pyvcf3` |
| `GROQ_API_KEY not set` | Add key to .env file |
| Port 8000 already in use | `uvicorn main:app --port 8001` |
| `ChromaDB collection not found` | Run `python data/setup_chromadb.py` |
| Frontend can't reach API | Check NEXT_PUBLIC_API_URL in .env |
| VCF parse error | Make sure file is unzipped (.vcf not .gz) |
| Railway build fails | Check Dockerfile path and requirements.txt |

---

*GeneRisk | JNNCE Batch B13 | VTU | 2026 | Research Use Only*
