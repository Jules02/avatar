import os
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from fuzzywuzzy import process
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, field_validator, ValidationError as PydanticValidationError
from fastapi import HTTPException
from loguru import logger

# Import custom exceptions and Kimble client
from exceptions import (
    ServiceError, ValidationError, KimbleError,
    handle_error
)
from clients.kimble import DateRange
from clients.kimble import KimbleClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config(BaseModel):
    """Configuration for the Kimble MCP server."""
    #KIMBLE_BASE_URL: str = os.getenv("KIMBLE_BASE_URL", "https://api.kimble.example.com")
    #KIMBLE_API_KEY: str = os.getenv("KIMBLE_API_KEY", "")
    #
    # @field_validator('KIMBLE_BASE_URL')
    # @classmethod
    # def validate_base_url(cls, v: str) -> str:
    #     if not v:
    #         raise ValueError("KIMBLE_BASE_URL must be set")
    #     if not v.startswith(('http://', 'https://')):
    #         raise ValueError("KIMBLE_BASE_URL must start with http:// or https://")
    #     return v
    #
    # @field_validator('KIMBLE_API_KEY')
    # @classmethod
    # def validate_api_key(cls, v: str) -> str:
    #     if not v:
    #         raise ValueError("KIMBLE_API_KEY must be set")
    #     return v
    
    class Config:
        env_file = ".env"
        extra = "forbid"

# Initialize FastMCP
mcp = FastMCP("workforce")

# Initialize configuration
try:
    config = Config()
except PydanticValidationError as e:
    logger.critical(f"Configuration error: {e}")
    raise

try:
    # Initialize Kimble client
    kimble_client = KimbleClient()
    logger.info("Kimble client initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize Kimble client: {e}")
    raise

@mcp.tool()
async def fill_absence(user_id: str, absence_date: str) -> Dict[str, Any]:
    """
    Fill an absence for a given date on the Kimble database.

    Args:
        user_id: The UUID of the user
        absence_date: The date of the absence in YYYY-MM-DD format

    Returns:
        Dict containing the result of the operation
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
            
        try:
            absence_date_obj = datetime.strptime(absence_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format. Expected YYYY-MM-DD: {e}")

        # Call Kimble client
        result = await kimble_client.fill_absence(
            user_id=user_id,
            absence_date=absence_date_obj
        )
        
        logger.info(f"Successfully filled absence for user {user_id} on {absence_date}")
        return {"status": "success", "data": result}
        
    except ValidationError as e:
        logger.warning(f"Validation error in kimble_fill_absence: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in kimble_fill_absence: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in kimble_fill_absence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@mcp.tool()
async def get_week_absences(user_id: str, year: int, week_no: int) -> Dict[str, Any]:
    """
    Get all absences for a specific week.

    Args:
        user_id: The UUID of the user
        year: The year (e.g., 2025)
        week_no: The ISO week number (1-53)

    Returns:
        Dict containing the list of absences for the specified week
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
        if not isinstance(week_no, int) or not (1 <= week_no <= 53):
            raise ValidationError("Week number must be between 1 and 53")
            
        # Calculate start and end of the ISO week
        # Using isocalendar() for proper ISO week handling
        first_day = datetime.strptime(f"{year}-{week_no}-1", "%G-%V-%u").date()
        last_day = first_day + timedelta(days=6)

        date_range_obj = DateRange(start=first_day, end=last_day)
        
        # Get absences for the week
        absences = await kimble_client.get_absences(
            user_id=user_id,
            date_range=date_range_obj,
        )
        
        return {
            "status": "success",
            "data": {
                "year": year,
                "week_no": week_no,
                "start_date": first_day.isoformat(),
                "end_date": last_day.isoformat(),
                "absences": absences
            }
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error in get_week_absences: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in get_week_absences: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in get_week_absences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@mcp.tool()
async def submit_week(user_id: str, year: int, week_no: int, confirmed: bool = False) -> Dict[str, Any]:
    """
    Submit a week to the Kimble database, sending an email to the manager for approval.
    
    This will first check for any absences in the specified week and require confirmation
    before proceeding with the submission.

    Args:
        user_id: The UUID of the user
        year: The year (e.g., 2025)
        week_no: The ISO week number (1-53)
        confirmed: Whether the user has confirmed the submission after reviewing absences

    Returns:
        Dict containing the result of the operation or the list of absences for review
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
        if not isinstance(week_no, int) or not (1 <= week_no <= 53):
            raise ValidationError("Week number must be between 1 and 53")
            
        # First, get absences for the week
        week_data = await get_week_absences(user_id, year, week_no)
        absences = week_data["data"]["absences"]
        
        # If there are absences and not confirmed, return them for review
        if absences and not confirmed:
            return {
                "status": "review_required",
                "message": "Please review the following absences before submission",
                "data": week_data["data"],
                "confirmation_required": True
            }
        
        # If confirmed or no absences, proceed with submission
        result = await kimble_client.submit_week(
            user_id=user_id,
            week_no=week_no
        )
        
        logger.info(f"Successfully submitted week {week_no} for user {user_id}")
        return {
            "status": "success",
            "message": "Week submitted successfully",
            "data": result
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error in kimble_submit_week: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in kimble_submit_week: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in kimble_submit_week: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@mcp.tool()
async def is_absent(user_id: str, date: str) -> Dict[str, Any]:
    """
    Check if a user is absent on a given date.

    Args:
        user_id: The UUID of the user
        date: The date to check in YYYY-MM-DD format

    Returns:
        Dict containing the absence status and details if any
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
            
        try:
            check_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format. Expected YYYY-MM-DD: {e}")
        
        # Call Kimble client
        absence_info = await kimble_client.is_absent(user_id, check_date)
        
        response = {
            "status": "success",
            "data": {
                "user_id": user_id,
                "date": date,
                "is_absent": absence_info
            }
        }
        
        # Add absence details if user is absent
        if absence_info:
            response["data"].update({
                "absence_id": absence_info.get("absence_id"),
                "justified": absence_info.get("justified", False),
                "created_at": absence_info.get("created_at")
            })
        
        logger.info(f"Checked absence for user {user_id} on {date}: {response}")
        return response
        
    except ValidationError as e:
        logger.warning(f"Validation error in kimble_is_absent: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in kimble_is_absent: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in kimble_is_absent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@mcp.tool()
async def get_absences(user_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Get all absences for a given user within a specified date range.

    Args:
        user_id: The UUID of the user
        date_range: A dictionary with 'start' and 'end' dates in YYYY-MM-DD format

    Returns:
        Dict containing the list of absences and metadata
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
            
        if not isinstance(date_range, dict) or 'start' not in date_range or 'end' not in date_range:
            raise ValidationError("date_range must be a dictionary with 'start' and 'end' dates")
            
        try:
            start_date = datetime.strptime(date_range['start'], "%Y-%m-%d").date()
            end_date = datetime.strptime(date_range['end'], "%Y-%m-%d").date()
            
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")
                
        except ValueError as e:
            raise ValidationError(f"Invalid date format. Expected YYYY-MM-DD: {e}")
        
        # Create date range object
        date_range_obj = DateRange(start=start_date, end=end_date)
        
        # Call Kimble client
        absences = await kimble_client.get_absences(user_id, date_range_obj)
        
        logger.info(f"Retrieved {len(absences)} absences for user {user_id} between {start_date} and {end_date}")
        
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "absences": absences,
                "count": len(absences)
            }
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error in get_absences: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in get_absences: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in get_absences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@mcp.tool()
async def count_absences(user_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Count all absences for a given user within a specified date range.

    Args:
        user_id: The UUID of the user
        date_range: A dictionary with 'start' and 'end' dates in YYYY-MM-DD format

    Returns:
        Dict containing the count of absences and metadata
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
        # Input validation
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("User ID must be a valid UUID string")
            
        if not isinstance(date_range, dict) or 'start' not in date_range or 'end' not in date_range:
            raise ValidationError("date_range must be a dictionary with 'start' and 'end' dates")
            
        try:
            start_date = datetime.strptime(date_range['start'], "%Y-%m-%d").date()
            end_date = datetime.strptime(date_range['end'], "%Y-%m-%d").date()
            
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")
                
            # Validate date range is not too large (e.g., max 1 year)
            if (end_date - start_date).days > 365:
                raise ValidationError("Date range cannot exceed 1 year")
                
        except ValueError as e:
            raise ValidationError(f"Invalid date format. Expected YYYY-MM-DD: {e}")

        date_range_obj = DateRange(start=start_date, end=end_date)
        
        # Call Kimble client to count absences
        counts = await kimble_client.count_absences(user_id, date_range_obj)
        
        logger.info(
            f"Counted {counts['total']} absences for user {user_id} "
            f"between {start_date} and {end_date}"
        )
        
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                },
                "total_absences": counts["total"],
                "justified": counts["justified"],
                "unjustified": counts["unjustified"]
            }
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error in count_absences: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in count_absences: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in count_absences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    # List of available tools to expose
    available_tools = [
        fill_absence,
        get_week_absences,
        submit_week,
        is_absent,
        get_absences,
        count_absences
    ]
    
    # Run the MCP server
    mcp.run(transport='stdio')
