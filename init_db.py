import pandas as pd
import ast
import asyncio

from database import engine, Base, AsyncSessionLocal
from models import Document
from elastic import create_index, add_document_to_elastic


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def load_data_from_csv(csv_path: str):
    await create_index()  # Создаем индекс в Elasticsearch

    df = pd.read_csv(csv_path)

    async with AsyncSessionLocal() as session:
        for index, row in df.iterrows():
            rubrics_list = ast.literal_eval(row['rubrics'])
            created_dt = pd.to_datetime(row['created_date']).to_pydatetime()

            # 1. Создаем запись для БД
            doc = Document(
                text=str(row['text']),
                rubrics=rubrics_list,
                created_date=created_dt
            )
            session.add(doc)
            await session.flush()  # Получаем doc.id от базы данных до commit'а

            # 2. Индексируем в Elasticsearch
            await add_document_to_elastic(doc_id=doc.id, text=doc.text)

        await session.commit()
        print("Данные успешно сохранены в PostgreSQL и Elasticsearch!")


async def main():
    await init_models()
    await load_data_from_csv("posts.csv")


if __name__ == "__main__":
    asyncio.run(main())