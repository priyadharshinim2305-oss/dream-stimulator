# app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
from functools import wraps
import json
import time
from datetime import datetime
import os

from config import Config
from database import db, User, DreamSession, DreamScene, PlayerChoice, DreamSymbol, PsychologicalTimeline
from dream_engine import dream_engine
from ai_director import AIDirector, ChoiceType, DreamChoice

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

db.init_app(app)

# Initialize AI Director
ai_director = AIDirector(dream_engine)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """Landing page."""
    return render_template('index.html')


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register new user."""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if len(username) < 3 or len(password) < 6:
        return jsonify({"error": "Username must be 3+ chars, password 6+ chars"}), 400
    
    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({"error": "Username already taken"}), 400
    
    user = User(
        username=username,
        psychological_profile={
            "confrontation": 0.5,
            "avoidance": 0.5,
            "curiosity": 0.5,
            "denial": 0.5,
            "recurring_symbols": [],
            "primary_fears": []
        }
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True
    
    return jsonify({
        "success": True,
        "user": {"id": user.id, "username": user.username}
    })


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login existing user."""
    data = request.get_json()
    username = data.get('username', '')
    password = data.get('password', '')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    session['user_id'] = user.id
    session['username'] = user.username
    session.permanent = True
    
    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "total_dreams": user.total_dreams
        }
    })


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """Logout user."""
    session.clear()
    return jsonify({"success": True})


@app.route('/api/auth/status')
def auth_status():
    """Check authentication status."""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({
                "authenticated": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "total_dreams": user.total_dreams
                }
            })
    return jsonify({"authenticated": False})


@app.route('/dream')
@login_required
def dream_page():
    """Dream interface page."""
    return render_template('dream.html')


@app.route('/api/dream/start', methods=['POST'])
@login_required
def start_dream():
    """Start a new dream session."""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    # Create new session
    dream_session = DreamSession(
        user_id=user_id,
        fear_level=0.0,
        tension_level=0.0,
        dream_depth=1,
        is_nightmare=False
    )
    db.session.add(dream_session)
    db.session.commit()
    
    # Initialize AI Director with user profile
    ai_director.initialize_session(user.psychological_profile)
    
    # Store session ID
    session['dream_session_id'] = dream_session.id
    session['scene_number'] = 0
    session['scene_start_time'] = time.time() * 1000
    
    # Generate first scene
    session_data = {
        "fear_level": dream_session.fear_level,
        "tension_level": dream_session.tension_level,
        "dream_depth": dream_session.dream_depth,
        "is_nightmare": dream_session.is_nightmare
    }
    
    scene_data = ai_director.generate_scene(session_data, 0, None)
    
    # Save scene
    dream_scene = DreamScene(
        session_id=dream_session.id,
        scene_number=0,
        narrative=scene_data.narrative,
        atmosphere=scene_data.atmosphere,
        imagery=scene_data.imagery,
        choices=[{
            "text": c.text,
            "choice_type": c.choice_type.value,
            "fear_impact": c.fear_impact,
            "tension_impact": c.tension_impact,
            "tags": c.psychological_tags
        } for c in scene_data.choices]
    )
    db.session.add(dream_scene)
    db.session.commit()
    
    session['current_scene_id'] = dream_scene.id
    
    return jsonify({
        "session_id": dream_session.id,
        "scene": {
            "id": dream_scene.id,
            "narrative": scene_data.narrative,
            "atmosphere": scene_data.atmosphere,
            "choices": [{"index": i, "text": c.text} for i, c in enumerate(scene_data.choices)],
            "depth": dream_session.dream_depth,
            "depth_name": Config.DEPTH_LEVELS.get(dream_session.dream_depth, "Unknown"),
            "fear_level": dream_session.fear_level,
            "tension_level": dream_session.tension_level
        }
    })


@app.route('/api/dream/choose', methods=['POST'])
@login_required
def make_choice():
    """Process player's choice and generate next scene."""
    data = request.get_json()
    choice_index = data.get('choice_index', 0)
    
    user_id = session['user_id']
    dream_session_id = session.get('dream_session_id')
    scene_id = session.get('current_scene_id')
    scene_start = session.get('scene_start_time', time.time() * 1000)
    
    if not dream_session_id or not scene_id:
        return jsonify({"error": "No active dream session"}), 400
    
    # Calculate response time
    response_time_ms = int(time.time() * 1000 - scene_start)
    
    # Get current state
    dream_session = DreamSession.query.get(dream_session_id)
    current_scene = DreamScene.query.get(scene_id)
    
    if not dream_session or not current_scene:
        return jsonify({"error": "Session not found"}), 404
    
    # Get the chosen option
    choices_data = current_scene.choices or []
    if choice_index >= len(choices_data):
        choice_index = 0
    
    choice_data = choices_data[choice_index]
    
    # Convert to DreamChoice object
    chosen = DreamChoice(
        text=choice_data.get("text", ""),
        choice_type=ChoiceType(choice_data.get("choice_type", 0)),
        fear_impact=choice_data.get("fear_impact", 0),
        tension_impact=choice_data.get("tension_impact", 0),
        psychological_tags=choice_data.get("tags", [])
    )
    
    # Process choice
    session_data = {
        "fear_level": dream_session.fear_level,
        "tension_level": dream_session.tension_level,
        "dream_depth": dream_session.dream_depth,
        "is_nightmare": dream_session.is_nightmare
    }
    
    updated_state, analysis = ai_director.process_choice(
        chosen, response_time_ms, session_data
    )
    
    # Save player choice
    player_choice = PlayerChoice(
        scene_id=scene_id,
        user_id=user_id,
        choice_text=chosen.text,
        choice_index=choice_index,
        fear_delta=analysis["fear_change"],
        tension_delta=analysis["tension_change"],
        psychological_tags=analysis["tags"],
        response_time_ms=response_time_ms
    )
    db.session.add(player_choice)
    
    # Update session
    dream_session.fear_level = updated_state["fear_level"]
    dream_session.tension_level = updated_state["tension_level"]
    dream_session.dream_depth = updated_state["dream_depth"]
    dream_session.is_nightmare = updated_state["is_nightmare"]
    dream_session.total_choices += 1
    
    # Check for dream ending conditions
    scene_number = session.get('scene_number', 0) + 1
    should_end = (
        scene_number >= 15 or  # Max scenes
        (dream_session.is_nightmare and scene_number >= 8) or  # Nightmares end sooner
        (dream_session.dream_depth >= 5 and scene_number >= 5)  # Deep dreams are intense
    )
    
    if should_end:
        # End the dream
        ending = ai_director.generate_ending(updated_state, scene_number)
        dream_session.ended_at = datetime.utcnow()
        
        # Update user stats
        user = User.query.get(user_id)
        user.total_dreams += 1
        
        # Save psychological analysis
        all_choices = PlayerChoice.query.filter_by(user_id=user_id).join(
            DreamScene
        ).filter(DreamScene.session_id == dream_session_id).all()
        
        choices_history = [{
            "choice_type": c.choice_index,
            "response_time": c.response_time_ms
        } for c in all_choices]
        
        final_analysis = ai_director.get_session_analysis(choices_history)
        
        # Save to psychological timeline
        timeline = PsychologicalTimeline(
            user_id=user_id,
            session_id=dream_session_id,
            fear_patterns={"final_level": dream_session.fear_level},
            avoidance_behaviors={"score": final_analysis["behavioral_patterns"]["avoidance"]},
            confrontation_score=final_analysis["behavioral_patterns"]["confrontation"],
            recurring_themes=final_analysis.get("recurring_symbols", [])
        )
        db.session.add(timeline)
        
        # Update user profile
        profile = user.psychological_profile or {}
        patterns = final_analysis["behavioral_patterns"]
        profile["confrontation"] = (profile.get("confrontation", 0.5) + patterns["confrontation"]) / 2
        profile["avoidance"] = (profile.get("avoidance", 0.5) + patterns["avoidance"]) / 2
        profile["curiosity"] = (profile.get("curiosity", 0.5) + patterns["curiosity"]) / 2
        
        # Add recurring symbols
        existing_symbols = profile.get("recurring_symbols", [])
        new_symbols = final_analysis.get("symbols_encountered", [])
        for symbol in new_symbols:
            if symbol not in existing_symbols:
                existing_symbols.append(symbol)
        profile["recurring_symbols"] = existing_symbols[-20:]  # Keep last 20
        
        user.psychological_profile = profile
        
        db.session.commit()
        
        # Clear session
        session.pop('dream_session_id', None)
        session.pop('current_scene_id', None)
        
        return jsonify({
            "ended": True,
            "ending_narrative": ending,
            "analysis": final_analysis,
            "final_state": {
                "fear_level": dream_session.fear_level,
                "tension_level": dream_session.tension_level,
                "depth_reached": dream_session.dream_depth,
                "was_nightmare": dream_session.is_nightmare,
                "total_scenes": scene_number
            }
        })
    
    # Generate next scene
    previous_choice = {
        "choice_type": chosen.choice_type.value,
        "text": chosen.text
    }
    
    scene_data = ai_director.generate_scene(updated_state, scene_number, previous_choice)
    
    # Save new scene
    dream_scene = DreamScene(
        session_id=dream_session_id,
        scene_number=scene_number,
        narrative=scene_data.narrative,
        atmosphere=scene_data.atmosphere,
        imagery=scene_data.imagery,
        choices=[{
            "text": c.text,
            "choice_type": c.choice_type.value,
            "fear_impact": c.fear_impact,
            "tension_impact": c.tension_impact,
            "tags": c.psychological_tags
        } for c in scene_data.choices]
    )
    db.session.add(dream_scene)
    db.session.commit()
    
    # Update session tracking
    session['scene_number'] = scene_number
    session['current_scene_id'] = dream_scene.id
    session['scene_start_time'] = time.time() * 1000
    
    return jsonify({
        "ended": False,
        "scene": {
            "id": dream_scene.id,
            "narrative": scene_data.narrative,
            "atmosphere": scene_data.atmosphere,
            "choices": [{"index": i, "text": c.text} for i, c in enumerate(scene_data.choices)],
            "depth": dream_session.dream_depth,
            "depth_name": Config.DEPTH_LEVELS.get(dream_session.dream_depth, "Unknown"),
            "fear_level": dream_session.fear_level,
            "tension_level": dream_session.tension_level,
            "is_nightmare": dream_session.is_nightmare
        },
        "choice_feedback": {
            "your_choice": chosen.text,
            "psychological_tags": analysis["tags"],
            "was_panicked": analysis["panic_response"],
            "showed_hesitation": analysis["hesitation"]
        }
    })


@app.route('/api/dream/wake', methods=['POST'])
@login_required
def wake_up():
    """Force end the dream (wake up)."""
    dream_session_id = session.get('dream_session_id')
    
    if not dream_session_id:
        return jsonify({"error": "No active dream"}), 400
    
    dream_session = DreamSession.query.get(dream_session_id)
    if dream_session:
        dream_session.ended_at = datetime.utcnow()
        
        user = User.query.get(session['user_id'])
        user.total_dreams += 1
        
        db.session.commit()
    
    session.pop('dream_session_id', None)
    session.pop('current_scene_id', None)
    
    return jsonify({
        "success": True,
        "message": "You force yourself awake. The dream shatters into fragments, already fading..."
    })


@app.route('/history')
@login_required
def history_page():
    """Dream history page."""
    return render_template('history.html')


@app.route('/api/history')
@login_required
def get_history():
    """Get user's dream history."""
    user_id = session['user_id']
    
    sessions = DreamSession.query.filter_by(user_id=user_id).order_by(
        DreamSession.started_at.desc()
    ).limit(20).all()
    
    history = []
    for s in sessions:
        history.append({
            "id": s.id,
            "started_at": s.started_at.isoformat(),
            "ended_at": s.ended_at.isoformat() if s.ended_at else None,
            "fear_level": s.fear_level,
            "dream_depth": s.dream_depth,
            "depth_name": Config.DEPTH_LEVELS.get(s.dream_depth, "Unknown"),
            "was_nightmare": s.is_nightmare,
            "total_choices": s.total_choices
        })
    
    # Get user's psychological profile
    user = User.query.get(user_id)
    profile = user.psychological_profile or {}
    
    return jsonify({
        "dreams": history,
        "total_dreams": user.total_dreams,
        "psychological_profile": profile
    })


@app.route('/api/history/<int:session_id>')
@login_required
def get_dream_detail(session_id):
    """Get detailed history of a specific dream."""
    user_id = session['user_id']
    
    dream_session = DreamSession.query.filter_by(
        id=session_id, user_id=user_id
    ).first()
    
    if not dream_session:
        return jsonify({"error": "Dream not found"}), 404
    
    scenes = DreamScene.query.filter_by(session_id=session_id).order_by(
        DreamScene.scene_number
    ).all()
    
    scenes_data = []
    for scene in scenes:
        choices = PlayerChoice.query.filter_by(scene_id=scene.id).all()
        scenes_data.append({
            "scene_number": scene.scene_number,
            "narrative": scene.narrative,
            "atmosphere": scene.atmosphere,
            "choices_made": [{
                "text": c.choice_text,
                "response_time_ms": c.response_time_ms,
                "tags": c.psychological_tags
            } for c in choices]
        })
    
    # Get psychological timeline entry
    timeline = PsychologicalTimeline.query.filter_by(session_id=session_id).first()
    
    return jsonify({
        "session": {
            "id": dream_session.id,
            "started_at": dream_session.started_at.isoformat(),
            "ended_at": dream_session.ended_at.isoformat() if dream_session.ended_at else None,
            "fear_level": dream_session.fear_level,
            "tension_level": dream_session.tension_level,
            "dream_depth": dream_session.dream_depth,
            "was_nightmare": dream_session.is_nightmare
        },
        "scenes": scenes_data,
        "analysis": {
            "fear_patterns": timeline.fear_patterns if timeline else {},
            "confrontation_score": timeline.confrontation_score if timeline else 0,
            "recurring_themes": timeline.recurring_themes if timeline else []
        }
    })


# Initialize database tables
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
