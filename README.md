# 🧠 Athena Backend

Athena is a modern **Learning Management System (LMS)** designed for educators, students, and administrators.  
It combines an interactive learning experience, real-time collaboration, and powerful analytics.

> 🚧 **Work in progress.** Most of the system is not production-ready yet.

---

## 🧰 Tech Stack

| Layer        | Technology              |
| ------------ | ----------------------- |
| **Backend**  | FastAPI (Python)        |
| **Frontend** | React (Vite, shadcn/ui) |
| **Database** | PostgreSQL              |
| **Storage**  | MinIO                   |
| **CI/CD**    | GitHub Actions          |

---

## 🧪 Development

```bash
# Install dependencies
poetry install

# Check code style
poetry run ruff check .

# Check code style and fix errors
poetry run ruff check . --fix

# Format code
poetry run ruff format .

# Start backend
poetry run python src/app.py
```

---

## 🧱 CI/CD

The project uses GitHub Actions for automated linting, testing, and auditing on every push or pull request to main and develop branches.

## ⚖️ License

MIT License Copyright © 2025 [Sergei Shekshuev](https://github.com/shekshuev)
