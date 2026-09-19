# ServiceNow Staff AI Engineer — Technical Showcase

A reference implementation built to demonstrate hands-on ownership of every
line item in ServiceNow's **Staff AI Engineer** job description: AI Agent
Studio-style agent/workflow orchestration, an AI Control Tower governance
plane, MCP + A2A multi-agent interoperability, an LLM/embeddings gateway,
and the CI/CD, IaC, and observability discipline a Staff engineer is
expected to set as the bar for a team.

This is a portfolio/interview artifact, not ServiceNow platform code (the
real AI Agent Studio, Skill Kit, and AI Control Tower are proprietary
ServiceNow products this repo does not have access to). What it demonstrates
instead is the **architecture, governance model, protocols, and engineering
rigor** those products are built on — implemented end-to-end, tested,
containerized, and CI-gated, so a reviewer can run it and see it work rather
than take a slide's word for it.

## Prerequisites

| Tool | Why it's required |
|---|---|
| Git | clone the repo, run pre-commit hooks on `git commit` |
| Python 3.11 or 3.12 | run/test the four services |
| Node.js 20+ | build/run the frontend showcase app |
| **Docker Desktop / Docker Engine** | `docker compose up` (full local stack), `docker build` (CI parity) |
| Terraform ≥ 1.9 (or OpenTofu) | `terraform_fmt` / `terraform_validate` pre-commit hooks, and `infra/terraform` itself |
| kubectl + kustomize | deploying to EKS (§6, cloud) |

### Install (Ubuntu / WSL2)
```bash
sudo apt update && sudo apt install -y git python3.12 python3.12-venv python3-pip curl unzip
curl -fsSL https://get.docker.com | sudo sh && sudo usermod -aG docker "$USER"   # log out/in after
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install -y terraform nodejs npm
```
### Install (macOS)
```bash
brew install git python@3.12 node terraform kubectl kustomize
brew install --cask docker   # then launch Docker Desktop once
```
### Install (Windows 11)
Use WSL2 Ubuntu for all `git commit` / `pre-commit` operations — the
`terraform_fmt` / `terraform_validate` pre-commit hooks are Bash scripts and
native Git Bash mangles Windows paths invoking them. Install Docker Desktop
(`winget install --id Docker.DockerDesktop -e`) and enable **Settings →
Resources → WSL Integration** for your distro so `docker` is callable from
inside WSL.

### Install the pre-commit git hook (all platforms)
```bash
python3.12 -m venv .venv-root && source .venv-root/bin/activate
pip install pre-commit==3.8.0
pre-commit install --install-hooks
pre-commit run --all-files   # optional: run once now against everything
```
From then on, `git commit` runs ruff, ruff-format, mypy (once per service,
scoped by path), terraform fmt/validate, hadolint, and basic hygiene checks
on the changed files — the same gate CI enforces, so a broken commit never
reaches a PR. Skip a single hook ad hoc with `SKIP=hadolint git commit ...`;
CI still runs it, so this isn't a way to permanently bypass a check.

## 1. Why this design (technical rationale)

| JD requirement | Design decision | Why (defensible in review) |
|---|---|---|
| "Architect and implement AI agents and workflows using AI Agent Studio, Skill Kit, and Workflow Data Fabric" | `services/agent-orchestrator`: a `SkillRegistry` (Skill Kit analogue) of risk-tiered, independently invocable capabilities, bound into `AgentDefinition`s with an explicit autonomy ceiling, executed by a `WorkflowEngine` that enforces policy *before* every step | Every skill declares its own governance metadata at definition time — policy isn't bolted on after the fact, it's a required field. This is "govern by design," the same posture AI Control Tower promotes |
| "Lead AI Control Tower implementation, adoption, and enablement — governance policies and monitoring" | `services/control-tower`: standalone `GovernanceEngine` (allow / deny / require-approval), an immutable in-memory audit trail with monotonic record IDs, and OpenTelemetry counters for decision volume by outcome and by agent | Governance lives in one independently deployable, independently auditable service, not copy-pasted into every agent runtime — see `docs/adr/0001-service-boundaries.md` |
| "Integrate and configure LLM-based capabilities in Cloud & ServiceNow Platform" | `services/llm-gateway`: a `Provider` protocol with a deterministic `MockProvider` (offline, CI-safe) and a real `AnthropicProvider` adapter behind the identical interface; an `InMemoryVectorStore` with cosine-similarity search | The provider is a swap point, not a hardcoded vendor call — the same interface a real ServiceNow Cloud LLM integration would sit behind |
| "Familiarity with MCP and A2A for governed multi-agent integration and interoperability" | `services/mcp-a2a-gateway`: a spec-shaped MCP JSON-RPC server (`initialize` / `tools/list` / `tools/call`) and an A2A agent-card + task-lifecycle implementation (`/.well-known/agent.json`, task submit/get) | Implements the actual wire protocols, not a diagram of them — a real MCP client or A2A peer can talk to this server with only a transport shim |
| "Strong understanding of NLP and modern LLM architectures (transformers, embeddings, vector search, agentic frameworks)" | Embeddings + cosine-similarity vector search in `llm-gateway`; agentic planning/execution loop with tool-calling and human-in-the-loop gates in `agent-orchestrator` | The underlying mechanics (embed → store → nearest-neighbour search; plan → check policy → execute-or-halt) are implemented, not assumed |
| "Familiarity with OpenTelemetry for AI system observability" | Every service configures an OTel `TracerProvider`; `agent-orchestrator` emits per-workflow and per-step spans with real trace IDs returned in API responses; `control-tower` emits decision/invocation counters | `OTEL_EXPORTER_OTLP_ENDPOINT` env var repoints every service at a real collector (Grafana/Tempo/Jaeger) with zero code changes — standard OTel SDK env-based config |
| "Proficiency in scripting/integration (JavaScript, Python) and cloud infrastructure (AWS/Azure/GCP)" | Python (FastAPI) backends; TypeScript/React frontend with a Node/Express server that proxies real backend calls (`frontend/server.ts`, `/api/live/*`); Terraform for AWS (VPC, S3 WORM audit bucket, SNS alerts) | Both halves of the stack are implemented, tested, and wired together — the frontend's "Live Python Backend" tab calls the real services, it doesn't just mock JSON that looks like it did |
| "Mentor engineers, set technical direction, establish best practices" | `.pre-commit-config.yaml`, `CODEOWNERS`, ADR process (`docs/adr/`), a CI pipeline that fails the build on any lint/type/test/build regression | The review-standards artifacts a Staff engineer is expected to introduce and enforce across a team |
| Preferred: "AI Control Tower governance frameworks" | `infra/terraform/modules/ai-control-tower`: an object-locked (WORM) S3 audit-log bucket with a 7-year prod retention policy, plus an SNS topic for deny/require-approval alerts | Declares the durable side of governance as versioned infrastructure, not a runbook step |

## 2. Repository layout

```
servicenow-staff-ai-engineer-showcase/
├── services/
│   ├── agent-orchestrator/     # FastAPI: Agent Studio-style skill/agent/workflow engine
│   ├── control-tower/          # FastAPI: governance policy engine, audit trail, OTel metrics
│   ├── mcp-a2a-gateway/        # FastAPI: MCP JSON-RPC server + A2A agent-card/task protocol
│   └── llm-gateway/            # FastAPI: LLM completion, embeddings, vector search
├── frontend/                   # React/TypeScript showcase UI (7 JD-mapped tabs + Live Backend tab)
├── infra/
│   ├── terraform/               # VPC + AI Control Tower audit infra — modules + dev/prod envs
│   └── k8s/                     # base + kustomize overlays (dev/prod)
├── docs/adr/                    # Architecture Decision Records
├── .github/workflows/ci.yml     # pre-commit → unit tests → docker build → terraform validate → frontend build
├── docker-compose.yml           # Full local stack (all four services)
├── Makefile                     # install / test / lint / fmt / precommit / up / down shortcuts
└── .pre-commit-config.yaml
```

## 3. Core domain model

- **Skill** (`agent-orchestrator/app/models.py::SkillDefinition`) — a callable capability with a declared `SkillRiskTier` (`read_only` / `write_low_risk` / `write_high_risk`) and an optional mandatory-human-approval flag.
- **Agent** (`AgentDefinition`) — a persona bound to an allow-list of skill IDs and a `max_autonomous_risk_tier` ceiling.
- **Workflow run** (`WorkflowEngine.run`) — plans a sequence of skills for a goal, then for each step: checks the skill is in the agent's allow-list → checks the skill's risk tier against the agent's ceiling → checks for a mandatory-approval flag → executes or halts with a typed `WorkflowStepStatus` (`completed` / `blocked_by_policy` / `awaiting_approval`).
- **Policy decision** (`control-tower/app/governance/policy.py::GovernanceEngine`) — the same allow/deny/require-approval rule, independently deployable and independently tested (see `docs/adr/0002-policy-parity.md` for why two call sites implement one rule).
- **MCP tool call** (`mcp-a2a-gateway/app/mcp/server.py`) — `initialize` → `tools/list` → `tools/call`, JSON-RPC 2.0 envelope, spec-shaped error codes.
- **A2A task** (`mcp-a2a-gateway/app/a2a/protocol.py`) — `AgentCard` capability discovery + `A2ATask` submit/get lifecycle with typed states.

## 4. Run instructions

### Local, no Docker (per service)
```bash
cd services/agent-orchestrator        # or control-tower / mcp-a2a-gateway / llm-gateway
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000   # 8001 / 8002 / 8003 for the others
```
```bash
pytest -q            # unit tests, no external services needed
ruff check app tests # lint
mypy app              # types
```
Or from the repo root: `make install && make test && make lint`.

### Docker (full stack: all four services)
```bash
docker compose up --build
curl http://localhost:8000/healthz   # agent-orchestrator
curl http://localhost:8001/healthz   # control-tower
curl http://localhost:8002/healthz   # mcp-a2a-gateway
curl http://localhost:8003/healthz   # llm-gateway
open http://localhost:8000/docs      # OpenAPI for any service
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env      # optional: point at the docker-compose backends
npm run dev                # http://localhost:3000
npm run build && npm start # production build
npm run lint                # tsc --noEmit
```
Open the **Live Python Backend** tab to call the real FastAPI services
(health, a real Control Tower policy decision, a real vector search) — every
other tab can run on mock data alone, this one proves the backend is real.

### Cloud (EKS via Terraform)
```bash
cd infra/terraform/environments/dev
terraform init
terraform plan  -var-file=dev.tfvars
terraform apply -var-file=dev.tfvars

aws eks update-kubeconfig --name snow-ai-dev --region us-east-1
kubectl apply -k ../../k8s/overlays/dev
kubectl get pods -n snow-ai-dev
```

## 5. CI/CD (`.github/workflows/ci.yml`)

Every push/PR to `main` runs, each job gating merge:
1. **pre-commit** — ruff, ruff-format, mypy (×4, path-scoped per service), terraform fmt/validate, hadolint, end-of-file/whitespace hygiene, all run with `--all-files`.
2. **unit-tests** — `pytest -q` for all four services, matrixed over Python 3.11 / 3.12 (8 legs).
3. **docker-build** — builds every service's image and runs a container smoke test (starts it, confirms it's `Running`) — a non-zero exit or a crashed container fails the job.
4. **terraform-validate** — `terraform fmt -check` + `terraform validate` for both `dev` and `prod` environments.
5. **frontend-build** — `npm ci`, `npm run build` (Vite + esbuild + `tsc --noEmit` via `npm run lint` in pre-commit's scope).

All actions are pinned to a full commit SHA (not a floating tag) for pipeline reproducibility.

## 6. Candidate mapping — this repo's authorship

| Repo artifact | Demonstrates | Grounded in prior real-world work |
|---|---|---|
| `agent-orchestrator` skill/agent/workflow model | Agent Studio-equivalent orchestration design | 17+ years building systematic signal-research pipelines with staged execution and explicit risk gating (BAM, Millburn) |
| `control-tower` governance engine + audit trail | AI Control Tower governance ownership | Production engineering discipline around auditable, reproducible pipeline decisions (BAM Systematic Macro) |
| `mcp-a2a-gateway` protocol implementation | MCP/A2A familiarity, multi-agent interoperability | Cross-asset, cross-system signal integration work (equities/futures/FX/options) requiring interoperable service boundaries |
| `llm-gateway` provider abstraction + vector search | LLM/embeddings/vector-search fluency | ML/NLP-to-alpha pipeline experience (BAM) |
| `.pre-commit-config.yaml`, CODEOWNERS, ADRs, CI matrix | Setting technical direction and review standards for a team | 14-year tenure at Millburn Ridgefield; production engineering leadership at JPM/Highbridge |
| Python + TypeScript across the stack, Terraform for AWS | Scripting/integration proficiency, cloud infrastructure | Core technical stack (Python/C++) plus multi-cloud (GCP/AWS) experience across prior roles |

## 7. Intentionally scoped as a stub (with clear extension points)

This is a portfolio repo, not production ServiceNow platform code:
- **Real AI Agent Studio / Skill Kit / AI Control Tower** — this repo cannot call ServiceNow's actual proprietary products; it implements the same governance and orchestration *architecture* those products encode, ready to be re-pointed at the real platform APIs behind the same interfaces (`SkillRegistry`, `GovernanceEngine`, `PolicyChecker`).
- **LLM provider** — `MockProvider` is deterministic/offline for CI; `AnthropicProvider` shows the real-provider seam. A ServiceNow-hosted or Azure OpenAI-backed model swaps in behind the same `Provider` protocol with no call-site changes.
- **Vector store** — in-memory cosine similarity for portability; the `InMemoryVectorStore` interface is the swap point for a managed vector DB (pgvector, Pinecone) in a real deployment.
- **Policy parity between `agent-orchestrator` and `control-tower`** — currently kept in sync by code review and shared tests rather than a shared library; see `docs/adr/0002-policy-parity.md` for the tradeoff and the extraction path.
