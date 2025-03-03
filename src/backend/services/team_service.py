from backend.database import db  # Replace with your actual DB setup
from routes import user_to_team  # Replace with your actual models

def invite_user_to_team(inviter_id, invitee_id, team_id, role="member"):
    """Invites a user to join a team."""
    existing_invite = user_to_team.query.filter_by(user_id=invitee_id, team_id=team_id).first()
    if existing_invite:
        return {"success": False, "message": "User already invited or a member."}

    new_invite = user_to_team(user_id=invitee_id, team_id=team_id, role=role, invited=True)
    db.session.add(new_invite)
    db.session.commit()
    return {"success": True, "message": "Invitation sent!"}

def accept_invite(user_id, team_id):
    """Accepts a team invitation."""
    invite = user_to_team.query.filter_by(user_id=user_id, team_id=team_id, invited=True).first()
    if not invite:
        return {"success": False, "message": "No pending invite found."}

    invite.invited = False  # Mark as accepted
    db.session.commit()
    return {"success": True, "message": "User has joined the team!"}

def user_has_access(user_id, team_id):
    """Checks if a user has access to a team."""
    membership = user_to_team.query.filter_by(user_id=user_id, team_id=team_id, invited=False).first()
    return membership is not None  # True if user has accepted the invite
