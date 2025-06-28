from flask import Flask, render_template, request, jsonify
from linkedin_post_generator import generate_post

app = Flask(__name__)

# Add CORS headers manually
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Handle preflight requests
@app.route("/generate", methods=["OPTIONS"])
def handle_options():
    return jsonify({"status": "ok"}), 200

@app.route("/")
def start():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    query = request.form.get("query")
    
    if not query:
        return jsonify({"error": "Topic is required"}), 400
    
    try:
        post_content = generate_post(query)
        return jsonify({"content": post_content})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

