package api

import (
	"bytes"
	"context"
	"deepsearch/logs"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"sync"

	"github.com/sashabaranov/go-openai"
)

type LLM struct {
	client        *openai.Client
	model         string
	currentCancel context.CancelFunc
	logger        *logs.Logger
	mu            sync.Mutex
}

func NewLLM(logger *logs.Logger) *LLM {
	config := openai.DefaultConfig(os.Getenv("GLM_API_KEY"))
	config.BaseURL = os.Getenv("GLM_BASE_URL")

	model := os.Getenv("GLM_MODEL")
	if model == "" {
		model = "glm-4.5-flash"
	}

	return &LLM{
		client: openai.NewClientWithConfig(config),
		model:  model,
		logger: logger,
	}
}

func (llm *LLM) Infer(ctx context.Context, prompt string, enableThinking bool, temperature float32) (string, error) {
	llm.mu.Lock()
	defer llm.mu.Unlock()

	llm.logger.Infof("调用模型：%s......", llm.model)

	reqCtx, cancel := context.WithCancel(ctx)
	defer cancel()

	llm.currentCancel = cancel

	// 统一使用自定义HTTP请求，以便控制思考模式参数
	return llm.sendRequestWithThinkingMode(reqCtx, prompt, temperature, enableThinking)
}

// sendRequestWithThinkingMode 发送带思考模式参数的请求
func (llm *LLM) sendRequestWithThinkingMode(ctx context.Context, prompt string, temperature float32, enableThinking bool) (string, error) {
	// 根据enableThinking参数设置思考模式
	thinkingType := "disabled"
	if enableThinking {
		thinkingType = "enabled"
		llm.logger.Info("启用思考模式")
	} else {
		llm.logger.Info("禁用思考模式")
	}

	// 构建请求数据
	requestData := map[string]interface{}{
		"model": llm.model,
		"messages": []map[string]string{
			{
				"role":    "user",
				"content": prompt,
			},
		},
		"thinking": map[string]string{
			"type": thinkingType,
		},
		"max_tokens":  4096,
		"temperature": temperature,
	}

	// 序列化请求数据
	jsonData, err := json.Marshal(requestData)
	if err != nil {
		llm.logger.Error(fmt.Sprintf("序列化请求数据失败: %v", err))
		return "", fmt.Errorf("failed to marshal request data: %v", err)
	}

	// 获取配置信息（通过环境变量重新创建）
	baseURL := os.Getenv("GLM_BASE_URL")
	apiKey := os.Getenv("GLM_API_KEY")

	// 创建自定义HTTP客户端
	httpClient := &http.Client{
		Timeout: 0, // 不设置超时，完全由上下文控制
	}

	// 确保URL格式正确（去除多余的斜杠）
	endpoint := fmt.Sprintf("%s/chat/completions", strings.TrimSuffix(baseURL, "/"))

	// 创建自定义HTTP请求
	httpReq, err := http.NewRequest("POST", endpoint, bytes.NewBuffer(jsonData))
	if err != nil {
		llm.logger.Error(fmt.Sprintf("创建HTTP请求失败: %v", err))
		return "", fmt.Errorf("failed to create HTTP request: %v", err)
	}

	// 设置请求头
	httpReq.Header.Set("Content-Type", "application/json")
	httpReq.Header.Set("Authorization", fmt.Sprintf("Bearer %s", apiKey))

	// 发送请求
	llm.logger.Info("发送请求...")
	httpResp, err := httpClient.Do(httpReq.WithContext(ctx))
	if err != nil {
		llm.logger.Error(fmt.Sprintf("发送HTTP请求失败: %v", err))
		return "", fmt.Errorf("failed to send HTTP request: %v", err)
	}
	defer httpResp.Body.Close()

	// 读取响应体
	respBody, err := io.ReadAll(httpResp.Body)
	if err != nil {
		llm.logger.Error(fmt.Sprintf("读取响应体失败: %v", err))
		return "", fmt.Errorf("failed to read response body: %v", err)
	}

	// 检查HTTP状态码
	if httpResp.StatusCode != http.StatusOK {
		llm.logger.Error(fmt.Sprintf("API请求失败，状态码: %d, 响应: %s", httpResp.StatusCode, string(respBody)))
		return "", fmt.Errorf("API request failed with status code %d: %s", httpResp.StatusCode, string(respBody))
	}

	// 解析响应
	var respData struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}

	if err := json.Unmarshal(respBody, &respData); err != nil {
		llm.logger.Error(fmt.Sprintf("解析响应数据失败: %v", err))
		return "", fmt.Errorf("failed to unmarshal response data: %v", err)
	}

	// 清除取消函数
	llm.currentCancel = nil

	if len(respData.Choices) == 0 {
		return "", fmt.Errorf("no response from LLM")
	}

	return respData.Choices[0].Message.Content, nil
}

// CancelRequest 取消当前请求
func (llm *LLM) CancelRequest() bool {
	llm.mu.Lock()
	defer llm.mu.Unlock()

	if llm.currentCancel != nil {
		llm.currentCancel()
		llm.currentCancel = nil
		return true
	}
	return false
}

// 全局 LLM 实例
var GlobalLLM *LLM

// InitLLM 初始化全局 LLM 实例
func InitLLM(logger *logs.Logger) {
	GlobalLLM = NewLLM(logger)
}
