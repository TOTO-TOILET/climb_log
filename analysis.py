import pandas as pd 
import sqlite3
from datetime import datetime, timedelta

db_path = "/Users/yuta/Desktop/climb_proj/instance/climbs.db"
connection = sqlite3.connect(db_path)


class DataFrame:
    def __init__(self, db_path):
        connection = sqlite3.connect(db_path)

        query_climb = 'SELECT * FROM climbs'
        self.climbs_df = pd.read_sql_query(query_climb, connection)

        query_user = 'SELECT * FROM users'
        self.user_df = pd.read_sql_query(query_user, connection)

        query_score = 'SELECT * FROM score'
        self.score_df = pd.read_sql_query(query_score, connection)
        
        connection.close()


# this returns today's climbing activity of user with specified id
def excercise_today(id):
    df = DataFrame()
    user_climb_data = df.climbs_df[df.climbs_df.upload_author_id==id] # make the value inside upload_author_id dynamic
    user_climb_data['date_logged'] = pd.to_datetime(user_climb_data.date_logged) # convert the value to datetime format for conpatibility
    user_data_today = user_climb_data[user_climb_data['date_logged'].dt.date == datetime.now().date()]
    if user_data_today.empty: # need to implement error handling in case there is no excersize history that day
        return None
    else:
        return user_data_today
    
    
# this returns max_grade of the user with specified id 
def user_max(id):
    df = DataFrame()
    user_detail = df.user_df[df.user_df.id == id]
    return int(user_detail.current_grade)


# this returns performance score based solely on the attempt number and the grade which is before being refined to the final score 
def performance_score(id):
    max_attempts = 100
    grade = excercise_today(id)[excercise_today(id).completed == True].grade # this ensures that its getting only completed climbs
    user_max_grade = user_max(id)
    user_attempt = excercise_today(id)[excercise_today(id).completed == True].attempt # this ensures that its getting only completed climbs
    intensity_level = grade / user_max_grade
    score = intensity_level * (max_attempts / (user_attempt + max_attempts)) * 100
    return int(score.mean())


# this returns the final score of the day 
def final_score(id):
    score = performance_score(id)
    user_max_grade = user_max(id)
    climbs_completed = excercise_today(id)[excercise_today(id).completed == True]
    completed_climb_num = climbs_completed.count().grade
    completed_climb_num

    # add or deduct number from perfromnace score based on the number of climbs completed
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

    # give extra score if the user cpmpleted climbs with the grade higher than the grade 2 grades lower than their max grade
    base_hard_climbs = climbs_completed[climbs_completed.grade >= user_max_grade -2].count().id
    score += base_hard_climbs * 2
    score

    # give extra score if the user cpmpleted their max grade
    max_grade = climbs_completed[climbs_completed.grade == user_max_grade].count().id
    score += max_grade * 3

    # give extra score if the user cpmpleted climbs with the grade higher than their max grade
    hard_grade = climbs_completed[climbs_completed.grade > user_max_grade].count().id
    score += hard_grade * 5
    
    if score > 100:
        score = 100
    return score


# this returns table formatted data frame for graph for keeping track of score and corolies bunred throughout a week 
def score_and_caroly(id):
    df = DataFrame()
    score_df = df.score_df[df.score_df.score_owner_id == id]
    score_df['recorded_at'] = pd.to_datetime(score_df.recorded_at)
    score_df['date'] = score_df['recorded_at'].dt.date
    latest_per_day = score_df.loc[score_df.groupby('date')['recorded_at'].idxmax()]
    return latest_per_day


# returns average grade completed in the past 7 days 
def weekly_average_grade(id):  
    df = DataFrame()
    score_df = df.score_df[df.score_df['score_owner_id'] == id]
    score_df['recorded_at'] = pd.to_datetime(score_df['recorded_at'])
    score_df['date'] = score_df['recorded_at'].dt.date
    latest_per_day = score_df.loc[score_df.groupby('date')['recorded_at'].idxmax()]

    # Filter for the last 7 days
    one_week_ago = datetime.now().date() - timedelta(days=7)
    last_week_data = latest_per_day[latest_per_day['date'] >= one_week_ago]
    mean_grade = last_week_data['grade'].mean()
    return mean_grade


# this retunrs table format data frame for all climbs complete by grade 
def all_completed_grade(id):
    df = DataFrame()
    user_climbs = df.climbs_df[df.climbs_df['upload_author_id'] == id]
    filtered_users_climbs = user_climbs[user_climbs['completed'] == True]
    total_grade_completed = filtered_users_climbs.groupby('grade').count()
    return total_grade_completed


# this returns table formated data frame for style of all the climbs completed
def style_completed(id):
    df = DataFrame()
    user_climbs = df.climbs_df[df.climbs_df['upload_author_id'] == id]
    # print(user_climbs)
    total_completed = user_climbs[user_climbs.completed == True]
    total_completed = total_completed.groupby('style').count()
    by_style = total_completed[['id']]
    return by_style


# this returns a table format data with styles and number of climbs in each styles user attempted today 
def style_attempted(id):
    df = DataFrame()
    user_climbs = df.climbs_df[df.climbs_df['upload_author_id'] == id]
    user_climbs['date_logged'] = pd.to_datetime(user_climbs.date_logged).dt.date
    total_today = user_climbs[user_climbs.date_logged == datetime.now().date()]
    total_today = total_today.groupby('style').count()
    by_style = total_today[['id']]
    return by_style


# this returns tabel formatted data frame for climbs attempted today by grade 
def grade_attempted(id):
    df = DataFrame()
    user_climbs = df.climbs_df[df.climbs_df['upload_author_id'] == id]
    user_climbs = user_climbs[user_climbs.completed == True]
    user_climbs['date_logged'] = pd.to_datetime(user_climbs.date_logged).dt.date
    total_today = user_climbs[user_climbs.date_logged == datetime.now().date()]
    filtered_total_today = total_today[['grade', 'attempt']]
    return filtered_total_today


