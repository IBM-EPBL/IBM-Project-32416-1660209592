from flask import Flask, render_template, request, redirect, url_for, session
import os
import re
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
import ibm_db

app = Flask(__name__)

app.secret_key = 'my secret key'

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=0c77d6f2-5da9-48a9-81f8-86b520b87518.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=31198;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=tzx11389;PWD=soCIdVT7k8obiRke",'','')

picFolder = os.path.join('static','pics')
app.config['UPLOAD_FOLDER'] = picFolder

@app.route("/dashboard")
def dashboard():
	dashboardPic = os.path.join(app.config['UPLOAD_FOLDER'],'dashboard.jpg')
	return render_template('dashboard.html', dashboard=dashboardPic)

@app.route('/')
@app.route('/login', methods =['GET', 'POST'])
def login():
	msg = ' '
	loginPic = os.path.join(app.config['UPLOAD_FOLDER'],'loginImge1.png')
	if request.method == 'POST' and 'usrname' in request.form and 'password' in request.form:
		username = request.form['usrname']
		password = request.form['password']
		sql = "SELECT * FROM account WHERE ID = '"+username+"' AND pass = '"+password+"'"
		stmt = ibm_db.exec_immediate(conn, sql)
		account = ibm_db.fetch_both(stmt)
		if account:
			session['loggedin'] = True
			session['id'] = account[0]
			session['username'] = account[1]
			msg = 'Logged in successfully !'
			return redirect(url_for('dashboard'))
		else:
			msg = 'Incorrect username / password !'
	return render_template('login.html', errorMsg = msg,loginpic = loginPic)

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))

@app.route('/register', methods =['GET', 'POST'])
def register():
	msg = ''
	registerImg = os.path.join(app.config['UPLOAD_FOLDER'],'loginImge1.png')
	if request.method == 'POST' and 'usrname' in request.form and 'password' in request.form and 'email' in request.form :
		username = request.form['usrname']
		password = request.form['password']
		email = request.form['email']
		sql = "SELECT * FROM account WHERE ID = '"+username+"'"
		stmt = ibm_db.exec_immediate(conn, sql)
		account = ibm_db.fetch_both(stmt)

		if account:
			msg = 'Account already exists !'
		elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
			msg = 'Invalid email address !'
		elif not re.match(r'[A-Za-z0-9]+', username):
			msg = 'Username must contain only characters and numbers !'
		elif not username or not password or not email:
			msg = 'Please fill out the form !'
		else:
			ins = "INSERT INTO account VALUES ('"+username+"','"+email+"','"+password+"')"
			prep_stmt = ibm_db.prepare(conn, ins)
			ibm_db.execute(prep_stmt)
			msg = 'You have successfully registered !'
	elif request.method == 'POST':
		msg = 'Please fill out form !'
	return render_template('register.html', errorMsg = msg,registerImg=registerImg)

standard_to = StandardScaler()
# app = Flask(__name__)
@app.route("/predict", methods=['POST'])
def predict():
	dashboardPic = os.path.join(app.config['UPLOAD_FOLDER'],'dashboard.jpg')
	model = pickle.load(open('prediction_model.pkl', 'rb'))
	Fuel_Type_Diesel=0
	if request.method == 'POST':
		Year = int(request.form['Year'])
		Present_Price=float(request.form['Present_Price'])
		Kms_Driven=int(request.form['Kms_Driven'])
		Kms_Driven2=np.log(Kms_Driven)
		Owner=int(request.form['Owner'])
		Fuel_Type_Petrol=request.form['Fuel_Type_Petrol']
		if(Fuel_Type_Petrol=='Petrol'):
			Fuel_Type_Petrol=1
			Fuel_Type_Diesel=0
		else:
			Fuel_Type_Petrol=0
			Fuel_Type_Diesel=1
		Year=2022-Year
		Seller_Type_Individual=request.form['Seller_Type_Individual']
		if(Seller_Type_Individual=='Individual'):
			Seller_Type_Individual=1
		else:
			Seller_Type_Individual=0	
		Transmission_Mannual=request.form['Transmission_Mannual']
		if(Transmission_Mannual=='Manual Car'):
			Transmission_Mannual=1
		else:
			Transmission_Mannual=0
		prediction=model.predict([[Present_Price,Kms_Driven2,Owner,Year,Fuel_Type_Diesel,Fuel_Type_Petrol,Seller_Type_Individual,Transmission_Mannual]])
		output=round(prediction[0],2)
		if output<0:
			return render_template('dashboard.html',prediction_text="Sorry you cannot sell this car",dashboard=dashboardPic)
		else:
			return render_template('dashboard.html',prediction_text="You Can Sell The Car at {}".format(output),dashboard=dashboardPic)
	else:
		return render_template('dashboard.html',dashboard=dashboardPic)


if __name__ == '__main__':
	app.run()