import os

from llama_index import VectorStoreIndex, StorageContext, load_index_from_storage, download_loader, ServiceContext
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine
from llama_index.agent import OpenAIAgent
from llama_index.readers.schema.base import Document

import kairos.models.cases_model as cases_db


INDEX_SET = {}
AGENT_SET = {}
SERVICE_CONTEXT = ServiceContext.from_defaults(chunk_size=512)

def create_index_for_case(event_log_id,case_instance=None, case_id=None):
    if not case_instance:
        if not case_id:
            raise Exception("Please provide the case or a case instance.")
        case_instance = cases_db.get_case(case_id)
    case_instance = format_mongo_output(case_instance)

    storage_context = StorageContext.from_defaults()
    cur_index = VectorStoreIndex.from_documents(
        case_instance,
        service_context=SERVICE_CONTEXT,
        storage_context=storage_context,
    )
    storage_context.persist(persist_dir=f"./storage/{event_log_id}/{case_id}")
    if not INDEX_SET.get(str(event_log_id)):
        INDEX_SET[str(event_log_id)] = {}
    INDEX_SET[str(event_log_id)][case_id] = cur_index

def create_index_for_log(event_log_id):
    cases = cases_db.get_cases_by_log_id_and_completion(event_log_id,True)

    if len(cases) < 1:
        raise Exception(f"There are no completed cases for this log {event_log_id}.")
    INDEX_SET[str(event_log_id)] = {}
    for document in cases:
        create_index_for_case(event_log_id,case_instance=document,case_id=document['_id'])

def load_index_for_case(event_log_id,case_id):
    storage_context = StorageContext.from_defaults(
        persist_dir=f"./storage/{event_log_id}/{case_id}"
    )
    cur_index = load_index_from_storage(
        storage_context, service_context=SERVICE_CONTEXT
    )
    INDEX_SET[str(event_log_id)][case_id] = cur_index

def load_index_for_log(event_log_id):
    cases = os.listdir(f"./storage/{event_log_id}")
    INDEX_SET[str(event_log_id)] = {}
    for case_instance in cases:
        load_index_for_case(event_log_id,case_instance)


def create_sub_question_query_engine_for_log(event_log_id):
    if (not os.path.exists(f"./storage/{event_log_id}")):
        create_index_for_log(event_log_id)
    elif INDEX_SET == {}:
        load_index_for_log(event_log_id)

    cases = os.listdir(f"./storage/{event_log_id}")

    individual_query_engine_tools = [
        QueryEngineTool(
            query_engine=INDEX_SET[str(event_log_id)][case_instance].as_query_engine(),
            metadata=ToolMetadata(
                name=f"vector_index_{case_instance}",
                description=(
                    "useful for when you want to answer queries about case"
                    f" {case_instance} in event log {event_log_id}"
                ),
            ),
        )
        for case_instance in cases
    ]

    query_engine = SubQuestionQueryEngine.from_defaults(
        query_engine_tools=individual_query_engine_tools,
        service_context=SERVICE_CONTEXT,
    )

    query_engine_tool = QueryEngineTool(
        query_engine=query_engine,
        metadata=ToolMetadata(
            name="sub_question_query_engine",
            description=(
                "useful for when you want to answer queries that require analyzing"
                f" multiple cases in event log {event_log_id}"
            ),
        ),
    )

    tools = individual_query_engine_tools + [query_engine_tool]
    agent = OpenAIAgent.from_tools(tools, verbose=True)
    AGENT_SET[str(event_log_id)] = agent

def ask_ai(query, event_log_id):
    agent = AGENT_SET.get(event_log_id)
    if not agent:
        create_sub_question_query_engine_for_log(event_log_id)
        agent = AGENT_SET.get(event_log_id)

    response = agent.chat(query)
    return format_ai_response(response)

def format_mongo_output(output):
    if isinstance(output, list):
        documents = []
        for item in output:
            documents.append(Document(text=str(item)))
        return documents
    else:
        return [Document(text=str(output))]
    
def format_ai_response(response):
    parts = str(response).split("========================", 1)
    return parts[1] if len(parts) > 1 else parts[0]