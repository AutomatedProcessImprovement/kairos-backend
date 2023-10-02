import os

from dotenv import load_dotenv

from langchain.llms import OpenAI
from langchain.agents import create_pandas_dataframe_agent
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType

import pandas as pd
import kairos.models.messages_model as messages_db

load_dotenv()

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)

prescirption_prompts = {
    "NEXT_ACTIVITY" : "NEXT_ACTIVITY: This is an algorithm which predicts the next activity of a case in a business process. Explain this output of the algorithm in a way that could be put in a user interface. In your response, include only the fields: Accuracy, Precision, Recall, and Explanation. In Explanation, use 480-520 characters and do not include the description of accuracy, precision, and recall. Do not include information about dates. Do not include name of the prediction model. Do not include anything about contacting the support team. Based on these rules, explain the following output: ",

    "ALARM": "This is an algorithm that calculates the probability of a negative outcome which is defined as output. Explain this output of the algorithm in a way that could be put in a user interface. In your response, include only the fields: Accuracy, Precision, Recall, and Explanation. Do not include information about dates. In Explanation, use 480-520 characters and do not include the description of accuracy, precision, and recall. Do not include name of the prediction model. Do not include anything about contacting the support team. Based on these rules, explain the following output: ",
    
    "TREATMENT_EFFECT": "There's an algorithm that produces an output defined as following. The output is an object with the following fields: proba_if_treated: The probability of a positive outcome if the case is treated. proba_if_untreated: The probability of a positive outcome if the case is not treated. cate: The Conditional Average Treatment Effect (CATE) score of the case. treatment: The treatment definition of the case. This is directly from the user’s previously inputted treatment definition. Given those definitions, explain if the following output is positive or negative in a way that could be put in a user interface. In your response, include only the fields: for proba_if_treated use Probability of a Positive Outcome if Recommendation Applied, for proba_if_untreated use Probability of a Positive Outcome if Recommendation is not Applied, CATE, and Explanation. In Explanation, use 480-520 characters. Do not include information about dates. Do not include the name of the prediction model. Do not include anything about contacting the support team.  Based on these rules, explain the following output: "
}

def load_csv(file,delimiter):
    df = pd.read_csv(file, delimiter=delimiter)
    agent = create_pandas_dataframe_agent(
        llm,
        df,
        verbose=True,
        agent_type=AgentType.OPENAI_FUNCTIONS,
    )
    

# def explain_prescription(prescription):
#     prompt = prescirption_prompts.get(prescription.get('type'))
#     if not prompt:
#         return None
#     content = prompt + str(prescription)
#     message = {'role': 'user','content': content}
#     return ask_ai(message)

# def ask_ai(message):
#     messages = messages_db.get_messages()
#     messages.append(message)

#     try:
#         chat = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
#     except Exception as e:
#         current_app.logger.error(f'Error in openAI call - {e}')
#         return None
    
#     reply_content = chat.get('choices')[0].get('message').get('content')
#     reply = {'role': 'assistant','content': reply_content}

#     messages_db.save_message(message)
#     message_id = messages_db.save_message(reply).inserted_id

#     return reply_content