import os.path
from llama_index import VectorStoreIndex, SimpleDirectoryReader, StorageContext, load_index_from_storage, download_loader

SIMPLE_MONGO_READER = download_loader('SimpleMongoReader')

HOST = "localhost"
PORT = "27017"
DB_NAME = "flask_db"
# query_dict is passed into db.collection.find()

def query_for_context(collection,query):
    query_dict = {}
    reader = SIMPLE_MONGO_READER(HOST, PORT)

    # check if storage already exists
    if (not os.path.exists('./storage')):
        # load the documents and create the index
        # documents = SimpleDirectoryReader('data').load_data()
        documents = reader.load_data(DB_NAME, collection, query_dict=query_dict)
        index = VectorStoreIndex.from_documents(documents)
        # store it for later
        index.storage_context.persist()
    else:
        # load the existing index
        storage_context = StorageContext.from_defaults(persist_dir='./storage')
        index = load_index_from_storage(storage_context)

    # either way we can now query the index
    query_engine = index.as_query_engine()
    response = query_engine.query(query)
    print(response)