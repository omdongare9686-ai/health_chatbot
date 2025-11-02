# Deploy Your Health Chatbot Online

## Option 1: Deploy to Render (Recommended - Free)

### Steps:

1. **Create a GitHub Account** (if you don't have one)
   - Go to https://github.com
   - Sign up for free

2. **Create a Git Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   ```
   
   Then create a new repository on GitHub and push:
   ```bash
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

3. **Deploy to Render**
   - Go to https://render.com
   - Sign up with your GitHub account
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Settings:
     - **Name**: health-chatbot (or any name)
     - **Environment**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Plan**: Free
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Your app will be live at: `https://your-app-name.onrender.com`

## Option 2: Deploy to Railway

1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and deploys
6. Your app will be live at: `https://your-app-name.up.railway.app`

## Option 3: Deploy to PythonAnywhere

1. Go to https://www.pythonanywhere.com
2. Create a free "Beginner" account
3. Upload your files via Web interface or Git
4. Configure WSGI file to point to `app.py`
5. Your app will be at: `yourusername.pythonanywhere.com`

## Option 4: Use ngrok (Temporary tunnel to localhost)

1. Download ngrok from https://ngrok.com
2. Run your Flask app locally: `python app.py`
3. In another terminal, run: `ngrok http 5000`
4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)
5. Share this URL - it works as long as your computer is running

## Files Included:

- `Procfile` - For Heroku/Render deployment
- `render.yaml` - Render deployment config
- Updated `app.py` - Now supports cloud hosting
- `requirements.txt` - Includes gunicorn for production

## Notes:

- Make sure `disease_symptom_dataset.csv` is in your repository
- Free tiers may have cold starts (first request takes longer)
- Some services require credit card for verification (but stay free)

