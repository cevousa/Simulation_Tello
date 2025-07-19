"""
Hardware-Bound License Management Library
=========================================

This library provides secure license validation with hardware binding.
Designed for minimal integration into existing applications.

Author: License Management System
Date: July 2025
"""

import hashlib
import platform
import uuid
import json
import jwt
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class LicenseManager:
    """
    Core license validation and management class.
    Handles hardware-bound license verification with minimal code changes required.
    """
    
    def __init__(self, public_key_path: Optional[str] = None, license_file: Optional[str] = None):
        """
        Initialize the License Manager.
        
        Args:
            public_key_path: Path to public key file (optional, will use embedded key)
            license_file: Path to license file (optional, will search common locations)
        """
        self.public_key = self._load_public_key(public_key_path)
        self.license_file = license_file or self._find_license_file()
        self._cached_license = None
        self._last_check = None
    
    def _load_public_key(self, key_path: Optional[str] = None) -> str:
        """Load or return embedded public key."""
        if key_path and os.path.exists(key_path):
            with open(key_path, 'r') as f:
                return f.read()
        
        # Embedded public key (will be replaced with actual key)
        return """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAvVl7rQakFsPpB2s6z0pO
rRv+ARgjOR2H1fSHh2nYkKe45XF1Jt29aXri/xtuzK72sRrkJVQ9iWoCbeX3icpF
Sd3HGwCHoeB6bPSahJOleDrCSaTawSeji3YBr6vqss/rEmszG5+FB2SpkKmMHym9
SSmW/u7NfTInZvQxCQ4Pti1W8xl1Fj+xIzjfV12AkBt4R+B6dsAwWAauwF53nksc
yLXhTzWDgIfEwSMfH8/znVbKJI8MsJC46B5yIpP1THXlXy6s8TSov3RFGvmAC86m
BVQ736Dj1nyQKllj5fu3Jqgq0YHa9LffX2bVbB0XC4BXNFIA5zghZYdDhoC4U+SR
TwIDAQAB
-----END PUBLIC KEY-----"""
    
    def _find_license_file(self) -> Optional[str]:
        """Search for license file in common locations."""
        possible_paths = [
            "./license.dat",
            "./serial.dat", 
            os.path.expanduser("~/.config/app/license.dat"),
            os.path.join(os.getenv('APPDATA', ''), 'MyApp', 'license.dat'),
            "./app_license.key"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def generate_hardware_id(self) -> str:
        """
        Generate deterministic hardware ID that works on both dev and production machines.
        
        Returns:
            16-character hardware fingerprint
        """
        # Collect hardware information
        node_id = str(uuid.getnode())  # MAC address
        processor = platform.processor() or "unknown"
        machine = platform.machine() or "unknown"
        system = platform.system() or "unknown"
        
        # Create deterministic hash
        hw_string = f"{node_id}:{processor}:{machine}:{system}"
        hw_hash = hashlib.blake2b(hw_string.encode(), digest_size=8).hexdigest()
        
        return hw_hash[:16].upper()
    
    def validate_license(self, show_errors: bool = True) -> bool:
        """
        Validate current license. This is the main function to call from your app.
        
        Args:
            show_errors: Whether to print error messages
            
        Returns:
            True if license is valid, False otherwise
        """
        try:
            # Check if we have a license file
            if not self.license_file or not os.path.exists(self.license_file):
                if show_errors:
                    print("❌ No license file found. Please obtain a valid license.")
                return False
            
            # Load license token
            with open(self.license_file, 'r') as f:
                token = f.read().strip()
            
            # Decode and verify JWT token
            try:
                # Load public key for verification
                from cryptography.hazmat.primitives import serialization
                public_key_obj = serialization.load_pem_public_key(self.public_key.encode())
                
                claims = jwt.decode(
                    token,
                    public_key_obj,
                    algorithms=["PS256"],
                    options={
                        "require": ["user", "email", "hardware_id", "exp", "iss"]
                    }
                )
            except jwt.InvalidTokenError as e:
                if show_errors:
                    print(f"❌ Invalid license token: {str(e)}")
                return False
            
            # Verify hardware binding
            current_hw_id = self.generate_hardware_id()
            if claims["hardware_id"] != current_hw_id:
                if show_errors:
                    print("❌ This license is bound to a different machine.")
                    print(f"   Expected: {claims['hardware_id']}")
                    print(f"   Current:  {current_hw_id}")
                return False
            
            # Check expiration
            exp_timestamp = claims["exp"]
            exp_date = datetime.fromtimestamp(exp_timestamp)
            current_date = datetime.utcnow()
            
            if current_date >= exp_date:
                if show_errors:
                    print(f"❌ License expired on {exp_date.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                return False
            
            # Cache valid license
            self._cached_license = claims
            self._last_check = current_date
            
            if show_errors:
                days_left = (exp_date - current_date).days
                print(f"✅ License valid for {claims['user']} ({claims['email']})")
                print(f"   Expires: {exp_date.strftime('%Y-%m-%d')} ({days_left} days remaining)")
            
            return True
            
        except Exception as e:
            if show_errors:
                print(f"❌ License validation error: {str(e)}")
            return False
    
    def get_license_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the current license.
        
        Returns:
            Dictionary with license details or None if invalid
        """
        if self.validate_license(show_errors=False):
            return {
                'user': self._cached_license['user'],
                'email': self._cached_license['email'],
                'hardware_id': self._cached_license['hardware_id'],
                'expires': datetime.fromtimestamp(self._cached_license['exp']),
                'issuer': self._cached_license['iss'],
                'days_remaining': (datetime.fromtimestamp(self._cached_license['exp']) - datetime.utcnow()).days
            }
        return None
    
    def install_license(self, license_token: str, license_path: Optional[str] = None) -> bool:
        """
        Install a new license token.
        
        Args:
            license_token: The license token string
            license_path: Where to save the license (optional)
            
        Returns:
            True if license was installed successfully
        """
        try:
            # Validate the token first
            from cryptography.hazmat.primitives import serialization
            public_key_obj = serialization.load_pem_public_key(self.public_key.encode())
            
            claims = jwt.decode(
                license_token,
                public_key_obj,
                algorithms=["PS256"],
                options={"require": ["user", "email", "hardware_id", "exp", "iss"]}
            )
            
            # Check hardware binding
            current_hw_id = self.generate_hardware_id()
            if claims["hardware_id"] != current_hw_id:
                print("❌ License is not valid for this machine.")
                return False
            
            # Save license
            save_path = license_path or "./license.dat"
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            with open(save_path, 'w') as f:
                f.write(license_token)
            
            self.license_file = save_path
            print(f"✅ License installed successfully to {save_path}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install license: {str(e)}")
            return False


def require_valid_license(func):
    """
    Decorator to require valid license before function execution.
    Usage: @require_valid_license
    """
    def wrapper(*args, **kwargs):
        lm = LicenseManager()
        if not lm.validate_license():
            raise Exception("Valid license required to use this feature")
        return func(*args, **kwargs)
    return wrapper


# Convenience function for simple integration
def check_license() -> bool:
    """
    Simple license check function for minimal integration.
    
    Returns:
        True if license is valid, False otherwise
    """
    lm = LicenseManager()
    return lm.validate_license()


# Auto-check on import (can be disabled by setting environment variable)
if not os.getenv('DISABLE_LICENSE_AUTOCHECK'):
    _auto_lm = LicenseManager()
    if not _auto_lm.validate_license(show_errors=False):
        print("\n" + "="*50)
        print("⚠️  LICENSE VALIDATION REQUIRED")
        print("="*50)
        print("This application requires a valid license to run.")
        print("Please contact your software vendor for licensing.")
        print("="*50 + "\n")
