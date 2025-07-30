from datetime import date
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import httpx

class DateRange(BaseModel):
    """Represents a date range with start and end dates."""
    start: date
    end: date

class KimbleClient:
    """Client for interacting with the Kimble API."""
    
    def __init__(self, base_url: str, api_key: str):
        """Initialize the Kimble client.
        
        Args:
            base_url: Base URL of the Kimble API
            api_key: API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            timeout=30.0
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def fill_absence(self, user_id: int, absence_date: date, reason: str) -> Dict[str, Any]:
        """Fill an absence for a user.
        
        Args:
            user_id: ID of the user
            absence_date: Date of the absence
            reason: Reason for absence (e.g., 'SICK', 'VAC')
            
        Returns:
            Response from the Kimble API
        """
        data = {
            'userId': user_id,
            'date': absence_date.isoformat(),
            'reason': reason,
            'status': 'PENDING_APPROVAL'
        }
        
        response = await self.client.post(
            '/api/v1/absences',
            json=data
        )
        response.raise_for_status()
        return response.json()

    async def submit_week(self, user_id: int, week_no: int) -> Dict[str, Any]:
        """Submit a week for approval.

        Args:
            user_id: ID of the user
            week_no: Week number to submit

        Returns:
            Response from the Kimble API
        """
        response = await self.client.post(
            f'/api/v1/users/{user_id}/timesheets/submit',
            json={'weekNumber': week_no}
        )
        response.raise_for_status()
        return response.json()

    async def get_absences(self, user_id: int, date_range: DateRange) -> List[Dict[str, Any]]:
        """Get absences for a user within a date range.
        
        Args:
            user_id: ID of the user
            date_range: Date range to search for absences
            
        Returns:
            List of absence records
        """
        params = {
            'userId': str(user_id),
            'startDate': date_range.start.isoformat(),
            'endDate': date_range.end.isoformat()
        }
        
        response = await self.client.get(
            '/api/v1/absences',
            params=params
        )
        response.raise_for_status()
        return response.json()

    async def count_absences(self, user_id: int, date_range: DateRange) -> int:
        """Count absences for a user within a date range.
        
        Args:
            user_id: ID of the user
            date_range: Date range to count absences for
            
        Returns:
            Number of absences
        """
        absences = await self.get_absences(user_id, date_range)
        return len(absences)

    async def is_absent(self, user_id: int, check_date: date) -> bool:
        """Check if a user is absent on a specific date.
        
        Args:
            user_id: ID of the user
            check_date: Date to check for absence
            
        Returns:
            True if user is absent, False otherwise
        """
        date_range = DateRange(start=check_date, end=check_date)
        absences = await self.get_absences(user_id, date_range)
        return len(absences) > 0
