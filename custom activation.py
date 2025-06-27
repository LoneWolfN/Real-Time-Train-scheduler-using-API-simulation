import numpy as np
import tensorflow as tf
from keras import layers, models
import matplotlib.pyplot as plt
np.random.seed(42)
X = np.linspace(-5, 5, 200).reshape(-1, 1)
y = np.sin(X) + 0.1 * np.random.randn(*X.shape)
class DynamicActivation(tf.keras.layers.Layer):
    def __init__(self, hidden_units=16):
        super(DynamicActivation, self).__init__()
        self.dense1 = layers.Dense(hidden_units, activation='relu')
        self.dense2 = layers.Dense(1)

    def call(self, inputs):
        x_flat = tf.reshape(inputs, [-1, 1])
        x_act = self.dense1(x_flat)
        x_out = self.dense2(x_act)
        return tf.reshape(x_out, tf.shape(inputs))
def build_dynamic_model():
    inputs = tf.keras.Input(shape=(1,))
    x = layers.Dense(32)(inputs)
    x = DynamicActivation()(x)
    x = layers.Dense(1)(x)
    model = tf.keras.Model(inputs, x)
    return model
def build_relu_model():
    model = tf.keras.Sequential([
        layers.Dense(32, activation='relu', input_shape=(1,)),
        layers.Dense(1)
    ])
    return model
dynamic_model = build_dynamic_model()
dynamic_model.compile(optimizer='adam', loss='mse')
dynamic_model.fit(X, y, epochs=100, verbose=0)

# Compile and train baseline model
relu_model = build_relu_model()
relu_model.compile(optimizer='adam', loss='mse')
relu_model.fit(X, y, epochs=1000, verbose=0)
X_test = np.linspace(-5, 5, 300).reshape(-1, 1)
y_pred_dynamic = dynamic_model.predict(X_test)
y_pred_relu = relu_model.predict(X_test)

plt.figure(figsize=(10, 6))
plt.scatter(X, y, label='True Data', alpha=0.4)
plt.plot(X_test, y_pred_dynamic, label='Dynamic Activation', color='green')
plt.plot(X_test, y_pred_relu, label='ReLU Activation', color='red')
plt.title("Dynamic vs ReLU Activation")
plt.legend()
plt.grid(True)
plt.show()