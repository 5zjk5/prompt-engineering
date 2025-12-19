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
                msg = {"role": "assistant", "content": message.content}
                # Check for tool_calls and convert them to OpenAI format
                if hasattr(message, 'tool_calls') and message.tool_calls:
                    openai_tool_calls = []
                    for tc in message.tool_calls:
                        openai_tool_calls.append(
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"]),
                                },
                            }
                        )
                    msg["tool_calls"] = openai_tool_calls
                openai_messages.append(msg)
            elif isinstance(message, SystemMessage):
                openai_messages.append({"role": "system", "content": message.content})
            elif isinstance(message, ToolMessage):
                openai_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": message.tool_call_id,
                        "content": message.content,
                    }
                )
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


# Test the sync methods
def test_sync_methods():
    """Test the sync methods of the custom model"""
    print("=" * 50)
    print("Testing sync methods")
    print("=" * 50)
    
    # Create a message
    message = HumanMessage(content="说出数字 123 不需要其他内容")

    # Test invoke 1
    print("\n--- Testing invoke 1 ---")
    response = model.invoke([message])
    print(response)

    # Test stream
    print("\n--- Testing stream ---")
    for chunk in model.stream([message]):
        print(chunk, end="\n", flush=True)
        print()
    print("\n" + "-" * 50)

    # Test invoke 2
    print("\n--- Testing invoke 2 ---")
    message = "Translate: I love building applications."
    response = model.invoke(message)
    print(response)

    # Test invoke 3
    print("\n--- Testing invoke 3 ---")
    message = [{"role": "user", "content": "Translate: I love building applications."}]
    response = model.invoke(message)
    print(response)


# Test the async methods
async def test_async_methods():
    """Test the async methods of the custom model"""
    print("\n" + "=" * 50)
    print("Testing async methods")
    print("=" * 50)
    
    # Create a message
    message = HumanMessage(content="说出数字 123 不需要其他内容")
    
    # Test ainvoke
    print("\n--- Testing ainvoke ---")
    result = await model.ainvoke([message])
    print(result)
    
    # Test astream
    print("\n--- Testing astream ---")
    async for chunk in model.astream([message]):
        print(chunk, end="\n", flush=True)
        print()
    print("=" * 50)


# Test batch
def test_batch():
    """Test the batch methods of the custom model"""
    print("\n" + "=" * 50)
    print("Testing batch methods")
    print("=" * 50)
    
    # Create multiple messages
    messages = [
        "介绍你自己",
        "你是谁？",
    ]
    result = model.batch(messages)
    print(result)
    print("=" * 50)


# Test agent
def test_agent():
    from langchain.agents import create_agent
    from langchain.tools import tool

    print("\n" + "=" * 50)
    print("Testing langchain agent")
    print("=" * 50)

    @tool
    def get_weather(city: str) -> str:
        """Get weather for a given city."""
        return f"It's always sunny in {city}!"

    agent = create_agent(
        model=model,
        tools=[get_weather],
        system_prompt="You are a helpful assistant",
    )

    # Run the agent
    # 非流式
    # agent invoke 1
    print('\n--- Testing agent invoke 1 ---')
    message = {"messages": [{"role": "user", "content": "调用get_weather工具查询北京天气"}]}
    result = agent.invoke(message)
    print(result)

    # agent invoke 2
    print('\n--- Testing agent invoke 2 ---')
    message = {"messages": "hi, my name is bob"}
    result = agent.invoke(message)
    print(result)

    # agent invoke 3
    print('\n--- Testing agent invoke 3 ---')
    message = {"messages": [HumanMessage(content="hi, my name is bob")]}
    result = agent.invoke(message)
    print(result)

    # 流式
    # for chunk in agent.stream(
    #     {"messages": [{"role": "user", "content": "调用天气工具查询北京天气"}]}, 
    #     stream_mode="values", context={"user_role": "expert"}):
    #     # Each chunk contains the full state at that point
    #     latest_message = chunk["messages"][-1]
    #     if latest_message.content:
    #         print(f"Agent: {latest_message.content}")
    #     elif latest_message.tool_calls:
    #         print(f"Calling tools: {[tc['name'] for tc in latest_message.tool_calls]}")
    
    print("=" * 50)


def test_image():
    """Test the image methods of the custom model"""
    print("\n" + "=" * 50)
    print("Testing image methods")
    print("=" * 50)
    
    import base64
    def encode_image(image_path: str) -> str:
        """将图像编码为 base64 字符串"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    img_path = r"F:\prompt-engineering\langchain-langgraph-V1.0\案例\Deep_Research\researcher_subgraph.png"
    img_base64_1 = encode_image(img_path)
    img_path = r"F:\prompt-engineering\langchain-langgraph-V1.0\案例\Deep_Research\supervisor_subgraph.png"
    img_base64_2 = encode_image(img_path)

    # 多张图片
    print("Testing image invoke")
    print("=" * 50)
    messages = [
        HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "图中讲了什么",
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url":  f"data:image/jpeg;base64,{img_base64_1}"
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url":  f"data:image/jpeg;base64,{img_base64_2}"
                    },
                },
            ]
        ),
    ]
    response = model.invoke(messages)
    print(response)

    print("Testing image batch")
    print("=" * 50)
    # 里面每一个元素都是列表
    messages = [
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "图中讲了什么",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":  f"data:image/jpeg;base64,{img_base64_1}"
                        },
                    },
                ]
            )
        ],
        [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": "图中讲了什么",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url":  f"data:image/jpeg;base64,{img_base64_2}"
                        },
                    },
                ]
            )
        ],
    ]
    response = model.batch(messages)
    print(response)



# Run the tests
if __name__ == "__main__":
    import asyncio

    # Example usage with GLM API
    # API_KEY = ""
    # BASE_URL = "https://open.bigmodel.cn/api/paas/v4/"
    # MODEL = "GLM-4.5-Flash"  # GLM-4V-Flash 图片理解
    # extra_body={"thinking": {"type": "disabled",},}

    # ModelScope
    # API_KEY = ""
    # BASE_URL = "https://api-inference.modelscope.cn/v1"
    # MODEL = "Qwen/Qwen3-32B"
    # extra_body = {
    #     # enable thinking, set to False to disable
    #     "enable_thinking": False,  # true 只支持流式
    #     # use thinking_budget to contorl num of tokens used for thinking
    #     # "thinking_budget": 4096
    # }

    # Gemini
    # API_KEY = ""
    # BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
    # MODEL = "gemini-2.5-flash-lite"
    # extra_body={
    #   'extra_body': {
    #     "google": {
    #       "thinking_config": {
    #         "thinking_budget": 0,
    #         "include_thoughts": True
    #       }
    #     }
    #   }
    # }

    # Azure
    # MODEL = "gpt-4.1-nano"
    # azure_api_version='2025-03-01-preview'
    # azure_endpoint=""
    # azure_api_key=""

    model = ChatOpenAIModel(
        api_key=API_KEY,
        base_url=BASE_URL,
        extra_body=extra_body,
        model=MODEL,
        use_azure=False,  # 使用微软openai接口
        # azure_api_key=azure_api_key,
        # azure_endpoint=azure_endpoint,
        # azure_api_version=azure_api_version,
    )
    
    # Run sync tests
    test_sync_methods()
    
    # Run async tests
    asyncio.run(test_async_methods())
    
    # # # Run batch tests
    test_batch()

    # Test langchain agent use
    test_agent()

    # Test image
    test_image()
