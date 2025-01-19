from flask import Flask, render_template, request, jsonify
import base64
import io
from well_analysis import load_data, calculate_daily_on_durations, plot_daily_on_durations
import matplotlib.pyplot as plt

app = Flask(__name__)

# Route for home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for well analysis API
@app.route('/api/well-analysis', methods=['POST'])
def analyze_well():
    try:
        # Get dates from request
        data = request.json
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        # Load and analyze data
        csv_data = load_data('NGM156.csv')  # Make sure your CSV file is in the right location
        if csv_data is None:
            return jsonify({'success': False, 'error': 'Failed to load data'})
            
        daily_durations = calculate_daily_on_durations(csv_data, start_date, end_date)
        
        # Create and save plot
        plt.figure(figsize=(12, 6))
        plot_daily_on_durations(daily_durations)
        
        # Convert plot to base64 string
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png')
        img_buf.seek(0)
        img_base64 = base64.b64encode(img_buf.read()).decode('utf-8')
        plt.close()
        
        return jsonify({'success': True, 'image': img_base64})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)