"""Unit tests for Privacy Controller.

Tests specific examples and edge cases for encryption, export, and deletion.
"""

import pytest
import os
import json
from jeevanfit.privacy import PrivacyController, EncryptedData, DataExport, DeletionConfirmation


class TestEncryptionRoundTrip:
    """Test encryption and decryption round-trip for various data types."""
    
    def test_encrypt_decrypt_string(self):
        """Test encryption round-trip with string data."""
        controller = PrivacyController()
        original = "Hello, World!"
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_number(self):
        """Test encryption round-trip with numeric data."""
        controller = PrivacyController()
        original = 42
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_list(self):
        """Test encryption round-trip with list data."""
        controller = PrivacyController()
        original = [1, 2, 3, "four", 5.0]
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_dict(self):
        """Test encryption round-trip with dictionary data."""
        controller = PrivacyController()
        original = {
            "name": "John Doe",
            "age": 30,
            "active": True,
            "scores": [85, 90, 95]
        }
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_nested_structure(self):
        """Test encryption round-trip with deeply nested data."""
        controller = PrivacyController()
        original = {
            "user": {
                "id": "user123",
                "profile": {
                    "name": "Jane Smith",
                    "preferences": {
                        "theme": "dark",
                        "notifications": True
                    }
                },
                "data": [
                    {"entry": 1, "value": 100},
                    {"entry": 2, "value": 200}
                ]
            }
        }
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_empty_string(self):
        """Test encryption round-trip with empty string."""
        controller = PrivacyController()
        original = ""
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_empty_dict(self):
        """Test encryption round-trip with empty dictionary."""
        controller = PrivacyController()
        original = {}
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_empty_list(self):
        """Test encryption round-trip with empty list."""
        controller = PrivacyController()
        original = []
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_unicode(self):
        """Test encryption round-trip with unicode characters."""
        controller = PrivacyController()
        original = "Hello 世界 🌍 Привет"
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original
    
    def test_encrypt_decrypt_large_data(self):
        """Test encryption round-trip with large data structure."""
        controller = PrivacyController()
        original = {
            "entries": [{"id": i, "data": f"entry_{i}" * 10} for i in range(100)]
        }
        
        encrypted = controller.encryptData(original)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == original


class TestEncryptionSecurity:
    """Test security properties of encryption."""
    
    def test_same_data_different_ciphertext(self):
        """Test that encrypting same data twice produces different ciphertexts."""
        controller = PrivacyController()
        data = {"secret": "password123"}
        
        encrypted1 = controller.encryptData(data)
        encrypted2 = controller.encryptData(data)
        
        # Different IVs should produce different ciphertexts
        assert encrypted1.ciphertext != encrypted2.ciphertext or encrypted1.iv != encrypted2.iv
    
    def test_different_keys_different_ciphertext(self):
        """Test that different keys produce different ciphertexts."""
        key1 = os.urandom(32)
        key2 = os.urandom(32)
        
        controller1 = PrivacyController(encryption_key=key1)
        controller2 = PrivacyController(encryption_key=key2)
        
        data = {"secret": "password123"}
        
        encrypted1 = controller1.encryptData(data)
        encrypted2 = controller2.encryptData(data)
        
        assert encrypted1.ciphertext != encrypted2.ciphertext
    
    def test_wrong_key_cannot_decrypt(self):
        """Test that data encrypted with one key cannot be decrypted with another."""
        key1 = os.urandom(32)
        key2 = os.urandom(32)
        
        controller1 = PrivacyController(encryption_key=key1)
        controller2 = PrivacyController(encryption_key=key2)
        
        data = {"secret": "password123"}
        encrypted = controller1.encryptData(data)
        
        # Attempting to decrypt with wrong key should fail or produce wrong data
        try:
            decrypted = controller2.decryptData(encrypted)
            assert decrypted != data
        except Exception:
            # Expected: decryption fails
            pass
    
    def test_encryption_key_validation(self):
        """Test that invalid encryption keys are rejected."""
        # Key too short
        with pytest.raises(ValueError):
            PrivacyController(encryption_key=b"short")
        
        # Key too long
        with pytest.raises(ValueError):
            PrivacyController(encryption_key=os.urandom(64))
    
    def test_encrypted_data_structure(self):
        """Test that encrypted data has correct structure."""
        controller = PrivacyController()
        data = {"test": "data"}
        
        encrypted = controller.encryptData(data)
        
        assert isinstance(encrypted, EncryptedData)
        assert encrypted.algorithm == "AES-256-CBC"
        assert isinstance(encrypted.ciphertext, str)
        assert isinstance(encrypted.iv, str)
        assert len(encrypted.ciphertext) > 0
        assert len(encrypted.iv) > 0


class TestDataExport:
    """Test data export functionality."""
    
    def test_export_user_data(self):
        """Test exporting user data."""
        controller = PrivacyController()
        user_id = "user123"
        user_data = {
            "profile": {"name": "John Doe"},
            "entries": [{"id": 1}, {"id": 2}]
        }
        
        controller._store_user_data(user_id, user_data)
        export = controller.exportUserData(user_id)
        
        assert isinstance(export, DataExport)
        assert export.user_id == user_id
        assert export.format == "JSON"
        assert export.data == user_data
        assert export.export_date is not None
    
    def test_export_nonexistent_user(self):
        """Test exporting data for user that doesn't exist."""
        controller = PrivacyController()
        export = controller.exportUserData("nonexistent")
        
        assert export.user_id == "nonexistent"
        assert export.data == {}
    
    def test_export_to_dict(self):
        """Test converting export to dictionary."""
        controller = PrivacyController()
        user_id = "user123"
        user_data = {"test": "data"}
        
        controller._store_user_data(user_id, user_data)
        export = controller.exportUserData(user_id)
        
        export_dict = export.to_dict()
        
        assert export_dict["user_id"] == user_id
        assert export_dict["format"] == "JSON"
        assert export_dict["data"] == user_data
        assert "export_date" in export_dict
    
    def test_export_json_serializable(self):
        """Test that export can be serialized to JSON."""
        controller = PrivacyController()
        user_id = "user123"
        user_data = {"test": "data", "number": 42}
        
        controller._store_user_data(user_id, user_data)
        export = controller.exportUserData(user_id)
        
        # Should be able to serialize to JSON
        json_str = json.dumps(export.to_dict(), default=str)
        assert json_str is not None
        
        # Should be able to parse back
        parsed = json.loads(json_str)
        assert parsed["user_id"] == user_id


class TestDataDeletion:
    """Test data deletion functionality."""
    
    def test_delete_user_data(self):
        """Test deleting user data."""
        controller = PrivacyController()
        user_id = "user123"
        user_data = {"test": "data"}
        
        controller._store_user_data(user_id, user_data)
        
        # Verify data exists
        export_before = controller.exportUserData(user_id)
        assert export_before.data == user_data
        
        # Delete data
        confirmation = controller.deleteUserData(user_id)
        
        assert isinstance(confirmation, DeletionConfirmation)
        assert confirmation.user_id == user_id
        assert confirmation.status == "COMPLETED"
        assert confirmation.deletion_date is not None
        
        # Verify data is gone
        export_after = controller.exportUserData(user_id)
        assert export_after.data == {}
    
    def test_delete_nonexistent_user(self):
        """Test deleting data for user that doesn't exist."""
        controller = PrivacyController()
        
        # Should not raise error
        confirmation = controller.deleteUserData("nonexistent")
        
        assert confirmation.user_id == "nonexistent"
        assert confirmation.status == "COMPLETED"
    
    def test_deletion_confirmation_to_dict(self):
        """Test converting deletion confirmation to dictionary."""
        controller = PrivacyController()
        confirmation = controller.deleteUserData("user123")
        
        conf_dict = confirmation.to_dict()
        
        assert conf_dict["user_id"] == "user123"
        assert conf_dict["status"] == "COMPLETED"
        assert "deletion_date" in conf_dict


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_encrypt_none(self):
        """Test encrypting None value."""
        controller = PrivacyController()
        
        encrypted = controller.encryptData(None)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted is None
    
    def test_encrypt_boolean(self):
        """Test encrypting boolean values."""
        controller = PrivacyController()
        
        for value in [True, False]:
            encrypted = controller.encryptData(value)
            decrypted = controller.decryptData(encrypted)
            assert decrypted == value
    
    def test_encrypt_special_characters(self):
        """Test encrypting data with special characters."""
        controller = PrivacyController()
        data = {
            "special": "!@#$%^&*()_+-=[]{}|;':\",./<>?",
            "newlines": "line1\nline2\nline3",
            "tabs": "col1\tcol2\tcol3"
        }
        
        encrypted = controller.encryptData(data)
        decrypted = controller.decryptData(encrypted)
        
        assert decrypted == data
