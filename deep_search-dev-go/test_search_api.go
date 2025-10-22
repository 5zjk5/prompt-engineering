package main

import (
	"fmt"
	"os"

	"deepsearch/api"
	"deepsearch/logs"

	"github.com/joho/godotenv"
)

// testSearchAPI 测试搜索API
func testSearchAPI() {
	// 初始化日志
	projectRoot, _ := os.Getwd()
	logger, _ := logs.DefineLogLevel(projectRoot, "test_search_api", "info", "info")
	logger.Info("开始测试搜索API...")

	// 创建搜索API实例
	searchAPI := api.NewSearchAPI(logger)
	if searchAPI == nil {
		logger.Error("创建搜索API实例失败")
		return
	}

	// 测试搜索
	userInput := []string{"langchain", "天气预报"}
	logger.Info(fmt.Sprintf("搜索关键词: %v", userInput))

	// 执行搜索
	response, _ := searchAPI.Search(userInput)
	if response.Msg != "success" {
		logger.Error(fmt.Sprintf("搜索API测试失败: %s", response.Msg))
		return
	}

	logger.Info("搜索结果:")

	// 提取debug_url和结果列表
	debugURL := response.DebugURL
	results := response.Results

	// 打印debug_url
	logger.Info(fmt.Sprintf("Debug URL: %s", debugURL))

	// 检查结果是否为空
	if len(results) == 0 {
		logger.Warning("搜索结果为空")
		logger.Error("搜索API测试失败!")
	} else {
		// 打印每个搜索结果
		// for i, result := range results {
		// 	logger.Info(fmt.Sprintf("\n结果 %d:", i+1))
		// 	logger.Info(fmt.Sprintf("  网站名称: %s", result.SiteName))
		// 	logger.Info(fmt.Sprintf("  标题: %s", result.Title))
		// 	logger.Info(fmt.Sprintf("  摘要: %s", result.Summary))
		// 	logger.Info(fmt.Sprintf("  URL: %s", result.URL))
		// }

		logger.Info("搜索API测试成功!")
	}
}

// testMultipleSearches 测试多个搜索请求
func testMultipleSearches() {
	// 初始化日志
	projectRoot, _ := os.Getwd()
	logger, _ := logs.DefineLogLevel(projectRoot, "test_multiple_searches", "info", "info")
	logger.Info("\n开始测试多个搜索请求...")

	// 创建搜索API实例
	searchAPI := api.NewSearchAPI(logger)
	if searchAPI == nil {
		logger.Error("创建搜索API实例失败")
		return
	}

	// 测试不同的搜索关键词
	testCases := [][]string{
		{"人工智能", "应用"},
		{"Python", "编程"},
		{"机器学习", "算法"},
	}

	for i, userInput := range testCases {
		logger.Info(fmt.Sprintf("\n测试用例 %d: %v", i+1, userInput))

		// 执行搜索
		response, _ := searchAPI.Search(userInput)
		if response.Msg != "success" {
			logger.Error(fmt.Sprintf("搜索请求 %d 失败: %s", i+1, response.Msg))
			continue
		}

		// 提取debug_url和结果列表
		debugURL := response.DebugURL
		results := response.Results

		// 打印debug_url
		logger.Info(fmt.Sprintf("Debug URL: %s", debugURL))

		// 检查结果是否为空
		if len(results) == 0 {
			logger.Warning(fmt.Sprintf("搜索结果 %d 为空", i+1))
		} else {
			logger.Info(fmt.Sprintf("搜索结果 %d 共找到 %d 条结果:", i+1, len(results)))
			// 打印每个搜索结果的标题和URL
			// for j, result := range results {
			// 	logger.Info(fmt.Sprintf("  %d. %s - %s", j+1, result.Title, result.URL))
			// }
		}
	}
}

func main() {
	// 加载环境变量
	err := godotenv.Load()
	if err != nil {
		fmt.Println("加载.env文件失败:", err)
	}

	fmt.Println("开始测试搜索API...")

	// 测试单个搜索请求
	testSearchAPI()

	// 测试多个搜索请求
	testMultipleSearches()

	fmt.Println("\n所有测试完成!")
}
