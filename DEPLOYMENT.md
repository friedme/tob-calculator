# Deployment Guide

Complete guide to deploying your TOB Calculator to various hosting platforms.

## 🎯 Choosing a Platform

| Platform | Free Tier | Ease | Best For |
|----------|-----------|------|----------|
| **Render** | ✅ Yes | ⭐⭐⭐⭐ | Beginners |
| **Railway** | ✅ Yes | ⭐⭐⭐⭐⭐ | Quick deploy |
| **Fly.io** | ✅ Yes | ⭐⭐⭐ | Advanced users |
| **PythonAnywhere** | ✅ Yes | ⭐⭐ | Python-specific |
| **Heroku** | ❌ No* | ⭐⭐⭐⭐ | Popular choice |

*Heroku removed free tier in 2022

---

## 🚀 Render.com (Recommended for Beginners)

### Prerequisites
1. GitHub account
2. Push your code to GitHub

### Steps

1. **Create Render account**
   - Go to https://render.com
   - Sign up with GitHub

2. **Create Web Service**
   - Click "New +"
   - Select "Web Service"
   - Connect your GitHub repository

3. **Configure Settings**
   ```
   Name: tob-calculator
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn app:app
   ```

4. **Add gunicorn**
   Add to `requirements.txt`:
   ```
   gunicorn==21.2.0
   ```

5. **Environment Variables**
   - Go to "Environment"
   - Add: `SECRET_KEY` = (generate random string)
   - Add: `PYTHON_VERSION` = 3.11.0

6. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (~5 minutes)
   - Your app will be at: `https://tob-calculator.onrender.com`

### Free Tier Limitations
- App sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month free

---

## 🚂 Railway.app (Easiest Deployment)

### Steps

1. **Create Railway account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Auto-Configuration**
   Railway automatically detects Flask and configures everything!

4. **Generate Domain**
   - Click "Settings"
   - Click "Generate Domain"
   - Your app is live!

### Additional Setup (Optional)

Add `railway.json`:
```json
{
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "gunicorn app:app",
    "restartPolicyType": "on-failure",
    "restartPolicyMaxRetries": 10
  }
}
```

### Free Tier
- $5 free credit monthly
- ~500 hours of usage
- Auto-sleeps when inactive

---

## ✈️ Fly.io (For Advanced Users)

### Prerequisites
```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Or on Windows with PowerShell:
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Steps

1. **Login**
   ```bash
   fly auth login
   ```

2. **Initialize App**
   ```bash
   cd tob_calculator
   fly launch
   ```

3. **Follow Prompts**
   - App name: `tob-calculator-your-name`
   - Region: Choose closest to you
   - Postgres: No
   - Redis: No
   - Deploy now: Yes

4. **Configure fly.toml**
   Fly generates this automatically, but verify:
   ```toml
   app = "tob-calculator"
   primary_region = "ams"

   [build]
   builder = "paketobuildpacks/builder:base"

   [env]
   PORT = "8080"

   [[services]]
   http_checks = []
   internal_port = 8080
   processes = ["app"]
   protocol = "tcp"
   ```

5. **Deploy**
   ```bash
   fly deploy
   ```

6. **Open App**
   ```bash
   fly open
   ```

### Free Tier
- 3 shared-cpu VMs
- 160GB bandwidth/month
- Auto-sleeps when inactive

---

## 🐍 PythonAnywhere

### Steps

1. **Create Account**
   - Go to https://www.pythonanywhere.com
   - Sign up (free tier available)

2. **Upload Code**
   - Go to "Files" tab
   - Upload all your project files
   - Or use Git:
     ```bash
     git clone https://github.com/your-username/tob-calculator
     ```

3. **Create Virtual Environment**
   - Go to "Consoles" tab
   - Start Bash console
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 tob-env
   cd tob_calculator
   pip install -r requirements.txt
   ```

4. **Create Web App**
   - Go to "Web" tab
   - Click "Add a new web app"
   - Choose "Manual configuration"
   - Python 3.10

5. **Configure WSGI File**
   Click "WSGI configuration file" and edit:
   ```python
   import sys
   path = '/home/yourusername/tob_calculator'
   if path not in sys.path:
       sys.path.append(path)

   from app import app as application
   ```

6. **Set Virtual Environment**
   - In "Virtualenv" section
   - Enter: `/home/yourusername/.virtualenvs/tob-env`

7. **Reload**
   - Click "Reload"
   - Visit: `https://yourusername.pythonanywhere.com`

### Free Tier Limitations
- Must reload every 3 months
- Limited CPU time
- One web app only

---

## 🔧 Production Checklist

Before deploying, ensure:

### Security
- [ ] Change `SECRET_KEY` to random value
- [ ] Set `DEBUG = False` in production
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS (most platforms do this automatically)

### Performance
- [ ] Add gunicorn for production server
- [ ] Configure worker processes
- [ ] Set up file upload limits
- [ ] Add error logging

### Monitoring
- [ ] Set up error tracking (optional: Sentry)
- [ ] Configure log aggregation
- [ ] Monitor uptime
- [ ] Set up alerts

---

## 📝 Environment Variables

Create `.env` file (don't commit to Git!):
```bash
SECRET_KEY=your-random-secret-key-here
DEBUG=False
MAX_CONTENT_LENGTH=16777216
```

Load in `app.py`:
```python
from dotenv import load_dotenv
import os

load_dotenv()
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-key')
```

Install python-dotenv:
```bash
pip install python-dotenv
```

---

## 🐛 Common Deployment Issues

### "Application Error"
- Check logs: `fly logs` or platform-specific command
- Verify all dependencies in requirements.txt
- Check Python version compatibility

### "502 Bad Gateway"
- Gunicorn not starting correctly
- Check start command
- Verify port binding

### "Module not found"
- Missing dependency in requirements.txt
- Run `pip freeze > requirements.txt` locally
- Redeploy

### Files not uploading
- Check `MAX_CONTENT_LENGTH` setting
- Verify upload folder permissions
- Check platform file size limits

---

## 🔄 Continuous Deployment

### GitHub Actions (Auto-deploy on push)

Create `.github/workflows/deploy.yml`:
```yaml
name: Deploy to Render

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Trigger Render Deploy
        run: |
          curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}
```

Add `RENDER_DEPLOY_HOOK` secret in GitHub repo settings.

---

## 💰 Cost Estimates (If Exceeding Free Tier)

| Platform | Hobby Tier | Professional |
|----------|-----------|--------------|
| **Render** | $7/month | $25/month |
| **Railway** | $5/month | $20/month |
| **Fly.io** | ~$5/month | ~$30/month |
| **Heroku** | $7/month | $25/month |

For bi-monthly personal use, free tiers are sufficient!

---

## 🎓 Learning Resources

- **Flask Deployment**: https://flask.palletsprojects.com/en/latest/deploying/
- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **Fly.io Docs**: https://fly.io/docs

---

**Ready to deploy?** Choose your platform and follow the steps above! 🚀
