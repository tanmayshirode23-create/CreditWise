from flask import Flask, render_template, request, jsonify
import pandas as pd
import os
import joblib
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, FunctionTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

app = Flask(__name__)

# Global pipeline object
pipeline = None

def load_or_train_model():
    global pipeline
    if os.path.exists("loan_pipeline.joblib"):
        print("Loading saved pipeline...")
        pipeline = joblib.load("loan_pipeline.joblib")
        return

    print("Training new pipeline...")
    df = pd.read_csv("loan_approval_data.csv")

    # Drop Applicant_ID
    df = df.drop("Applicant_ID", axis=1)

    # Target
    y = df["Loan_Approved"].map({"Yes": 1, "No": 0})
    X = df.drop(columns=["Loan_Approved"])

    # Feature engineering function
    def add_features(X_df):
        X_df = X_df.copy()
        X_df["DTI_Ratio_sq"] = X_df["DTI_Ratio"] ** 2
        X_df["Credit_Score_Sq"] = X_df["Credit_Score"] ** 2
        X_df = X_df.drop(columns=["DTI_Ratio", "Credit_Score"])
        return X_df

    # Column groups
    numeric_features = X.select_dtypes(include=["float64", "int64"]).columns
    categorical_features = X.select_dtypes(include=["object"]).columns

    # Preprocessing
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="mean")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features)
        ]
    )

    # Full pipeline
    pipeline = Pipeline(steps=[
        ("features", FunctionTransformer(add_features)),
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000))
    ])

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    pipeline.fit(X_train, y_train)

    joblib.dump(pipeline, "loan_pipeline.joblib")
    print("Pipeline trained and saved successfully!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.json
        input_df = pd.DataFrame([data])  # single-row DataFrame

        prediction = pipeline.predict(input_df)[0]
        probability = pipeline.predict_proba(input_df)[0]

        result = {
            "prediction": "Approved" if prediction == 1 else "Not Approved",
            "probability_approved": round(probability[1] * 100, 2),
            "probability_rejected": round(probability[0] * 100, 2)
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    load_or_train_model()
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug, host="0.0.0.0", port=port)
