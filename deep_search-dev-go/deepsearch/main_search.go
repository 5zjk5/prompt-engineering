package deepsearch

import (
	"context"
	"deepsearch/api"
	"deepsearch/deepsearch/prompt"
	"deepsearch/logs"
	"encoding/json"
	"fmt"
	"strings"
)

// SearchCrawl 搜索和爬取结构体
type SearchCrawl struct {
	SearchAPI  *api.SearchAPI
	CrawlerAPI *api.CrawlerAPI
	Logger     *logs.Logger
}

// NewSearchCrawl 创建搜索和爬取实例
func NewSearchCrawl(logger *logs.Logger) *SearchCrawl {
	return &SearchCrawl{
		SearchAPI:  api.NewSearchAPI(logger),
		CrawlerAPI: api.NewCrawlerAPI(logger),
		Logger:     logger,
	}
}

// Run 运行搜索和爬取：返回 crawlResList
func (sc *SearchCrawl) Run(ctx context.Context, topic string, haveQuery []string, allSummarySearch []string) ([]string, error) {
	// 初始化爬虫API
	err := sc.CrawlerAPI.InitBrowser()
	if err != nil {
		sc.Logger.Errorf("初始化爬虫API失败: %v", err)
		return nil, fmt.Errorf("初始化爬虫API失败: %v", err)
	}
	defer sc.CrawlerAPI.CloseBrowser()

	// 执行搜索
	sc.Logger.Infof("开始调用搜索接口...\ntopic: %s\nrewrite_query: %v", topic, haveQuery)
	searchResults, err := sc.SearchAPI.Search(haveQuery)
	if err != nil {
		sc.Logger.Errorf("搜索失败: %v", err)
		return nil, fmt.Errorf("搜索失败: %v", err)
	}

	sc.Logger.Infof("搜索接口调用工作流: %s", searchResults.DebugURL)
	
	if len(searchResults.Results) == 0 {
		sc.Logger.Warning("共搜索到 0 条结果...")
		return []string{}, nil
	}
	sc.Logger.Infof("共搜索到 %d 条结果...", len(searchResults.Results))

	// 选择相关URL
	sc.Logger.Info("开始进行 url 筛选...")
	relatedURLs, err := sc.selectRelatedURLs(ctx, topic, searchResults, allSummarySearch)
	if err != nil {
		sc.Logger.Errorf("选择相关URL失败: %v", err)
		return nil, fmt.Errorf("选择相关URL失败: %v", err)
	}

	sc.Logger.Infof("共挑出 %d 个需要的 url: %v", len(relatedURLs), relatedURLs)

	// 爬取URL内容
	sc.Logger.Info("开始爬取 url...")
	crawlResults, err := sc.CrawlerAPI.CrawlURLs(ctx, relatedURLs)
	if err != nil {
		sc.Logger.Errorf("爬取URL内容失败: %v", err)
		return nil, fmt.Errorf("爬取URL内容失败: %v", err)
	}

	sc.Logger.Info("爬取完成...")

	// 提取爬取内容
	var contents []string
	for _, result := range crawlResults {
		// 清理内容，移除换行符和制表符
		content := strings.ReplaceAll(result.Content, "\n", "")
		content = strings.ReplaceAll(content, "\t", "")
		if content != "" && content != "NA" {
			contents = append(contents, content)
		}
	}

	if len(contents) == 0 {
		sc.Logger.Warning("搜索爬取结果为空！")
	}

	return contents, nil
}

// selectRelatedURLs 选择相关URL
func (sc *SearchCrawl) selectRelatedURLs(ctx context.Context, topic string, searchResults *api.SearchResponse, allSummarySearch []string) ([]string, error) {
	// 构建URL映射
	urlMap := make(map[string]string)
	var searchResultsText []string
	var originalURLs []string // 兜底
	
	for i, result := range searchResults.Results {
		urlKey := fmt.Sprintf("url_%d", i+1) // 从1开始计数，与Python版本一致
		urlMap[urlKey] = result.URL
		originalURLs = append(originalURLs, result.URL)
		
		// 格式化搜索结果文本，与Python版本一致
		resultText := fmt.Sprintf("摘要：%s\n标题：%s\n链接：%s", result.Summary, result.Title, urlKey)
		searchResultsText = append(searchResultsText, resultText)
		searchResultsText = append(searchResultsText, "==============================================================")
	}
	
	sc.Logger.Infof("映射后链接：%v", urlMap)
	
	// 构建提示词，使用Python版本的格式
	promptText := fmt.Sprintf(prompt.RelatedUrlPrompt, topic, allSummarySearch, strings.Join(searchResultsText, "\n"))
	
	sc.Logger.Infof("选择相关的搜索结果 prompt:\n%s", promptText)
	
	// 调用大模型
	llm := api.GlobalLLM
	if llm == nil {
		sc.Logger.Error("全局LLM实例未初始化")
		return nil, fmt.Errorf("全局LLM实例未初始化")
	}
	
	response, err := llm.Infer(ctx, promptText, false, 0.7)
	if err != nil {
		sc.Logger.Errorf("调用大模型失败: %v", err)
		return nil, fmt.Errorf("调用大模型失败: %v", err)
	}
	
	sc.Logger.Infof("大模型选择需要的搜索结果结果：\n%s", response)
	
	// 解析响应，提取URL
	var selectedURLs []string
	response = strings.TrimSpace(response)
	
	// 直接尝试解析JSON数组
	var urlKeys []string
	if err := json.Unmarshal([]byte(response), &urlKeys); err == nil {
		// 成功解析JSON数组
		for _, urlKey := range urlKeys {
			if url, exists := urlMap[urlKey]; exists {
				selectedURLs = append(selectedURLs, url)
			}
		}
	} else {
		// 如果不是有效的JSON，尝试手动解析
		sc.Logger.Warningf("无法解析JSON响应，尝试手动解析: %s", response)
		// 简单的字符串解析，提取url_x格式的字符串
		lines := strings.Split(response, "\n")
		for _, line := range lines {
			line = strings.TrimSpace(line)
			// 移除可能的引号和逗号
			line = strings.Trim(line, "\"'`,")
			if strings.HasPrefix(line, "url_") {
				if url, exists := urlMap[line]; exists {
					selectedURLs = append(selectedURLs, url)
				}
			}
		}
		
		// 如果仍然没有找到URL，使用原始所有结果作为兜底
		if len(selectedURLs) == 0 {
			sc.Logger.Warning("解析结果失败，使用原始所有结果...")
			selectedURLs = originalURLs
		}
	}
	
	if len(selectedURLs) == 0 {
		sc.Logger.Warning("未选择到任何相关URL")
	}
	
	return selectedURLs, nil
}
