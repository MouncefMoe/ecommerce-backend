# Deployment Guide

This guide will help you deploy your E-commerce Backend API to a live server so others can try it.

## 🚀 Quick Deploy (Recommended)

### Option 1: Render.com (FREE - Best for demos)

1. **Sign up for Render**: Go to [render.com](https://render.com) and create a free account

2. **Create New Web Service**:
   - Click "New +" → "Blueprint"
   - Connect your GitHub account
   - Select the `ecommerce-backend` repository
   - Render will auto-detect `render.yaml` and set up everything!

3. **Wait for deployment** (5-10 minutes)

4. **Seed demo data**:
   - Go to your service's Shell tab
   - Run: `python scripts/seed_demo_data.py`

5. **Your API is live!**
   - Main URL: `https://your-app-name.onrender.com`
   - Docs: `https://your-app-name.onrender.com/docs`
   - Demo: `https://your-app-name.onrender.com/demo/`

**⚠️ Free tier note**: The server sleeps after 15 minutes of inactivity. First request may take 30 seconds to wake up.

---

### Option 2: Railway.app (Easy & Fast)

1. **Go to [Railway.app](https://railway.app)**

2. **Click "Start a New Project"**:
   - Select "Deploy from GitHub repo"
   - Connect your `ecommerce-backend` repository

3. **Add PostgreSQL**:
   - Click "+ New" → "Database" → "Add PostgreSQL"

4. **Configure environment variables**:
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   SECRET_KEY=<generate with: openssl rand -hex 32>
   ENVIRONMENT=production
   ALLOWED_ORIGINS=*
   ```

5. **Deploy!** Railway will auto-deploy on every push

6. **Seed data**:
   - Open the deployment shell
   - Run: `python scripts/seed_demo_data.py`

---

### Option 3: Fly.io (More control)

1. **Install flyctl**:
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Create fly.toml** in your project root:
   ```toml
   app = "your-app-name"

   [build]

   [env]
   PORT = "8000"

   [[services]]
   http_checks = []
   internal_port = 8000
   processes = ["app"]
   protocol = "tcp"
   script_checks = []

   [[services.ports]]
   force_https = true
   handlers = ["http"]
   port = 80

   [[services.ports]]
   handlers = ["tls", "http"]
   port = 443
   ```

3. **Deploy**:
   ```bash
   fly auth login
   fly launch
   fly postgres create
   fly postgres attach <your-postgres-app>
   fly secrets set SECRET_KEY=$(openssl rand -hex 32)
   fly deploy
   ```

4. **Seed data**:
   ```bash
   fly ssh console
   python scripts/seed_demo_data.py
   exit
   ```

---

## 📊 After Deployment

### Test Your API

1. **Check health**:
   ```bash
   curl https://your-app.com/health
   ```

2. **Login as demo customer**:
   ```bash
   curl -X POST https://your-app.com/api/v1/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=customer@demo.com&password=customer123"
   ```

3. **Browse products**:
   ```bash
   curl https://your-app.com/api/v1/products
   ```

### Share Your Demo

Add these links to your GitHub README:

```markdown
## 🌐 Live Demo

- **API**: https://your-app.com
- **Interactive Docs**: https://your-app.com/docs
- **Demo Page**: https://your-app.com/demo/

### Try it out!

**Demo Credentials:**
- Customer: `customer@demo.com` / `customer123`
- Seller: `seller@demo.com` / `seller123`
- Admin: `admin@demo.com` / `admin123`
```

---

## 🔧 Environment Variables

Required for all platforms:

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Auto-set by platform |
| `SECRET_KEY` | JWT secret (32+ chars) | `openssl rand -hex 32` |
| `ENVIRONMENT` | production/staging/development | `production` |
| `ALLOWED_ORIGINS` | CORS origins | `*` or specific domains |

Optional:

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT expiry |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## 🎯 Update Your GitHub README

After deployment, update your README with:

1. Add a "Live Demo" badge:
   ```markdown
   [![Live Demo](https://img.shields.io/badge/demo-live-green.svg)](https://your-app.com)
   ```

2. Add the demo URL at the top

3. Add demo credentials

This will make your project much more impressive to potential employers! 🚀

---

## 🆘 Troubleshooting

**App won't start?**
- Check logs in your platform's dashboard
- Verify all environment variables are set
- Ensure DATABASE_URL is correct

**Database connection errors?**
- Make sure PostgreSQL is running
- Check DATABASE_URL format
- For Railway: Use `${{Postgres.DATABASE_URL}}`

**Can't access /docs?**
- Docs are only enabled in development by default
- Set `DEBUG=true` to enable in production (not recommended)

**Need help?**
- Check platform-specific docs
- Open an issue on GitHub
- Review application logs
