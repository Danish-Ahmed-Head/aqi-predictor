"""
Training Pipeline: Train and evaluate AQI prediction models
This script runs daily to retrain models with new data
"""
import pandas as pd
import numpy as np
import hopsworks
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge, Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import seaborn as sns
from utils import get_env_variable, print_data_summary

class AQITrainingPipeline:
    """
    Pipeline for training AQI prediction models
    """
    
    def __init__(self, target_hours_ahead=24):
        """
        Initialize training pipeline
        
        Args:
            target_hours_ahead (int): Hours ahead to predict (24 = predict tomorrow)
        """
        self.hopsworks_api_key = get_env_variable('HOPSWORKS_API_KEY')
        self.target_hours = target_hours_ahead
        self.project = None
        self.fs = None
        self.mr = None
        self.models = {}
        self.results = {}
        self.best_model = None
        self.feature_columns = None
        self.scaler = StandardScaler()
        
    def connect_to_hopsworks(self):
        """Connect to Hopsworks"""
        try:
            print("Connecting to Hopsworks...")
            self.project = hopsworks.login(api_key_value=self.hopsworks_api_key)
            self.fs = self.project.get_feature_store()
            self.mr = self.project.get_model_registry()
            print("✓ Connected successfully")
        except Exception as e:
            print(f"✗ Connection failed: {e}")
            raise
    
    def fetch_training_data(self):
        """
        Fetch feature data from Hopsworks Feature Store
        
        Returns:
            pd.DataFrame: Training data
        """
        print("\nFetching training data from Feature Store...")
        
        try:
            aqi_fg = self.fs.get_feature_group("aqi_features", version=1)
            df = aqi_fg.read()
            
            print(f"✓ Fetched {len(df)} records")
            print(f"  Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            
            return df
            
        except Exception as e:
            print(f"✗ Error fetching data: {e}")
            raise
    
    def prepare_features_and_target(self, df):
        """
        Prepare feature matrix X and target vector y
        
        Args:
            df (pd.DataFrame): Raw feature data
            
        Returns:
            tuple: (X, y, feature_names)
        """
        print(f"\nPreparing features for {self.target_hours}h ahead prediction...")
        
        # Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Create target: AQI value N hours in the future
        df['target'] = df['aqi'].shift(-self.target_hours)
        
        # Remove rows with missing target
        df = df.dropna(subset=['target'])
        
        # Define feature columns (exclude non-predictive columns)
        exclude_cols = ['timestamp', 'city', 'target', 'latitude', 'longitude']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        # Handle any remaining NaN values
        df = df.dropna(subset=feature_cols)
        
        X = df[feature_cols]
        y = df['target']
        
        self.feature_columns = feature_cols
        
        print(f"✓ Prepared {len(X)} samples with {len(feature_cols)} features")
        print(f"  Target: AQI {self.target_hours} hours ahead")
        print(f"  Features: {feature_cols[:5]}... (showing first 5)")
        
        return X, y, feature_cols
    
    def train_multiple_models(self, X_train, X_test, y_train, y_test):
        """
        Train and evaluate multiple models
        
        Args:
            X_train, X_test, y_train, y_test: Train/test splits
            
        Returns:
            dict: Results for all models
        """
        print("\n" + "="*60)
        print("TRAINING MODELS")
        print("="*60)
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Define models to train
        self.models = {
            'Random Forest': RandomForestRegressor(
                n_estimators=100,
                max_depth=15,
                min_samples_split=5,
                random_state=42,
                n_jobs=-1
            ),
            'Gradient Boosting': GradientBoostingRegressor(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            ),
            'Ridge Regression': Ridge(alpha=1.0),
            'Lasso Regression': Lasso(alpha=1.0)
        }
        
        # Train and evaluate each model
        for name, model in self.models.items():
            print(f"\n{'='*60}")
            print(f"Training: {name}")
            print(f"{'='*60}")
            
            # Use scaled data for linear models, original for tree-based
            if 'Regression' in name:
                X_tr, X_te = X_train_scaled, X_test_scaled
            else:
                X_tr, X_te = X_train, X_test
            
            # Train
            model.fit(X_tr, y_train)
            
            # Predict
            y_pred_train = model.predict(X_tr)
            y_pred_test = model.predict(X_te)
            
            # Calculate metrics
            train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
            test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
            test_mae = mean_absolute_error(y_test, y_pred_test)
            test_r2 = r2_score(y_test, y_pred_test)
            
            # Cross-validation score
            cv_scores = cross_val_score(
                model, X_tr, y_train, 
                cv=5, 
                scoring='neg_mean_squared_error'
            )
            cv_rmse = np.sqrt(-cv_scores.mean())
            
            # Store results
            self.results[name] = {
                'model': model,
                'train_rmse': train_rmse,
                'test_rmse': test_rmse,
                'test_mae': test_mae,
                'test_r2': test_r2,
                'cv_rmse': cv_rmse,
                'predictions': y_pred_test
            }
            
            # Print results
            print(f"  Train RMSE: {train_rmse:.2f}")
            print(f"  Test RMSE:  {test_rmse:.2f}")
            print(f"  Test MAE:   {test_mae:.2f}")
            print(f"  Test R²:    {test_r2:.3f}")
            print(f"  CV RMSE:    {cv_rmse:.2f}")
            
            # Check for overfitting
            if train_rmse < test_rmse * 0.7:
                print(f"  ⚠️  Warning: Possible overfitting detected")
        
        return self.results
    
    def select_best_model(self):
        """
        Select the best performing model based on test RMSE
        
        Returns:
            tuple: (best_model_name, best_model)
        """
        print("\n" + "="*60)
        print("MODEL COMPARISON")
        print("="*60)
        
        # Create comparison dataframe
        comparison = pd.DataFrame({
            name: {
                'Test RMSE': results['test_rmse'],
                'Test MAE': results['test_mae'],
                'Test R²': results['test_r2'],
                'CV RMSE': results['cv_rmse']
            }
            for name, results in self.results.items()
        }).T
        
        print(comparison.to_string())
        
        # Select best model (lowest test RMSE)
        best_model_name = comparison['Test RMSE'].idxmin()
        self.best_model = self.results[best_model_name]['model']
        
        print(f"\n🏆 Best Model: {best_model_name}")
        print(f"   Test RMSE: {self.results[best_model_name]['test_rmse']:.2f}")
        print(f"   Test R²: {self.results[best_model_name]['test_r2']:.3f}")
        
        return best_model_name, self.best_model
    
    def analyze_feature_importance(self, model_name):
        """
        Analyze and plot feature importance (for tree-based models)
        
        Args:
            model_name (str): Name of the model to analyze
        """
        model = self.results[model_name]['model']
        
        if hasattr(model, 'feature_importances_'):
            print(f"\n{'='*60}")
            print(f"FEATURE IMPORTANCE - {model_name}")
            print(f"{'='*60}")
            
            importance_df = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            print("\nTop 10 Most Important Features:")
            print(importance_df.head(10).to_string(index=False))
            
            # Create reports directory if it doesn't exist
            import os
            os.makedirs('reports', exist_ok=True)
            
            # Save plot
            plt.figure(figsize=(10, 6))
            plt.barh(importance_df.head(15)['feature'], importance_df.head(15)['importance'])
            plt.xlabel('Importance')
            plt.title(f'Top 15 Feature Importances - {model_name}')
            plt.tight_layout()
            plt.savefig('reports/feature_importance.png', dpi=300, bbox_inches='tight')
            print("✓ Feature importance plot saved to reports/feature_importance.png")
            plt.close()
    
    def analyze_with_shap(self, model_name, X_test):
        """
        Use SHAP for model explainability
        
        Args:
            model_name (str): Name of the model
            X_test: Test features
        """
        print(f"\n{'='*60}")
        print(f"SHAP ANALYSIS - {model_name}")
        print(f"{'='*60}")
        
        try:
            import shap
            
            model = self.results[model_name]['model']
            
            # Use TreeExplainer for tree-based models
            if hasattr(model, 'feature_importances_'):
                explainer = shap.TreeExplainer(model)
                # Use subset of test data for faster computation
                X_sample = X_test.sample(min(100, len(X_test)), random_state=42)
                shap_values = explainer.shap_values(X_sample)
                
                # Summary plot
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, plot_type="bar", show=False)
                plt.tight_layout()
                plt.savefig('reports/shap_summary.png', dpi=300, bbox_inches='tight')
                print("✓ SHAP summary plot saved to reports/shap_summary.png")
                plt.close()
                
                # Detailed summary plot
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, show=False)
                plt.tight_layout()
                plt.savefig('reports/shap_detailed.png', dpi=300, bbox_inches='tight')
                print("✓ SHAP detailed plot saved to reports/shap_detailed.png")
                plt.close()
                
                print("✓ SHAP analysis complete")
            else:
                print("⚠️  SHAP analysis only available for tree-based models")
                
        except Exception as e:
            print(f"⚠️  SHAP analysis failed: {e}")
    
    def save_model(self, model, model_name):
        """
        Save model to Hopsworks Model Registry
        
        Args:
            model: Trained model
            model_name (str): Name of the model
        """
        print(f"\nSaving model to Hopsworks Model Registry...")
        
        try:
            # Create directory for model artifacts
            import os
            os.makedirs('models', exist_ok=True)
            
            # Save model
            model_path = 'models/aqi_model.pkl'
            joblib.dump(model, model_path)
            
            # Save scaler
            scaler_path = 'models/scaler.pkl'
            joblib.dump(self.scaler, scaler_path)
            
            # Save feature columns
            feature_path = 'models/feature_columns.json'
            with open(feature_path, 'w') as f:
                json.dump(self.feature_columns, f)
            
            # Save metadata
            metadata = {
                'model_name': model_name,
                'target_hours_ahead': self.target_hours,
                'training_date': datetime.now().isoformat(),
                'metrics': {
                    'test_rmse': float(self.results[model_name]['test_rmse']),
                    'test_mae': float(self.results[model_name]['test_mae']),
                    'test_r2': float(self.results[model_name]['test_r2'])
                }
            }
            
            # Upload to Hopsworks
            aqi_model = self.mr.python.create_model(
                name="aqi_predictor",
                metrics=metadata['metrics'],
                description=f"AQI prediction model ({model_name}) - {self.target_hours}h ahead",
                input_example=None
            )
            
            aqi_model.save('models')
            
            print("✓ Model saved successfully to Hopsworks!")
            
        except Exception as e:
            print(f"✗ Error saving model: {e}")
            print("✓ Model saved locally as backup")
    
    def generate_report(self, y_test, best_model_name):
        """
        Generate training report with visualizations
        
        Args:
            y_test: True values
            best_model_name (str): Name of best model
        """
        print("\nGenerating training report...")
        
        import os
        os.makedirs('reports', exist_ok=True)
        
        y_pred = self.results[best_model_name]['predictions']
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Actual vs Predicted
        axes[0, 0].scatter(y_test, y_pred, alpha=0.5)
        axes[0, 0].plot([y_test.min(), y_test.max()], 
                        [y_test.min(), y_test.max()], 
                        'r--', lw=2)
        axes[0, 0].set_xlabel('Actual AQI')
        axes[0, 0].set_ylabel('Predicted AQI')
        axes[0, 0].set_title('Actual vs Predicted AQI')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Residuals
        residuals = y_test - y_pred
        axes[0, 1].scatter(y_pred, residuals, alpha=0.5)
        axes[0, 1].axhline(y=0, color='r', linestyle='--', lw=2)
        axes[0, 1].set_xlabel('Predicted AQI')
        axes[0, 1].set_ylabel('Residuals')
        axes[0, 1].set_title('Residual Plot')
        axes[0, 1].grid(True, alpha=0.3)
        
        # 3. Error Distribution
        axes[1, 0].hist(residuals, bins=50, edgecolor='black', alpha=0.7)
        axes[1, 0].set_xlabel('Prediction Error')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Distribution of Prediction Errors')
        axes[1, 0].axvline(x=0, color='r', linestyle='--', lw=2)
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Model Comparison
        model_names = list(self.results.keys())
        rmse_values = [self.results[name]['test_rmse'] for name in model_names]
        
        axes[1, 1].barh(model_names, rmse_values)
        axes[1, 1].set_xlabel('Test RMSE')
        axes[1, 1].set_title('Model Comparison')
        axes[1, 1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        plt.savefig('reports/training_report.png', dpi=300, bbox_inches='tight')
        print("✓ Training report saved to reports/training_report.png")
        plt.close()
    
    def run_pipeline(self):
        """
        Execute the complete training pipeline
        """
        print("\n" + "="*60)
        print(f"TRAINING PIPELINE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Step 1: Connect to Hopsworks
        self.connect_to_hopsworks()
        
        # Step 2: Fetch training data
        df = self.fetch_training_data()
        
        if len(df) < 100:
            print(f"✗ Insufficient data for training ({len(df)} samples)")
            print("  Need at least 100 samples. Please collect more data first.")
            return False
        
        # Step 3: Prepare features and target
        X, y, feature_names = self.prepare_features_and_target(df)
        
        # Step 4: Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=False
        )
        
        print(f"\nData split:")
        print(f"  Training samples: {len(X_train)}")
        print(f"  Testing samples:  {len(X_test)}")
        
        # Step 5: Train models
        self.train_multiple_models(X_train, X_test, y_train, y_test)
        
        # Step 6: Select best model
        best_model_name, best_model = self.select_best_model()
        
        # Step 7: Analyze feature importance
        self.analyze_feature_importance(best_model_name)
        
        # Step 7.5: SHAP analysis
        self.analyze_with_shap(best_model_name, X_test)
        
        # Step 8: Generate report
        self.generate_report(y_test, best_model_name)
        
        # Step 9: Save model
        self.save_model(best_model, best_model_name)
        
        print("\n" + "="*60)
        print("✓ TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*60)
        
        return True

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    target_hours = 24  # Default: predict 24 hours ahead
    
    if len(sys.argv) > 1:
        target_hours = int(sys.argv[1])
    
    print(f"Training model to predict AQI {target_hours} hours ahead...")
    
    # Run pipeline
    pipeline = AQITrainingPipeline(target_hours_ahead=target_hours)
    success = pipeline.run_pipeline()
    
    if not success:
        sys.exit(1)