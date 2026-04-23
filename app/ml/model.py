import numpy as np
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout

# 🔷 Rebuild SAME architecture
model = Sequential([
    LSTM(128, return_sequences=True, input_shape=(4, 5)),
    Dropout(0.3),
    LSTM(64),
    Dropout(0.3),
    Dense(32, activation='relu'),
    Dense(1)
])

# 🔷 Load trained weights
model.load_weights("app/ml/lstm_model.h5")


def predict_eta(sequence):
    """
    sequence should be:
    [
      [f1, f2, f3, f4, f5],
      [f1, f2, f3, f4, f5],
      [f1, f2, f3, f4, f5],
      [f1, f2, f3, f4, f5]
    ]
    """

    sequence = np.array(sequence)

    # 🔥 FIX: reshape to (1, 4, 5)
    sequence = sequence.reshape(1, 4, 5)

    prediction = model.predict(sequence, verbose=0)

    return float(prediction[0][0])