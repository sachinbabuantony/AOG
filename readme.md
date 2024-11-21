AOG Check Application:
This is a Flask-based web application designed to calculate and display Aircraft on Ground (AOG) status for specific aircraft based on their serial numbers. It integrates with the RadarBox API to fetch flight data and provides a user-friendly interface for viewing results.

How to use:
1. Open the app 
2. Put a Serial No. eg: 5507
3. click calculate AOG

Features:
Input aircraft serial numbers to calculate AOG.
Displays flight details such as:
Aircraft Registration
Airline Name
Status (IN_FLIGHT, LANDED, etc.)
Recent Location
AOG in days (toggle between hours and days).
Fetches real-time data from the RadarBox API.
Interactive and responsive design with user-friendly error handling.


Project Structure:
plaintext
Copy code
AOG/
├── app.py              # Main Flask application
├── Procfile            # Deployment configuration for platforms like Heroku
├── requirements.txt    # Python dependencies
├── static/             # Static assets like images and CSS
│   ├── airline_economics_logo.jpg
│   ├── RAMP.jpg
├── templates/          # HTML templates for the application
│   ├── index.html      # Input form page
│   ├── results.html    # Results display page


Step 1: Clone the Repository or Extract Files
Download and extract the provided zip file or clone the GitHub repository if applicable.

Step 2: Install Dependencies
Ensure you have Python 3.8+ installed on your system. Install the required Python packages using pip:

bash
Copy code
pip install -r requirements.txt
Step 3: Set the API Token
Replace the API_TOKEN value in app.py with a secure API token from RadarBox. Alternatively, configure this in an environment variable or secret vault for better security.

Step 4: Run the Application
Run the Flask application locally:
