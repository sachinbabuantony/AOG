from flask import Flask, request
from datetime import datetime, timedelta
import requests
import pandas as pd
import pytz

app = Flask(__name__)

API_TOKEN = 'f817516b1241f95db82006cd603ee62dd50732b1'  # Replace with your actual API token

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        serial_number = request.form.get('serialNumber', '').strip()

        if not serial_number:
            return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            background-color: #f8d7da;
                            color: #721c24;
                            margin: 0;
                            padding: 20px;
                        }
                        h1 {
                            color: #721c24;
                            font-size: 2rem;
                        }
                        a {
                            display: inline-block;
                            margin-top: 20px;
                            text-decoration: none;
                            color: #721c24;
                            font-weight: bold;
                            font-size: 1.1rem;
                        }
                        img {
                            width: 150px;
                            margin-bottom: 20px;
                        }
                    </style>
                </head>
                <body>
                    <img src="/static/airline_economics_logo.jpg" alt="Logo">
                    <h1>Please enter an aircraft serial number.</h1>
                    <a href="/">Back to Input Form</a>
                </body>
                </html>
            '''
        
        # Check if the input contains a comma, indicating multiple serial numbers
        if ',' in serial_number:
            return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Multiple Serial Numbers Detected</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            background-color: #f8d7da;
                            color: #721c24;
                            margin: 0;
                            padding: 20px;
                        }
                        h1 {
                            color: #721c24;
                            font-size: 2rem;
                        }
                        p {
                            font-size: 1.1rem;
                        }
                        a {
                            display: inline-block;
                            margin-top: 20px;
                            text-decoration: none;
                            color: #721c24;
                            font-weight: bold;
                            font-size: 1.1rem;
                        }
                        img {
                            width: 150px;
                            margin-bottom: 20px;
                        }
                    </style>
                </head>
                <body>
                    <img src="/static/airline_economics_logo.jpg" alt="Logo">
                    <h1>Please enter only one aircraft serial number.</h1>
                    <p>Multiple serial numbers detected. Please input a single serial number without commas.</p>
                    <a href="/">Back to Input Form</a>
                </body>
                </html>
            '''
        
        # Proceed with the rest of your code
        # Get the current UTC time
        current_time = datetime.utcnow()
        
        # Get the time 4 days ago from now
        four_days_ago = current_time - timedelta(days=4)
        
        # Convert to ISO 8601 format (used in APIs)
        to_date = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        from_date = four_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Adjusted payload with dynamic dates
        payload = {
            "pageSize": 1,
            "page": 1,
            "fromDate": from_date,
            "toDate": to_date,
            "serialNumbers": [serial_number],
            "aircraftClasses": ["AIRLINER"]
        }
        
        # Headers
        headers = {
            'Authorization': f'Bearer {API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # API URL
        url = 'https://api.radarbox.com/v2/flights/search'
        
        # Fetch data
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            flight_data = response.json()
            if 'flights' in flight_data and flight_data['flights']:
                df = pd.json_normalize(flight_data['flights'])
        
                # Select columns
                selected_columns = ['aircraftSerialNumber', 'aircraftRegistration', 'airlineName', 'actualTakeoff', 'actualLanding', 'aircraftTypeDescription', 'status', 'arrAirportCity', 'depAirportName']
                selected_df = df.reindex(columns=selected_columns)
        
                # Proceed with data processing
                # Get the latest flight based on 'actualTakeoff'
                latest_flight = selected_df.loc[selected_df['actualTakeoff'].idxmax()]
        
                # Convert actualTakeoff and actualLanding to datetime
                latest_flight['actualTakeoff'] = pd.to_datetime(latest_flight['actualTakeoff'], errors='coerce')
                latest_flight['actualLanding'] = pd.to_datetime(latest_flight['actualLanding'], errors='coerce')
        
                # Calculate AOG Time
                current_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                takeoff = latest_flight['actualTakeoff']
                landing = latest_flight['actualLanding']
                status = latest_flight['status']
        
                if status == 'IN_FLIGHT':
                    aog_till_date = 0
                    recent_location = latest_flight['depAirportName']
                elif status == 'LANDED':
                    aog_till_date = (current_time_utc - landing).total_seconds() / (3600 * 24)
                    recent_location = latest_flight['arrAirportCity']
                else:
                    aog_till_date = 'No Take-off Times Received'
                    recent_location = 'Unknown'
        
                # Round AOG time if numeric
                if isinstance(aog_till_date, float):
                    aog_till_date = round(aog_till_date, 2)
        
                # HTML page with results
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>AOG Check</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            text-align: center;
                            background-color: #f0f4f8;
                            color: #333;
                            margin: 0;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                        }}
                        img {{
                            width: 200px;
                            margin-bottom: 20px;
                        }}
                        h1 {{
                            color: #2c3e50;
                            font-size: 2.5rem;
                            margin-bottom: 30px;
                        }}
                        table {{
                            margin-left: auto;
                            margin-right: auto;
                            border-collapse: collapse;
                            width: 90%;
                            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                            background-color: #fff;
                        }}
                        table th, table td {{
                            border: 1px solid #dddddd;
                            padding: 12px 15px;
                            text-align: center;
                            font-size: 1rem;
                        }}
                        table th {{
                            background-color: #3498db;
                            color: white;
                            position: sticky;
                            top: 0;
                        }}
                        table tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        a.button {{
                            display: inline-block;
                            margin-top: 30px;
                            padding: 10px 20px;
                            background-color: #3498db;
                            color: white;
                            text-decoration: none;
                            font-weight: bold;
                            border: none;
                            border-radius: 5px;
                            transition: background-color 0.3s ease;
                            cursor: pointer;
                            font-size: 1rem;
                        }}
                        a.button:hover {{
                            background-color: #2980b9;
                        }}
                        .button-container {{
                            margin-top: 20px;
                        }}
                        @media (max-width: 768px) {{
                            table {{
                                width: 100%;
                            }}
                            img {{
                                width: 150px;
                            }}
                            h1 {{
                                font-size: 2rem;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <img src="/static/airline_economics_logo.jpg" alt="Logo">
                        <h1>AOG Check Result</h1>
                        <table>
                            <tr>
                                <th>Aircraft Serial Number</th>
                                <td>{latest_flight["aircraftSerialNumber"]}</td>
                            </tr>
                            <tr>
                                <th>Aircraft Registration</th>
                                <td>{latest_flight["aircraftRegistration"]}</td>
                            </tr>
                            <tr>
                                <th>Airline Name</th>
                                <td>{latest_flight["airlineName"]}</td>
                            </tr>
                            <tr>
                                <th>Aircraft Type</th>
                                <td>{latest_flight["aircraftTypeDescription"]}</td>
                            </tr>
                            <tr>
                                <th>Status</th>
                                <td>{latest_flight["status"]}</td>
                            </tr>
                            <tr>
                                <th>Recent Location</th>
                                <td>{recent_location}</td>
                            </tr>
                            <tr>
                                <th>AOG Till Date (Days)</th>
                                <td>{aog_till_date}</td>
                            </tr>
                        </table>
                        <div class="button-container">
                            <a href="/" class="button">Back to Input Form</a>
                        </div>
                    </div>
                </body>
                </html>
                '''
            else:
                # No flight data found
                return '''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>No Data Found</title>
                    <style>
                        body {
                            font-family: Arial, sans-serif;
                            text-align: center;
                            background-color: #f0f4f8;
                            color: #333;
                            margin: 0;
                            padding: 20px;
                        }
                        .container {
                            max-width: 600px;
                            margin: 0 auto;
                        }
                        img {
                            width: 200px;
                            margin-bottom: 20px;
                        }
                        h1 {
                            color: #2c3e50;
                            font-size: 2.5rem;
                            margin-bottom: 30px;
                        }
                        a.button {
                            display: inline-block;
                            margin-top: 20px;
                            padding: 10px 20px;
                            background-color: #3498db;
                            color: white;
                            text-decoration: none;
                            font-weight: bold;
                            border-radius: 5px;
                            transition: background-color 0.3s ease;
                        }
                        a.button:hover {
                            background-color: #2980b9;
                        }
                        @media (max-width: 768px) {
                            img {
                                width: 150px;
                            }
                            h1 {
                                font-size: 2rem;
                            }
                        }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <img src="/static/airline_economics_logo.jpg" alt="Logo">
                        <h1>No flight data found for the provided serial number.</h1>
                        <a href="/" class="button">Back to Input Form</a>
                    </div>
                </body>
                </html>
                '''
        else:
            # Error fetching data from API
            return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Error</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            text-align: center;
                            background-color: #f8d7da;
                            color: #721c24;
                            margin: 0;
                            padding: 20px;
                        }}
                        .container {{
                            max-width: 600px;
                            margin: 0 auto;
                        }}
                        img {{
                            width: 200px;
                            margin-bottom: 20px;
                        }}
                        h1 {{
                            color: #721c24;
                            font-size: 2rem;
                            margin-bottom: 30px;
                        }}
                        p {{
                            font-size: 1.1rem;
                            margin-bottom: 20px;
                        }}
                        a.button {{
                            display: inline-block;
                            padding: 10px 20px;
                            background-color: #721c24;
                            color: white;
                            text-decoration: none;
                            font-weight: bold;
                            border-radius: 5px;
                            transition: background-color 0.3s ease;
                        }}
                        a.button:hover {{
                            background-color: #501217;
                        }}
                        @media (max-width: 768px) {{
                            img {{
                                width: 150px;
                            }}
                            h1 {{
                                font-size: 2rem;
                            }}
                        }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <img src="/static/airline_economics_logo.jpg" alt="Logo">
                        <h1>Error Fetching Data</h1>
                        <p>Status Code: {response.status_code}</p>
                        <p>Message: {response.text}</p>
                        <a href="/" class="button">Back to Input Form</a>
                    </div>
                </body>
                </html>
            '''
        
    # HTML form adjusted to accept only one serial number
    return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>AOG Check</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f0f4f8;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                }
                .container {
                    background-color: #ffffff;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                    width: 90%;
                    text-align: center;
                }
                img {
                    width: 200px;
                    margin-bottom: 20px;
                }
                h1 {
                    color: #2c3e50;
                    margin-bottom: 30px;
                    font-size: 2.5rem;
                }
                form {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                }
                input[type="text"] {
                    padding: 12px;
                    width: 100%;
                    font-size: 1rem;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    box-sizing: border-box;
                }
                input[type="submit"] {
                    background-color: #3498db;
                    color: white;
                    padding: 12px 20px;
                    border: none;
                    cursor: pointer;
                    font-size: 1.1rem;
                    border-radius: 5px;
                    width: 100%;
                    transition: background-color 0.3s ease;
                }
                input[type="submit"]:hover {
                    background-color: #2980b9;
                }
                @media (max-width: 768px) {
                    img {
                        width: 150px;
                    }
                    h1 {
                        font-size: 2rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <img src="/static/airline_economics_logo.jpg" alt="Logo">
                <h1>AOG Check</h1>
                <form method="post">
                    <input type="text" id="serialNumber" name="serialNumber" placeholder="Enter Aircraft Serial Number">
                    <input type="submit" value="Calculate AOG">
                </form>
            </div>
        </body>
        </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)
