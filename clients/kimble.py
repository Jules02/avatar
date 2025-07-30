from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel
import httpx
import random
from uuid import uuid4

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
        """Fill an absence for a user (fake implementation).
        
        Args:
            user_id: ID of the user
            absence_date: Date of the absence
            reason: Reason for absence (e.g., 'SICK', 'VAC')
            
        Returns:
            Fake response with absence details
        """
        return {
            'id': str(uuid4()),
            'userId': user_id,
            'date': absence_date.isoformat(),
            'reason': reason,
            'status': 'PENDING_APPROVAL',
            'submittedAt': date.today().isoformat(),
            'message': 'Absence request submitted successfully (FAKE DATA)'
        }

    async def submit_week(self, user_id: int, week_no: int) -> Dict[str, Any]:
        """Submit a week for approval (fake implementation).

        Args:
            user_id: ID of the user
            week_no: Week number to submit

        Returns:
            Fake response with submission details
        """
        return {
            'success': True,
            'userId': user_id,
            'weekNumber': week_no,
            'submissionDate': date.today().isoformat(),
            'status': 'SUBMITTED',
            'message': f'Week {week_no} submitted for approval (FAKE DATA)'
        }

    async def get_absences(self, user_id: int, date_range: DateRange) -> List[Dict[str, Any]]:
        """Get absences for a user within a date range (fake implementation).
        
        Args:
            user_id: ID of the user
            date_range: Date range to search for absences
            
        Returns:
            List of fake absence records
        """
        # Generate some random absences for testing
        absences = []
        current_date = date_range.start
        delta = date_range.end - date_range.start
        
        # Generate 0-3 random absences in the date range
        for _ in range(random.randint(0, 3)):
            # Pick a random date in the range
            days_offset = random.randint(0, delta.days)
            absence_date = date_range.start + timedelta(days=days_offset)
            reason = random.choice(['SICK', 'VAC', 'OTHER'])
            
            absences.append({
                'id': str(uuid4()),
                'userId': user_id,
                'date': absence_date.isoformat(),
                'reason': reason,
                'status': random.choice(['APPROVED', 'PENDING_APPROVAL', 'REJECTED']),
                'createdAt': (absence_date - timedelta(days=1)).isoformat()
            })
            
        return absences

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
        """Check if a user is absent on a specific date (fake implementation).
        
        Args:
            user_id: ID of the user
            check_date: Date to check for absence
            
        Returns:
            bool: True if user is absent, False otherwise (randomly generated)
        """
        # 20% chance of being absent on any given day
        return random.random() < 0.2
