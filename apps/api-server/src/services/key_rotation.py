"""
ECC Key Rotation Service

Handles periodic rotation of ECC private keys for enhanced security.
"""

import os
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

from src.services.ecc import get_ecc_service, init_ecc_service

logger = logging.getLogger(__name__)


class KeyRotationService:
    """Service for rotating ECC private keys"""
    
    def __init__(self, rotation_days: int = 90):
        """
        Initialize key rotation service
        
        Args:
            rotation_days: Number of days between key rotations (default: 90)
        """
        self.rotation_days = rotation_days
        self.current_key_pem: Optional[str] = None
        self.previous_key_pem: Optional[str] = None
        self.rotation_date: Optional[datetime] = None
    
    def load_current_key(self) -> str:
        """Load current key from environment"""
        self.current_key_pem = os.getenv("ECC_PRIVATE_KEY_PEM")
        if not self.current_key_pem:
            raise ValueError("ECC_PRIVATE_KEY_PEM not found in environment")
        return self.current_key_pem
    
    def generate_new_key(self) -> str:
        """Generate a new ECC key pair"""
        private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ).decode()
        return pem
    
    def should_rotate(self) -> bool:
        """Check if key should be rotated based on age"""
        if not self.rotation_date:
            return False
        
        days_since_rotation = (datetime.now() - self.rotation_date).days
        return days_since_rotation >= self.rotation_days
    
    async def rotate_key(self) -> dict:
        """
        Rotate the ECC key
        
        Returns:
            dict with rotation status and new key info
        """
        try:
            # Store old key as previous
            self.previous_key_pem = self.current_key_pem
            
            # Generate new key
            new_key_pem = self.generate_new_key()
            
            # Update environment
            os.environ["ECC_PRIVATE_KEY_PEM"] = new_key_pem
            
            # Re-initialize ECC service with new key
            init_ecc_service(new_key_pem)
            
            # Update rotation date
            self.rotation_date = datetime.now()
            
            logger.info("ECC key rotated successfully")
            
            return {
                "success": True,
                "rotation_date": self.rotation_date.isoformat(),
                "next_rotation": (self.rotation_date + timedelta(days=self.rotation_days)).isoformat(),
                "message": "Key rotated successfully. Update your environment configuration."
            }
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Key rotation failed. Please check logs."
            }
    
    async def validate_key_rotation(self) -> dict:
        """
        Validate current key and check if rotation is needed
        
        Returns:
            dict with validation status
        """
        try:
            self.load_current_key()
            
            # Check if rotation is needed
            needs_rotation = self.should_rotate()
            
            if needs_rotation:
                return {
                    "valid": True,
                    "needs_rotation": True,
                    "rotation_days": self.rotation_days,
                    "message": f"Key is {self.rotation_days}+ days old. Rotation recommended."
                }
            
            return {
                "valid": True,
                "needs_rotation": False,
                "message": "Key is valid and within rotation period."
            }
        except Exception as e:
            logger.error(f"Key validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
                "message": "Key validation failed."
            }
    
    async def schedule_rotation(self):
        """Schedule periodic key rotation"""
        while True:
            try:
                # Check every day
                await asyncio.sleep(86400)  # 24 hours
                
                validation = await self.validate_key_rotation()
                
                if validation.get("needs_rotation"):
                    logger.info("Initiating scheduled key rotation...")
                    result = await self.rotate_key()
                    logger.info(f"Rotation result: {result}")
                    
                    # In production, this should trigger an alert
                    # to update environment configuration
                    if result["success"]:
                        logger.warning(
                            "IMPORTANT: ECC key has been rotated. "
                            "Update ECC_PRIVATE_KEY_PEM in your environment configuration."
                        )
            except Exception as e:
                logger.error(f"Error in rotation scheduler: {e}")


# Global instance
key_rotation_service = KeyRotationService(rotation_days=90)


async def start_key_rotation_scheduler():
    """Start the key rotation scheduler in background"""
    logger.info("Starting key rotation scheduler...")
    await key_rotation_service.schedule_rotation()


# API endpoint for manual key rotation
from fastapi import APIRouter, Depends, HTTPException, status
from src.middleware.auth_middleware import require_auth

rotation_router = APIRouter(prefix="/api/v1/security", tags=["Security"])


@rotation_router.get("/key-status")
async def get_key_status():
    """Get current key status and rotation info"""
    return await key_rotation_service.validate_key_rotation()


@rotation_router.post("/rotate-key")
async def rotate_key(current_user = Depends(require_auth)):
    """
    Manually rotate the ECC key (admin only)
    
    Requires admin role
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can rotate keys"
        )
    
    result = await key_rotation_service.rotate_key()
    
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("error", "Key rotation failed")
        )
    
    return result
