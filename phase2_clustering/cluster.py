import pandas as pd
import json
import os
import chromadb
import hdbscan
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import euclidean_distances

def main():
    # 1. Load the pruned data
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(base_dir, '..', 'phase1_ingestion', 'output', 'cleaned_reviews.csv')
    
    if not os.path.exists(input_file):
        print(f"Error: Could not find {input_file}")
        return

    print("Loading pruned reviews...")
    df = pd.read_csv(input_file)
    
    if len(df) == 0:
        print("Dataset is empty. Exiting.")
        return
        
    reviews_list = df['review_text'].tolist()
    ids_list = df['id'].astype(str).tolist()
    
    # 2. Setup Embeddings
    print("Loading embedding model BAAI/bge-small-en-v1.5...")
    model = SentenceTransformer('BAAI/bge-small-en-v1.5')
    
    print("Generating embeddings (this may take a moment)...")
    embeddings = model.encode(reviews_list)
    
    # 3. Store in ChromaDB Ephemeral Client
    print("Storing embeddings in ChromaDB...")
    client = chromadb.EphemeralClient()
    collection = client.create_collection(name="groww_reviews")
    
    collection.add(
        documents=reviews_list,
        embeddings=embeddings.tolist(),
        ids=ids_list,
        metadatas=[{"rating": row['rating'], "source": row['source']} for _, row in df.iterrows()]
    )
    
    # 4. Cluster with HDBSCAN
    print("Clustering using HDBSCAN...")
    # Normalize embeddings for better Euclidean distance behavior
    embeddings_norm = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    
    # We lower min_cluster_size to 5 and min_samples to 2 to prevent everything from being noise
    clusterer = hdbscan.HDBSCAN(min_cluster_size=5, min_samples=2, metric='euclidean', cluster_selection_method='eom')
    cluster_labels = clusterer.fit_predict(embeddings_norm)
    
    df['cluster'] = cluster_labels
    
    # 5. Extract top 5 clusters (ignore noise cluster -1)
    # Get cluster sizes, excluding -1
    cluster_counts = df[df['cluster'] != -1]['cluster'].value_counts()
    top_clusters = cluster_counts.head(5).index.tolist()
    
    print(f"Top 5 clusters found: {top_clusters}")
    
    output_data = {}
    
    # Extract 20 most central reviews per cluster
    for cluster_id in top_clusters:
        # Get indices of reviews in this cluster
        cluster_indices = df.index[df['cluster'] == cluster_id].tolist()
        
        # Get embeddings for this cluster
        cluster_embeddings = embeddings[cluster_indices]
        
        # Calculate cluster centroid
        centroid = np.mean(cluster_embeddings, axis=0).reshape(1, -1)
        
        # Calculate distance of each point to the centroid
        distances = euclidean_distances(cluster_embeddings, centroid).flatten()
        
        # Add distances to the cluster dataframe
        cluster_df = df.iloc[cluster_indices].copy()
        cluster_df['distance_to_centroid'] = distances
        
        # Sort by distance (closest to centroid first)
        cluster_df = cluster_df.sort_values(by='distance_to_centroid')
        
        # Sample top 20
        top_20 = cluster_df.head(20)
        
        # Store in dict
        output_data[f"Cluster_{cluster_id}"] = top_20['review_text'].tolist()
        
    # 6. Save JSON
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'clusters.json')
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)
        
    print(f"Successfully extracted {len(output_data)} clusters with up to 20 central reviews each.")
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
