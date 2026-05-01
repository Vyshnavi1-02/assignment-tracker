from flask import Flask, render_template, request, redirect, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# ------------------------
# DATABASE CONFIG (Render + Local)
# ------------------------
database_url = os.environ.get('DATABASE_URL')

if database_url:
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------------
# MODELS
# ------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), default="Pending")
    priority = db.Column(db.String(20))
    deadline = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ------------------------
# ROUTES
# ------------------------

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    tasks = Task.query.filter_by(user_id=session['user_id']).all()

    total = len(tasks)
    completed = len([t for t in tasks if t.status == "Completed"])
    pending = total - completed

    return render_template('index.html',
                           tasks=tasks,
                           total=total,
                           completed=completed,
                           pending=pending)

# ------------------------
# ADD TASK
# ------------------------

@app.route('/add', methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/login')

    name = request.form.get('task')
    priority = request.form.get('priority')
    deadline = request.form.get('deadline')

    if name:
        new_task = Task(
            name=name,
            priority=priority,
            deadline=deadline,
            user_id=session['user_id']
        )
        db.session.add(new_task)
        db.session.commit()

    return redirect('/')

# ------------------------
# COMPLETE TASK
# ------------------------

@app.route('/complete/<int:id>')
def complete(id):
    task = Task.query.get(id)

    if task:
        task.status = "Completed"
        db.session.commit()

    return redirect('/')

# ------------------------
# DELETE TASK
# ------------------------

@app.route('/delete/<int:id>')
def delete(id):
    task = Task.query.get(id)

    if task:
        db.session.delete(task)
        db.session.commit()

    return redirect('/')

# ------------------------
# EDIT TASK
# ------------------------

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    task = Task.query.get_or_404(id)

    if request.method == 'POST':
        task.name = request.form['task']
        db.session.commit()
        return redirect('/')

    return render_template('edit.html', task=task)

# ------------------------
# REGISTER
# ------------------------

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing = User.query.filter_by(username=username).first()

        if existing:
            return "User already exists"

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# ------------------------
# LOGIN
# ------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session['user_id'] = user.id
            return redirect('/')
        else:
            return "Invalid credentials"

    return render_template('login.html')

# ------------------------
# LOGOUT
# ------------------------

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect('/login')

# ------------------------
# CREATE DATABASE
# ------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)
