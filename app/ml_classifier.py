import os
import logging
from typing import Tuple, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import torch
import numpy as np
from app.config import settings

logger = logging.getLogger(__name__)

class EmailClassifier:
    def __init__(self):
        self.problem_classifier = None
        self.category_classifier = None
        self.embedding_model = None
        self.load_models()
    
    def load_models(self):
        """Load Hugging Face models for classification, cached under models directory"""
        try:
            # Ensure a local model cache directory exists
            os.makedirs(settings.MODEL_PATH, exist_ok=True)

            # Also point HF caches to the local models dir for consistency
            os.environ.setdefault("TRANSFORMERS_CACHE", settings.MODEL_PATH)
            os.environ.setdefault("HF_HOME", settings.MODEL_PATH)

            # Load sentence transformer for embeddings (cache locally)
            self.embedding_model = SentenceTransformer(
                settings.HUGGINGFACE_MODEL_NAME,
                cache_folder=settings.MODEL_PATH
            )

            # Prepare a lightweight classification backbone cached locally
            tokenizer = AutoTokenizer.from_pretrained(
                "distilbert-base-uncased",
                cache_dir=settings.MODEL_PATH
            )
            model = AutoModelForSequenceClassification.from_pretrained(
                "distilbert-base-uncased",
                cache_dir=settings.MODEL_PATH
            )

            # Build pipelines using the locally cached model/tokenizer
            self.problem_classifier = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer
            )

            # Reuse the same backbone for category classifier to avoid duplicate downloads
            self.category_classifier = pipeline(
                "text-classification",
                model=model,
                tokenizer=tokenizer
            )

            logger.info("ML models loaded successfully from local cache directory: %s", settings.MODEL_PATH)

        except Exception as e:
            logger.error(f"Error loading ML models: {e}")
            # Fallback to simple rule-based classification
            self.use_fallback = True
    
    def classify_email(self, subject: str, content: str) -> Tuple[bool, Optional[str], float]:
        """
        Classify email as problem or information and categorize if it's a problem
        
        Returns:
            Tuple[is_problem, category, confidence_score]
        """
        try:
            # Combine subject and content for classification
            combined_text = f"Subject: {subject}\n\nContent: {content}"
            
            # First, classify as problem vs information
            problem_result = self.problem_classifier(combined_text[:512])  # Limit text length
            is_problem = problem_result[0]['label'] == 'LABEL_1'  # Assuming LABEL_1 is problem
            problem_confidence = problem_result[0]['score']
            
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
            return self._fallback_classification(subject, content)
    
    def _categorize_problem(self, subject: str, content: str) -> Tuple[Optional[str], float]:
        """Categorize problem emails into specific categories"""
        try:
            # Define problem categories
            problem_categories = [
                "technical_issue",
                "billing_problem", 
                "service_outage",
                "account_access",
                "data_issue",
                "performance_problem",
                "security_concern",
                "other"
            ]
            
            # Use embeddings to find the most similar category
            combined_text = f"Subject: {subject}\n\nContent: {content}"
            
            # Get embeddings for the email text
            email_embedding = self.embedding_model.encode(combined_text[:512])
            
            # Get embeddings for category descriptions
            category_descriptions = [
                "technical problem error bug issue",
                "billing payment invoice charge",
                "service down unavailable outage",
                "account login access password",
                "data missing corrupted lost",
                "slow performance timeout",
                "security breach hack unauthorized",
                "general problem issue"
            ]
            
            category_embeddings = self.embedding_model.encode(category_descriptions)
            
            # Calculate similarities
            similarities = np.dot(category_embeddings, email_embedding) / (
                np.linalg.norm(category_embeddings, axis=1) * np.linalg.norm(email_embedding)
            )
            
            # Get the most similar category
            best_category_idx = np.argmax(similarities)
            confidence = float(similarities[best_category_idx])
            
            return problem_categories[best_category_idx], confidence
            
        except Exception as e:
            logger.error(f"Error in problem categorization: {e}")
            return "other", 0.5
    
    def _fallback_classification(self, subject: str, content: str) -> Tuple[bool, Optional[str], float]:
        """Fallback rule-based classification when ML models fail"""
        # Simple keyword-based classification
        problem_keywords = [
            'error', 'problem', 'issue', 'bug', 'fail', 'broken', 'down', 'outage',
            'billing', 'payment', 'charge', 'invoice', 'account', 'access', 'login',
            'security', 'breach', 'hack', 'unauthorized', 'performance', 'slow'
        ]
        
        combined_text = (subject + " " + content).lower()
        
        # Count problem keywords
        problem_count = sum(1 for keyword in problem_keywords if keyword in combined_text)
        
        # Classify as problem if more than 2 problem keywords found
        is_problem = problem_count >= 2
        
        if is_problem:
            # Simple category assignment based on keywords
            if any(word in combined_text for word in ['billing', 'payment', 'charge']):
                category = "billing_problem"
            elif any(word in combined_text for word in ['error', 'bug', 'fail']):
                category = "technical_issue"
            elif any(word in combined_text for word in ['down', 'outage', 'unavailable']):
                category = "service_outage"
            else:
                category = "other"
        else:
            category = None
        
        # Simple confidence based on keyword count
        confidence = min(0.9, 0.5 + (problem_count * 0.1))
        
        return is_problem, category, confidence
