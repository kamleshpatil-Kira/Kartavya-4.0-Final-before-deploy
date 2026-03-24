# Full Stack Deployment (Frontend + Backend)

This deploys:
- Frontend (Next.js) on `:3000`
- Backend API (FastAPI) on `:8000`

## 1. Prerequisites

- Docker Engine + Docker Compose plugin installed
- A valid `GEMINI_API_KEY`
- Open ports: `3000`, `8000`

## 2. Configure environment

**Option A: System Environment (Recommended for Production)**
1. Open `/etc/environment`:
   `sudo vi /etc/environment`
2. Add your key at the bottom:
   `GEMINI_API_KEY=your_real_key_here`
3. Export it properly to the shell before running Docker:
   `set -a; source /etc/environment; set +a`

**Option B: Local `.env` file**
Create `.env` in project root (this overrides system environment):

```env
GEMINI_API_KEY=your_real_key_here
GEMINI_MODEL=gemini-3-pro-preview
LOG_LEVEL=INFO
DEBUG=False
```


## 3. Build and start (frontend + backend)

```bash
docker compose -f docker-compose.prod.yml up -d --build backend frontend
```

Check status:

```bash
docker compose -f docker-compose.prod.yml ps
```

Health checks:

```bash
curl http://127.0.0.1:8000/api/health
curl http://127.0.0.1:3000/api/health
```

Open app:
- `http://<server-ip>:3000`

## 4. Logs / restart / stop

Logs:

```bash
docker compose -f docker-compose.prod.yml logs -f backend
docker compose -f docker-compose.prod.yml logs -f frontend
```

Restart:

```bash
docker compose -f docker-compose.prod.yml restart backend frontend
```

Stop:

```bash
docker compose -f docker-compose.prod.yml down
```

## 5. Persistence

These folders are mounted and survive container recreation:
- `./uploads`
- `./output`
- `./temp`
- `./logs`

## 6. Common issues

- `GEMINI_API_KEY not set`: check `.env` exists and has key.
- Frontend cannot reach backend: ensure backend container is healthy and `NEXT_API_BASE_URL=http://backend:8000`.
- First build is slow: Python/Node dependencies are installed during image build.
