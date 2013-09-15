from app import app
from flask import render_template

@app.route('/')
def index():
	return render_template('index.html', active="home")

@app.route('/example/')
def example():
	return render_template('example.html', active="example")

@app.route('/facebook/')
def facebook():
	return render_template('facebook.html', active="facebook")