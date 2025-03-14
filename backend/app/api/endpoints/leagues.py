from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from ...core.database import get_db
from ...services.league_service import LeagueService
from ...api.endpoints.auth import get_current_user
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
):
    """
    Get current standings for a league.
    
    Args:
        league_id: ID of the league to get standings for
        current_user: Authenticated user
        db: Database session
        
    Returns:
        LeagueStandingsResponse: Current league standings
        
    Raises:
        HTTPException: If league not found
    """
    league_service = LeagueService(db)
    return await league_service.get_standings(league_id)

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
    db: AsyncSession = Depends(get_db)
):
    """
    Add a user as a member to a league.
    
    Args:
        league_id: ID of the league to add member to
        user_id: ID of the user to add
        current_user: Authenticated user
        db: Database session
        
    Raises:
        HTTPException: If league or user not found, or if user already a member
    """
    league_service = LeagueService(db)
    if not await league_service.add_member(league_id, user_id):
        raise HTTPException(status_code=400, detail="Could not add member")

@router.delete(
    "/{league_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member from league",
    description="Remove a user from a league. Only the league owner can remove members."
)
async def remove_member(
    league_id: int,
    user_id: int,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a member from a league. Only the league owner can do this.
    
    Args:
        league_id: ID of the league to remove member from
        user_id: ID of the user to remove
        current_user: Authenticated user (must be league owner)
        db: Database session
        
    Raises:
        HTTPException: If league not found, user not found, or current user not owner
    """
    league_service = LeagueService(db)
    if not await league_service.remove_member(league_id, user_id, current_user.id):
        raise HTTPException(status_code=400, detail="Could not remove member") 