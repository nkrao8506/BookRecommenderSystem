# 📚 Book Recommender System

A full-stack book recommendation system that suggests books based on collaborative filtering. The system displays popular books and provides personalized recommendations based on user input.

## 🌟 Features

- **Top 50 Popular Books**: Displays the most popular books based on ratings and votes
- **Book Recommendations**: Get personalized book suggestions by entering a book title
- **Modern UI**: Clean, responsive dark-themed interface built with Bootstrap
- **Multiple Frontends**: Flask-based web interface and Next.js modern frontend
- **REST API**: Django backend API for data management

## 🛠️ Tech Stack

### Backend
- **Flask** - Lightweight web framework for the main application
- **Django** - Backend API framework
- **Python** - Core programming language
- **NumPy** - Numerical computations for similarity calculations
- **Pickle** - Serialized ML model storage

### Frontend
- **HTML/CSS** - Flask templates with Bootstrap 5
- **Next.js 16** - Modern React framework (alternative frontend)
- **Tailwind CSS** - Utility-first CSS framework
- **Framer Motion** - Animation library

### Machine Learning
- **Collaborative Filtering** - Recommendation algorithm
- **Cosine Similarity** - Book similarity computation

## 📁 Project Structure

```
BookRecommenderSystem/
├── app.py                  # Flask application entry point
├── manage.py               # Django management script
├── db.sqlite3              # SQLite database
├── Books.csv               # Books dataset
├── Ratings.csv             # User ratings dataset
├── Users.csv               # Users dataset
├── books.pkl               # Processed books data
├── popular.pkl             # Popular books data
├── pt.pkl                  # Pivot table for recommendations
├── similarity_score.pkl    # Pre-computed similarity scores
├── backend/                # Django backend
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/              # Flask HTML templates
│   ├── index.html          # Home page (Top 50 books)
│   └── recommend.html      # Recommendation page
├── web/                    # Next.js frontend
│   ├── src/
│   ├── package.json
│   └── ...
├── model/                  # ML model
│   └── recommender.ipynb   # Jupyter notebook for model training
├── books/                  # Django books app
├── migrations/             # Database migrations
└── uploads/                # User uploads directory
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+ (for Next.js frontend)
- pip (Python package manager)
- npm or yarn (Node package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/BookRecommenderSystem.git
   cd BookRecommenderSystem
   ```

2. **Install Python dependencies**
   ```bash
   pip install flask numpy pandas scikit-learn django django-cors-headers
   ```

3. **Install Node.js dependencies (for Next.js frontend)**
   ```bash
   cd web
   npm install
   cd ..
   ```

## 🏃‍♂️ How to Run

### Option 1: Flask Application (Recommended for quick start)

```bash
python app.py
```

The application will be available at `http://localhost:5000`

### Option 2: Django Backend + Next.js Frontend

1. **Start Django backend**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Backend API will be available at `http://localhost:8000`

2. **Start Next.js frontend** (in a new terminal)
   ```bash
   cd web
   npm run dev
   ```
   Frontend will be available at `http://localhost:3000`

## 📖 How It Works

### Recommendation Algorithm

1. **Data Processing**: The system uses collaborative filtering on book ratings data
2. **Pivot Table**: Creates a user-book rating matrix
3. **Similarity Calculation**: Computes cosine similarity between books
4. **Recommendations**: When a user enters a book title, the system finds the 5 most similar books

### API Endpoints (Flask)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page with top 50 popular books |
| `/recommend` | GET | Recommendation form page |
| `/recommend_books` | POST | Get book recommendations (form data: `user_input`) |

## 📊 Dataset

The project uses book rating datasets containing:
- **Books.csv**: Book information (title, author, image URLs)
- **Ratings.csv**: User ratings for books
- **Users.csv**: User demographic information

## 🎨 Screenshots

### Home Page
- Displays top 50 popular books with cover images, authors, votes, and ratings

### Recommendation Page
- Search box to enter a book title
- Displays 5 similar book recommendations with cover images and authors

## 🔧 Configuration

### Flask Configuration
Edit `app.py` to modify:
- Debug mode settings
- Port configuration
- Template folder location

### Django Configuration
Edit `backend/settings.py` to modify:
- Database settings
- CORS configuration
- Installed apps

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

Your Name - [your.email@example.com](mailto:your.email@example.com)

## 🙏 Acknowledgments

- Book dataset providers
- Bootstrap for UI components
- Flask and Django communities
- Next.js team for the amazing framework
```

This README.md file has been saved to `BookRecommenderSystem/README.md`.
