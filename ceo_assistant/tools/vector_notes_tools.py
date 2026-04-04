from __future__ import annotations

import json
import os
import uuid

from google.cloud import aiplatform, storage
from vertexai.language_models import TextEmbeddingModel

PROJECT_ID  = os.environ["GCP_PROJECT_ID"]
LOCATION    = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
BUCKET_NAME = os.environ.get("NOTES_BUCKET", "megacorp-meeting-notes")
INDEX_ID    = os.environ.get("VECTOR_INDEX_ID", "")
ENDPOINT_ID = os.environ.get("VECTOR_ENDPOINT_ID", "")
METADATA_BLOB = "metadata/notes_metadata.json"


def _gcs():
    return storage.Client(project=PROJECT_ID)

def _bucket():
    return _gcs().bucket(BUCKET_NAME)

def _embedding_model():
    return TextEmbeddingModel.from_pretrained("text-embedding-004")

def _load_metadata():
    blob = _bucket().blob(METADATA_BLOB)
    if not blob.exists():
        return {}
    return json.loads(blob.download_as_text())

def _save_metadata(metadata):
    blob = _bucket().blob(METADATA_BLOB)
    blob.upload_from_string(json.dumps(metadata, indent=2), content_type="application/json")


def upload_meeting_note(title: str, date: str, attendees: str, content: str) -> str:
    """Upload a meeting note, embed it, and store in Vertex AI Vector Search.

    Args:
        title: Meeting title.
        date: Date in YYYY-MM-DD format.
        attendees: Comma-separated list of attendees.
        content: Full meeting note text including decisions and action items.

    Returns:
        Confirmation with the note ID.
    """
    try:
        note_id  = str(uuid.uuid4())
        raw_text = f"Title: {title}\nDate: {date}\nAttendees: {attendees}\n\n{content}"

        # 1. Store raw text in GCS
        _bucket().blob(f"notes/{note_id}.txt").upload_from_string(raw_text, content_type="text/plain")

        # 2. Generate embedding
        embedding = _embedding_model().get_embeddings([raw_text])[0].values

        # 3. Store embedding JSON in GCS
        _bucket().blob(f"embeddings/{note_id}.json").upload_from_string(
            json.dumps({"id": note_id, "embedding": embedding}),
            content_type="application/json",
        )

        # 4. Update metadata
        metadata = _load_metadata()
        metadata[note_id] = {
            "title": title, "date": date, "attendees": attendees, "content": content,
        }
        _save_metadata(metadata)

        # 5. Upsert into Vector Search index
        if INDEX_ID:
            aiplatform.init(project=PROJECT_ID, location=LOCATION)
            index = aiplatform.MatchingEngineIndex(index_name=INDEX_ID)
            index.upsert_datapoints(
                datapoints=[{"datapoint_id": note_id, "feature_vector": embedding}]
            )

        return f"Note '{title}' uploaded and indexed with ID: {note_id}"
    except Exception as ex:
        return f"Failed to upload note: {ex}"


def search_meeting_notes(query: str, top_k: int = 3) -> str:
    """Semantically search meeting notes using Vertex AI Vector Search.

    Args:
        query: Natural language search query.
        top_k: Number of most relevant notes to return (default 3).

    Returns:
        Full content of the most relevant meeting notes.
    """
    try:
        embedding = _embedding_model().get_embeddings([query])[0].values
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        endpoint = aiplatform.MatchingEngineIndexEndpoint(index_endpoint_name=ENDPOINT_ID)
        response = endpoint.find_neighbors(
            deployed_index_id="megacorp_notes_index",
            queries=[embedding],
            num_neighbors=top_k,
        )
        neighbors = response[0] if response else []
        if not neighbors:
            return "No relevant meeting notes found."

        metadata = _load_metadata()
        results  = []
        for n in neighbors:
            note = metadata.get(n.id)
            if note:
                results.append(
                    f"**{note['title']}** ({note['date']}) [similarity: {round(n.distance, 3)}]\n"
                    f"Attendees: {note['attendees']}\n\n{note['content']}"
                )
        return "\n\n---\n\n".join(results) if results else "No notes found."
    except Exception as ex:
        return f"Search failed: {ex}"


def list_all_notes() -> str:
    """List all indexed meeting notes with titles and dates.

    Returns:
        Formatted list of available notes.
    """
    try:
        metadata = _load_metadata()
        if not metadata:
            return "No meeting notes have been uploaded yet."
        lines = [
            f"- [{v['date']}] {v['title']} (attendees: {v['attendees']})"
            for v in sorted(metadata.values(), key=lambda x: x["date"], reverse=True)
        ]
        return "Indexed meeting notes:\n" + "\n".join(lines)
    except Exception as ex:
        return f"Failed to list notes: {ex}"
