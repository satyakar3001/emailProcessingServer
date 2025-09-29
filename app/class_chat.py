import os
import logging
from typing import Tuple, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import JsonOutputParser
# from langchain_core.exceptions import OutputParserExceptoin

from dotenv import load_dotenv
from app.config import settings

logger = logging.getLogger(__name__)

class Chain:
    def __init__(self):
        self.llm = ChatGroq(
            temperature =0,
            # groq_api_key=os.getenv("GROQ_API_KEY"),
            groq_api_key=settings.GROQ_API_KEY,
            model_name = "llama-3.1-8b-instant"
                )
        
    # def extract_jobs(self,cleaned_text):
    #     prompt_extract = PromptTemplate.from_template( """
    # ### SCRAPED TEXT FROM WEBSITE:
    # {page_data}
    # ### INSTRUCTION:
    # The scraped text is from the careet's page of a website.
    # Your job is to extract the job postings and return them in JSON format containing
    # following keys: `role`, `experience`, `skills`, and `description` .
    # Only return the valid JSON.
    # ### VALID JSON (NO PREAMBLE): """)
        
    #     chain_extract = prompt_extract | self.llm
    #     res = chain_extract.invoke(input={"page_data":cleaned_text})

    #     try:
    #         json_parser = JsonOutputParser()
    #         res = json_parser.parse(res.content)
    #         res = res[0]['skills']
    #     except OutputParserExceptoin as e:
    #         raise OutputParserExceptoin("Context too big Unable to parse job")
        
    #     return res if isinstance(res,list) else [res]
    def classify_email_chat(self, subject: str, content: str) -> Tuple[bool, Optional[str], float]:
        """
        Classify email as problem or information and categorize if it's a problem
        
        Returns: 
            Tuple[is_problem, category, confidence_score]
        """
        try:
            # Combine subject and content for classification
            combined_text = f"Subject: {subject}\n\nContent: {content}"
            
            # First, classify as problem vs information
            # problem_result = self.problem_classifier(combined_text[:512]) # Limit text length
            prompt_email = PromptTemplate.from_template("""
                ### COMBINED EMAIL TEXT:
                {combined_text}
                ### INSTRUCTION:
                Classify the above email as either a 'problem' or 'information'.
                If classified as 'problem', further categorize it into one of the following categories:"technical problem error bug issue",
                "billing payment invoice charge",
                "service down unavailable outage",
                "account login access password",
                "data missing corrupted lost",
                "slow performance timeout",
                "security breach hack unauthorized",
                "general problem issue"
    

                ### (NO PREAMBLE): """)
            chain_email = prompt_email | self.llm
            chain_email = chain_email.invoke({'combined_text': combined_text})
            return chain_email.content
           
            
            category = None
            category_confidence = 0.0
            
            # If it's a problem, categorize it
            if is_problem:
                category, category_confidence = self._categorize_problem(subject, content)
            
            # Calculate overall confidence
            overall_confidence = (problem_confidence + category_confidence) / 2 if category else problem_confidence
            
            return is_problem, category, overall_confidence
        
        except Exception as e:
            logger.error(f"Error in email classification: {e}")
            # Fallback to rule-based classification
            # return self._fallback_classification(subject, content)
            return "error in classification{e}"
    
    def write_mail(self,job,links):
        prompt_email = PromptTemplate.from_template("""
    ### JOB DESCRIPTION
    {job_description}
    ### INSTRUCTION:
    

    ###Email (NO PREAMBLE): """)
        chain_email = prompt_email | self.llm
        chain_email = chain_email.invoke({'job_description': job, 'link_list': links})
        return chain_email.content
