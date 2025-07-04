from app.models import ScoutingData, Team, Match
import statistics
from flask import current_app
import random

def calculate_team_metrics(team_id):
    """Calculate key performance metrics for a team based on their scouting data"""
    # Get the team object to log the team number
    team = Team.query.get(team_id)
    team_number = team.team_number if team else team_id
    
    # Get all scouting data for this team
    scouting_data = ScoutingData.query.filter_by(team_id=team_id).all()
    
    if not scouting_data:
        print(f"    No scouting data found for team {team_number} (ID: {team_id})")
        return {}
    else:
        print(f"    Found {len(scouting_data)} scouting records for team {team_number}")
        
    # Initialize metrics dictionary
    metrics = {}
    
    # Get game configuration
    game_config = current_app.config.get('GAME_CONFIG', {})
    
    # Find metric IDs from game config
    component_metric_ids = []
    total_metric_id = None
    metric_info = {}
    
    # Identify metrics from game config
    if 'data_analysis' in game_config and 'key_metrics' in game_config['data_analysis']:
        for metric in game_config['data_analysis']['key_metrics']:
            metric_id = metric.get('id')
            metric_info[metric_id] = metric
            
            # Check if this is a component metric or the total metric
            if metric.get('is_total_component'):
                component_metric_ids.append(metric_id)
            elif 'total' in metric_id.lower() or 'tot' == metric_id.lower():
                total_metric_id = metric_id
    
    # If no component metrics defined, use default IDs
    if not component_metric_ids:
        component_metric_ids = ["apt", "tpt", "ept"]
        print(f"    WARNING: No component metrics defined in config, using defaults: {component_metric_ids}")
    else:
        print(f"    Using component metrics from config: {component_metric_ids}")
    
    # If no total metric defined, use default ID
    if not total_metric_id:
        total_metric_id = "tot"
        print(f"    WARNING: No total metric defined in config, using default: {total_metric_id}")
    else:
        print(f"    Using total metric from config: {total_metric_id}")
    
    # Prepare metric collection arrays
    metric_values = {metric_id: [] for metric_id in component_metric_ids}
    metric_values[total_metric_id] = []
    
    # Track raw endgame positions for capability calculation
    endgame_positions = []
    
    # Calculate individual match metrics for the team
    print(f"    Calculating metrics across {len(scouting_data)} matches:")
    for idx, data in enumerate(scouting_data):
        match_info = f"Match {data.match.match_number}" if data.match else f"Record #{idx+1}"
        
        # Calculate point values for this match
        for metric_id in component_metric_ids:
            metric_value = data.calculate_metric(metric_id)
            metric_values[metric_id].append(metric_value)
            
        # Calculate total points
        total_pts = data.calculate_metric(total_metric_id)
        metric_values[total_metric_id].append(total_pts)
        
        print(f"      {match_info}: {total_metric_id}={total_pts}, components={[f'{id}={metric_values[id][-1]}' for id in component_metric_ids]}")
        
        # Capture raw endgame position data - directly get from the data dictionary
        if 'endgame_position' in data.data:
            endgame_positions.append(data.data['endgame_position'])
    
    # Calculate average point values
    for metric_id, values in metric_values.items():
        if values:
            # Store with both the dynamic ID and a standardized key for backward compatibility
            metrics[metric_id] = statistics.mean(values)
            
            # Create standardized keys for the frontend
            if metric_id in component_metric_ids:
                # Map component metric IDs to standard keys
                if metric_id == component_metric_ids[0]:
                    metrics['auto_points'] = metrics[metric_id]
                elif metric_id == component_metric_ids[1] if len(component_metric_ids) > 1 else None:
                    metrics['teleop_points'] = metrics[metric_id]
                elif metric_id == component_metric_ids[2] if len(component_metric_ids) > 2 else None:
                    metrics['endgame_points'] = metrics[metric_id]
            
            # Map total metric ID to standard key
            if metric_id == total_metric_id:
                metrics['total_points'] = metrics[metric_id]
    
    # Custom calculation for endgame capability - find highest position the team has reached
    if endgame_positions:
        # Find endgame_position element in config to get point values
        position_points = {}
        endgame_element = None
        for element in game_config.get('endgame_period', {}).get('scoring_elements', []):
            if element.get('id') == 'endgame_position' and element.get('points'):
                position_points = element.get('points')
                endgame_element = element
                break
        
        # Set default values
        highest_position = "None"
        highest_points = 0
        
        # Find the highest value position this team has demonstrated
        if position_points:
            for position in endgame_positions:
                if position in position_points and position_points[position] > highest_points:
                    highest_points = position_points[position]
                    highest_position = position
            
        # Store both the position name and the point value
        metrics['endgame_capability'] = highest_points
        metrics['endgame_position_name'] = highest_position
    
    # Calculate other key metrics defined in the game configuration
    if 'data_analysis' in game_config and 'key_metrics' in game_config['data_analysis']:
        for metric_config in game_config['data_analysis']['key_metrics']:
            metric_id = metric_config.get('id')
            formula = metric_config.get('formula')
            
            # Skip metrics we've already calculated
            if metric_id in metrics:
                continue
                
            # Skip if no formula defined
            if not formula:
                continue
            
            # Calculate this metric for each scouting record
            metric_values = []
            for data in scouting_data:
                try:
                    value = data.calculate_metric(formula)
                    metric_values.append(value)
                except Exception as e:
                    print(f"Error calculating {metric_id} for team {team_id}: {str(e)}")
            
            # Calculate average if we have values
            if metric_values:
                metrics[metric_id] = statistics.mean(metric_values)
    
    return metrics

def predict_match_outcome(match_id):
    """Predict the outcome of a match based on team performance metrics"""
    match = Match.query.get(match_id)
    if not match:
        return None
    
    print("\n" + "="*80)
    print(f"PREDICTING MATCH {match.match_type} {match.match_number} (ID: {match_id})")
    print("="*80)
    
    # Get team numbers for each alliance from the alliance strings
    # Alliance fields store comma-separated team numbers like "118,254,2767"
    red_team_numbers = match.red_alliance.split(',') if match.red_alliance else []
    blue_team_numbers = match.blue_alliance.split(',') if match.blue_alliance else []
    
    print(f"DEBUG: Raw red alliance string: '{match.red_alliance}'")
    print(f"DEBUG: Raw blue alliance string: '{match.blue_alliance}'")
    print(f"DEBUG: Initial parsed red team numbers: {red_team_numbers}")
    print(f"DEBUG: Initial parsed blue team numbers: {blue_team_numbers}")
    
    # Clean up team numbers - strip whitespace and convert to integers
    red_team_numbers_int = []
    for num in red_team_numbers:
        num = num.strip()
        if num and num.isdigit():
            red_team_numbers_int.append(int(num))
        else:
            print(f"WARNING: Invalid red team number: '{num}'")
    
    blue_team_numbers_int = []
    for num in blue_team_numbers:
        num = num.strip()
        if num and num.isdigit():
            blue_team_numbers_int.append(int(num))
        else:
            print(f"WARNING: Invalid blue team number: '{num}'")
    
    print(f"DEBUG: Cleaned red team numbers: {red_team_numbers_int}")
    print(f"DEBUG: Cleaned blue team numbers: {blue_team_numbers_int}")
    
    # Query teams - check if any teams are missing from the database
    all_team_numbers = red_team_numbers_int + blue_team_numbers_int
    all_teams = Team.query.filter(Team.team_number.in_(all_team_numbers)).all() if all_team_numbers else []
    found_team_numbers = [team.team_number for team in all_teams]
    
    missing_teams = [num for num in all_team_numbers if num not in found_team_numbers]
    if missing_teams:
        print(f"WARNING: These teams are not in the database: {missing_teams}")
    
    # Query teams
    red_teams = []
    blue_teams = []
    
    for team in all_teams:
        if team.team_number in red_team_numbers_int:
            red_teams.append(team)
        elif team.team_number in blue_team_numbers_int:
            blue_teams.append(team)
    
    print(f"DEBUG: Found {len(red_teams)} red teams: {[team.team_number for team in red_teams]}")
    print(f"DEBUG: Found {len(blue_teams)} blue teams: {[team.team_number for team in blue_teams]}")
    
    # Calculate team metrics and alliance strength
    red_alliance_teams = []
    print("\nRED ALLIANCE METRICS:")
    for team in red_teams:
        print(f"  Calculating metrics for red team {team.team_number} (ID: {team.id})")
        metrics = calculate_team_metrics(team.id)
        
        if metrics:
            print(f"  Team {team.team_number} has metrics: {list(metrics.keys())}")
            # Check for critical metrics
            if not metrics.get('total_points') and not any(key for key in metrics.keys() if 'tot' in key.lower()):
                print(f"  WARNING: Team {team.team_number} missing total points metric!")
            red_alliance_teams.append({
                'team': team,
                'metrics': metrics
            })
        else:
            print(f"  WARNING: No metrics found for team {team.team_number}")
    
    blue_alliance_teams = []
    print("\nBLUE ALLIANCE METRICS:")
    for team in blue_teams:
        print(f"  Calculating metrics for blue team {team.team_number} (ID: {team.id})")
        metrics = calculate_team_metrics(team.id)
        
        if metrics:
            print(f"  Team {team.team_number} has metrics: {list(metrics.keys())}")
            # Check for critical metrics
            if not metrics.get('total_points') and not any(key for key in metrics.keys() if 'tot' in key.lower()):
                print(f"  WARNING: Team {team.team_number} missing total points metric!")
            blue_alliance_teams.append({
                'team': team,
                'metrics': metrics
            })
        else:
            print(f"  WARNING: No metrics found for team {team.team_number}")
            
    print(f"\nFinal red alliance teams for prediction: {[team_data['team'].team_number for team_data in red_alliance_teams]}")
    print(f"Final blue alliance teams for prediction: {[team_data['team'].team_number for team_data in blue_alliance_teams]}")
    
    # Get game configuration to find total_metric_id
    game_config = current_app.config.get('GAME_CONFIG', {})
    total_metric_id = None
    
    # Identify metrics from game config
    print("\nLOOKING FOR TOTAL METRIC ID:")
    if 'data_analysis' in game_config and 'key_metrics' in game_config['data_analysis']:
        for metric in game_config['data_analysis']['key_metrics']:
            metric_id = metric.get('id')
            # Check if this is the total metric
            if 'total' in metric_id.lower() or 'tot' == metric_id.lower():
                total_metric_id = metric_id
                print(f"  Found total metric ID: {total_metric_id}")
                break
    
    # If no total metric defined, use default ID
    if not total_metric_id:
        total_metric_id = "tot"
        print(f"  No total metric found in config, using default: {total_metric_id}")
    
    # Calculate alliance scores based on total points (predictive model)
    red_alliance_score = 0
    print("\nCALCULATING RED ALLIANCE SCORE:")
    for team_data in red_alliance_teams:
        team_number = team_data['team'].team_number
        # Try different metric IDs in order of preference
        team_score = 0
        if total_metric_id in team_data['metrics']:
            team_score = team_data['metrics'][total_metric_id]
            print(f"  Team {team_number}: {team_score} points from {total_metric_id}")
        elif 'total_points' in team_data['metrics']:
            team_score = team_data['metrics']['total_points']
            print(f"  Team {team_number}: {team_score} points from total_points")
        else:
            print(f"  WARNING: Team {team_number} has no total points metric!")
        
        red_alliance_score += team_score
    
    blue_alliance_score = 0
    print("\nCALCULATING BLUE ALLIANCE SCORE:")
    for team_data in blue_alliance_teams:
        team_number = team_data['team'].team_number
        # Try different metric IDs in order of preference
        team_score = 0
        if total_metric_id in team_data['metrics']:
            team_score = team_data['metrics'][total_metric_id]
            print(f"  Team {team_number}: {team_score} points from {total_metric_id}")
        elif 'total_points' in team_data['metrics']:
            team_score = team_data['metrics']['total_points']
            print(f"  Team {team_number}: {team_score} points from total_points")
        else:
            print(f"  WARNING: Team {team_number} has no total points metric!")
        
        blue_alliance_score += team_score
    
    # Add some randomness to the prediction (matches aren't perfectly predictable)
    red_random_factor = 0.9 + 0.2 * random.random()
    blue_random_factor = 0.9 + 0.2 * random.random()
    
    final_red_score = red_alliance_score * red_random_factor
    final_blue_score = blue_alliance_score * blue_random_factor
    
    print(f"\nFINAL SCORES:")
    print(f"  Red alliance base score: {red_alliance_score}, random factor: {red_random_factor:.2f}, final: {final_red_score:.1f}")
    print(f"  Blue alliance base score: {blue_alliance_score}, random factor: {blue_random_factor:.2f}, final: {final_blue_score:.1f}")
    
    # Determine expected winner
    winner = 'red' if final_red_score > final_blue_score else 'blue'
    confidence = abs(final_red_score - final_blue_score) / (final_red_score + final_blue_score) if (final_red_score + final_blue_score) > 0 else 0
    
    print(f"  Predicted winner: {winner.upper()} with {confidence*100:.1f}% confidence")
    print("="*80 + "\n")
    
    prediction = {
        'red_alliance': {
            'teams': red_alliance_teams,
            'predicted_score': round(final_red_score)
        },
        'blue_alliance': {
            'teams': blue_alliance_teams,
            'predicted_score': round(final_blue_score)
        },
        'predicted_winner': winner,
        'confidence': confidence
    }
    
    return prediction

def get_match_details_with_teams(match_id):
    """Get complete match details with team information and metrics"""
    match = Match.query.get(match_id)
    if not match:
        return None
        
    # Get prediction data
    prediction = predict_match_outcome(match_id)
    
    # Enhance with actual match score if available
    if match.red_score is not None and match.blue_score is not None:
        match_completed = True
        actual_winner = 'red' if match.red_score > match.blue_score else 'blue' if match.blue_score > match.red_score else 'tie'
    else:
        match_completed = False
        actual_winner = None
    
    # Combine everything into a complete match report
    match_details = {
        'match': match,
        'prediction': prediction,
        'match_completed': match_completed,
        'actual_winner': actual_winner,
        'prediction_correct': match_completed and prediction and actual_winner == prediction['predicted_winner']
    }
    
    return match_details