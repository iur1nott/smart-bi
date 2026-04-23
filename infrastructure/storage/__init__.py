"""
Storage Module - File storage operations for S3/Supabase.
Provides abstraction layer for file storage operations.
"""

from .s3_client import S3Client, get_s3_client

__all__ = ["S3Client", "get_s3_client"]
