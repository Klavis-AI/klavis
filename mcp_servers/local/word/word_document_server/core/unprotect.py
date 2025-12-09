"""
Unprotect document functionality for the Word Document Server.

This module handles removing document protection.
"""
import os
import json
import hashlib
import tempfile
import shutil
from typing import Tuple, Optional

def remove_protection_info(filename: str, password: Optional[str] = None) -> Tuple[bool, str]:
    """
    Remove protection information from a document and decrypt it if necessary.
    
    Args:
        filename: Path to the Word document
        password: Password to verify before removing protection
        
    Returns:
        Tuple of (success, message)
    """
    base_path, _ = os.path.splitext(filename)
    metadata_path = f"{base_path}.protection"
    
    # Check if protection metadata exists
    if not os.path.exists(metadata_path):
        return False, "Document is not protected"
    
    try:
        # Load protection data
        with open(metadata_path, 'r') as f:
            protection_data = json.load(f)
        
        # Verify password if provided and required
        if password and protection_data.get("password_hash"):
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != protection_data.get("password_hash"):
                return False, "Incorrect password"
        
        # Handle true encryption if it was applied
        if protection_data.get("true_encryption") and password:
            try:
                import msoffcrypto
                
                # Create a temporary file for the decrypted output
                temp_fd, temp_path = tempfile.mkstemp(suffix='.docx')
                os.close(temp_fd)
                
                # Open the encrypted document
                with open(filename, 'rb') as f:
                    office_file = msoffcrypto.OfficeFile(f)
                    
                    # Decrypt with provided password
                    try:
                        office_file.load_key(password=password)
                        
                        # Write the decrypted file to the temp path
                        with open(temp_path, 'wb') as out_file:
                            office_file.decrypt(out_file)
                        
                        # Replace encrypted file with decrypted version
                        shutil.move(temp_path, filename)
                    except Exception as decrypt_error:
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        return False, f"Failed to decrypt document: {str(decrypt_error)}"
            except ImportError:
                return False, "Missing msoffcrypto package required for encryption/decryption"
            except Exception as e:
                return False, f"Error decrypting document: {str(e)}"
        
        # Remove the protection metadata file
        os.remove(metadata_path)
        return True, "Protection removed successfully"
    except Exception as e:
        return False, f"Error removing protection: {str(e)}"
