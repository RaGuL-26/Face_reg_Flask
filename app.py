
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import cv2
import face_recognition
import json

app = Flask(__name__)
app.secret_key = 'abcdefghij123456'

login_manager = LoginManager(app)

USERS_FILE = 'users.json'

# Load initial users data from users.json
try:
    with open(USERS_FILE, 'r') as f:
        users = json.load(f)
except FileNotFoundError:
    # If the file doesn't exist, initialize an empty dictionary
    users = {}

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    user = User()
    user.id = user_id
    return user

class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Register')

@app.route('/')
def index():
    return render_template('index.html')
# ... (previous code)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')

        # Check if the username exists in the users dictionary loaded from users.json
        if username in users:
            known_encoding = users[username]['face_encoding']

            video_capture = cv2.VideoCapture(0)
            _, frame = video_capture.read()

            unknown_encoding = face_recognition.face_encodings(frame)

            # Check if any faces are found before trying to compare encodings
            if not unknown_encoding:
                flash('No face found in the Camera. Please try again.', 'danger')
                video_capture.release()
                return redirect(url_for('login'))

            result = face_recognition.compare_faces([known_encoding], unknown_encoding[0])

            if result and result[0]:
                user = User()
                user.id = username
                login_user(user)
                flash('Login successful!', 'success')
                video_capture.release()
                return redirect(url_for('dashboard'))
            else:
                flash('Face authentication failed. Please try again.', 'danger')

            video_capture.release()
        else:
            flash('User not found. Please register first.', 'danger')
            return redirect(url_for('register'))

    return render_template('login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.name.data

        # Check if the username already exists
        if username in users:
            flash('User already registered. Please log in.', 'danger')
            return redirect(url_for('login'))

        return redirect(url_for('capture_picture', username=username))

    return render_template('register.html', form=form)



@app.route('/capture_picture/<username>')
def capture_picture(username):
    video_capture = cv2.VideoCapture(0)
    _, frame = video_capture.read()
    picture_path = f'static/pictures/{username}.jpg'

    # Save the picture in the specified folder
    cv2.imwrite(picture_path, frame)

    # Update the user's face_encoding in the users dictionary
    known_image = face_recognition.load_image_file(picture_path)
    
    # Get face encodings
    face_encodings = face_recognition.face_encodings(known_image)

    # Check if any faces are found before trying to access the encoding
    if face_encodings:
        users[username] = {'name': username, 'password': '', 'face_encoding': face_encodings[0].tolist()}
    else:
        flash('No face found in the captured picture. Please try again.', 'danger')
        return redirect(url_for('register'))

    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

    video_capture.release()
    flash('Picture captured successfully! You can now log in.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', name=current_user.id)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
