import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, classification_report
import mlflow
import mlflow.pytorch
import os

mlflow.set_tracking_uri("sqlite:///mlops/mlflow.db")
mlflow.set_experiment("InfokanSaham")

os.makedirs("models/artifacts", exist_ok=True)

# ── Hyperparameters ──────────────────────────────────────
PARAMS = {
    "hidden_size":   128,
    "num_layers":    2,
    "dropout":       0.3,
    "learning_rate": 0.001,
    "batch_size":    64,
    "epochs":        100,
    "sequence_len":  20,
}

# ── Model Architecture ───────────────────────────────────
class LSTMModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, dropout):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout,
            batch_first=True
        )
        self.batch_norm = nn.BatchNorm1d(hidden_size)
        self.dropout    = nn.Dropout(dropout)
        self.fc         = nn.Linear(hidden_size, 1)
        self.sigmoid    = nn.Sigmoid()

    def forward(self, x):
        out, _ = self.lstm(x)
        out = out[:, -1, :]      
        out = self.batch_norm(out)
        out = self.dropout(out)
        out = self.fc(out)
        return out

# ── Training ─────────────────────────────────────────────
def train():
    # Load data
    X_train = np.load("models/artifacts/X_train.npy")
    X_test  = np.load("models/artifacts/X_test.npy")
    y_train = np.load("models/artifacts/y_train.npy")
    y_test  = np.load("models/artifacts/y_test.npy")

    # Convert ke tensor
    X_train_t = torch.FloatTensor(X_train)
    X_test_t  = torch.FloatTensor(X_test)
    y_train_t = torch.FloatTensor(y_train).unsqueeze(1)
    y_test_t  = torch.FloatTensor(y_test).unsqueeze(1)

    train_loader = DataLoader(
        TensorDataset(X_train_t, y_train_t),
        batch_size=PARAMS["batch_size"], shuffle=True
    )

    input_size = X_train.shape[2]
    model      = LSTMModel(input_size, PARAMS["hidden_size"],
                           PARAMS["num_layers"], PARAMS["dropout"])
    
    # Hitung class weight untuk handle imbalance
    n_neg = (y_train == 0).sum()
    n_pos = (y_train == 1).sum()
    pos_weight = torch.tensor([n_neg / n_pos], dtype=torch.float)
    print(f"Class weight — pos_weight: {pos_weight.item():.2f}")
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)
    optimizer  = torch.optim.Adam(model.parameters(), lr=PARAMS["learning_rate"])
    scheduler  = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5)

    with mlflow.start_run(run_name="LSTM_v1"):
        mlflow.log_params(PARAMS)

        best_val_acc = 0
        for epoch in range(PARAMS["epochs"]):
            # Training
            model.train()
            train_losses = []
            for X_batch, y_batch in train_loader:
                optimizer.zero_grad()
                output = model(X_batch)
                loss   = criterion(output, y_batch)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                train_losses.append(loss.item())

            # Validation
            model.eval()
            with torch.no_grad():
                val_output = model(X_test_t)
                val_loss   = criterion(val_output, y_test_t).item()
                val_preds  = (torch.sigmoid(val_output).squeeze() > 0.5).numpy().astype(int)
                val_acc    = accuracy_score(y_test, val_preds)

            scheduler.step(val_loss)

            avg_train_loss = np.mean(train_losses)
            mlflow.log_metrics({
                "train_loss": avg_train_loss,
                "val_loss":   val_loss,
                "val_acc":    val_acc,
            }, step=epoch)

            if (epoch + 1) % 5 == 0:
                print(f"Epoch {epoch+1}/{PARAMS['epochs']} "
                      f"| train_loss: {avg_train_loss:.4f} "
                      f"| val_loss: {val_loss:.4f} "
                      f"| val_acc: {val_acc:.4f}")

            # Simpan model terbaik
            if val_acc > best_val_acc:
                best_val_acc = val_acc
                torch.save(model.state_dict(), "models/artifacts/lstm_best.pt")
                mlflow.log_artifact("models/artifacts/lstm_best.pt", "lstm_model")

        # Final evaluation
        model.load_state_dict(torch.load("models/artifacts/lstm_best.pt"))
        model.eval()
        with torch.no_grad():
            final_preds = (torch.sigmoid(model(X_test_t)).squeeze() > 0.5).numpy().astype(int)

        print("\n=== Final Classification Report ===")
        print(classification_report(y_test, final_preds,
              target_names=["Turun", "Naik"]))

        mlflow.log_metric("best_val_acc", best_val_acc)

        print(f"\n Done\nbest val accuracy: {best_val_acc:.4f}")

if __name__ == "__main__":
    train()