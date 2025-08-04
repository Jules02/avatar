import os
import logging
from datetime import date, datetime
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
from clients.kimble import KimbleClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config(BaseModel):
    """Configuration for the Kimble MCP server."""
    KIMBLE_BASE_URL: str = os.getenv("KIMBLE_BASE_URL", "https://api.kimble.example.com")
    KIMBLE_API_KEY: str = os.getenv("KIMBLE_API_KEY", "")
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
async def kimble_fill_absence(user_id: str, absence_date: str, reason: str) -> Dict[str, Any]:
    """
    Fill an absence for a given date and reason on the Kimble database.

    Args:
        user_id: The UUID of the user
        absence_date: The date of the absence in YYYY-MM-DD format
        reason: The reason for the absence (sick, unjustified, remote_not_logged, etc.)

    Returns:
        Dict containing the result of the operation
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
        # Input validation
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("User ID must be a valid UUID string")
            
        try:
            absence_date_obj = datetime.strptime(absence_date, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValidationError(f"Invalid date format. Expected YYYY-MM-DD: {e}")
            
        # Define possible reasons and their variations
        REASON_MAPPING = {
            'sick': ['sick', 'ill', 'unwell', 'not feeling well', 'under the weather'],
            'unjustified': ['unjustified', 'no reason', 'no show', 'absent without notice'],
            'remote_not_logged': ['remote not logged', 'forgot to log', 'missed logging']
        }
        
        # Flatten the mapping for fuzzy matching
        all_reasons = []
        for main_reason, variations in REASON_MAPPING.items():
            all_reasons.extend([(v, main_reason) for v in [main_reason] + variations])
        
        # Use fuzzy matching to find the best match
        reason_lower = reason.lower()
        best_match, score = process.extractOne(reason_lower, [r[0] for r in all_reasons])
        
        # If we have a good match (score > 70), use the mapped reason
        if score > 70:
            reason = next((r[1] for r in all_reasons if r[0] == best_match), 'unjustified')
        else:
            # If no good match, default to 'unjustified' but log the original reason
            original_reason = reason
            reason = 'unjustified'
            logger.info(f"No good match for reason '{original_reason}'. Defaulting to 'unjustified'")
        
        # Call Kimble client
        result = await kimble_client.fill_absence(
            user_id=user_id,
            absence_date=absence_date_obj,
            reason=reason
        )
        
        logger.info(f"Successfully filled absence for user {user_id} on {absence_date} with reason: {reason}")
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
async def kimble_submit_week(user_id: int, week_no: int) -> Dict[str, Any]:
    """
    Submit a week to the Kimble database, sending an email to the manager for approval.

    Args:
        user_id: The ID of the user (must be positive integer)
        week_no: The number of the week to submit (1-53)

    Returns:
        Dict containing the result of the operation
        
    Raises:
        HTTPException: With status code 400 for validation errors or 500 for server errors
    """
    try:
        # Input validation
        #if not isinstance(user_id, int) or user_id <= 0:
        #   raise ValidationError("User ID must be a positive integer")
            
        if not isinstance(week_no, int) or not (1 <= week_no <= 53):
            raise ValidationError("Week number must be between 1 and 53")
        
        # Call Kimble client
        result = await kimble_client.submit_week(
            user_id=user_id,
            week_no=week_no
        )
        
        logger.info(f"Successfully submitted week {week_no} for user {user_id}")
        return {"status": "success", "data": result}
        
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
async def kimble_is_absent(user_id: str, date: str) -> Dict[str, Any]:
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
        # Input validation
        if not user_id or not isinstance(user_id, str):
            raise ValidationError("User ID must be a valid UUID string")
            
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
                "reason": absence_info.get("reason"),
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
async def kimble_get_absences(user_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
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
        
        # Create date range object
        date_range_obj = KimbleDateRange(start=start_date, end=end_date)
        
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
        logger.warning(f"Validation error in kimble_get_absences: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in kimble_get_absences: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in kimble_get_absences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@mcp.tool()
async def kimble_count_absences(user_id: str, date_range: Dict[str, str]) -> Dict[str, Any]:
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
        
        # Create date range object
        date_range_obj = KimbleDateRange(start=start_date, end=end_date)
        
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
                "by_reason": counts["by_reason"],
                "justified": counts["justified"],
                "unjustified": counts["unjustified"]
            }
        }
        
    except ValidationError as e:
        logger.warning(f"Validation error in kimble_count_absences: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except KimbleError as e:
        logger.error(f"Kimble service error in kimble_count_absences: {e}")
        raise HTTPException(status_code=502, detail=f"Kimble service error: {e}")
        
    except Exception as e:
        logger.error(f"Unexpected error in kimble_count_absences: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    # List of available tools to expose
    available_tools = [
        kimble_fill_absence,
        kimble_submit_week,
        kimble_is_absent,
        kimble_get_absences,
        kimble_count_absences
    ]
    
    # Run the MCP server
    mcp.run(transport='stdio')
