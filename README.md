# ✈️ FlightPulse

### AI-Powered Flight Delay Prediction & Route Risk Analytics System

FlightPulse is a full-stack machine learning platform that analyzes real-world U.S. Department of Transportation flight data to predict flight delay risk and estimate expected delays.

Built with **Python, Java Spring Boot, React, and PostgreSQL**, the system combines machine learning, statistical analysis, and interactive data visualization to provide flight-level predictions and route, airline, and airport risk analytics.

> **Real Flight Data → Statistical Analysis → Machine Learning → Risk Prediction → Interactive Dashboard**

### 🚀 Key Features

- ✈️ Flight delay probability prediction
- 📊 Expected delay estimation
- 🛫 Route-level risk analysis
- 🏢 Airline performance analytics
- 🏙️ Airport delay analytics
- 📈 Interactive dashboards and visualizations
- 🧮 Statistical and mathematical analysis
- 🤖 Machine learning-based prediction
- 🔍 Model performance and feature analysis
- 🗄️ PostgreSQL-based data and prediction storage

### 🛠️ Tech Stack

**Frontend:** React  
**Backend:** Java + Spring Boot  
**ML & Statistics:** Python, Pandas, NumPy, Scikit-learn, SciPy  
**Database:** PostgreSQL  
**Data:** U.S. Department of Transportation / Bureau of Transportation Statistics

### 🧠 ML Approach

FlightPulse uses historical flight characteristics and engineered features to estimate the probability of a flight being delayed.

The system includes:

- Classification for delay prediction
- Regression for expected delay estimation
- Statistical analysis of flight, airline, airport, and route behavior
- Model evaluation using appropriate classification and regression metrics

### 📊 Analytics

The dashboard provides insights into:

- Delay trends over time
- Airline-wise performance
- Airport-wise delay patterns
- Route risk
- Departure-time patterns
- Delay distributions
- Predicted vs. actual performance
- Machine learning feature importance

### 🏗️ Architecture

```text
                    ┌─────────────────┐
                    │   React Client  │
                    │   Dashboard UI  │
                    └────────┬────────┘
                             │
                          REST API
                             │
                    ┌────────▼────────┐
                    │ Spring Boot API │
                    │    Java Backend │
                    └──────┬─────┬─────┘
                           │     │
                    ┌──────▼─┐ ┌─▼──────────┐
                    │PostgreSQL│ │ Python ML │
                    │ Database │ │  Service  │
                    └──────────┘ └────────────┘
