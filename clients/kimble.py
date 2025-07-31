from datetime import date, timedelta, datetime
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, field_validator, ValidationError
import httpx
import random
import logging
from uuid import uuid4

from ..exceptions import KimbleError, ValidationError as AvatarValidationError, handle_error

logger = logging.getLogger(__name__)

class DateRange(BaseModel):
    """Represents a date range with start and end dates."""
    start: date
    end: date
    
    @field_validator('start', 'end')
    @classmethod
    def validate_date_not_in_future(cls, v: date) -> date:
        if v > date.today():
            raise ValueError(f"Date {v} cannot be in the future")
        return v
        
    @field_validator('end')
    @classmethod
    def validate_date_range(cls, v: date, values) -> date:
        if 'start' in values and v < values['start']:
            raise ValueError("End date cannot be before start date")
        return v

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
            Dict: Response with absence details
            
        Raises:
            KimbleError: If there's an error creating the absence
            ValidationError: If the input validation fails
        """
        try:
            # Validate inputs
            if not isinstance(user_id, int) or user_id <= 0:
                raise AvatarValidationError("User ID must be a positive integer")
                
            if not isinstance(absence_date, date):
                raise AvatarValidationError("Invalid date format")
                
            if reason not in ['SICK', 'VAC', 'OTHER']:
                raise AvatarValidationError("Reason must be one of: 'SICK', 'VAC', 'OTHER'")
                
            # Simulate a potential error (10% chance)
            if random.random() < 0.1:
                raise KimbleError("Failed to create absence: Service unavailable")
                
            return {
                'id': str(uuid4()),
                'userId': user_id,
                'date': absence_date.isoformat(),
                'reason': reason,
                'status': 'PENDING_APPROVAL',
                'submittedAt': date.today().isoformat(),
                'message': 'Absence request submitted successfully (FAKE DATA)'
            }
            
        except Exception as e:
            handle_error(e)

    async def submit_week(self, user_id: int, week_no: int) -> Dict[str, Any]:
        """Submit a week for approval (fake implementation).

        Args:
            user_id: ID of the user
            week_no: Week number to submit (1-53)

        Returns:
            Dict: Response with submission details
            
        Raises:
            KimbleError: If there's an error submitting the week
            ValidationError: If the input validation fails
        """
        try:
            # Validate inputs
            if not isinstance(user_id, int) or user_id <= 0:
                raise AvatarValidationError("User ID must be a positive integer")
                
            if not isinstance(week_no, int) or not (1 <= week_no <= 53):
                raise AvatarValidationError("Week number must be between 1 and 53")
                
            # Simulate a potential error (10% chance)
            if random.random() < 0.1:
                raise KimbleError("Failed to submit week: Service unavailable")
                
            return {
                'success': True,
                'userId': user_id,
                'weekNumber': week_no,
                'submissionDate': date.today().isoformat(),
                'status': 'SUBMITTED',
                'message': f'Week {week_no} submitted for approval (FAKE DATA)'
            }
            
        except Exception as e:
            handle_error(e)

    async def get_absences(self, user_id: int, date_range: DateRange) -> List[Dict[str, Any]]:
        """Get absences for a user within a date range (fake implementation).
        
        Args:
            user_id: ID of the user
            date_range: Date range to search for absences
            
        Returns:
            List[Dict]: List of absence records
            
        Raises:
            KimbleError: If there's an error fetching absences
            ValidationError: If the input validation fails
        """
        try:
            # Validate inputs
            if not isinstance(user_id, int) or user_id <= 0:
                raise AvatarValidationError("User ID must be a positive integer")
                
            if not isinstance(date_range, DateRange):
                raise AvatarValidationError("Invalid date range provided")
                
            # Simulate a potential error (5% chance)
            if random.random() < 0.05:
                raise KimbleError("Failed to fetch absences: Service unavailable")
            
            # Generate some random absences for testing
            absences = []
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
            
        except Exception as e:
            handle_error(e)

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
            bool: True if user is absent, False otherwise
            
        Raises:
            KimbleError: If there's an error checking absence
            ValidationError: If the input validation fails
        """
        try:
            # Validate inputs
            if not isinstance(user_id, int) or user_id <= 0:
                raise AvatarValidationError("User ID must be a positive integer")
                
            if not isinstance(check_date, date):
                raise AvatarValidationError("Invalid date format")
                
            if check_date > date.today():
                raise AvatarValidationError("Cannot check absence for future dates")
                
            # Simulate a potential error (5% chance)
            if random.random() < 0.05:
                raise KimbleError("Failed to check absence: Service unavailable")
                
            # 20% chance of being absent on any given day
            return random.random() < 0.2
            
        except Exception as e:
            handle_error(e)
