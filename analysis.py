import pandas as pd
import sqlite3
from datetime import datetime, timedelta

# Database connection class
class DataFrame:
    def __init__(self, db_path):
        # Establish connection and load data
        connection = sqlite3.connect(db_path)

        # Load the climbs table
        query_climb = 'SELECT * FROM climbs'
        self.climbs_df = pd.read_sql_query(query_climb, connection)

        # Load the users table
        query_user = 'SELECT * FROM users'
        self.user_df = pd.read_sql_query(query_user, connection)

        # Load the score table
        query_score = 'SELECT * FROM score'
        self.score_df = pd.read_sql_query(query_score, connection)

        # Close the connection
        connection.close()


# Analysis and processing class
class ClimbingAnalyzer:
    def __init__(self, df):
        self.df = df  # Pass an instance of the DataFrame class

    def excercise_today(self, user_id):
        user_climb_data = self.df.climbs_df[self.df.climbs_df.upload_author_id == user_id]
        user_climb_data['date_logged'] = pd.to_datetime(user_climb_data['date_logged'])
        today_data = user_climb_data[user_climb_data['date_logged'].dt.date == datetime.now().date()]

        if today_data.empty:
            return None
        return today_data

    def user_max_grade(self, user_id):
        user_detail = self.df.user_df[self.df.user_df.id == user_id]
        if user_detail.empty:
            raise ValueError(f"No user found with ID: {user_id}")
        return int(user_detail.current_grade)

    def performance_score(self, user_id):
        exercise_data = self.excercise_today(user_id)
        if exercise_data is None or exercise_data.empty:
            raise ValueError(f"No exercise data found for user {user_id} today.")

        completed_climbs = exercise_data[exercise_data['completed'] == True]
        if completed_climbs.empty:
            return 0

        grade = completed_climbs['grade']
        attempts = completed_climbs['attempt']
        max_grade = self.user_max_grade(user_id)

        intensity_level = grade / max_grade
        max_attempts = 100
        score = intensity_level * (max_attempts / (attempts + max_attempts)) * 100
        return int(score.mean())

    def final_score(self, user_id):
        score = self.performance_score(user_id)
        completed_climbs = self.excercise_today(user_id)[self.excercise_today(user_id)['completed'] == True]
        completed_climb_num = completed_climbs['grade'].count()

        # Adjust score based on completed climbs
        if completed_climb_num == 1:
            score -= 10
        elif completed_climb_num == 2:
            score -= 8
        elif completed_climb_num == 3:
            score -= 6
        elif completed_climb_num == 4:
            score -= 4
        elif completed_climb_num == 5:
            score += 3
        elif completed_climb_num == 6:
            score += 5
        elif completed_climb_num > 6:
            score += 7

        # Additional bonuses for challenging climbs
        user_max_grade = self.user_max_grade(user_id)
        bonus = (
            completed_climbs[completed_climbs['grade'] >= user_max_grade - 2].shape[0] * 2 +
            completed_climbs[completed_climbs['grade'] == user_max_grade].shape[0] * 3 +
            completed_climbs[completed_climbs['grade'] > user_max_grade].shape[0] * 5
        )
        score += bonus

        # Cap the score at 100
        return min(score, 100)

    def score_and_calories(self, user_id):
        score_df = self.df.score_df[self.df.score_df.score_owner_id == user_id]
        score_df['recorded_at'] = pd.to_datetime(score_df['recorded_at'])
        score_df['date'] = score_df['recorded_at'].dt.date

        # Get the latest record for each day
        latest_per_day = score_df.loc[score_df.groupby('date')['recorded_at'].idxmax()]
        return latest_per_day

    def weekly_average_grade(self, user_id):
        score_df = self.df.score_df[self.df.score_df['score_owner_id'] == user_id]
        score_df['recorded_at'] = pd.to_datetime(score_df['recorded_at'])
        score_df['date'] = score_df['recorded_at'].dt.date

        # Get the latest record for each day
        latest_per_day = score_df.loc[score_df.groupby('date')['recorded_at'].idxmax()]

        # Filter for the last 7 days
        one_week_ago = datetime.now().date() - timedelta(days=7)
        last_week_data = latest_per_day[latest_per_day['date'] >= one_week_ago]
        return round(last_week_data['grade'].mean(), 1)

    def all_completed_grade(self, user_id):
        user_climbs = self.df.climbs_df[self.df.climbs_df['upload_author_id'] == user_id]
        completed_climbs = user_climbs[user_climbs['completed'] == True]
        return completed_climbs.groupby('grade').count()

    def style_completed(self, user_id):
        user_climbs = self.df.climbs_df[self.df.climbs_df['upload_author_id'] == user_id]
        completed_climbs = user_climbs[user_climbs['completed'] == True]
        return completed_climbs.groupby('style').count()[['id']]

    def style_attempted(self, user_id):
        user_climbs = self.df.climbs_df[self.df.climbs_df['upload_author_id'] == user_id]
        user_climbs['date_logged'] = pd.to_datetime(user_climbs['date_logged']).dt.date
        today_climbs = user_climbs[user_climbs['date_logged'] == datetime.now().date()]
        return today_climbs.groupby('style').count()[['id']]

    def grade_attempted(self, user_id):
        user_climbs = self.df.climbs_df[self.df.climbs_df['upload_author_id'] == user_id]
        user_climbs['date_logged'] = pd.to_datetime(user_climbs['date_logged']).dt.date
        today_climbs = user_climbs[user_climbs['date_logged'] == datetime.now().date()]
        return today_climbs[['grade', 'attempt']]

    def all_climbs_num(self, id):
        all_climbs_registered = df.climbs_df[df.climbs_df.upload_author_id == id]
        return all_climbs_registered.count().id

    def cal_burned(self, user_id):
        user_score = df.score_df[df.score_df['score_owner_id'] == user_id]
        if not user_score.empty:
            latest_data = user_score.loc[0]
            return latest_data.performance_score
        else:
            return None
        
    def climbs_completed(self, id):
        all_climbs_registered = df.climbs_df[df.climbs_df.upload_author_id == id]
        return all_climbs_registered[all_climbs_registered.completed == True].count().id

# Instantiate and Use
db_path = "/Users/yuta/Desktop/climb_proj/instance/climbs.db"
df = DataFrame(db_path)
analyzer = ClimbingAnalyzer(df)

# print("Today's exercise data:", analyzer.excercise_today(3))
# print("Weekly average grade:", analyzer.weekly_average_grade(3))
# print("Final score for today:", analyzer.final_score(3))

# print(analyzer.grade_attempted(3))


