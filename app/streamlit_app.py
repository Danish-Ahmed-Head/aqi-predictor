"""
Streamlit Web Dashboard for AQI Predictions
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hopsworks
import joblib
import sys
import os

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils import get_aqi_category

# Page configuration
st.set_page_config(
    page_title="Karachi AQI Predictor",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .big-metric {
        font-size: 60px;
        font-weight: bold;
        text-align: center;
    }
    .category-text {
        font-size: 24px;
        text-align: center;
        margin-top: -10px;
    }
    .stAlert {
        padding: 1rem;
        border-radius: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def load_model_and_artifacts():
    """Load model, scaler, and feature columns from Hopsworks"""
    try:
        # Connect to Hopsworks
        api_key = st.secrets.get("HOPSWORKS_API_KEY") or os.getenv("HOPSWORKS_API_KEY")
        project = hopsworks.login(api_key_value=api_key)
        mr = project.get_model_registry()
        
        # Download model
        model_meta = mr.get_model("aqi_predictor", version=1)
        model_dir = model_meta.download()
        
        # Load artifacts
        model = joblib.load(f"{model_dir}/aqi_model.pkl")
        scaler = joblib.load(f"{model_dir}/scaler.pkl")
        
        import json
        with open(f"{model_dir}/feature_columns.json", 'r') as f:
            feature_columns = json.load(f)
        
        return model, scaler, feature_columns, True
    
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None, None, None, False

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_latest_features():
    """Fetch latest features from Feature Store"""
    try:
        api_key = st.secrets.get("HOPSWORKS_API_KEY") or os.getenv("HOPSWORKS_API_KEY")
        project = hopsworks.login(api_key_value=api_key)
        fs = project.get_feature_store()
        
        aqi_fg = fs.get_feature_group("aqi_features", version=1)
        df = aqi_fg.read()
        
        # Sort by timestamp and get recent data
        df = df.sort_values('timestamp')
        
        return df, True
    
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return None, False

def prepare_features_for_prediction(latest_data, feature_columns):
    """Prepare features in the correct format for prediction"""
    # Get the most recent row
    latest_row = latest_data.iloc[-1:].copy()
    
    # Ensure all required features are present
    missing_features = set(feature_columns) - set(latest_row.columns)
    
    if missing_features:
        st.warning(f"Missing features: {missing_features}")
        # Fill with zeros or median values
        for feat in missing_features:
            latest_row[feat] = 0
    
    # Select only required features in correct order
    X = latest_row[feature_columns]
    
    return X

def generate_predictions(model, scaler, latest_data, feature_columns, hours=72):
    """
    Generate predictions for next N hours
    Note: This is simplified - in production you'd update features iteratively
    """
    predictions = []
    import pytz
    current_time = datetime.now(pytz.UTC)
    
    # Prepare initial features
    X = prepare_features_for_prediction(latest_data, feature_columns)
    
    # Check if model needs scaled features
    model_name = type(model).__name__
    if 'Ridge' in model_name or 'Lasso' in model_name:
        X_scaled = scaler.transform(X)
        prediction_features = X_scaled
    else:
        prediction_features = X
    
    # Generate predictions (simplified approach)
    for h in range(1, hours + 1):
        pred_aqi = model.predict(prediction_features)[0]
        
        predictions.append({
            'timestamp': current_time + timedelta(hours=h),
            'aqi': max(0, pred_aqi),  # Ensure non-negative
            'hour': h
        })
    
    return pd.DataFrame(predictions)

def plot_aqi_forecast(predictions_df, current_aqi):
    """Create interactive AQI forecast chart"""
    fig = go.Figure()
    
    # Add predicted AQI line
    fig.add_trace(go.Scatter(
        x=predictions_df['timestamp'],
        y=predictions_df['aqi'],
        mode='lines+markers',
        name='Predicted AQI',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6),
        hovertemplate='<b>%{x|%b %d, %H:%M}</b><br>AQI: %{y:.0f}<extra></extra>'
    ))
    
    # Add current AQI as a starting point
    fig.add_trace(go.Scatter(
        x=[datetime.now()],
        y=[current_aqi],
        mode='markers',
        name='Current AQI',
        marker=dict(size=15, color='red', symbol='star'),
        hovertemplate='<b>Now</b><br>AQI: %{y:.0f}<extra></extra>'
    ))
    
    # Add AQI category background bands
    fig.add_hrect(y0=0, y1=50, fillcolor="green", opacity=0.1, line_width=0, annotation_text="Good", annotation_position="right")
    fig.add_hrect(y0=50, y1=100, fillcolor="yellow", opacity=0.1, line_width=0, annotation_text="Moderate", annotation_position="right")
    fig.add_hrect(y0=100, y1=150, fillcolor="orange", opacity=0.1, line_width=0, annotation_text="Unhealthy (Sensitive)", annotation_position="right")
    fig.add_hrect(y0=150, y1=200, fillcolor="red", opacity=0.1, line_width=0, annotation_text="Unhealthy", annotation_position="right")
    fig.add_hrect(y0=200, y1=300, fillcolor="purple", opacity=0.1, line_width=0, annotation_text="Very Unhealthy", annotation_position="right")
    
    fig.update_layout(
        title="AQI Forecast - Next 3 Days",
        xaxis_title="Date & Time",
        yaxis_title="Air Quality Index (AQI)",
        hovermode='x unified',
        height=500,
        showlegend=True,
        legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01)
    )
    
    return fig

def plot_daily_summary(predictions_df):
    """Create daily summary bar chart"""
    # Group by day
    predictions_df['date'] = predictions_df['timestamp'].dt.date
    daily_avg = predictions_df.groupby('date')['aqi'].agg(['mean', 'min', 'max']).reset_index()
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=daily_avg['date'],
        y=daily_avg['mean'],
        name='Average AQI',
        marker_color='lightblue',
        error_y=dict(
            type='data',
            symmetric=False,
            array=daily_avg['max'] - daily_avg['mean'],
            arrayminus=daily_avg['mean'] - daily_avg['min']
        )
    ))
    
    fig.update_layout(
        title="Daily AQI Summary",
        xaxis_title="Date",
        yaxis_title="AQI",
        height=300,
        showlegend=False
    )
    
    return fig

def main():
    """Main dashboard function"""
    
    # Header
    st.title("🌫️ Karachi Air Quality Index Predictor")
    st.markdown("### Real-time AQI Predictions & Air Quality Monitoring")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        forecast_hours = st.slider(
            "Forecast Duration (hours)",
            min_value=12,
            max_value=72,
            value=72,
            step=12
        )
        
        st.markdown("---")
        st.markdown("### 📊 About AQI")
        st.markdown("""
        **AQI Categories:**
        - 🟢 0-50: Good
        - 🟡 51-100: Moderate
        - 🟠 101-150: Unhealthy (Sensitive)
        - 🔴 151-200: Unhealthy
        - 🟣 201-300: Very Unhealthy
        - 🟤 301+: Hazardous
        """)
        
        st.markdown("---")
        st.info("Data updates every hour")
    
    # Load model and data
    with st.spinner("Loading model and data..."):
        model, scaler, feature_columns, model_loaded = load_model_and_artifacts()
        latest_data, data_loaded = get_latest_features()
    
    if not model_loaded or not data_loaded:
        st.error("❌ Unable to load model or data. Please check your configuration.")
        return
    
    # Get current AQI
    current_aqi = latest_data.iloc[-1]['aqi']
    current_timestamp = latest_data.iloc[-1]['timestamp']
    aqi_info = get_aqi_category(current_aqi)
    
    # Current Status Section
    st.markdown("## 📍 Current Air Quality")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"<div class='big-metric' style='color: {aqi_info['color']}'>{int(current_aqi)}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='category-text'>{aqi_info['category']}</div>", unsafe_allow_html=True)
    
    with col2:
        pm25 = latest_data.iloc[-1].get('pm25', 'N/A')
        st.metric("PM2.5", f"{pm25:.1f}" if isinstance(pm25, (int, float)) else pm25, help="Fine particulate matter")
    
    with col3:
        temp = latest_data.iloc[-1].get('temperature', 'N/A')
        st.metric("Temperature", f"{temp:.1f}°C" if isinstance(temp, (int, float)) else temp)
    
    with col4:
        humidity = latest_data.iloc[-1].get('humidity', 'N/A')
        st.metric("Humidity", f"{humidity:.0f}%" if isinstance(humidity, (int, float)) else humidity)
    
    # Health message
    st.info(f"**Health Advisory:** {aqi_info['health_message']}")
    
    st.markdown("---")
    
    # Generate predictions
    with st.spinner("Generating predictions..."):
        predictions_df = generate_predictions(
            model, scaler, latest_data, feature_columns, hours=forecast_hours
        )
    
    # Alert for hazardous conditions
    if current_aqi > 200:
        st.error("🚨 **HAZARDOUS AIR QUALITY ALERT!** 🚨")
        st.error("Health Warning: Everyone may experience serious health effects. Avoid all outdoor activities.")
    elif current_aqi > 150:
        st.warning("⚠️ **UNHEALTHY AIR QUALITY!** ⚠️")
        st.warning("Everyone may begin to experience health effects. Sensitive groups should avoid outdoor activities.")
    
    # Check for predicted hazardous conditions in next 72 hours
    hazardous_predictions = predictions_df[predictions_df['aqi'] > 200]
    if len(hazardous_predictions) > 0:
        st.error(f"⚠️ **ALERT:** Hazardous air quality predicted in the next 72 hours!")
        st.error(f"Expected at: {hazardous_predictions.iloc[0]['timestamp'].strftime('%Y-%m-%d %H:%M')}")
    
    st.markdown("---")
    
    # Forecast Section
    st.markdown("## 📈 AQI Forecast")
    
    # Main forecast chart
    forecast_fig = plot_aqi_forecast(predictions_df, current_aqi)
    st.plotly_chart(forecast_fig, use_container_width=True)
    
    # Statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        avg_24h = predictions_df.head(24)['aqi'].mean()
        st.metric("24h Average", f"{avg_24h:.0f}")
    
    with col2:
        max_72h = predictions_df['aqi'].max()
        max_time = predictions_df.loc[predictions_df['aqi'].idxmax(), 'timestamp']
        st.metric("Peak AQI", f"{max_72h:.0f}", 
                 delta=f"at {max_time.strftime('%m/%d %H:%M')}")
    
    with col3:
        min_72h = predictions_df['aqi'].min()
        st.metric("Lowest AQI", f"{min_72h:.0f}")
    
    # Daily summary
    st.markdown("### 📅 Daily Summary")
    daily_fig = plot_daily_summary(predictions_df)
    st.plotly_chart(daily_fig, use_container_width=True)
    
    # Detailed hourly data
    with st.expander("📋 Detailed Hourly Forecast"):
        # Format the data nicely
        display_df = predictions_df[['timestamp', 'aqi', 'hour']].copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
        display_df['aqi'] = display_df['aqi'].round(1)
        display_df.columns = ['Date & Time', 'Predicted AQI', 'Hours Ahead']
        
        st.dataframe(display_df, use_container_width=True, height=400)
    
    # Historical trends
    st.markdown("---")
    st.markdown("## 📊 Historical Trends")
    
    # Last 7 days - fix timezone awareness
    import pytz
    seven_days_ago = datetime.now(pytz.UTC) - timedelta(days=7)
    recent_data = latest_data[latest_data['timestamp'] >= seven_days_ago]
    
    if len(recent_data) > 0:
        fig_historical = go.Figure()
        
        fig_historical.add_trace(go.Scatter(
            x=recent_data['timestamp'],
            y=recent_data['aqi'],
            mode='lines',
            name='Historical AQI',
            line=dict(color='#ff7f0e', width=2)
        ))
        
        fig_historical.update_layout(
            title="AQI - Last 7 Days",
            xaxis_title="Date",
            yaxis_title="AQI",
            height=400
        )
        
        st.plotly_chart(fig_historical, use_container_width=True)
    else:
        st.warning("Insufficient historical data available")
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Last updated: {current_timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
    st.markdown("*Data source: AQICN | Model: Machine Learning Prediction*")

if __name__ == "__main__":
    main()