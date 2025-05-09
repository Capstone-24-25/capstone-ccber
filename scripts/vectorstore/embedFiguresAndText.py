import pandas as pd
from qdrant_client.http import models as rest
from tqdm.auto import tqdm
import uuid
import os
from utils.client_provider import ClientProvider  

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME")           # Choose your collection name
BATCH_SIZE = 10                                     # Batch size for uploads

qdrant_client = ClientProvider.get_qdrant_client()
embeddings = ClientProvider.get_embeddings()

def create_collection_if_not_exists(collection_name, vector_size=1536):
    """Create collection if it doesn't exist"""
    collections = qdrant_client.get_collections().collections
    collection_names = [collection.name for collection in collections]
    
    if collection_name not in collection_names:
        print(f"Creating collection '{collection_name}'...")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=rest.VectorParams(
                size=vector_size,
                distance=rest.Distance.COSINE
            )
        )
        print(f"Collection '{collection_name}' created successfully!")
    else:
        print(f"Collection '{collection_name}' already exists.")

def upload_to_qdrant(df):
    """Upload data from dataframe to Qdrant"""
    
    # First create collection if needed
    create_collection_if_not_exists(COLLECTION_NAME)
    
    total_rows = len(df)
    print(f"Processing {total_rows} records...")
    
    # Process in batches
    for i in tqdm(range(0, total_rows, BATCH_SIZE)):
        batch_df = df.iloc[i:i + BATCH_SIZE]
        
        # Prepare points for this batch
        points = []
        
        for _, row in batch_df.iterrows():
            # Determine the content to embed based on type
            if pd.notna(row['Text Content']):
                content_to_embed = row['Text Content']
                content_type = 'text_chunk'
            elif pd.notna(row['Image Description']):
                content_to_embed = row['Image Description']
                content_type = 'image_description'
            else:
                print(f"Warning: Row has no content to embed: {row}")
                continue
                
            # Create embedding
            embedding_vector = embeddings.embed_query(content_to_embed)
            
            # Create point ID
            point_id = str(uuid.uuid4())
            
            # Create metadata payload
            payload = {
                "source": row['Source'] if pd.notna(row['Source']) else '',
                "page_number": int(row['Page Number']) if pd.notna(row['Page Number']) else None,
                "type": row['Type'] if pd.notna(row['Type']) else '',
                "content_type": content_type,
                "text_content": row['Text Content'] if pd.notna(row['Text Content']) else '',
                # Store image-specific data when available
                "figure_number": int(row['Figure Number']) if pd.notna(row['Figure Number']) else None,
                "image_key": row['Image Key'] if pd.notna(row['Image Key']) else '',
                "image_url": row['Image URL'] if pd.notna(row['Image URL']) else '',
                "image_description": row['Image Description'] if pd.notna(row['Image Description']) else ''
            }
            
            # Add point to batch
            points.append(rest.PointStruct(
                id=point_id,
                vector=embedding_vector,
                payload=payload
            ))
        
        # Upload batch to Qdrant
        if points:
            qdrant_client.upsert(
                collection_name=COLLECTION_NAME,
                points=points
            )
            print(f"Batch of {len(points)} points uploaded successfully!")
        else:
            print("No valid points in this batch.")
    
    print(f"Upload complete! {total_rows} records processed.")

def verify_upload():
    """Verify the upload by counting points in collection"""
    collection_info = qdrant_client.get_collection(COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' contains {collection_info.vectors_count} points.")

# Main execution
if __name__ == "__main__":
    # Load dataframe with all of our embedding data
    df = pd.read_csv('data/dataframesForEmbeddings/combined_data.csv')  
    
    # Upload data to Qdrant
    upload_to_qdrant(df)
    
    # Verify the upload
    verify_upload()
    
