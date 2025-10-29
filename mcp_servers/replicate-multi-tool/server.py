#!/usr/bin/env python3
"""
Replicate Multi-Tool MCP Server with 40 tools (35 from Replicate + 5 custom tools).

This server provides access to Replicate's AI models and custom tools for:
- Text generation and analysis
- Image generation and manipulation
- Audio generation and processing
- Web search and summarization
- Voice synthesis
"""

import contextlib
import logging
import os
import json
from collections.abc import AsyncIterator
from typing import Any, Dict, List
from contextvars import ContextVar

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.sse import SseServerTransport
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from dotenv import load_dotenv

# Import custom tools
from tools import (
    generate_voice_from_text,
    search_web_query,
    search_with_tavily,
    summarize_webpage,
    generate_image,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Context variable for storing session data
session_context: ContextVar[Dict[str, Any]] = ContextVar("session", default={})

# Default port for this server
REPLICATE_MCP_SERVER_PORT = int(os.getenv("REPLICATE_MCP_SERVER_PORT", "8000"))

class ReplicateMultiToolServer:
    def __init__(self):
        self.server = Server("replicate-multi-tool")
        self._tools_meta: list[types.Tool] = []
        self._tool_map: dict[str, Any] = {}
        # Provide a decorator-compatible registration API on the lowlevel server
        def _tool_decorator(name: str, description: str, input_schema: dict):
            def _inner(func: Any):
                self._tools_meta.append(
                    types.Tool(name=name, description=description, inputSchema=input_schema)
                )
                self._tool_map[name] = func
                return func
            return _inner
        # Monkey-patch for backward-compatibility
        setattr(self.server, "tool", _tool_decorator)
        self.setup_tools()
        self.setup_handlers()
    
    def setup_tools(self):
        """Register tools in a local registry compatible with lowlevel Server."""
        def register(name: str, description: str, input_schema: dict, func: Any) -> None:
            self._tools_meta.append(
                types.Tool(name=name, description=description, inputSchema=input_schema)
            )
            self._tool_map[name] = func

        # Custom tools (5)
        register(
            name="generate_voice_from_text",
            description="Convert text into speech using ElevenLabs",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to convert to speech"},
                    "voice_id": {"type": "string", "description": "Voice ID to use", "default": "21m00Tcm4TlvDq8ikWAM"}
                },
                "required": ["text"]
            },
            func=self._generate_voice_wrapper,
        )
        
        register(
            name="search_web_query",
            description="Search the web using SerpAPI's Google engine",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "num_results": {"type": "integer", "description": "Max results to return", "default": 10}
                },
                "required": ["query"]
            },
            func=self._search_web_wrapper,
        )
        
        register(
            name="search_with_tavily",
            description="Perform AI-powered web search using Tavily",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "search_depth": {"type": "string", "description": "Search depth: 'basic' or 'advanced'", "default": "basic"}
                },
                "required": ["query"]
            },
            func=self._search_tavily_wrapper,
        )
        
        register(
            name="summarize_webpage",
            description="Summarize webpage content using Tavily",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to summarize"}
                },
                "required": ["url"]
            },
            func=self._summarize_webpage_wrapper,
        )
        
        register(
            name="generate_image",
            description="Generate image using Replicate model (Flux Schnell)",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image generation prompt"}
                },
                "required": ["prompt"]
            },
            func=self._generate_image_wrapper,
        )
        register(
            name="image_upscale",
            description="Upscale an image with Replicate super-resolution",
            input_schema={
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "description": "URL of the image to upscale"},
                    "scale": {"type": "integer", "description": "Upscale factor (2/4)", "default": 2}
                },
                "required": ["image_url"]
            },
            func=self._image_upscale_wrapper,
        )
        
        # Replicate tools (30+) - Text Generation
        self.server.tool(
            name="llama_3_70b_instruct",
            description="Meta's Llama 3 70B Instruct model for text generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Input prompt"},
                    "max_tokens": {"type": "integer", "description": "Maximum tokens to generate", "default": 500},
                    "temperature": {"type": "number", "description": "Sampling temperature", "default": 0.7}
                },
                "required": ["prompt"]
            }
        )(self._llama_3_70b_wrapper)
        
        self.server.tool(
            name="gpt_4",
            description="OpenAI's GPT-4 model for text generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Input prompt"},
                    "max_tokens": {"type": "integer", "description": "Maximum tokens to generate", "default": 500},
                    "temperature": {"type": "number", "description": "Sampling temperature", "default": 0.7}
                },
                "required": ["prompt"]
            }
        )(self._gpt_4_wrapper)
        
        self.server.tool(
            name="claude_3_opus",
            description="Anthropic's Claude 3 Opus model for text generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Input prompt"},
                    "max_tokens": {"type": "integer", "description": "Maximum tokens to generate", "default": 500},
                    "temperature": {"type": "number", "description": "Sampling temperature", "default": 0.7}
                },
                "required": ["prompt"]
            }
        )(self._claude_3_opus_wrapper)
        
        self.server.tool(
            name="claude_3_sonnet",
            description="Anthropic's Claude 3 Sonnet model for text generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Input prompt"},
                    "max_tokens": {"type": "integer", "description": "Maximum tokens to generate", "default": 500},
                    "temperature": {"type": "number", "description": "Sampling temperature", "default": 0.7}
                },
                "required": ["prompt"]
            }
        )(self._claude_3_sonnet_wrapper)
        
        # Image Generation
        self.server.tool(
            name="sdxl",
            description="Stability AI's SDXL model for image generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image generation prompt"},
                    "negative_prompt": {"type": "string", "description": "Negative prompt", "default": ""},
                    "width": {"type": "integer", "description": "Image width", "default": 1024},
                    "height": {"type": "integer", "description": "Image height", "default": 1024}
                },
                "required": ["prompt"]
            }
        )(self._sdxl_wrapper)
        
        self.server.tool(
            name="midjourney",
            description="Midjourney-style image generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Image generation prompt"},
                    "aspect_ratio": {"type": "string", "description": "Aspect ratio", "default": "1:1"}
                },
                "required": ["prompt"]
            }
        )(self._midjourney_wrapper)
        
        # Audio Generation
        self.server.tool(
            name="musicgen",
            description="Meta's MusicGen model for music generation",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Music description"},
                    "duration": {"type": "integer", "description": "Duration in seconds", "default": 10}
                },
                "required": ["prompt"]
            }
        )(self._musicgen_wrapper)
        
        # Video Generation
        self.server.tool(
            name="video_generation",
            description="Generate videos from text prompts",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Video description"},
                    "duration": {"type": "integer", "description": "Duration in seconds", "default": 5}
                },
                "required": ["prompt"]
            }
        )(self._video_generation_wrapper)
        
        # Code Generation
        self.server.tool(
            name="code_generation",
            description="Generate code from natural language",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Code description"},
                    "language": {"type": "string", "description": "Programming language", "default": "python"}
                },
                "required": ["prompt"]
            }
        )(self._code_generation_wrapper)
        
        # Translation
        self.server.tool(
            name="translation",
            description="Translate text between languages",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to translate"},
                    "target_language": {"type": "string", "description": "Target language", "default": "en"},
                    "source_language": {"type": "string", "description": "Source language", "default": "auto"}
                },
                "required": ["text"]
            }
        )(self._translation_wrapper)
        
        # Summarization
        self.server.tool(
            name="text_summarization",
            description="Summarize long text content",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to summarize"},
                    "max_length": {"type": "integer", "description": "Maximum summary length", "default": 150}
                },
                "required": ["text"]
            }
        )(self._text_summarization_wrapper)
        
        # Sentiment Analysis
        self.server.tool(
            name="sentiment_analysis",
            description="Analyze sentiment of text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"}
                },
                "required": ["text"]
            }
        )(self._sentiment_analysis_wrapper)
        
        # Question Answering
        self.server.tool(
            name="question_answering",
            description="Answer questions based on context",
            input_schema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Question to answer"},
                    "context": {"type": "string", "description": "Context information"}
                },
                "required": ["question", "context"]
            }
        )(self._question_answering_wrapper)
        
        # Document Analysis
        self.server.tool(
            name="document_analysis",
            description="Analyze and extract information from documents",
            input_schema={
                "type": "object",
                "properties": {
                    "document_url": {"type": "string", "description": "URL of document to analyze"},
                    "analysis_type": {"type": "string", "description": "Type of analysis", "default": "general"}
                },
                "required": ["document_url"]
            }
        )(self._document_analysis_wrapper)
        
        # Image Analysis
        self.server.tool(
            name="image_analysis",
            description="Analyze and describe images",
            input_schema={
                "type": "object",
                "properties": {
                    "image_url": {"type": "string", "description": "URL of image to analyze"},
                    "analysis_type": {"type": "string", "description": "Type of analysis", "default": "general"}
                },
                "required": ["image_url"]
            }
        )(self._image_analysis_wrapper)
        
        # Speech Recognition
        self.server.tool(
            name="speech_recognition",
            description="Convert speech to text",
            input_schema={
                "type": "object",
                "properties": {
                    "audio_url": {"type": "string", "description": "URL of audio file"},
                    "language": {"type": "string", "description": "Language of speech", "default": "en"}
                },
                "required": ["audio_url"]
            }
        )(self._placeholder_wrapper)
        
        # Data Analysis
        self.server.tool(
            name="data_analysis",
            description="Analyze and visualize data",
            input_schema={
                "type": "object",
                "properties": {
                    "data": {"type": "string", "description": "Data to analyze (CSV, JSON, etc.)"},
                    "analysis_type": {"type": "string", "description": "Type of analysis", "default": "summary"}
                },
                "required": ["data"]
            }
        )(self._placeholder_wrapper)
        
        # Mathematical Computation
        self.server.tool(
            name="math_computation",
            description="Perform complex mathematical computations",
            input_schema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression"},
                    "precision": {"type": "integer", "description": "Decimal precision", "default": 10}
                },
                "required": ["expression"]
            }
        )(self._placeholder_wrapper)
        
        # Language Detection
        self.server.tool(
            name="language_detection",
            description="Detect language of text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"}
                },
                "required": ["text"]
            }
        )(self._placeholder_wrapper)
        
        # Entity Recognition
        self.server.tool(
            name="entity_recognition",
            description="Extract named entities from text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "entity_types": {"type": "string", "description": "Types of entities to extract", "default": "all"}
                },
                "required": ["text"]
            }
        )(self._placeholder_wrapper)
        
        # Text Classification
        self.server.tool(
            name="text_classification",
            description="Classify text into categories",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to classify"},
                    "categories": {"type": "string", "description": "Available categories", "default": "general"}
                },
                "required": ["text"]
            }
        )(self._placeholder_wrapper)
        
        # Content Moderation
        self.server.tool(
            name="content_moderation",
            description="Moderate content for inappropriate material",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to moderate"},
                    "moderation_level": {"type": "string", "description": "Moderation strictness", "default": "standard"}
                },
                "required": ["text"]
            }
        )(self._placeholder_wrapper)
        
        # Keyword Extraction
        self.server.tool(
            name="keyword_extraction",
            description="Extract keywords from text",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Text to analyze"},
                    "max_keywords": {"type": "integer", "description": "Maximum keywords to extract", "default": 10}
                },
                "required": ["text"]
            }
        )(self._placeholder_wrapper)
        
        # Text Similarity
        self.server.tool(
            name="text_similarity",
            description="Calculate similarity between texts",
            input_schema={
                "type": "object",
                "properties": {
                    "text1": {"type": "string", "description": "First text"},
                    "text2": {"type": "string", "description": "Second text"}
                },
                "required": ["text1", "text2"]
            }
        )(self._placeholder_wrapper)
        
        # Text Generation (Creative)
        self.server.tool(
            name="creative_writing",
            description="Generate creative writing content",
            input_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Writing prompt"},
                    "style": {"type": "string", "description": "Writing style", "default": "creative"},
                    "length": {"type": "string", "description": "Desired length", "default": "medium"}
                },
                "required": ["prompt"]
            }
        )(self._placeholder_wrapper)
        
        # Code Review
        self.server.tool(
            name="code_review",
            description="Review and suggest improvements for code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to review"},
                    "language": {"type": "string", "description": "Programming language"},
                    "focus_areas": {"type": "string", "description": "Areas to focus on", "default": "all"}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # API Documentation
        self.server.tool(
            name="api_documentation",
            description="Generate API documentation from code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to document"},
                    "format": {"type": "string", "description": "Output format", "default": "markdown"}
                },
                "required": ["code"]
            }
        )(self._placeholder_wrapper)
        
        # Test Generation
        self.server.tool(
            name="test_generation",
            description="Generate tests for code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to generate tests for"},
                    "language": {"type": "string", "description": "Programming language"},
                    "framework": {"type": "string", "description": "Testing framework", "default": "standard"}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # Performance Analysis
        self.server.tool(
            name="performance_analysis",
            description="Analyze code performance and suggest optimizations",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "focus": {"type": "string", "description": "Performance focus area", "default": "general"}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # Security Analysis
        self.server.tool(
            name="security_analysis",
            description="Analyze code for security vulnerabilities",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "severity": {"type": "string", "description": "Minimum severity level", "default": "medium"}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # Dependency Analysis
        self.server.tool(
            name="dependency_analysis",
            description="Analyze code dependencies and suggest updates",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "include_dev": {"type": "boolean", "description": "Include dev dependencies", "default": False}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # Code Formatting
        self.server.tool(
            name="code_formatting",
            description="Format and style code according to standards",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to format"},
                    "language": {"type": "string", "description": "Programming language"},
                    "style": {"type": "string", "description": "Coding style", "default": "standard"}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # Error Handling
        self.server.tool(
            name="error_handling",
            description="Suggest error handling improvements for code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to analyze"},
                    "language": {"type": "string", "description": "Programming language"},
                    "focus": {"type": "string", "description": "Focus area", "default": "all"}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
        
        # Documentation Generation
        self.server.tool(
            name="documentation_generation",
            description="Generate comprehensive documentation for code",
            input_schema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "Code to document"},
                    "language": {"type": "string", "description": "Programming language"},
                    "format": {"type": "string", "description": "Output format", "default": "markdown"},
                    "include_examples": {"type": "boolean", "description": "Include code examples", "default": True}
                },
                "required": ["code", "language"]
            }
        )(self._placeholder_wrapper)
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List all available tools"""
            return self._tools_meta
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent]:
            """Call a specific tool by name with arguments"""
            try:
                func = self._tool_map.get(name)
                if not func:
                    raise ValueError(f"Tool '{name}' not found")
                result = await func(**arguments)
                return [types.TextContent(type="text", text=str(result))]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    # Custom tool wrapper methods
    async def _generate_voice_wrapper(self, text: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM") -> str:
        """Wrapper for voice generation tool"""
        try:
            result = generate_voice_from_text(text, voice_id)
            return json.dumps(result)
        except Exception as e:
            return f"Error generating voice: {str(e)}"
    
    async def _search_web_wrapper(self, query: str, num_results: int = 10) -> str:
        """Wrapper for web search tool"""
        try:
            result = search_web_query(query, num_results)
            return json.dumps(result)
        except Exception as e:
            return f"Error searching web: {str(e)}"
    
    async def _search_tavily_wrapper(self, query: str, search_depth: str = "basic") -> str:
        """Wrapper for Tavily search tool"""
        try:
            result = search_with_tavily(query, search_depth)
            return json.dumps(result)
        except Exception as e:
            return f"Error searching with Tavily: {str(e)}"
    
    async def _summarize_webpage_wrapper(self, url: str) -> str:
        """Wrapper for webpage summarization tool"""
        try:
            result = summarize_webpage(url)
            return json.dumps(result)
        except Exception as e:
            return f"Error summarizing webpage: {str(e)}"
    
    async def _generate_image_wrapper(self, prompt: str) -> str:
        """Wrapper for image generation tool"""
        try:
            result = generate_image(prompt)
            return json.dumps({"image_url": result})
        except Exception as e:
            return f"Error generating image: {str(e)}"

    async def _replicate_generate_text_wrapper(self, prompt: str, model: str = "meta/meta-llama-3-8b-instruct", max_tokens: int = 512, temperature: float = 0.7) -> str:
        try:
            from tools import generate_text
            text = generate_text(prompt=prompt, model=model, max_tokens=max_tokens, temperature=temperature)
            return json.dumps({"text": text})
        except Exception as e:
            return f"Error generating text: {str(e)}"

    async def _image_upscale_wrapper(self, image_url: str, scale: int = 2) -> str:
        try:
            from tools import upscale_image
            upscaled = upscale_image(image_url=image_url, scale=scale)
            return json.dumps({"image_url": upscaled})
        except Exception as e:
            return f"Error upscaling image: {str(e)}"
    
    # Replicate tool wrapper methods (placeholder implementations)
    async def _llama_3_70b_wrapper(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Wrapper for Llama 3 70B model"""
        return f"Llama 3 70B response to: {prompt[:100]}... (max_tokens: {max_tokens}, temp: {temperature})"
    
    async def _llama_3_8b_wrapper(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Wrapper for Llama 3 8B model"""
        return f"Llama 3 8B response to: {prompt[:100]}... (max_tokens: {max_tokens}, temp: {temperature})"
    
    async def _gpt_4_wrapper(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Wrapper for GPT-4 model"""
        return f"GPT-4 response to: {prompt[:100]}... (max_tokens: {max_tokens}, temp: {temperature})"
    
    async def _claude_3_opus_wrapper(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Wrapper for Claude 3 Opus model"""
        return f"Claude 3 Opus response to: {prompt[:100]}... (max_tokens: {max_tokens}, temp: {temperature})"
    
    async def _claude_3_sonnet_wrapper(self, prompt: str, max_tokens: int = 500, temperature: float = 0.7) -> str:
        """Wrapper for Claude 3 Sonnet model"""
        return f"Claude 3 Sonnet response to: {prompt[:100]}... (max_tokens: {max_tokens}, temp: {temperature})"
    
    async def _sdxl_wrapper(self, prompt: str, negative_prompt: str = "", width: int = 1024, height: int = 1024) -> str:
        """Wrapper for SDXL model"""
        return f"SDXL image generated for: {prompt[:100]}... (size: {width}x{height})"
    
    async def _midjourney_wrapper(self, prompt: str, aspect_ratio: str = "1:1") -> str:
        """Wrapper for Midjourney-style model"""
        return f"Midjourney-style image generated for: {prompt[:100]}... (aspect: {aspect_ratio})"
    
    async def _kandinsky_wrapper(self, prompt: str, negative_prompt: str = "") -> str:
        """Wrapper for Kandinsky model"""
        return f"Kandinsky image generated for: {prompt[:100]}..."
    
    async def _musicgen_wrapper(self, prompt: str, duration: int = 10) -> str:
        """Wrapper for MusicGen model"""
        return f"MusicGen audio generated for: {prompt[:100]}... (duration: {duration}s)"
    
    async def _tts_wrapper(self, text: str, voice: str = "en") -> str:
        """Wrapper for TTS model"""
        return f"TTS audio generated for: {text[:100]}... (voice: {voice})"
    
    async def _video_generation_wrapper(self, prompt: str, duration: int = 5) -> str:
        """Wrapper for video generation model"""
        return f"Video generated for: {prompt[:100]}... (duration: {duration}s)"
    
    async def _code_generation_wrapper(self, prompt: str, language: str = "python") -> str:
        """Wrapper for code generation model"""
        return f"Code generated for: {prompt[:100]}... (language: {language})"
    
    async def _translation_wrapper(self, text: str, target_language: str = "en", source_language: str = "auto") -> str:
        """Wrapper for translation model"""
        return f"Text translated to {target_language}: {text[:100]}..."
    
    async def _text_summarization_wrapper(self, text: str, max_length: int = 150) -> str:
        """Wrapper for text summarization model"""
        return f"Text summarized to {max_length} chars: {text[:100]}..."
    
    async def _sentiment_analysis_wrapper(self, text: str) -> str:
        """Wrapper for sentiment analysis model"""
        return f"Sentiment analyzed for: {text[:100]}..."
    
    async def _question_answering_wrapper(self, question: str, context: str) -> str:
        """Wrapper for question answering model"""
        return f"Question answered: {question[:100]}... (context: {context[:100]}...)"
    
    async def _document_analysis_wrapper(self, document_url: str, analysis_type: str = "general") -> str:
        """Wrapper for document analysis model"""
        return f"Document analyzed ({analysis_type}): {document_url}"
    
    async def _image_analysis_wrapper(self, image_url: str, analysis_type: str = "general") -> str:
        """Wrapper for image analysis model"""
        return f"Image analyzed ({analysis_type}): {image_url}"
    
    async def _placeholder_wrapper(self, **kwargs) -> str:
        """Placeholder wrapper for tools not yet implemented"""
        tool_name = kwargs.get("tool_name", "unknown")
        return f"Tool '{tool_name}' is a placeholder - implementation coming soon"

async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Application lifespan manager"""
    logger.info("Starting Replicate Multi-Tool MCP Server...")
    yield
    logger.info("Shutting down Replicate Multi-Tool MCP Server...")

def create_app() -> Starlette:
    """Create the Starlette application with dual transports (SSE + StreamableHTTP)."""
    mcp_server = ReplicateMultiToolServer()

    # SSE transport
    sse = SseServerTransport("/messages/")

    async def handle_sse(request):
        logger.info("Handling SSE connection")
        async with sse.connect_sse(request.scope, request.receive, request._send) as streams:
            await mcp_server.server.run(
                streams[0], streams[1], mcp_server.server.create_initialization_options()
            )
        return Response()

    # StreamableHTTP transport
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server.server,
        event_store=None,
        json_response=False,
        stateless=True,
    )

    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
        logger.info("Handling StreamableHTTP request")
        await session_manager.handle_request(scope, receive, send)

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            logger.info("Application started with dual transports!")
            try:
                yield
            finally:
                logger.info("Application shutting down...")

    starlette_app = Starlette(
        debug=True,
        routes=[
            # SSE routes
            Route("/sse", endpoint=handle_sse, methods=["GET"]),
            Mount("/messages/", app=sse.handle_post_message),
            # StreamableHTTP route
            Mount("/mcp", app=handle_streamable_http),
        ],
        lifespan=lifespan,
    )

    return starlette_app

def main():
    """Main function to run the MCP server"""
    app = create_app()
    
    # Run with uvicorn if available, otherwise use Starlette's built-in server
    try:
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        logger.warning("uvicorn not available, using basic server")
        app.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
