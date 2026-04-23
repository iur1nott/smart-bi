"""
File Repository Implementation - PostgreSQL-based file metadata persistence.
Handles files, sheets, and columns metadata.
"""

from typing import List, Optional
from datetime import datetime
import logging
import uuid

from domain.entities import File, FileSheet, SheetColumn
from infrastructure.database import Database, get_database
from infrastructure.models import FileModel, FileSheetModel, SheetColumnModel

logger = logging.getLogger(__name__)


class FileRepositoryImpl:
    """
    PostgreSQL implementation for file metadata persistence.
    Handles files, sheets, and columns using SQLAlchemy ORM.
    """

    def __init__(self, database: Optional[Database] = None):
        """
        Initialize the repository with a database connection.

        Args:
            database: Optional Database instance. Uses global instance if not provided.
        """
        self._db = database or get_database()

    # File operations
    def save_file(self, file: File) -> bool:
        """
        Save a file and its sheets/columns to the database.

        Args:
            file: The file entity to save (with sheets and columns)

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                # Check if file exists
                existing = (
                    session.query(FileModel)
                    .filter(FileModel.file_id == file.file_id)
                    .first()
                )

                if existing:
                    # Update existing file
                    existing.file_name = file.file_name
                    existing.storage_path = file.storage_path
                    existing.file_size_kb = file.file_size_kb
                else:
                    # Create new file
                    model = FileModel(
                        file_id=file.file_id,
                        user_id=file.user_id,
                        file_name=file.file_name,
                        storage_path=file.storage_path,
                        file_size_kb=file.file_size_kb,
                        uploaded_at=file.uploaded_at,
                    )
                    session.add(model)

                # Save sheets and columns
                for sheet in file.sheets:
                    self._save_sheet_internal(session, sheet)

                return True

        except Exception as e:
            logger.error(f"Error saving file {file.file_id}: {e}")
            return False

    def _save_sheet_internal(self, session, sheet: FileSheet) -> None:
        """Save a sheet and its columns within an existing session."""
        existing = (
            session.query(FileSheetModel)
            .filter(FileSheetModel.sheet_id == sheet.sheet_id)
            .first()
        )

        if existing:
            existing.sheet_name = sheet.sheet_name
        else:
            sheet_model = FileSheetModel(
                sheet_id=sheet.sheet_id,
                file_id=sheet.file_id,
                sheet_name=sheet.sheet_name,
            )
            session.add(sheet_model)

        # Save columns
        for column in sheet.columns:
            self._save_column_internal(session, column)

    def _save_column_internal(self, session, column: SheetColumn) -> None:
        """Save a column within an existing session."""
        existing = (
            session.query(SheetColumnModel)
            .filter(SheetColumnModel.column_id == column.column_id)
            .first()
        )

        if existing:
            existing.column_name = column.column_name
            existing.data_type = column.data_type
        else:
            column_model = SheetColumnModel(
                column_id=column.column_id,
                sheet_id=column.sheet_id,
                column_name=column.column_name,
                data_type=column.data_type,
            )
            session.add(column_model)

    def find_file_by_id(self, file_id: str) -> Optional[File]:
        """
        Find a file by its ID.

        Args:
            file_id: The unique identifier of the file

        Returns:
            File entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(FileModel)
                    .filter(FileModel.file_id == file_id)
                    .first()
                )

                if model:
                    return self._file_model_to_entity(session, model)
                return None

        except Exception as e:
            logger.error(f"Error finding file by ID {file_id}: {e}")
            return None

    def find_files_by_user(self, user_id: str) -> List[File]:
        """
        Find all files for a user.

        Args:
            user_id: The user ID to search for

        Returns:
            List of File entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(FileModel)
                    .filter(FileModel.user_id == user_id)
                    .order_by(FileModel.uploaded_at.desc())
                    .all()
                )

                return [self._file_model_to_entity(session, m) for m in models]

        except Exception as e:
            logger.error(f"Error finding files for user {user_id}: {e}")
            return []

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from the database.
        Cascade deletes sheets and columns.

        Args:
            file_id: The unique identifier of the file to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(FileModel)
                    .filter(FileModel.file_id == file_id)
                    .first()
                )

                if model:
                    session.delete(model)
                    return True
                return False

        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False

    # Sheet operations
    def find_sheet_by_id(self, sheet_id: str) -> Optional[FileSheet]:
        """
        Find a sheet by its ID with columns.

        Args:
            sheet_id: The unique identifier of the sheet

        Returns:
            FileSheet entity if found, None otherwise
        """
        try:
            with self._db.session_scope() as session:
                model = (
                    session.query(FileSheetModel)
                    .filter(FileSheetModel.sheet_id == sheet_id)
                    .first()
                )

                if model:
                    return self._sheet_model_to_entity(session, model)
                return None

        except Exception as e:
            logger.error(f"Error finding sheet by ID {sheet_id}: {e}")
            return None

    def find_sheets_by_file(self, file_id: str) -> List[FileSheet]:
        """
        Find all sheets for a file.

        Args:
            file_id: The file ID to search for

        Returns:
            List of FileSheet entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(FileSheetModel)
                    .filter(FileSheetModel.file_id == file_id)
                    .all()
                )

                return [self._sheet_model_to_entity(session, m) for m in models]

        except Exception as e:
            logger.error(f"Error finding sheets for file {file_id}: {e}")
            return []

    # Column operations
    def find_columns_by_sheet(self, sheet_id: str) -> List[SheetColumn]:
        """
        Find all columns for a sheet.

        Args:
            sheet_id: The sheet ID to search for

        Returns:
            List of SheetColumn entities
        """
        try:
            with self._db.session_scope() as session:
                models = (
                    session.query(SheetColumnModel)
                    .filter(SheetColumnModel.sheet_id == sheet_id)
                    .all()
                )

                return [self._column_model_to_entity(m) for m in models]

        except Exception as e:
            logger.error(f"Error finding columns for sheet {sheet_id}: {e}")
            return []

    # Model to Entity converters
    def _file_model_to_entity(self, session, model: FileModel) -> File:
        """Convert a FileModel to a File entity with sheets."""
        # Load sheets
        sheets = (
            session.query(FileSheetModel)
            .filter(FileSheetModel.file_id == model.file_id)
            .all()
        )

        return File(
            file_id=str(model.file_id),
            user_id=str(model.user_id),
            file_name=model.file_name,
            storage_path=model.storage_path,
            file_size_kb=model.file_size_kb,
            uploaded_at=model.uploaded_at,
            sheets=[self._sheet_model_to_entity(session, s) for s in sheets],
        )

    def _sheet_model_to_entity(self, session, model: FileSheetModel) -> FileSheet:
        """Convert a FileSheetModel to a FileSheet entity with columns."""
        # Load columns
        columns = (
            session.query(SheetColumnModel)
            .filter(SheetColumnModel.sheet_id == model.sheet_id)
            .all()
        )

        return FileSheet(
            sheet_id=str(model.sheet_id),
            file_id=str(model.file_id),
            sheet_name=model.sheet_name,
            columns=[self._column_model_to_entity(c) for c in columns],
        )

    def _column_model_to_entity(self, model: SheetColumnModel) -> SheetColumn:
        """Convert a SheetColumnModel to a SheetColumn entity."""
        return SheetColumn(
            column_id=str(model.column_id),
            sheet_id=str(model.sheet_id),
            column_name=model.column_name,
            data_type=model.data_type,
        )
