from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI
from langchain.schema.output_parser import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import LLMChain
from pathlib import Path
import json
import os
import logging
from rebuff import Rebuff

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from transformers import Pipeline



class PromptInjectionDetector:

    def __int__(self, config_path: str,
                request: dict):
        self.config = json.load(open(config_path, 'r'))
        self.request = request
        self.first_sanity_check_pipeline = self._model_default_factory()

        # add as the env variable
        os.environ['OPENAI_API_KEY'] = self.config['OPENAI_API_KEY']

    def _model_default_factory(self) -> Pipeline:
        try:
            from transformers import pipeline
        except ImportError as e:
            raise ImportError(
                "Cannot import transformers, please install with "
                "`pip install transformers`."
            ) from e
        return pipeline("text-classification", model="deepset/deberta-v3-base-injection")
    def first_sanity_check_invoker(self) -> dict:
        query = self.request["query"]
        response = self.first_sanity_check_pipeline(query)
        if response[0]["label"] == "INJECTION" and response[0]["score"] >= self.config["FIRST_SANITY_CHECK_THRESHOLD"]:
            return {"label": "Very likely Injection", "return": True, "metrics_obtained": response[0]["score"]}
        elif response[0]["label"] == "INJECTION" and response[0]["score"] < self.config["FIRST_SANITY_CHECK_THRESHOLD"]:
            return {"label": "MAYBE INJECTION", "return": False, "metrics_obtained": response[0]["score"]}
        else:
            return {"label": "LEGIT", "return": False, "metrics_obtained": response[0]["score"]}

    def set_rebuff(self):
        # Set up Rebuff with your playground.rebuff.ai API key, or self-host Rebuff
        rb = Rebuff(api_token=self.config["REBUFF_API"], api_url=self.config["REBUFF_URL"])
        return rb

    def second_sanity_check_invoker(self):

        rb = self.set_rebuff()

        response = rb.detect_injection(self.request["query"],
                                       max_heuristic_score=self.config["REBUFF_SETTINGS"]["MAX_HEURISTIC_SCORE"],
                                       max_vector_score=self.config["REBUFF_SETTINGS"]["MAX_VECTOR_SCORE"],
                                       max_model_score=self.config["REBUFF_SETTINGS"]["MAX_MODEL_SCORE"],
                                       check_heuristic=bool(self.config["REBUFF_SETTINGS"]["CHECK_HEURISTIC"]),
                                       check_vector=bool(self.config["REBUFF_SETTINGS"]["CHECK_VECTOR"]),
                                       check_llm=bool(self.config["REBUFF_SETTINGS"]["CHECK_LLM"])
                                       )
        response = json.loads(response.model_dump_json())
        injectionDetected = response['injectionDetected']
        metrics_value = {"heuristicScore":response['heuristicScore'],
                        "modelScore": response["modelScore"],
                        "vectorScore": response["vectorScore"]["topScore"]}

        if injectionDetected:
            return {"label": "INJECTION", "return": True, "metrics_obtained": metrics_value}
        else:
            return {"label": "LEGIT", "return": False, "metrics_obtained": metrics_value}


    def process_query(self):
        """
        Receives a query string and returns the response from the loaded LLM model.

        Parameters:
            request (str): query string

        Returns:
            response (dict): API response (see readme) containing history, inputs and response.
        """

        # first sanity test
        logging.info("First sanity check in progress!!")
        first_response = self.first_sanity_check_invoker()

        if first_response["return"]:
            logging.info("First sanity check detected Injection")
            return {
                "answer": "Prompt Injection detected, please don't trick this model for unwanted results" ,
                "sanity_check_from_which_step": "1",
                "metadata": {
                    "metrics_obtained": first_response["metrics_obtained"],
                    "label": first_response["label"]
                }
            }
        else:
            logging.info("First sanity passed. Moving to second sanity check!!")
            second_response = self.second_sanity_check_invoker()
            if second_response["return"]:
                logging.info("Second sanity detected Injection")
                return {
                    "answer": "Prompt Injection detected, please don't trick this model for unwanted results",
                    "sanity_check_from_which_step": "2",
                    "metadata": {
                        "metrics_obtained": second_response["metrics_obtained"],
                        "label": second_response["label"]
                    }
                }
            else:
                logging.info("No injection detected, providing query to LLM")

                prompt = ChatPromptTemplate.from_template("Tell me a joke about {foo}")
                model = ChatOpenAI(model_name="gpt-3.5-turbo",
                                   openai_api_key=self.config['OPENAI_API_KEY'])
                chain = prompt | model | StrOutputParser()
                return {
                    "answer": ,
                    "sanity_check_from_which_step": "2",
                    "metadata": {
                        "metrics_obtained": second_response["metrics_obtained"],
                        "label": second_response["label"]
                    }
                }
                # llm_chain = LLMChain(
                #     llm=llm,
                #     prompt=PromptTemplate.from_template(prompt_template)
                # )
                # llm_chain(self.request["query"])

