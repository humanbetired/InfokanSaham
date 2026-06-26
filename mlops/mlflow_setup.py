import mlflow
import os

os.makedirs("mlops", exist_ok=True)
mlflow.set_tracking_uri("sqlite:///mlops/mlflow.db")
mlflow.set_experiment("InfokanSaham")
print("MLflow ready")
print(f"Tracking URI: {mlflow.get_tracking_uri()}")