package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"deepsearch/logs"
)

// 请求结构体
type Request struct {
	Topic string `json:"topic"`
	Lang  string `json:"lang"`
}

// 响应结构体
type Response struct {
	Status int `json:"status"`
}

// fetch 函数模拟Python版本的fetch函数
func fetch(client *http.Client, topic string, index int, total int, logger *logs.Logger, wg *sync.WaitGroup, semaphore chan struct{}) {
	defer wg.Done()

	// 获取信号量
	semaphore <- struct{}{}
	defer func() { <-semaphore }()

	// API URL
	url := "http://localhost:7396/api/deep_search"
	logger.Info("ip:" + url)
	logger.Info(fmt.Sprintf("【处理中】第 %d/%d 条数据: %s", index+1, total, topic))

	// 3次重试机会
	for i := 0; i < 3; i++ {
		// 创建请求体
		requestBody := Request{
			Topic: topic,
			Lang:  "en",
		}
		jsonData, err := json.Marshal(requestBody)
		if err != nil {
			logger.Error(fmt.Sprintf("⚠️ 第 %d 条: %s 请求失败，出错: %v", index+1, topic, err))
			continue
		}

		// 发送POST请求
		req, err := http.NewRequest("POST", url, bytes.NewBuffer(jsonData))
		if err != nil {
			logger.Error(fmt.Sprintf("⚠️ 第 %d 条: %s 请求失败，出错: %v", index+1, topic, err))
			continue
		}
		req.Header.Set("Content-Type", "application/json")

		resp, err := client.Do(req)
		if err != nil {
			logger.Error(fmt.Sprintf("⚠️ 第 %d 条: %s 请求失败，出错: %v", index+1, topic, err))
			continue
		}

		defer resp.Body.Close()

		// 读取响应
		body, err := io.ReadAll(resp.Body)
		if err != nil {
			logger.Error(fmt.Sprintf("⚠️ 第 %d 条: %s 请求失败，出错: %v", index+1, topic, err))
			continue
		}

		result := string(body)

		if resp.StatusCode == 200 {
			// 解析JSON响应
			var response Response
			err := json.Unmarshal(body, &response)
			if err != nil {
				logger.Error(fmt.Sprintf("⚠️ 第 %d 条: %s 解析响应失败，出错: %v", index+1, topic, err))
				continue
			}

			if response.Status == 200 {
				// 截取前50个字符用于日志
				shortResult := result
				if len(shortResult) > 50 {
					shortResult = shortResult[:50]
				}
				logger.Info(fmt.Sprintf("✅ 完成 第 %d 条: %s | 响应长度: %d，%s...", index+1, topic, len(result), shortResult))
				return
			} else {
				// 截取前50个字符用于日志
				shortResult := result
				if len(shortResult) > 50 {
					shortResult = shortResult[:50]
				}
				logger.Error(fmt.Sprintf("❌ 完成 第 %d 条: %s | 响应长度: %d，%s...", index+1, topic, len(result), shortResult))
				return
			}
		} else {
			// 截取前50个字符用于日志
			shortResult := result
			// if len(shortResult) > 50 {
			// 	shortResult = shortResult[:50]
			// }
			logger.Error(fmt.Sprintf("❌ 第 %d 条: %s 请求失败，%s...", index+1, topic, shortResult))
			continue
		}
	}
}

func main() {
	// 初始化日志
	projectRoot := filepath.Dir(os.Args[0])
	logger, _ := logs.DefineLogLevel(projectRoot, "test_deepsearch_api", "INFO", "INFO")
	logger.Info("开始测试deepsearch API...")

	// 测试主题
	topics := []string{"最近医疗大健康有什么新动态，对创业者，个人有什么机遇？"}
	total := len(topics)

	// 控制最大并发数量
	maxConcurrent := 5
	semaphore := make(chan struct{}, maxConcurrent)

	// 创建HTTP客户端
	client := &http.Client{
		Timeout: 300 * time.Second, // 增加到5分钟
	}

	// 使用WaitGroup等待所有goroutine完成
	var wg sync.WaitGroup

	// 启动goroutine处理每个主题
	for i, topic := range topics {
		wg.Add(1)
		go fetch(client, topic, i, total, logger, &wg, semaphore)
	}

	// 等待所有goroutine完成
	wg.Wait()
	logger.Info("所有测试已完成")
}
