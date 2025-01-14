from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from models import User, Post, Like, Comment,db, CommentLike, Review,Product,Diet, Exercise, PostLike,JournalEntry,Diets,Recipe,TrainingPlan,Achievement
import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from flask import jsonify
import json
from itsdangerous import URLSafeTimedSerializer
import resend
from flask_migrate import Migrate   

app = Flask(__name__)
app.secret_key = 'your_secret_key'  
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

with app.app_context():
    db.create_all()
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)
@app.route('/')
def home():
    return render_template('home.html')

s = URLSafeTimedSerializer("your-secret-key")
resend.api_key = "re_7BG7Bybg_syEjY3QrHpVxd4oB7NqVUQFV"

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()

        if user:
            token = s.dumps(user.email, salt='reset-password')
            reset_url = url_for('reset_token', token=token, _external=True)

           
            resend.Emails.send({
                "from": "onboarding@resend.dev",
                "to": email,
                "subject": "Password Reset Request",
                "html": f"<p>Click <a href='{reset_url}'>here</a> to reset your password.</p>"
            })
            flash('Password reset link has been sent to your email.', 'info')
        else:
            flash('No account with that email exists.', 'danger')

    return render_template('reset_request.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    try:
        email = s.loads(token, salt='reset-password', max_age=3600)
    except Exception:
        flash('The token is invalid or expired.', 'danger')
        return redirect(url_for('reset_request'))

    if request.method == 'POST':
        new_password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('login'))

    return render_template('reset_token.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account with that email exists.', 'danger')
        elif not user.is_verified:
            flash('Please verify your email before logging in.', 'danger')
        elif check_password_hash(user.password, password):
            login_user(user)
            flash('Zalogowano pomyślnie!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Nieprawidłowe hasło lub email', 'danger')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        terms_accepted = request.form.get('terms')

       
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))

        if not terms_accepted:
            flash('You must accept the terms and conditions', 'danger')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register'))

        
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password, is_verified=False)
        db.session.add(new_user)
        db.session.commit()

       
        token = s.dumps(email, salt='email-verification')
        verification_url = url_for('verify_email', token=token, _external=True)

    
        resend.Emails.send({
            "from": "onboarding@resend.dev",
            "to": email,
            "subject": "Verify your account",
            "html": f"<p>Click <a href='{verification_url}'>here</a> to verify your account.</p>"
        })

        flash('Registration successful! Please verify your email.', 'info')
        return redirect(url_for('login'))

    return render_template('register.html')
@app.route('/terms-and-conditions')
def terms_and_conditions():
    return render_template('terms_and_conditions.html')
    
@app.route('/verify/<token>')
def verify_email(token):
    try:
        email = s.loads(token, salt='email-verification', max_age=3600)
    except Exception:
        flash('The verification link is invalid or has expired.', 'danger')
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first()
    if user and not user.is_verified:
        user.is_verified = True
        db.session.commit()
        flash('Your account has been verified! You can now log in.', 'success')
    elif user.is_verified:
        flash('Your account is already verified.', 'info')
    else:
        flash('Verification failed. Please try again.', 'danger')

    return redirect(url_for('login'))


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))

@app.route('/protected')
@login_required
def protected():
    return f"Hello, {current_user.username}! This is a protected route."

# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif','webp'}

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/forum', methods=['GET', 'POST'])
@login_required
def forum():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        tags = request.form.get('tags', '').strip()

        
        image_file = request.files.get('image')
        image_path = None
        if image_file:
            
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)

           
            image_path = image_path.replace("\\", "/")

        
        new_post = Post(
            title=title,
            content=content,
            tags=tags,
            image=image_path.split('static/')[-1] if image_path else None,
            user_id=current_user.id
        )
        db.session.add(new_post)
        db.session.commit()
        flash('Post added successfully!', 'success')
        return redirect(url_for('forum'))

    author = request.args.get('author')
    sort_by = request.args.get('sort_by', 'created_at')
    tag = request.args.get('tag')

    query = Post.query

    if author:
        query = query.filter(Post.author == author)

    if tag:
        query = query.filter(Post.tags.contains(tag))

   
    if sort_by == 'likes':
        query = query.order_by(Post.likes_count.desc())
    elif sort_by == 'created_at':
        query = query.order_by(Post.created_at.desc())

    
    page = request.args.get('page', 1, type=int)
    posts = query.paginate(page=page, per_page=5)
    for post in posts.items:
        for comment in post.comments:
            existing_like = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment.id).first()
            if existing_like:
                comment.user_liked = existing_like.like_type == 'like'
                comment.user_unliked = existing_like.like_type == 'unlike'
            else:
                comment.user_liked = False
                comment.user_unliked = False
    return render_template('forum.html', posts=posts)
@app.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    
    
    if post.user_id != current_user.id:
        flash('You are not authorized to edit this post.', 'danger')
        return redirect(url_for('forum'))
    
    if request.method == 'POST':
        post.title = request.form['title']
        post.content = request.form['content']
        
        
        image_file = request.files.get('image')
        if image_file and image_file.filename != '':
            filename = secure_filename(image_file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            post.image = image_path.split('static/')[-1]
        
        db.session.commit()
        flash('Post updated successfully!', 'success')
        return redirect(url_for('forum'))
    
    return render_template('edit_post.html', post=post)


@app.route('/post/delete/<int:post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)

    
    if post.user_id != current_user.id:
        flash('You are not authorized to delete this post.', 'danger')
        return redirect(url_for('forum'))

    
    Comment.query.filter_by(post_id=post.id).delete()

    
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted successfully!', 'success')
    return redirect(url_for('forum'))

@app.route('/post/like/<int:post_id>', methods=['POST'])
@login_required
def like_post(post_id):
    try:
        post = Post.query.get_or_404(post_id)

        
        existing_vote = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()

        if existing_vote:
            
            db.session.delete(existing_vote)
            post.likes_count -= 1
        else:
            
            new_like = PostLike(user_id=current_user.id, post_id=post_id)
            db.session.add(new_like)
            post.likes_count += 1

        db.session.commit()
        return jsonify({'likes_count': post.likes_count, 'unlikes_count': post.unlikes_count})
    except Exception as e:
        print(f"Error in like_post: {e}")  
        return jsonify({'error': 'An error occurred while liking the post'}), 500

@app.route('/post/unlike/<int:post_id>', methods=['POST'])
@login_required
def post_unlike(post_id):
    try:
        post = Post.query.get_or_404(post_id)

        
        existing_vote = PostLike.query.filter_by(user_id=current_user.id, post_id=post_id).first()

        if existing_vote:
            
            db.session.delete(existing_vote)
            post.unlikes_count -= 1
        else:
           
            new_unlike = PostLike(user_id=current_user.id, post_id=post_id)
            db.session.add(new_unlike)
            post.unlikes_count += 1

        db.session.commit()
        return jsonify({'likes_count': post.likes_count, 'unlikes_count': post.unlikes_count})
    except Exception as e:
        print(f"Error: {e}")  
        return jsonify({'error': 'An error occurred'}), 500


@app.route('/post/remove_like/<int:post_id>', methods=['POST'])
@login_required
def remove_like(post_id):
    post = Post.query.get_or_404(post_id)

    existing_like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()

    if existing_like:
        if existing_like.like_type == 'like':
            post.likes_count -= 1
        elif existing_like.like_type == 'unlike':
            post.unlikes_count -= 1

        db.session.delete(existing_like)
        db.session.commit()

    return redirect(request.referrer or url_for('forum'))


@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def add_comment(post_id):
    content = request.form['content']
    image_file = request.files.get('image')
    image_path = None

    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_path = os.path.join('uploads', filename)

    new_comment = Comment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
        image=image_path.split('static/')[-1] if image_path else None
    )
    db.session.add(new_comment)
    db.session.commit()
    flash('Comment added successfully!', 'success')
    return redirect(request.referrer or url_for('forum'))


from flask import jsonify

@app.route('/comment/like/<int:comment_id>', methods=['POST'])
@login_required
def like_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    
    existing_vote = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if existing_vote:
        if existing_vote.like_type == 'like':
            
            db.session.delete(existing_vote)
            comment.likes_count -= 1
        elif existing_vote.like_type == 'unlike':
            
            existing_vote.like_type = 'like'
            comment.unlikes_count -= 1
            comment.likes_count += 1
    else:
        
        new_like = CommentLike(user_id=current_user.id, comment_id=comment_id, like_type='like')
        db.session.add(new_like)
        comment.likes_count += 1

    db.session.commit()
    return jsonify({'likes_count': comment.likes_count, 'unlikes_count': comment.unlikes_count})


@app.route('/comment/unlike/<int:comment_id>', methods=['POST'])
@login_required
def unlike_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)

    existing_vote = CommentLike.query.filter_by(user_id=current_user.id, comment_id=comment_id).first()

    if existing_vote:
        if existing_vote.like_type == 'unlike':
            db.session.delete(existing_vote)
            comment.unlikes_count -= 1
        elif existing_vote.like_type == 'like':
            existing_vote.like_type = 'unlike'
            comment.likes_count -= 1
            comment.unlikes_count += 1
    else:
        new_unlike = CommentLike(user_id=current_user.id, comment_id=comment_id, like_type='unlike')
        db.session.add(new_unlike)
        comment.unlikes_count += 1

    db.session.commit()
    return jsonify({'likes_count': comment.likes_count, 'unlikes_count': comment.unlikes_count})


@app.route('/comment/reply/<int:comment_id>', methods=['POST'])
@login_required
def reply_to_comment(comment_id):
    parent_comment = Comment.query.get_or_404(comment_id)
    content = request.form['content']
    image_file = request.files.get('image')
    image_path = None

    if image_file:
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
        image_path = image_path.replace("\\", "/")

    reply = Comment(
        post_id=parent_comment.post_id,
        user_id=current_user.id,
        content=content,
        image=image_path.split('static/')[-1] if image_path else None,
        parent_id=comment_id
    )
    db.session.add(reply)
    db.session.commit()
    flash('Reply added successfully!', 'success')
    return redirect(request.referrer or url_for('forum'))

@app.route('/products', methods=['GET'])
def products():
    query = Product.query

    category = request.args.get('category')
    if category and category != 'All':
        query = query.filter(Product.category == category)

    min_proteins = request.args.get('min_proteins', type=float)
    if min_proteins:
        query = query.filter(Product.proteins >= min_proteins)

    max_sugars = request.args.get('max_sugars', type=float)
    if max_sugars:
        query = query.filter(Product.sugars <= max_sugars)

    min_fats = request.args.get('min_fats', type=float)
    if min_fats:
        query = query.filter(Product.fats >= min_fats)

    max_fats = request.args.get('max_fats', type=float)
    if max_fats:
        query = query.filter(Product.fats <= max_fats)

    min_health_score = request.args.get('min_health_score', type=float)
    if min_health_score:
        query = query.filter(Product.health_score >= min_health_score)

    max_health_score = request.args.get('max_health_score', type=float)
    if max_health_score:
        query = query.filter(Product.health_score <= max_health_score)

    sort_by = request.args.get('sort_by')
    if sort_by == "name":
        query = query.order_by(Product.name.asc())
    elif sort_by == "health_score":
        query = query.order_by(Product.health_score.desc())

    products = query.all()

    categories = Product.query.with_entities(Product.category).distinct().all()

    return render_template(
        'products.html',
        products=products,
        categories=[cat[0] for cat in categories]
    )



@app.route('/diets', methods=['GET'])
def diets():
    diets = Diet.query.all()
    return render_template('diets.html', diets=diets)

@app.route('/diets/<int:diet_id>', methods=['GET'])
def diet_details(diet_id):
    diet = Diet.query.get_or_404(diet_id)
    return render_template('diet_details.html', diet=diet)

@app.route('/exercises', methods=['GET'])
def exercises():
    return render_template('exercises.html')

@app.route('/exercises/<category>', methods=['GET'])
def exercise_list(category):
    query = Exercise.query.filter_by(category=category)

    body_part = request.args.get('body_part')
    if body_part and body_part != 'All':
        query = query.filter(Exercise.body_part == body_part)

    difficulty = request.args.get('difficulty')
    if difficulty and difficulty != 'All':
        query = query.filter(Exercise.difficulty == difficulty)

    exercises = query.all()

    body_parts = Exercise.query.with_entities(Exercise.body_part).distinct().all()
    difficulties = Exercise.query.with_entities(Exercise.difficulty).distinct().all()

    return render_template(
        'exercise_list.html',
        category=category,
        exercises=exercises,
        body_parts=[bp[0] for bp in body_parts],
        difficulties=[d[0] for d in difficulties],
    )


@app.route('/plan', methods=['GET'])
def plan():
    training_plans = [
        {
            "id": 1,
            "goal": "Build Muscle",
            "location": "Gym",
            "experience": "Intermediate",
            "equipment": "Full gym access",
            "health_limitations": "None",
            "details": [
                {
                    "day": "Monday",
                    "workout": "Chest and Triceps",
                    "exercises": [
                        {"name": "Bench Press", "sets": 4, "reps": "8-10"},
                        {"name": "Incline Dumbbell Press", "sets": 4, "reps": "8-10"},
                        {"name": "Cable Flyes", "sets": 3, "reps": "10-12"},
                        {"name": "Tricep Dips", "sets": 3, "reps": "10-12"},
                        {"name": "Skull Crushers", "sets": 3, "reps": "10-12"}
                    ]
                },
                {
                    "day": "Wednesday",
                    "workout": "Back and Biceps",
                    "exercises": [
                        {"name": "Pull-ups", "sets": 3, "reps": "to failure"},
                        {"name": "Barbell Rows", "sets": 4, "reps": "8-10"},
                        {"name": "Lat Pulldowns", "sets": 4, "reps": "10-12"},
                        {"name": "Barbell Curls", "sets": 3, "reps": "8-10"},
                        {"name": "Hammer Curls", "sets": 3, "reps": "10-12"}
                    ]
                },
                {
                    "day": "Friday",
                    "workout": "Legs and Shoulders",
                    "exercises": [
                        {"name": "Squats", "sets": 4, "reps": "8-10"},
                        {"name": "Leg Press", "sets": 4, "reps": "10-12"},
                        {"name": "Calf Raises", "sets": 4, "reps": "12-15"},
                        {"name": "Shoulder Press", "sets": 4, "reps": "8-10"},
                        {"name": "Lateral Raises", "sets": 3, "reps": "10-12"}
                    ]
                }
            ]
        },
        {
  "id": 2,
  "goal": "Increase Strength",
  "location": "Gym",
  "experience": "Advanced",
  "equipment": "Full gym access",
  "health_limitations": "None",
  "details": [
    {
      "day": "Tuesday",
      "workout": "Full Body Heavy Lifting",
      "exercises": [
        {"name": "Deadlift", "sets": 5, "reps": "5"},
        {"name": "Bench Press", "sets": 5, "reps": "5"},
        {"name": "Squats", "sets": 5, "reps": "5"}
      ]
    },
    {
      "day": "Thursday",
      "workout": "Upper Body Strength",
      "exercises": [
        {"name": "Military Press", "sets": 5, "reps": "5"},
        {"name": "Pull-ups", "sets": 5, "reps": "to failure"},
        {"name": "Barbell Rows", "sets": 5, "reps": "5"}
      ]
    },
    {
      "day": "Saturday",
      "workout": "Lower Body Strength",
      "exercises": [
        {"name": "Front Squats", "sets": 5, "reps": "5"},
        {"name": "Deadlifts", "sets": 5, "reps": "5"},
        {"name": "Leg Press", "sets": 5, "reps": "5"}
      ]
    }
  ]
},
        {
  "id": 3,
  "goal": "Improve Cardio Endurance",
  "location": "Outdoor",
  "experience": "Beginner",
  "equipment": "None",
  "health_limitations": "None",
  "details": [
    {
      "day": "Monday",
      "workout": "Light Running",
      "exercises": [
        {"name": "Running", "duration": "30 minutes", "pace": "Moderate"}
      ]
    },
    {
      "day": "Wednesday",
      "workout": "Interval Training",
      "exercises": [
        {"name": "Sprints", "repeats": "10", "sprint_duration": "30 seconds", "rest_duration": "1 minute"}
      ]
    },
    {
      "day": "Friday",
      "workout": "Long Distance Running",
      "exercises": [
        {"name": "Running", "duration": "60 minutes", "pace": "Steady"}
      ]
    }
  ]
},
   {
  "id": 4,
  "goal": "Functional Training",
  "location": "Gym",
  "experience": "Intermediate",
  "equipment": "Full gym access",
  "health_limitations": "None",
  "details": [
    {
      "day": "Monday",
      "workout": "Circuit Training",
      "exercises": [
        {"name": "Squats", "sets": 3, "reps": "10"},
        {"name": "Push-ups", "sets": 3, "reps": "10"},
        {"name": "Pull-ups", "sets": 3, "reps": "to failure"},
        {"name": "Planks", "duration": "1 minute"}
      ]
    },
    {
      "day": "Wednesday",
      "workout": "Core Training",
      "exercises": [
        {"name": "Russian Twists", "sets": 3, "reps": "15"},
        {"name": "Leg Raises", "sets": 3, "reps": "12"},
        {"name": "Bicycle Crunches", "sets": 3, "reps": "15"}
      ]
    },
    {
      "day": "Friday",
      "workout": "Agility and Coordination",
      "exercises": [
        {"name": "Ladder Drills", "duration": "15 minutes"},
        {"name": "Cone Drills", "duration": "15 minutes"},
        {"name": "Box Jumps", "sets": 3, "reps": "10"}
      ]
    }
  ]
},
{
  "id": 5,
  "goal": "Fat Burning",
  "location": "Outdoor",
  "experience": "Beginner",
  "equipment": "Minimal",
  "health_limitations": "None",
  "details": [
    {
      "day": "Monday",
      "workout": "Cardio Mix",
      "exercises": [
        {"name": "Jumping Jacks", "duration": "5 minutes"},
        {"name": "Running in Place", "duration": "5 minutes"},
        {"name": "Burpees", "sets": 4, "reps": "10"}
      ]
    },
    {
      "day": "Wednesday",
      "workout": "Strength and Cardio",
      "exercises": [
        {"name": "Squats", "sets": 3, "reps": "15"},
        {"name": "Push-ups", "sets": 3, "reps": "12"},
        {"name": "Jump Rope", "duration": "10 minutes"}
      ]
    },
    {
      "day": "Friday",
      "workout": "High Intensity Interval Training",
      "exercises": [
        {"name": "HIIT Circuit", "duration": "20 minutes", "details": "30 seconds on, 30 seconds off"}
      ]
    }
  ]
},
{
  "id": 6,
  "goal": "Advanced Circuit Training",
  "location": "Gym",
  "experience": "Advanced",
  "equipment": "Full gym access",
  "health_limitations": "None",
  "details": [
    {
      "day": "Tuesday",
      "workout": "Upper Body Circuit",
      "exercises": [
        {"name": "Bench Press", "sets": 3, "reps": "10"},
        {"name": "Barbell Rows", "sets": 3, "reps": "10"},
        {"name": "Dips", "sets": 3, "reps": "to failure"}
      ]
    },
    {
      "day": "Thursday",
      "workout": "Lower Body Circuit",
      "exercises": [
        {"name": "Leg Press", "sets": 3, "reps": "10"},
        {"name": "Deadlifts", "sets": 3, "reps": "10"},
        {"name": "Lunges", "sets": 3, "reps": "10 per leg"}
      ]
    },
    {
      "day": "Saturday",
      "workout": "Core Circuit",
      "exercises": [
        {"name": "Planks", "duration": "1 minute"},
        {"name": "Sit-ups", "sets": 3, "reps": "15"},
        {"name": "Hanging Leg Raises", "sets": 3, "reps": "12"}
      ]
    }
  ]
},
  {
  "id": 7,
  "goal": "Improve Mobility",
  "location": "Home",
  "experience": "Beginner",
  "equipment": "Minimal (Yoga Mat)",
  "health_limitations": "Low Mobility",
  "details": [
    {
      "day": "Monday",
      "workout": "Stretching and Yoga",
      "exercises": [
        {"name": "Full Body Stretching", "duration": "30 minutes"},
        {"name": "Yoga Sequence", "duration": "30 minutes"}
      ]
    },
    {
      "day": "Wednesday",
      "workout": "Balance Exercises",
      "exercises": [
        {"name": "Bosu Ball Squats", "sets": 3, "reps": "10"},
        {"name": "One-leg Stand", "sets": 3, "duration": "30 seconds per leg"}
      ]
    },
    {
      "day": "Friday",
      "workout": "Pilates",
      "exercises": [
        {"name": "Pilates Routine", "duration": "30 minutes"}
      ]
    }
  ]
},
{
  "id": 8,
  "goal": "Strength Training for Women",
  "location": "Gym",
  "experience": "Intermediate",
  "equipment": "Full gym access",
  "health_limitations": "None",
  "details": [
    {
      "day": "Tuesday",
      "workout": "Upper Body",
      "exercises": [
        {"name": "Bench Press", "sets": 4, "reps": "10"},
        {"name": "Assisted Pull-ups", "sets": 4, "reps": "8"},
        {"name": "Dumbbell Rows", "sets": 4, "reps": "12"}
      ]
    },
    {
      "day": "Thursday",
      "workout": "Legs and Glutes",
      "exercises": [
        {"name": "Squats", "sets": 4, "reps": "10"},
        {"name": "Single-leg Deadlift", "sets": 3, "reps": "8 per leg"},
        {"name": "Dumbbell Lunges", "sets": 4, "reps": "10 per leg"}
      ]
    },
    {
      "day": "Saturday",
      "workout": "Core and Stretching",
      "exercises": [
        {"name": "Planks", "duration": "1 minute"},
        {"name": "Leg Raises", "sets": 3, "reps": "15"},
        {"name": "Stretching Routine", "duration": "15 minutes"}
      ]
    }
  ]
},
 {
  "id": 9,
  "goal": "Strength Training for Men",
  "location": "Gym",
  "experience": "Advanced",
  "equipment": "Full gym access",
  "health_limitations": "None",
  "details": [
    {
      "day": "Monday",
      "workout": "Upper Body",
      "exercises": [
        {"name": "Bench Press", "sets": 4, "reps": "5"},
        {"name": "Cable Flyes", "sets": 4, "reps": "8"},
        {"name": "Wide Grip Pull-ups", "sets": 3, "reps": "to failure"}
      ]
    },
    {
      "day": "Wednesday",
      "workout": "Lower Body",
      "exercises": [
        {"name": "Barbell Squats", "sets": 5, "reps": "5"},
        {"name": "Deadlift", "sets": 4, "reps": "5"},
        {"name": "Barbell Lunges", "sets": 3, "reps": "10 per leg"}
      ]
    },
    {
      "day": "Friday",
      "workout": "Core and Conditioning",
      "exercises": [
        {"name": "Hanging Leg Raises", "sets": 4, "reps": "10"},
        {"name": "Russian Twists with Dumbbell", "sets": 3, "reps": "15"},
        {"name": "Interval Running", "duration": "20 minutes", "details": "30 seconds sprint, 1 minute walk"}
      ]
    }
  ]
},
{
  "id": 10,
  "goal": "Maintenance Program",
  "location": "Outdoor",
  "experience": "Intermediate",
  "equipment": "Minimal",
  "health_limitations": "Light Joint Issues",
  "details": [
    {
      "day": "Monday",
      "workout": "Upper Body Light",
      "exercises": [
        {"name": "Push-ups", "sets": 3, "reps": "15"},
        {"name": "Chair Dips", "sets": 3, "reps": "12"},
        {"name": "Dumbbell Shoulder Press", "sets": 3, "reps": "12"}
      ]
    },
    {
      "day": "Wednesday",
      "workout": "Legs and Core Light",
      "exercises": [
        {"name": "Wall Squats", "sets": 3, "reps": "15"},
        {"name": "Leg Raises", "sets": 3, "reps": "10"},
        {"name": "Plank", "duration": "30 seconds", "sets": 3}
      ]
    },
    {
      "day": "Friday",
      "workout": "Cardio and Mobility",
      "exercises": [
        {"name": "Brisk Walking", "duration": "30 minutes"},
        {"name": "Dynamic Stretching", "duration": "10 minutes"},
        {"name": "Yoga", "duration": "20 minutes"}
      ]
    }
  ]
}
  


        
    ]

    location = request.args.get('location')
    experience = request.args.get('experience')

    if location and location != 'All':
        training_plans = [plan for plan in training_plans if plan['location'] == location]

    if experience and experience != 'All':
        training_plans = [plan for plan in training_plans if plan['experience'] == experience]

    
    locations = list(set(plan['location'] for plan in training_plans))
    experiences = list(set(plan['experience'] for plan in training_plans))

    return render_template('plan.html', training_plans=training_plans, locations=locations, experiences=experiences)


@app.route('/opinions', methods=['GET', 'POST'])
def opinions():
    if request.method == 'POST':
     
        if not current_user.is_authenticated:
            flash('You need to log in to leave a review.', 'danger')
            return redirect(url_for('login'))
        
        content = request.form['content']
        rating = int(request.form['rating'])
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5.', 'danger')
            return redirect(url_for('opinions'))
        
        new_review = Review(
            user_id=current_user.id,
            content=content,
            rating=rating
        )
        db.session.add(new_review)
        db.session.commit()
        flash('Your review has been added!', 'success')
        return redirect(url_for('opinions'))
    

    reviews = Review.query.order_by(Review.created_at.desc()).all()
    average_rating = db.session.query(func.avg(Review.rating)).scalar()
    average_rating = round(average_rating, 1) if average_rating else None 

    return render_template('opinie.html', reviews=reviews, average_rating=average_rating)

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')
@app.route('/profile/details', methods=['GET'])
@login_required
def profile_details():
    return render_template('profile_details_view.html', user=current_user)

from datetime import datetime

@app.route('/profile/details/edit', methods=['GET', 'POST'])
@login_required
def edit_profile_details():
    user = current_user

    if request.method == 'POST':
        
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.age = int(request.form.get('age')) if request.form.get('age') else None
        user.bio = request.form.get('bio')
        user.weight = float(request.form.get('weight')) if request.form.get('weight') else None
        user.height = float(request.form.get('height')) if request.form.get('height') else None
        user.weight_goal = float(request.form.get('weight_goal')) if request.form.get('weight_goal') else None
        user.favorite_foods = request.form.get('favorite_foods')
        user.favorite_products = request.form.get('favorite_products')

        
        birth_date_str = request.form.get('birth_date')
        if birth_date_str:
            try:
                user.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
                return redirect(url_for('edit_profile_details'))

       
        profile_image = request.files.get('profile_image')
        if profile_image and profile_image.filename != '':
          filename = secure_filename(profile_image.filename)
          image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
          profile_image.save(image_path)
    
          user.profile_image = f'uploads/{filename}'
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile_details'))

    return render_template('profile_details_edit.html', user=user)
@app.route('/profile/training-plan')
@login_required
def my_training_plan():
    
    days_order = {
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6,
        'Sunday': 7
    }

    
    training_plans = TrainingPlan.query.filter_by(user_id=current_user.id).all()

    grouped_plans = {}
    for plan in training_plans:
        key = (plan.day_of_week, plan.start_time, plan.end_time)
        if key not in grouped_plans:
            grouped_plans[key] = {
                'id': plan.id,
                'day_of_week': plan.day_of_week,
                'start_time': plan.start_time,
                'end_time': plan.end_time,
                'exercises': []
            }
        grouped_plans[key]['exercises'].append({
            'category': plan.category,
            'exercise': plan.exercise,
            'sets': plan.sets,
            'reps': plan.reps,
            'notes': plan.notes
        })

    sorted_grouped_plans = sorted(grouped_plans.values(), key=lambda x: days_order.get(x['day_of_week'], 8))

    return render_template('training_plan.html', grouped_plans=sorted_grouped_plans)


from datetime import datetime
@app.route('/profile/training-plan/add', methods=['GET', 'POST'])
@login_required
def add_training_plan():
    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        start_time = datetime.strptime(request.form['start_time'], "%H:%M").time()
        end_time = datetime.strptime(request.form['end_time'], "%H:%M").time()
        notes = request.form.get('notes', '')

        categories = request.form.getlist('category[]')
        exercises = request.form.getlist('exercise[]')
        sets_list = request.form.getlist('sets[]')
        reps_list = request.form.getlist('reps[]')

        for i in range(len(exercises)):
            new_plan = TrainingPlan(
                user_id=current_user.id,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                category=categories[i],
                exercise=exercises[i],
                sets=int(sets_list[i]),
                reps=reps_list[i],
                notes=notes
            )
            db.session.add(new_plan)

        db.session.commit()
        flash('Training plan added successfully!', 'success')
        return redirect(url_for('my_training_plan'))

    return render_template('new_training_plan.html')
@app.route('/profile/training-plan/delete/<int:plan_id>', methods=['POST'])
@login_required
def delete_training_plan(plan_id):
    plan = TrainingPlan.query.get_or_404(plan_id)
    db.session.delete(plan)
    db.session.commit()
    flash('Training plan deleted successfully!', 'success')
    return redirect(url_for('my_training_plan'))

import logging

from datetime import datetime

@app.route('/profile/training-plan/edit/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def edit_training_plan(plan_id):
    plan = TrainingPlan.query.filter_by(id=plan_id, user_id=current_user.id).first()

    if not plan:
        flash("Training plan not found.", "danger")
        return redirect(url_for('my_training_plan'))

    if request.method == 'POST':
        try:
            
            if 'day_of_week' in request.form:
                plan.day_of_week = request.form['day_of_week']

           
            start_time_str = request.form.get('start_time')
            if start_time_str:
                plan.start_time = datetime.strptime(start_time_str, '%H:%M').time()

            end_time_str = request.form.get('end_time')
            if end_time_str:
                plan.end_time = datetime.strptime(end_time_str, '%H:%M').time()

            
            if 'category' in request.form:
                plan.category = request.form['category']

            if 'exercise' in request.form:
                plan.exercise = request.form['exercise']

            if 'sets' in request.form:
                plan.sets = int(request.form['sets'])

            if 'reps' in request.form:
                plan.reps = int(request.form['reps'])

            if 'notes' in request.form:
                plan.notes = request.form['notes']

           
            db.session.commit()
            flash('Training plan updated successfully!', 'success')
            return redirect(url_for('my_training_plan'))
        except Exception as e:
            flash(f"Error updating training plan: {e}", "danger")
            return redirect(url_for('edit_training_plan', plan_id=plan_id))

    return render_template('edit_training_plan.html', plan=plan)
@app.route('/profile/achievements')
@login_required
def achievements():
    category = request.args.get('category') 
    query = Achievement.query.filter_by(user_id=current_user.id)
    
    if category:  
        query = query.filter_by(category=category)

    user_achievements = query.all()
    categories = Achievement.query.with_entities(Achievement.category).distinct().all()
    categories = [c[0] for c in categories]  
    test_achievements = [
        {
            'title': 'Profile Complete',
            'description': 'You completed your profile!',
            'category': 'Profile',
            'icon': 'icons/profile_complete.png',
            'created_at': datetime.utcnow()
        },
        {
            'title': 'First Journal Entry',
            'description': 'You added your first journal entry!',
            'category': 'Journal',
            'icon': 'icons/journal.webp',
            'created_at': datetime.utcnow()
        }
    ]
    return render_template(
        'achievements.html', 
        achievements=test_achievements, 
        categories=categories, 
        selected_category=category
    )
def add_test_achievements():
    achievements = [
        Achievement(user_id=current_user.id, title="Test Achievement 1", description="Description 1", category="Profile", icon="icons/test1.png"),
        Achievement(user_id=current_user.id, title="Test Achievement 2", description="Description 2", category="Journal", icon="icons/test2.png"),
    ]
    db.session.bulk_save_objects(achievements)
    db.session.commit()

def get_user_achievements(user_id):
    """ Pobiera osiągnięcia użytkownika. """
    return Achievement.query.filter_by(user_id=user_id).all()

@app.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    """ Aktualizuje profil użytkownika i sprawdza osiągnięcia. """
    user = current_user
    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.age = request.form.get('age')
    user.bio = request.form.get('bio')
    user.weight = request.form.get('weight')
    user.height = request.form.get('height')
    user.birth_date = request.form.get('birth_date')
    user.weight_goal = request.form.get('weight_goal')
    user.favorite_foods = request.form.get('favorite_foods')
    user.favorite_products = request.form.get('favorite_products')

    
    if all([user.first_name, user.last_name, user.age, user.weight, user.height]):
        existing_achievement = Achievement.query.filter_by(
            user_id=user.id, title="Profile Complete").first()
        if not existing_achievement:
            add_achievement(
                user.id,
                title="Profile Complete",
                description="You completed your profile!",
                category="Profile",
                icon="icons/profile_complete.png"
            )
    print("Profile updated successfully!")

    # Sprawdzanie osiągnięć
    check_and_award_achievements(user)
    db.session.commit()
    flash("Profile updated successfully!", "success")
    return redirect(url_for('profile_details'))

def check_and_award_achievements(user):
    """Sprawdza i przyznaje osiągnięcia użytkownikowi."""

   
    if user.first_name and user.last_name and user.age and user.weight and user.height:
        if not Achievement.query.filter_by(user_id=user.id, title="Profile Complete").first():
            add_achievement(
                user.id,
                title="Profile Complete",
                description="You completed your profile!",
                category="Profile",
                icon="icons/profile_complete.png"
            )

    journal_count = JournalEntry.query.filter_by(user_id=user.id).count()
    if journal_count >= 1:
        if not Achievement.query.filter_by(user_id=user.id, title="First Journal Entry").first():
            add_achievement(
                user.id,
                title="First Journal Entry",
                description="You added your first journal entry!",
                category="Journal",
                icon="icons/first_journal.png"
            )

    
    training_plan_count = TrainingPlan.query.filter_by(user_id=user.id).count()
    if training_plan_count >= 1:
        if not Achievement.query.filter_by(user_id=user.id, title="First Training Plan").first():
            add_achievement(
                user.id,
                title="First Training Plan",
                description="You created your first training plan!",
                category="Training",
                icon="icons/first_training.png"
            )

    
    diet_count = Diets.query.filter_by(user_id=user.id).count()
    if diet_count >= 1:
        if not Achievement.query.filter_by(user_id=user.id, title="First Diet Plan").first():
            add_achievement(
                user.id,
                title="First Diet Plan",
                description="You created your first diet plan!",
                category="Diet",
                icon="icons/first_diet.png"
            )

    
    if user.weight and user.weight_goal and float(user.weight) <= float(user.weight_goal):
        if not Achievement.query.filter_by(user_id=user.id, title="Weight Goal Achieved").first():
            add_achievement(
                user.id,
                title="Weight Goal Achieved",
                description="You reached your target weight!",
                category="Diet",
                icon="icons/weight_goal.png"
            )

    
    if check_journal_streak(user.id, days=7):
        if not Achievement.query.filter_by(user_id=user.id, title="Consistency Champion").first():
            add_achievement(
                user.id,
                title="Consistency Champion",
                description="You've maintained a streak of 7 days in your journal!",
                category="Journal",
                icon="icons/consistency_champion.png"
            )

    db.session.commit()


def award_achievement(user, title, description, category, icon):
    """Dodaje osiągnięcie użytkownikowi, jeśli jeszcze go nie ma."""
    if not Achievement.query.filter_by(user_id=user.id, title=title).first():
        new_achievement = Achievement(
            user_id=user.id,
            title=title,
            description=description,
            category=category,
            icon=icon
        )
        db.session.add(new_achievement)
def check_journal_streak(user_id, days):
    """Sprawdza, czy użytkownik dodał wpisy przez 'days' dni z rzędu."""
    entries = JournalEntry.query.filter_by(user_id=user_id).order_by(JournalEntry.date.desc()).all()
    if len(entries) < days:
        return False

    current_streak = 1
    for i in range(1, len(entries)):
        delta = (entries[i - 1].date - entries[i].date).days
        if delta == 1:
            current_streak += 1
        else:
            break
    return current_streak >= days
def add_achievement(user_id, title, description, category, icon):
    """ Dodaje osiągnięcie użytkownikowi. """
    achievement = Achievement(
        user_id=user_id,
        title=title,
        description=description,
        category=category,
        icon=icon
    )
    db.session.add(achievement)
    db.session.commit()        
from flask import render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
from reportlab.pdfgen import canvas

@app.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        
        if 'email' in request.form:
            new_email = request.form['email']
            if User.query.filter_by(email=new_email).first():
                flash("This email is already in use.", "danger")
            else:
                current_user.email = new_email
                db.session.commit()
                flash("Email updated successfully!", "success")

       
        elif 'current_password' in request.form and 'new_password' in request.form:
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            if check_password_hash(current_user.password, current_password):
                current_user.password = generate_password_hash(new_password)
                db.session.commit()
                flash("Password updated successfully!", "success")
            else:
                flash("Current password is incorrect.", "danger")
    
    return render_template('settings.html', current_email=current_user.email)


from fpdf import FPDF
from datetime import datetime

@app.route('/generate_report')
@login_required
def generate_report():
    user = current_user 
    date_generated = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 

    
    diets = Diets.query.filter_by(user_id=user.id).all()
    training_plans = TrainingPlan.query.filter_by(user_id=user.id).all()

    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    
    pdf.cell(200, 10, txt="User Report", ln=True, align="C")
    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Username: {user.username}", ln=True)
    pdf.cell(200, 10, txt=f"Date Generated: {date_generated}", ln=True)
    pdf.ln(5)

    
    pdf.cell(200, 10, txt="My Diets:", ln=True, align="L")
    pdf.ln(5)
    for diet in diets:
        pdf.cell(200, 10, txt=f"Day: {diet.day_of_week}", ln=True)
        pdf.cell(200, 10, txt=f"  - Breakfast: {diet.breakfast or 'N/A'}", ln=True)
        pdf.cell(200, 10, txt=f"  - Second Breakfast: {diet.second_breakfast or 'N/A'}", ln=True)
        pdf.cell(200, 10, txt=f"  - Lunch: {diet.lunch or 'N/A'}", ln=True)
        pdf.cell(200, 10, txt=f"  - Dinner: {diet.dinner or 'N/A'}", ln=True)
        pdf.cell(200, 10, txt=f"  - Snack: {diet.snack or 'N/A'}", ln=True)
        pdf.ln(3)

    pdf.ln(5)
    pdf.cell(200, 10, txt="My Training Plans:", ln=True, align="L")
    pdf.ln(5)
    for plan in training_plans:
        pdf.cell(200, 10, txt=f"Day: {plan.day_of_week}", ln=True)
        pdf.cell(200, 10, txt=f"  - Time: {plan.start_time} - {plan.end_time}", ln=True)
        pdf.cell(200, 10, txt=f"  - Category: {plan.category}", ln=True)
        pdf.cell(200, 10, txt=f"  - Exercise: {plan.exercise}", ln=True)
        pdf.cell(200, 10, txt=f"  - Sets: {plan.sets}, Reps: {plan.reps}", ln=True)
        pdf.cell(200, 10, txt=f"  - Notes: {plan.notes or 'N/A'}", ln=True)
        pdf.ln(3)

    filename = f"report_{user.username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    pdf.output(f"static/reports/{filename}")

    return send_file(f"static/reports/{filename}", as_attachment=True)

@app.route('/profile/journal', methods=['GET'])
@login_required
def journal():
    entries = JournalEntry.query.filter_by(user_id=current_user.id).all()

    for entry in entries:
        if entry.workout_details:
            try:
                entry.workout_details = json.loads(entry.workout_details)
            except json.JSONDecodeError:
                entry.workout_details = []

    return render_template('journal.html', entries=entries)

@app.route('/profile/journal/new', methods=['GET', 'POST'])
@login_required
def new_journal_entry():
    if request.method == 'POST':
        
        date_str = request.form.get('date')
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        day_of_week = request.form.get('day_of_week')
        breakfast = request.form.get('breakfast')
        second_breakfast = request.form.get('second_breakfast')
        lunch = request.form.get('lunch')
        dinner = request.form.get('dinner')
        snack = request.form.get('snack')
        conclusions = request.form.get('conclusions')

        
        workout_types = request.form.getlist('workout_type[]')
        workout_reps = request.form.getlist('workout_reps[]')
        workout_notes = request.form.getlist('workout_notes[]')

        
        workout_details = []
        for i in range(len(workout_types)):
            workout_details.append({
                'type': workout_types[i],
                'reps': workout_reps[i],
                'notes': workout_notes[i]
            })

        
        new_entry = JournalEntry(
            user_id=current_user.id,
            date=date,
            day_of_week=day_of_week,
            breakfast=breakfast,
            second_breakfast=second_breakfast,
            lunch=lunch,
            dinner=dinner,
            snack=snack,
            workout_details=json.dumps(workout_details), 
            conclusions=conclusions
        )
        db.session.add(new_entry)
        db.session.commit()
        flash('New journal entry added!', 'success')
        return redirect(url_for('journal'))

    return render_template('new_journal_entry.html')
from datetime import datetime

@app.route('/profile/journal/edit/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def edit_journal_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()

    if request.method == 'POST':
       
        entry.date = datetime.strptime(request.form['date'], '%Y-%m-%d').date()

        entry.day_of_week = request.form['day_of_week']
        entry.breakfast = request.form['breakfast']
        entry.second_breakfast = request.form['second_breakfast']
        entry.lunch = request.form['lunch']
        entry.dinner = request.form['dinner']
        entry.snack = request.form['snack']
        entry.conclusions = request.form['conclusions']

        
        workouts = []
        workout_types = request.form.getlist('workout_type')
        workout_reps = request.form.getlist('workout_reps')
        workout_notes = request.form.getlist('workout_notes')
        for i in range(len(workout_types)):
            workouts.append({
                'type': workout_types[i],
                'reps': workout_reps[i],
                'notes': workout_notes[i]
            })
        entry.workout_details = json.dumps(workouts)

        db.session.commit()
        flash('Entry updated successfully!', 'success')
        return redirect(url_for('journal'))

    
    entry.workout_details = json.loads(entry.workout_details) if entry.workout_details else []

    return render_template('edit_journal_entry.html', entry=entry)

@app.route('/profile/journal/delete/<int:entry_id>', methods=['POST'])
@login_required
def delete_journal_entry(entry_id):
    entry = JournalEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    db.session.delete(entry)
    db.session.commit()
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('journal'))
@app.route('/profile/diets/add', methods=['GET', 'POST'])
@login_required
def add_diet():
    if request.method == 'POST':
      
        day_of_week = request.form['day_of_week']
        breakfast = request.form['breakfast']
        second_breakfast = request.form['second_breakfast']
        lunch = request.form['lunch']
        dinner = request.form['dinner']
        snack = request.form['snack']

        
        new_diet = Diets(
            user_id=current_user.id,
            day_of_week=day_of_week,
            breakfast=breakfast,
            second_breakfast=second_breakfast,
            lunch=lunch,
            dinner=dinner,
            snack=snack
        )
        db.session.add(new_diet)
        db.session.commit()

        
        recipes = [
            Recipe(breakfast_id=new_diet.id, details=request.form['breakfast_recipe']),
            Recipe(second_breakfast_id=new_diet.id, details=request.form['second_breakfast_recipe']),
            Recipe(lunch_id=new_diet.id, details=request.form['lunch_recipe']),
            Recipe(dinner_id=new_diet.id, details=request.form['dinner_recipe']),
            Recipe(snack_id=new_diet.id, details=request.form['snack_recipe']),
        ]
        db.session.add_all(recipes)
        db.session.commit()

        flash('Diet added successfully!', 'success')
        return redirect(url_for('profile_diets'))

    return render_template('add_diet.html') 

@app.route('/profile/diets', methods=['GET'])
@login_required
def profile_diets():
    if request.method == 'POST':
       
        day_of_week = request.form['day_of_week']
        breakfast = request.form['breakfast']
        second_breakfast = request.form['second_breakfast']
        lunch = request.form['lunch']
        dinner = request.form['dinner']
        snack = request.form['snack']

        
        new_diet = Diets(
            user_id=current_user.id,
            day_of_week=day_of_week,
            breakfast=breakfast,
            second_breakfast=second_breakfast,
            lunch=lunch,
            dinner=dinner,
            snack=snack
        )
        db.session.add(new_diet)
        db.session.commit()

        
        recipes = [
            Recipe(breakfast_id=new_diet.id, details=request.form['breakfast_recipe']),
            Recipe(second_breakfast_id=new_diet.id, details=request.form['second_breakfast_recipe']),
            Recipe(lunch_id=new_diet.id, details=request.form['lunch_recipe']),
            Recipe(dinner_id=new_diet.id, details=request.form['dinner_recipe']),
            Recipe(snack_id=new_diet.id, details=request.form['snack_recipe']),
        ]
        db.session.add_all(recipes)
        db.session.commit()

        flash('Diet added successfully!', 'success')
        return redirect(url_for('profile_diets'))

    
    diets = Diets.query.filter_by(user_id=current_user.id).all()
    return render_template('my_diets.html', diets=diets)

@app.route('/profile/my_diets', methods=['GET', 'POST'])
@login_required
def my_diets():
    if request.method == 'POST':
        day_of_week = request.form['day_of_week']
        breakfast = request.form['breakfast']
        second_breakfast = request.form['second_breakfast']
        lunch = request.form['lunch']
        dinner = request.form['dinner']
        snack = request.form['snack']

        
        new_diet = Diets(  
            user_id=current_user.id,
            day_of_week=day_of_week,
            breakfast=breakfast,
            second_breakfast=second_breakfast,
            lunch=lunch,
            dinner=dinner,
            snack=snack
        )
        db.session.add(new_diet)
        db.session.commit()

        
        recipes = [
            Recipe(breakfast_id=new_diet.id, details=request.form['breakfast_recipe']),
            Recipe(second_breakfast_id=new_diet.id, details=request.form['second_breakfast_recipe']),
            Recipe(lunch_id=new_diet.id, details=request.form['lunch_recipe']),
            Recipe(dinner_id=new_diet.id, details=request.form['dinner_recipe']),
            Recipe(snack_id=new_diet.id, details=request.form['snack_recipe']),
        ]
        db.session.add_all(recipes)
        db.session.commit()

        flash('Diet added successfully!', 'success')
        return redirect(url_for('my_diets'))

    diets = Diets.query.filter_by(user_id=current_user.id).all()  
    return render_template('my_diets.html', diets=diets)

@app.route('/profile/diets/edit/<int:diet_id>', methods=['GET', 'POST'])
@login_required
def edit_diet(diet_id):
    diet = Diets.query.get_or_404(diet_id)

    if request.method == 'POST':
        
        diet.day_of_week = request.form['day_of_week']
        diet.breakfast = request.form['breakfast']
        diet.second_breakfast = request.form['second_breakfast']
        diet.lunch = request.form['lunch']
        diet.dinner = request.form['dinner']
        diet.snack = request.form['snack']

        
        if request.form.get('breakfast_recipe'):
            if diet.breakfast_recipe:
                diet.breakfast_recipe[0].details = request.form['breakfast_recipe']
            else:
                diet.breakfast_recipe.append(Recipe(details=request.form['breakfast_recipe']))

        if request.form.get('second_breakfast_recipe'):
            if diet.second_breakfast_recipe:
                diet.second_breakfast_recipe[0].details = request.form['second_breakfast_recipe']
            else:
                diet.second_breakfast_recipe.append(Recipe(details=request.form['second_breakfast_recipe']))

        if request.form.get('lunch_recipe'):
            if diet.lunch_recipe:
                diet.lunch_recipe[0].details = request.form['lunch_recipe']
            else:
                diet.lunch_recipe.append(Recipe(details=request.form['lunch_recipe']))

        if request.form.get('dinner_recipe'):
            if diet.dinner_recipe:
                diet.dinner_recipe[0].details = request.form['dinner_recipe']
            else:
                diet.dinner_recipe.append(Recipe(details=request.form['dinner_recipe']))

        if request.form.get('snack_recipe'):
            if diet.snack_recipe:
                diet.snack_recipe[0].details = request.form['snack_recipe']
            else:
                diet.snack_recipe.append(Recipe(details=request.form['snack_recipe']))

        db.session.commit()
        flash('Diet updated successfully!', 'success')
        return redirect(url_for('my_diets'))

    return render_template('edit_diet.html', diet=diet)

@app.route('/profile/diets/delete/<int:diet_id>', methods=['POST'])
@login_required
def delete_diet(diet_id):
    diet = Diets.query.get_or_404(diet_id)
    db.session.delete(diet)
    db.session.commit()
    flash('Diet deleted successfully!', 'success')
    return redirect(url_for('my_diets'))

@app.route('/cookie-policy')
def cookie_policy():
    return render_template('cookie_policy.html')
@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route("/bmi", methods=["GET", "POST"])
def bmi():
    bmi_value = None
    category = None
    if request.method == "POST":
        weight = float(request.form.get("weight"))
        height = float(request.form.get("height")) / 100 
        bmi_value = round(weight / (height ** 2), 2)

        
        if bmi_value < 18.5:
            category = "Niedowaga"
        elif 18.5 <= bmi_value < 24.9:
            category = "Waga prawidłowa"
        elif 25 <= bmi_value < 29.9:
            category = "Nadwaga"
        else:
            category = "Otyłość"
    
    return render_template("bmi.html", bmi_value=bmi_value, category=category)

if __name__ == '__main__':
    with app.app_context():
        
        if not Product.query.first():
            products = [
                Product(name="Brokuły", category="Warzywa", proteins=2.8, carbs=7.0, sugars=1.7, fats=0.4, saturated_fats=0.1, salt=0.02, health_score=9.8, image="static/images/1.webp"),
    Product(name="Pierś z kurczaka", category="Mięso", proteins=31.0, carbs=0.0, sugars=0.0, fats=3.6, saturated_fats=1.0, salt=0.1, health_score=9.5, image="static/images/2.webp"),
    Product(name="Migdały", category="Orzechy", proteins=21.0, carbs=22.0, sugars=4.4, fats=49.0, saturated_fats=3.8, salt=0.0, health_score=8.7, image="static/images/3.webp"),
    Product(name="Bannan", category="Owoce", proteins=1.3, carbs=27.0, sugars=14.4, fats=0.3, saturated_fats=0.1, salt=0.01, health_score=8.0, image="static/images/4.webp"),
    Product(name="Chleb pełnoziarnisty", category="Produkty zbożowe", proteins=12.0, carbs=48.0, sugars=5.0, fats=3.0, saturated_fats=0.5, salt=1.2, health_score=7.5, image="static/images/5.webp"),
    Product(name="Pomidory", category="Warzywa", proteins=0.9, carbs=3.9, sugars=2.6, fats=0.2, saturated_fats=0.0, salt=0.02, health_score=9.0, image="static/images/6.webp"),
    Product(name="Ogórek", category="Warzywa", proteins=0.6, carbs=3.6, sugars=1.7, fats=0.1, saturated_fats=0.0, salt=0.01, health_score=9.0, image="static/images/7.webp"),
    Product(name="Soczewica", category="Rośliny strączkowe", proteins=25.8, carbs=60.1, sugars=2.0, fats=1.0, saturated_fats=0.2, salt=0.02, health_score=8.9, image="static/images/8.webp"),
    Product(name="Orzeszki ziemne", category="Orzechy", proteins=25.8, carbs=16.1, sugars=4.2, fats=49.2, saturated_fats=6.8, salt=0.0, health_score=8.5, image="static/images/9.webp"),
    Product(name="Pomarańcza", category="Owoce", proteins=0.9, carbs=12.0, sugars=9.2, fats=0.1, saturated_fats=0.0, salt=0.0, health_score=8.7, image="static/images/10.webp"),
    Product(name="Maliny", category="Owoce", proteins=1.2, carbs=11.9, sugars=4.4, fats=0.7, saturated_fats=0.0, salt=0.01, health_score=9.2, image="static/images/11.webp"),
    Product(name="Jogurt", category="Produkty mleczne", proteins=10.0, carbs=4.0, sugars=4.0, fats=5.0, saturated_fats=3.1, salt=0.1, health_score=8.3, image="static/images/12.webp"),
    Product(name="Ser żółty", category="Produkty mleczne", proteins=25.0, carbs=1.3, sugars=0.5, fats=33.0, saturated_fats=21.0, salt=2.0, health_score=7.5, image="static/images/13.webp"),
    Product(name="Stek wołowy", category="Mięso", proteins=29.0, carbs=0.0, sugars=0.0, fats=21.0, saturated_fats=8.0, salt=0.1, health_score=8.4, image="static/images/14.webp"),
    Product(name="Mleko", category="Produkty mleczne", proteins=3.3, carbs=4.8, sugars=4.8, fats=1.0, saturated_fats=0.6, salt=0.1, health_score=8.8, image="static/images/15.webp"),
    Product(name="Nerkowce", category="Orzechy", proteins=18.0, carbs=30.0, sugars=5.9, fats=44.0, saturated_fats=7.8, salt=0.02, health_score=8.2, image="static/images/16.webp"),
    Product(name="Łosoś", category="Mięso, Ryby, Jajka", proteins=20.0, carbs=0.0, sugars=0.0, fats=13.0, saturated_fats=3.1, salt=0.1, health_score=9.2, image="static/images/17.webp"),
    Product(name="Płatki owsiane", category="Produkty zbożowe", proteins=13.0, carbs=66.0, sugars=1.2, fats=7.0, saturated_fats=1.3, salt=0.01, health_score=9.5, image="static/images/18.webp"),
    Product(name="Komosa ryżowa", category="Produkty zbożowe", proteins=14.0, carbs=64.0, sugars=1.6, fats=6.0, saturated_fats=0.7, salt=0.01, health_score=9.3, image="static/images/19.webp"),
    Product(name="Ryż brązowy", category="Produkty zbożowe", proteins=7.5, carbs=77.0, sugars=0.7, fats=1.0, saturated_fats=0.2, salt=0.01, health_score=9.1, image="static/images/20.webp"),
    Product(name="Kasza gryczana", category="Produkty zbożowe", proteins=13.0, carbs=72.0, sugars=0.5, fats=3.0, saturated_fats=0.7, salt=0.01, health_score=9.0, image="static/images/21.webp"),
    Product(name="Jęczmień", category="Produkty zbożowe", proteins=12.0, carbs=73.0, sugars=0.8, fats=2.3, saturated_fats=0.5, salt=0.01, health_score=8.9, image="static/images/22.webp"),
    Product(name="Orkisz", category="Produkty zbożowe", proteins=15.0, carbs=70.0, sugars=0.7, fats=2.5, saturated_fats=0.4, salt=0.01, health_score=8.7, image="static/images/23.webp"),
    Product(name="Pierś z indyka", category="Mięso, Ryby, Jajka", proteins=29.0, carbs=0.0, sugars=0.0, fats=2.0, saturated_fats=0.5, salt=0.05, health_score=9.2, image="static/images/24.webp"),
    Product(name="Polędwica wołowa", category="Mięso, Ryby, Jajka", proteins=26.0, carbs=0.0, sugars=0.0, fats=9.0, saturated_fats=3.5, salt=0.05, health_score=8.8, image="static/images/25.webp"),
    Product(name="Makrela", category="Mięso, Ryby, Jajka", proteins=18.0, carbs=0.0, sugars=0.0, fats=13.8, saturated_fats=3.6, salt=0.2, health_score=9.0, image="static/images/26.webp"),
    Product(name="Sardynki", category="Mięso, Ryby, Jajka", proteins=25.0, carbs=0.0, sugars=0.0, fats=11.0, saturated_fats=2.5, salt=0.6, health_score=8.9, image="static/images/27.webp"),
    Product(name="Pstrąg", category="Mięso, Ryby, Jajka", proteins=19.0, carbs=0.0, sugars=0.0, fats=6.0, saturated_fats=1.5, salt=0.1, health_score=9.0, image="static/images/28.webp"),
    Product(name="Jajka", category="Mięso, Ryby, Jajka", proteins=12.0, carbs=1.0, sugars=1.0, fats=10.0, saturated_fats=3.0, salt=0.3, health_score=9.1, image="static/images/29.webp"),
    Product(name="Królik", category="Mięso, Ryby, Jajka", proteins=21.0, carbs=0.0, sugars=0.0, fats=4.5, saturated_fats=1.2, salt=0.1, health_score=9.2, image="static/images/30.webp"),
    Product(name="Krewetki", category="Mięso, Ryby, Jajka", proteins=20.0, carbs=0.2, sugars=0.0, fats=1.5, saturated_fats=0.4, salt=0.3, health_score=8.9, image="static/images/31.webp"),
    Product(name="Oliwa z oliwek", category="Tłuszcze", proteins=0.0, carbs=0.0, sugars=0.0, fats=100.0, saturated_fats=14.0, salt=0.0, health_score=9.7, image="static/images/32.webp"),
    Product(name="Olej lniany", category="Tłuszcze", proteins=0.0, carbs=0.0, sugars=0.0, fats=100.0, saturated_fats=9.0, salt=0.0, health_score=9.5, image="static/images/33.webp"),
    Product(name="Orzechy włoskie", category="Tłuszcze", proteins=15.0, carbs=14.0, sugars=2.6, fats=65.0, saturated_fats=6.1, salt=0.01, health_score=9.4, image="static/images/34.webp"),
    Product(name="Pestki dyni", category="Tłuszcze", proteins=19.0, carbs=15.0, sugars=1.3, fats=49.0, saturated_fats=8.7, salt=0.02, health_score=9.2, image="static/images/35.webp"),
    Product(name="Nasiona chia", category="Tłuszcze", proteins=17.0, carbs=42.0, sugars=0.0, fats=31.0, saturated_fats=3.3, salt=0.01, health_score=9.1, image="static/images/36.webp"),
    Product(name="Masło orzechowe", category="Tłuszcze", proteins=25.0, carbs=20.0, sugars=9.0, fats=50.0, saturated_fats=10.0, salt=0.6, health_score=8.9, image="static/images/37.webp"),
    Product(name="Orzechy laskowe", category="Tłuszcze", proteins=15.0, carbs=17.0, sugars=4.3, fats=61.0, saturated_fats=4.5, salt=0.01, health_score=9.2, image="static/images/38.webp"),
    Product(name="Olej kokosowy", category="Tłuszcze", proteins=0.0, carbs=0.0, sugars=0.0, fats=100.0, saturated_fats=90.0, salt=0.0, health_score=8.5, image="static/images/39.webp"),
    Product(name="Kasza jaglana", category="Produkty zbożowe", proteins=11.0, carbs=72.0, sugars=1.1, fats=4.0, saturated_fats=0.7, salt=0.01, health_score=8.8, image="static/images/40.webp"),
    Product(name="Makaron pełnoziarnisty", category="Produkty zbożowe", proteins=13.0, carbs=63.0, sugars=2.5, fats=2.5, saturated_fats=0.4, salt=0.01, health_score=8.7, image="static/images/41.webp"),
    Product(name="Chleb żytni", category="Produkty zbożowe", proteins=8.5, carbs=46.0, sugars=1.0, fats=1.8, saturated_fats=0.2, salt=0.5, health_score=8.6, image="static/images/42.webp"),
    Product(name="Jarmuż", category="Warzywa", proteins=4.3, carbs=9.0, sugars=0.8, fats=0.9, saturated_fats=0.1, salt=0.02, health_score=9.8, image="static/images/43.webp"),
    Product(name="Szpinak", category="Warzywa", proteins=3.5, carbs=3.6, sugars=0.4, fats=0.4, saturated_fats=0.1, salt=0.04, health_score=9.7, image="static/images/44.webp"),
    Product(name="Słodkie ziemniaki", category="Warzywa", proteins=2.0, carbs=20.0, sugars=4.2, fats=0.1, saturated_fats=0.0, salt=0.01, health_score=9.5, image="static/images/45.webp"),
    Product(name="Papryka czerwona", category="Warzywa", proteins=1.0, carbs=6.0, sugars=4.2, fats=0.3, saturated_fats=0.0, salt=0.01, health_score=9.4, image="static/images/46.webp"),
    Product(name="Borówki", category="Owoce", proteins=0.7, carbs=14.0, sugars=9.7, fats=0.3, saturated_fats=0.0, salt=0.0, health_score=9.5, image="static/images/47.webp"),
    Product(name="Jabłko", category="Owoce", proteins=0.3, carbs=14.0, sugars=10.4, fats=0.2, saturated_fats=0.0, salt=0.01, health_score=9.2, image="static/images/48.webp"),
    Product(name="Awokado", category="Owoce", proteins=2.0, carbs=8.5, sugars=0.7, fats=15.0, saturated_fats=2.1, salt=0.01, health_score=9.6, image="static/images/49.webp"),
    Product(name="Marchew", category="Warzywa", proteins=0.9, carbs=10.0, sugars=4.7, fats=0.2, saturated_fats=0.0, salt=0.03, health_score=9.3, image="static/images/50.webp"),
    Product(name="Jogurt naturalny", category="Produkty mleczne", proteins=10.0, carbs=4.0, sugars=4.0, fats=3.5, saturated_fats=2.2, salt=0.1, health_score=8.9, image="static/images/51.webp"),
    Product(name="Skyr", category="Produkty mleczne", proteins=11.0, carbs=4.0, sugars=4.0, fats=0.2, saturated_fats=0.1, salt=0.1, health_score=9.1, image="static/images/52.webp"),
    Product(name="Kefir", category="Produkty mleczne", proteins=3.5, carbs=4.5, sugars=4.5, fats=2.0, saturated_fats=1.2, salt=0.1, health_score=8.8, image="static/images/53.webp"),
    Product(name="Ricotta", category="Produkty mleczne", proteins=7.5, carbs=3.0, sugars=3.0, fats=13.0, saturated_fats=8.0, salt=0.4, health_score=8.6, image="static/images/54.webp"),
    Product(name="Twaróg", category="Produkty mleczne", proteins=11.0, carbs=3.0, sugars=2.5, fats=4.0, saturated_fats=1.8, salt=0.5, health_score=8.7, image="static/images/55.webp"),
    Product(name="Jogurt grecki", category="Produkty mleczne", proteins=9.0, carbs=4.0, sugars=4.0, fats=3.8, saturated_fats=2.4, salt=0.1, health_score=8.9, image="static/images/56.webp"),
    Product(name="Ser kozi", category="Produkty mleczne", proteins=18.0, carbs=0.1, sugars=0.1, fats=21.0, saturated_fats=15.0, salt=1.2, health_score=8.5, image="static/images/57.webp"),
    Product(name="Parmezan", category="Produkty mleczne", proteins=35.0, carbs=3.0, sugars=0.8, fats=25.0, saturated_fats=16.0, salt=1.5, health_score=8.4, image="static/images/58.webp"),
    Product(name="Ser feta", category="Produkty mleczne", proteins=14.0, carbs=4.0, sugars=4.0, fats=21.0, saturated_fats=14.0, salt=2.2, health_score=8.3, image="static/images/59.webp"),
    Product(name="Mleko odtłuszczone", category="Produkty mleczne", proteins=3.3, carbs=4.8, sugars=4.8, fats=1.0, saturated_fats=0.7, salt=0.1, health_score=8.9, image="static/images/60.webp"),
    Product(name="Maślanka", category="Produkty mleczne", proteins=3.4, carbs=4.8, sugars=4.8, fats=1.0, saturated_fats=0.7, salt=0.1, health_score=8.8, image="static/images/61.webp")]
                
            
        if not Diet.query.first():
            diets = [
                Diet(
    Tytuł="Dieta odchudzająca przy niskiej aktywności",
    Wiek="30-40",
    Płeć="Kobieta",
    Poziom_aktywności_fizycznej="Niska",
    Preferencje="Wegetariańska, bez laktozy",
    Wykluczenia="Laktoza",
    Inne_szczegóły="Skupienie na deficycie kalorycznym i zbilansowanym żywieniu",
    Śniadanie="Owsianka na mleku migdałowym z orzechami i świeżymi jagodami",
    Drugie_śniadanie="Sałatka z komosy ryżowej z awokado i pomidorkami koktajlowymi",
    Obiad="Grillowane tofu z brokułami na parze i kaszą jaglaną",
    Podwieczorek="Słupki warzyw z hummusem",
    Kolacja="Zupa krem z cukinii z pestkami słonecznika i pełnoziarnistym chlebem"
),
Diet(
    Tytuł="Dieta na masę mięśniową dla aktywnych mężczyzn",
    Wiek="20-30",
    Płeć="Mężczyzna",
    Poziom_aktywności_fizycznej="Wysoka",
    Preferencje="Tradycyjna, wysokobiałkowa",
    Wykluczenia="Brak",
    Inne_szczegóły="Bogata w białko i zdrowe tłuszcze",
    Śniadanie="Jajecznica z chlebem żytnim i awokado",
    Drugie_śniadanie="Shake białkowy z bananem i masłem orzechowym",
    Obiad="Grillowany kurczak z ryżem basmati i surówką z marchewki i jabłka",
    Podwieczorek="Omlet owsiany z owocami sezonowymi",
    Kolacja="Pieczony łosoś z puree z batatów i gotowanymi szparagami"
),
Diet(
    Tytuł="Dieta śródziemnomorska dla zdrowia serca",
    Wiek="45-60",
    Płeć="Kobieta",
    Poziom_aktywności_fizycznej="Umiarkowana",
    Preferencje="Śródziemnomorska",
    Wykluczenia="Tłuszcze trans, ograniczone czerwone mięso",
    Inne_szczegóły="Skupienie na kwasach omega-3 i jednonienasyconych tłuszczach",
    Śniadanie="Pełnoziarnisty tost z awokado, oliwą z oliwek, pomidorem i bazylią",
    Drugie_śniadanie="Garść migdałów i świeża pomarańcza",
    Obiad="Grillowana pierś z indyka z kaszą bulgur i gotowaną cukinią z papryką",
    Podwieczorek="Jogurt grecki niskotłuszczowy z miodem i orzechami włoskimi",
    Kolacja="Sałatka grecka z oliwkami, serem feta i dressingiem z oliwy z oliwek"
),
Diet(
    Tytuł="Wegańska dieta dla osób z cukrzycą",
    Wiek="35-50",
    Płeć="Mężczyzna",
    Poziom_aktywności_fizycznej="Umiarkowana",
    Preferencje="Wegańska",
    Wykluczenia="Produkty o wysokim indeksie glikemicznym",
    Inne_szczegóły="Dania o niskim IG z naciskiem na rośliny strączkowe i warzywa liściaste",
    Śniadanie="Jaglanka z orzechami włoskimi, cynamonem i borówkami",
    Drugie_śniadanie="Marchewki z pastą z pieczonej papryki i ciecierzycy",
    Obiad="Gulasz z soczewicy, pomidorów i bakłażana z brązowym ryżem",
    Podwieczorek="Koktajl z jarmużu, ogórka, jabłka i cytryny",
    Kolacja="Pieczone warzywa korzeniowe z ziołami i oliwą z oliwek"
),
Diet(
    Tytuł="Dieta ketogeniczna dla sportowców siłowych",
    Wiek="25-35",
    Płeć="Mężczyzna",
    Poziom_aktywności_fizycznej="Wysoka",
    Preferencje="Keto",
    Wykluczenia="Węglowodany powyżej 50g/dzień",
    Inne_szczegóły="Wysoka zawartość tłuszczów i białka wspierająca rozwój mięśni",
    Śniadanie="Jajecznica na maśle klarowanym z boczkiem i awokado",
    Drugie_śniadanie="Masło migdałowe z łodygami selera",
    Obiad="Stek wołowy z masłem czosnkowym i brokułami na parze",
    Podwieczorek="Kostki sera i oliwki",
    Kolacja="Pieczony łosoś z puree z kalafiora i sałatką z rukoli"
),
Diet(
    Tytuł="Dieta dla kobiet w ciąży",
    Wiek="30-40",
    Płeć="Kobieta",
    Poziom_aktywności_fizycznej="Umiarkowana",
    Preferencje="Zróżnicowana, tradycyjna",
    Wykluczenia="Surowe ryby, sery pleśniowe",
    Inne_szczegóły="Bogata w kwas foliowy, żelazo i wapń",
    Śniadanie="Owsianka z orzechami i gruszką",
    Drugie_śniadanie="Kanapka z chleba pełnoziarnistego z pastą jajeczną, sałatą i pomidorem",
    Obiad="Filet z kurczaka pieczony z ziołami, kasza pęczak i surówka z marchewki i jabłka",
    Podwieczorek="Jogurt naturalny z granolą i jagodami",
    Kolacja="Zupa krem z dyni z pestkami słonecznika i pełnoziarnistymi grzankami"
),
Diet(
    Tytuł="Dieta wysokobiałkowa na regenerację",
    Wiek="30-50",
    Płeć="Mężczyzna",
    Poziom_aktywności_fizycznej="Średnia",
    Preferencje="Wysokobiałkowa, zróżnicowana",
    Wykluczenia="Brak",
    Inne_szczegóły="Podnosi regenerację mięśni i dostarcza dużo energii",
    Śniadanie="Omlet z warzywami i pełnoziarnistym pieczywem",
    Drugie_śniadanie="Shake białkowy z mlekiem migdałowym i truskawkami",
    Obiad="Grillowana pierś z kurczaka z ryżem brązowym i brokułami",
    Podwieczorek="Serek wiejski z orzechami włoskimi",
    Kolacja="Pieczeń wołowa z puree z batatów i fasolką szparagową"
),
Diet(
    Tytuł="Dieta dla seniorów z osteoporozą",
    Wiek="60-70",
    Płeć="Kobieta",
    Poziom_aktywności_fizycznej="Niska",
    Preferencje="Tradycyjna, bogata w wapń",
    Wykluczenia="Brak",
    Inne_szczegóły="Wzmacnia kości i stawy",
    Śniadanie="Twarożek z rzodkiewką, szczypiorkiem i pieczywem pełnoziarnistym",
    Drugie_śniadanie="Jogurt naturalny z migdałami i suszonymi figami",
    Obiad="Duszone mięso cielęce z ziemniakami i buraczkami",
    Podwieczorek="Mleko wzbogacone wapniem z bananem",
    Kolacja="Sałatka z jajkiem, rukolą i pomidorem"
),
Diet(
    Tytuł="Dieta na poprawę zdrowia skóry",
    Wiek="20-30",
    Płeć="Kobieta",
    Poziom_aktywności_fizycznej="Umiarkowana",
    Preferencje="Bogata w antyoksydanty i zdrowe tłuszcze",
    Wykluczenia="Cukier rafinowany",
    Inne_szczegóły="Skupienie na promiennej i zdrowej cerze",
    Śniadanie="Koktajl z awokado, szpinaku, ogórka i kiwi",
    Drugie_śniadanie="Sałatka z rukoli, pomarańczy i orzechów włoskich",
    Obiad="Łosoś pieczony z puree z batatów i grillowanymi szparagami",
    Podwieczorek="Jogurt naturalny z miodem i nasionami chia",
    Kolacja="Komosa ryżowa z granatem, szpinakiem i awokado"
),
Diet(
    Tytuł="Dieta dla osób z celiakią",
    Wiek="20-50",
    Płeć="Dowolna",
    Poziom_aktywności_fizycznej="Umiarkowana",
    Preferencje="Bezglutenowa, zróżnicowana",
    Wykluczenia="Gluten",
    Inne_szczegóły="Bogata w błonnik i zdrowe tłuszcze",
    Śniadanie="Smoothie z mlekiem kokosowym, owocami jagodowymi i migdałami",
    Drugie_śniadanie="Pieczone bataty z hummusem",
    Obiad="Curry z ciecierzycy, mleka kokosowego i warzyw z ryżem basmati",
    Podwieczorek="Orzechy włoskie i świeży ananas",
    Kolacja="Pieczone warzywa korzeniowe z pesto z natki pietruszki"
)
            ]
        if not Exercise.query.first():
            exercises = [


                # Ćwiczenia w domu
                Exercise(name="Pompki", category="home",body_part="Klatka piersiowa", difficulty="Początkujący", description="Podstawowe ćwiczenie górnych partii ciała.",image="static/images/push_ups.webp"),
                Exercise(name="Deska", category="home", body_part="Core", difficulty="Średniozawansowany", description="Wzmacnia mięśnie brzucha.",image="static/images/plank.webp"),
                Exercise(name="Przysiady", category="home", body_part="Nogi", difficulty="Początkujący", description="Wzmacnia nogi i pośladki..",image="static/images/squats.webp"),
                Exercise(name="wykroki", category="home", body_part="Nogi", difficulty="Średniozawansowany", description="Skupia się na czworogłowych i pośladkach.",image="static/images/lunges.webp"),
                Exercise(name="Mostek", category="home", body_part="Pośladki", difficulty="Początkujący", description="Idealne do aktywacji pośladków.",image="static/images/glutebridge.webp"),
                Exercise(name="Burpees", category="home", body_part="Całe ciało", difficulty="Średniozawansowany", description="Wysoko intensywne ćwiczenie całego ciała.",image="static/images/Burpees.webp"),
                Exercise(name="Wspinaczka", category="home", body_part="Core", difficulty="Średniozawansowany", description="Ćwiczenie cardio angażujące mięśnie brzucha.",image="static/images/Mountain Climbers.webp"),
                Exercise(name="Boczna deska", category="home", body_part="Core", difficulty="Średniozawansowany", description="Strengthens obliques.",image="static/images/Side Plank.webp"),                        
                Exercise(name="Wysokie kolana", category="home", body_part="Nogi", difficulty="Początkujący", description="Ćwiczenie cardio na nogi.",image="static/images/High Knees.webp"),
                Exercise(name="Wysokie kolana", category="dom", body_part="Nogi", difficulty="Początkujący", description="Ćwiczenie cardio na nogi.", image="High Knees.webp"),
                Exercise(name="Pajacyki", category="home", body_part="Całe ciało", difficulty="Początkujący", description="Rozgrzewka cardio całego ciała.",image="static/images/Jumping Jacks.webp"),
                Exercise(name="Przysiad przy ścianie", category="home", body_part="Nogi", difficulty="Średniozawansowany", description="Wzmacnia mięśnie czworogłowe i wytrzymałość.",image="static/images/Wall Sit.webp"),
                Exercise(name="Pompki na krześle", category="home", body_part="Triceps", difficulty="Początkujący", description="Celuje w triceps za pomocą krzesła.",image="static/images/Chair Dips.webp"),
                Exercise(name="Brzuszki rowerowe", category="home", body_part="Core", difficulty="Średniozawansowany", description="Celuje w mięśnie brzucha i skośne.",image="static/images/Bicycle Crunches.webp"),
                Exercise(name="Superman", category="home", body_part="dolna część pleców", difficulty="Początkujący", description="Wzmacnia dolną część pleców.",image="static/images/Superman Exercise.webp"),
                Exercise(name="Unoszenie nóg", category="home", body_part="Core", difficulty="Średniozawansowany", description="Celuje w dolną część brzucha.",image="static/images/Leg Raises.webp"),
                Exercise(name="Wspięcia na palce", category="home", body_part="Nogi", difficulty="Początkujący", description="Buduje siłę łydek.",image="static/images/Calf Raises.webp"), 
                Exercise(name="Krążenie ramion", category="home", body_part="Barki", difficulty="Początkujący", description="Rozgrzewa mięśnie ramion.",image="static/images/Arm Circles.webp"),
                Exercise(name="Wchodzenie na podwyższenie", category="home", body_part="Nogi", difficulty="Średniozawansowany", description="Świetny na nogi i pośladki.",image="static/images/arm circles.webp"),
                Exercise(name="Pełzanie w pozycji niedźwiedzia", category="home", body_part="Całe ciało", difficulty="Średniozawansowany", description="Siła całego ciała i cardio.",image="static/images/Step-Ups.webp"),
                Exercise(name="Boksowanie w powietrzu", category="home", body_part="Ręce", difficulty="Początkujący", description="Ćwiczenia cardio i ramion.",image="static/images/Shadow Boxing.webp"),
                Exercise(name="Rosyjskie skręty tułowia", category="home", body_part="Core", difficulty="Średniozawansowany", description="Działa na mięśnie skośne.",image="static/images/Russian Twists.webp"),
                Exercise(name="Ćwiczenie ptak-pies", category="home", body_part="Core", difficulty="Początkujący", description="Poprawia stabilność rdzenia.",image="static/images/Bird Dog.webp"),
                Exercise(name="Unoszenie bioder w podporze", category="home", body_part="Pośladki", difficulty="Średniozawansowany", description="Wzmacnia pośladki i ścięgna podkolanowe.",image="static/images/Hip Thrusts.webp"),
                Exercise(name="Wypady w bok", category="home", body_part="Nogi", difficulty="Średniozawansowany", description="Celuje w wewnętrzne uda.",image="static/images/Side Lunges.webp"),
                Exercise(name="Odwrotne brzuszki", category="home", body_part="Core", difficulty="Średniozawansowany", description="Celuje w dolne mięśnie brzucha.",image="static/images/Reverse Crunches.webp"),
                
                # Ćwiczenia na siłowni
                Exercise(name="Wyciskanie sztangi na ławce", category="gym", body_part="Klatka piersiowa", difficulty="Średniozawanosowany", description="Klasyczne ćwiczenie na klatkę piersiową.",image="static/images/Bench Press.webp"),
                Exercise(name="Martwy ciąg", category="gym", body_part="Plecy", difficulty="Zawansowany", description="Złożone ćwiczenie na plecy.",image="static/images/Deadlift.webp"),
                Exercise(name="Podciąganie", category="gym", body_part="Plecy", difficulty="Średniozawansowany", description="Świetnie wzmacnia plecy i ramiona.",image="static/images/Pull-Ups.webp"),
                Exercise(name="Ściąganie drążka", category="gym", body_part="Plecy", difficulty="Początkujący", description="Celuje w mięśnie naramienne.",image="static/images/Lat Pulldown.webp"),
                Exercise(name="Wiosłowanie na wyciągu", category="gym", body_part="Plecy", difficulty="Średniozawansowany", description="Buduje siłę górnej części pleców.",image="static/images/Cable Rows.webp"),
                Exercise(name="Przysiady ze sztangą", category="gym", body_part="Nogi", difficulty="Średniozawansowany", description="Złożone ćwiczenie nóg.",image="static/images/Barbell Squats.webp"),
                Exercise(name="Wyciskanie nóg", category="gym", body_part="Nogi", difficulty="Początkujący", description="Buduje siłę nóg.",image="static/images/Leg Press.webp"),
                Exercise(name="Wykroki z hantlami", category="gym", body_part="Nogi", difficulty="Średniozawansowany", description="Buduje siłę nóg.",image="static/images/Dumbbell Lunges.webp"),
                Exercise(name="Uginanie przedramion", category="gym", body_part="Ramiona", difficulty="Początkujący", description="Wzmacnia biceps.",image="static/images/Bicep Curls.webp"),
                Exercise(name="Wyciskanie trójgłowe", category="gym", body_part="Ramiona", difficulty="Początkujący", description="Celuje w triceps.",image="static/images/Tricep Extensions.webp"),
                Exercise(name="Wyciskanie hantli na barki", category="gym", body_part="Barki", difficulty="Średniozawansowany", description="Buduje siłę ramion.",image="static/images/Dumbbell Dhoulder Press.webp"),
                Exercise(name="Wyciskanie Arnolda", category="gym", body_part="Barki", difficulty="Średniozawansowany", description="Odmiana wyciskania na barki.",image="static/images/Arnold Press.webp"),
                Exercise(name="Wiosłowanie hantlą", category="gym", body_part="Plecy", difficulty="Średniozawansowany", description="Wzmacnia mięśnie pleców.",image="static/images/Dumbbell Rows.webp"),
                Exercise(name="Wyciskanie na ławce skośnej", category="gym", body_part="Klatka piersiowa", difficulty="Średniozawansowany", description="Koncentruje się na górnej części klatki piersiowej.",image="static/images/Incline Bench Press.webp"),
                Exercise(name="Rozpiętki", category="gym", body_part="Klatka piersiowa", difficulty="Początkujący", description="Izoluje mięśnie klatki piersiowej.",image="static/images/chest fly.webp"),
                Exercise(name="Uginanie nóg", category="gym", body_part="Mięśnie dwugłowe uda", difficulty="Początkujący", description="Celuje w ścięgna podkolanowe.",image="static/images/Leg Curl.webp"),
                Exercise(name="Wspięcia na palce", category="gym", body_part="Łydki", difficulty="Początkujący", description="Wzmacnia mięśnie łydek.",image="static/images/Calf Raises.webp"),
                Exercise(name="Wiosłowanie T-bar", category="gym", body_part="Plecy", difficulty="Średniozawansowany", description="Buduje silne plecy.",image="static/images/T-Bar Row.webp"),
                Exercise(name="Przysiady na maszynie", category="gym", body_part="Nogi", difficulty="Średniozawansowany", description="Celuje w quady.",image="static/images/hacksquat.webp"),
                Exercise(name="Martwy ciąg rumuński", category="gym", body_part="Mięśnie dwugłowe uda", difficulty="Średniozawansowany", description="Koncentruje się na ścięgnach podkolanowych.",image="static/images/Romanian Deadlift.webp"),
                Exercise(name="Wyciskanie siedząc nad głową", category="gym", body_part="Barki", difficulty="Średniozawansowany", description="Wzmacnia ramiona.",image="static/images/Seated Overhead Press.webp"),
                Exercise(name="Wyciskanie hantli na klatkę", category="gym", body_part="Klatka piersiowa", difficulty="Początkujący", description="Działa na mięśnie klatki piersiowej.",image="static/images/Dumbbell Chest Press.webp"),
                Exercise(name="Wzruszanie ramionami z hantlami", category="gym", body_part="Czworoboczne", difficulty="Początkujący", description="Wzmacnia plecy",image="static/images/Dumbbell Shrugs.webp"),
                Exercise(name="Uginanie przedramion na modlitewniku", category="gym", body_part="Ramiona", difficulty="Początkujący", description="Izoluje biceps.",image="static/images/Preacher Curl.webp"),
                Exercise(name="Unoszenie bokiem na wyciągu", category="gym", body_part="Barki", difficulty="Średniozawansowany", description="Działa na mięśnie ramion.",image="static/images/Cable Lateral Raises.webp"),
                
            


            ]
            db.session.add_all(exercises)            
            db.session.add_all(diets)
            db.session.add_all(products)
            db.session.commit()
app.run(debug=True)


