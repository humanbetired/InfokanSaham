import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertForSequenceClassification, get_linear_schedule_with_warmup
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sqlalchemy import create_engine
from dotenv import load_dotenv
import mlflow
import os

load_dotenv()
mlflow.set_tracking_uri("sqlite:///mlops/mlflow.db")
mlflow.set_experiment("InfokanSaham")

engine = create_engine(os.getenv("DATABASE_URL"))
os.makedirs("models/artifacts/finbert", exist_ok=True)

PARAMS = {
    "model_name":    "ProsusAI/finbert",
    "max_length":    128,
    "batch_size":    8,
    "epochs":        3,
    "learning_rate": 2e-5,
}
LABEL_MAP = {"positive": 0, "neutral": 1, "negative": 2}

# ── Dataset ──────────────────────────────────────────────
class NewsDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.texts     = texts
        self.labels    = labels
        self.tokenizer = tokenizer
        self.max_len   = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        enc = self.tokenizer(
            str(self.texts[idx]),
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids":      enc["input_ids"].squeeze(),
            "attention_mask": enc["attention_mask"].squeeze(),
            "label":          torch.tensor(self.labels[idx], dtype=torch.long)
        }

# ── Training ─────────────────────────────────────────────
def train():
    # Load news sentiment data
    df = pd.read_sql("SELECT * FROM news_sentiment", engine)
    df = df.dropna(subset=["text", "sentiment_label"])
    df = df[df["sentiment_label"].isin(LABEL_MAP.keys())]
    df["label_id"] = df["sentiment_label"].map(LABEL_MAP)

    print(f"Total news data: {len(df)}")
    print(df["sentiment_label"].value_counts())

    # Kalau data terlalu sedikit, augment dengan duplikasi
    if len(df) < 50:
        print("Data news sedikit — augmenting...")
        df = pd.concat([df] * 5, ignore_index=True)
        # Tambahkan sedikit noise pada text supaya tidak identik
        df["text"] = df["text"].apply(
            lambda x: x + " " * np.random.randint(0, 3)
        )
        print(f"Augmented to: {len(df)} rows")

    texts  = df["text"].tolist()
    labels = df["label_id"].tolist()

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels
    )

    tokenizer = BertTokenizer.from_pretrained(PARAMS["model_name"])
    model     = BertForSequenceClassification.from_pretrained(
        PARAMS["model_name"], num_labels=3
    )

    train_loader = DataLoader(
        NewsDataset(X_train, y_train, tokenizer, PARAMS["max_length"]),
        batch_size=PARAMS["batch_size"], shuffle=True
    )
    test_loader = DataLoader(
        NewsDataset(X_test, y_test, tokenizer, PARAMS["max_length"]),
        batch_size=PARAMS["batch_size"]
    )

    optimizer = torch.optim.AdamW(model.parameters(), lr=PARAMS["learning_rate"])
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=len(train_loader),
        num_training_steps=len(train_loader) * PARAMS["epochs"]
    )

    with mlflow.start_run(run_name="FinBERT_finetune_v1"):
        mlflow.log_params(PARAMS)
        best_acc = 0

        for epoch in range(PARAMS["epochs"]):
            # Train
            model.train()
            total_loss = 0
            for batch in train_loader:
                optimizer.zero_grad()
                outputs = model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["label"]
                )
                outputs.loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                total_loss += outputs.loss.item()

            # Eval
            model.eval()
            all_preds, all_labels = [], []
            with torch.no_grad():
                for batch in test_loader:
                    outputs = model(
                        input_ids=batch["input_ids"],
                        attention_mask=batch["attention_mask"]
                    )
                    preds = torch.argmax(outputs.logits, dim=1).numpy()
                    all_preds.extend(preds)
                    all_labels.extend(batch["label"].numpy())

            acc = accuracy_score(all_labels, all_preds)
            avg_loss = total_loss / len(train_loader)

            mlflow.log_metrics({"train_loss": avg_loss, "val_acc": acc}, step=epoch)
            print(f"Epoch {epoch+1}/{PARAMS['epochs']} | loss: {avg_loss:.4f} | acc: {acc:.4f}")

            if acc > best_acc:
                best_acc = acc
                model.save_pretrained("models/artifacts/finbert")
                tokenizer.save_pretrained("models/artifacts/finbert")

        print("\n=== Final Classification Report ===")
        print(classification_report(all_labels, all_preds,
              target_names=["Positive", "Neutral", "Negative"]))

        mlflow.log_metric("best_val_acc", best_acc)
        print(f"\nFinBERT fine-tuning selesai — best acc: {best_acc:.4f}")

if __name__ == "__main__":
    train()