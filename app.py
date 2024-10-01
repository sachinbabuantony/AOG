from flask import Flask, request, url_for
from datetime import datetime, timedelta
import requests
import pandas as pd
import pytz

app = Flask(__name__)

API_TOKEN = 'ac65d28b7da079d096d137bea0de8b0b306c19d5'  # Replace with your actual API token

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        registrations_input = request.form.get('registrations', '')
        registrations = [reg.strip() for reg in registrations_input.split(',') if reg.strip()]
        
        if not registrations:
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
                    <h1>Please enter at least one aircraft registration.</h1>
                    <a href="/">Back to Input Form</a>
                </body>
                </html>
            '''
        
        # Get the current UTC time
        current_time = datetime.utcnow()

        # Get the time 7 days ago from now
        seven_days_ago = current_time - timedelta(days=7)

        # Convert to ISO 8601 format (used in APIs)
        to_date = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        from_date = seven_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ")

        # Adjusted payload with dynamic dates
        payload = {
            "pageSize": 10,
            "page": 1,
            "fromDate": from_date,
            "toDate": to_date,
            "registrations": registrations
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
                selected_columns = ['aircraftRegistration', 'actualTakeoff', 'actualLanding']
                selected_df = df[selected_columns]

                # Group by aircraftRegistration and get the latest actualTakeoff
                latest_takeoff_df = selected_df.loc[selected_df.groupby('aircraftRegistration')['actualTakeoff'].idxmax()]

                # Convert to datetime
                latest_takeoff_df['actualTakeoff'] = pd.to_datetime(latest_takeoff_df['actualTakeoff'], errors='coerce')
                latest_takeoff_df['actualLanding'] = pd.to_datetime(latest_takeoff_df['actualLanding'], errors='coerce')

                # Calculate AOG_Till_Date_Hours
                latest_takeoff_df['AOG_Till_Date_Hours'] = None

                uk_tz = pytz.timezone('Europe/London')
                current_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
                current_time_uk = current_time_utc.astimezone(uk_tz)

                for idx, row in latest_takeoff_df.iterrows():
                    takeoff = row['actualTakeoff']
                    landing = row['actualLanding']

                    if pd.notnull(takeoff) and pd.isnull(landing):
                        latest_takeoff_df.at[idx, 'AOG_Till_Date_Hours'] = 0
                    elif pd.notnull(takeoff) and pd.notnull(landing):
                        latest_takeoff_df.at[idx, 'AOG_Till_Date_Hours'] = (current_time_uk - landing).total_seconds() / 3600

                # Round the AOG_Till_Date_Hours to 2 decimal places
                latest_takeoff_df['AOG_Till_Date_Hours'] = latest_takeoff_df['AOG_Till_Date_Hours'].round(2)

                # Convert DataFrame to HTML with better styling
                html_table = latest_takeoff_df.to_html(index=False, classes='dataframe', border=0, justify='center')

                # HTML page with styling
                return f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>AOG Results</title>
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
                        a.button {{
                            display: inline-block;
                            margin-top: 30px;
                            padding: 10px 20px;
                            background-color: #3498db;
                            color: white;
                            text-decoration: none;
                            font-weight: bold;
                            border-radius: 5px;
                            transition: background-color 0.3s ease;
                        }}
                        a.button:hover {{
                            background-color: #2980b9;
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
                        <h1>AOG Results</h1>
                        {html_table}
                        <a href="/" class="button">Back to Input Form</a>
                    </div>
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
                        <h1>No flight data found for the provided registrations.</h1>
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
            <title>AOG Calculator</title>
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
                label {
                    font-size: 1.2rem;
                    margin-bottom: 10px;
                    width: 100%;
                    text-align: left;
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
                <h1>AOG Calculator</h1>
                <form method="post">
                    <input type="text" id="registrations" name="registrations" placeholder="Enter Aircraft Registrations (separated by commas)">
                    <input type="submit" value="Calculate AOG">
                </form>
            </div>
        </body>
        </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)