def initialize_services():
    """Initialize services and resolve circular dependencies."""
    from backend.services.authService import AuthService
    from backend.services.teamService import TeamService
    from backend.services.accountService import AccountService
    
    auth_service = AuthService()
    team_service = TeamService()
    account_service = AccountService()
    
    # Resolve circular dependency
    account_service.set_team_service(team_service)
    
    return auth_service, team_service, account_service