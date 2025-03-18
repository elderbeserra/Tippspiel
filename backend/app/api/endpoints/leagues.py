from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ...core.database import get_db
from ...services.league_service import LeagueService
from ...api.endpoints.auth import get_current_user
from ...api.deps import get_league_admin, get_current_superadmin_user
from ...schemas.league import (
    LeagueCreate,
    LeagueResponse,
    LeagueStandingsResponse
)
from ...schemas.user import UserResponse

router = APIRouter(tags=["leagues"])

@router.post(
    "",
    response_model=LeagueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new league",
    description="""
    Create a new private league with the following information:
    - Name (must be unique, 3-50 characters)
    - Optional icon (base64 encoded image)
    
    The authenticated user will automatically become the league owner and first member.
    """
)
async def create_league(
    league: LeagueCreate,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new league and set the current user as owner.
    
    Args:
        league: League creation data including name and optional icon
        current_user: Authenticated user who will own the league
        db: Database session
        
    Returns:
        LeagueResponse: Created league information
        
    Raises:
        HTTPException: If league name already exists
    """
    league_service = LeagueService(db)
    return await league_service.create_league(league, current_user.id)

@router.get(
    "/my",
    response_model=List[LeagueResponse],
    summary="Get user's leagues",
    description="Returns all leagues where the authenticated user is a member."
)
async def get_my_leagues(
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all leagues for the authenticated user.
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List[LeagueResponse]: List of leagues the user is a member of
    """
    league_service = LeagueService(db)
    return await league_service.get_user_leagues(current_user.id)

@router.get(
    "/{league_id}",
    response_model=LeagueResponse,
    summary="Get league details",
    description="Returns detailed information about a specific league."
)
async def get_league(
    league_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific league.
    
    Args:
        league_id: ID of the league to retrieve
        current_user: Authenticated user
        db: Database session
        
    Returns:
        LeagueResponse: League information
        
    Raises:
        HTTPException: If league not found
    """
    league_service = LeagueService(db)
    league = await league_service.get_league(league_id)
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    return league

@router.get(
    "/{league_id}/standings",
    response_model=LeagueStandingsResponse,
    summary="Get league standings",
    description="""
    Returns current standings for a league, including:
    - Total points per member
    - Position in league
    - Number of predictions made
    - Number of perfect predictions
    """
)
async def get_league_standings(
    league_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current standings for a league.
    
    Args:
        league_id: ID of the league to get standings for
        current_user: Authenticated user
        db: Database session
        
    Returns:
        LeagueStandingsResponse: League standings information
        
    Raises:
        HTTPException: If league not found
    """
    league_service = LeagueService(db)
    try:
        return await league_service.get_standings(league_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post(
    "/{league_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Add member to league",
    description="Add a user to a league. The user must exist in the system."
)
async def add_member(
    league_id: int,
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add a user to a league.
    
    Args:
        league_id: ID of the league to add the user to
        user_id: ID of the user to add
        current_user: Authenticated user (must be league admin)
        db: Database session
        
    Raises:
        HTTPException: If league or user not found, or current user not owner
    """
    # Check if user is league admin
    league_admin = get_league_admin(league_id)
    await league_admin(current_user=current_user, db=db)
    
    league_service = LeagueService(db)
    if not await league_service.add_member(league_id, user_id):
        raise HTTPException(status_code=404, detail="League or user not found")

@router.delete(
    "/{league_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from league",
    description="Remove a user from a league. Only the league admin (owner) can remove members."
)
async def remove_member(
    league_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Remove a user from a league.
    
    Args:
        league_id: ID of the league to remove the user from
        user_id: ID of the user to remove
        current_user: Authenticated user (must be league admin)
        db: Database session
        
    Raises:
        HTTPException: If league or user not found, or current user not owner
    """
    league_service = LeagueService(db)
    if not await league_service.remove_member(league_id, user_id, current_user.id):
        raise HTTPException(
            status_code=404,
            detail="League or user not found, or you don't have permission to remove this member"
        )

@router.delete(
    "/{league_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete league",
    description="Delete a league. Only the league admin (owner) can delete the league."
)
async def delete_league(
    league_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Delete a league. Only the league admin (owner) can do this.
    
    Args:
        league_id: ID of the league to delete
        current_user: Authenticated user (must be league admin)
        db: Database session
        
    Raises:
        HTTPException: If league not found or current user not owner
    """
    # Check if user is league admin
    from sqlalchemy import select
    from ...models.league import League
    
    # Superadmins can perform any league admin action
    if current_user.is_superadmin:
        pass  # Allow superadmins to proceed
    else:
        # Check if the user is the league owner
        query = select(League).where(League.id == league_id)
        result = db.execute(query)
        league = result.scalar_one_or_none()
        
        if not league:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="League not found",
            )
        
        # Get the owner_id as a regular integer
        owner_id = getattr(league, 'owner_id')
        if hasattr(owner_id, 'scalar'):
            owner_id = owner_id.scalar()
        
        if owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be the league admin to perform this action",
            )
    
    league_service = LeagueService(db)
    if not await league_service.delete_league(league_id):
        raise HTTPException(status_code=404, detail="League not found")

@router.put(
    "/{league_id}/transfer-ownership/{new_owner_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Transfer league ownership",
    description="Transfer league ownership to another member. Only the league admin (owner) can transfer ownership."
)
async def transfer_ownership(
    league_id: int,
    new_owner_id: int,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """
    Transfer league ownership to another member.
    
    Args:
        league_id: ID of the league to transfer ownership of
        new_owner_id: ID of the user to transfer ownership to
        current_user: Authenticated user (must be league admin)
        db: Database session
        
    Raises:
        HTTPException: If league not found, new owner not found, or current user not owner
    """
    # Check if user is league admin
    league_admin = get_league_admin(league_id)
    await league_admin(current_user=current_user, db=db)
    
    league_service = LeagueService(db)
    if not await league_service.transfer_ownership(league_id, new_owner_id):
        raise HTTPException(
            status_code=404,
            detail="League not found, or new owner is not a member of the league"
        ) 