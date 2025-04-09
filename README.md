# QueueMaster
QueueMaster is a modern, full-stack web application designed to manage real-life queues for customer service centers (e.g., banks, government offices). It provides real-time queue updates, analytics, and multi-language support using Flask, SocketIO, and PostgreSQL (or SQLite for testing). The project offers a user-friendly interface with dark mode support and an integrated help modal for new users.

## Features


**Real-Time Queue Updates**:
Uses Flask-SocketIO to update the queue and analytics in real time without the need for manual refresh.<br>

**User Authentication**:
Sign-up, login, logout, and password reset functionality implemented with Flask-Login and Flask-Mail.<br>

**Multi-Language Support**:
Integrated with Flask-Babel to support multiple languages (English, Spanish, French).<br>

**Analytics**:
Displays total customers served and average wait time, with an option to export analytics as a PDF report using jsPDF.<br>

**Responsive UI with Dark Mode**:
Built using Tailwind CSS, ensuring a responsive, modern interface with dark mode.<br>

**Help Modal**:
A built-in help modal provides new users with instructions on how to use the application.<br>

## Technologies Used
**Backend**:
Python, Flask, Flask-Login, Flask-Mail, Flask-Babel<br>

**Database**:
SQLite (default for development) and MongoDB (for production, configurable via environment variable)<br>

**Frontend**:
HTML, Tailwind CSS, Vanilla JavaScript, jsPDF<br>

**Others**:
psycopg2 (for PostgreSQL connection pooling)<br>

## Installation
1)Clone the repository:
```sh
git clone https://github.com/thepratholic/QueueMaster.git
```

2)Navigate to the project directory:
```sh
cd QueueMaster
```

3)Create a virtual environment (optional but recommended):
```sh
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```
4)Install the required dependencies:
```sh
pip install -r requirements.txt
```

5)Run the Flask application:
```sh
python app.py
```

6)Open your browser and go to http://127.0.0.1:5000/ to view the application.<br>



## Some real-world use cases:

1)Customer Service Centers: Managing customer queues at service counters (e.g., banks, government offices) to ensure a smooth and orderly process, reducing wait times and improving customer satisfaction.<br>

2)Healthcare Clinics: Organizing patient queues at clinics or hospitals to streamline appointment handling and minimize congestion in waiting areas, allowing healthcare providers to better manage patient flow.<br>

3)Event Management: Handling attendee queues at events, concerts, or exhibitions, ensuring efficient entry and avoiding long lines, while providing real-time updates on queue status.<br>

4)Retail Stores: Managing queues at checkout counters or customer support desks in large retail environments, helping improve service efficiency and reduce perceived wait times.<br>

5)Public Transport Systems: Organizing passenger boarding at bus stations, airports, or train terminals, ensuring a fair and timely boarding process for passengers in line.<br>


## Contributing
1)Fork the repository.<br>
2)Create your feature branch (git checkout -b feature/YourFeature).<br>
3)Commit your changes (git commit -m 'Add some feature').<br>
4)Push to the branch (git push origin feature/YourFeature).<br>
5)Open a Pull Request.<br>

Please feel free to contribute in this project!!