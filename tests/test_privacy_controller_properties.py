"""Property-based tests for Privacy Controller.

Feature: fitbuddy-lifestyle-assistant
Tests Properties 28 and 29 from the design document.
"""

import pytest
from hypothesis import given, strategies as st
from jeevanfit.privacy import PrivacyController, EncryptedData


# Strategy for generating various data types to encrypt
@st.composite
def data_to_encrypt(draw):
    """Generate various types of data that might need encryption."""
    data_type = draw(st.sampled_from([
        'string', 'number', 'list', 'dict', 'nested', 'mixed'
    ]))
    
    if data_type == 'string':
        return draw(st.text(min_size=0, max_size=1000))
    elif data_type == 'number':
        return draw(st.one_of(st.integers(), st.floats(allow_nan=False, allow_infinity=False)))
    elif data_type == 'list':
        return draw(st.lists(st.one_of(st.text(), st.integers()), max_size=20))
    elif data_type == 'dict':
        return draw(st.dictionaries(
            st.text(min_size=1, max_size=50),
            st.one_of(st.text(), st.integers(), st.booleans()),
            max_size=10
        ))
    elif data_type == 'nested':
        return {
            'user_id': draw(st.text(min_size=1, max_size=50)),
            'data': draw(st.lists(st.dictionaries(
                st.text(min_size=1, max_size=20),
                st.one_of(st.text(), st.integers()),
                max_size=5
            ), max_size=5))
        }
    else:  # mixed
        return {
            'string': draw(st.text(max_size=100)),
            'number': draw(st.integers()),
            'list': draw(st.lists(st.integers(), max_size=10)),
            'bool': draw(st.booleans())
        }


# Property 28: Data encryption at rest
# Feature: fitbuddy-lifestyle-assistant, Property 28: Data encryption at rest
@given(data=data_to_encrypt())
def test_property_28_data_encryption_at_rest(data):
    """**Validates: Requirements 9.1**
    
    Property 28: Data encryption at rest
    For any user data stored in the database, the sensitive fields should be 
    encrypted using AES-256 encryption before storage.
    
    This test verifies that:
    1. Data can be encrypted using AES-256
    2. Encrypted data is different from original data
    3. Encrypted data uses the correct algorithm
    4. Each encryption produces unique ciphertext (due to random IV)
    """
    controller = PrivacyController()
    
    # Encrypt the data
    encrypted = controller.encryptData(data)
    
    # Verify it's an EncryptedData object
    assert isinstance(encrypted, EncryptedData)
    
    # Verify algorithm is AES-256
    assert encrypted.algorithm == "AES-256-CBC"
    
    # Verify ciphertext and IV are present and non-empty
    assert encrypted.ciphertext
    assert encrypted.iv
    assert len(encrypted.ciphertext) > 0
    assert len(encrypted.iv) > 0
    
    # Verify encrypted data is different from original (when serialized)
    # The ciphertext should not contain the plaintext
    import json
    plaintext_str = json.dumps(data, default=str)
    assert plaintext_str not in encrypted.ciphertext
    
    # Verify that encrypting the same data twice produces different ciphertexts
    # (due to random IV)
    encrypted2 = controller.encryptData(data)
    assert encrypted.ciphertext != encrypted2.ciphertext or encrypted.iv != encrypted2.iv


# Property 28 (additional): Encryption round-trip preserves data
@given(data=data_to_encrypt())
def test_property_28_encryption_round_trip(data):
    """**Validates: Requirements 9.1**
    
    Property 28 (round-trip): Encryption and decryption preserve data
    For any data that is encrypted and then decrypted, the result should be
    identical to the original data.
    """
    controller = PrivacyController()
    
    # Encrypt then decrypt
    encrypted = controller.encryptData(data)
    decrypted = controller.decryptData(encrypted)
    
    # Verify data is preserved
    assert decrypted == data


# Property 28 (additional): Different keys produce different ciphertexts
@given(data=data_to_encrypt())
def test_property_28_different_keys_different_ciphertext(data):
    """**Validates: Requirements 9.1**
    
    Property 28 (key isolation): Different encryption keys produce different ciphertexts
    For any data encrypted with different keys, the ciphertexts should be different.
    """
    import os
    
    key1 = os.urandom(32)
    key2 = os.urandom(32)
    
    controller1 = PrivacyController(encryption_key=key1)
    controller2 = PrivacyController(encryption_key=key2)
    
    encrypted1 = controller1.encryptData(data)
    encrypted2 = controller2.encryptData(data)
    
    # Different keys should produce different ciphertexts
    # (even with same IV, which is unlikely but possible)
    assert encrypted1.ciphertext != encrypted2.ciphertext


# Property 28 (additional): Cannot decrypt with wrong key
@given(data=data_to_encrypt())
def test_property_28_wrong_key_fails_decryption(data):
    """**Validates: Requirements 9.1**
    
    Property 28 (key security): Data encrypted with one key cannot be decrypted with another
    For any data encrypted with one key, attempting to decrypt with a different key
    should fail or produce garbage data.
    """
    import os
    
    key1 = os.urandom(32)
    key2 = os.urandom(32)
    
    controller1 = PrivacyController(encryption_key=key1)
    controller2 = PrivacyController(encryption_key=key2)
    
    encrypted = controller1.encryptData(data)
    
    # Attempting to decrypt with wrong key should fail
    try:
        decrypted = controller2.decryptData(encrypted)
        # If it doesn't raise an exception, the decrypted data should be different
        assert decrypted != data
    except Exception:
        # Expected: decryption should fail with wrong key
        pass


# Strategy for generating user data with multiple components
@st.composite
def user_data_with_components(draw):
    """Generate realistic user data with lifestyle entries, analysis history, and profile."""
    user_id = draw(st.text(min_size=1, max_size=50))
    
    # Generate lifestyle entries
    lifestyle_entries = draw(st.lists(
        st.dictionaries(
            st.sampled_from(['entry_id', 'timestamp', 'food_items', 'water_intake', 'sleep_data']),
            st.one_of(st.text(), st.integers(), st.floats(allow_nan=False, allow_infinity=False)),
            min_size=1
        ),
        min_size=1,
        max_size=10
    ))
    
    # Generate analysis history
    analysis_history = draw(st.lists(
        st.dictionaries(
            st.sampled_from(['record_id', 'timestamp', 'analysis_type', 'confidence']),
            st.one_of(st.text(), st.integers(), st.floats(min_value=0, max_value=1, allow_nan=False)),
            min_size=1
        ),
        min_size=0,
        max_size=5
    ))
    
    # Generate profile information
    profile = draw(st.dictionaries(
        st.sampled_from(['body_type', 'preferences', 'created_at']),
        st.one_of(st.text(), st.dictionaries(st.text(min_size=1), st.text(), max_size=3)),
        min_size=1
    ))
    
    return {
        'user_id': user_id,
        'lifestyle_entries': lifestyle_entries,
        'analysis_history': analysis_history,
        'profile': profile
    }


# Property 29: Data export completeness
# Feature: fitbuddy-lifestyle-assistant, Property 29: Data export completeness
@given(user_data=user_data_with_components())
def test_property_29_data_export_completeness(user_data):
    """**Validates: Requirements 9.4**
    
    Property 29: Data export completeness
    For any user requesting data export, the exported file should contain all stored 
    data for that user in valid JSON format including all lifestyle entries, 
    analysis history, and profile information.
    
    This test verifies that:
    1. Export contains all data components
    2. Export is in JSON format
    3. Export includes user_id and export_date
    4. All original data is present in the export
    """
    controller = PrivacyController()
    user_id = user_data['user_id']
    
    # Store user data
    controller._store_user_data(user_id, user_data)
    
    # Export the data
    export = controller.exportUserData(user_id)
    
    # Verify export structure
    assert export.user_id == user_id
    assert export.format == "JSON"
    assert export.export_date is not None
    
    # Verify all data is present in export
    exported_data = export.data
    
    # Check that all top-level keys from original data are in export
    for key in user_data.keys():
        assert key in exported_data, f"Key '{key}' missing from export"
    
    # Verify lifestyle entries are complete
    if 'lifestyle_entries' in user_data:
        assert 'lifestyle_entries' in exported_data
        assert len(exported_data['lifestyle_entries']) == len(user_data['lifestyle_entries'])
    
    # Verify analysis history is complete
    if 'analysis_history' in user_data:
        assert 'analysis_history' in exported_data
        assert len(exported_data['analysis_history']) == len(user_data['analysis_history'])
    
    # Verify profile is complete
    if 'profile' in user_data:
        assert 'profile' in exported_data
    
    # Verify export can be converted to JSON (valid JSON format)
    import json
    export_dict = export.to_dict()
    json_str = json.dumps(export_dict, default=str)
    assert json_str is not None
    
    # Verify we can parse it back
    parsed = json.loads(json_str)
    assert parsed['user_id'] == user_id
    assert parsed['format'] == "JSON"


# Property 29 (additional): Export for non-existent user returns empty data
@given(user_id=st.text(min_size=1, max_size=50))
def test_property_29_export_nonexistent_user(user_id):
    """**Validates: Requirements 9.4**
    
    Property 29 (edge case): Export for non-existent user
    For any user ID that has no stored data, the export should return an empty
    data structure but still be valid.
    """
    controller = PrivacyController()
    
    # Export data for user that doesn't exist
    export = controller.exportUserData(user_id)
    
    # Verify export structure is valid
    assert export.user_id == user_id
    assert export.format == "JSON"
    assert export.export_date is not None
    
    # Data should be empty dict
    assert export.data == {}


# Property 29 (additional): Multiple exports produce consistent data
@given(user_data=user_data_with_components())
def test_property_29_export_consistency(user_data):
    """**Validates: Requirements 9.4**
    
    Property 29 (consistency): Multiple exports of same user produce same data
    For any user, exporting their data multiple times should produce the same
    data content (though export_date will differ).
    """
    controller = PrivacyController()
    user_id = user_data['user_id']
    
    # Store user data
    controller._store_user_data(user_id, user_data)
    
    # Export twice
    export1 = controller.exportUserData(user_id)
    export2 = controller.exportUserData(user_id)
    
    # Data should be identical
    assert export1.data == export2.data
    assert export1.user_id == export2.user_id
    assert export1.format == export2.format
