# QueueMaster
QueueMaster is a simple queue management web application built using Flask. It allows users to add, remove, search for persons in the queue, export the queue to a CSV file, and view real-time queue analytics.

## Features

- **Insert**: Add a person to the queue.<br>
- **Delete**: Remove the person at the front of the queue.<br>
- **Search**: Check the position of a person in the queue.<br>
- **Analytics**: View real-time data on the average wait time and the total number of people served.<br>

## Technologies Used
Flask: Python web framework used to create the backend.<br>
HTML/CSS: For the frontend interface.<br>
JavaScript: For interactivity and AJAX requests. <br>
Python: Core programming language used in this project.<br>

## Installation
1)Clone the repository:
```sh
git clone https://github.com/chelaramanipratham/QueueMaster.git
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

6)Open your browser and go to http://127.0.0.1:5000/ to view the application.

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


## Contributing
1)Fork the repository.<br>
2)Create your feature branch (git checkout -b feature/YourFeature).<br>
3)Commit your changes (git commit -m 'Add some feature').<br>
4)Push to the branch (git push origin feature/YourFeature).<br>
5)Open a Pull Request.<br>

Please feel free to contribute in this project!!
