from tools.tools_function import tavily_search, height_search


tavily_search_tool = {
        "type": "function",
        "function": {
            "name": 'tavily_search',
            "description": "根据用户查询，去搜索引擎，返回搜索结果",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "description": "用户搜索内容 query",
                        "type": "string"
                    },
                },
                "required": ["query"]
            }
        }
      }

height_search_tool = {
        "type": "function",
        "function": {
            "name": 'height_search',
            "description": "只要是有姓名，身高关键字，都需要使用此工具根据姓名，查询对应身高，每次只能查询一个人的身高",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "description": "指具体的姓名或名字",
                        "type": "string"
                    },
                },
                "required": ["name"]
            }
        }
      }

tools = [
    tavily_search_tool,
    height_search_tool
]

tool_names = ['tavily_search', 'height_search']

tool_dict = {
    'tavily_search': tavily_search,
    'height_search': height_search
}
