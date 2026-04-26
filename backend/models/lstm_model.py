import numpy as np
from .base_model import BaseModel

class LSTMForecastModel(BaseModel):
    """LSTM Neural Network for time series forecasting"""
    
    def __init__(self, sequence_length=7):
        super().__init__('LSTM')
        self.sequence_length = sequence_length
        self.model = None
    
    def build_model(self, input_shape):
        """Build LSTM architecture"""
        # Local imports so the rest of the project can run without TensorFlow installed.
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import LSTM, Dense, Dropout

        model = Sequential([
            LSTM(50, activation='relu', return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, activation='relu'),
            Dropout(0.2),
            Dense(25, activation='relu'),
            Dense(1)
        ])
        
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model
    
    def prepare_sequences(self, data):
        """Convert time series to sequences for LSTM"""
        X, y = [], []
        
        for i in range(len(data) - self.sequence_length):
            X.append(data[i:i + self.sequence_length])
            y.append(data[i + self.sequence_length])
        
        return np.array(X), np.array(y)
    
    def train(self, time_series_data, epochs=50, batch_size=32):
        """Train LSTM model"""
        print(f"Training {self.model_name}...")
        
        # Prepare sequences
        X, y = self.prepare_sequences(time_series_data)
        
        # Reshape for LSTM [samples, time steps, features]
        X = X.reshape((X.shape[0], X.shape[1], 1))
        
        # Build model
        self.model = self.build_model((X.shape[1], 1))
        
        # Early stopping to prevent overfitting
        from tensorflow.keras.callbacks import EarlyStopping
        early_stop = EarlyStopping(monitor='loss', patience=10, restore_best_weights=True)
        
        # Train
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            verbose=0,
            callbacks=[early_stop]
        )
        
        self.is_trained = True
        print(f"✅ {self.model_name} trained successfully")
        print(f"Final Loss: {history.history['loss'][-1]:.4f}")
    
    def predict(self, last_sequence):
        """Predict next value given last sequence"""
        if not self.is_trained:
            raise Exception("Model not trained yet!")
        
        # Reshape input
        last_sequence = np.array(last_sequence).reshape((1, self.sequence_length, 1))
        prediction = self.model.predict(last_sequence, verbose=0)
        return max(0, prediction[0][0])
    
    def predict_next_days(self, last_sequence, days=7):
        """Predict next N days"""
        predictions = []
        current_sequence = list(last_sequence)
        
        for _ in range(days):
            # Predict next value
            next_val = self.predict(current_sequence[-self.sequence_length:])
            predictions.append(int(next_val))
            
            # Update sequence
            current_sequence.append(next_val)
        
        return predictions

    def save_model(self, filepath):
        """Save Keras model in native format."""
        import os

        if not self.is_trained or self.model is None:
            raise RuntimeError("LSTM model is not trained; nothing to save.")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        print(f"✅ Model saved to {filepath}")

    def load_model(self, filepath):
        """Load Keras model from disk."""
        from tensorflow.keras.models import load_model

        self.model = load_model(filepath)
        self.is_trained = True
        print(f"✅ Model loaded from {filepath}")