from flask import Flask, render_template, request, session
from textblob import TextBlob
import os
import csv
import fitz  # PyMuPDF for PDF reading
from werkzeug.utils import secure_filename
from flask import send_file
import io


app = Flask(__name__)
app.secret_key = "6tudhffeeee"

# Sentiment analysis function
def analyze_textblob(text):
    polarity = TextBlob(text).sentiment.polarity
    if polarity > 0:
        return "Positive", "😊", "green"
    elif polarity < 0:
        return "Negative", "😠", "red"
    else:
        return "Neutral", "😐", "gray"

@app.route("/", methods=["GET", "POST"])
def index():
    if "history" not in session:
        session["history"] = []

    result = emoji = color = ""
    input_text = request.form.get("review", "").strip() if request.method == "POST" else ""

    if request.method == "POST":
        if "clear_history" in request.form:
            session["history"] = []
            session.modified = True
            return render_template("index.html", result=result, emoji=emoji, color=color, input_text="", history=session["history"])

        # Only analyze if input_text is present
        if input_text:
            result, emoji, color = analyze_textblob(input_text)
            session["history"].append({
                "text": input_text,
                "sentiment": result,
                "emoji": emoji,
                "color": color
            })
            session.modified = True

    return render_template("index.html",
                           result=result,
                           emoji=emoji,
                           color=color,
                           input_text=input_text,
                           history=session["history"])
UPLOAD_FOLDER = '/tmp/uploads'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'txt':
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.readlines()
    elif ext == 'csv':
        with open(filepath, 'r', encoding='utf-8') as f:
            return [row[0] for row in csv.reader(f) if row]
    elif ext == 'pdf':
        text_list = []
        doc = fitz.open(filepath)
        for page in doc:
            text_list.extend(page.get_text().split('\n'))
        return text_list
    return []
@app.route("/analyze_file", methods=["POST"])
def analyze_file():
    uploaded_file = request.files.get("file")
    if uploaded_file and allowed_file(uploaded_file.filename):
        filename = secure_filename(uploaded_file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(filepath)

        comments = extract_text_from_file(filepath)
        results = {"Positive": 0, "Negative": 0, "Neutral": 0}
        total = 0

        for comment in comments:
            if comment.strip():
                sentiment, _, _ = analyze_textblob(comment)
                results[sentiment] += 1
                total += 1

        percent = {k: round((v / total) * 100, 2) for k, v in results.items()} if total > 0 else {}
        
        # Create downloadable result
        output = io.StringIO()
        for k, v in percent.items():
            output.write(f"{k}: {v}%\n")
        output.seek(0)

        return send_file(io.BytesIO(output.getvalue().encode('utf-8')),
                         mimetype='text/plain',
                         as_attachment=True,
                         download_name='sentiment_summary.txt')

    return "Invalid file", 400




if __name__ == "__main__":
   app.run(host='0.0.0.0', port=5000, debug=True)




