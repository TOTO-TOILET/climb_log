from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, Boolean, Float, Table, Column, ForeignKey
from datetime import datetime, timedelta
from forms import LogForm, AddClimb, LoginForm, RegisterForm
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from analysis import ClimbingAnalyzer, DataFrame
import requests

# from flask_ckeditor import CKEditor, CKEditorField


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap5(app)


# initiate the analysis feauture created in a separate file analysis.py
db_path = "/Users/yuta/Desktop/climb_proj/instance/climbs.db"
df = DataFrame(db_path)
analyzer = ClimbingAnalyzer(df)
# print(analyzer.grade_attempted(3)) example use!


if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
# bcrypt = Bcrypt(app) pw_hash = bcrypt.generate_password_hash('hunter2')..bcrypt.check_password_hash(pw_hash, 'hunter2') # returns True

login_manager = LoginManager()
login_manager.init_app(app)

#call back for login function
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)

# Create the database
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///climbs.db'
db = SQLAlchemy(model_class=Base, session_options={"expire_on_commit": True})
db.init_app(app)

# Config Table for users 
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    user_icon: Mapped[str] = mapped_column(String(250), nullable=True) # User stores picture for their profile 
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    current_grade: Mapped[str] = mapped_column(String(10), nullable=True)
    home_gym: Mapped[str] = mapped_column(String(100), nullable=True)

    climbs = relationship('Climb', back_populates='uploaded_by')
    comments = relationship('Comment', back_populates='comment_author')
    scores = relationship('Score', back_populates='score_owner')


# Config Table for climbs
class Climb(db.Model):
    __tablename__ = 'climbs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    photo: Mapped[str] = mapped_column(String(255), nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False) # at the tim when the climb is uploaded the default of this attribute is False
    date_completed: Mapped[str] = mapped_column(String(100), nullable=True)
    grade: Mapped[int] = mapped_column(Integer, nullable=False, default=None) # when the grade is 100 that means the climb is not graded thus unkown
    style: Mapped[str] = mapped_column(String(100), nullable=False) 
    evaluation: Mapped[int] = mapped_column(Integer, nullable=True)
    when_stripped: Mapped[str] = mapped_column(String(50), nullable=True) 
    is_stripped: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    date_logged: Mapped[str] = mapped_column(String(100), nullable= True)
    attempt: Mapped[int] = mapped_column(Integer, nullable=False, default = 0)
    total_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    upload_author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    feel_strong: Mapped[bool] = mapped_column(Boolean, nullable=True)

    comments = relationship('Comment', back_populates='parent_climb')
    uploaded_by = relationship('User', back_populates='climbs')


# Config Table for comments
class Comment(db.Model):
    __tablename__ = 'comments'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    date_commented: Mapped[str] = mapped_column(String(100), nullable=False)  
    author_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    climb_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('climbs.id'))

    comment_author = relationship('User', back_populates='comments')
    parent_climb = relationship('Climb', back_populates='comments')


# keep track of user's scores and grade over time
class Score(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    performance_score: Mapped[int] = mapped_column(Integer, nullable=True)
    activity_score: Mapped[int] = mapped_column(Integer, nullable=True) # this stores number of calory burned 
    grade: Mapped[int] = mapped_column(Integer, nullable=True)
    score_owner_id: Mapped[int] = mapped_column(Integer, db.ForeignKey('users.id'))
    recorded_at: Mapped[str] = mapped_column(String, nullable=True)

    score_owner = relationship('User', back_populates='scores')


with app.app_context():
    db.create_all()

def get_carolies_burned():
    today = datetime.today().date()

# Query the database for climbs logged by the current user today
    daily_climbs = db.session.execute(
        db.select(Climb).where(
            Climb.upload_author_id == current_user.id,
            Climb.date_logged != None,  # Ensure date_logged is not None
            Climb.date_logged.startswith(today.strftime('%Y-%m-%d'))  # Check if date_logged starts with today's date
        )
    ).scalars().all()

    carolies_buned = 0

    carolies_hard = 50
    carolies_moderate = 30
    carolies_easy = 10
    # print(daily_climbs)
    for i in daily_climbs:
        if i.grade >= int(current_user.current_grade) -1:
            carolies_buned += i.attempt * carolies_hard
        elif i.grade > int(current_user.current_grade) -3:
            carolies_buned += i.attempt * carolies_moderate
        else:
            carolies_buned += i.attempt * carolies_easy

    print(f'{carolies_buned} caloroes burned')
    return carolies_buned


@app.route('/')
def home():
    if current_user.is_authenticated:
        all_climbs = db.session.execute(db.select(Climb).where(Climb.upload_author_id == current_user.id)).scalars().all()
        for i in all_climbs:
            if i.date_logged:
                date = datetime.strptime(i.date_logged.split(' ')[0], '%Y-%m-%d').date()
                if date != datetime.today().date():
                    # if the last logged date is not today reset the attmept numnber to keep track of daily attempt num
                    i.attempt = 0
            else:
                i.date_logged = 0
                i.date_logged = datetime.today().strftime('%Y-%m-%d')
        db.session.commit()
    # score_demo()
    # demo_data()
    # demo()
    # climbs = db.session.execute(db.select(Climb)).scalars().all()
    # for climb in climbs:
    #     climb.date_logged = datetime.now().date()
    #     if climb.date_completed:
    #         climb.date_completed = datetime.now().date()
    #     db.session.commit()
    return render_template('index.html')


@app.route('/listings')
@login_required
def listings():
    """
    Show all listings 
    """
    # needs fix to make the page work when the user has not logged anything yet on the data base!!
    climbs = db.session.execute(db.select(Climb).where(Climb.completed == False, Climb.upload_author_id==current_user.id)).scalars().all()
    base_url = 'http://127.0.0.1:5000' # head url for making img dynamic
    if not climbs:
        flash("You currently have no climbs logged. Start logging your climbs!", "info")

    return render_template('climb_list.html', climbs = climbs, base_url = base_url)


@app.route('/detail/<int:climb_id>', methods = ['GET', 'POST'])
def detail(climb_id):
    """
    Log attempt and send
    """
    form = LogForm()
    base_url = 'http://127.0.0.1:5000' # head url for making img dynamic
    try:
        requested_climb = db.get_or_404(Climb, climb_id)
    except Exception as e:
        if not requested_climb:
            print('No match found')
        requested_climb = None
    if form.validate_on_submit():
        db.session.expire_all()
        current_user_id = current_user.id
        current_date = datetime.now().date()
        last_date = datetime.strptime(requested_climb.date_logged.split(' ')[0], '%Y-%m-%d').date()
        if form.sent.data:
            requested_climb.completed = True
            requested_climb.evaluation = form.evaluation.data
            requested_climb.total_attempts = requested_climb.total_attempts + form.attempt.data
            if last_date == current_date:
                requested_climb.attempt = requested_climb.attempt + form.attempt.data
            else:
                requested_climb.attempt = form.attempt.data
            requested_climb.date_completed = current_date
            requested_climb.date_logged = current_date

            p_score = analyzer.final_score(current_user_id)
            print(p_score)
            cal = get_carolies_burned()
            grade = requested_climb.grade
            new_log = Score(
                score_owner_id = current_user_id,
                performance_score = p_score,
                activity_score = cal,
                grade = grade,
                recorded_at = datetime.now()
            )
            db.session.add(new_log)
            
        else:
            requested_climb.completed = False
            requested_climb.evaluation = form.evaluation.data
            requested_climb.total_attempts = requested_climb.total_attempts + form.attempt.data
            
            if last_date == current_date:
                requested_climb.attempt = requested_climb.attempt + form.attempt.data
            else:
                requested_climb.attempt = form.attempt.data
            requested_climb.date_logged = current_date
            p_score = analyzer.final_score(current_user_id)
            cal = get_carolies_burned()
            grade = requested_climb.grade
            new_log = Score(
                score_owner_id = current_user_id,
                performance_score = p_score,
                activity_score = cal,
                grade = grade,
                recorded_at = datetime.now()
            )
            db.session.add(new_log)
            # print(p_score)
        db.session.commit()
        return redirect(url_for('listings'))

    return render_template('climb.html', base_url = base_url, climb = requested_climb, form = form)


@app.route('/add', methods=['GET', 'POST'])
def add():
    form = AddClimb()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to log in first!')
            return redirect(url_for('login'))
        
        file = form.img.data  # Get the uploaded file
        filename = secure_filename(file.filename)

        if not filename:
            file_path = None

        # Ensure the file path is correct
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)  # Save the file
        except Exception as e:
            print(f"Error saving file: {e}")
            return "File saving failed", 500

        # Create new climb record
        new_climb = Climb(
            photo=file_path,
            when_stripped=form.when_stripped.data,
            grade=form.grade.data,
            style=form.style.data,
            date_logged=datetime.now().date(),
            upload_author_id=current_user.id  # This should be dynamic,
        )
        db.session.add(new_climb)
        db.session.commit()
        return redirect(url_for('listings'))

    return render_template('add.html', form=form)


@app.route('/history')
@login_required
def history():
    climbs = db.session.execute(db.select(Climb).where(Climb.completed == True, Climb.upload_author_id == current_user.id)).scalars().all()
    if not climbs:
        flash("You currently have no climbs logged. Start logging your climbs!", "info")
    base_url = 'http://127.0.0.1:5000' # head url for making img dynamic
    return render_template('climb_list.html', climbs = climbs, base_url = base_url)


@app.route('/register', methods = ['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            if form.user_icon.data:
                img = form.user_icon.data
            else:
                img = None
            new_user = User(
                user_name = form.user_name.data,
                user_icon = img,
                email = form.email.data,
                password = generate_password_hash(form.password.data, method='pbkdf2:sha256', salt_length=8),
                current_grade = form.current_grade.data,
                home_gym = form.home_gym.data,
            )
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            flash('This email is already taken')
            return redirect(url_for('register'))
        
        login_user(new_user)
        return redirect(url_for('home'))

    return render_template('register.html', form = form)


@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        requested_email = form.email.data
        requested_pass = form.password.data
        requested_user = db.session.execute(db.select(User).where(User.email == requested_email)).scalar()
        if not requested_user:
            flash('Email not found')
            return redirect(url_for('login'))
        elif not check_password_hash(requested_user.password, requested_pass):
            flash('Password is incorrect')
            return redirect(url_for('login'))
        else:
            login_user(requested_user)
            return redirect(url_for('home'))

    return render_template('login.html', form = form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/delete/<id>')
@login_required
def delete(id):
    requested_climb = db.get_or_404(Climb, id)
    db.session.delete(requested_climb)
    db.session.commit()
    return redirect(url_for('home'))



def demo_data():
    from datetime import datetime
    # Create Users
    user1 = User(
        user_name="JohnDoe",
        user_icon="/static/icons/johndoe_icon.png",
        email="john.doe@example.com",
        password="password123",  # For testing only, never store passwords in plaintext
        current_grade="V5",
        home_gym="Mountain Gym"
    )
    user2 = User(
        user_name="JaneSmith",
        user_icon="/static/icons/janesmith_icon.png",
        email="jane.smith@example.com",
        password="password123",
        current_grade="V3",
        home_gym="Rock Center"
    )

    # Add users to the session
    db.session.add_all([user1, user2])
    db.session.commit()

    # Create Climbs
    climb1 = Climb(
        photo="/static/climb1.jpg",
        completed=False,
        grade=5,
        style="Power",
        evaluation=None,
        date_logged=str(datetime.now().date()),
        attempt=0,
        feel_strong=True,
        upload_author_id=user1.id
    )
    climb2 = Climb(
        photo="/static/climb2.jpg",
        completed=True,
        date_completed=str(datetime.now().date()),
        grade=7,
        style="Technique",
        evaluation=8,
        when_stripped=None,
        is_stripped=False,
        date_logged=str(datetime.now().date()),
        attempt=3,
        feel_strong=False,
        upload_author_id=user2.id
    )
    climb3 = Climb(
        photo="/static/climb3.jpg",
        completed=False,
        grade=3,
        style="Endurance",
        evaluation=None,
        date_logged=str(datetime.now().date()),
        attempt=1,
        feel_strong=True,
        upload_author_id=user1.id
    )
    climb4 = Climb(
        photo="/static/climb4.jpg",
        completed=True,
        date_completed=str(datetime.now().date()),
        grade=10,
        style="Finger Strength",
        evaluation=9,
        when_stripped="2024-11-18",
        is_stripped=True,
        date_logged=str(datetime.now().date()),
        attempt=4,
        feel_strong=True,
        upload_author_id=user2.id
    )
    climb5 = Climb(
        photo="/static/climb5.jpg",
        completed=False,
        grade=8,
        style="Coordination",
        evaluation=None,
        date_logged=str(datetime.now().date()),
        attempt=2,
        feel_strong=False,
        upload_author_id=user1.id
    )

    # Add climbs to the session
    db.session.add_all([climb1, climb2, climb3, climb4, climb5])
    db.session.commit()

    # Create Comments
    comment1 = Comment(
        body="Great climb, very challenging!",
        date_commented=str(datetime.now().date()),
        author_id=user1.id,
        climb_id=climb2.id
    )
    comment2 = Comment(
        body="Loved the technique on this one.",
        date_commented=str(datetime.now().date()),
        author_id=user2.id,
        climb_id=climb1.id
    )

    # Add comments to the session
    db.session.add_all([comment1, comment2])
    db.session.commit()

    print("Demo data successfully added!")

def demo():
    import random
    styles = [
        'Climp', 'Power', 'Pinch', 'Sloper', 'Balance', 'Jug', 
        'Pocket', 'Cordination', 'FootTech', 'Technical', 'Endurance'
    ]

    climbs = [
        Climb(
            photo="/static/climb_1.jpg",
            completed=False,
            date_completed=None,
            grade=5,
            style=random.choice(styles),
            evaluation=None,
            when_stripped=None,
            is_stripped=False,
            date_logged=datetime.now().strftime('%Y-%m-%d'),
            attempt=3,
            upload_author_id=3,
            feel_strong=True,
            total_attempts = 10
        ),
        Climb(
            photo="/static/climb_2.jpg",
            completed=True,
            date_completed="2024-11-20",
            grade=6,
            style=random.choice(styles),
            evaluation=4,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-18",
            attempt=2,
            upload_author_id=3,
            feel_strong=True,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_3.jpg",
            completed=False,
            date_completed=None,
            grade=4,
            style=random.choice(styles),
            evaluation=None,
            when_stripped="2024-11-25",
            is_stripped=True,
            date_logged="2024-11-22",
            attempt=1,
            upload_author_id=3,
            feel_strong=False,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_4.jpg",
            completed=True,
            date_completed="2024-11-19",
            grade=7,
            style=random.choice(styles),
            evaluation=5,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-18",
            attempt=5,
            upload_author_id=3,
            feel_strong=True,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_5.jpg",
            completed=False,
            date_completed=None,
            grade=8,
            style=random.choice(styles),
            evaluation=None,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-21",
            attempt=0,
            upload_author_id=3,
            feel_strong=False,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_6.jpg",
            completed=True,
            date_completed="2024-11-22",
            grade=6,
            style=random.choice(styles),
            evaluation=4,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-20",
            attempt=2,
            upload_author_id=3,
            feel_strong=True,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_7.jpg",
            completed=False,
            date_completed=None,
            grade=3,
            style=random.choice(styles),
            evaluation=None,
            when_stripped="2024-11-26",
            is_stripped=True,
            date_logged="2024-11-23",
            attempt=4,
            upload_author_id=3,
            feel_strong=False,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_8.jpg",
            completed=True,
            date_completed="2024-11-18",
            grade=5,
            style=random.choice(styles),
            evaluation=3,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-16",
            attempt=3,
            upload_author_id=3,
            feel_strong=True,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_9.jpg",
            completed=False,
            date_completed=None,
            grade=7,
            style=random.choice(styles),
            evaluation=None,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-22",
            attempt=2,
            upload_author_id=6,
            feel_strong=True,
            total_attempts = 10,
        ),
        Climb(
            photo="/static/climb_10.jpg",
            completed=True,
            date_completed="2024-11-21",
            grade=6,
            style=random.choice(styles),
            evaluation=4,
            when_stripped=None,
            is_stripped=False,
            date_logged="2024-11-19",
            attempt=1,
            upload_author_id=3,
            feel_strong=True,
            total_attempts = 10
        )
    ]

    # Add climbs to the database
    try:
        db.session.add_all(climbs)
        db.session.commit()
        print("10 sample climbs added to the database for user with id 6.")
    except Exception as e:
        db.session.rollback()
        print(f"Failed to add climbs: {e}")

def score_demo():
    from random import randint
    today = datetime.today()

       # Generate demo data for one week
    for i in range(7):  # 7 days
        date = today - timedelta(days=i)
        performance_score = randint(70, 100)  # Random performance score between 70 and 100
        activity_score = randint(150, 500)   # Random calorie burn (activity score)
        grade = randint(1, 10)               # Random grade between 1 and 10

        # Create a new Score record
        new_score = Score(
            performance_score=performance_score,
            activity_score=activity_score,
            grade=grade,
            score_owner_id=3,                # Ensure this field matches your model
            recorded_at=date                 # Save as a datetime object
        )

        # Add the record to the database session
        db.session.add(new_score)

    # Commit all changes to the database
    db.session.commit()

import json
@app.route('/demo')
def dashboard():
    db.session.expire_all()
    # Example data for graphs
    climbs_by_grade = {"V1": 10, "V2": 15, "V3": 5, "V4": 8, "V5": 20}  # Bar Chart
    activity_data = {
        "dates": ["2024-11-01", "2024-11-02", "2024-11-03"],
        "attempts": [5, 8, 10],
        "grades": ["V3", "V4", "V5"],
    }  # Multi-Line Chart
    # strength_breakdown = {"Finger": 40, "Power": 35, "Endurance": 25}  # Donut Chart
    # print(json.dumps(analyzer.style_attempted(current_user.id)))
    styles_attempted_today = analyzer.style_attempted(current_user.id)
    cal_burned = analyzer.cal_burned(current_user.id)
    p_score = analyzer.final_score(current_user.id)
    weekly_grade = analyzer.weekly_average_grade(current_user.id)
    completed_num = analyzer.climbs_completed(current_user.id)
    all_climbs_num = analyzer.all_climbs_num(current_user.id)
    return render_template(
        "dashboard.html",
        climbs_by_grade=json.dumps(climbs_by_grade),
        activity_data=json.dumps(activity_data),
        styles_attempted_today=styles_attempted_today,
        cal_burned=cal_burned,
        p_score=p_score,
        weekly_grade=weekly_grade,
        completed_num=completed_num,
        all_climbs_num=all_climbs_num
    )


if __name__ == '__main__':
    app.run(debug=True)