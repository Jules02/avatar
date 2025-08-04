from datetime import date, datetime, timedelta
from uuid import uuid4
from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, field_validator, ValidationError
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, ForeignKey, select, update, delete
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
import logging
import os
import random
from contextlib import asynccontextmanager

from exceptions import KimbleError, ValidationError as AvatarValidationError, handle_error

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()

class DBAbsence(Base):
    """Database model for absences."""
    __tablename__ = 'absences'
    
    absence_id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = Column(String(36), index=True, nullable=True)
    date = Column(Date, index=True, nullable=True)
    reason = Column(String(100), nullable=True)
    justified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=True)
    
    __table_args__ = (
        {'schema': 'eis'},
    )

class DBConnection:
    """Manages database connections."""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize the database connection."""
        # Default to local development settings if DATABASE_URL is not set
        db_url = os.getenv('DATABASE_URL', 'mysql+pymysql://eis_user:eis_pass@127.0.0.1:3307/eis')
        self.engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            echo=os.getenv('SQL_ECHO', 'False').lower() == 'true'
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Don't create tables automatically - they should be created by the SQL script
        # Base.metadata.create_all(bind=self.engine)
    
    @asynccontextmanager
    async def get_db(self):
        """Async context manager for database sessions."""
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

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
    """Client for interacting with the Kimble database."""
    
    def __init__(self):
        """Initialize the Kimble database client."""
        self.db = DBConnection()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def close(self):
        """Close the database connection."""
        if hasattr(self, 'db'):
            # Clean up any resources if needed
            pass

    async def fill_absence(
        self, 
        user_id: str, 
        absence_date: date, 
        reason: str
    ) -> Dict[str, Any]:
        """Create or update an absence record in the database.
        
        Args:
            user_id: UUID string of the user
            absence_date: Date of absence
            reason: Reason for absence (sick, unjustified, remote_not_logged, etc.)
            
        Returns:
            Dictionary with operation status and data
            
        Raises:
            AvatarValidationError: If input validation fails
            KimbleError: If database operation fails
        """
        if not user_id:
            raise AvatarValidationError("User ID is required")
            
        if absence_date > date.today():
            raise AvatarValidationError("Cannot create absence for future dates")
            
        try:
            async with self.db.get_db() as session:
                # Check if absence already exists for this user and date
                stmt = select(DBAbsence).where(
                    (DBAbsence.user_id == user_id) & 
                    (DBAbsence.date == absence_date)
                )
                result = session.execute(stmt).scalar_one_or_none()
                
                if result:
                    # Update existing absence
                    stmt = (
                        update(DBAbsence)
                        .where(DBAbsence.absence_id == result.absence_id)
                        .values(
                            reason=reason,
                            justified=reason in ['sick'],  # Only 'sick' is marked as justified in the sample data
                            created_at=datetime.utcnow()
                        )
                    )
                    session.execute(stmt)
                    action = "updated"
                    absence_id = result.absence_id
                else:
                    # Create new absence
                    absence = DBAbsence(
                        user_id=user_id,
                        date=absence_date,
                        reason=reason,
                        justified=reason in ['sick']  # Only 'sick' is marked as justified in the sample data
                    )
                    session.add(absence)
                    session.flush()  # To get the generated absence_id
                    absence_id = absence.absence_id
                    action = "created"
                
                session.commit()
                
                # Get the updated/created record
                stmt = select(DBAbsence).where(DBAbsence.absence_id == absence_id)
                result = session.execute(stmt).scalar_one()
                
                return {
                    "status": "success",
                    "action": action,
                    "data": {
                        "absence_id": result.absence_id,
                        "user_id": result.user_id,
                        "date": result.date.isoformat() if result.date else None,
                        "reason": result.reason,
                        "justified": bool(result.justified),
                        "created_at": result.created_at.isoformat() if result.created_at else None
                    }
                }
        except SQLAlchemyError as e:
            logger.error(f"Database error in fill_absence: {e}")
            raise KimbleError(f"Database operation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in fill_absence: {e}")
            raise KimbleError(f"Failed to process absence: {e}")
                
    async def is_absent(self, user_id: str, check_date: date) -> Dict[str, Any]:
        """Check if a user is absent on a specific date.
        
        Args:
            user_id: UUID string of the user
            check_date: Date to check for absence
            
        Returns:
            Dictionary with absence information if found, None otherwise
            
        Raises:
            AvatarValidationError: If input validation fails
            KimbleError: If database operation fails
        """
        if not user_id:
            raise AvatarValidationError("User ID is required")
            
        try:
            async with self.db.get_db() as session:
                stmt = select(DBAbsence).where(
                    (DBAbsence.user_id == user_id) & 
                    (DBAbsence.date == check_date)
                )
                result = session.execute(stmt).scalar_one_or_none()
                
                if result:
                    return {
                        "is_absent": True,
                        "absence_id": result.absence_id,
                        "reason": result.reason,
                        "justified": bool(result.justified),
                        "created_at": result.created_at.isoformat() if result.created_at else None
                    }
                return {"is_absent": False}
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in is_absent: {e}")
            raise KimbleError(f"Database operation failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in is_absent: {e}")
            raise KimbleError(f"Failed to process absence: {e}")

    async def get_absences(self, user_id: str, date_range: 'DateRange') -> List[Dict[str, Any]]:
        """Get all absences for a user within a date range.
        
        Args:
            user_id: UUID string of the user
            date_range: DateRange object with start and end dates
            
        Returns:
            List of dictionaries with absence details
            
        Raises:
            AvatarValidationError: If input validation fails
            KimbleError: If database operation fails
        """
        if not user_id:
            raise AvatarValidationError("User ID is required")
            
        if not date_range or not date_range.start or not date_range.end:
            raise AvatarValidationError("Invalid date range provided")
            
        if date_range.start > date_range.end:
            raise AvatarValidationError("Start date cannot be after end date")
            
        try:
            async with self.db.get_db() as session:
                stmt = select(DBAbsence).where(
                    (DBAbsence.user_id == user_id) & 
                    (DBAbsence.date >= date_range.start) & 
                    (DBAbsence.date <= date_range.end)
                ).order_by(DBAbsence.date)
                
                result = session.execute(stmt).scalars().all()
                
                return [{
                    "absence_id": absence.absence_id,
                    "date": absence.date.isoformat() if absence.date else None,
                    "reason": absence.reason,
                    "justified": bool(absence.justified),
                    "created_at": absence.created_at.isoformat() if absence.created_at else None
                } for absence in result]
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_absences: {e}")
            raise KimbleError(f"Database operation failed: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error in get_absences: {e}", exc_info=True)
            raise KimbleError(f"Unexpected error: {e}")
            
    async def count_absences(self, user_id: str, date_range: 'DateRange') -> Dict[str, Any]:
        """Count absences for a user within a date range, grouped by reason.
        
        Args:
            user_id: UUID string of the user
            date_range: DateRange object with start and end dates
            
        Returns:
            Dictionary with total count and counts by reason
            
        Raises:
            AvatarValidationError: If input validation fails
            KimbleError: If database operation fails
        """
        if not user_id:
            raise AvatarValidationError("User ID is required")
            
        if not date_range or not date_range.start or not date_range.end:
            raise AvatarValidationError("Invalid date range provided")
            
        if date_range.start > date_range.end:
            raise AvatarValidationError("Start date cannot be after end date")
            
        try:
            async with self.db.get_db() as session:
                # Get all absences in the date range
                stmt = select(DBAbsence).where(
                    (DBAbsence.user_id == user_id) & 
                    (DBAbsence.date >= date_range.start) & 
                    (DBAbsence.date <= date_range.end)
                )
                
                result = session.execute(stmt).scalars().all()
                
                # Count by reason
                reason_counts = {}
                for absence in result:
                    reason = absence.reason or 'unknown'
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
                
                # Count justified vs unjustified
                justified_count = sum(1 for a in result if a.justified)
                
                return {
                    "total": len(result),
                    "by_reason": reason_counts,
                    "justified": justified_count,
                    "unjustified": len(result) - justified_count
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Database error in count_absences: {e}")
            raise KimbleError(f"Database operation failed: {e}")
            
        except Exception as e:
            logger.error(f"Unexpected error in count_absences: {e}", exc_info=True)
            raise KimbleError(f"Unexpected error: {e}")

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
            #if not isinstance(user_id, int) or user_id <= 0:
            #   raise AvatarValidationError("User ID must be a positive integer")
                
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
            #if not isinstance(user_id, int) or user_id <= 0:
            #   raise AvatarValidationError("User ID must be a positive integer")
                
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
            #if not isinstance(user_id, int) or user_id <= 0:
            #    raise AvatarValidationError("User ID must be a positive integer")
                
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
