"""
Intended execution environment: Azure Databricks with Unity Catalog.
"""
from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Define the explicit schema for the Bronze Ingestion Table
BRONZE_TABLE_SCHEMA = StructType([
    StructField("celex_id", StringType(), False),
    StructField("file_name", StringType(), False),
    StructField("file_path", StringType(), False),
    StructField("source_api", StringType(), False),
    StructField("status", StringType(), False),
    StructField("ingestion_timestamp", TimestampType(), False)
])

def ingest_metadata_to_bronze(spark: SparkSession, downloaded_files: list, catalog: str = "accenture2026dbcks", schema: str = "team2"):
    """
    Ingests metadata of downloaded PDF documents into the Bronze Delta Table using the PySpark Dataframe API.
    Target Environment: Azure Databricks Unity Catalog.
    """
    table_name = f"{catalog}.{schema}.bronze_regulatory_log"
    
    # Create the Bronze Delta Table if it does not exist within the managed schema
    spark.sql(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            celex_id STRING,
            file_name STRING,
            file_path STRING,
            source_api STRING,
            status STRING,
            ingestion_timestamp TIMESTAMP
        ) USING DELTA
    """)
    
    # Prepare local Python records from the input list using timezone-aware UTC datetime
    records = []
    for file_info in downloaded_files:
        records.append((
            file_info["celex_id"],
            file_info["file_name"],
            file_info["file_path"],
            "EUR-Lex",
            "RAW_DOWNLOADED",
            datetime.now(timezone.utc)
        ))
        
    if not records:
        print("No new records to ingest into the Bronze layer.")
        return

    # Create a base PySpark DataFrame from the Python records using the explicit schema
    input_df = spark.createDataFrame(records, schema=BRONZE_TABLE_SCHEMA)
    
    # PySpark Dataframe API transformation to enforce exact column selection and auditing
    final_bronze_df = input_df.select(
        input_df["celex_id"],
        input_df["file_name"],
        input_df["file_path"],
        input_df["source_api"],
        input_df["status"],
        current_timestamp().alias("ingestion_timestamp")
    )
    
    # Append the transformed DataFrame directly into the Delta Table via the PySpark Writer API
    final_bronze_df.write \
        .format("delta") \
        .mode("append") \
        .saveAsTable(table_name)
        
    print(f"Successfully appended {len(records)} metadata records to {table_name} using PySpark Dataframe API.")


if __name__ == "__main__":
    # Execution setup specifically configured for your Azure Databricks production workspace
    print("Initializing active SparkSession from Databricks cluster...")
    spark_session = SparkSession.builder.getOrCreate()
    
    # Production cloud layout mapping directly to your team2 Unity Catalog Volume
    production_files = [
        {"celex_id": "32022R2554", "file_name": "32022R2554_EN.pdf", "file_path": "/Volumes/accenture2026dbcks/team2/volume/32022R2554_EN.pdf"},
        {"celex_id": "32018L0843", "file_name": "32018L0843_EN.pdf", "file_path": "/Volumes/accenture2026dbcks/team2/volume/32018L0843_EN.pdf"},
        {"celex_id": "32014L0065", "file_name": "32014L0065_EN.pdf", "file_path": "/Volumes/accenture2026dbcks/team2/volume/32014L0065_EN.pdf"},
        {"celex_id": "32016R0679", "file_name": "32016R0679_EN.pdf", "file_path": "/Volumes/accenture2026dbcks/team2/volume/32016R0679_EN.pdf"},
        {"celex_id": "32024R1689", "file_name": "32024R1689_EN.pdf", "file_path": "/Volumes/accenture2026dbcks/team2/volume/32024R1689_EN.pdf"}
    ]
    
    # Execute the core Bronze ingestion function
    ingest_metadata_to_bronze(
        spark=spark_session,
        downloaded_files=production_files,
        catalog="accenture2026dbcks",
        schema="team2"
    )