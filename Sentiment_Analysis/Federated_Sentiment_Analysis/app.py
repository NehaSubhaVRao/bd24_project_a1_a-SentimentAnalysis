from flask import Flask, render_template, request, redirect, url_for
from model import train_model, predict_model

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    keyword1 = request.form.get('keyword1')
    keyword2 = request.form.get('keyword2')
    keywords_list = []

    if keyword1:
        keywords_list.append(keyword1.strip())
    if keyword2:
        keywords_list.append(keyword2.strip())
        
    if keywords_list:
        try:
            sentiment_plot_path, total_positive_sentiment = predict_model(keywords_list)
            return render_template('search_results.html', keywords=keywords_list, sentiment_plot_path=sentiment_plot_path, total_positive_sentiment=total_positive_sentiment)
        except Exception as e:
            error_message = f"Error occurred during prediction: {str(e)}"
            return render_template('error.html', error_message=error_message)
    else:
        try:
            print("Staring training the model")
            train_model()
            return redirect(url_for('index'))
        except Exception as e:
            error_message = f"Error occurred during training: {str(e)}"
            return render_template('error.html', error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
