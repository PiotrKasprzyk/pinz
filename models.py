from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import json
db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    profile_image = db.Column(db.String(300), nullable=True) 
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    bio = db.Column(db.Text, nullable=True)
    weight = db.Column(db.Float, nullable=True)  
    height = db.Column(db.Float, nullable=True)  
    birth_date = db.Column(db.Date, nullable=True)  
    weight_goal = db.Column(db.Float, nullable=True)  
    favorite_foods = db.Column(db.Text, nullable=True)  
    favorite_products = db.Column(db.Text, nullable=True)
    diets = db.relationship('Diets', backref='user', lazy=True)
    training_plan = db.relationship('TrainingPlan', backref='user', lazy=True)
    @staticmethod
    def get(user_id):
        return User.query.get(int(user_id))
class Post(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    likes = db.relationship('Like', backref='post', lazy='dynamic')
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    likes_count = db.Column(db.Integer, default=0)
    unlikes_count = db.Column(db.Integer, default=0) 
    tags = db.Column(db.Text, nullable=True)
    comments = db.relationship(
        'Comment', backref='post', lazy='dynamic', cascade="all, delete-orphan"
    )
class Like(db.Model):
    __tablename__ = 'like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    like_type = db.Column(db.String(10), nullable=False)  
class PostLike(db.Model):
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id', name='_user_post_uc'),)


class Comment(db.Model):
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(300), nullable=True)  
    likes_count = db.Column(db.Integer, default=0)  
    unlikes_count = db.Column(db.Integer, default=0)  
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=True)
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')  


class CommentLike(db.Model):
    __tablename__ = 'comment_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False)
    like_type = db.Column(db.String(10), nullable=False)  

    
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id', name='_user_comment_uc'),)
class Review(db.Model):
    __tablename__ = 'review'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False) 
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    proteins = db.Column(db.Float, nullable=False)  
    carbs = db.Column(db.Float, nullable=False)    
    sugars = db.Column(db.Float, nullable=False)    
    fats = db.Column(db.Float, nullable=False)      
    saturated_fats = db.Column(db.Float, nullable=False)  
    salt = db.Column(db.Float, nullable=False)     
    health_score = db.Column(db.Float, nullable=False)  
    image = db.Column(db.String(255), nullable=True)
class Diet(db.Model):
    __tablename__ = 'diet'
    id = db.Column(db.Integer, primary_key=True)
    Tytuł = db.Column(db.String(100), nullable=False) 
    Wiek = db.Column(db.String(20), nullable=False)  
    Płeć = db.Column(db.String(10), nullable=False) 
    Poziom_aktywności_fizycznej = db.Column(db.String(50), nullable=False)  
    Preferencje = db.Column(db.Text, nullable=True)   
    Wykluczenia = db.Column(db.Text, nullable=True)   
    Inne_szczegóły = db.Column(db.Text, nullable=True) 
    Śniadanie = db.Column(db.Text, nullable=False)   
    Drugie_śniadanie = db.Column(db.Text, nullable=True) 
    Obiad = db.Column(db.Text, nullable=False)        
    Podwieczorek = db.Column(db.Text, nullable=True)        
    Kolacja = db.Column(db.Text, nullable=False)       
class Exercise(db.Model):
    __tablename__ = 'exercise'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  
    category = db.Column(db.String(50), nullable=False) 
    body_part = db.Column(db.String(50), nullable=False)  
    difficulty = db.Column(db.String(20), nullable=False)  
    description = db.Column(db.Text, nullable=True)  
    image = db.Column(db.String(255), nullable=True)  
class JournalEntry(db.Model):
    __tablename__ = 'journal_entry'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    day_of_week = db.Column(db.String(15), nullable=False)
    breakfast = db.Column(db.Text, nullable=True)
    second_breakfast = db.Column(db.Text, nullable=True)
    lunch = db.Column(db.Text, nullable=True)
    dinner = db.Column(db.Text, nullable=True)
    snack = db.Column(db.Text, nullable=True)
    workout_type = db.Column(db.Text, nullable=True)
    workout_reps = db.Column(db.String(50), nullable=True) 
    workout_notes = db.Column(db.Text, nullable=True)
    conclusions = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    workout_details = db.Column(db.Text, nullable=True) 
    def get_workout_details(self):
            try:
                return json.loads(self.workout_details) if self.workout_details else []
            except json.JSONDecodeError:
                return []
class Recipe(db.Model):
    __tablename__ = 'recipe'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False, default="Default content")
    breakfast_id = db.Column(db.Integer, db.ForeignKey('diets.id'), nullable=True)
    second_breakfast_id = db.Column(db.Integer, db.ForeignKey('diets.id'), nullable=True)
    lunch_id = db.Column(db.Integer, db.ForeignKey('diets.id'), nullable=True)
    dinner_id = db.Column(db.Integer, db.ForeignKey('diets.id'), nullable=True)
    snack_id = db.Column(db.Integer, db.ForeignKey('diets.id'), nullable=True)
    
    details = db.Column(db.Text, nullable=False)  

class Diets(db.Model):
    __tablename__ = 'diets'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.String(10), nullable=False)  
    breakfast = db.Column(db.String(100), nullable=True)
    second_breakfast = db.Column(db.String(100), nullable=True)
    lunch = db.Column(db.String(100), nullable=True)
    dinner = db.Column(db.String(100), nullable=True)
    snack = db.Column(db.String(100), nullable=True)
    breakfast_recipe = db.relationship('Recipe', foreign_keys=[Recipe.breakfast_id], backref='diets_breakfast', lazy=True)
    second_breakfast_recipe = db.relationship('Recipe', foreign_keys=[Recipe.second_breakfast_id], backref='diets_second_breakfast', lazy=True)
    lunch_recipe = db.relationship('Recipe', foreign_keys=[Recipe.lunch_id], backref='diets_lunch', lazy=True)
    dinner_recipe = db.relationship('Recipe', foreign_keys=[Recipe.dinner_id], backref='diets_dinner', lazy=True)
    snack_recipe = db.relationship('Recipe', foreign_keys=[Recipe.snack_id], backref='diets_snack', lazy=True)
class TrainingPlan(db.Model):
    __tablename__ = 'training_plan'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)  
    start_time = db.Column(db.Time, nullable=False)       
    end_time = db.Column(db.Time, nullable=False)        
    category = db.Column(db.String(50), nullable=False)   
    exercise = db.Column(db.String(100), nullable=False)  
    sets = db.Column(db.Integer, nullable=False)          
    reps = db.Column(db.String(20), nullable=False)        
    notes = db.Column(db.Text, nullable=True)              
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    
class Achievement(db.Model):
    __tablename__ = 'achievement'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)  
    achieved_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    icon = db.Column(db.String(300), nullable=True)  
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    
    user = db.relationship('User', backref='achievements')




