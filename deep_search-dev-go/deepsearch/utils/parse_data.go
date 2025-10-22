package utils

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"time"
	"deepsearch/logs"
)

// parseQueryList 大模型生成的列表 query 解析为 list，并验证搜索时间是否符合要求，不符合要求赋值为 common
func parseQueryList(queryListStr string) ([]string, error) {
	queryList, err := ReParseList(queryListStr)
	if err != nil {
		return nil, err
	}
	
	if len(queryList) == 0 {
		return []string{}, nil
	}
	
	return queryList, nil
}

// ReParseList 正则提取大模型输出的列表字符串
func ReParseList(str string) ([]string, error) {
	var listStr string
	
	// 首先尝试匹配被 ```python 包裹的代码块
	re := regexp.MustCompile("```python\\s*([\\s\\S]*?)\\s*```")
	matches := re.FindStringSubmatch(str)
	
	if len(matches) > 1 {
		listStr = strings.TrimSpace(matches[1])
	} else {
		// 如果没有匹配到代码块，则直接使用整个字符串
		listStr = strings.TrimSpace(str)
	}
	
	// 解析 JSON 数组
	var queryList []string
	err := json.Unmarshal([]byte(listStr), &queryList)
	if err != nil {
		// 尝试直接解析为字符串列表
		if strings.HasPrefix(listStr, "[") && strings.HasSuffix(listStr, "]") {
			// 去掉方括号
			inner := strings.TrimSpace(listStr[1 : len(listStr)-1])
			// 分割字符串
			items := strings.Split(inner, ",")
			for _, item := range items {
				// 去掉引号和空格
				item = strings.TrimSpace(item)
				if strings.HasPrefix(item, "\"") && strings.HasSuffix(item, "\"") {
					item = item[1 : len(item)-1]
				} else if strings.HasPrefix(item, "'") && strings.HasSuffix(item, "'") {
					item = item[1 : len(item)-1]
				}
				queryList = append(queryList, item)
			}
		} else {
			return nil, fmt.Errorf("无法解析查询列表: %v", err)
		}
	}
	
	return queryList, nil
}

// SaveDeepsearchData 保存深度搜索的中间数据和结果
func SaveDeepsearchData(topic string, haveQuery []string, summarySearch []string, summaryText string, epoch int, projectRoot string, crawlResList []string, logger *logs.Logger, mode string) error {
	data := map[string]interface{}{
		"topic":         topic,
		"have_query":    haveQuery,
		"summary_search": summarySearch,
		"summary_text":  summaryText,
		"crawl_res":     crawlResList,
		"epoch":         epoch,
		"mode":          mode,
	}

	now := time.Now()
	dateTime := now.Format("20060102_150405")

	saveDir := filepath.Join(projectRoot, "eval", "deepsearch_data")
	err := os.MkdirAll(saveDir, 0755)
	if err != nil {
		return fmt.Errorf("创建保存目录失败: %v", err)
	}

	// 清理主题中的非法字符
	reg := regexp.MustCompile(`[\/\\:\*\?"<>\|]`)
	topic = reg.ReplaceAllString(topic, "_")
	
	savePath := filepath.Join(saveDir, fmt.Sprintf("%s_%s.json", topic[:30], dateTime))
	
	file, err := os.Create(savePath)
	if err != nil {
		return fmt.Errorf("创建保存文件失败: %v", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	err = encoder.Encode(data)
	if err != nil {
		return fmt.Errorf("写入数据失败: %v", err)
	}

	logger.Info("保存中间数据及所有结果成功！")
	return nil
}

// VerifyParams 深度搜索入参校验
func VerifyParams(topic string) (string, error) {
	topic = strings.TrimSpace(topic)
	topic = strings.ReplaceAll(topic, "/", ",")
	topic = strings.ReplaceAll(topic, "\\", ",")
	
	if topic == "" {
		return "", fmt.Errorf("主题 topic 不能为空")
	}
	
	return topic, nil
}