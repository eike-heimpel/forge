# Forge Project

This is a monorepo for the Forge project, containing the frontend and backend applications.

## Getting Started

To get started, you'll need to install the dependencies for both the frontend and backend.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Running Both

You can also use the root `package.json` to start both applications at the same time:

```bash
npm install
npm start
```
