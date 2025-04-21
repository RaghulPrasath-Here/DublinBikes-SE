# 🚲 DublinBikes Prediction Web App

A Flask-based web application that predicts bike availability across Dublin city stations using real-time data and machine learning.

---

## 🌐 Overview

This project integrates multiple components:

- **Flask Web Application**: Interactive UI for displaying live and predicted bike availability.
- **JCDecaux API**: Retrieves live station data every 5 minutes.
- **OpenWeather API**: Retrieves weather data hourly.
- **Amazon RDS (MySQL)**: Stores historical weather and station data.
- **ML Model (Scikit-Learn)**: Predicts bike availability per station.
- **Hosted on AWS EC2**: The web app is deployed via Gunicorn + Nginx.

---

## 📁 Folder Structure

```
DublinBikes-SE/
├── AWS/       # AWS automation scripts (e.g., RDS, EC2 setup)
├── flask_app/       # Flask backend and frontend templates
└── JCDAPI/          # JCDecaux API handlers and DB scripts
```

---

## 🚀 How to Run Locally

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd SWE
```

2. **Set up virtual environment**

```bash
conda create -n swe_project python=3.11
conda activate swe_project
pip install -r requirements.txt
```

3. **Run the app**

```bash
cd flask_app
flask run
```

---

## 🔑 API Keys & Secrets

You need:
- JCDecaux API key
- OpenWeatherMap API key
- Google Maps API key

Store them in a `.env` file or as environment variables.

---

## 🔬 Testing

```bash
python -m unittest discover
coverage run -m unittest discover
coverage html
```

---

## 📊 Machine Learning

Trained using historical JCDecaux + weather data. Predicts bike availability 24 hours ahead.

---

## 📦 Deployment (AWS)

- EC2 + Gunicorn + Nginx
- MySQL on Amazon RDS
- `nohup` to persist app

---