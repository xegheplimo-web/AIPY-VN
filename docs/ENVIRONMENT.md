# Environment

## Local Machine

- OS: Windows 10/11 x64
- CPU: AMD Ryzen 9 9950X 16-Core
- RAM: 96GB
- GPU: NVIDIA RTX 3090 24GB VRAM (optional for AI features)

## Preferred Workspace

- Main workspace: `A:\AIPY\vietstore-rag`
- Models folder: `models/`
- Cache folder: `cache/`
- Output folder: `outputs/`

## Runtime Rules

- Use isolated environments (.venv, Docker)
- Prefer local dependencies over global
- Do not install CPU-only AI dependencies when GPU available
- Verify CUDA/GPU before running heavy AI workloads
- Avoid writing temporary files into system folders

## Required Tools

- Git
- Node.js LTS (>= 18)
- pnpm or npm
- Python 3.11+
- uv (Python package manager)
- Docker Desktop
- Visual Studio Build Tools (if compiling native deps)
