"""SQL Data Loader module for loading transformed data into the star schema.

Provides the SQLDataLoader class that handles bulk insertion into staging tables,
execution of the star schema load procedure, and row count validation.

Requirements: 5.1, 5.2
"""

import logging

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.pipeline.models import LoadResult

logger = logging.getLogger(__name__)


class SQLDataLoader:
    """Loads transformed DataFrames into SQL staging and triggers star schema population.

    Uses SQLAlchemy for database connectivity and pandas for bulk insertion.
    """

    def __init__(self, connection_string: str):
        """Establish database connection.

        Args:
            connection_string: SQLAlchemy-compatible connection string.
        """
        self.connection_string = connection_string
        self.engine: Engine = create_engine(connection_string)

    def load_to_staging(self, df: pd.DataFrame, table_name: str) -> int:
        """Bulk insert DataFrame into the specified staging table.

        Uses pandas to_sql with 'replace' to ensure idempotent loads —
        the staging table is refreshed each run.

        Args:
            df: The DataFrame to load into the staging table.
            table_name: Name of the target staging table.

        Returns:
            The number of rows inserted.
        """
        row_count = len(df)
        logger.info("Loading %d rows into staging table '%s'", row_count, table_name)

        df.to_sql(
            name=table_name,
            con=self.engine,
            if_exists="replace",
            index=False,
        )

        logger.info("Successfully loaded %d rows into '%s'", row_count, table_name)
        return row_count

    def execute_load_procedure(self) -> LoadResult:
        """Call the sp_load_star_schema stored procedure.

        Executes the procedure and parses the result set to build a LoadResult
        containing rows_inserted, rows_updated, rows_rejected, and success status.

        Returns:
            LoadResult with counts and success flag.
        """
        logger.info("Executing stored procedure sp_load_star_schema")

        with self.engine.connect() as connection:
            result = connection.execute(text("EXEC sp_load_star_schema"))
            row = result.fetchone()

            if row is not None:
                rows_inserted = int(row[0]) if row[0] is not None else 0
                rows_updated = int(row[1]) if row[1] is not None else 0
                rows_rejected = int(row[2]) if row[2] is not None else 0
                success = bool(row[3]) if len(row) > 3 and row[3] is not None else True
            else:
                rows_inserted = 0
                rows_updated = 0
                rows_rejected = 0
                success = True

            connection.commit()

        load_result = LoadResult(
            rows_inserted=rows_inserted,
            rows_updated=rows_updated,
            rows_rejected=rows_rejected,
            success=success,
        )

        logger.info(
            "Procedure completed: inserted=%d, updated=%d, rejected=%d, success=%s",
            load_result.rows_inserted,
            load_result.rows_updated,
            load_result.rows_rejected,
            load_result.success,
        )

        return load_result

    def validate_row_counts(self, source_count: int, staging_count: int) -> bool:
        """Compare source and staging row counts to verify data integrity.

        Args:
            source_count: Number of rows in the source DataFrame.
            staging_count: Number of rows loaded into the staging table.

        Returns:
            True if counts match, False otherwise.
        """
        if source_count == staging_count:
            logger.info(
                "Row count validation passed: source=%d, staging=%d",
                source_count,
                staging_count,
            )
            return True
        else:
            logger.warning(
                "Row count mismatch: source=%d, staging=%d (difference=%d)",
                source_count,
                staging_count,
                abs(source_count - staging_count),
            )
            return False
