# Odisha Krishi AI - Smart Agriculture Platform

A comprehensive AI-powered agricultural platform for Odisha farmers, featuring 3D visualization, crop prediction, soil analysis, and precision agriculture recommendations.

## 🌾 Features

- **3D Farm Visualization**: Interactive 3D farm models using Three.js and React
- **Crop Prediction**: ML-powered crop yield and health prediction
- **Soil Analysis**: Comprehensive soil health assessment
- **Weather Integration**: Real-time weather data and forecasts
- **Precision Agriculture**: AI-driven farming recommendations
- **Multi-language Support**: Local language support for Odisha farmers
- **Blockchain Integration**: Secure data storage and transaction tracking

## 🏗️ Project Structure

```
odisha-krishi-ai/
├── frontend/          # React + Three.js frontend
├── backend/           # FastAPI backend service
├── ml-service/        # ML prediction service
├── ml-models/         # Machine learning models
├── translations/      # Multi-language support
└── docker-compose.yml # Container orchestration
```

## 🚀 Quick Start

### Option 1: Using Docker (Recommended)

1. **Install Docker Desktop**:
   - Download from [Docker Desktop](https://www.docker.com/products/docker-desktop/)
   - Install and start Docker Desktop

2. **Run the application**:
   ```bash
   # Clone the repository
   git clone https://github.com/suman0309/sih-2.git
   cd sih-2
   
   # Start all services
   docker-compose up --build
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - ML Service: http://localhost:8001

### Option 2: Manual Setup

#### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Git

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### Backend Setup
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

#### ML Service Setup
```bash
cd ml-service
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

## 🛠️ Development

### API Endpoints

#### Backend Service (Port 8000)
- `GET /health` - Health check
- `POST /recommend` - Get farming recommendations

#### ML Service (Port 8001)
- `GET /health` - Health check
- `POST /predict` - Crop prediction

### Environment Variables

Create a `.env` file in the root directory:
```env
DB_USER=postgres
DB_PASSWORD=postgres
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/krishi_ai
```

## 📱 Usage

1. **3D Farm Visualization**: Navigate through your virtual farm
2. **Crop Prediction**: Input field data to get yield predictions
3. **Soil Analysis**: Upload soil samples for health assessment
4. **Weather Monitoring**: View real-time weather conditions
5. **Recommendations**: Get AI-powered farming advice

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Odisha Government for supporting agricultural innovation
- Local farmers for providing valuable feedback
- Open source community for amazing tools and libraries

## 📞 Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**Built with ❤️ for Odisha Farmers**