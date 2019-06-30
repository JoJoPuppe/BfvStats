from flask import Flask
from flask_sqlalchemy import SQLAlchemy


#app = Flask(__name__)
#app = Flask(__name__.split('.')[0])
app = Flask('app')

app.config.from_pyfile('config.py')

db = SQLAlchemy(app)

from app import views
