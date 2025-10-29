# 🚀 Windows Quick Start Guide

## ⏱️ Total Time: 30-60 minutes (excluding data collection)

---

## 📋 **STEP 1: Check Prerequisites (5 minutes)**

### Open Command Prompt (cmd) and run:

```cmd
python --version
```

**✅ You need Python 3.9 or 3.10**

- If you get "command not found" → Install Python from https://www.python.org/downloads/
- If version is 3.12+ → Download and install Python 3.10 instead
- If version is 3.8 or lower → Download and install Python 3.10

**During Python installation:**
- ✅ CHECK "Add Python to PATH"
- ✅ CHECK "Install pip"

Check Git:
```cmd
git --version
```

If not installed → Download from https://git-scm.com/download/win

---

## 🔑 **STEP 2: Get API Keys (15 minutes)**

### A) OpenWeather API Token

1. Open browser: **(https://home.openweathermap.org/api_keys)**
2. Fill form:
   - Name: Your Name
   - Email: Your Email  
   - Purpose: "Academic project for AQI prediction"
3. Submit → Check email → Copy token
4. **Save it in Notepad for now**

### B) Hopsworks API Key

1. Open browser: **https://app.hopsworks.ai/signup**
2. Sign up → Verify email → Login
3. Click "Create New Project"
   - Name: `aqi-karachi`
   - Click Create
4. Go to Settings (⚙️ icon) → API Keys
5. Click "Create new API key"
   - Name: `aqi-project`
6. **COPY THE KEY IMMEDIATELY** (you only see it once!)
7. **Save it in Notepad**

---

## 📁 **STEP 3: Setup Project (10 minutes)**

### Create Project Folder

```cmd
cd Desktop
mkdir aqi-predictor
cd aqi-predictor
```

### Download Project Files

**Option A: Clone from GitHub (if I give you the repo)**
```cmd
git clone https://github.com/YOUR_USERNAME/aqi-predictor.git
cd aqi-predictor
```

**Option B: Create manually**
Create all files I provided above one by one in correct folders.

### Run Setup Script

```cmd
setup.bat
```

This will:
- Create virtual environment
- Install all dependencies (takes 5-10 minutes)
- Create folders and files

---

## 🔐 **STEP 4: Add API Keys (2 minutes)**

### Edit `.env` file

Open `.env` in Notepad and add your keys:

```
OpenWeather_TOKEN=paste_your_openweather_token_here
HOPSWORKS_API_KEY=paste_your_hopsworks_key_here
CITY_NAME=karachi
```

**Save and close**

### Edit Streamlit secrets

Open `.streamlit\secrets.toml` in Notepad:

```toml
[default]
HOPSWORKS_API_KEY = "paste_your_hopsworks_key_here"
```

**Save and close**

---

## 📊 **STEP 5: Collect Initial Data (Choose One)**

### Activate Virtual Environment First

```cmd
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### Option A: Quick Test (5 minutes)
Collect just ONE data point to test everything:

```cmd
python src\feature_pipeline.py
```

### Option B: Full Backfill (7 days = 2-3 hours)
Collect 7 days of hourly data:

```cmd
python src\feature_pipeline.py --backfill 7
```

**⚠️ This takes time!** It collects data every 10 seconds (168 times for 7 days).

**Recommended:** Start with Option A to test, then run Option B overnight.

---

## 🤖 **STEP 6: Train Model (10 minutes)**

**IMPORTANT:** You need at least 100 data points to train.

After collecting data:

```cmd
python src\training_pipeline.py
```

This will:
- Fetch data from Hopsworks
- Train 4 different models
- Compare performance
- Save best model
- Generate reports

---

## 🌐 **STEP 7: Launch Dashboard (2 minutes)**

```cmd
streamlit run app\streamlit_app.py
```

Browser will open automatically at: **http://localhost:8501**

You should see:
- Current AQI
- 72-hour forecast
- Interactive charts
- Health advisories

**Press Ctrl+C to stop the dashboard**

---

## 🤖 **STEP 8: Setup Automation (10 minutes)**

### Create GitHub Repository

1. Go to **https://github.com** → Login
2. Click **New Repository**
   - Name: `aqi-predictor`
   - Public or Private (your choice)
   - Don't initialize with README (we have one)
3. Click **Create**

### Push Code to GitHub

```cmd
git init
git add .
git commit -m "Initial commit - AQI Predictor"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/aqi-predictor.git
git push -u origin main
```

### Add GitHub Secrets

1. Go to your repository on GitHub
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add two secrets:
   - Name: `OpenWeather_TOKEN`, Value: your token
   - Name: `HOPSWORKS_API_KEY`, Value: your key

### Enable GitHub Actions

1. Go to **Actions** tab
2. Click "I understand, enable them"
3. You should see two workflows:
   - Feature Pipeline (runs hourly)
   - Training Pipeline (runs daily)

---

## ✅ **STEP 9: Verify Everything Works**

### Check Data Collection
```cmd
python src\feature_pipeline.py
```
Should print: "✓ Pipeline completed successfully!"

### Check Training
```cmd
python src\training_pipeline.py
```
Should print model metrics and save reports to `reports/` folder

### Check Dashboard
```cmd
streamlit run app\streamlit_app.py
```
Should open browser with working dashboard

### Check GitHub Actions
Go to repository → Actions tab → Should see scheduled runs

---

## 📊 **STEP 10: Run EDA (Optional)**

```cmd
python notebooks\01_exploratory_data_analysis.py
```

This generates visualizations in `reports/` folder:
- `aqi_distribution.png`
- `aqi_categories.png`
- `temporal_patterns.png`
- `correlation_matrix.png`
- And more...

---

## 🎯 **Daily Usage**

Once everything is setup:

### Check Dashboard
```cmd
venv\Scripts\activate
streamlit run app\streamlit_app.py
```

### Manually Collect Data
```cmd
venv\Scripts\activate
python src\feature_pipeline.py
```

### Manually Retrain Model
```cmd
venv\Scripts\activate
python src\training_pipeline.py
```

**But remember:** GitHub Actions does this automatically!

---

## 🐛 **Common Errors & Fixes**

### Error: "python is not recognized"
**Fix:** Python not in PATH. Reinstall Python and check "Add to PATH"

### Error: "No module named 'hopsworks'"
**Fix:** Activate virtual environment first: `venv\Scripts\activate`

### Error: "Feature group not found"
**Fix:** Run feature pipeline first to create it

### Error: "Insufficient data for training"
**Fix:** Collect more data. Need minimum 100 samples.

### Error: "API error" or "connection failed"
**Fix:** Check your API keys in `.env` file

### Error: GitHub Actions not running
**Fix:** Check secrets are added in repository settings

---

## 📁 **Important Files**

```
aqi-predictor/
├── venv/                    ← Virtual environment (DON'T touch)
├── src/
│   ├── feature_pipeline.py  ← Run this hourly
│   ├── training_pipeline.py ← Run this daily
│   └── utils.py             ← Helper functions
├── app/
│   └── streamlit_app.py     ← Your dashboard
├── data/                    ← Backup data
├── models/                  ← Trained models
├── reports/                 ← Charts and reports
├── .env                     ← YOUR API KEYS (never share!)
├── requirements.txt         ← Dependencies
└── README.md                ← Full documentation
```

---
