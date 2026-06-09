# Gold_delta_table.py (Uploaded to Databricks)
import json
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, ArrayType, FloatType

spark = SparkSession.builder.getOrCreate()

gold_schema = StructType([
    StructField("chunk_id", StringType(), False),
    StructField("celex_id", StringType(), True),
    StructField("text_content", StringType(), True),
    StructField("embeddings", ArrayType(FloatType()), True)
])

# Added /files/ into the path string
username = spark.sql("SELECT current_user()").collect()[0][0]
absolute_path = f"/Workspace/Users/{username}/bundle/ai-regulatory-assistant/files/data/gold_staging.json"
print(f"Loading staging data via memory buffer from: {absolute_path}")

# Read using standard Python open, then parse to Spark
with open(absolute_path, "r", encoding="utf-8") as f:
    raw_data = json.load(f)

# Convert the raw dictionary list directly to a Spark DataFrame
gold_df = spark.createDataFrame(raw_data, schema=gold_schema)

target_table = "accenture2026dbcks.team2.gold_regulatory_embeddings"
print(f"Writing to Delta Table: {target_table}")

gold_df.write.format("delta").mode("overwrite").saveAsTable(target_table)
print("Gold Delta Table updated successfully!")