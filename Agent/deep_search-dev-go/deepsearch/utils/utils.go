package utils

import (
	"context"
	"fmt"
	"strings"
	"deepsearch/api"
	"deepsearch/deepsearch/prompt"
	"deepsearch/logs"
)

// FormulateQuery 根据 topic 规划出指定数量的 query
func FormulateQuery(ctx context.Context, topic string, haveQuery []string, summarySearch []string, logger *logs.Logger, queryNum int) ([]string, error) {
	logger.Info("开始根据 topic 规划 query！")

	// 构建提示词
	promptText := fmt.Sprintf(prompt.FormulateQueryPrompt, queryNum, haveQuery, summarySearch, topic)
	logger.Infof("规划 query prompt：\n%s", promptText)

	logger.Info("调用 LLM 规划 query...")
	
	// 调用 LLM
	response, err := api.GlobalLLM.Infer(ctx, promptText, false, 0.7)
	if err != nil {
		logger.Errorf("调用 LLM 规划 query 失败: %v", err)
		return nil, err
	}
	
	logger.Infof("规划 query 结果：\n%s", response)

	// 解析查询列表
	logger.Info("解析 query 规划结果...")
	queryList, err := parseQueryList(response)
	if err != nil {
		logger.Errorf("解析 query 规划结果失败: %v", err)
		return nil, err
	}
	
	logger.Infof("解析 query 规划结果 query 列表：\n%v", queryList)

	return queryList, nil
}

// SummarizeCrawlRes 根据爬取结果进行总结，并判断是否满足了 topic 要求
func SummarizeCrawlRes(ctx context.Context, crawlRes []string, topic string, summarySearch []string, logger *logs.Logger) (string, string, error) {
	logger.Info("开始评估，总结新内容...")

	// 构建提示词
	promptText := fmt.Sprintf(prompt.SummaryCrawlResPrompt, summarySearch, crawlRes, topic)
	logger.Infof("评估，总结新内容 prompt：\n%s", promptText)

	logger.Info("调用 LLM 评估，总结新内容...")
	
	// 调用 LLM
	response, err := api.GlobalLLM.Infer(ctx, promptText, false, 0.7)
	if err != nil {
		logger.Errorf("调用 LLM 评估，总结新内容失败: %v", err)
		return "no", "", err
	}
	
	logger.Infof("评估，总结新内容结果：\n%s", response)

	// 解析响应
	response = strings.ToLower(response)
	
	// 提取答案部分
	answer := response
	if summaryIndex := strings.Index(response, "总结"); summaryIndex != -1 {
		answer = response[:summaryIndex]
	}
	if analysisIndex := strings.Index(response, "分析"); analysisIndex != -1 {
		answer = response[:analysisIndex]
	}
	
	// 提取总结部分
	summary := ""
	if summaryParts := strings.Split(response, "总结"); len(summaryParts) > 1 {
		summary = strings.Join(summaryParts[1:], "")
	} else {
		summary = response
	}
	
	summary = strings.ReplaceAll(summary, "\n", "")
	logger.Infof("解析后评估，总结新内容：\n评估：%s\n总结：%s", answer, summary)

	return answer, summary, nil
}

// FinalSummary 把所有轮次总结的搜索结果汇总做最后的总结
func FinalSummary(ctx context.Context, topic string, summarySearch []string, logger *logs.Logger) (string, error) {
	logger.Info("开始最后总结内容...")

	// 构建提示词
	promptText := fmt.Sprintf(prompt.FinalSummaryPrompt, topic, summarySearch)
	logger.Infof("最后总结内容 prompt：\n%s", promptText)

	logger.Info("调用 LLM 最后总结内容...")
	
	// 调用 LLM
	response, err := api.GlobalLLM.Infer(ctx, promptText, false, 0.2)
	if err != nil {
		logger.Errorf("调用 LLM 最后总结内容失败: %v", err)
		logger.Error("使用每一轮的搜索总结作为结果！")
		return strings.Join(summarySearch, "。"), nil
	}
	
	logger.Infof("最后总结内容结果共 %d 字符：\n%s", len(response), response)

	return response, nil
}