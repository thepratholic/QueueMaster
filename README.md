
# QueueMaster 🎫

A modern queue management system built with Flask and PostgreSQL, featuring real-time updates and a sleek UI powered by Tailwind CSS.

## 🌟 Features

- **User Authentication**
  - Secure signup and login
  - Password reset functionality with email verification
  - Profile management

- **Queue Management**
  - Add people to queue with real-time updates
  - Remove/serve people from queue
  - Live queue count and statistics
  - Export queue data to PDF

- **User Interface**
  - Clean, modern design with Tailwind CSS
  - Dark mode support
  - Responsive layout for all devices
  - Interactive notifications

- **Security**
  - Secure password hashing
  - Protected routes
  - Environment variable management
  - Session handling

## 🛠️ Tech Stack

- **Backend:** Python/Flask
- **Database:** PostgreSQL
- **Frontend:** HTML, JavaScript, Tailwind CSS
- **Authentication:** Flask-Login
- **Email Service:** SMTP (Gmail)
- **Additional Libraries:**
  - Flask-SQLAlchemy
  - Flask-Babel (Internationalization)

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL database
- SMTP credentials (for email functionality)

## 🚀 Quick Start

1. Fork this project on Replit
2. Set up your environment variables in Replit Secrets:
   - `SMTP_EMAIL`: Your Gmail address
   - `SMTP_PASSWORD`: Your Gmail app password
   - `DATABASE_URL`: Your PostgreSQL connection string

3. Click the Run button to start the application

## 💡 Usage

1. **Sign Up/Login**
   - Create an account or login with existing credentials
   - Use the forgot password feature if needed

2. **Managing Queues**
   - Add people to queue using the input field
   - Click "Delete" to serve the next person
   - View live queue status
   - Export queue data as needed

3. **Profile Management**
   - Update your username, email, and mobile number
   - Manage your account settings

## 🔐 Environment Variables

Required environment variables:
```
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password
DATABASE_URL=postgresql://username:password@host:5432/database_name
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests.

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👤 Author

**Pratham Chelaramani**
- GitHub: [@thepratholic](https://github.com/thepratholic)
- LinkedIn: [thepratholic](https://www.linkedin.com/in/thepratholic)
- Email: chelaramanipratham@gmail.com

## 🙏 Acknowledgments

- Flask documentation and community
- Tailwind CSS team

## 📱 Support

For support, email chelaramanipratham@gmail.com or create an issue in the repository.
