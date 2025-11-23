"""
Production-grade function_tool decorator for OpenAI function calling.

This module provides a robust decorator that automatically generates OpenAI-compatible
JSON schemas from Python function signatures with comprehensive type hint support,
docstring parameter extraction, and validation.

Key Features:
    - Full Python typing module support (Optional, List, Dict, Union, Literal, etc.)
    - Automatic parameter description extraction from docstrings
    - Comprehensive validation with helpful error messages
    - OpenAI strict mode compliance
    - Production-quality error handling

Usage:
    @function_tool
    async def my_tool(param1: str, param2: int = 5):
        '''Tool description.
        
        Args:
            param1: Description of param1
            param2: Description of param2
        '''
        ...
        
    @function_tool(name_override="custom_name")
    async def my_other_tool(param: str):
        '''Another tool.'''
        ...
"""

import inspect
import logging
import re
from typing import (
    get_type_hints,
    get_origin,
    get_args,
    Optional,
    List,
    Dict,
    Any,
    Union,
)
from enum import Enum

# Configure logger
logger = logging.getLogger(__name__)


# ============================================================================
# Error Classes
# ============================================================================

class FunctionToolError(Exception):
    """Base exception for function_tool errors."""
    pass


class InvalidTypeHintError(FunctionToolError):
    """Raised when an unsupported or invalid type hint is encountered."""
    pass


class SchemaValidationError(FunctionToolError):
    """Raised when generated schema fails validation."""
    pass


# ============================================================================
# Docstring Parsing Utilities
# ============================================================================

def extract_param_descriptions(docstring: str) -> Dict[str, str]:
    """
    Extract parameter descriptions from Google/NumPy style docstrings.
    
    Supports formats like:
        Args:
            param_name: Description here
            another_param: Another description
                that can span multiple lines
    
    Args:
        docstring: The function's docstring
        
    Returns:
        Dictionary mapping parameter names to their descriptions
    """
    if not docstring:
        return {}
    
    descriptions = {}
    
    # Look for Args: or Arguments: section
    args_pattern = r'(?:Args|Arguments):\s*\n((?:\s+\w+.*\n(?:\s+.*\n)*)*)'
    match = re.search(args_pattern, docstring)
    
    if not match:
        return {}
    
    args_section = match.group(1)
    
    # Parse individual parameters
    # Pattern: parameter_name: description (possibly multi-line)
    param_pattern = r'^\s+(\w+):\s*(.+?)(?=^\s+\w+:|$)'
    
    for param_match in re.finditer(param_pattern, args_section, re.MULTILINE | re.DOTALL):
        param_name = param_match.group(1)
        description = param_match.group(2)
        
        # Clean up description (remove extra whitespace, join lines)
        description = ' '.join(line.strip() for line in description.split('\n') if line.strip())
        descriptions[param_name] = description
    
    return descriptions


# ============================================================================
# Type Conversion Utilities
# ============================================================================

def python_type_to_json_schema(py_type: Any, param_name: str = "") -> dict:
    """
    Convert Python type hints to JSON schema with full typing module support.
    
    Supports:
        - Basic types: str, int, float, bool
        - Containers: List, Dict
        - Optional/Union types
        - Nested generics: List[Dict[str, Any]]
        - Enum types
        - Literal types (if available in typing)
    
    Args:
        py_type: The Python type hint to convert
        param_name: Parameter name for error messages
        
    Returns:
        JSON schema dictionary for the type
        
    Raises:
        InvalidTypeHintError: If type is unsupported
    """
    origin = get_origin(py_type)
    
    # Handle None type
    if py_type is type(None):
        return {"type": "null"}
    
    # Handle Enum types
    if inspect.isclass(py_type) and issubclass(py_type, Enum):
        enum_values = [item.value for item in py_type]
        return {"type": "string", "enum": enum_values}
    
    # Handle generic types (List, Dict, Optional, Union, etc.)
    if origin is not None:
        args = get_args(py_type)
        
        # Handle List types
        if origin is list or origin is List:
            if args:
                items_schema = python_type_to_json_schema(args[0], f"{param_name}[]")
                return {"type": "array", "items": items_schema}
            return {"type": "array", "items": {}}
        
        # Handle Dict types
        elif origin is dict or origin is Dict:
            return {"type": "object"}
        
        # Handle Union types (including Optional)
        elif origin is Union:
            # Filter out None to find the actual type(s)
            non_none_types = [t for t in args if t is not type(None)]
            
            if len(non_none_types) == 1:
                # This is Optional[T] - just return schema for T
                return python_type_to_json_schema(non_none_types[0], param_name)
            elif len(non_none_types) > 1:
                # Multiple non-None types in Union
                # OpenAI doesn't support union types well, pick the first one
                logger.warning(
                    f"Parameter '{param_name}': Union types not fully supported by OpenAI, "
                    f"using first type: {non_none_types[0]}"
                )
                return python_type_to_json_schema(non_none_types[0], param_name)
            else:
                # Only None type
                return {"type": "null"}
        
        # Handle Literal types (e.g., Literal["a", "b", "c"])
        # Note: Literal is available in typing from Python 3.8+
        try:
            from typing import Literal as LiteralType
            if origin is LiteralType:
                # Convert Literal to enum
                literal_values = list(args)
                # Determine type from first value
                if literal_values:
                    first_val = literal_values[0]
                    if isinstance(first_val, str):
                        return {"type": "string", "enum": literal_values}
                    elif isinstance(first_val, int):
                        return {"type": "integer", "enum": literal_values}
                    elif isinstance(first_val, bool):
                        return {"type": "boolean", "enum": literal_values}
                return {"type": "string", "enum": literal_values}
        except ImportError:
            pass  # Literal not available in this Python version
    
    # Handle basic types
    if py_type is str or py_type == str:
        return {"type": "string"}
    elif py_type is int or py_type == int:
        return {"type": "integer"}
    elif py_type is float or py_type == float:
        return {"type": "number"}
    elif py_type is bool or py_type == bool:
        return {"type": "boolean"}
    elif py_type is list or py_type == list or py_type is List:
        return {"type": "array", "items": {}}
    elif py_type is dict or py_type == dict or py_type is Dict:
        return {"type": "object"}
    elif py_type is Any:
        # 'Any' type - use object as fallback
        return {"type": "object"}
    
    # Unknown type - raise error with helpful message
    raise InvalidTypeHintError(
        f"Unsupported type hint for parameter '{param_name}': {py_type}. "
        f"Supported types: str, int, float, bool, List, Dict, Optional, Union, Enum, Literal, Any"
    )


# ============================================================================
# Schema Generation
# ============================================================================

def generate_json_schema(func: Any) -> dict:
    """
    Generate OpenAI-compatible JSON schema from function signature.
    
    Extracts type hints, default values, and parameter descriptions from
    the function's signature and docstring.
    
    Args:
        func: The function to generate schema for
        
    Returns:
        JSON schema dictionary with properties and required fields
        
    Raises:
        InvalidTypeHintError: If function has missing or invalid type hints
        SchemaValidationError: If generated schema is invalid
    """
    sig = inspect.signature(func)
    
    # Get type hints (raises if not all params have hints)
    try:
        type_hints = get_type_hints(func)
    except Exception as e:
        raise InvalidTypeHintError(
            f"Failed to get type hints for function '{func.__name__}': {e}"
        )
    
    # Extract parameter descriptions from docstring
    docstring = inspect.getdoc(func) or ""
    param_descriptions = extract_param_descriptions(docstring)
    
    properties = {}
    required = []
    
    for param_name, param in sig.parameters.items():
        # Skip 'self' parameter for methods
        if param_name == 'self':
            continue
        
        # Ensure parameter has type hint
        if param_name not in type_hints:
            raise InvalidTypeHintError(
                f"Parameter '{param_name}' in function '{func.__name__}' "
                f"is missing a type hint. All parameters must have type hints."
            )
        
        param_type = type_hints[param_name]
        has_default = param.default is not inspect.Parameter.empty
        
        # Generate JSON schema for this type
        try:
            type_schema = python_type_to_json_schema(param_type, param_name)
        except InvalidTypeHintError as e:
            raise InvalidTypeHintError(
                f"In function '{func.__name__}', parameter '{param_name}': {e}"
            )
        
        # Build property schema
        property_schema = type_schema.copy()
        
        # Add description if available from docstring
        if param_name in param_descriptions:
            property_schema["description"] = param_descriptions[param_name]
        
        properties[param_name] = property_schema
        
        # Add to required if no default value
        if not has_default:
            required.append(param_name)
    
    # Build final schema
    schema = {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False
    }
    
    # Validate schema
    validate_json_schema(schema, func.__name__)
    
    return schema


# ============================================================================
# Validation
# ============================================================================

def validate_json_schema(schema: dict, func_name: str) -> None:
    """
    Validate that generated schema meets OpenAI requirements.
    
    Args:
        schema: The generated JSON schema
        func_name: Function name for error messages
        
    Raises:
        SchemaValidationError: If schema is invalid
    """
    # Check required fields
    if "type" not in schema or schema["type"] != "object":
        raise SchemaValidationError(
            f"Schema for '{func_name}' must have type 'object'"
        )
    
    if "properties" not in schema:
        raise SchemaValidationError(
            f"Schema for '{func_name}' must have 'properties' field"
        )
    
    if "additionalProperties" not in schema or schema["additionalProperties"] != False:
        raise SchemaValidationError(
            f"Schema for '{func_name}' must have 'additionalProperties': false for strict mode"
        )
    
    # Validate all properties have types
    for prop_name, prop_schema in schema.get("properties", {}).items():
        if "type" not in prop_schema and "enum" not in prop_schema:
            raise SchemaValidationError(
                f"Property '{prop_name}' in '{func_name}' schema must have a 'type' or 'enum' field"
            )


def validate_function_signature(func: Any) -> None:
    """
    Validate that function signature is compatible with function_tool.
    
    Args:
        func: The function to validate
        
    Raises:
        FunctionToolError: If function signature has issues
    """
    if not callable(func):
        raise FunctionToolError(f"'{func}' is not callable")
    
    # Check if function is async (recommended for OpenAI AsyncClient)
    if not inspect.iscoroutinefunction(func):
        logger.warning(
            f"Function '{func.__name__}' is not async. "
            f"Inferno uses AsyncOpenAI, consider making it async."
        )


# ============================================================================
# Main Decorator
# ============================================================================

def function_tool(func=None, *, name_override: Optional[str] = None):
    """
    Decorator to mark a function as an OpenAI tool and generate its JSON schema.
    
    This decorator:
        - Generates OpenAI-compatible JSON schema from type hints
        - Extracts parameter descriptions from docstrings
        - Validates function signature and schema
        - Attaches metadata to function for tool registration
    
    Args:
        func: The function to decorate (provided automatically when using @function_tool)
        name_override: Optional custom name for the tool (default: function name)
    
    Returns:
        Decorated function with attached metadata attributes:
            - .name: Tool name
            - .description: Tool description from docstring
            - .params_json_schema: JSON schema for parameters
            - .strict_json_schema: Always True for OpenAI strict mode
    
    Raises:
        FunctionToolError: If function signature is invalid
        InvalidTypeHintError: If type hints are missing or unsupported
        SchemaValidationError: If generated schema is invalid
    
    Usage:
        @function_tool
        async def my_tool(param1: str, param2: int = 5):
            '''Tool description.
            
            Args:
                param1: Description of param1
                param2: Description of param2
            '''
            return "result"
            
        @function_tool(name_override="custom_name")
        async def another_tool(x: str):
            '''Another tool.'''
            return x
    """
    def decorator(f: Any) -> Any:
        # Validate function signature
        validate_function_signature(f)
        
        # Determine tool name
        tool_name = name_override if name_override else f.__name__
        
        # Extract description from docstring
        tool_description = inspect.getdoc(f) or f"Execute {tool_name}"
        
        # Generate JSON schema for parameters
        try:
            params_schema = generate_json_schema(f)
        except (InvalidTypeHintError, SchemaValidationError) as e:
            logger.error(f"Failed to generate schema for '{tool_name}': {e}")
            raise
        
        # Attach metadata to function
        f.name = tool_name
        f.description = tool_description
        f.params_json_schema = params_schema
        f.strict_json_schema = True
        
        logger.debug(f"Successfully decorated function '{tool_name}' with schema")
        
        return f
    
    # Handle both @function_tool and @function_tool(name_override="...")
    if func is None:
        # Called with arguments: @function_tool(name_override="...")
        return decorator
    else:
        # Called without arguments: @function_tool
        return decorator(func)
