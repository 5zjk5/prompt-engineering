package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"deepsearch/logs"
)

// SearchResult 表示单个搜索结果
type SearchResult struct {
	SiteName string `json:"sitename"`
	Summary  string `json:"summary"`
	Title    string `json:"title"`
	URL      string `json:"url"`
}

// SearchResponse 表示搜索 API 的响应
type SearchResponse struct {
	DebugURL string         `json:"debug_url"`
	Results  []SearchResult `json:"results"`
	Msg      string         `json:"msg"`
}

// SearchAPI 封装了搜索 API 的调用
type SearchAPI struct {
	token      string
	url        string
	workflowID string
	logger     *logs.Logger
	client     *http.Client
}

// NewSearchAPI 创建一个新的 SearchAPI 实例
func NewSearchAPI(logger *logs.Logger) *SearchAPI {
	token := os.Getenv("SEARCH_API_TOKEN")
	url := os.Getenv("SEARCH_API_URL")
	if url == "" {
		url = "https://api.coze.cn/v1/workflow/run"
	}
	workflowID := os.Getenv("WORKFLOW_ID")
	
	if token == "" || workflowID == "" {
		logger.Error("搜索API配置不完整，请检查环境变量")
		return nil
	}
	
	return &SearchAPI{
		token:      token,
		url:        url,
		workflowID: workflowID,
		logger:     logger,
		client:     &http.Client{},
	}
}

// SearchRequest 表示搜索请求的参数
type SearchRequest struct {
	WorkflowID string                 `json:"workflow_id"`
	Parameters map[string]interface{} `json:"parameters"`
}

// Search 执行搜索操作
func (s *SearchAPI) Search(userInput []string) (*SearchResponse, error) {
	// 构建请求体
	reqBody := SearchRequest{
		WorkflowID: s.workflowID,
		Parameters: map[string]interface{}{
			"USER_INPUT": userInput,
		},
	}
	
	// 将请求体转换为 JSON
	jsonData, err := json.Marshal(reqBody)
	if err != nil {
		return &SearchResponse{
			DebugURL: "请求失败，无 debug_url 信息",
			Results:  []SearchResult{},
			Msg:      fmt.Sprintf("搜索请求失败: %v", err),
		}, nil
	}
	
	// 创建 HTTP 请求
	req, err := http.NewRequest("POST", s.url, bytes.NewBuffer(jsonData))
	if err != nil {
		return &SearchResponse{
			DebugURL: "请求失败，无 debug_url 信息",
			Results:  []SearchResult{},
			Msg:      fmt.Sprintf("搜索请求失败: %v", err),
		}, nil
	}
	
	// 设置请求头
	req.Header.Set("Authorization", "Bearer "+s.token)
	req.Header.Set("Content-Type", "application/json")
	
	// 发送请求
	resp, err := s.client.Do(req)
	if err != nil {
		return &SearchResponse{
			DebugURL: "请求失败，无 debug_url 信息",
			Results:  []SearchResult{},
			Msg:      fmt.Sprintf("搜索请求失败: %v", err),
		}, nil
	}
	defer resp.Body.Close()
	
	// 读取响应体
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return &SearchResponse{
			DebugURL: "请求失败，无 debug_url 信息",
			Results:  []SearchResult{},
			Msg:      fmt.Sprintf("搜索请求失败: %v", err),
		}, nil
	}
	
	// 解析响应 JSON
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return &SearchResponse{
			DebugURL: "请求失败，无 debug_url 信息",
			Results:  []SearchResult{},
			Msg:      fmt.Sprintf("搜索请求失败: %v", err),
		}, nil
	}
	
	// 提取 debug_url
	debugURL, _ := result["debug_url"].(string)
	
	// 格式化搜索结果
	formattedResults, ret := s.formatSearchResults(result)
	
	// 返回结果
	if ret == 0 {
		return &SearchResponse{
			DebugURL: debugURL,
			Results:  formattedResults,
			Msg:      "success",
		}, nil
	}
	
	return &SearchResponse{
		DebugURL: debugURL,
		Results:  []SearchResult{},
		Msg:      "search fail",
	}, nil
}

// formatSearchResults 格式化搜索结果
func (s *SearchAPI) formatSearchResults(results map[string]interface{}) ([]SearchResult, int) {
	var formattedResults []SearchResult
	
	// 获取 data 字段
	data, ok := results["data"].(string)
	if !ok {
		s.logger.Warning("搜索结果缺少 data 字段")
		return formattedResults, 1
	}
	
	// 将字符串转换为 JSON 对象
	var dataObj map[string]interface{}
	if err := json.Unmarshal([]byte(data), &dataObj); err != nil {
		s.logger.Errorf("解析搜索结果时出错: %v", err)
		return formattedResults, 1
	}
	
	// 获取 output 字段
	output, ok := dataObj["output"].([]interface{})
	if !ok {
		s.logger.Warning("搜索结果缺少 output 字段")
		return formattedResults, 1
	}
	
	// 遍历 output 列表
	for _, item := range output {
		outputItem, ok := item.(map[string]interface{})
		if !ok {
			continue
		}
		
		// 获取 data 字段
		dataField, ok := outputItem["data"].(map[string]interface{})
		if !ok {
			continue
		}
		
		// 获取 doc_results 字段
		docResults, ok := dataField["doc_results"].([]interface{})
		if !ok {
			continue
		}
		
		// 遍历 doc_results
		for _, doc := range docResults {
			docItem, ok := doc.(map[string]interface{})
			if !ok {
				continue
			}
			
			// 提取所需字段
			siteName, _ := docItem["sitename"].(string)
			summary, _ := docItem["summary"].(string)
			title, _ := docItem["title"].(string)
			url, _ := docItem["url"].(string)
			
			// 创建结果对象
			result := SearchResult{
				SiteName: siteName,
				Summary:  summary,
				Title:    title,
				URL:      url,
			}
			
			formattedResults = append(formattedResults, result)
		}
	}
	
	return formattedResults, 0
}