from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
import re
import random
from datetime import datetime
from difflib import get_close_matches

app = Flask(__name__)

# Add CORS headers for local development
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# Load dataset
DATA_FILE = "disease_symptom_dataset.csv"

if not os.path.exists(DATA_FILE):
    raise FileNotFoundError(f"{DATA_FILE} not found! Make sure it exists in the project folder.")

dataset = pd.read_csv(DATA_FILE)
# Get symptom column names (all columns except 'disease')
symptom_cols = [col for col in dataset.columns if col.lower() != 'disease']

# All possible symptoms (normalized: with and without underscores/spaces)
all_symptoms = set(symptom_cols)
# Also add versions with spaces instead of underscores for matching
for symptom in symptom_cols:
    all_symptoms.add(symptom.replace('_', ' '))

# Normalize symptom name (handle underscores/spaces variations)
def normalize_symptom(symptom_name):
    """Convert symptom name to match dataset format (underscores)"""
    return symptom_name.replace(' ', '_').lower()

# Extract symptoms from natural language text
def extract_symptoms(text):
    """Extract potential symptoms from natural language input"""
    text_lower = text.lower()
    found_symptoms = []
    
    # Check each known symptom (try both underscore and space versions)
    for symptom in symptom_cols:
        symptom_lower = symptom.lower()
        symptom_spaces = symptom_lower.replace('_', ' ')
        
        # Check for exact match - try space version first (more common in natural language)
        # Use word boundaries to avoid partial matches
        pattern_spaces = r'\b' + re.escape(symptom_spaces) + r'\b'
        if re.search(pattern_spaces, text_lower):
            found_symptoms.append(symptom)
            continue
        
        # For underscore versions, check if the words appear together
        if '_' in symptom_lower:
            # Split by underscore and check if all words appear together
            words = symptom_lower.split('_')
            if len(words) == 2:
                # Check if both words appear near each other (within a few words)
                pattern = r'\b' + re.escape(words[0]) + r'\b.*?\b' + re.escape(words[1]) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    found_symptoms.append(symptom)
            else:
                # Single word symptoms
                pattern = r'\b' + re.escape(symptom_lower) + r'\b'
                if re.search(pattern, text_lower):
                    found_symptoms.append(symptom)
        else:
            # Single word symptom
            pattern = r'\b' + re.escape(symptom_lower) + r'\b'
            if re.search(pattern, text_lower):
                found_symptoms.append(symptom)
    
    return list(set(found_symptoms))  # Remove duplicates

# Fuzzy match
def match_symptom(input_symptom):
    """Match input symptom to database symptom using fuzzy matching"""
    input_lower = input_symptom.lower().strip()
    
    # Try exact match first (handle spaces/underscores)
    normalized_input = normalize_symptom(input_lower)
    for symptom in symptom_cols:
        if symptom.lower() == normalized_input or symptom.lower().replace('_', ' ') == input_lower:
            return symptom
    
    # Try fuzzy matching with lower threshold
    all_symptoms_list = list(all_symptoms)
    match = get_close_matches(input_lower, all_symptoms_list, n=1, cutoff=0.5)
    if match:
        matched = match[0]
        # Return the original column name (with underscore if needed)
        if matched in symptom_cols:
            return matched
        else:
            # Convert space version back to underscore version
            return normalize_symptom(matched)
    
    return None

# Predict disease
def predict_disease(symptoms_input):
    """
    Predict disease from symptoms input.
    Can handle: comma-separated list, natural language, or both
    """
    recognized = []
    unrecognized = []
    
    # First, try to extract symptoms directly from the text (natural language)
    extracted = extract_symptoms(symptoms_input)
    if extracted:
        recognized.extend(extracted)
    
    # Also try comma-separated approach
    symptoms_list = [s.strip() for s in symptoms_input.split(",") if s.strip()]
    
    for symptom in symptoms_list:
        # Skip if already recognized from extraction
        symptom_normalized = normalize_symptom(symptom)
        already_found = any(s.lower() == symptom_normalized or 
                          s.lower().replace('_', ' ') == symptom.lower() 
                          for s in recognized)
        
        if not already_found:
            matched = match_symptom(symptom)
            if matched:
                if matched not in recognized:
                    recognized.append(matched)
            else:
                unrecognized.append(symptom)
    
    # Remove duplicates while preserving order
    recognized = list(dict.fromkeys(recognized))
    
    if not recognized:
        return None, unrecognized, []

    # Create mask for matching symptoms (check if symptom column has value 1)
    mask = pd.Series([False] * len(dataset))
    for symptom in recognized:
        if symptom in symptom_cols:
            mask = mask | (dataset[symptom] == 1)
    
    temp_df = dataset[mask]

    if temp_df.empty:
        return "Unknown / No matching symptoms found", unrecognized, recognized
    else:
        # Get the most common disease, handling edge cases
        # Note: column name is 'disease' (lowercase) in the dataset
        mode_result = temp_df['disease'].mode()
        if len(mode_result) > 0:
            return mode_result.iloc[0], unrecognized, recognized
        else:
            # If no mode, return the first disease in the filtered dataset
            return temp_df['disease'].iloc[0], unrecognized, recognized

# Handle conversational messages
def handle_conversation(message, name=""):
    """Handle conversational messages like greetings, thanks, etc."""
    message_lower = message.lower().strip()
    
    # Greetings
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 
                 'greetings', 'what\'s up', 'sup', 'howdy']
    if any(msg in message_lower for msg in greetings):
        if name:
            return f"Hello {name}! I'm here to help you with your health concerns. How can I assist you today?"
        return "Hello! I'm your Health AI Assistant. How can I help you with your symptoms today?"
    
    # Thanks and appreciation
    thanks = ['thank you', 'thanks', 'thank', 'appreciate', 'grateful', 'ty', 'thx']
    if any(msg in message_lower for msg in thanks):
        responses = [
            "You're very welcome! I'm glad I could help. Is there anything else you'd like to know?",
            "You're welcome! Feel free to ask if you have any other questions about your health.",
            "My pleasure! If you need any more assistance with your symptoms, just let me know.",
            "You're welcome! I'm here whenever you need help. Take care!"
        ]
        return random.choice(responses)
    
    # How are you / How's it going
    how_are_you = ['how are you', 'how are things', 'how\'s it going', 'how do you do']
    if any(msg in message_lower for msg in how_are_you):
        return "I'm doing well, thank you for asking! I'm here and ready to help you with any health questions or symptoms you might have. What can I help you with today?"
    
    # Goodbye
    goodbyes = ['bye', 'goodbye', 'see you', 'farewell', 'later', 'cya', 'good night']
    if any(msg in message_lower for msg in goodbyes):
        if name:
            return f"Goodbye {name}! Take care of yourself and feel better soon!"
        return "Goodbye! Take care and feel better soon!"
    
    # Help request
    help_words = ['help', 'what can you do', 'what do you do', 'how does this work']
    if any(msg in message_lower for msg in help_words):
        available_symptoms = ", ".join([s.replace('_', ' ') for s in sorted(symptom_cols)])
        return f"I'm a Health AI Assistant that helps predict diseases based on symptoms. You can describe your symptoms in natural language (e.g., 'I have fever and headache') or as a list (e.g., 'fever, headache, cough').\n\nAvailable symptoms I can recognize: {available_symptoms}\n\nJust tell me what symptoms you're experiencing, and I'll help analyze them!"
    
    # Polite responses
    polite = ['please', 'could you', 'would you', 'can you help']
    if any(msg in message_lower for msg in polite) and len(message_lower.split()) < 5:
        return "Of course! I'd be happy to help. Please tell me about any symptoms you're experiencing."
    
    return None  # Not a conversational message

# Save report
def save_report(name, age, gender, symptoms, disease):
    df = pd.DataFrame([{
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Age": age,
        "Gender": gender,
        "Symptoms": symptoms,
        "Predicted Disease": disease
    }])
    header = not os.path.exists("reports.csv")
    df.to_csv("reports.csv", mode="a", index=False, header=header)

# Routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"response": "Invalid request. Please provide your information."}), 400
        
        name = data.get("name", "").strip()
        age = data.get("age", "").strip()
        gender = data.get("gender", "").strip()
        symptoms_input = data.get("message", "").strip()

        if not symptoms_input:
            return jsonify({"response": "Please provide your symptoms or feel free to ask me anything!"})

        # First, check if it's a conversational message
        conversation_response = handle_conversation(symptoms_input, name)
        if conversation_response:
            return jsonify({"response": conversation_response})

        # Otherwise, treat it as a symptom query
        disease, unrecognized, recognized = predict_disease(symptoms_input)

        if disease is None:
            # Provide helpful feedback with available symptoms
            available_symptoms = ", ".join([s.replace('_', ' ') for s in sorted(symptom_cols)])
            response_text = "I couldn't recognize any symptoms from your input. "
            response_text += f"Please try using symptom names like: {available_symptoms}. "
            response_text += "You can write them naturally (e.g., 'I have fever and headache') or as a list (e.g., 'fever, headache, cough')."
            return jsonify({"response": response_text})

        # Format recognized symptoms for display
        recognized_display = [s.replace('_', ' ') for s in recognized]
        
        try:
            save_report(name, age, gender, ", ".join(recognized_display), disease)
        except Exception as e:
            # Log error but don't fail the response
            print(f"Error saving report: {e}")

        # Create a more conversational response
        if name:
            response_text = f"Hi {name}, based on the symptoms you've described ({', '.join(recognized_display)}), I believe you may have: **{disease}**. "
        else:
            response_text = f"Based on your symptoms ({', '.join(recognized_display)}), you may have: **{disease}**. "
        
        response_text += "Your report has been saved successfully. "
        response_text += "Please remember that this is an AI-based prediction and not a substitute for professional medical advice. "
        response_text += "I recommend consulting with a healthcare professional for a proper diagnosis and treatment."
        
        if unrecognized:
            response_text += f"\n\nNote: I couldn't recognize the following symptoms: {', '.join(unrecognized)}. They weren't included in the analysis."

        return jsonify({"response": response_text})
    
    except Exception as e:
        # Log the error for debugging
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({"response": f"I encountered an error: {error_msg}. Please try again."}), 500

@app.route("/download_report")
def download_report():
    if os.path.exists("reports.csv"):
        return send_file("reports.csv", as_attachment=True)
    return "No report available yet."

if __name__ == "__main__":
    # Get port from environment variable (for cloud deployment) or use default
    port = int(os.environ.get("PORT", 5000))
    # Use 0.0.0.0 if PORT is set (cloud deployment), otherwise 127.0.0.1 for local
    # Cloud services like Render set PORT automatically
    is_cloud = "PORT" in os.environ and os.environ.get("PORT") != "5000"
    host = "0.0.0.0" if is_cloud else "127.0.0.1"
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true" and not is_cloud
    
    print(f"\n{'='*50}")
    print(f"🚀 Starting Flask server...")
    if is_cloud:
        print(f"☁️  Cloud deployment mode")
        print(f"📡 Server running on port: {port}")
        print(f"🌐 Your app will be accessible via the cloud URL")
    else:
        print(f"💻 Local development mode")
        print(f"📡 Server running at: http://127.0.0.1:{port}")
        print(f"🌐 Or try: http://localhost:{port}")
    print(f"{'='*50}\n")
    app.run(debug=debug, host=host, port=port)
