from flask import Flask, render_template, request, redirect, session, url_for
from datetime import datetime, timedelta
from functools import wraps
import subprocess
import os
import getpass

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__, template_folder=os.path.abspath("templates"))
app.secret_key = 'Ir0nH0rse5'
# Set session timeout to 30 minutes
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

# Shared password for all users
shared_password = "1542653"

# Function to check if the user is logged in
def is_logged_in():
    return 'username' in session
    
# Function to check if the session is expired
def is_session_expired():
    if 'last_activity' in session:
        last_activity = session['last_activity']
        session_timeout = app.config['PERMANENT_SESSION_LIFETIME']
        if datetime.now() - last_activity > session_timeout:
            return True
    return False   

def save_user_ip_to_file(username,ip_address,prompt):
    try:
        with open('user_ips.txt', 'a') as file:
            file.write(f"Username: {username}|{ip_address}|{prompt}\n")
        print("User IP address saved to 'user_ips.txt' successfully.")
    except Exception as e:
        print(f"Error saving user IP address: {str(e)}")
        
@app.route('/')
def index():
    if 'username' in session:
        return render_template('index.html', username=session['username'])
    return redirect(url_for('login'))
    
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if password == shared_password:
            session['username'] = username
            session['last_activity'] = datetime.now()
            return redirect(url_for('index'))
        else:
            error='Invalid username or password'
    return render_template('login.html',error=error)
 

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))  

# Home route
@app.route('/')
def home():
    if not is_logged_in():
        return redirect(url_for('login'))
    if is_session_expired():
        return redirect(url_for('logout'))
    session['last_activity'] = datetime.now()
    return render_template('index.html', username=session['username'])    

@app.route('/Generate_Requirements')
@login_required
def Generate_Requirements():
    return render_template('Generate_Requirements.html')
    
@app.route('/Generate_TestCases')
@login_required
def Generate_TestCases():
    return render_template('Generate_TestCases.html')
    
@app.route('/Generate_APITestCases')
@login_required
def Generate_APITestCases():
    return render_template('Generate_APITestCases.html')   

@app.route('/Code_Documentation')
@login_required
def Code_Documentation():
    return render_template('Code_Documentation.html')   

@app.route('/Generate_TestCasesMetlifePOC')
@login_required
def Generate_TestCasesMetlifePOC():
    return render_template('Generate_TestCasesMetlifePOC.html')  
    
@app.route('/Code_migration')
@login_required
def Code_migration():
    return render_template('Code_migration.html')  
  
@app.route('/Convert_Requirements_BDD')
@login_required
def Convert_Requirements_BDD():
    return render_template('Convert_Requirements_BDD.html')     

@app.route('/Generate_UnitTestCases')
@login_required
def Generate_UnitTestCases():
    return render_template('Generate_UnitTestCases.html') 
    
@app.route('/Generate_performanceTestCases')
@login_required
def Generate_performanceTestCases():
    return render_template('Generate_performanceTestCases.html') 

@app.route('/Generate_code_optimization')
@login_required
def Generate_code_optimization():
    return render_template('Generate_code_optimization.html') 
 
@app.route('/Generate_TestScenarios')
@login_required
def Generate_TestScenarios():
    return render_template('Generate_TestScenarios.html')  
    
@app.route('/Code_To_Flowchart')
@login_required
def Code_To_Flowchart():
    return render_template('Code_To_Flowchart.html')    



@app.route('/run_script', methods=['POST'])
def run_script():
    try:

        data = request.get_json()
        script_path = os.path.join('scripts', data['scriptPath'])  # Adjust the path
        input_text = data['inputText']
        user_ip = request.remote_addr
        windows_username = getpass.getuser()
        # Save the user's IP address to a file
        save_user_ip_to_file(windows_username,user_ip,input_text)
        # Run the Python script using subprocess
        result = subprocess.check_output(['python', script_path, input_text], text=True)

        return jsonify(success=True, output=result)
    except subprocess.CalledProcessError as e:
        print(f"CalledProcessError: {e}")
        print(f"Output: {e.output}")
        return jsonify(success=False, error=e.output)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify(success=False, error=str(e))
        
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000,debug=True)
