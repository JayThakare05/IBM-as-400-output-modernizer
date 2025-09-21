# services/ai_service.py - Improved AI Processing Service
import logging
import re
from functools import lru_cache
from typing import Optional, Dict, List, Any, Tuple
from collections import Counter
from core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered text processing with enhanced validation"""
    
    def __init__(self):
        self.modernizer = None
        self.has_transformers = False
        self._load_ai_model()
    
    def _load_ai_model(self):
        """Load AI model if available"""
        if not settings.ENABLE_AI_PROCESSING:
            logger.info("AI processing disabled in configuration")
            return
            
        try:
            from transformers import pipeline
            self.modernizer = pipeline(
                "text2text-generation", 
                model=settings.AI_MODEL_NAME,
                max_length=50
            )
            self.has_transformers = True
            logger.info(f"AI model loaded successfully: {settings.AI_MODEL_NAME}")
        except Exception as e:
            logger.warning(f"Failed to load AI model: {e}")
            self.has_transformers = False

    def _validate_column_name(self, name: str, original: str) -> bool:
        """
        Validate that the generated column name is reasonable
        """
        if not name or len(name) < 2 or len(name) > 40:
            return False
        
        # Check for common AI artifacts and nonsense
        invalid_patterns = [
            r'.*customeromer.*', r'.*identifierifier.*', r'.*addressess.*', 
            r'.*numberber.*', r'.*the.*', r'.*a.*', r'.*an.*',
            r'.*column.*', r'.*field.*', r'.*value.*', r'.*name.*',
            r'.*legacy.*', r'.*original.*', r'.*old.*'
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, name, re.IGNORECASE):
                return False
        
        # Should be snake_case with valid characters
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            return False
        
        # Should not be too similar to the original (indicating poor transformation)
        if name.lower() == original.lower():
            return False
            
        return True

    def predict_column_name_from_data(self, column_data: List[Any], col_index: int = 0) -> str:
        """
        Enhanced column name prediction with better fallbacks
        """
        if not column_data:
            return f"column_{col_index}"

        # Take a sample of non-null values
        sample = [str(d).strip() for d in column_data[:100] if d is not None and str(d).strip()]
        if not sample:
            return f"data_column_{col_index}"

        # First try pattern-based detection (more reliable)
        pattern_result = self._pattern_based_prediction(sample, col_index)
        if pattern_result and not pattern_result.startswith(('text_data_', 'numeric_data_')):
            return pattern_result

        # Only then try AI if pattern-based failed
        if self.modernizer and self.has_transformers:
            try:
                sample_preview = sample[:3]
                prompt = (
                    f"Based on these sample values: {sample_preview}, "
                    f"generate a concise snake_case column name. "
                    f"Return only the column name, no explanations. "
                    f"Examples: ['john@email.com'] -> 'email', "
                    f"['555-1234'] -> 'phone_number', "
                    f"['100.00'] -> 'amount'"
                )
                
                result = self.modernizer(prompt, max_length=20, do_sample=False)
                generated_name = result[0]["generated_text"].strip().lower() if isinstance(result, list) else str(result).strip().lower()
                
                # Clean and validate
                clean_name = self._clean_column_name(generated_name)
                if clean_name and self._validate_column_name(clean_name, ""):
                    logger.info(f"AI predicted: {clean_name}")
                    return clean_name
            except Exception as e:
                logger.warning(f"AI column prediction failed: {e}")

        return pattern_result  # Fall back to pattern result

    def _pattern_based_prediction(self, sample: List[str], col_index: int) -> str:
        """Reliable pattern-based column name prediction"""
        patterns = [
            ('email', re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')),
            ('phone_number', re.compile(r'^\+?[\d\s-()]{7,20}$')),
            ('date', re.compile(r'^\d{4}-\d{2}-\d{2}$|^\d{2}/\d{2}/\d{4}$|^\d{2}-\d{2}-\d{4}$')),
            ('zip_code', re.compile(r'^\d{5}(-\d{4})?$')),
            ('amount', re.compile(r'^\$?\d+(?:\.\d{2})?$')),
            ('price', re.compile(r'^\$?\d+(?:\.\d{2})?$')),
            ('quantity', re.compile(r'^\d+$')),
            ('id', re.compile(r'^[A-Z0-9_-]+$')),
            ('percentage', re.compile(r'^\d+(?:\.\d+)?%$')),
            ('status', re.compile(r'^(active|inactive|pending|approved|rejected)$', re.IGNORECASE)),
        ]

        match_counts = Counter()
        for value in sample:
            for name, pattern in patterns:
                if pattern.match(value):
                    match_counts[name] += 1
                    break

        # Check for dominant pattern
        if match_counts:
            most_common, count = match_counts.most_common(1)[0]
            if count / len(sample) > 0.3:  # 30% threshold
                return most_common

        # Data type fallback
        if all(v.replace('.', '').replace('-', '').isdigit() for v in sample[:10]):
            return f"numeric_{col_index}"
            
        return f"text_{col_index}"

    @lru_cache(maxsize=1024)
    def modernize_column_name(self, col: str) -> str:
        """
        Modernize column name with strict validation
        """
        if not col or not str(col).strip():
            return "unknown_column"

        original_col = str(col).strip()
        
        # First check AS/400 specific patterns (most reliable)
        as400_result = self._analyze_as400_patterns(original_col)
        if as400_result != self._to_snake_case(original_col):
            if self._validate_column_name(as400_result, original_col):
                return as400_result

        # Use AI if available with strict validation
        if self.modernizer and self.has_transformers:
            try:
                prompt = (
                    f"Convert this database column name to modern snake_case: '{original_col}'. "
                    f"Return only the clean column name. "
                    f"Examples: CUS_ID -> customer_id, EMPNO -> employee_number, "
                    f"ADDR1 -> address_line_1, CUSTNAME -> customer_name"
                )
                
                result = self.modernizer(prompt, max_length=25, do_sample=False)
                generated_text = result[0]["generated_text"] if isinstance(result, list) else str(result)
                
                # Clean and validate
                clean_name = self._clean_column_name(generated_text)
                if clean_name and self._validate_column_name(clean_name, original_col):
                    logger.info(f"AI transformed: {original_col} -> {clean_name}")
                    return clean_name
            except Exception as e:
                logger.warning(f"AI transformation failed for '{original_col}': {e}")

        # Fallback to heuristic transformation with validation
        heuristic_result = self._heuristic_transformation(original_col)
        if self._validate_column_name(heuristic_result, original_col):
            return heuristic_result
            
        # Ultimate fallback
        return self._to_snake_case(original_col)

    def _clean_column_name(self, name: str) -> str:
        """Clean column name with strict rules"""
        if not name:
            return ""
        
        # Remove quotes, special chars, and AI artifacts
        clean = re.sub(r'[\'"`]', '', name.strip().lower())
        clean = re.sub(r'^(the|a|an|column|field|name|value|result|output)\s*', '', clean)
        clean = re.sub(r'\s*(column|field|name|value|result|output)$', '', clean)
        
        # Convert to snake_case
        clean = self._to_snake_case(clean)
        clean = re.sub(r'_+', '_', clean).strip('_')
        
        return clean or "column"

    def _heuristic_transformation(self, col: str) -> str:
        """Reliable heuristic transformation"""
        col_lower = col.lower()
        
        # Common abbreviations mapping with validation
        abbreviations = {
            'cust': 'customer', 'emp': 'employee', 'addr': 'address',
            'dept': 'department', 'prod': 'product', 'qty': 'quantity',
            'amt': 'amount', 'desc': 'description', 'num': 'number',
            'id': 'id', 'no': 'number', 'dt': 'date',
            'cd': 'code', 'nm': 'name', 'stat': 'status',
            'typ': 'type', 'flg': 'flag', 'act': 'active'
        }
        
        # Simple word replacement without over-correction
        result = col_lower
        for abbr, full in abbreviations.items():
            # Only replace if it's a whole word or prefix
            if re.search(rf'^{abbr}[^a-z]|^{abbr}$|[^a-z]{abbr}[^a-z]|[^a-z]{abbr}$', result):
                result = re.sub(rf'\b{abbr}\b', full, result)
        
        return self._to_snake_case(result)

    def _to_snake_case(self, s: str) -> str:
        """Convert to snake_case safely"""
        if not s or not str(s).strip():
            return "column"
        
        s = str(s).strip()
        s = re.sub(r'([a-z])([A-Z])', r'\1_\2', s)
        s = re.sub(r'[^\w\s]', '_', s)
        s = re.sub(r'\s+', '_', s)
        s = re.sub(r'_+', '_', s)
        return s.lower().strip('_') or "column"

    def _analyze_as400_patterns(self, col: str) -> str:
        """AS/400 pattern recognition"""
        col_upper = col.upper()
        
        as400_mappings = {
            'CUS_ID': 'customer_id', 'CUSTID': 'customer_id', 'CUSTNO': 'customer_number',
            'CUSTNUM': 'customer_number', 'CUST#': 'customer_id', 'CUSTNAME': 'customer_name',
            'CUSTNAM': 'customer_name', 'CUSTNM': 'customer_name', 'NME': 'name',
            'EMPNO': 'employee_number', 'EMPNUM': 'employee_number', 'EMP#': 'employee_id',
            'EMPNAME': 'employee_name', 'EMPNAM': 'employee_name', 'EMPNM': 'employee_name',
            'ADDR1': 'address_line_1', 'ADDR2': 'address_line_2', 'STREET': 'street_address',
            'CITY': 'city', 'STATE': 'state', 'ZIP': 'zip_code', 'ZIPCODE': 'zip_code',
            'POSTAL': 'postal_code', 'COUNTRY': 'country', 'CREDITLMT': 'credit_limit',
            'BALANCE': 'account_balance', 'AMT': 'amount', 'AMOUNT': 'amount', 'PRICE': 'price',
            'HIREDATE': 'hire_date', 'CREATEDT': 'create_date', 'MODDT': 'modify_date',
            'SHIPDT': 'ship_date', 'ORDERDT': 'order_date', 'PARTNO': 'part_number',
            'ITEMNO': 'item_number', 'PRODCD': 'product_code', 'SKU': 'sku', 'QTY': 'quantity',
            'DESC': 'description', 'DESCR': 'description', 'E-MAIL': 'email',
            'EMAIL': 'email', 'PHONE': 'phone_number', 'DEPT': 'department', 
            'STATUS': 'status', 'TYPE': 'type', 'CODE': 'code', 'FLAG': 'flag', 
            'ACTIVE': 'is_active', 'INACTIVE': 'is_inactive'
        }
        
        return as400_mappings.get(col_upper, self._to_snake_case(col))

    def get_status(self) -> Dict:
        """Get AI service status"""
        return {
            "ai_enabled": self.has_transformers,
            "model_name": settings.AI_MODEL_NAME if self.has_transformers else None,
            "cache_size": self.modernize_column_name.cache_info().currsize if hasattr(self.modernize_column_name, 'cache_info') else 0
        }

# GlobalAAC AI service instance
ai_service = AIService()