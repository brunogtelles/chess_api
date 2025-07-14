import requests
from flask import current_app
from requests.exceptions import RequestException
from datetime import datetime, timedelta
import csv
from io import StringIO


class LichessService:
    @staticmethod
    def _make_request(endpoint):
        headers = {}
        if current_app.config["LICHESS_TOKEN"]:
            headers["Authorization"] = f"Bearer {current_app.config['LICHESS_TOKEN']}"

        try:
            response = requests.get(
                f"{current_app.config['LICHESS_API_URL']}{endpoint}",
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except RequestException as e:
            current_app.logger.error(f"Error accessing Lichess API: {str(e)}")
            return None

    @staticmethod
    def get_user(username):
        return LichessService._make_request(f"/user/{username}")

    @staticmethod
    def get_top_classical_players():
        return LichessService._make_request("/player/top/50/classical")

    @staticmethod
    def get_user_rating_history(username):
        return LichessService._make_request(f"/user/{username}/rating-history")

    @staticmethod
    def get_top_classical_players_names():
        data = LichessService._make_request("/player/top/50/classical")

        if not data or "users" not in data:
            return []

        return [user["username"] for user in data["users"]]

    @staticmethod
    def get_top1_classical_player():
        data = LichessService._make_request("/player/top/1/classical")
        if not data or "users" not in data or len(data["users"]) == 0:
            current_app.logger.error("Unexpected return: %s", data)
            return None
        return data["users"][0]["username"]

    @staticmethod
    def get_top_player_30day_history():
        top_player = LichessService.get_top1_classical_player()
        if not top_player:
            return None

        return {
            "player": top_player,
            "history": LichessService.get_30day_rating_history(top_player),
        }

    @staticmethod
    def get_30day_rating_history(username):
        profile = LichessService._make_request(f"/user/{username}")
        if not profile:
            return None
    
        current_rating = profile.get('perfs', {}).get('classical', {}).get('rating')
        if not current_rating:
            return None

        history_data = LichessService._make_request(f"/user/{username}/rating-history")
    
        ratings = {}
        if history_data:
            for game_type in history_data:
                if game_type['name'].lower() == 'classical':
                    for point in game_type['points']:
                        year, month, day, rating = point
                        date_key = f"{year}-{month:02d}-{day:02d}"
                        ratings[date_key] = rating
                    break

        end_date = datetime.now()
        start_date = end_date - timedelta(days=29)
    
        daily_ratings = []
    
        for day in range(30):
            date = (start_date + timedelta(days=day))
            date_key = date.strftime('%Y-%m-%d')
            display_date = date.strftime('%b %d')
        
            rating = ratings.get(date_key, current_rating)
        
            daily_ratings.append({
                'date': display_date,
                'rating': rating,
                'is_estimated': date_key not in ratings
            })
    
        return daily_ratings
    
    @staticmethod
    def get_30day_rating_series(username):
        try:
            profile = LichessService._make_request(f"/user/{username}")
            if not profile:
                current_app.logger.error(f"History not found for {username}")
                return None
        
            current_rating = profile.get('perfs', {}).get('classical', {}).get('rating')
            if not current_rating:
                current_app.logger.error(f"Rating classical not found for {username}")
                return None

            history_data = LichessService._make_request(f"/user/{username}/rating-history")
            ratings = {}

            if history_data:
                for game_type in history_data:
                    if game_type['name'].lower() == 'classical':
                        for point in game_type['points']:
                            try:
                                year, month, day, rating = point
                                if 1 <= month <= 12 and 1 <= day <= 31:
                                    date_key = (datetime(year, month, day)).date()
                                    ratings[date_key] = rating
                            except (ValueError, TypeError) as e:
                                current_app.logger.warning(f"Inválid rating: {point} - {str(e)}")
                        break

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=29)
        
            rating_series = []
            last_known_rating = current_rating
        
            for day in range(30):
                current_date = start_date + timedelta(days=day)
                last_known_rating = ratings.get(current_date, last_known_rating)
                rating_series.append(last_known_rating)
        
            return rating_series

        except Exception as e:
            current_app.logger.error(f"Something went wrong while searching for {username} history: {str(e)}")
            return None

    @staticmethod
    def generate_top50_rating_history_csv():
        try:
            top_players = LichessService._make_request("/player/top/50/classical")
            if not top_players or 'users' not in top_players:
                current_app.logger.error("Invalid return.")
                return None

            output = StringIO()
            writer = csv.writer(output)
        
            headers = ['Username']
            today = datetime.now().date()
            for day in range(30):
                date = today - timedelta(days=29-day)
                headers.append(date.strftime('%Y-%m-%d'))
            writer.writerow(headers)

            for player in top_players['users']:
                username = player['username']
                rating_series = LichessService.get_30day_rating_series(username)
                if rating_series and len(rating_series) == 30:
                    writer.writerow([username] + rating_series)
                else:
                    current_app.logger.warning(f"Incomplete data for {username}")

            return output.getvalue()

        except Exception as e:
            current_app.logger.error(f"Something went wrong while generating your CSV: {str(e)}")
            return None
