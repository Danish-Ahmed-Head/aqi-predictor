# 🌫️ Karachi AQI Predictor

A complete end-to-end machine learning system for predicting Air Quality Index (AQI) in Karachi using serverless architecture.

![AQI Predictor](https://img.shields.io/badge/AQI-Predictor-blue)
![Python](https://img.shields.io/badge/Python-3.10-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Project Overview

This project builds a comprehensive AQI prediction system that:
- ✅ Collects real-time air quality data every hour
- ✅ Processes and engineers features automatically
- ✅ Trains ML models daily with new data
- ✅ Predicts AQI for the next 3 days
- ✅ Provides interactive web dashboard
- ✅ Runs completely serverless with CI/CD automation

## 🏗️ Architecture

```
┌─────────────────┐
│   AQICN API     │
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

## 🚀 Features

### Data Pipeline
- **Automated Data Collection**: Fetches AQI data every hour using GitHub Actions
- **Feature Engineering**: Creates 40+ features including lagged values, rolling statistics, and time-based features
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

## 🛠️ Technology Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.10 |
| **ML Framework** | Scikit-learn |
| **Feature Store** | Hopsworks |
| **Web Framework** | Streamlit |
| **Automation** | GitHub Actions |
| **Data API** | AQICN |
| **Visualization** | Plotly, Matplotlib |
| **Model Explainability** | SHAP |

## 📦 Installation

### Prerequisites
- Python 3.10 or higher
- Git
- GitHub account
- AQICN API token
- Hopsworks account

### Step 1: Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/aqi-predictor.git
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
```
AQICN_TOKEN=your_aqicn_token_here
HOPSWORKS_API_KEY=your_hopsworks_key_here
CITY_NAME=karachi
```

## 🔑 Getting API Keys

### AQICN API Token
1. Visit: https://aqicn.org/data-platform/token/
2. Fill in the form with your details
3. Check your email for the token
4. Add to `.env` file

### Hopsworks API Key
1. Sign up at: https://app.hopsworks.ai/
2. Create a new project (e.g., "aqi-karachi")
3. Go to Project Settings → API Keys
4. Create new API key and copy it
5. Add to `.env` file

## 🎯 Usage

### Run Feature Pipeline (Collect Data)
```bash
python src/feature_pipeline.py
```

This will:
- Fetch current AQI data from AQICN
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

## 🤖 CI/CD Automation

### Setup GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `AQICN_TOKEN`: Your AQICN API token
   - `HOPSWORKS_API_KEY`: Your Hopsworks API key

### Automated Pipelines

**Feature Pipeline** (Hourly)
- Runs every hour automatically
- Collects fresh AQI data
- Updates Feature Store

**Training Pipeline** (Daily)
- Runs at 2 AM UTC daily
- Retrains models with new data
- Updates Model Registry

### Manual Triggers

You can also trigger pipelines manually:
1. Go to: Actions tab in GitHub
2. Select the workflow
3. Click "Run workflow"

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
│   └── utils.py                      # Helper functions
│
├── app/
│   └── streamlit_app.py              # Web dashboard
│
├── data/                             # Local data backups
├── models/                           # Trained models
├── reports/                          # Training reports & plots
├── notebooks/                        # Jupyter notebooks for EDA
│
├── .env.template                     # Environment variables template
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
└── .gitignore                        # Git ignore rules
```

## 📈 Model Performance

| Model | Test RMSE | Test MAE | Test R² |
|-------|-----------|----------|---------|
| Random Forest | TBD | TBD | TBD |
| Gradient Boosting | TBD | TBD | TBD |
| Ridge Regression | TBD | TBD | TBD |

*(Metrics will be updated after first training)*

## 🔍 Key Features Engineered

1. **Time-based Features**
   - Hour of day, day of week, month
   - Weekend indicator, rush hour indicator
   - Cyclical encoding (sin/cos transformations)

2. **Lagged Features**
   - AQI values from 1h, 3h, 6h, 12h, 24h ago

3. **Rolling Statistics**
   - Moving averages (3h, 6h, 12h, 24h windows)
   - Rolling standard deviation
   - Rolling min/max

4. **Change Features**
   - Rate of change
   - Absolute change over different time periods

5. **Pollutant Features**
   - PM2.5, PM10, O3, NO2, SO2, CO levels
   - Pollutant ratios

6. **Weather Features**
   - Temperature, humidity, pressure, wind speed
   - Weather interactions

## 🎨 Dashboard Screenshots

*(Add screenshots here after deployment)*

## 📝 Future Improvements

- [ ] Add weather forecast integration for better predictions
- [ ] Implement ensemble models
- [ ] Add alerting system for hazardous AQI levels
- [ ] Deploy to cloud platform (AWS/GCP/Azure)
- [ ] Add more cities
- [ ] Implement deep learning models (LSTM, Transformers)
- [ ] Add mobile app
- [ ] Real-time notifications

## 🐛 Troubleshooting

### Issue: "No module named 'hopsworks'"
**Solution**: Install requirements: `pip install -r requirements.txt`

### Issue: "Feature group not found"
**Solution**: Run feature pipeline first to create the feature group: `python src/feature_pipeline.py`

### Issue: "Insufficient data for training"
**Solution**: Collect more data by running feature pipeline multiple times or use backfill: `python src/feature_pipeline.py --backfill 7`

### Issue: GitHub Actions not running
**Solution**: Check that secrets are properly set in repository settings

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Danish Ahmed**
- University: Karachi Institute of Economics and Technology
- Domain: Data Sciences
- CGPA: 3.53

## 🙏 Acknowledgments

- 10Pearls for the internship opportunity
- AQICN for providing the air quality data API
- Hopsworks for the feature store platform
- Streamlit for the dashboard framework

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Built with ❤️ for cleaner air in Karachi**