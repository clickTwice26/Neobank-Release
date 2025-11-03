# NeoBank - Expense Tracker

A modern expense tracker web application built with Flask, MongoDB, Redis, TailwindCSS, and Boxicons following the NeoBank design system.

## Features

- � User authentication (register, login, logout)
- 👤 User-specific data isolation
# NeoBank - Expense Tracker

A modern expense tracker web application built with Flask, MongoDB, Redis, TailwindCSS, and Boxicons following the NeoBank design system.

## Features

- � **User Authentication**
  - Username/password registration and login
  - Google OAuth 2.0 integration
  - Session management with Flask-Login
  - Profile pictures from Google
  
- �💰 **Expense Tracking**
  - Track income and expenses
  - Categorize transactions
  - Edit and delete transactions
  - User-specific data isolation

- 📊 **Dashboard & Analytics**
  - Visual dashboard with summary cards
  - Category breakdown with progress bars
  - Recent transactions list
  - Period filtering (week, month, year)

- 🎨 **Modern Design**
  - Clean, minimalist UI following NeoBank guidelines
  - Mobile-first responsive design
  - TailwindCSS styling
  - Boxicons for icons

- ⚡ **Performance & Security**
  - Redis caching for improved performance
  - Rate limiting to prevent abuse
  - Password hashing with Werkzeug
  - User data isolation

## Design System

- **Primary Color:** #0A2540 (Deep Blue)
- **Accent Color:** #10B981 (Vibrant Green)
- **Typography:** Inter/Poppins
- **Icons:** Boxicons
- **CSS Framework:** TailwindCSS

## Tech Stack

- **Backend:** Flask (Python)
- **Authentication:** Flask-Login, Authlib (Google OAuth)
- **Database:** MongoDB Atlas
- **Cache/Rate Limiting:** Redis
- **Frontend:** TailwindCSS, Boxicons
- **Templating:** Jinja2

## Prerequisites

- Python 3.8+
- Redis Server
- MongoDB Atlas account
- Google OAuth 2.0 credentials (for Google login)
- 📊 Visual dashboard with category breakdown
- 🎨 Clean, minimalist design following NeoBank guidelines
- 💾 MongoDB Atlas for data persistence
- ⚡ Redis caching for improved performance
- 🚦 Rate limiting to prevent abuse
- 📱 Mobile-first responsive design
- 🎯 Category-based organization
- 📅 Date filtering (week, month, year)

## Design System

- **Primary Color:** #0A2540 (Deep Blue)
- **Accent Color:** #10B981 (Vibrant Green)
- **Typography:** Inter/Poppins
- **Icons:** Boxicons
- **CSS Framework:** TailwindCSS

## Tech Stack

- **Backend:** Flask (Python)
- **Database:** MongoDB Atlas
- **Cache/Rate Limiting:** Redis
- **Frontend:** TailwindCSS, Boxicons
- **Templating:** Jinja2

## Prerequisites

- Python 3.8+
- Redis Server
- MongoDB Atlas account (credentials in .env)

## Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd /home/raju/30_days_challenge/NeoBank
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install and start Redis:**
   ```bash
   # On Ubuntu/Debian
   sudo apt-get install redis-server
   sudo systemctl start redis-server
   
   # On macOS
   brew install redis
   brew services start redis
   ```

5. **Configure environment variables:**
   The `.env` file should contain:
   ```env
   # MongoDB Configuration
   MONGODB_ATLAS_USER=shagatoc_db_user
   MONGODB_ATLAS_PASSWORD=kdAsOBF2VeXPb9XN
   DB_URL=mongodb+srv://shagatoc_db_user:kdAsOBF2VeXPb9XN@begautos.ieu4t68.mongodb.net/neobank?retryWrites=true&w=majority&appName=begautos
   
   # Flask Secret Key
   SECRET_KEY=your-secret-key-change-in-production
   
   # Redis Configuration
   REDIS_HOST=localhost
   REDIS_PORT=6379
   REDIS_DB=0
   
   # Google OAuth (Get from Google Cloud Console)
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   ```

## Setting Up Google OAuth

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable Google+ API
4. Go to "Credentials" and create "OAuth 2.0 Client ID"
5. Add authorized redirect URIs:
   - `http://localhost:5001/auth/google/callback`
   - `http://127.0.0.1:5001/auth/google/callback`
   - Add your production URL when deploying
6. Copy the Client ID and Client Secret to your `.env` file

## Running the Application

1. **Start the Flask application:**
   ```bash
   python app.py
   ```

2. **Access the application:**
   Open your browser and navigate to:
   ```
   http://localhost:5001
   ```

3. **Create an account:**
   - Click "Create Account" to register with username/email/password
   - Or click "Sign up with Google" to use Google OAuth
   
4. **Start tracking:**
   - Once logged in, use the dashboard to view your finances
   - Click the green + button to add transactions
   - View all transactions in the "Transactions" tab

## Authentication Features

### Regular Login/Registration
- Username-based authentication
- Email validation
- Password hashing with Werkzeug
- Minimum 6 characters password requirement

### Google OAuth Login
- One-click sign-in with Google
- Automatic account creation
- Profile picture integration
- Email linking for existing accounts

## Project Structure

```
NeoBank/
├── app.py                      # Main application file
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── design_guidelines.md        # Design system documentation
├── models/
│   ├── __init__.py
│   ├── transaction.py          # Transaction model
│   └── user.py                 # User model with auth
├── routes/
│   ├── __init__.py
│   ├── auth.py                 # Authentication routes
│   ├── dashboard.py            # Dashboard routes
│   ├── transactions.py         # Transaction CRUD routes
│   └── api.py                  # API endpoints
└── templates/
    ├── base.html               # Base template
    ├── dashboard.html          # Dashboard page
    ├── auth/
    │   ├── login.html          # Login page
    │   └── register.html       # Registration page
    └── transactions/
        ├── list.html           # Transaction list
        └── form.html           # Add/Edit form
```

## API Endpoints

### Authentication Routes

- `GET /auth/login` - Login page
- `POST /auth/login` - Authenticate user
- `GET /auth/register` - Registration page
- `POST /auth/register` - Create new user account
- `GET /auth/logout` - Logout and clear session

### Web Routes (Require Authentication)

- `GET /` - Redirects to dashboard (if logged in) or login page
- `GET /dashboard` - Dashboard with summary
- `GET /transactions` - List all transactions
- `GET /transactions/add` - Add transaction form
- `POST /transactions/add` - Create new transaction
- `GET /transactions/edit/<id>` - Edit transaction form
- `POST /transactions/edit/<id>` - Update transaction
- `POST /transactions/delete/<id>` - Delete transaction

### API Routes

- `GET /api/stats?period=week|month|year` - Get financial statistics
- `GET /api/categories?type=income|expense` - Get categories by type

## Features Details

### User Authentication
- Secure registration with username, email, and password
- Password hashing with Werkzeug security
- Session-based authentication
- User-specific transaction isolation
- Logout functionality

### Transaction Management
- Add income and expenses
- Categorize transactions
- Edit and delete transactions
- Date-based filtering
- All transactions are user-specific

### Dashboard
- View total income, expenses, and balance
- Category breakdown visualization
- Recent transactions list
- Period filtering (week/month/year)

### Caching & Performance
- Redis caching for frequently accessed data
- Automatic cache invalidation on data changes
- Rate limiting to prevent abuse

### Design Features
- Mobile-first responsive design
- Floating Action Button (FAB) for quick add
- Bottom navigation for easy access
- Floating label inputs
- Color-coded transactions (green for income, red for expenses)

## Categories

### Expense Categories
- Food & Dining
- Transportation
- Shopping
- Entertainment
- Bills & Utilities
- Healthcare
- Education
- Other

### Income Categories
- Salary
- Freelance
- Investment
- Gift
- Other

## Development

To run in development mode with debug enabled:
```bash
export FLASK_ENV=development
python app.py
```

## Production Deployment

1. Set proper secret key in `.env`
2. Configure production MongoDB and Redis instances
3. Use a production WSGI server like Gunicorn:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## Troubleshooting

### Redis Connection Issues
If Redis is not available, the app will continue to work but without caching and rate limiting features.

Check Redis status:
```bash
redis-cli ping
# Should return: PONG
```

### MongoDB Connection Issues
Ensure your IP is whitelisted in MongoDB Atlas Network Access settings.

## License

This project is created for educational purposes as part of the 30 Days Challenge.

## Credits

- Design System: NeoBank
- Icons: Boxicons
- CSS: TailwindCSS
- Database: MongoDB Atlas
- Caching: Redis
