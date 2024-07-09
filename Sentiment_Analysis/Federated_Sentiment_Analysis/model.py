import os
import sys
import warnings
import json
import re
import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import tensorflow_federated as tff
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime

file_path = r'\Sentiment_Analysis\Federated_Sentiment_Analysis\DATA\processed-data.json'
keras_model_path = r'\Sentiment_Analysis\Federated_Sentiment_Analysis\Model_Parameters\keras_model.h5'

print(file_path)

# # Suppress TensorFlow and other warnings
# os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # TensorFlow logging
# warnings.filterwarnings("ignore")  # General warnings

# # Suppress specific TensorFlow logs
# tf.get_logger().setLevel('ERROR')

# # Suppress all errors by redirecting stderr
# sys.stderr = open(os.devnull, 'w')

# # Custom error handler to suppress specific exceptions
# def custom_error_handler(type, value, traceback):
#     if issubclass(type, TypeError) and "isinstance() arg 2 must be a type or tuple of types" in str(value):
#         pass
#     else:
#         sys.__excepthook__(type, value, traceback)

# # Install custom error handler
# sys.excepthook = custom_error_handler

def preprocess_text(text):
    text = re.sub(r'[^a-zA-Z\s]', '', text).lower()
    return text

def read_and_split_unlabelled_dataset(file_path):
    comments = []
    created_utc = []
    
    try:
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    data = json.loads(line.strip())
                    # Check if 'body' and 'created_utc' keys exist
                    if 'body' in data and 'created_utc' in data:
                        comment = preprocess_text(data['body'])
                        timestamp = data['created_utc']
                        comments.append(comment)
                        created_utc.append(timestamp)
                except json.JSONDecodeError as e:
                    print(f"JSON decode error: {e}")
                    continue
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

    # Ensure comments and created_utc are not empty
    if not comments or not created_utc:
        print("No valid data found.")
        exit(1)
    
    return comments, created_utc

# Function to read and split dataset into comments, labels, and created_utc
def read_and_split_training_dataset(file_path):
    comments = []
    labels = []
    try:
        with open(file_path, 'r') as file:
            for line in file:
                try:
                    data = json.loads(line.strip())
                    # Check if 'body' and 'label' keys exist
                    if 'body' in data and 'label' in data:
                        comment = preprocess_text(data['body'])
                        label = 1 if data['label'] == 'positive' else 0
                        comments.append(comment)
                        labels.append(label)
                except json.JSONDecodeError as e:
                    pass
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        exit(1)
    except Exception as e:
        print(f"An error occurred: {e}")
        exit(1)

    # Ensure comments and labels are not empty
    if not comments or not labels:
        print("No valid data found.")
        exit(1)
    return comments, labels

# Function to tokenize and pad sequences
def tokenize_and_pad_sequences(comments, max_words=10000, max_length=100):
    tokenizer = Tokenizer(num_words=max_words)
    tokenizer.fit_on_texts(comments)
    sequences = tokenizer.texts_to_sequences(comments)
    padded_sequences = pad_sequences(sequences, padding='post', maxlen=max_length)
    return tokenizer, padded_sequences

# Function to create the Keras model
def create_keras_model():
    """Create a Keras model for sentiment analysis."""
    model = tf.keras.Sequential([
        tf.keras.layers.Embedding(input_dim=10000, output_dim=128),
        tf.keras.layers.LSTM(128),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    return model

# Function to save the Keras model as an h5 file
def save_keras_model_as_h5(state, path):
    """Save the Keras model as an h5 file after federated training."""
    keras_model = create_keras_model()
    # Extract the TFF model weights
    tff_weights = state.model
    keras_model.set_weights(tff_weights.trainable + tff_weights.non_trainable)
    keras_model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
    keras_model.save(path)
    print(f"Keras model saved successfully to {path}")

# Function to load the Keras model from the h5 file
def load_keras_model(path):
    model = tf.keras.models.load_model(path)
    return model

# Load the Keras model weights from h5 file
def load_keras_model_weights(model, path):
    """Load weights into the Keras model from the specified path."""
    model.load_weights(path)

# Function to predict sentiment percentage for given keywords
def predict_sentiment_percentage(model, keywords, comments, created_utc):
    detailed_result = {}
    total_positive_sentiment = {}

    for keyword in keywords:
        keyword_comments = [comments[i] for i in range(len(comments)) if keyword in comments[i]]
        keyword_utc = [created_utc[i] for i in range(len(comments)) if keyword in comments[i]]
        if not keyword_comments:
            detailed_result[keyword] = {'positive': 0, 'negative': 0, 'timestamps': [], 'predictions': []}
            total_positive_sentiment[keyword] = 0
            continue
        
        tokenizer, keyword_padded_sequences = tokenize_and_pad_sequences(keyword_comments)
        predictions = model.predict(keyword_padded_sequences)
        positive_count = np.sum(predictions >= 0.5)
        negative_count = np.sum(predictions < 0.5)

        total_count = positive_count + negative_count
        positive_percentage = round((positive_count / total_count) * 100, 2) if total_count > 0 else 0


        # Store results with timestamps
        detailed_result[keyword] = {
            'positive': positive_percentage,
            'timestamps': keyword_utc,
            'predictions': predictions.flatten()
        }
        total_positive_sentiment[keyword] = positive_percentage

    return detailed_result, total_positive_sentiment

# Function to plot sentiment evolution over time
def plot_sentiment_evolution(sentiment_data, keywords, middle_sample_rate=100, boundary_sample_rate=1):
    plt.figure(figsize=(14, 7))
    
    colors = ['red', 'blue', 'green', 'purple', 'orange']  # Define colors for each keyword

    for idx, keyword in enumerate(keywords):
        timestamps = [datetime.fromtimestamp(ts) for ts in sentiment_data[keyword]['timestamps']]
        positive_predictions = sentiment_data[keyword]['predictions']
        
        # Separate the boundary values and the middle values
        middle_indices = [i for i, val in enumerate(positive_predictions) if 0.1 < val < 0.9]
        boundary_indices = [i for i, val in enumerate(positive_predictions) if val <= 0.1 or val >= 0.9]
        
        # Downsample data points
        middle_indices_sampled = middle_indices[::middle_sample_rate]
        boundary_indices_sampled = boundary_indices[::boundary_sample_rate]
        
        sampled_indices = sorted(set(middle_indices_sampled + boundary_indices_sampled))
        
        timestamps_sampled = [timestamps[i] for i in sampled_indices]
        positive_predictions_sampled = [positive_predictions[i] for i in sampled_indices]

        # Plot using specific color for each keyword
        plt.scatter(timestamps_sampled, positive_predictions_sampled, label=f'Sentiment for "{keyword}"', color=colors[idx % len(colors)], alpha=0.6, edgecolors='w', linewidth=0.5)

    plt.xlabel('Time')
    plt.ylabel('Sentiment Score')
    plt.ylim(-0.1, 1.1)  # Set y-axis limits to show only extreme values
    plt.title(f'Sentiment Evolution for Keywords: {", ".join(keywords)} Over Time')
    plt.legend()
    plt.xticks(rotation=45)
    plt.gcf().autofmt_xdate()
    #plt.show()

    # Ensure 'static' directory exists
    if not os.path.exists('static'):
        os.makedirs('static')

    # Save plot to a file
    static_dir = 'static'
    plot_filename = 'sentiment_plot.png'
    plot_path = os.path.join(static_dir, plot_filename)
    plt.savefig(plot_path)
    plt.close()
    return plot_filename


# Function to handle keyword input and perform sentiment analysis
def analyze_keywords(keras_model, keywords):
    sentiment_data, total_positive_sentiment = predict_sentiment_percentage(keras_model, keywords, comments, created_utc)
    return sentiment_data, total_positive_sentiment
    

def predict_model(keywords):

    # Split into comments,labels,created_utc_list
    global comments, created_utc
    comments, created_utc = read_and_split_unlabelled_dataset(file_path)

    # Load the Keras model
    #keras_model_path = r'D:\Federated Sentiment Analysis\Model_Parameters\keras_model.h5'
    keras_model = load_keras_model(keras_model_path)

    # Perform sentiment analysis
    sentiment_data, total_positive_sentiment = analyze_keywords(keras_model, keywords)

    # Plot sentiment evolution
    sentiment_plot_path = plot_sentiment_evolution(sentiment_data, keywords)

    # Save the plot and return the path along with total positive sentiment
    # Assuming you save the plot and want to return the path
    #sentiment_plot_path = 'static/sentiment_plot.png'

    return sentiment_plot_path, total_positive_sentiment

def train_model():   

        comments, labels = read_and_split_training_dataset(file_path)
       # Tokenize and pad sequences
        tokenizer, padded_sequences = tokenize_and_pad_sequences(comments)

        dataset = tf.data.Dataset.from_tensor_slices((padded_sequences, labels)).batch(32)

        # Split dataset into training and validation
        DATASET_SIZE = len(padded_sequences)
        train_size = int(0.8 * DATASET_SIZE)
        train_dataset = dataset.take(train_size)
        val_dataset = dataset.skip(train_size)


        # Convert to TFF model
        def model_fn():
            """Create and return a TFF model from a Keras model."""
            keras_model = create_keras_model()
            # Load the weights into the Keras model
            load_keras_model_weights(keras_model, keras_model_path)
            return tff.learning.from_keras_model(
                keras_model,
                input_spec=train_dataset.element_spec,
                loss=tf.keras.losses.BinaryCrossentropy(),
                metrics=[tf.keras.metrics.BinaryAccuracy()]
            )

        # Split data equally among clients
        def make_federated_data(client_data, num_clients):
            """Create a list of federated datasets for each client."""
            client_data_list = []
            data_per_client = len(client_data) // num_clients
            for i in range(num_clients):
                client_data_list.append(client_data.skip(i * data_per_client).take(data_per_client))
            return client_data_list
        
        # Create federated data
        client_ids = [0, 1, 2, 3]  # Simulated client IDs
        num_clients = len(client_ids)
        federated_train_data = make_federated_data(train_dataset, num_clients)


        # Define the client optimizer function
        def client_optimizer_fn():
            """Return the Adam optimizer for the client."""
            return tf.keras.optimizers.Adam(learning_rate=0.01)

        # Set up federated training
        iterative_process = tff.learning.build_federated_averaging_process(
            model_fn,
            client_optimizer_fn=client_optimizer_fn
        )

         # Install the default TFF execution context
        tff.backends.native.set_local_execution_context()  # Ensure we have a context for local execution

        # Initialize the federated state
        state = iterative_process.initialize()

        # Run federated training
        NUM_ROUNDS = 5
        for round_num in range(NUM_ROUNDS):
            state, metrics = iterative_process.next(state, federated_train_data)
            print(f'Round {round_num + 1}, Metrics={metrics}')

        # Save the Keras model as an h5 file
        save_keras_model_as_h5(state, keras_model_path)
