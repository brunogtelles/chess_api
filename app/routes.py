from flask import render_template, jsonify, current_app, make_response
from app import app
from app.services.lichess_service import LichessService

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/user/<username>')
def get_user(username):
    user_data = LichessService.get_user(username)
    return jsonify(user_data)

@app.route('/top-classical-players/names')
def get_top_classical_players_names():
    try:
        player_names = LichessService.get_top_classical_players_names()
        return jsonify({
            'status': 'success',
            'count': len(player_names),
            'names': player_names,
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
@app.route('/top-player/30day-history')
def get_top_player_history():
    try:
        top_player = LichessService.get_top1_classical_player()
        if not top_player:
            return jsonify({
                'status': 'error',
                'message': 'Something went wrong while searching for the best player.'
            }), 502

        history = LichessService.get_30day_rating_history(top_player)
        if not history:
            return jsonify({
                'status': 'error',
                'message': "Something went wrong while searching for the best player's rating."
            }), 502

        # Transforma no formato que você pediu {date: rating}
        rating_dict = {item['date']: item['rating'] for item in history}
        
        return jsonify({
            'status': 'success',
            'player': top_player,
            'current_rating': history[-1]['rating'],
            'history': rating_dict
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
    from flask import make_response

@app.route('/top50/rating-history-csv')
def get_top50_rating_history_csv():
    try:
        csv_data = LichessService.generate_top50_rating_history_csv()
        if not csv_data:
            return jsonify({
                'status': 'error',
                'message': 'Something went wrong while generating your CSV.'
            }), 500

        response = make_response(csv_data)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename=top50_rating_history.csv'
        return response

    except Exception as e:
        current_app.logger.exception("Something went wrong:")
        return jsonify({
            'status': 'error',
            'message': 'Server error',
            'error_details': str(e)
        }), 500