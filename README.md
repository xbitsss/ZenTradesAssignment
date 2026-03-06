# Clara Answers — Pipeline A Guide

Pipeline A takes a demo call transcript and generates two things:
- `memo.json` — structured account data extracted from the transcript
- `agent_spec.json` — a draft Retell agent configuration

---

## Prerequisites

- Docker Desktop installed and running
- Ollama installed locally with `phi3:mini` pulled
- A transcript file (`.txt`) for the demo call

---

## Folder Structure

Before running, make sure your project looks like this:

```
ZenTradesAssignment/
├── .env
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── scripts/
│   ├── pipeline_a.py
│   ├── extract_memo.py
│   ├── generate_agent.py
│   └── create_task.py
└── data/
    └── demo_calls/
        └── ACC001_demo.txt   ← your transcript goes here
```

---

## Step 1 — Set up your `.env` file (SKIP, SINCE THE CURRENT MODEL IS OLLAMA)

Create a `.env` file in the project root:

```
GEMINI_API_KEY=your_key_here
```

> If you're using Ollama instead of Gemini, you can leave this blank — no key needed.

---

## Step 2 — Start Docker

Open a terminal in your project folder and run:

```bash
docker compose up -d --build
```

This starts two containers:
- `zentradesassignment-n8n-1` — n8n workflow UI
- `pipeline` — Python environment for running scripts

Verify both are running:

```bash
docker ps
```

---

## Step 3 — Add your transcript

Rename your demo call transcript to follow this pattern:

```
ACC001_demo.txt
```

Place it in:

```
data/demo_calls/ACC001_demo.txt
```

> The `ACC001` part is the account ID. Use `ACC002`, `ACC003` etc. for other accounts.

---

## Step 4 — Shell into the pipeline container

```bash
docker exec -it pipeline sh
```

You should see:

```
/app $
```

---

## Step 5 — Run Pipeline A

```bash
python scripts/pipeline_a.py --transcript data/demo_calls/ACC001_demo.txt --account_id ACC001
```

---

## Step 6 — Check the output

If it worked, you'll see:

```
✅ Pipeline A complete for ACC001
   Outputs: outputs/accounts/ACC001/v1/
```

Your output files will be at:

```
outputs/
└── accounts/
    └── ACC001/
        └── v1/
            ├── transcript.txt    ← copy of your input
            ├── memo.json         ← extracted account data
            └── agent_spec.json   ← draft Retell agent config
```

---

## Running multiple accounts

Just repeat Steps 3–5 for each account, incrementing the ID:

```bash
python scripts/pipeline_a.py --transcript data/demo_calls/ACC002_demo.txt --account_id ACC002
python scripts/pipeline_a.py --transcript data/demo_calls/ACC003_demo.txt --account_id ACC003
```

Or run all at once:

```bash
python scripts/batch_run.py
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `container not found` | Run `docker ps` to get the exact container name |
| `python not found` | You're in the wrong container — exec into `pipeline` not `n8n` |
| `quota exceeded` | Your Gemini key hit its limit — create a new key or switch to Ollama |
| `JSON decode error` | The model returned bad output — re-run, it usually fixes itself |
| Ollama not reachable | Make sure Ollama is running on your machine, not inside Docker |