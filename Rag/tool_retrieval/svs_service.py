import uvicorn
import traceback
from dotenv import load_dotenv
from art import text2art
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from logs.logger import define_log_level
from db_operation import create_lifespan
from utils.utils import verify_tool
from db_operation.insert import insert_tool_to_db, generate_hypothetical_query, tool_description_optimize
from db_operation.delete import delete_tool_from_db
from db_operation.update import update_tool_to_db
from db_operation.select import select_tool_from_db
from utils.retrieval import retrieval_tool_func
from model import InsertToolRequest, DeleteToolRequest, UpdateToolRequest, SelectToolRequest, RetrievalToolRequest


# 初始化
load_dotenv()
project_root = Path(__file__).resolve().parent
db_path = project_root / "db"

# 创建全局日志记录器
insert_logger = define_log_level(project_root, 'insert')
delete_logger = define_log_level(project_root, 'delete')
update_logger = define_log_level(project_root, 'update')
select_logger = define_log_level(project_root, 'select')
retrieval_logger = define_log_level(project_root, 'retrieval')

# 创建FastAPI应用
app = FastAPI(
    title="工具管理服务",
    description="提供工具的增删改查和检索功能",
    version="1.0.0",
    lifespan=create_lifespan(db_path)
)


@app.post("/tools/insert_tool")
async def insert_tool(requests: InsertToolRequest):
    """
    新工具入库，工具格式为 json
    传入可选参数 tool_optimized 是否优化工具描述，默认值为 True
    示例：
    {
        "tool_name": "tool1",
        "description": "这是一个工具",
        "parameters": {
            "type": "object",
            "properties": {
            "request_url": {
                "type": "string",
                "description": "指定要检索详细内容的网页URL。"
            }
            },
            "required": [
                "request_url"
            ]
        }
    }
    """
    insert_logger.info(f"=" * 20)
    tool = requests.tool_json
    try:
        insert_logger.info(f"Insert tool: {tool}")
        verify_tool(tool, insert_logger)
        
        # 是否需要优化工具参数
        if requests.tool_optimized:
            tool = await tool_description_optimize(tool, insert_logger)

        # 工具插入到数据库
        await insert_tool_to_db(str(db_path), tool)
        insert_logger.info(f"Insert tool vector to db success!")

        # 工具假设性问题插入到数据库
        await generate_hypothetical_query(str(db_path), tool, insert_logger)

        insert_logger.info(f"Insert tool success!")
        return JSONResponse(status_code=200, content={'detail': 'Insert tool success!'})
    except HTTPException as e:
        insert_logger.error(f"HTTP Exception: {e.detail}")
        insert_logger.error(f"Traceback: {traceback.format_exc()}")
        await delete_tool_from_db(str(db_path), tool['name'])  # 回滚
        raise e
    except Exception as e:
        insert_logger.error(f"Error inserting tool: {e.args}")
        insert_logger.error(f"Traceback: {traceback.format_exc()}")
        await delete_tool_from_db(str(db_path), tool['name'])  # 回滚
        raise HTTPException(status_code=500, detail=f"Error inserting tool: {e.args}")
    finally:
        insert_logger.info(f"=" * 20)


@app.post("/tools/delete_tool")
async def delete_tool(requests: DeleteToolRequest):
    """
    根据 tool_name 删除工具
    示例：
    {
        "tool_name": "tool1"
    }
    """
    delete_logger.info(f"=" * 20)
    try:
        tool_id = requests.tool_name
        delete_logger.info(f"Delete tool: {tool_id}")
        if not tool_id:
            raise HTTPException(status_code=400, detail="tool_name is required to delete.")

        # 从数据库中删除工具
        await delete_tool_from_db(str(db_path), tool_id)
        delete_logger.info(f"Delete tool from db success!")

        return JSONResponse(status_code=200, content={'detail': 'Delete tool success!'})
    except HTTPException as e:
        delete_logger.error(f"HTTP Exception: {e.detail}")
        delete_logger.error(f"Traceback: {traceback.format_exc()}")
        raise e
    except Exception as e:
        delete_logger.error(f"Error deleting tool: {e.args}")
        delete_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error deleting tool: {e.args}")
    finally:
        delete_logger.info(f"=" * 20)


@app.post("/tools/update_tool")
async def update_tool(requests: UpdateToolRequest):
    """
    根据 tool_name 更新工具描述，接收 json
    示例：
    {
        "tool_name": "tool1",
        "description": "这是一个工具",
        "parameters": {
            "type": "object",
            "properties": {
            "request_url": {
                "type": "string",
                "description": "指定要检索详细内容的网页URL。"
            }
            },
            "required": [
                "request_url"
            ]
        }
    }
    """
    update_logger.info(f"=" * 20)
    try:
        tool = requests.tool_json
        update_logger.info(f"Update tool: {tool}")
        verify_tool(tool, update_logger)

        # 工具更新插入到数据库
        await update_tool_to_db(str(db_path), tool)
        update_logger.info(f"Update tool vector to db success!")

        # 更新工具假设性问题
        await generate_hypothetical_query(str(db_path), tool, update_logger)

        update_logger.info(f"Update tool vector to db success!")
        return JSONResponse(status_code=200, content={'detail': 'Update tool success!'})
    except HTTPException as e:
        update_logger.error(f"HTTP Exception: {e.detail}")
        update_logger.error(f"Traceback: {traceback.format_exc()}")
        raise e
    except Exception as e:
        update_logger.error(f"Error updating tool: {e.args}")
        update_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error updating tool: {e.args}")
    finally:
        update_logger.info(f"=" * 20)


@app.post("/tools/select_tool")
async def select_tool(requests: SelectToolRequest):
    """
    1、根据 tool_name 获取工具信息和假设性问题
    2、没有 tool_name 默认获得所有工具信息和假设性问题
    示例：
    {
        "tool_name": "tool1"
    }
    """
    select_logger.info(f"=" * 20)
    try:
        tool_id = requests.tool_name
        select_logger.info(f"Select tool: {tool_id}")
        
        # 从数据库中查询工具和假设性问题
        tools = await select_tool_from_db(str(db_path), tool_id)
        select_logger.info(f"Select tool from db success!")

        # 没查到工具
        if not tools:
            select_logger.warning(f"Tool '{tool_id}' not found")
            raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found")
        
        return JSONResponse(status_code=200, content={'tools': tools})
    except HTTPException as e:
        select_logger.error(f"HTTP Exception: {e.detail}")
        select_logger.error(f"Traceback: {traceback.format_exc()}")
        raise e
    except Exception as e:
        select_logger.error(f"Error selecting tool: {e.args}")
        select_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error selecting tool: {e.args}")
    finally:
        select_logger.info(f"=" * 20)


@app.post("/tools/retrieval_tool")
async def retrieval_tool(requests: RetrievalToolRequest):
    """
    根据 query 检索工具
    示例：
    {
        "query": "检索工具",
        "method": "hybrid",
        "n_results": 5
    }
    """
    retrieval_logger.info(f"=" * 20)
    try:
        query = requests.query
        method = requests.method
        n_results = requests.n_results
        
        retrieval_logger.info(f"Retrieval tool with query: {query}, method: {method}, n_results: {n_results}")
        
        # 调用检索函数
        results = await retrieval_tool_func(str(db_path), query, method, n_results, retrieval_logger)
        retrieval_logger.info(f"Retrieval tool success! Found {len(results)} results.")
        
        return JSONResponse(status_code=200, content={'results': results})
    except Exception as e:
        retrieval_logger.error(f"Error retrieving tool: {e.args}")
        retrieval_logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error retrieving tool: {e.args}")
    finally:
        retrieval_logger.info(f"=" * 20)


if __name__ == "__main__":
    print(text2art('TOOL_RETRIEVAL'))
    uvicorn.run(app, host="0.0.0.0", port=8009)
