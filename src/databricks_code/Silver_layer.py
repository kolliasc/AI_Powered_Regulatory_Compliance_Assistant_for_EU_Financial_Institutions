# Silver_layer.py (Uploaded to Databricks)
import json
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType

spark = SparkSession.builder.getOrCreate()

silver_schema = StructType([
    StructField("chunk_id", StringType(), False),
    StructField("celex_id", StringType(), True),
    StructField("text_content", StringType(), True)
])

# Added /files/ into the path string
username = spark.sql("SELECT current_user()").collect()[0][0]
absolute_path = f"/Workspace/Users/{username}/bundle/ai-regulatory-assistant/files/data/silver_staging.json"

print(f"Loading staging data via memory buffer from: {absolute_path}")

# Read using standard Python open, then parse to Spark
with open(absolute_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Convert the raw dictionary list directly to a Spark DataFrame
silver_df = spark.createDataFrame(raw_data, schema=silver_schema)

target_table = "accenture2026dbcks.team2.silver_regulatory_chunks"
print(f"Writing to Delta Table: {target_table}")

silver_df.write.format("delta").mode("overwrite").saveAsTable(target_table)
print("Silver Delta Table updated successfully!")