"""Privacy Controller for JeevanFit Lifestyle Assistant.

Handles data encryption, decryption, export, and deletion operations.
Uses AES-256 encryption for data at rest.
"""

import json
import os
from typing import Any, Dict
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import base64


class EncryptedData:
    """Represents encrypted data with metadata."""
    
    def __init__(self, ciphertext: str, iv: str, algorithm: str = "AES-256-CBC"):
        self.ciphertext = ciphertext
        self.iv = iv
        self.algorithm = algorithm
    
    def to_dict(self) -> Dict[str, str]:
        return {
            "ciphertext": self.ciphertext,
            "iv": self.iv,
            "algorithm": self.algorithm
        }


class DataExport:
    """Represents exported user data."""
    
    def __init__(self, user_id: str, data: Dict[str, Any], format: str = "JSON"):
        self.user_id = user_id
        self.export_date = datetime.utcnow()
        self.data = data
        self.format = format
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "export_date": self.export_date.isoformat(),
            "data": self.data,
            "format": self.format
        }


class DeletionConfirmation:
    """Represents confirmation of data deletion."""
    
    def __init__(self, user_id: str, status: str = "COMPLETED"):
        self.user_id = user_id
        self.deletion_date = datetime.utcnow()
        self.status = status
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "deletion_date": self.deletion_date.isoformat(),
            "status": self.status
        }


class PrivacyController:
    """Manages data privacy operations including encryption, export, and deletion."""
    
    def __init__(self, encryption_key: bytes = None):
        """Initialize the Privacy Controller.
        
        Args:
            encryption_key: 32-byte key for AES-256 encryption. If None, generates a new key.
        """
        if encryption_key is None:
            self.encryption_key = os.urandom(32)  # 256 bits for AES-256
        else:
            if len(encryption_key) != 32:
                raise ValueError("Encryption key must be 32 bytes for AES-256")
            self.encryption_key = encryption_key
        
        self.backend = default_backend()
        # In-memory storage for demo purposes (would be database in production)
        self._user_data_store: Dict[str, Any] = {}
    
    def encryptData(self, data: Any) -> EncryptedData:
        """Encrypt data using AES-256 encryption.
        
        Args:
            data: Data to encrypt (will be JSON serialized)
        
        Returns:
            EncryptedData object containing ciphertext and IV
        """
        # Serialize data to JSON
        json_data = json.dumps(data, default=str)
        plaintext = json_data.encode('utf-8')
        
        # Generate random IV (Initialization Vector)
        iv = os.urandom(16)  # AES block size is 16 bytes
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        encryptor = cipher.encryptor()
        
        # Pad plaintext to block size
        padder = padding.PKCS7(128).padder()
        padded_data = padder.update(plaintext) + padder.finalize()
        
        # Encrypt
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        
        # Encode to base64 for storage
        ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
        iv_b64 = base64.b64encode(iv).decode('utf-8')
        
        return EncryptedData(ciphertext=ciphertext_b64, iv=iv_b64)
    
    def decryptData(self, encrypted: EncryptedData) -> Any:
        """Decrypt data that was encrypted with encryptData.
        
        Args:
            encrypted: EncryptedData object containing ciphertext and IV
        
        Returns:
            Decrypted data (deserialized from JSON)
        """
        # Decode from base64
        ciphertext = base64.b64decode(encrypted.ciphertext)
        iv = base64.b64decode(encrypted.iv)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(self.encryption_key),
            modes.CBC(iv),
            backend=self.backend
        )
        decryptor = cipher.decryptor()
        
        # Decrypt
        padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()
        
        # Unpad
        unpadder = padding.PKCS7(128).unpadder()
        plaintext = unpadder.update(padded_plaintext) + unpadder.finalize()
        
        # Deserialize from JSON
        json_data = plaintext.decode('utf-8')
        return json.loads(json_data)
    
    def exportUserData(self, user_id: str) -> DataExport:
        """Export all user data in JSON format.
        
        Args:
            user_id: ID of the user whose data to export
        
        Returns:
            DataExport object containing all user data
        """
        # Retrieve user data from storage
        user_data = self._user_data_store.get(user_id, {})
        
        # Create export with all user data
        export = DataExport(
            user_id=user_id,
            data=user_data,
            format="JSON"
        )
        
        return export
    
    def deleteUserData(self, user_id: str) -> DeletionConfirmation:
        """Permanently delete all user data.
        
        Args:
            user_id: ID of the user whose data to delete
        
        Returns:
            DeletionConfirmation object confirming deletion
        """
        # Remove user data from storage
        if user_id in self._user_data_store:
            del self._user_data_store[user_id]
        
        # Return confirmation
        return DeletionConfirmation(user_id=user_id, status="COMPLETED")
    
    def _store_user_data(self, user_id: str, data: Any) -> None:
        """Internal method to store user data (for testing purposes).
        
        Args:
            user_id: ID of the user
            data: Data to store
        """
        self._user_data_store[user_id] = data
