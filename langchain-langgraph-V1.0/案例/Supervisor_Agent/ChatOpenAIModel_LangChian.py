import time
import json
from typing import Any, Dict, Iterator, List, Optional, AsyncIterator, Sequence, Union
from collections.abc import AsyncIterator, Callable, Iterator, Sequence
from langchain_core.runnables import Runnable
from langchain_core.utils.function_calling import convert_to_openai_tool
from langchain_core.language_models import LanguageModelInput
from langchain_core.tools import BaseTool
from openai import AsyncOpenAI, OpenAI, AsyncAzureOpenAI, AzureOpenAI
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, AIMessageChunk, BaseMessage, ChatMessage, HumanMessage, SystemMessage, ToolMessage


class ChatOpenAIModel(BaseChatModel):
    """
    使用langchain 实现自定义模型，所有兼容 opanai 模型接口，都可以使用该模型接口。
    官网链接：
    https://python.langchain.com/docs/how_to/custom_chat_model/#base-chat-model
    """

    api_key: str = ""
    model_name: str = Field(default="gpt-5", alias="model")
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    timeout: Optional[int] = 60
    base_url: str = "https://api.openai.com/v1"
    extra_body: Optional[Dict[str, Any]] = None  # 额外的请求参数，如思考功能

    # 微软opanai接口
    use_azure: Optional[bool] = False
    azure_api_key: str = ""
    azure_endpoint: Optional[str] = "https://llm-east-us2-test.openai.azure.com/"
    azure_api_version: Optional[str] = "2025-03-01-preview"
    
    # OpenAI客户端实例
    client: Optional[OpenAI] = None
    async_client: Optional[AsyncOpenAI] = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create OpenAI client
        if not self.use_azure:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            self.async_client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        else:
            self.client = AzureOpenAI(
                api_key=self.azure_api_key,
                azure_endpoint=self.azure_endpoint,
                api_version=self.azure_api_version,
            )   
            self.async_client = AsyncAzureOpenAI(
                api_key=self.azure_api_key,
                azure_endpoint=self.azure_endpoint,
                api_version=self.azure_api_version,
            )   

    @property
    def _llm_type(self) -> str:
        """Get the type of language model used by this chat model."""
        return "openai-compatible-chat-model"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return a dictionary of identifying parameters.

        This information is used by the LangChain callback system, which
        is used for tracing purposes make it possible to monitor LLMs.
        """
        requests_params = {
            "model": self.model_name,
            "timeout": self.timeout
        }
        if self.temperature is not None:
            requests_params["temperature"] = self.temperature
        if self.max_tokens is not None:
            requests_params["max_tokens"] = self.max_tokens
        if self.extra_body is not None:
            requests_params["extra_body"] = self.extra_body
        return requests_params

    def _convert_messages_to_openai_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to OpenAI format."""
        openai_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                openai_messages.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                openai_messages.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                openai_messages.append({"role": "system", "content": message.content})
            else:
                openai_messages.append({"role": "user", "content": message.content})
        return openai_messages

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Override the _generate method to implement the chat model logic.

        This calls the OpenAI-compatible API to generate a response to the input prompt.

        Args:
            messages: the prompt composed of a list of messages.
            stop: a list of strings on which the model should stop generating.
                  If generation stops due to a stop token, the stop token itself
                  SHOULD BE INCLUDED as part of the output. This is not enforced
                  across models right now, but it's a good practice to follow since
                  it makes it much easier to parse the output of the model
                  downstream and understand why generation stopped.
            run_manager: A run manager with callbacks for the LLM.
        """
        # Convert LangChain messages to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare the request parameters - combine model parameters with messages
        request_params = {
            **self._identifying_params,  # 使用模型的识别参数
            "messages": openai_messages,  # 添加消息内容
        }
        if stop is not None:
            request_params["stop"] = stop
        if 'tools' in kwargs:
            request_params['tools'] = kwargs['tools']
            
        try:
            # Make the API request
            start_time = time.time()
            response = self.client.chat.completions.create(**request_params)
            end_time = time.time()
            
            return self._create_chat_result(response.model_dump_json(), end_time - start_time)
            
        except Exception as e:
            raise Exception(f"Error calling API: {str(e)}. The request params are: {request_params}")

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Stream the output of the model.

        This method calls the OpenAI-compatible streaming API to generate output in a streaming fashion.

        Args:
            messages: the prompt composed of a list of messages.
            stop: a list of strings on which the model should stop generating.
                  If generation stops due to a stop token, the stop token itself
                  SHOULD BE INCLUDED as part of the output. This is not enforced
                  across models right now, but it's a good practice to follow since
                  it makes it much easier to parse the output of the model
                  downstream and understand why generation stopped.
            run_manager: A run manager with callbacks for the LLM.
        """
        # Convert LangChain messages to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare the request parameters
        request_params = {
            **self._identifying_params,  # 使用模型的识别参数
            "messages": openai_messages,  # 添加消息内容
            "stream": True,
        }
        if stop is not None:
            request_params["stop"] = stop
            
        try:
            # Make the streaming API request
            start_time = time.time()
            stream = self.client.chat.completions.create(**request_params)
            
            # 初始化计数器和内容收集器
            chunk_count = 0
            reasoning_chunk_count = 0
            content_chunk_count = 0
            reasoning_content_full = ""  # 收集完整的思考内容
            content_full = ""  # 收集完整的回答内容
            
            # Process the streaming response
            for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    chunk_start_time = time.time()
                    
                    # 处理思考内容
                    reasoning_content = delta.reasoning_content if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None else ""
                    if reasoning_content:
                        chunk_count += 1
                        reasoning_chunk_count += 1
                        reasoning_content_full += reasoning_content  # 收集完整思考内容
                        chat_chunk = ChatGenerationChunk(
                            message=AIMessageChunk(
                                content=reasoning_content,
                                additional_kwargs={
                                    "request_params": self._identifying_params,
                                    "base_url": self.base_url,
                                    "langchain_llm_type": self._llm_type,
                                },
                                response_metadata={
                                    "content_type": "reasoning",  # 标记为思考内容
                                    "chunk_index": str(chunk_count),
                                },
                            )
                        )
                        if run_manager:
                            run_manager.on_llm_new_token(reasoning_content, chunk=chat_chunk)
                        yield chat_chunk
                    
                    # 处理正文内容
                    content = delta.content if delta and delta.content is not None else ""
                    if content:
                        chunk_count += 1
                        content_chunk_count += 1
                        content_full += content  # 收集完整回答内容
                        chat_chunk = ChatGenerationChunk(
                            message=AIMessageChunk(
                                content=content,
                                additional_kwargs={
                                    "request_params": self._identifying_params,
                                    "base_url": self.base_url,
                                    "langchain_llm_type": self._llm_type,
                                },
                                response_metadata={
                                    "content_type": "content",  # 标记为正文内容
                                    "chunk_index": str(chunk_count),
                                },
                            )
                        )
                        if run_manager:
                            run_manager.on_llm_new_token(content, chunk=chat_chunk)
                        yield chat_chunk
            
            # Let's add some other information (e.g., response metadata)
            end_time = time.time()
            final_chunk = ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    additional_kwargs={
                        "request_params": self._identifying_params,
                        "base_url": self.base_url,
                        "langchain_llm_type": self._llm_type,
                    },
                    response_metadata={
                        "content_type": "end",
                        "model_name": self.model_name,
                        "latency": str(end_time - start_time),
                        "total_chunks": str(chunk_count),
                        "reasoning_chunks": str(reasoning_chunk_count),
                        "content_chunks": str(content_chunk_count),
                        "reasoning_content_full": reasoning_content_full,  # 添加完整思考内容
                        "content_full": content_full,  # 添加完整回答内容
                    },
                )
            )
            if run_manager:
                run_manager.on_llm_new_token("", chunk=final_chunk)
            yield final_chunk
            
        except Exception as e:
            raise Exception(f"Error calling API: {str(e)}. The request params are: {request_params}")

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Async version of _generate method to implement the chat model logic.

        This calls the OpenAI-compatible API asynchronously to generate a response to the input prompt.

        Args:
            messages: the prompt composed of a list of messages.
            stop: a list of strings on which the model should stop generating.
                  If generation stops due to a stop token, the stop token itself
                  SHOULD BE INCLUDED as part of the output. This is not enforced
                  across models right now, but it's a good practice to follow since
                  it makes it much easier to parse the output of the model
                  downstream and understand why generation stopped.
            run_manager: A run manager with callbacks for the LLM.
        """
        # Convert LangChain messages to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare the request parameters - combine model parameters with messages
        request_params = {
            **self._identifying_params,  # 使用模型的识别参数
            "messages": openai_messages,  # 添加消息内容
        }
        if stop is not None:
            request_params["stop"] = stop
        if 'tools' in kwargs:
            request_params['tools'] = kwargs['tools']

        try:
            # Make the async API request
            start_time = time.time()
            response = await self.async_client.chat.completions.create(**request_params)
            end_time = time.time()
            
            return self._create_chat_result(response.model_dump_json(), end_time - start_time)
            
        except Exception as e:
            raise Exception(f"Error calling API: {str(e)}. The request params are: {request_params}")

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncIterator[ChatGenerationChunk]:
        """Async version of _stream method to stream the output of the model.

        This method calls the OpenAI-compatible streaming API asynchronously to generate output in a streaming fashion.

        Args:
            messages: the prompt composed of a list of messages.
            stop: a list of strings on which the model should stop generating.
                  If generation stops due to a stop token, the stop token itself
                  SHOULD BE INCLUDED as part of the output. This is not enforced
                  across models right now, but it's a good practice to follow since
                  it makes it much easier to parse the output of the model
                  downstream and understand why generation stopped.
            run_manager: A run manager with callbacks for the LLM.
        """
        # Convert LangChain messages to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(messages)
        
        # Prepare the request parameters - combine model parameters with messages
        request_params = {
            **self._identifying_params,  # 使用模型的识别参数
            "messages": openai_messages,  # 添加消息内容
            "stream": True,  # 启用流式响应
        }
        if stop is not None:
            request_params["stop"] = stop
            
        try:
            # Make the async streaming API request
            start_time = time.time()
            stream = await self.async_client.chat.completions.create(**request_params)
            
            # 初始化计数器和内容收集器
            chunk_count = 0
            reasoning_chunk_count = 0
            content_chunk_count = 0
            reasoning_content_full = ""  # 收集完整的思考内容
            content_full = ""  # 收集完整的回答内容
            
            # Process the streaming response
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    chunk_start_time = time.time()
                    
                    # 处理思考内容
                    reasoning_content = delta.reasoning_content if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None else ""
                    if reasoning_content:
                        chunk_count += 1
                        reasoning_chunk_count += 1
                        reasoning_content_full += reasoning_content  # 收集完整思考内容
                        chat_chunk = ChatGenerationChunk(
                            message=AIMessageChunk(
                                content=reasoning_content,
                                additional_kwargs={
                                    "request_params": self._identifying_params,
                                    "base_url": self.base_url,
                                    "langchain_llm_type": self._llm_type,
                                },
                                response_metadata={
                                    "content_type": "reasoning",  # 标记为思考内容
                                    "chunk_index": str(chunk_count),
                                },
                            )
                        )
                        if run_manager:
                            await run_manager.on_llm_new_token(reasoning_content, chunk=chat_chunk)
                        yield chat_chunk
                    
                    # 处理正文内容
                    content = delta.content if delta and delta.content is not None else ""
                    if content:
                        chunk_count += 1
                        content_chunk_count += 1
                        content_full += content  # 收集完整回答内容
                        chat_chunk = ChatGenerationChunk(
                            message=AIMessageChunk(
                                content=content,
                                additional_kwargs={
                                    "request_params": self._identifying_params,
                                    "base_url": self.base_url,
                                    "langchain_llm_type": self._llm_type,
                                },
                                response_metadata={
                                    "content_type": "content",  # 标记为正文内容
                                    "chunk_index": str(chunk_count),
                                },
                            )
                        )
                        if run_manager:
                            await run_manager.on_llm_new_token(content, chunk=chat_chunk)
                        yield chat_chunk
            
            # Let's add some other information (e.g., response metadata)
            end_time = time.time()
            final_chunk = ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    additional_kwargs={
                        "request_params": self._identifying_params,
                        "base_url": self.base_url,
                        "langchain_llm_type": self._llm_type,
                    },
                    response_metadata={
                        "content_type": "end",
                        "model_name": self.model_name,
                        "latency": str(end_time - start_time),
                        "total_chunks": str(chunk_count),
                        "reasoning_chunks": str(reasoning_chunk_count),
                        "content_chunks": str(content_chunk_count),
                        "reasoning_content_full": reasoning_content_full,  # 添加完整思考内容
                        "content_full": content_full,  # 添加完整回答内容
                    },
                )
            )
            if run_manager:
                await run_manager.on_llm_new_token("", chunk=final_chunk)
            yield final_chunk
            
        except Exception as e:
            raise Exception(f"Error calling API: {str(e)}. The request params are: {request_params}")

    def bind_tools(
        self,
        tools: Sequence[dict[str, Any] | type | Callable | BaseTool],
        *,
        tool_choice: dict | str | bool | None = None,
        strict: bool | None = None,
        parallel_tool_calls: bool | None = None,
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        """Bind tool-like objects to this chat model.

        Assumes model is compatible with OpenAI tool-calling API.

        Args:
            tools: A list of tool definitions to bind to this chat model.
                Supports any tool definition handled by
                `langchain_core.utils.function_calling.convert_to_openai_tool`.
            tool_choice: Which tool to require the model to call. Options are:

                - `str` of the form `'<<tool_name>>'`: calls `<<tool_name>>` tool.
                - `'auto'`: automatically selects a tool (including no tool).
                - `'none'`: does not call a tool.
                - `'any'` or `'required'` or `True`: force at least one tool to be called.
                - `dict` of the form `{"type": "function", "function": {"name": <<tool_name>>}}`: calls `<<tool_name>>` tool.
                - `False` or `None`: no effect, default OpenAI behavior.
            strict: If `True`, model output is guaranteed to exactly match the JSON Schema
                provided in the tool definition. The input schema will also be validated according to the
                [supported schemas](https://platform.openai.com/docs/guides/structured-outputs/supported-schemas?api-mode=responses#supported-schemas).
                If `False`, input schema will not be validated and model output will not
                be validated. If `None`, `strict` argument will not be passed to the model.
            parallel_tool_calls: Set to `False` to disable parallel tool use.
                Defaults to `None` (no specification, which allows parallel tool use).
            kwargs: Any additional parameters are passed directly to `bind`.
        """  # noqa: E501
        if parallel_tool_calls is not None:
            kwargs["parallel_tool_calls"] = parallel_tool_calls
        formatted_tools = [
            convert_to_openai_tool(tool, strict=strict) for tool in tools
        ]
        tool_names = []
        for tool in formatted_tools:
            if "function" in tool:
                tool_names.append(tool["function"]["name"])
            elif "name" in tool:
                tool_names.append(tool["name"])
            else:
                pass
        if tool_choice:
            if isinstance(tool_choice, str):
                # tool_choice is a tool/function name
                if tool_choice in tool_names:
                    tool_choice = {
                        "type": "function",
                        "function": {"name": tool_choice},
                    }
                # 'any' is not natively supported by OpenAI API.
                # We support 'any' since other models use this instead of 'required'.
                elif tool_choice == "any":
                    tool_choice = "required"
                else:
                    pass
            elif isinstance(tool_choice, bool):
                tool_choice = "required"
            elif isinstance(tool_choice, dict):
                pass
            else:
                msg = (
                    f"Unrecognized tool_choice type. Expected str, bool or dict. "
                    f"Received: {tool_choice}"
                )
                raise ValueError(msg)
            kwargs["tool_choice"] = tool_choice
        return super().bind(tools=formatted_tools, **kwargs)

    def _create_chat_result(self, response: Union[dict, BaseModel], latency: float) -> ChatResult:
        """格式化输出结果"""
        generations = []
        if not isinstance(response, dict):
            response = json.loads(response)
        for res in response["choices"]:
            message = self._convert_dict_to_message(res["message"], response, latency)
            generation_info = dict(finish_reason=res.get("finish_reason"))
            generations.append(
                ChatGeneration(message=message, generation_info=generation_info)
            )
        token_usage = response.get("usage", {})
        llm_output = {
            "token_usage": token_usage,
            "model_name": self.model_name,
        }
        return ChatResult(generations=generations, llm_output=llm_output)

    def _convert_dict_to_message(self, dct: Dict[str, Any], response: dict, latency) -> BaseMessage:
        """转换为各个对应角色类型，针对非流式响应，因为非流式适应 func call"""
        role = dct.get("role")
        content = dct.get("content", "")
        # 确保content不为None，如果为None则设为空字符串
        if content is None:
            content = ""
        if role == "system":
            return SystemMessage(content=content)
        if role == "user":
            return HumanMessage(content=content)
        if role == "assistant":
            additional_kwargs={
                    "request_params": self._identifying_params,
                    "base_url": self.base_url,
                    "langchain_llm_type": self._llm_type,
            }
            tool_calls = dct.get("tool_calls", None)
            if tool_calls is not None:
                additional_kwargs["tool_calls"] = tool_calls
            return AIMessage(  # 自定义封装返回内容
                content=content,
                additional_kwargs=additional_kwargs,  
                response_metadata={  # Use for response metadata
                    "model_name": self.model_name,
                    "finish_reason": response.get("choices", [{}])[0].get("finish_reason"),
                    "reasoning_content": response.get("choices", [{}])[0].get("message", {}).get('model_extra', {}).get('reasoning_content'),
                },
                usage_metadata={
                    "input_tokens": response.get("usage", {}).get("prompt_tokens", 0),
                    "output_tokens": response.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": response.get("usage", {}).get("total_tokens", 0),
                    "latency": latency,
                },
            )
        if role == "tool":
            additional_kwargs = {}
            if "name" in dct:
                additional_kwargs["name"] = dct["name"]
            return ToolMessage(
                content=content,
                tool_call_id=dct.get("tool_call_id"),
                additional_kwargs=additional_kwargs,
            )
        return ChatMessage(role=role, content=content) 


# Gemini
# API_KEY = "AIzaSyDJi6ax5l9vc4Z_-rUGTqwNjkYVQNbqdws"
# BASE_URL = "https://agent.smartedu.lenovo.com/v1beta/openai/"
# MODEL = "gemini-2.5-pro"
# extra_body={
#       'extra_body': {
#         "google": {
#           "thinking_config": {
#             "thinking_budget": 512,
#             "include_thoughts": False
#           }
#         }
#       }
#     }
# model = ChatOpenAIModel(
#     api_key=API_KEY,
#     base_url=BASE_URL,
#     extra_body=extra_body,
#     model=MODEL
# )


# Azure
MODEL = "gpt-4.1"
azure_api_version='2025-03-01-preview'
azure_endpoint=""
azure_api_key=""

model = ChatOpenAIModel(
        model=MODEL,
        use_azure=True,  # 使用微软openai接口
        azure_api_key=azure_api_key,
        azure_endpoint=azure_endpoint,
        azure_api_version=azure_api_version,
)