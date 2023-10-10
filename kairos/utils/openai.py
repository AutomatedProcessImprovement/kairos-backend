import os
from dotenv import load_dotenv

from langchain.agents import create_pandas_dataframe_agent, ZeroShotAgent, AgentExecutor
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.tools.python.tool import PythonAstREPLTool
from langchain.chains import LLMChain

import kairos.utils.event_log as log_utils

load_dotenv()

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

AGENTS = {}

llm_code = ChatOpenAI(temperature=0, openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo-16k-0613") 

prescirption_prompts = {
    "NEXT_ACTIVITY" : "NEXT_ACTIVITY: This is an algorithm which predicts the next activity of a case in a business process. Explain this output of the algorithm in a way that could be put in a user interface. In your response, include only the fields: Accuracy, Precision, Recall, and Explanation. In Explanation, use 480-520 characters and do not include the description of accuracy, precision, and recall. Do not include information about dates. Do not include name of the prediction model. Do not include anything about contacting the support team. Based on these rules, explain the following output: ",

    "ALARM": "This is an algorithm that calculates the probability of a negative outcome which is defined as output. Explain this output of the algorithm in a way that could be put in a user interface. In your response, include only the fields: Accuracy, Precision, Recall, and Explanation. Do not include information about dates. In Explanation, use 480-520 characters and do not include the description of accuracy, precision, and recall. Do not include name of the prediction model. Do not include anything about contacting the support team. Based on these rules, explain the following output: ",
    
    "TREATMENT_EFFECT": "There's an algorithm that produces an output defined as following. The output is an object with the following fields: proba_if_treated: The probability of a positive outcome if the case is treated. proba_if_untreated: The probability of a positive outcome if the case is not treated. cate: The Conditional Average Treatment Effect (CATE) score of the case. treatment: The treatment definition of the case. This is directly from the user’s previously inputted treatment definition. Given those definitions, explain if the following output is positive or negative in a way that could be put in a user interface. In your response, include only the fields: for proba_if_treated use Probability of a Positive Outcome if Recommendation Applied, for proba_if_untreated use Probability of a Positive Outcome if Recommendation is not Applied, CATE, and Explanation. In Explanation, use 480-520 characters. Do not include information about dates. Do not include the name of the prediction model. Do not include anything about contacting the support team.  Based on these rules, explain the following output: "
}

def create_pandas_agent(event_log_id,df,delimiter):
    # df = log_utils.get_dataframe_from_file(file,delimiter)
    if df.empty: 
        raise Exception('Could not read csv file.')

    chat_history_buffer = ConversationBufferMemory(
        memory_key="chat_history_buffer",
        input_key="input"
        )

    pd_agent = create_pandas_dataframe_agent(
        llm_code,
        df,
        max_execution_time=2.0,
        early_stopping_method="generate",
        agent_executor_kwargs={"memory": chat_history_buffer},
        input_variables=['df_head', 'input', 'agent_scratchpad', 'chat_history_buffer']
    )
    pd_agent.run('Say this is a test')
    AGENTS[event_log_id] = pd_agent
    print(AGENTS)
    return pd_agent

def create_python_agent(event_log_id):
    PREFIX = """Have a conversation with a human, answering the following questions as best you can. You have access to the following tools:"""
    SUFFIX = """Begin!"

    {chat_history}
    Question: {input}
    {agent_scratchpad}"""

    tools = [PythonAstREPLTool()]
    
    prompt = ZeroShotAgent.create_prompt(
        tools,
        prefix=PREFIX,
        suffix=SUFFIX,
        input_variables=["input", "chat_history", "agent_scratchpad"],
    )
    memory = ConversationBufferMemory(memory_key="chat_history")

    llm_chain = LLMChain(llm=llm_code, prompt=prompt)
    agent = ZeroShotAgent(llm_chain=llm_chain, tools=tools, verbose=True)
    agent_chain = AgentExecutor.from_agent_and_tools(
        agent=agent, tools=tools,max_execution_time=2.0, early_stopping_method="generate", memory=memory
    )
    AGENTS[event_log_id] = agent_chain
    return agent_chain

def get_agent(event_log_id):
    agent = AGENTS.get(event_log_id)

    if not agent:
        raise Exception(f'Agent for log {event_log_id} does not exist.')
    return agent

def save_openai_context(input,event_log_id=None,agent=None,output='Context saved.'):
    if not agent:
        if not event_log_id:
            raise Exception(f'Please provide event log id or the agent to save context.')
        agent = get_agent(event_log_id)
    agent.memory.save_context({'input':f'Save context: {input}'},{'output':output})
