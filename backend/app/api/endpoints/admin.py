from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from ...core.database import get_db
from ...services.admin_service import AdminService
from ...schemas.user import UserResponse
from ...schemas.league import LeagueResponse
from ..deps import get_current_admin_user, get_current_superadmin_user

router = APIRouter(tags=["admin"])

@router.get(
    "/users/",
    response_model=List[UserResponse],
    summary="Get all users",
    description="Returns a list of all users with pagination. Admin access required."
)
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users with pagination.
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        List[UserResponse]: List of users
    """
    admin_service = AdminService(db)
    return await admin_service.get_all_users(skip, limit)

@router.put(
    "/users/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Update user role",
    description="Update a user's admin status. Admin access required. Superadmin access required to grant superadmin privileges."
)
async def update_user_role(
    user_id: int,
    is_admin: bool,
    is_superadmin: bool = False,
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a user's admin status.
    
    Args:
        user_id: ID of the user to update
        is_admin: New admin status
        is_superadmin: New superadmin status (requires superadmin privileges)
        current_admin: Current authenticated admin user
        db: Database session
        
    Raises:
        HTTPException: If user not found or insufficient privileges
    """
    # Only superadmins can grant superadmin privileges
    if is_superadmin and not current_admin.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin privileges required to grant superadmin status"
        )
    
    admin_service = AdminService(db)
    if not await admin_service.update_user_role(user_id, is_admin, is_superadmin):
        raise HTTPException(status_code=404, detail="User not found")

@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user and all associated data. Admin access required."
)
async def delete_user(
    user_id: int,
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a user and all associated data.
    
    Args:
        user_id: ID of the user to delete
        current_admin: Current authenticated admin user
        db: Database session
        
    Raises:
        HTTPException: If user not found
    """
    # Prevent admins from deleting themselves
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Only superadmins can delete other admins
    if not current_admin.is_superadmin:
        # Check if target user is an admin
        admin_service = AdminService(db)
        target_user = await admin_service.get_user_by_id(user_id)
        if target_user:
            # Get is_admin as a regular boolean
            is_admin_value = getattr(target_user, 'is_admin')
            if hasattr(is_admin_value, 'scalar'):
                is_admin_value = is_admin_value.scalar()
            
            if is_admin_value:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Superadmin privileges required to delete admin users"
                )
    
    admin_service = AdminService(db)
    if not await admin_service.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")

@router.get(
    "/leagues/",
    response_model=List[LeagueResponse],
    summary="Get all leagues",
    description="Returns a list of all leagues with pagination. Admin access required."
)
async def get_all_leagues(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all leagues with pagination.
    
    Args:
        skip: Number of leagues to skip
        limit: Maximum number of leagues to return
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        List[LeagueResponse]: List of leagues
    """
    admin_service = AdminService(db)
    return await admin_service.get_all_leagues(skip, limit)

@router.delete(
    "/leagues/{league_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete league",
    description="Delete a league. Admin access required."
)
async def delete_league(
    league_id: int,
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a league.
    
    Args:
        league_id: ID of the league to delete
        current_admin: Current authenticated admin user
        db: Database session
        
    Raises:
        HTTPException: If league not found
    """
    admin_service = AdminService(db)
    if not await admin_service.delete_league(league_id):
        raise HTTPException(status_code=404, detail="League not found")

@router.get(
    "/system/stats",
    response_model=Dict[str, Any],
    summary="Get system statistics",
    description="Returns system statistics including database size, user count, etc. Admin access required."
)
async def get_system_stats(
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system statistics.
    
    Args:
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dict[str, Any]: System statistics
    """
    admin_service = AdminService(db)
    return await admin_service.get_system_stats()

@router.post(
    "/system/maintenance",
    response_model=Dict[str, Any],
    summary="Run database maintenance",
    description="Run database maintenance tasks including VACUUM and integrity check. Admin access required."
)
async def run_database_maintenance(
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Run database maintenance tasks.
    
    Args:
        current_admin: Current authenticated admin user
        db: Database session
        
    Returns:
        Dict[str, Any]: Maintenance results
    """
    admin_service = AdminService(db)
    return await admin_service.run_database_maintenance()

@router.put(
    "/data/race-results/{race_result_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Correct race result",
    description="Correct a race result and recalculate affected scores. Admin access required."
)
async def correct_race_result(
    race_result_id: int,
    position: int,
    driver_number: int,
    current_admin: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Correct a race result and recalculate affected scores.
    
    Args:
        race_result_id: ID of the race result to correct
        position: New position
        driver_number: New driver number
        current_admin: Current authenticated admin user
        db: Database session
        
    Raises:
        HTTPException: If race result not found
    """
    admin_service = AdminService(db)
    if not await admin_service.correct_race_result(race_result_id, position, driver_number):
        raise HTTPException(status_code=404, detail="Race result not found") 