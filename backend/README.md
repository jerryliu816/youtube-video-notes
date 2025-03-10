# YouTube Video Summarization 

## Overview

This project is a **YouTube Video Summarization Web App** that allows authenticated users to input a **YouTube URL**, extract its transcript, and generate a **summarized version** using an **LLM (Llama-3.1-8B)** via **Groq API**. The app is built with a **Next.js frontend**, a **FastAPI backend**, and **Auth0 authentication**.

## Tech Stack

| Component          | Technology Used                                    |
| ------------------ | -------------------------------------------------- |
| **Frontend**       | Next.js, React, Tailwind CSS, Auth0                |
| **Backend**        | FastAPI, OpenAI/Groq API, LangChain                |
| **Authentication** | Auth0 (OAuth 2.0)                                  |
| **Database**       | (None - Stateless API)                             |
| **Reverse Proxy**  | Nginx                                              |
| **Deployment**     | PM2 (Node.js), Gunicorn (FastAPI), Certbot (HTTPS) |

## Architecture Overview

### **Frontend (Next.js)**

- Handles **user authentication** via **Auth0**.
- Sends API requests to the **FastAPI backend**.
- Uses **Tailwind CSS** for styling.

### **Backend (FastAPI)**

- Extracts **YouTube transcripts** using `youtube_transcript_api`.
- Processes text with **Groq’s LLM API** to generate summaries.
- Handles API requests from Next.js.

### **Authentication (Auth0)**

- Manages **OAuth 2.0 authentication**.
- Ensures only logged-in users can access the summarization feature.

### **Reverse Proxy & Deployment (Nginx, PM2, Gunicorn)**

- **Nginx serves Next.js (port 3000).**
- **Nginx serves FastAPI (port 8000).**
- **Certbot handles HTTPS (SSL/TLS).**
- **PM2 manages Next.js, Gunicorn runs FastAPI.**

## API Flow

### **Authentication**

| Endpoint               | Description                              |
| ---------------------- | ---------------------------------------- |
| `GET /api/auth/login`  | Redirects to Auth0 login page.           |
| `GET /api/auth/logout` | Logs out the user.                       |
| `GET /api/auth/token`  | Retrieves the user's Auth0 access token. |

### **Summarization API**

| Endpoint      | Method | Description                                      |
| ------------- | ------ | ------------------------------------------------ |
| `/summarize/` | `POST` | Accepts YouTube URL & returns summarized content |

#### **Request Format**

```json
{
  "youtube_url": "https://youtube.com/watch?v=123",
  "target_language": "en",
  "mode": "video"
}
```

#### **Response Format**

```json
{
  "summary": "Summarized content...",
  "language": "en"
}
```

# Deployment Instructions

## 1️⃣ Set Up Next.js (Frontend)

```bash
# Install dependencies
cd frontend
npm install

# Build for production
npm run build

# Run with PM2
pm install -g pm2
pm2 start "npm run start" --name "nextjs-app"
pm2 save
pm2 startup
```

## 2️⃣ Set Up FastAPI (Backend)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt

# Run FastAPI with Gunicorn
pip install gunicorn

gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000 --daemon

or

uvicorn main:app --reload
```

## 3️⃣ Configure Nginx Reverse Proxy

Edit the Nginx config for Next.js (/etc/nginx/sites-available/nextjs):

```bash
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable it:

```bash
sudo ln -s /etc/nginx/sites-available/nextjs /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

## 4️⃣ Configure HTTPS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

### Environment Variables

#### **Frontend **``

```bash
NEXT_PUBLIC_FASTAPI_BACKEND=https://api.yourdomain.com
NEXT_PUBLIC_AUTH0_DOMAIN=your-auth0-domain
NEXT_PUBLIC_AUTH0_CLIENT_ID=your-auth0-client-id
NEXT_PUBLIC_AUTH0_REDIRECT_URI=https://yourdomain.com/api/auth/callback
```


#### **Backend **``

```bash
GROQ_API_KEY=your-groq-api-key
AUTH0_DOMAIN=your-auth0-domain
```


### Logging Setup

#### FastAPI Logging (backend/main.py)

import logging
logging.basicConfig(filename="fastapi_app.log", format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

#### Next.js Logging (frontend/pages/index.tsx)

console.info("API Request Sent");
console.error("API Error", error);

# Final Checklist ✅

✔ Next.js is running behind Nginx at https://yourdomain.com✔ FastAPI is running behind Nginx at https://api.yourdomain.com✔ Both services are secured with HTTPS✔ Environment variables are properly configured✔ Logging is enabled for debugging

🚀 Your project is now production-ready! 🎉

