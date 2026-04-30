import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
from joblib import load
import os

# 🔥 CONFIG
MODEL_PATH = "app/ml/lstm_model.h5"
SCALER_PATH = "app/ml/scaler.save"  # optional

# 🔷 Build SAME architecture (must match training)
def build_model():
    model = Sequential([
        LSTM(128, return_sequences=True, input_shape=(4, 5)),
        Dropout(0.3),
        LSTM(64),
        Dropout(0.3),
        Dense(32, activation='relu'),
        Dense(1)
    ])
    return model


# 🔷 Load model
model = build_model()
model.load_weights(MODEL_PATH)

# 🔷 Load scaler (if exists)
scaler = None
if os.path.exists(SCALER_PATH):
    scaler = load(SCALER_PATH)
    print("✅ Scaler loaded")
else:
    print("⚠️ No scaler found — using raw values")


# 🔷 Prediction function
def predict_eta(sequence):
    """
    Input:
    sequence = [
      [f1, f2, f3, f4, f5],
      [f1, f2, f3, f4, f5],
      [f1, f2, f3, f4, f5],
      [f1, f2, f3, f4, f5]
    ]
    """

    try:
        sequence = np.array(sequence, dtype=float)

        # 🔥 Validate shape
        if sequence.shape != (4, 5):
            raise ValueError(f"Expected shape (4,5), got {sequence.shape}")

        # 🔥 Apply scaling if available
        if scaler:
            sequence = scaler.transform(sequence)

        # 🔥 Reshape for LSTM
        sequence = sequence.reshape(1, 4, 5)

        # 🔥 Predict
        prediction = model.predict(sequence, verbose=0)

        eta = float(prediction[0][0])

        # 🔥 Safety clamp (avoid crazy values)
        if eta < 0:
            eta = 0

        return round(eta, 2)

    except Exception as e:
        print("❌ Prediction error:", e)
        return 5.0   # fallback ETA