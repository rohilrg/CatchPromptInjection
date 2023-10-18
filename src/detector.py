import json
import logging
import statistics
from rebuff import Rebuff
from transformers import Pipeline
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.output_parser import StrOutputParser


class PromptInjectionDetector:
    """
    Class to detect prompt injection using a two-step sanity check approach.
    """

    def __init__(self, config_path: str):
        """
        Initializes the PromptInjectionDetector instance.

        Parameters:
            config_path (str): Path to the configuration file.
        """
        self.config = json.load(open(config_path, "r"))
        self.first_sanity_check_pipeline = self._model_default_factory()

    def _model_default_factory(self) -> Pipeline:
        """
        Returns a default pipeline for text classification.

        Returns:
            Pipeline: Default text classification pipeline.
        """
        try:
            from transformers import pipeline
        except ImportError as e:
            raise ImportError(
                "Cannot import transformers, please install with "
                "`pip install transformers`."
            ) from e
        return pipeline(
            "text-classification", model="deepset/deberta-v3-base-injection"
        )

    def first_sanity_check_invoker(self) -> dict:
        """
        Invokes the first sanity check for prompt injection detection.

        Returns:
            dict: Result of the first sanity check.
        """
        query = self.request["query"]
        response = self.first_sanity_check_pipeline(query)
        if (
            response[0]["label"] == "INJECTION"
            and response[0]["score"] >= self.config["FIRST_SANITY_CHECK_THRESHOLD"]
        ):
            return {
                "Input query is": "PROMPT INJECTION",
                "return": True,
                "Confidence level:": response[0]["score"],
            }
        elif (
            response[0]["label"] == "INJECTION"
            and response[0]["score"] < self.config["FIRST_SANITY_CHECK_THRESHOLD"]
        ):
            return {
                "Input query is": "MAYBE INJECTION",
                "return": False,
                "Confidence level:": response[0]["score"],
            }
        else:
            return {
                "Input query is": "LEGIT",
                "return": False,
                "Confidence level:": response[0]["score"],
            }

    def set_rebuff(self):
        """
        Sets up Rebuff with the provided API token and URL.

        Returns:
            Rebuff: Rebuff instance.
        """
        rb = Rebuff(
            api_token=self.config["REBUFF_API"], api_url=self.config["REBUFF_URL"]
        )
        return rb

    def second_sanity_check_invoker(self):
        """
        Invokes the second sanity check for prompt injection detection.

        Returns:
            dict: Result of the second sanity check.
        """
        rb = self.set_rebuff()
        response = rb.detect_injection(
            self.request["query"],
            max_heuristic_score=self.config["REBUFF_SETTINGS"]["MAX_HEURISTIC_SCORE"],
            max_vector_score=self.config["REBUFF_SETTINGS"]["MAX_VECTOR_SCORE"],
            max_model_score=self.config["REBUFF_SETTINGS"]["MAX_MODEL_SCORE"],
            check_heuristic=bool(self.config["REBUFF_SETTINGS"]["CHECK_HEURISTIC"]),
            check_vector=bool(self.config["REBUFF_SETTINGS"]["CHECK_VECTOR"]),
            check_llm=bool(self.config["REBUFF_SETTINGS"]["CHECK_LLM"]),
        )
        response = json.loads(response.model_dump_json())
        mean_score = statistics.mean(
            [
                response["heuristicScore"],
                response["modelScore"],
                response["vectorScore"]["topScore"],
            ]
        )

        injectionDetected = response["injectionDetected"]
        metrics_value = {
            "heuristicScore": response["heuristicScore"],
            "modelScore": response["modelScore"],
            "vectorScore": response["vectorScore"]["topScore"],
            "mean_score": mean_score,
        }
        if injectionDetected:
            return {
                "Input query is": "PROMPT INJECTION",
                "return": True,
                "Confidence level:": metrics_value,
            }
        else:
            return {
                "Input query is": "LEGIT",
                "return": False,
                "Confidence level:": metrics_value,
            }

    def process_query(self, request):
        """
        Processes a query and determines if it contains prompt injection.

        Parameters:
            request: The query request.

        Returns:
            dict: The AI response and associated metadata.
        """
        self.request = request
        logging.info("First sanity check in progress!!")
        first_response = self.first_sanity_check_invoker()

        if first_response["return"]:
            logging.info("First sanity check detected Injection")
            return {
                "AIResponse:": "Prompt Injection detected, please don't trick this model for unwanted results.",
                "Sanity Check of input done by": "dedicated model, step first.",
                "metadata": {
                    "Confidence level:": first_response["Confidence level:"],
                    "Input query is": first_response["Input query is"],
                },
            }
        else:
            logging.info("First sanity passed. Moving to second sanity check!!")
            second_response = self.second_sanity_check_invoker()
            if (
                second_response["return"]
                and second_response["Confidence level:"]["mean_score"]
                > self.config["SECOND_SANITY_CHECK_THRESHOLD"]
            ):
                logging.info("Second sanity detected Injection")
                return {
                    "AIResponse:": "Prompt Injection detected, please don't trick this model for unwanted results.",
                    "Sanity Check of input done by": "Rebuff API, step second",
                    "metadata": {
                        "Confidence level:": second_response["Confidence level:"],
                        "Input query is": second_response["Input query is"],
                    },
                }
            else:
                logging.info("No injection detected, providing query to LLM")
                prompt = ChatPromptTemplate.from_template("Tell me a joke about {foo}")
                model = ChatOpenAI(
                    model_name="gpt-3.5-turbo",
                    openai_api_key=self.config["OPENAI_API_KEY"],
                    temperature=0.7,
                )
                chain = prompt | model | StrOutputParser()
                response = chain.invoke({"foo": f"{self.request['query']}"})
                return {
                    "AIResponse:": response.replace("\n", " "),
                    "Sanity Check of input done by": "none of the methods.",
                    "metadata": {
                        "Confidence level:": "Not produced",
                        "Input query is": "LEGIT",
                    },
                }
