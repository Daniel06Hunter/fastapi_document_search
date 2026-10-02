from elasticsearch import AsyncElasticsearch


ELASTIC_URL = "http://localhost:9200"
INDEX_NAME = "documents_index"

es_client = AsyncElasticsearch(ELASTIC_URL)


async def create_index():
    exists = await es_client.indices.exists(index=INDEX_NAME)
    if not exists:
        await es_client.indices.create(
            index=INDEX_NAME,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "text": {"type": "text"}
                    }
                }
            }
        )
        print(f"Индекс {INDEX_NAME} успешно создан.")


async def add_document_to_elastic(doc_id: int, text: str):
    await es_client.index(
        index=INDEX_NAME,
        id=str(doc_id),
        document={
            "id": doc_id,
            "text": text
        }
    )


async def search_in_elastic(query_text: str, limit: int = 20) -> list[int]:

    response = await es_client.search(
        index=INDEX_NAME,
        body={
            "size": limit,
            "query": {
                "match": {
                    "text": query_text
                }
            }
        }
    )


    hits = response["hits"]["hits"]
    doc_ids = [int(hit["_source"]["id"]) for hit in hits]
    return doc_ids


async def delete_document_from_elastic(doc_id: int):
    try:
        await es_client.delete(index=INDEX_NAME, id=str(doc_id))
    except Exception as e:
        print(f"Ошибка при удалении из Elasticsearch (ID {doc_id}): {e}")