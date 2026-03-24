# Deploying Kartavya-3.0 on Jenkins (End-to-End Guide)

This guide covers everything needed to deploy the Kartavya-3.0 full-stack application (FastAPI + Next.js) using Jenkins CI/CD with Docker Compose.

---

## What to Ask Your Senior (Permissions Checklist)

Before you can deploy, you need your senior to set up or grant you access to the following on the Jenkins server:

| # | What to Ask | Why |
|---|---|---|
| 1 | **Jenkins login credentials** (username + password) | So you can access the Jenkins dashboard |
| 2 | **Permission to create a new Pipeline job** | You need to create a pipeline that reads the `Jenkinsfile` |
| 3 | **Docker installed on Jenkins server** | The deployment uses Docker Compose to build and run containers |
| 4 | **Jenkins user added to `docker` group** | So Jenkins can run `docker` commands (`sudo usermod -aG docker jenkins`) |
| 5 | **Permission to add Credentials** | You need to upload the `.env` file as a Jenkins Secret File |
| 6 | **Ports 3000 and 8000 open** on the server | Frontend runs on 3000, Backend on 8000 |
| 7 | **GitHub repo URL** for the org repo | Jenkins will fetch code from this repo |
| 8 | **GitHub access token or SSH key** configured in Jenkins | So Jenkins can clone your private repo |

---

## How API Keys Are Secured (No Leak Guarantee)

Your `GEMINI_API_KEY` is **never** stored in the code or Git repository. Here's the security chain:

```
.env file → Uploaded to Jenkins as "Secret File" credential
         → Jenkins copies it into workspace at build time
         → Docker Compose reads it via `env_file: .env`
         → After deployment, Jenkinsfile deletes .env from workspace
```

**Security measures in the Jenkinsfile:**
1. `.env` is injected via `withCredentials` — Jenkins **masks** secret values in all build logs
2. `.env` is deleted from the workspace in the `post.always` block after every build
3. `.env` is in `.gitignore` and `.dockerignore` — never committed or included in Docker images
4. The API key only exists inside the running Docker container's environment

---

## Step 1: Push Code to Your Org GitHub Repo

```bash
# Add your org's remote (replace with actual URL)
git remote add origin https://github.com/your-org/kartavya-3.0.git

# Push to main branch
git push -u origin main
```

Make sure these files are in the repo root:
- `Jenkinsfile`
- `docker-compose.prod.yml`
- `Dockerfile.backend`
- `Dockerfile.frontend`
- `.env.example` (template only, NO real keys)

> **CRITICAL:** Double-check that `.env` is NOT pushed. Run `git status` to verify.

---

## Step 2: Add Credentials in Jenkins

1. Go to Jenkins Dashboard → **Manage Jenkins** → **Credentials** → **System** → **Global credentials**
2. Click **Add Credentials**
3. Set **Kind** = `Secret file`
4. Upload your `.env` file containing:
   ```env
   GEMINI_API_KEY=your_real_key_here
   GEMINI_MODEL=gemini-3-pro-preview
   LOG_LEVEL=INFO
   DEBUG=False
   PORT=8000
   ```
5. Set **ID** = `kartavya-env-secrets`
6. Set **Description** = `Kartavya-3.0 Production Environment Variables`
7. Click **Create**

---

## Step 3: Create the Jenkins Pipeline Job

1. Go to Jenkins Dashboard → **New Item**
2. Enter name: `Kartavya-3.0-Deploy`
3. Select **Pipeline** → Click **OK**
4. In the **Pipeline** section:
   - **Definition**: `Pipeline script from SCM`
   - **SCM**: `Git`
   - **Repository URL**: `https://github.com/your-org/kartavya-3.0.git`
   - **Branch**: `*/main`
   - **Script Path**: `Jenkinsfile`
5. Click **Save**

---

## Step 4: Run the Build

1. Go to the `Kartavya-3.0-Deploy` job
2. Click **Build Now**
3. Jenkins will automatically:
   - Clone the repo
   - Inject your `.env` secrets securely
   - Build Docker images for backend and frontend
   - Start the containers
   - Run health checks
   - Clean up secrets from workspace

---

## Step 5: Verify After Deployment

After a successful build, verify everything works:

| Check | Command / URL |
|---|---|
| Backend API | `curl http://SERVER_IP:8000/api/health` → should return `{"status":"ok"}` |
| Frontend | Open `http://SERVER_IP:3000` in browser |
| Generate a course | Create a test course and verify it completes |
| Download PDF | Verify PDF downloads with correct fonts (no tofu boxes) |
| Download xAPI | Verify xAPI ZIP downloads and works |

---

## After Deployment: Adding New Features

When you add new features to the project after the initial deployment:

```
1. Create a new branch locally
   → git checkout -b feature/my-new-feature

2. Make your changes and test locally

3. Push the branch to GitHub
   → git push origin feature/my-new-feature

4. Create a Pull Request on GitHub
   → Get it reviewed and approved

5. Merge to main
   → Jenkins will automatically detect the change
   → (if webhook is configured) or click "Build Now" manually

6. Jenkins rebuilds and redeploys automatically
```

> **Tip:** Ask your senior to set up a **GitHub Webhook** pointing to `http://JENKINS_IP/github-webhook/` so Jenkins triggers automatically on every push to `main`.

---

## Common Issues After Deployment

| Problem | Solution |
|---|---|
| **PDF has tofu boxes** | Font packages are installed in `Dockerfile.backend`. Rebuild the image. |
| **Frontend can't reach backend** | Inside Docker, the frontend uses `http://backend:8000` (Docker internal DNS). This is handled by `docker-compose.prod.yml`. |
| **API key not working** | Re-upload `.env` in Jenkins Credentials. Make sure the ID is exactly `kartavya-env-secrets`. |
| **Containers keep restarting** | Check logs: `docker compose -f docker-compose.prod.yml logs --tail 50` |
| **Port already in use** | Stop existing containers first: `docker compose -f docker-compose.prod.yml down` |

---

## Project Structure (What Goes Where)

```
kartavya-3.0/
├── Jenkinsfile              ← CI/CD pipeline (auto-reads by Jenkins)
├── docker-compose.prod.yml  ← Orchestrates backend + frontend containers
├── Dockerfile.backend       ← Builds Python/FastAPI container
├── Dockerfile.frontend      ← Builds Next.js container (multi-stage)
├── .env.example             ← Template for environment variables (safe to commit)
├── .env                     ← REAL secrets (NEVER commit this)
├── .gitignore               ← Ensures .env is never committed
├── .dockerignore            ← Ensures .env is never in Docker images
├── backend/                 ← FastAPI application
├── frontend/                ← Next.js application
├── generators/              ← PDF, xAPI generators
├── services/                ← Course generation, Gemini API
└── utils/                   ← Logger, helpers
```
