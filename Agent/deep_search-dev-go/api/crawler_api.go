package api

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/playwright-community/playwright-go"
	"deepsearch/logs"
)

// CrawlResult 表示爬取结果
type CrawlResult struct {
	URL     string `json:"url"`
	Content string `json:"content"`
}

// CrawlerAPI 封装了网页爬取功能
type CrawlerAPI struct {
	browser playwright.Browser
	logger  *logs.Logger
	mu      sync.Mutex
}

// NewCrawlerAPI 创建一个新的 CrawlerAPI 实例
func NewCrawlerAPI(logger *logs.Logger) *CrawlerAPI {
	return &CrawlerAPI{
		logger: logger,
	}
}

// InitBrowser 初始化浏览器
func (c *CrawlerAPI) InitBrowser() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	if c.browser != nil {
		return nil
	}
	
	c.logger.Info("正在初始化浏览器...")
	
	// 启动Playwright
	pw, err := playwright.Run()
	if err != nil {
		return fmt.Errorf("启动Playwright失败: %v", err)
	}
	
	// 启动浏览器
	browser, err := pw.Chromium.Launch(playwright.BrowserTypeLaunchOptions{
		Headless: playwright.Bool(true),
	})
	if err != nil {
		return fmt.Errorf("启动浏览器失败: %v", err)
	}
	
	c.browser = browser
	c.logger.Info("浏览器初始化成功")
	
	return nil
}

// CloseBrowser 关闭浏览器
func (c *CrawlerAPI) CloseBrowser() error {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	if c.browser == nil {
		return nil
	}
	
	c.logger.Info("正在关闭浏览器...")
	
	err := c.browser.Close()
	c.browser = nil
	
	if err != nil {
		c.logger.Errorf("关闭浏览器失败: %v", err)
		return err
	}
	
	c.logger.Info("浏览器已关闭")
	return nil
}

// CrawlSingleURL 爬取单个URL的内容
func (c *CrawlerAPI) CrawlSingleURL(ctx context.Context, url string) (*CrawlResult, error) {
	// 确保浏览器已初始化
	if c.browser == nil {
		if err := c.InitBrowser(); err != nil {
			return &CrawlResult{
				URL:     url,
				Content: "浏览器初始化失败",
			}, err
		}
	}
	
	// 创建页面
	page, err := c.browser.NewPage()
	if err != nil {
		return &CrawlResult{
			URL:     url,
			Content: fmt.Sprintf("创建页面失败: %v", err),
		}, err
	}
	defer page.Close()
	
	// 设置超时
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	
	// 导航到URL
	_, err = page.Goto(url)
	if err != nil {
		return &CrawlResult{
			URL:     url,
			Content: "页面加载超时，可能是网站加载太慢或无法访问",
		}, fmt.Errorf("页面加载超时: %v", err)
	}
	
	// 等待页面加载完成
	page.WaitForTimeout(3000)
	
	// 等待一小段时间确保页面加载完成
	time.Sleep(1 * time.Second)
	
	// 获取页面文本内容
	textContent, err := page.InnerText("body")
	if err != nil {
		return &CrawlResult{
			URL:     url,
			Content: "无法获取页面文本内容",
		}, err
	}
	
	if textContent == "" {
		textContent = "无法获取页面文本内容"
	}
	
	return &CrawlResult{
		URL:     url,
		Content: textContent,
	}, nil
}

// CrawlURLs 并行爬取多个URL的内容
func (c *CrawlerAPI) CrawlURLs(ctx context.Context, urls []string) ([]*CrawlResult, error) {
	// 确保浏览器已初始化
	if c.browser == nil {
		if err := c.InitBrowser(); err != nil {
			return nil, err
		}
	}
	
	c.logger.Infof("开始爬取 %d 个URL...", len(urls))
	
	// 创建结果通道
	resultChan := make(chan *CrawlResult, len(urls))
	errorChan := make(chan error, len(urls))
	
	// 使用 WaitGroup 等待所有 goroutine 完成
	var wg sync.WaitGroup
	wg.Add(len(urls))
	
	// 为每个 URL 启动一个 goroutine 进行爬取
	for _, url := range urls {
		go func(u string) {
			defer wg.Done()
			
			// 检查上下文是否已取消
			select {
			case <-ctx.Done():
				resultChan <- &CrawlResult{
					URL:     u,
					Content: "爬取已取消",
				}
				return
			default:
			}
			
			// 爬取单个 URL
			result, err := c.CrawlSingleURL(ctx, u)
			if err != nil {
				c.logger.Errorf("爬取URL %s 时出错: %v", u, err)
				errorChan <- err
				return
			}
			
			resultChan <- result
		}(url)
	}
	
	// 等待所有 goroutine 完成
	go func() {
		wg.Wait()
		close(resultChan)
		close(errorChan)
	}()
	
	// 收集结果
	var results []*CrawlResult
	for result := range resultChan {
		results = append(results, result)
	}
	
	// 检查是否有错误
	for err := range errorChan {
		if err != nil {
			c.logger.Errorf("爬取任务出错: %v", err)
		}
	}
	
	c.logger.Infof("爬取完成，共获取到 %d 个结果", len(results))
	return results, nil
}