package main

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"deepsearch/api"
	"deepsearch/logs"

	"github.com/joho/godotenv"
)

func main() {
	// 初始化日志
	projectRoot := filepath.Dir(os.Args[0])
	logger, _ := logs.DefineLogLevel(projectRoot, "test_llm_api", "INFO", "INFO")
	logger.Info("开始测试LLM API...")

	// 加载环境变量
	err := godotenv.Load()
	if err != nil {
		logger.Info("未找到.env文件，使用系统环境变量")
	} else {
		logger.Info("已加载.env文件")
	}

	// 检查环境变量
	apiKey := os.Getenv("GLM_API_KEY")
	baseURL := os.Getenv("GLM_BASE_URL")
	model := os.Getenv("GLM_MODEL")

	logger.Info(fmt.Sprintf("环境变量检查:"))
	if apiKey == "" {
		logger.Error("GLM_API_KEY 未设置")
	} else {
		if len(apiKey) > 10 {
			logger.Info(fmt.Sprintf("GLM_API_KEY: %s...", apiKey[:10]))
		} else {
			logger.Info(fmt.Sprintf("GLM_API_KEY: %s", apiKey))
		}
	}

	if baseURL == "" {
		logger.Error("GLM_BASE_URL 未设置")
	} else {
		logger.Info(fmt.Sprintf("GLM_BASE_URL: %s", baseURL))
	}

	if model == "" {
		logger.Info("GLM_MODEL 未设置，将使用默认值")
	} else {
		logger.Info(fmt.Sprintf("GLM_MODEL: %s", model))
	}

	// 初始化全局LLM实例
	api.InitLLM(logger)
	if api.GlobalLLM == nil {
		logger.Error("初始化LLM失败")
		return
	}

	// 定义提示词模板
	promptTemplate := "# 角色 \n" +
		"你是一名专业的搜索专家，对搜索查询有着深刻的理解，能根据主题精心制作有针对性的网络搜索查询，能使用这些跟主题高度相关的查询收集全面的信息。\n\n\n" +
		"## 背景 \n" +
		"用户给定了一个主题，需要根据这个主题去搜索查询一些跟主题相关的资料，用于生成参考文章，所以需要拆解一些跟主题高度相关的子主题去进行搜索。\n\n\n" +
		"## 任务 \n" +
		"您的任务是生成 3 个搜索查询。新生成的查询必须确保不与现有的查询重复，且适合用于搜索引擎检索。 \n" +
		"此外，新查询应基于现有信息进行补充和完善。这样可以确保生成的查询既丰富又具有针对性，能够有效提升搜索效率和结果的相关性。 \n" +
		"这将有助于收集本节主题相关的综合信息。 \n" +
		"以下是已有查询： \n" +
		"\"人工智能的发展历史\" \n" +
		"以下是已有信息： \n" +
		"\"人工智能从20世纪50年代开始发展，经历了多次起伏\"\n\n\n" +
		"## 主题 \n" +
		"人工智能的未来发展趋势\n\n\n" +
		"## 输出 \n" +
		"严格按照 python 列表格式，以 markdown 格式输出，例如：```python" + `[\"查询1\", ......]` + "```\n\n\n" +
		"## 限制 \n" +
		"- 生成的每个 query 必须与主题高度相关关键词，你必须细节一些，不能笼统。 \n" +
		"- 每个 query 都是不同的子主题。 \n" +
		"- 使查询足够具体，以便找到高质量的相关来源。 \n" +
		"- 时间必须来自时间列表，不能自己创造。 \n" +
		"- 输出格式必须是符合 python 格式的列表类型，不能残缺括号，其中的字符串格式必须使用引号括起来，不要输出其他任何多余的信息。 \n" +
		"- 生成的查询不能跟已有查询重复。 \n" +
		"- 每个查询不能过于泛化，语义结构自然一些，生成的 query 不能与已有查询高度相似。"

	// 测试用例
	testCases := []struct {
		enableThinking bool
		temperature    float32
		description    string
	}{
		{
			enableThinking: false,
			temperature:    0.7,
			description:    "搜索查询生成测试",
		},
		{
			enableThinking: true,
			temperature:    0.7,
			description:    "搜索查询生成测试（启用思考模式）",
		},
	}

	// 执行测试
	for i, tc := range testCases {
		logger.Info(fmt.Sprintf("【测试 %d/%d】%s", i+1, len(testCases), tc.description))
		logger.Info(fmt.Sprintf("思考模式: %v", tc.enableThinking))

		// 创建上下文，设置超时时间
		ctx, cancel := context.WithTimeout(context.Background(), 300*time.Second)
		defer cancel()

		// 调用LLM接口前记录时间
		startTime := time.Now()
		logger.Info(fmt.Sprintf("开始调用LLM API: %v", startTime.Format("15:04:05.000")))
		
		response, err := api.GlobalLLM.Infer(ctx, promptTemplate, tc.enableThinking, tc.temperature)
		
		// 计算调用耗时
		elapsedTime := time.Since(startTime)
		endTime := time.Now()
		logger.Info(fmt.Sprintf("LLM API调用完成: %v", endTime.Format("15:04:05.000")))
		logger.Info(fmt.Sprintf("总耗时: %v (毫秒: %d)", elapsedTime, elapsedTime.Milliseconds()))

		if err != nil {
			logger.Error(fmt.Sprintf("❌ 测试失败: %v", err))
			continue
		}

		// 截取响应前100个字符用于日志
		shortResponse := response
		// if len(shortResponse) > 100 {
		// 	shortResponse = shortResponse[:100]
		// }

		logger.Info(fmt.Sprintf("✅ 测试成功 | 响应长度: %d", len(response)))
		logger.Info(fmt.Sprintf("响应预览: %s...", shortResponse))
		logger.Info("----------------------------------------\n")
	}

	logger.Info("所有LLM API测试已完成")
}
