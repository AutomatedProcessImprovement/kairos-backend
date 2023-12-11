from kairos.factory import create_app
from dotenv import load_dotenv
import os

load_dotenv()

app = create_app()
app.config["PRCORE_HEADERS"] = {"Authorization": os.getenv("PRCORE_TOKEN")}
app.config["PRCORE_BASE_URL"] = os.getenv("PRCORE_BASE_URL")
app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.config["OPENAI_ASSISTANT_ID"] = os.getenv("OPENAI_ASSISTANT_ID")
app.config["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")