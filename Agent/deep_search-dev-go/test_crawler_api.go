package main

import (
	"context"
	"fmt"
	"os"
	"time"

	"deepsearch/api"
	"deepsearch/logs"
)

// testCrawlerAPI 测试爬虫API功能
func testCrawlerAPI() {
	// 初始化日志
	projectRoot, _ := os.Getwd()
	logger, _ := logs.DefineLogLevel(projectRoot, "test_crawler_api", "info", "info")

	// 测试URL列表 - 使用更简单、更可能快速加载的URL
	testUrls := []string{
		"https://www.baidu.com",
		"https://www.msn.cn/zh-cn/news/other/%E5%AE%98%E6%96%B9%E9%80%9A%E6%8A%A5-%E5%A5%B3%E5%AD%90%E8%AF%AF%E8%B8%A9%E6%B0%A2%E6%B0%91%E9%85%B8%E4%B8%AD%E6%AF%92-%E6%8A%A2%E6%95%91%E6%97%A0%E6%95%88%E4%B8%8D%E5%B9%B8%E8%BA%AB%E4%BA%A1/ar-AA1MBYd6?ocid=entnewsntp&pc=U531&cvid=68c8bdfd575041e18eba238ed27fe496&ei=7",
		"https://www.msn.cn/zh-cn/news/other/%E4%BA%8B%E5%8F%91%E4%B8%8A%E6%B5%B7%E8%99%B9%E6%A1%A5%E7%AB%99-%E7%94%B7%E5%AD%90%E8%87%AA%E7%A7%B0%E7%89%A9%E5%93%81%E4%B8%A2%E5%A4%B1-%E9%9D%A2%E5%AF%B9%E8%AD%A6%E5%AF%9F%E5%8D%B4%E6%85%8C%E4%BA%86/ar-AA1MC0tt?ocid=entnewsntp&pc=U531&cvid=68c8bdfd575041e18eba238ed27fe496&ei=12",
		"https://www.msn.cn/zh-cn/news/other/%E9%BB%84%E9%9C%84%E4%BA%91%E5%A4%A7%E5%8F%98%E6%A0%B7-%E7%BD%91%E5%8F%8B%E6%83%8A%E5%8F%B9-%E6%9E%9C%E7%84%B6%E9%92%B1%E8%83%BD%E5%85%BB%E4%BA%BA/ar-AA1MxZtq?ocid=entnewsntp&pc=U531&cvid=68c8bdfd575041e18eba238ed27fe496&ei=18",
	}

	logger.Info("开始测试爬虫API...")
	logger.Info(fmt.Sprintf("测试URL列表: %v", testUrls))

	startTime := time.Now()

	// 创建爬虫API实例
	crawler := api.NewCrawlerAPI(logger)

	// 确保在函数结束时关闭浏览器
	defer func() {
		if err := crawler.CloseBrowser(); err != nil {
			logger.Errorf("关闭浏览器失败: %v", err)
		}
	}()

	// 初始化浏览器
	if err := crawler.InitBrowser(); err != nil {
		logger.Errorf("浏览器初始化失败: %v", err)
		return
	}

	// 创建上下文，设置超时
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// 爬取URL内容
	logger.Info("开始爬取URL内容...")
	results, err := crawler.CrawlURLs(ctx, testUrls)
	if err != nil {
		logger.Errorf("爬取过程中发生错误: %v", err)
		return
	}

	endTime := time.Now()
	logger.Infof("爬取完成，总耗时: %.2f秒", endTime.Sub(startTime).Seconds())

	// 打印结果
	logger.Info("爬取结果:")
	for i, result := range results {
		logger.Info(fmt.Sprintf("\n结果 %d:", i+1))
		logger.Info(fmt.Sprintf("URL: %s", result.URL))
		// 只打印前100个字符的内容预览
		contentPreview := result.Content
		if len(contentPreview) > 100 {
			contentPreview = contentPreview[:100] + "..."
		}
		logger.Info(fmt.Sprintf("内容预览: %s", contentPreview))
	}

	logger.Info("测试完成")
}

func main() {
	testCrawlerAPI()
}
