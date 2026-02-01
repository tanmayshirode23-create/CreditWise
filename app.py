from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
import joblib
import os

app = Flask(__name__)

# Global variables for model and preprocessors
model = None
scaler = None
label_encoder_edu = None
ohe = None

def load_or_train_model():
    """Load saved model or train a new one"""
    global model, scaler, label_encoder_edu, ohe
    
    # Check if model files exist
    if os.path.exists('model.joblib') and os.path.exists('scaler.joblib') and \
       os.path.exists('label_encoder_edu.joblib') and os.path.exists('ohe.joblib'):
        try:
            model = joblib.load('model.joblib')
            scaler = joblib.load('scaler.joblib')
            label_encoder_edu = joblib.load('label_encoder_edu.joblib')
            ohe = joblib.load('ohe.joblib')
            print("Model loaded successfully!")
            return
        except Exception as e:
            print(f"Error loading model: {e}. Training new model...")
    
    # Train new model
    print("Training new model...")
    df = pd.read_csv("loan_approval_data.csv")
    
    # Handle missing values
    categorical_cols = df.select_dtypes(include=['object']).columns
    numerical_cols = df.select_dtypes(include=["float64"]).columns
    
    from sklearn.impute import SimpleImputer
    num_imp = SimpleImputer(strategy="mean")
    df[numerical_cols] = num_imp.fit_transform(df[numerical_cols])
    
    cat_imp = SimpleImputer(strategy="most_frequent")
    df[categorical_cols] = cat_imp.fit_transform(df[categorical_cols])
    
    # Drop Applicant_ID
    df = df.drop("Applicant_ID", axis=1)
    
    # Feature Encoding
    label_encoder_edu = LabelEncoder()
    df["Education_Level"] = label_encoder_edu.fit_transform(df["Education_Level"])
    
    le_loan = LabelEncoder()
    df["Loan_Approved"] = le_loan.fit_transform(df["Loan_Approved"])
    
    # One-hot encoding
    cols = ["Employment_Status", "Marital_Status", "Loan_Purpose", "Property_Area", 
            "Gender", "Employer_Category"]
    ohe = OneHotEncoder(drop="first", sparse_output=False, handle_unknown="ignore")
    encoded = ohe.fit_transform(df[cols])
    encoded_df = pd.DataFrame(encoded, columns=ohe.get_feature_names_out(cols), index=df.index)
    df = pd.concat([df.drop(columns=cols), encoded_df], axis=1)
    
    # Feature Engineering
    df["DTI_Ratio_sq"] = df["DTI_Ratio"] ** 2
    df["Credit_Score_Sq"] = df["Credit_Score"] ** 2
    
    X = df.drop(columns=["Loan_Approved", "Credit_Score", "DTI_Ratio"])
    y = df["Loan_Approved"]
    
    # Train test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scaling
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train model
    model = LogisticRegression()
    model.fit(X_train_scaled, y_train)
    
    # Save model and preprocessors
    joblib.dump(model, 'model.joblib')
    joblib.dump(scaler, 'scaler.joblib')
    joblib.dump(label_encoder_edu, 'label_encoder_edu.joblib')
    joblib.dump(ohe, 'ohe.joblib')
    
    print("Model trained and saved successfully!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        
        # Create DataFrame from input
        input_data = pd.DataFrame({
            'Applicant_Income': [float(data.get('applicant_income', 0))],
            'Coapplicant_Income': [float(data.get('coapplicant_income', 0))],
            'Age': [float(data.get('age', 0))],
            'Dependents': [float(data.get('dependents', 0))],
            'Existing_Loans': [float(data.get('existing_loans', 0))],
            'DTI_Ratio': [float(data.get('dti_ratio', 0))],
            'Credit_Score': [float(data.get('credit_score', 0))],
            'Savings': [float(data.get('savings', 0))],
            'Collateral_Value': [float(data.get('collateral_value', 0))],
            'Loan_Amount': [float(data.get('loan_amount', 0))],
            'Loan_Term': [float(data.get('loan_term', 0))],
            'Employment_Status': [data.get('employment_status', 'Salaried')],
            'Marital_Status': [data.get('marital_status', 'Single')],
            'Loan_Purpose': [data.get('loan_purpose', 'Personal')],
            'Property_Area': [data.get('property_area', 'Urban')],
            'Gender': [data.get('gender', 'Male')],
            'Employer_Category': [data.get('employer_category', 'Private')],
            'Education_Level': [data.get('education_level', 'Graduate')]
        })
        
        # Handle missing values
        numerical_cols = input_data.select_dtypes(include=["float64"]).columns
        categorical_cols = input_data.select_dtypes(include=['object']).columns
        
        from sklearn.impute import SimpleImputer
        num_imp = SimpleImputer(strategy="mean")
        input_data[numerical_cols] = num_imp.fit_transform(input_data[numerical_cols])
        
        cat_imp = SimpleImputer(strategy="most_frequent")
        input_data[categorical_cols] = cat_imp.fit_transform(input_data[categorical_cols])
        
        # Encode Education Level
        input_data["Education_Level"] = label_encoder_edu.transform(input_data["Education_Level"])
        
        # One-hot encode categorical features
        cols = ["Employment_Status", "Marital_Status", "Loan_Purpose", "Property_Area", 
                "Gender", "Employer_Category"]
        encoded = ohe.transform(input_data[cols])
        encoded_df = pd.DataFrame(encoded, columns=ohe.get_feature_names_out(cols), index=input_data.index)
        input_data = pd.concat([input_data.drop(columns=cols), encoded_df], axis=1)
        
        # Feature Engineering
        input_data["DTI_Ratio_sq"] = input_data["DTI_Ratio"] ** 2
        input_data["Credit_Score_Sq"] = input_data["Credit_Score"] ** 2
        
        # Drop Credit_Score and DTI_Ratio (keeping squared versions)
        if "Credit_Score" in input_data.columns:
            input_data = input_data.drop(columns=["Credit_Score"])
        if "DTI_Ratio" in input_data.columns:
            input_data = input_data.drop(columns=["DTI_Ratio"])
        
        # Scale features
        input_scaled = scaler.transform(input_data)
        
        # Make prediction
        prediction = model.predict(input_scaled)[0]
        probability = model.predict_proba(input_scaled)[0]
        
        result = {
            'prediction': 'Approved' if prediction == 1 else 'Not Approved',
            'probability_approved': float(probability[1]) * 100,
            'probability_rejected': float(probability[0]) * 100
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    load_or_train_model()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False') == 'True'
    app.run(debug=debug, host='0.0.0.0', port=port)
