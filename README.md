# 🌫️ Karachi AQI Predictor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://aqi-predictor-aewykmqnvacleujd4kzero.streamlit.app/)
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **A complete end-to-end machine learning system for predicting Air Quality Index (AQI) in Karachi using serverless architecture**

**Live Dashboard:** https://aqi-predictor-aewykmqnvacleujd4kzero.streamlit.app/

---

## 📋 Project Overview

This project builds a comprehensive AQI prediction system that:
- ✅ Collects real-time air quality data every hour
- ✅ Processes and engineers features automatically
- ✅ Trains ML models daily with new data
- ✅ Predicts AQI for the next 3 days
- ✅ Provides interactive web dashboard
- ✅ Runs completely serverless with CI/CD automation

**Author:** Danish Ahmed | Karachi Institute of Economics & Technology  
**Domain:** Data Sciences | CGPA: 3.53  
**Program:** 10Pearls Shine Internship

---

## 🏗️ Architecture

```
┌─────────────────┐
│ OpenWeather API │
│  (Data Source)  │
└────────┬────────┘
         │
         ↓
┌─────────────────────────┐      ┌──────────────────┐
│  Feature Pipeline       │ ───→ │  Hopsworks       │
│  (Hourly via GH Actions)│      │  Feature Store   │
└─────────────────────────┘      └────────┬─────────┘
                                          │
                                          ↓
                              ┌─────────────────────────┐
                              │  Training Pipeline      │
                              │  (Daily via GH Actions) │
                              └──────────┬──────────────┘
                                         │
                                         ↓
                              ┌─────────────────────┐
                              │  Model Registry     │
                              │  (Best Model)       │
                              └──────────┬──────────┘
                                         │
                                         ↓
                              ┌─────────────────────┐
                              │  Streamlit Dashboard│
                              │  (Predictions)      │
                              └─────────────────────┘
```

---

## 🚀 Features

### Data Pipeline
- **Automated Data Collection**: Fetches AQI data every hour using GitHub Actions
- **Feature Engineering**: Creates 29+ features including lagged values, rolling statistics, and time-based features
- **Feature Store**: Uses Hopsworks for versioned, organized feature storage

### ML Models
- **Multiple Algorithms**: Random Forest, Gradient Boosting, Ridge, Lasso
- **Automatic Model Selection**: Chooses best model based on validation metrics
- **Daily Retraining**: Updates model with fresh data automatically
- **Model Registry**: Stores models with metadata and metrics

### Dashboard
- **Real-time Predictions**: Shows AQI forecast for next 72 hours
- **Interactive Visualizations**: Plotly charts with AQI category bands
- **Health Advisories**: Provides health recommendations based on AQI levels
- **Historical Trends**: Displays past 7 days of AQI data

---

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.10 |
| **ML Framework** | Scikit-learn |
| **Feature Store** | Hopsworks |
| **Web Framework** | Streamlit |
| **Automation** | GitHub Actions |
| **Data API** | OpenWeather |
| **Visualization** | Plotly, Matplotlib |
| **Model Explainability** | SHAP |

---

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Git
- GitHub account
- OpenWeather API key
- Hopsworks account

### Step 1: Clone Repository
```bash
git clone https://github.com/Danish-Ahmed-Head/aqi-predictor.git
cd aqi-predictor
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Setup Environment Variables
Create a `.env` file in the project root:

```bash
cp .env.template .env
```

Edit `.env` and add your credentials:
```env
OPENWEATHER_API_KEY=your_openweather_key_here
HOPSWORKS_API_KEY=your_hopsworks_key_here
CITY_NAME=karachi
CITY_LATITUDE=24.8607
CITY_LONGITUDE=67.0011
```

---

## 🔑 Getting API Keys

### OpenWeather API Key
1. Visit: https://home.openweathermap.org/api_keys
2. Sign up or log in
3. Generate a new API key
4. Wait for it to become active (~10 minutes)
5. Add to `.env` file as `OPENWEATHER_API_KEY`

### Hopsworks API Key
1. Sign up at: https://app.hopsworks.ai/
2. Create a new project (e.g., "aqi-karachi")
3. Go to Project Settings → API Keys
4. Create new API key and copy it
5. Add to `.env` file as `HOPSWORKS_API_KEY`

---

## 🎯 Usage

### Run Feature Pipeline (Collect Data)
```bash
python src/feature_pipeline.py
```

This will:
- Fetch current AQI data from OpenWeather
- Process and engineer features
- Upload to Hopsworks Feature Store

### Backfill Historical Data
```bash
python src/feature_pipeline.py --backfill 7
```

This collects data for the past 7 days (adjust number as needed).

### Train Models
```bash
python src/training_pipeline.py
```

This will:
- Fetch training data from Feature Store
- Train multiple ML models
- Evaluate and compare performance
- Save best model to Model Registry
- Generate training reports

### Run Dashboard
```bash
streamlit run app/streamlit_app.py
```

Access the dashboard at: http://localhost:8501

---

## 🤖 CI/CD Automation

### Setup GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `OPENWEATHER_API_KEY`: Your OpenWeather API key
   - `HOPSWORKS_API_KEY`: Your Hopsworks API key

### Automated Pipelines

**Feature Pipeline (Hourly)**
- Runs every hour automatically
- Collects fresh AQI data
- Updates Feature Store

**Training Pipeline (Daily)**
- Runs at 2 AM UTC daily
- Retrains models with new data
- Updates Model Registry

### Manual Triggers
You can also trigger pipelines manually:
1. Go to: Actions tab in GitHub
2. Select the workflow
3. Click "Run workflow"

---

## 📊 Project Structure

```
aqi-predictor/
│
├── .github/
│   └── workflows/
│       ├── feature_pipeline.yml      # Hourly data collection
│       └── training_pipeline.yml     # Daily model training
│
├── src/
│   ├── feature_pipeline.py           # Data collection & processing
│   ├── training_pipeline.py          # Model training & evaluation
│   ├── utils.py                      # Helper functions
│   ├── fix_feature_store.py          # Feature store management
│   ├── upload_backup.py              # Backup data upload
│   └── create_synthetic_data.py      # Test data generation
│
├── app/
│   ├── streamlit_app.py              # Web dashboard
│   ├── utils.py                      # Dashboard utilities
│   └── model/                        # Model artifacts
│
├── notebooks/
│   └── 01_exploratory_data_analysis.py  # EDA
│
├── data/                             # Local data backups
├── models/                           # Trained models
├── reports/                          # Training reports & plots
│
├── .env.template                     # Environment variables template
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── .gitignore                        # Git ignore rules
```

---

## 📈 Model Performance

### Results

| Model | Test RMSE | Test MAE | Test R² |
|-------|-----------|----------|---------|
| **Ridge Regression** ⭐ | **9.14** | **7.53** | **0.741** |
| Gradient Boosting | 9.70 | 7.61 | 0.708 |
| Random Forest | 10.32 | 8.08 | 0.669 |
| Lasso Regression | 10.96 | 8.70 | 0.627 |

### Best Model: Ridge Regression
- **Test RMSE:** 9.14 (average error ~9 AQI points)
- **Test MAE:** 7.53 (median error ~7.5 AQI points)
- **Test R²:** 0.741 (explains 74% of variance)
- **Why it won:** Best balance between accuracy and generalization

---

## 🔍 Key Features Engineered

### 29+ Features Created:

1. **Time-based Features (12)**
   - Hour of day, day of week, month, year
   - Weekend indicator, rush hour indicator
   - Cyclical encoding (sin/cos transformations)

2. **Lagged Features (5)**
   - AQI values from 1h, 3h, 6h, 12h, 24h ago

3. **Rolling Statistics (16)**
   - Moving averages (3h, 6h, 12h, 24h windows)
   - Rolling standard deviation, min, max

4. **Change Features (4)**
   - Rate of change
   - Absolute change over different time periods

5. **Pollutant Features**
   - PM2.5, PM10, O3, NO2, SO2, CO levels
   - Pollutant ratios

6. **Weather Features**
   - Temperature, humidity, pressure, wind speed
   - Weather interactions

---

## 📝 Future Improvements

- [ ] Add weather forecast integration for better predictions
- [ ] Implement ensemble models
- [ ] Expand to multiple cities (Lahore, Islamabad, Faisalabad)
- [ ] Deploy mobile application
- [ ] Add SMS/Email alert system
- [ ] Implement deep learning models (LSTM, Transformers)
- [ ] Create geographic heatmap visualization
- [ ] Add 5+ year historical trend analysis

---

## 🐛 Troubleshooting

### Issue: "No module named 'hopsworks'"
**Solution:** Install requirements: `pip install -r requirements.txt`

### Issue: "Feature group not found"
**Solution:** Run feature pipeline first: `python src/feature_pipeline.py`

### Issue: "Insufficient data for training"
**Solution:** Collect more data:
```bash
python src/create_synthetic_data.py 7
# OR
python src/feature_pipeline.py --backfill 7
```

### Issue: GitHub Actions not running
**Solution:** Check that secrets are properly set in repository settings

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 👤 Author

**Danish Ahmed**
- 🎓 University: Karachi Institute of Economics & Technology
- 📧 Email: danishahmed.bscs21@iba-suk.edu.pk
- 💼 Domain: Data Sciences | CGPA: 3.53
- 🔗 GitHub: https://github.com/Danish-Ahmed-Head

**Project:** 10Pearls Shine Data Science Internship  
**Submission Date:** November 2025

---

## 🙏 Acknowledgments

- **10Pearls** - For the Shine Internship Program opportunity
- **OpenWeather** - For providing free Air Quality & Weather APIs
- **Hopsworks** - For serverless Feature Store platform
- **Streamlit** - For amazing dashboard framework

---

## 📧 Contact

For questions or support:
- Open an issue on GitHub
- Email: danishahmed.bscs21@iba-suk.edu.pk

---

## 🌟 Project Links

- **Live Dashboard:** https://aqi-predictor-aewykmqnvacleujd4kzero.streamlit.app/
- **GitHub Repository:** https://github.com/Danish-Ahmed-Head/aqi-predictor
- **Hopsworks Feature Store:** https://c.app.hopsworks.ai/p/1271956/fs/1258563/fg/1579512
- **Model Registry:** https://c.app.hopsworks.ai/p/1271956/models/aqi_predictor

---

**Built with ❤️ for cleaner air in Karachi** 🌫️ → 🌤️

---

## 🏆 Key Achievements

- ✅ 74% prediction accuracy (R² = 0.741)
- ✅ 29+ engineered features
- ✅ 4 ML models trained and compared
- ✅ 100% automated pipeline
- ✅ Live dashboard deployed
- ✅ Production-ready serverless system

**Star this repository if you found it helpful!** ⭐
