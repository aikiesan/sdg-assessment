import click
from flask.cli import with_appcontext
from app import db
from app.models.sdg import SdgGoal

SDG_GOAL_DATA = [
    {'number': 1, 'name': 'No Poverty', 'color_code': '#E5243B', 'description': 'End poverty...'},
    {'number': 2, 'name': 'Zero Hunger', 'color_code': '#DDA63A', 'description': 'End hunger...'},
    {'number': 3, 'name': 'Good Health and Well-being', 'color_code': '#4C9F38', 'description': 'Ensure healthy lives...'},
    {'number': 4, 'name': 'Quality Education', 'color_code': '#C5192D', 'description': 'Ensure inclusive education...'},
    {'number': 5, 'name': 'Gender Equality', 'color_code': '#FF3A21', 'description': 'Achieve gender equality...'},
    {'number': 6, 'name': 'Clean Water and Sanitation', 'color_code': '#26BDE2', 'description': 'Ensure availability...'},
    {'number': 7, 'name': 'Affordable and Clean Energy', 'color_code': '#FCC30B', 'description': 'Ensure access to energy...'},
    {'number': 8, 'name': 'Decent Work and Economic Growth', 'color_code': '#A21942', 'description': 'Promote sustained growth...'},
    {'number': 9, 'name': 'Industry, Innovation and Infrastructure', 'color_code': '#FD6925', 'description': 'Build resilient infrastructure...'},
    {'number': 10, 'name': 'Reduced Inequality', 'color_code': '#DD1367', 'description': 'Reduce inequality...'},
    {'number': 11, 'name': 'Sustainable Cities and Communities', 'color_code': '#FD9D24', 'description': 'Make cities inclusive...'},
    {'number': 12, 'name': 'Responsible Consumption and Production', 'color_code': '#BF8B2E', 'description': 'Ensure sustainable patterns...'},
    {'number': 13, 'name': 'Climate Action', 'color_code': '#3F7E44', 'description': 'Take urgent action...'},
    {'number': 14, 'name': 'Life Below Water', 'color_code': '#0A97D9', 'description': 'Conserve oceans...'},
    {'number': 15, 'name': 'Life on Land', 'color_code': '#56C02B', 'description': 'Protect ecosystems...'},
    {'number': 16, 'name': 'Peace and Justice Strong Institutions', 'color_code': '#00689D', 'description': 'Promote peaceful societies...'},
    {'number': 17, 'name': 'Partnerships to achieve the Goal', 'color_code': '#19486A', 'description': 'Strengthen the means...'},
]

@click.command('populate-goals')
@with_appcontext
def populate_goals_command():
    """Populates the sdg_goals table with goals 1-17."""
    print("Populating sdg_goals table...")
    added_count = 0
    try:
        for goal_data in SDG_GOAL_DATA:
            existing_goal = SdgGoal.query.filter_by(number=goal_data['number']).first()
            if not existing_goal:
                new_goal = SdgGoal(
                    number=goal_data['number'],
                    name=goal_data['name'],
                    color_code=goal_data['color_code'],
                    description=goal_data.get('description', '')
                )
                db.session.add(new_goal)
                added_count += 1
                print(f"  Adding SDG {goal_data['number']}...")
        if added_count > 0:
            db.session.commit()
            print(f"Successfully added {added_count} SDG goals.")
        else:
            print("All SDG goals (1-17) already exist.")
    except Exception as e:
        db.session.rollback()
        print(f"ERROR populating sdg_goals: {e}")
