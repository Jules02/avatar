import os
import logging
from datetime import date, datetime
from typing import Any, Dict, List, Optional
import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import Kimble client
from clients.kimble import KimbleClient, DateRange as KimbleDateRange

class Config(BaseModel):
    """Configuration for the Kimble MCP server."""
    KIMBLE_BASE_URL: str = os.getenv("KIMBLE_BASE_URL", "https://api.kimble.example.com")
    KIMBLE_API_KEY: str = os.getenv("KIMBLE_API_KEY", "")
    
    class Config:
        env_file = ".env"

# Initialize FastMCP
mcp = FastMCP("workforce")

# Initialize configuration
config = Config()

# Initialize Kimble client
kimble_client = KimbleClient(
    base_url=config.KIMBLE_BASE_URL,
    api_key=config.KIMBLE_API_KEY
)

@mcp.tool()
async def kimble_fill_absence(user_id: int, absence_date: str, reason: str) -> Dict[str, Any]:
    """
    Fill an absence for a given date and reason on the Kimble database.

    Args:
        user_id: The ID of the user
        absence_date: The date of the absence in YYYY-MM-DD format
        reason: The reason for the absence (SICK, VAC, etc.)

    Returns:
        Dict containing the result of the operation
    """
    try:
        absence_date = datetime.strptime(absence_date, "%Y-%m-%d").date()
        result = await kimble_client.fill_absence(user_id, absence_date, reason)
        return {"status": "success", "data": result}
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return {"status": "error", "message": f"Invalid date format: {e}"}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        return {"status": "error", "message": f"HTTP error: {e.response.text}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

@mcp.tool()
async def kimble_submit_week(user_id: int, week_no: int) -> Dict[str, Any]:
    """
    Submit a week to the Kimble database, sending an email to the manager for approval.

    Args:
        user_id: The ID of the user
        week_no: The number of the week to submit (1-53)

    Returns:
        Dict containing the result of the operation
    """
    try:
        if not 1 <= week_no <= 53:
            raise ValueError("Week number must be between 1 and 53")
            
        result = await kimble_client.submit_week(user_id, week_no)
        return {"status": "success", "data": result}
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return {"status": "error", "message": str(e)}
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error occurred: {e}")
        return {"status": "error", "message": f"HTTP error: {e.response.text}"}
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

@mcp.tool()
async def kimble_is_absent(user_id: int, date: str) -> Dict[str, Any]:
    """
    Check if a user is absent on a given date.

    Args:
        user_id: The ID of the user
        date: The date to check in YYYY-MM-DD format

    Returns:
        Dict containing the absence status and details if any
    """
    try:
        check_date = datetime.strptime(date, "%Y-%m-%d").date()
        is_absent = await kimble_client.is_absent(user_id, check_date)
        return {
            "status": "success",
            "data": {
                "is_absent": is_absent,
                "user_id": user_id,
                "date": date
            }
        }
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return {"status": "error", "message": f"Invalid date format: {e}"}
    except Exception as e:
        logger.error(f"Error checking absence: {e}", exc_info=True)
        return {"status": "error", "message": f"Error checking absence: {str(e)}"}

@mcp.tool()
async def kimble_get_absences(user_id: int, date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Get all absences for a given user within a specified date range.

    Args:
        user_id: The ID of the user
        date_range: A dictionary with 'start' and 'end' dates in YYYY-MM-DD format

    Returns:
        Dict containing the list of absences and metadata
    """
    try:
        start_date = datetime.strptime(date_range['start'], "%Y-%m-%d").date()
        end_date = datetime.strptime(date_range['end'], "%Y-%m-%d").date()
        
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")
            
        date_range_obj = KimbleDateRange(start=start_date, end=end_date)
        absences = await kimble_client.get_absences(user_id, date_range_obj)
        
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "absences": absences,
                "count": len(absences)
            }
        }
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        return {"status": "error", "message": f"Missing required field: {e}"}
    except ValueError as e:
        logger.error(f"Invalid date format or range: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Error retrieving absences: {e}", exc_info=True)
        return {"status": "error", "message": f"Error retrieving absences: {str(e)}"}

@mcp.tool()
async def kimble_count_absences(user_id: int, date_range: Dict[str, str]) -> Dict[str, Any]:
    """
    Count all absences for a given user within a specified date range.

    Args:
        user_id: The ID of the user
        date_range: A dictionary with 'start' and 'end' dates in YYYY-MM-DD format

    Returns:
        Dict containing the count of absences and metadata
    """
    try:
        start_date = datetime.strptime(date_range['start'], "%Y-%m-%d").date()
        end_date = datetime.strptime(date_range['end'], "%Y-%m-%d").date()
        
        if start_date > end_date:
            raise ValueError("Start date must be before or equal to end date")
            
        date_range_obj = KimbleDateRange(start=start_date, end=end_date)
        count = await kimble_client.count_absences(user_id, date_range_obj)
        
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "date_range": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "count": count
            }
        }
    except KeyError as e:
        logger.error(f"Missing required field: {e}")
        return {"status": "error", "message": f"Missing required field: {e}"}
    except ValueError as e:
        logger.error(f"Invalid date format or range: {e}")
        return {"status": "error", "message": str(e)}
    except Exception as e:
        logger.error(f"Error counting absences: {e}", exc_info=True)
        return {"status": "error", "message": f"Error counting absences: {str(e)}"}

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
