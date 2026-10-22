"""
Error Normalizer - error message normalization tool
Normalizes error messages to improve vector retrieval accuracy
"""
import re
from typing import Optional


class ErrorNormalizer:
    """Error message normalization and processing utilities"""
    
    # Common Python error types
    ERROR_TYPES = [
        'ValueError', 'TypeError', 'KeyError', 'AttributeError',
        'IndexError', 'ImportError', 'ModuleNotFoundError',
        'FileNotFoundError', 'PermissionError', 'RuntimeError',
        'SyntaxError', 'IndentationError', 'NameError',
        'ZeroDivisionError', 'AssertionError', 'OSError',
        'IOError', 'MemoryError', 'RecursionError',
        'Exception', 'BaseException'
    ]
    
    @staticmethod
    def normalize(error_info: str) -> str:
        """
        Normalize an error message
        
        Main operations:
        1. Remove concrete file paths, replacing them with <FILE>
        2. Remove concrete line numbers, replacing them with <LINE>
        3. Remove concrete numeric values (keeping error-relevant ones)
        4. Remove temporary variable names and memory addresses
        5. Normalize whitespace
        
        :param error_info: raw error message
        :return: normalized error message
        """
        if not error_info or not isinstance(error_info, str):
            return ""
        
        text = error_info
        
        # 1. Normalize file paths
        # Matches: File "/path/to/file.py" or File "C:\path\to\file.py"
        text = re.sub(r'File\s+"[^"]*[\\/]([^\\/]+\.py)"', r'File "<PATH>/\1"', text)
        text = re.sub(r'File\s+"([^"\\/:]+\.py)"', r'File "\1"', text)
        
        # 2. Normalize line numbers
        # Matches: line 123 or Line 123
        text = re.sub(r',\s*[Ll]ine\s+\d+', ', line <LINE>', text)
        
        # 3. Normalize object memory addresses
        # Matches: <object at 0x7f8b8c0d0a90>
        text = re.sub(r'<[\w\s]+\s+at\s+0x[0-9a-fA-F]+>', '<object at <ADDR>>', text)
        
        # 4. Normalize temporary variable names (those with numeric suffixes)
        # Keep common variable names; only replace obvious temporaries
        text = re.sub(r'\b([a-z_]+)_\d{3,}\b', r'\1_<ID>', text)
        
        # 5. Keep numbers such as base 10, base 16 in error messages
        # but replace other isolated large numbers
        text = re.sub(r'(?<!base\s)(?<!version\s)\b\d{4,}\b', '<NUM>', text)
        
        # 6. Normalize whitespace (collapse multiple spaces into one)
        text = re.sub(r'\s+', ' ', text)
        
        # 7. Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def extract_error_type(error_info: str) -> str:
        """
        Extract the error type
        
        Extract the Python exception type from an error message
        e.g. ValueError, TypeError, ImportError
        
        :param error_info: error message
        :return: error type, or "UnknownError" if not found
        """
        if not error_info or not isinstance(error_info, str):
            return "UnknownError"
        
        # Prefer matching known error types
        for error_type in ErrorNormalizer.ERROR_TYPES:
            if error_type in error_info:
                return error_type
        
        # Try matching via regex
        # Matches: XxxError or XxxException
        match = re.search(r'\b(\w+(?:Error|Exception))\b', error_info)
        if match:
            return match.group(1)
        
        return "UnknownError"
    
    @staticmethod
    def extract_error_message(error_info: str) -> str:
        """
        Extract the core error message
        
        Extract the last-line error message from a full traceback
        
        :param error_info: full error message
        :return: core error message
        """
        if not error_info or not isinstance(error_info, str):
            return ""
        
        lines = error_info.strip().split('\n')
        
        # The last line is usually the error message
        for line in reversed(lines):
            line = line.strip()
            if line and ':' in line:
                # Check whether it contains an error type
                for error_type in ErrorNormalizer.ERROR_TYPES:
                    if error_type in line:
                        return line
        
        # If not found, return the last non-empty line
        for line in reversed(lines):
            if line.strip():
                return line.strip()
        
        return error_info
    
    @staticmethod
    def create_searchable_text(
        error_info: str, 
        fix_strategy: str,
        max_error_length: int = 1000,
        max_strategy_length: int = 1000
    ) -> str:
        """
        Create text for vector search
        
        Combine the error message and fix strategy into structured searchable text
        This text is sent to ChromaDB for vectorization
        
        :param error_info: raw error message
        :param fix_strategy: description of the fix strategy
        :param max_error_length: maximum length of the error message
        :param max_strategy_length: maximum length of the fix strategy
        :return: structured searchable text
        """
        # Normalize the error message
        normalized_error = ErrorNormalizer.normalize(error_info)
        
        # Extract the error type
        error_type = ErrorNormalizer.extract_error_type(error_info)
        
        # Extract the core error message
        error_message = ErrorNormalizer.extract_error_message(error_info)
        
        # Truncate overly long text
        if len(normalized_error) > max_error_length:
            normalized_error = normalized_error[:max_error_length] + "..."
        
        if len(fix_strategy) > max_strategy_length:
            fix_strategy = fix_strategy[:max_strategy_length] + "..."
        
        # Combine into structured text
        # This format matters for vectorization because it provides clear context
        searchable_text = f"""Error Type: {error_type}

Error Message:
{error_message}

Normalized Error:
{normalized_error}

Fix Strategy:
{fix_strategy}
"""
        
        return searchable_text.strip()
    
    @staticmethod
    def extract_keywords(error_info: str) -> list:
        """
        Extract keywords from an error message
        
        Used to assist search and classification
        
        :param error_info: error message
        :return: list of keywords
        """
        if not error_info or not isinstance(error_info, str):
            return []
        
        keywords = []
        
        # Add the error type
        error_type = ErrorNormalizer.extract_error_type(error_info)
        if error_type != "UnknownError":
            keywords.append(error_type)
        
        # Extract common Python key concepts
        concepts = [
            'import', 'module', 'package', 'function', 'method',
            'class', 'attribute', 'variable', 'list', 'dict',
            'string', 'integer', 'float', 'None', 'True', 'False',
            'file', 'path', 'permission', 'network', 'database',
            'syntax', 'indentation', 'recursion', 'memory'
        ]
        
        error_lower = error_info.lower()
        for concept in concepts:
            if concept in error_lower:
                keywords.append(concept)
        
        return list(set(keywords))  # deduplicate
    
    @staticmethod
    def similarity_hint(error_info: str) -> dict:
        """
        Generate similarity hints
        
        Used to assist vector retrieval by providing extra context
        
        :param error_info: error message
        :return: dict containing various hints
        """
        return {
            "error_type": ErrorNormalizer.extract_error_type(error_info),
            "keywords": ErrorNormalizer.extract_keywords(error_info),
            "normalized": ErrorNormalizer.normalize(error_info),
            "message": ErrorNormalizer.extract_error_message(error_info)
        }
