package main

import (
	"context"
	"deepsearch/api"
	"deepsearch/deepsearch"
	"deepsearch/logs"
	"deepsearch/deepsearch/utils"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/joho/godotenv"
)

// 版本号
const VERSION = "0.1"

// DeepSearchRequest 定义请求数据结构
type DeepSearchRequest struct {
	Topic string `json:"topic"`
}

// DeepSearchResponse 定义响应数据结构
type DeepSearchResponse struct {
	Status int         `json:"status"`
	Time   float64     `json:"time,omitempty"`
	Msg    string      `json:"msg"`
	Data   interface{} `json:"data,omitempty"`
}

// 全局变量，项目根目录
var projectRoot string

// 初始化函数
func init() {
	// 获取当前执行文件所在目录的绝对路径
	var err error
	projectRoot, err = filepath.Abs(filepath.Dir(os.Args[0]))
	if err != nil {
		panic(err)
	}
}

func main() {
	// 加载环境变量
	err := godotenv.Load()
	if err != nil {
		log.Println("警告: 加载.env文件失败，将使用系统环境变量")
	}

	// 打印ASCII艺术字体的DEEPSEARCH
	printAsciiArt("DEEPSEARCH")
	fmt.Printf("Version: %s\n", VERSION)

	// 设置HTTP路由
	http.HandleFunc("/api/deep_search", deepSearchHandler)

	// 启动HTTP服务器
	fmt.Println("Starting server on :7396")
	err = http.ListenAndServe(":7396", nil)
	if err != nil {
		fmt.Printf("Server failed to start: %v\n", err)
	}
}

// deepSearchHandler 处理深度搜索请求
func deepSearchHandler(w http.ResponseWriter, r *http.Request) {
	// 只处理POST请求
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}

	// 解析请求体
	var req DeepSearchRequest
	err := json.NewDecoder(r.Body).Decode(&req)
	if err != nil {
		sendErrorResponse(w, 400, "Invalid request format", err.Error())
		return
	}

	// 获取topic参数
	topic := req.Topic

	// 创建日志 - 在接收到请求时才创建日志，与Python版本一致
	logger, logName := logs.DefineLogLevel(projectRoot, topic, "info", "info")
	logger.Infof("日志已创建：%s", logName)

	// 初始化全局LLM实例
	api.InitLLM(logger)

	// 创建上下文，用于处理请求取消
	ctx, cancel := context.WithCancel(r.Context())
	defer cancel()

	// 使用通道来处理结果和错误
	resultChan := make(chan interface{})
	errorChan := make(chan error)

	// 启动goroutine处理深度搜索
	go func() {
		defer func() {
			if r := recover(); r != nil {
				errorChan <- fmt.Errorf("panic: %v", r)
			}
		}()

		start := time.Now()

		// 参数校验
		topic, err := utils.VerifyParams(topic)
		if err != nil {
			errorChan <- err
			return
		}
		logger.Infof("参数校验成功！主题：%s", topic)

		// 创建深度搜索实例并运行
		ds := deepsearch.NewDeepSearch(projectRoot, logger)
		result, err := ds.Run(ctx, topic, "deepsearch")
		if err != nil {
			errorChan <- err
			return
		}

		// 计算耗时
		elapsed := time.Since(start).Seconds()
		logger.Infof("深度搜索总共耗时：%fs", elapsed)

		// 返回结果
		response := DeepSearchResponse{
			Status: 200,
			Time:   elapsed,
			Msg:    "success",
			Data:   result,
		}
		resultChan <- response
	}()

	// 启动goroutine监听请求取消
	go func() {
		select {
		case <-ctx.Done():
			// 请求被取消
			logger.Warning("用户取消了请求，正在终止任务...")
			errorChan <- fmt.Errorf("request cancelled")
			return
		case <-r.Context().Done():
			// 客户端断开连接
			logger.Warning("客户端断开连接")
			errorChan <- fmt.Errorf("request cancelled")
			return
		}
	}()

	// 处理结果或错误
	select {
	case result := <-resultChan:
		sendJSONResponse(w, result)
	case err := <-errorChan:
		if err.Error() == "request cancelled" {
			sendErrorResponse(w, 499, "请求已被用户取消", nil)
		} else {
			sendErrorResponse(w, 500, "fail", err.Error())
		}
	}
}

// sendJSONResponse 发送JSON响应
func sendJSONResponse(w http.ResponseWriter, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// sendErrorResponse 发送错误响应
func sendErrorResponse(w http.ResponseWriter, status int, msg string, data interface{}) {
	response := DeepSearchResponse{
		Status: status,
		Msg:    msg,
		Data:   data,
	}
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(response)
}

// printAsciiArt 打印ASCII艺术字体
func printAsciiArt(text string) {
	// 简单的ASCII艺术字体
	art := `
    ____            __  __                       __      
   / __ \___  _____/ /_/ /_  ____  ____     ____/ /______
  / /_/ / _ \/ ___/ __/ __ \/ __ \/ __ \   / __  / ___/
 / ____/  __(__  ) /_/ / / / /_/ / / / /  / /_/ (__  ) 
/_/    \___/____/\__/_/ /_/\____/_/ /_/   \__,_/____/  
`
	fmt.Println(art)
}
