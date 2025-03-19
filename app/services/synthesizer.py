from typing import List
import pandas as pd
from pydantic import BaseModel, Field
#from services.llm_factory import LLMFactory
from app.services.llm_factory import LLMFactory
from playsound import playsound
from TTS.api import TTS

class SynthesizedResponse(BaseModel):
    thought_process: List[str] = Field(description="List of thoughts that the AI assistant had while synthesizing the answer")
    answer: str = Field(description="The synthesized answer to the user's question")
    enough_context: bool = Field(description="Whether the assistant has enough context to answer the question")


class Synthesizer:
    SYSTEM_PROMPT = """
    # Role and Purpose
    You are an AI assistant acting as a project manager. Your task is to synthesize a coherent and helpful answer 
    based on the given question and relevant context retrieved from a knowledge database or a list of tasks.

    # Guidelines:
    1. Provide a clear and concise answer to the question.
    2. Use only the information from the relevant context to support your answer.
    3. The context is retrieved based on cosine similarity, so some information might be missing or irrelevant.
    4. Be transparent when there is insufficient information to fully answer the question.
    5. Do not make up or infer information not present in the provided context.
    6. If you cannot answer the question based on the given context, clearly state that.
    7. Maintain a helpful and professional tone appropriate for customer service.
    8. If the user asks for a list of tasks, return a list of tasks.
    Review the question from the user:
    """

    @staticmethod
    def generate_response(question: str, context: pd.DataFrame) -> SynthesizedResponse:
        """Generates a synthesized response based on the question and context.

        Args:
            question: The user's question.
            context: The relevant context retrieved from the knowledge base.

        Returns:
            A SynthesizedResponse containing thought process and answer.
        """
        context_str = Synthesizer.dataframe_to_json(
            context, columns_to_keep=["content", "category"]
        )

        messages = [
            {"role": "system", "content": Synthesizer.SYSTEM_PROMPT},
            {"role": "user", "content": f"# User question:\n{question}"},
            {
                "role": "assistant",
                "content": f"# Retrieved information:\n{context_str}",
            },
        ]

        llm = LLMFactory("openai")
        return llm.create_completion(
            response_model=SynthesizedResponse,
            messages=messages,
        )

    @staticmethod
    def play_response(response: str):
        """
        Plays the synthesized response using the TTS engine.

        Args:
            response (str): The synthesized response to play.
        """
        # Initialize the TTS engine with a pretrained model.
        tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")

        # Generate speech to file.  
        tts.tts_to_file(text=response, file_path="response_output.wav")

        # Play the generated audio file.
        playsound("response_output.wav")    
        
    @staticmethod
    def dataframe_to_json(
        context: pd.DataFrame,
        columns_to_keep: List[str],
    ) -> str:
        """
        Convert the context DataFrame to a JSON string.

        Args:
            context (pd.DataFrame): The context DataFrame.
            columns_to_keep (List[str]): The columns to include in the output.

        Returns:
            str: A JSON string representation of the selected columns.
        """
        return context[columns_to_keep].to_json(orient="records", indent=2)
