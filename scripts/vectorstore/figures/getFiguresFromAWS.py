import boto3
import re
import pandas as pd
from dotenv import load_dotenv
import os

# Takes in a bucket name and source name, outputs a dataframe containing the figures, their s3 keys and their urls.

def get_figures_from_source(bucket_name, source_name): # e.g. source_name = 'MMD-Figures/'. Should correspond to folder in s3 bucket.
  # Load environment variables from the .env file
  load_dotenv()
  aws_access_key_id= os.getenv("AWS_ACCESS_KEY_ID")
  aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")

  # Create AWS s3 client
  s3 = boto3.client('s3',
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)

  s3_objects = s3.list_objects_v2(Bucket=bucket_name, Prefix=source_name)
  
  # Prepare to get metadata
  figure_numbers = []
  image_keys = []
  image_urls = []
  
  # Check if the bucket is empty
  if 'Contents' not in s3_objects:
    print(f"No objects found in bucket '{bucket_name}' with prefix '{source_name}', please check your s3 bucket and make sure folder exists.")
    return 
  
  for obj in s3_objects['Contents']:
    print(obj["Key"])
    file_type = obj["Key"][-3:]
    img_key = obj["Key"]

    if file_type == 'png' or file_type == 'jpg' or file_type == 'peg': #Make sure object is an image
      figure_number = int(re.search(r'img_(\d+)', img_key).group(1))
      img_url = f'https://{bucket_name}.s3.us-east-1.amazonaws.com/{img_key}'

      figure_numbers.append(figure_number)
      image_keys.append(img_key)
      image_urls.append(img_url)

    else:
      print(f'File type {file_type} not supported. Skipping {img_key}')
      continue

  data = {
      'Source': source_name,
      'Type': 'Image',
      'Text Content': 'NA',
      'Figure Number': figure_numbers,
      'Image Key': image_keys,
      'Image URL': image_urls,
  }
  
  df = pd.DataFrame(data)
  return df
