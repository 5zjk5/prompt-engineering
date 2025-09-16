import os
import requests
import json
import logging


class SearchAPI:
    def __init__(self, logger=None):
        self.token = os.getenv('SEARCH_API_TOKEN')
        self.url = os.getenv('SEARCH_API_URL', 'https://api.coze.cn/v1/workflow/run')
        self.workflow_id = os.getenv('WORKFLOW_ID')
        self.logger = logger or logging.getLogger(__name__)
        
        if not self.token or not self.url or not self.workflow_id:
            raise ValueError("搜索API配置不完整，请检查环境变量")
    
    def search(self, user_input):
        """
        执行搜索操作
        
        Args:
            user_input (list): 用户输入的关键词列表
            
        Returns:
            dict: 包含debug_url和搜索结果列表的字典
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "workflow_id": self.workflow_id,
            "parameters": {
                "USER_INPUT": user_input
            }
        }
        
        try:
            response = requests.post(self.url, headers=headers, json=data)
            response.raise_for_status()
            results = response.json()
            
            # 提取debug_url，无论成功还是失败都需要返回
            debug_url = results.get("debug_url", "")
            
            # 调用format_search_results方法格式化结果
            formatted_results, ret = self.format_search_results(results)
            
            # 返回包含debug_url和搜索结果列表的字典
            if ret == 0:
                return {
                    "debug_url": debug_url,
                    "results": formatted_results,
                    "msg": "success"
                }
            else:
                return {
                    "debug_url": debug_url,
                    "results": [],
                    "msg": "search fail"
                }
            
        except requests.exceptions.RequestException as e:
            return {
                "debug_url": "请求失败，无 debug_url 信息",
                "results": [],
                "msg": f"搜索请求失败: {str(e)}"
            }
    
    def format_search_results(self, results):
        """
        格式化搜索结果
        
        Args:
            results (dict): 搜索结果
            
        Returns:
            list: 格式化后的搜索结果列表，每个元素是一个包含sitename, summary, title, url的字典
        """
        formatted_results = []
        
        try:
            # 获取data字段，它是一个字符串列表
            data_list = results.get("data")
            if not data_list:
                self.logger.warning("搜索结果缺少data字段")
                return [], 1
            
            # 将字符串转换为JSON对象
            data_obj = json.loads(data_list)
            
            # 遍历output列表中的每个元素
            for output_item in data_obj["output"]:          
                for doc in output_item['data']['doc_results'] :
                    # 提取所需字段
                    sitename = doc.get("sitename", "")
                    summary = doc.get("summary", "")
                    title = doc.get("title", "")
                    url = doc.get("url", "")
                    
                    # 创建结果字典
                    result_dict = {
                        "sitename": sitename,
                        "summary": summary,
                        "title": title,
                        "url": url
                    }
                    
                    formatted_results.append(result_dict)
            
            return formatted_results, 0
        except Exception as e:
            self.logger.info(f"解析搜索结果时出错: {e}")
            return formatted_results, 1
