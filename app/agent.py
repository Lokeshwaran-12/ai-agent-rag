"""
AI Agent module with LLM integration, tool calling, and memory management.
This implements Task 1: AI Agent Development.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from openai import AzureOpenAI, OpenAI
from app.config import settings


class AgentMemory:
    """Simple session-based memory for the AI agent."""
    
    def __init__(self):
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Optional[Dict] = None):
        """Add a message to the session history."""
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        self.sessions[session_id].append(message)
    
    def get_history(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve conversation history for a session."""
        history = self.sessions.get(session_id, [])
        if limit:
            return history[-limit:]
        return history
    
    def clear_session(self, session_id: str):
        """Clear a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_context_messages(self, session_id: str, limit: int = 10) -> List[Dict[str, str]]:
        """Get formatted messages for LLM context."""
        history = self.get_history(session_id, limit)
        return [{"role": msg["role"], "content": msg["content"]} for msg in history]


class AgentTools:
    """Tools that the AI agent can use."""
    
    @staticmethod
    def get_current_time() -> str:
        """Get the current time."""
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    @staticmethod
    def calculate(expression: str) -> str:
        """Safely evaluate a mathematical expression."""
        try:
            # Only allow basic math operations for safety
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expression):
                return "Error: Invalid characters in expression"
            
            result = eval(expression, {"__builtins__": {}}, {})
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @staticmethod
    def search_documents(query: str, rag_system) -> str:
        """Search documents using the RAG system."""
        try:
            results = rag_system.search(query)
            if not results:
                return "No relevant documents found."
            
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"{i}. {result['content'][:200]}... (Source: {result['source']})"
                )
            return "\n\n".join(formatted_results)
        except Exception as e:
            return f"Error searching documents: {str(e)}"


# Tool definitions for function calling
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current date and time in UTC",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform a mathematical calculation. Supports basic arithmetic operations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_documents",
            "description": "Search through company documents to find relevant information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant documents"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


class AIAgent:
    """Main AI Agent with LLM, tool calling, and memory capabilities."""
    
    def __init__(self, rag_system=None):
        """Initialize the AI agent."""
        self.memory = AgentMemory()
        self.tools = AgentTools()
        self.rag_system = rag_system
        
        # Initialize OpenAI client (Azure AI Foundry, Azure OpenAI, or standard OpenAI)
        if settings.azure_openai_api_key and settings.azure_openai_endpoint:
            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            self.model = settings.azure_openai_deployment_name
        elif settings.openai_api_key:
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = "gpt-4"
        else:
            raise ValueError("No OpenAI API key configured")
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result."""
        if tool_name == "get_current_time":
            return self.tools.get_current_time()
        elif tool_name == "calculate":
            return self.tools.calculate(arguments.get("expression", ""))
        elif tool_name == "search_documents":
            if not self.rag_system:
                return "Document search is not available. RAG system not initialized."
            return self.tools.search_documents(arguments.get("query", ""), self.rag_system)
        else:
            return f"Unknown tool: {tool_name}"
    
    def _should_use_rag(self, query: str) -> bool:
        """Determine if the query requires document search."""
        # Keywords that suggest document search is needed
        doc_keywords = [
            "policy", "document", "company", "procedure", "guideline",
            "rule", "regulation", "faq", "how to", "what is our",
            "according to", "based on", "find", "search",
            "vacation", "leave", "holiday", "benefit", "employee",
            "work", "salary", "bonus", "time off", "sick", "remote",
            "office", "product", "api", "integration", "technical"
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in doc_keywords)
    
    async def process_query(
        self,
        query: str,
        session_id: str = "default",
        use_tools: bool = True
    ) -> Dict[str, Any]:
        """
        Process a user query and return a response.
        
        Args:
            query: User's question or request
            session_id: Session identifier for memory
            use_tools: Whether to enable tool calling
            
        Returns:
            Dictionary with answer, sources, and metadata
        """
        # Add user message to memory
        self.memory.add_message(session_id, "user", query)
        
        # Check if we should strongly suggest RAG
        should_search = self._should_use_rag(query)
        
        # Build messages for LLM
        system_content = """You are a helpful AI assistant with access to company documents and tools.
            
Your capabilities:
1. Search company documents (Policies, FAQs, API Docs) for specific information. ALWAYS search documents first if the user asks about company rules, products, or technical details.
2. Answer general questions using your knowledge.
3. Perform calculations when needed.
4. Provide the current time.

When answering based on documents:
- If the answer is explicitly stated in the retrieved documents, you must use that value. Do not assume or generalize.
- If the answer is NOT in the documents, explicitly state that you could not find the information.
- Cite sources clearly.
- Be clear and concise.
- Do not make up policies that are not in the text."""

        if should_search:
            system_content += "\n\nIMPORTANT: The user is asking about a topic (vacation/policy/technical) that is likely covered in the company documents. Please use the 'search_documents' tool to find the answer."

        system_message = {
            "role": "system",
            "content": system_content
        }
        
        context_messages = self.memory.get_context_messages(session_id, limit=10)
        messages = [system_message] + context_messages
        
        # Prepare response
        sources = []
        tool_calls_made = []
        
        try:
            # Make initial LLM call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS if use_tools else None,
                temperature=settings.temperature,
                max_tokens=settings.max_tokens
            )
            
            message = response.choices[0].message
            
            # Handle tool calls
            if message.tool_calls:
                # Add assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })
                
                # Execute each tool call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    # Execute tool
                    tool_result = self._execute_tool(function_name, function_args)
                    tool_calls_made.append({
                        "tool": function_name,
                        "arguments": function_args,
                        "result": tool_result
                    })
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
                    
                    # Track sources if document search
                    if function_name == "search_documents":
                        sources.append(f"Document search: {function_args.get('query')}")
                
                # Force the model to answer based on results
                messages.append({
                    "role": "user",
                    "content": "SYSTEM INSTRUCTION: The tool results are provided above. Please use them to answer the original question in plain natural language. \n\nCRITICAL: If the answer is explicitly stated in the retrieved documents, you must use that value. Do not assume or generalize. If it's not there, say so. DO NOT output any JSON."
                })

                # Get final response with tool results
                final_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=settings.temperature,
                    max_tokens=settings.max_tokens
                )
                
                answer = final_response.choices[0].message.content
                
            # Fallback: Check if content contains a JSON tool call (for Phi-4 and smaller models)
            elif message.content and "search_documents" in message.content and ("{" in message.content or "[" in message.content):
                try:
                    # Clean up content to find JSON
                    content = message.content
                    # Remove markdown code blocks
                    content = content.replace("```json", "").replace("```", "").strip()
                    
                    import re
                    # Look for JSON structure (object or list)
                    json_match = re.search(r'(\{.*\}|\[.*\])', content, re.DOTALL)
                    
                    if json_match:
                        json_str = json_match.group(0)
                        # Fix common LLM JSON errors
                        if "'" in json_str and '"' not in json_str:
                            json_str = json_str.replace("'", '"')
                        
                        try:
                            tool_data = json.loads(json_str)
                            
                            # Handle list of tool calls
                            if isinstance(tool_data, list):
                                tool_data = tool_data[0] # Just take the first one
                                
                            # Handle OpenAI style {"type": "function", "function": {...}}
                            if "function" in tool_data:
                                tool_data = tool_data["function"]
                                
                            if "name" in tool_data and tool_data["name"] == "search_documents":
                                # It's a manual tool call!
                                function_name = "search_documents"
                                function_args = tool_data.get("arguments", {})
                                
                                # Handle string arguments
                                if isinstance(function_args, str):
                                    try:
                                        function_args = json.loads(function_args.replace("'", '"'))
                                    except:
                                        pass
                                    
                                # Execute tool
                                tool_result = self._execute_tool(function_name, function_args)
                                tool_calls_made.append({
                                    "tool": function_name,
                                    "arguments": function_args,
                                    "result": tool_result
                                })
                                sources.append(f"Document search: {function_args.get('query')}")
                                
                                # Add context to messages and ask again
                                messages.append({"role": "assistant", "content": message.content})
                                messages.append({
                                    "role": "user", 
                                    "content": f"SYSTEM: The tool returned the following information: {tool_result}\n\nINSTRUCTION: Please provide a natural language answer to the original question based ONLY on this information. \n\nCRITICAL: If the answer is explicitly stated in the retrieved documents, you must use that value. Do not assume or generalize. If it's not there, say so. DO NOT output any JSON."
                                })
                                
                                # Get final response
                                final_response = self.client.chat.completions.create(
                                    model=self.model,
                                    messages=messages,
                                    temperature=settings.temperature,
                                    max_tokens=settings.max_tokens
                                )
                                answer = final_response.choices[0].message.content
                            else:
                                answer = message.content
                        except Exception as e:
                           # JSON parse failed
                           answer = message.content
                    else:
                        answer = message.content
                except Exception as e:
                    print(f"Fallback parsing failed: {e}")
                    answer = message.content
            else:
                answer = message.content
            
            # Add assistant response to memory
            self.memory.add_message(
                session_id,
                "assistant",
                answer,
                {"tool_calls": tool_calls_made, "sources": sources}
            )
            
            return {
                "answer": answer,
                "sources": sources,
                "tool_calls": tool_calls_made,
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            error_msg = f"Error processing query: {str(e)}"
            self.memory.add_message(session_id, "assistant", error_msg, {"error": True})
            return {
                "answer": error_msg,
                "sources": [],
                "tool_calls": [],
                "session_id": session_id,
                "error": str(e)
            }
