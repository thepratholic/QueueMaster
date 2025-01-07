# QueueMaster
QueueMaster is a simple queue management web application built using Flask. It allows users to add, remove, search for persons in the queue, and view real-time queue analytics.

## Features

- **Insert**: Add a person to the queue.<br>
- **Delete**: Remove the person at the front of the queue.<br>
- **Analytics**: View real-time data on the average wait time and the total number of people served.<br>

## Technologies Used
Flask: Python web framework used to create the backend.<br>
HTML/CSS: For the frontend interface.<br>
JavaScript: For interactivity and AJAX requests. <br>
Python: Core programming language used in this project.<br>

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


## Usage
### Insert Person into Queue<br>
Go to the main page.<br>
Enter the person's name and priority level.<br>
Click on "Insert" to add the person to the queue.<br>

### Delete Person from Queue
Click on the "Delete" button to remove the person at the front of the queue.<br>

### View Queue
Click on "Display Queue" to view the current queue with priorities.<br>

### Queue Analytics
Click on "Analytics" to view statistics like average waiting time and the total number of persons served.<br>

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
