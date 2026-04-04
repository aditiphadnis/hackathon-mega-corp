# create_vector_index.py
from google.cloud import aiplatform

aiplatform.init(project="ai-agent-use-cases-485910", location="us-central1")

index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="megacorp-notes-index",
    dimensions=768,
    approximate_neighbors_count=10,
    distance_measure_type="COSINE_DISTANCE",
    index_update_method="STREAM_UPDATE",
    leaf_node_embedding_count=500,        # ← add this
    leaf_nodes_to_search_percent=7,       # ← add this
)
print("INDEX ID:", index.name)

endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="megacorp-notes-endpoint",
    public_endpoint_enabled=True,
)
endpoint.deploy_index(
    index=index,
    deployed_index_id="megacorp_notes_index",
    min_replica_count=1,
    max_replica_count=1,
)
print("ENDPOINT ID:", endpoint.name)