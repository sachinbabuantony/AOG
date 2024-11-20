from flask import Flask, request, url_for
from datetime import datetime, timedelta
import requests
import pandas as pd
import pytz

app = Flask(__name__)

API_TOKEN = 'e40e9d79b155af6f3fc39ad327b6dfad6f9ecd85'  # need to remove from source code to secret vault

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
        
        # Get the current UTC time
        current_time = datetime.utcnow()
    
        # Get the time 4 days ago from now
        seven_days_ago = current_time - timedelta(days=4)
    
        # Convert to ISO 8601 format (used in APIs)
        to_date = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        from_date = seven_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")
    
        # Adjusted payload with dynamic dates and pageSize
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

                # Get all rows where 'status' is 'IN_FLIGHT'
                inflight_df = selected_df[selected_df['status'] == 'IN_FLIGHT']

                # Get aircraftSerialNumbers that are 'IN_FLIGHT'
                inflight_serials = inflight_df['aircraftSerialNumber'].unique()

                # For aircraft not in 'IN_FLIGHT', get the latest 'actualTakeoff' per 'aircraftSerialNumber'
                not_inflight_df = selected_df[~selected_df['aircraftSerialNumber'].isin(inflight_serials)]
                if not not_inflight_df.empty:
                    # Drop rows with NaN values in 'actualTakeoff' before grouping
                    not_inflight_df = not_inflight_df.dropna(subset=['actualTakeoff']) 
                    latest_not_inflight_df = not_inflight_df.loc[
                        not_inflight_df.groupby('aircraftSerialNumber')['actualTakeoff'].idxmax()
                    ]
                    # Combine inflight_df and latest_not_inflight_df
                    latest_takeoff_df = pd.concat([inflight_df, latest_not_inflight_df])
                else:
                    latest_takeoff_df = inflight_df
    
                # Group by aircraftSerialNumber and get the latest actualTakeoff
                if (selected_df['status'] == 'IN_FLIGHT').any():
                    # Get all rows where 'status' is 'IN_FLIGHT'
                    latest_takeoff_df = selected_df[selected_df['status'] == 'IN_FLIGHT']
                else:
                    # Group by 'aircraftSerialNumber' and get the row with the latest 'actualTakeoff' time
                    latest_takeoff_df = selected_df.loc[
                        selected_df.groupby('aircraftSerialNumber')['actualTakeoff'].idxmax()
                    ]
    
                latest_takeoff_df = latest_takeoff_df.copy()

                # Convert actualTakeoff and actualLanding to datetime format (if not already done)
                latest_takeoff_df['actualTakeoff'] = pd.to_datetime(latest_takeoff_df['actualTakeoff'], errors='coerce')
                latest_takeoff_df['actualLanding'] = pd.to_datetime(latest_takeoff_df['actualLanding'], errors='coerce')

                # Create a new column to store AOG time in days
                latest_takeoff_df['AOG_Till_Date_Days'] = None
    
                current_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    
                # Apply logic to determine Recent Location based on status
                for idx, row in latest_takeoff_df.iterrows():
                    takeoff = row['actualTakeoff']
                    landing = row['actualLanding']
                    status = row['status']
    
                    # Determine Recent Location
                    if status == 'LANDED':
                        latest_takeoff_df.at[idx, 'Recent Location'] = row['arrAirportCity']
                    elif status == 'IN_FLIGHT':
                        latest_takeoff_df.at[idx, 'Recent Location'] = row['depAirportName']
                    else:
                        latest_takeoff_df.at[idx, 'Recent Location'] = 'Unknown'
    
                    # New Logic: If the status is 'IN_FLIGHT', AOG_Till_Date_Days is zero
                    if status == 'IN_FLIGHT':
                        latest_takeoff_df.at[idx, 'AOG_Till_Date_Days'] = 0

                    # Existing logic
                    # Case 1: If the flight has taken off but hasn't landed, AOG is 0
                    elif pd.notnull(takeoff) and pd.isnull(landing):
                        latest_takeoff_df.at[idx, 'AOG_Till_Date_Days'] = 0

                    # Case 1: If the flight has taken off but hasn't landed, AOG is 0
                    elif pd.isnull(takeoff) and pd.isnull(landing):
                        latest_takeoff_df.at[idx, 'AOG_Till_Date_Days'] = 'No Take-off Times Received'

                    # Case 2: If the flight has both taken off and landed, calculate AOG from last landing to current time in days
                    elif pd.notnull(takeoff) and pd.notnull(landing):
                        latest_takeoff_df.at[idx, 'AOG_Till_Date_Days'] = (current_time_utc - landing).total_seconds() / (3600 * 24)
    
                # Round the AOG_Till_Date_Days to 2 decimal places if it's numeric
                latest_takeoff_df['AOG_Till_Date_Days'] = latest_takeoff_df['AOG_Till_Date_Days'].astype(float).round(2)
    
                # Rename the column for generality
                latest_takeoff_df.rename(columns={'AOG_Till_Date_Days': 'AOG_Till_Date'}, inplace=True)
    
                # Convert DataFrame to HTML with better styling and add data-day attribute for conversion
                html_table = '''
                <table id="aogTable" class="dataframe">
                    <thead>
                        <tr>
                            <th>Aircraft Serial Number</th>
                            <th>Aircraft Registration</th>
                            <th>Airline Name</th>
                            <th>Aircraft Type</th>
                            <th>Status</th>
                            <th>Recent Location</th>
                            <th>AOG (No. of Days)</th>
                        </tr>
                    </thead>
                    <tbody>
                '''
                for _, row in latest_takeoff_df.iterrows():
                    html_table += '<tr>'
                    html_table += f'<td>{row["aircraftSerialNumber"]}</td>'
                    html_table += f'<td>{row["aircraftRegistration"]}</td>'
                    html_table += f'<td>{row["airlineName"]}</td>'
                    html_table += f'<td>{row["aircraftTypeDescription"]}</td>'
                    html_table += f'<td>{row["status"]}</td>'
                    html_table += f'<td>{row["Recent Location"]}</td>'
                    # Add data-day attribute for AOG_Till_Date
                    aog_value = row["AOG_Till_Date"]
                    html_table += f'<td data-day="{aog_value}">{aog_value}</td>'
                    html_table += '</tr>'
                html_table += '''
                    </tbody>
                </table>
                '''
    
                # HTML page with styling and toggle button
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
                            max-width: 1200px;
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
                        table.dataframe {{
                            margin-left: auto;
                            margin-right: auto;
                            border-collapse: collapse;
                            width: 90%;
                            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
                            background-color: #fff;
                        }}
                        table.dataframe th, table.dataframe td {{
                            border: 1px solid #dddddd;
                            padding: 12px 15px;
                            text-align: center;
                            font-size: 1rem;
                        }}
                        table.dataframe th {{
                            background-color: #3498db;
                            color: white;
                            position: sticky;
                            top: 0;
                        }}
                        table.dataframe tr:nth-child(even) {{
                            background-color: #f9f9f9;
                        }}
                        a.button, button.toggle-button {{
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
                        a.button:hover, button.toggle-button:hover {{
                            background-color: #2980b9;
                        }}
                        .button-container {{
                            margin-top: 20px;
                        }}
                        @media (max-width: 768px) {{
                            table.dataframe {{
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
                        <h1>AOG Check</h1>
                        {html_table}
                        <div class="button-container">
                            <button class="toggle-button" id="toggleButton">Show in Hours</button>
                        </div>
                        <a href="/" class="button">Back to Input Form</a>
                    </div>
                    <script>
                        const toggleButton = document.getElementById('toggleButton');
                        let showingDays = true;
    
                        toggleButton.addEventListener('click', function() {{
                            const table = document.getElementById('aogTable');
                            const headers = table.querySelectorAll('th');
                            const aogHeader = headers[6];  // Adjusted index due to new columns
                            const cells = table.querySelectorAll('td[data-day]');
    
                            if (showingDays) {{
                                // Switch to Hours
                                aogHeader.textContent = 'AOG Till Date (Hours)';
                                cells.forEach(cell => {{
                                    const days = parseFloat(cell.getAttribute('data-day'));
                                    const hours = (days * 24).toFixed(2);
                                    cell.textContent = hours;
                                }});
                                toggleButton.textContent = 'Show in Days';
                                showingDays = false;
                            }} else {{
                                // Switch to Days
                                aogHeader.textContent = 'AOG (No. of Days)';
                                cells.forEach(cell => {{
                                    const days = parseFloat(cell.getAttribute('data-day'));
                                    cell.textContent = days;
                                }});
                                toggleButton.textContent = 'Show in Hours';
                                showingDays = true;
                            }}
                        }});
                    </script>
                </body>
                </html>
                '''
            else:
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
    
    # HTML form with improved styling and logo
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
