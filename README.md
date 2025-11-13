# Fake Profile Detection in Online Social Networks

A machine learning-based solution to detect fake profiles in social networks using various algorithms including Random Forest, Support Vector Machine (SVM), and Neural Networks.

## 📋 Table of Contents
- [Project Overview](#-project-overview)
- [Features](#-features)
- [Algorithms Used](#-algorithms-used)
- [Installation](#-installation)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Data](#-data)
- [Web Application](#-web-application)
- [Results](#-results)
- [Contributing](#-contributing)
- [License](#-license)

## 🌟 Project Overview
This project aims to identify fake profiles in social networks using machine learning techniques. It analyzes various profile attributes and behavioral patterns to classify profiles as genuine or fake with high accuracy.

## ✨ Features
- Multiple ML models for fake profile detection
- Web-based interface for easy interaction
- Comprehensive model evaluation metrics
- Visualization of results and model performance
- Gender prediction from names
- Profile analysis with detailed insights

## 🤖 Algorithms Used
1. **Random Forest Classifier**
   - Ensemble learning method
   - Handles non-linear data well
   - Provides feature importance

2. **Support Vector Machine (SVM)**
   - Effective in high-dimensional spaces
   - Good for binary classification
   - Handles non-linear decision boundaries

3. **Neural Network**
   - Deep learning approach
   - Can capture complex patterns
   - Requires more computational resources

## 🚀 Installation

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Dependencies
Install the required packages using:
```bash
pip install -r web_requirements.txt
```

### Additional Dependencies
- numpy
- pandas
- scikit-learn
- matplotlib
- Flask
- joblib
- gender-guesser

## 🛠 Usage

### Running the Web Application
1. Navigate to the project directory
2. Run the Flask application:
   ```bash
   python app.py
   ```
3. Open your browser and go to `http://127.0.0.1:5000/`

### Running Individual Models
You can run each model separately:
```bash
# Random Forest
python "Random Forest.py"

# Support Vector Machine
python "Support Vector Machine.py"

# Neural Network
python "Neural Network.py"
```

## 📁 Project Structure
```
Fake-Profile-Detection-using-ML/
├── data/                    # Dataset files
│   ├── users.csv           # Genuine user profiles
│   └── fusers.csv          # Fake user profiles
├── html/                   # HTML outputs
├── pdf/                    # PDF reports
├── saved_model/            # Trained model files
├── templates/              # Web application templates
│   ├── base.html          # Base template
│   └── index.html         # Main page
├── app.py                 # Flask web application
├── check_profile.py        # Profile checking utility
├── predict_profile.py      # Prediction module
├── Random Forest.py        # Random Forest implementation
├── Support Vector Machine.py # SVM implementation
├── Neural Network.py       # Neural Network implementation
└── web_requirements.txt    # Python dependencies
```

## 📊 Data
### Dataset Description
The project uses two main datasets:
1. **Genuine Users** (`users.csv`): Contains features of real user profiles
2. **Fake Users** (`fusers.csv`): Contains features of fake user profiles

### Features
- Profile attributes (name, age, gender, etc.)
- Activity metrics
- Network characteristics
- Profile completeness
- And other relevant features

## 🌐 Web Application
A Flask-based web interface is provided for easy interaction with the models. The web app allows users to:
- Input profile details
- Get real-time predictions
- View confidence scores
- Access model explanations

## 📈 Results
Model performance metrics and visualizations are available in the `html/` and `pdf/` directories, including:
- Confusion matrices
- ROC curves
- Precision-Recall curves
- Feature importance plots

## 🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Freelancer.com for the initial project inspiration
- Open-source community for various libraries and tools
- Contributors who helped improve this project

---

<div align="center">
  <h3>Connect with me:</h3>
  <a href="https://www.linkedin.com/in/yourprofile" target="_blank">
    <img src="https://img.shields.io/badge/LinkedIn-0077B5?style=for-the-badge&logo=linkedin&logoColor=white" alt="LinkedIn">
  </a>
  <a href="https://github.com/yourusername" target="_blank">
    <img src="https://img.shields.io/badge/GitHub-100000?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
</div>
