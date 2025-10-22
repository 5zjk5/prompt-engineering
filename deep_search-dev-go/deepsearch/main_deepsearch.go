package deepsearch

import (
	"context"
	"deepsearch/api"
	"deepsearch/deepsearch/utils"
	"deepsearch/logs"
	"fmt"
	"strings"
	"sync"
	"time"
)

// DeepSearch 深度搜索结构体
type DeepSearch struct {
	LLM         *api.LLM
	SearchAPI   *api.SearchAPI
	CrawlerAPI  *api.CrawlerAPI
	Logger      *logs.Logger
	ProjectRoot string
	CancelFunc  context.CancelFunc
	CancelMu    sync.Mutex
	MaxEpochs   int
}

// NewDeepSearch 创建深度搜索实例
func NewDeepSearch(projectRoot string, logger *logs.Logger) *DeepSearch {
	return &DeepSearch{
		LLM:         api.NewLLM(logger),
		SearchAPI:   api.NewSearchAPI(logger),
		CrawlerAPI:  api.NewCrawlerAPI(logger),
		Logger:      logger,
		ProjectRoot: projectRoot,
		MaxEpochs:   5,
	}
}

// Run 运行深度搜索
func (ds *DeepSearch) Run(ctx context.Context, topic string, mode string) (string, error) {
	// 记录开始时间
	startTime := time.Now()
	ds.Logger.Infof("开始深度搜索，主题: %s", topic)

	// 创建可取消的上下文
	ctx, cancel := context.WithCancel(ctx)
	ds.setCancelFunc(cancel)
	defer ds.clearCancelFunc()

	// 执行深度搜索
	result, err := ds.deepSearch(ctx, topic, mode)
	if err != nil {
		ds.Logger.Errorf("深度搜索失败: %v", err)
		return "", err
	}

	// 记录结束时间
	duration := time.Since(startTime)
	ds.Logger.Infof("深度搜索完成，耗时: %v", duration)

	return result, nil
}

// deepSearch 执行深度搜索核心逻辑
func (ds *DeepSearch) deepSearch(ctx context.Context, topic string, mode string) (string, error) {
	// 初始化变量
	var allHaveQuery []string
	var allSummarySearch []string
	var allCrawlResList []string
	actualEpochs := 0

	ds.Logger.Info("================开始================")
	ds.Logger.Infof("开始深度搜索, 深度搜索主题：%s", topic)

	// 遍历 maxEpochs 次
	for epoch := 0; epoch < ds.MaxEpochs; epoch++ {
		select {
		case <-ctx.Done():
			return "", ctx.Err()
		default:
		}

		startTime := time.Now()
		ds.Logger.Infof("开始第 %d/%d 轮搜索", epoch+1, ds.MaxEpochs)
		actualEpochs = epoch + 1

		// 第一阶段：生成搜索查询
		haveQuery, err := ds.stepFormulateQuery(ctx, topic, allHaveQuery, allSummarySearch, epoch)
		if err != nil {
			ds.Logger.Errorf("第 %d/%d 轮生成搜索查询失败: %v", epoch+1, ds.MaxEpochs, err)
			continue
		}

		if len(haveQuery) == 0 {
			ds.Logger.Infof("第 %d/%d 轮 topic 拆解无结果，开始下一轮迭代！", epoch+1, ds.MaxEpochs)
			continue
		}

		// 更新已有的查询列表
		allHaveQuery = append(allHaveQuery, haveQuery...)

		// 第二阶段：执行搜索和爬取
		crawlResList, err := ds.stepSearchAndCrawl(ctx, topic, haveQuery, allSummarySearch)
		if err != nil {
			ds.Logger.Errorf("第 %d/%d 轮搜索和爬取失败: %v", epoch+1, ds.MaxEpochs, err)
			continue
		}

		if len(crawlResList) == 0 {
			ds.Logger.Infof("第 %d/%d 轮搜索无结果，开始下一轮迭代！", epoch+1, ds.MaxEpochs)
			continue
		}

		// 更新总结和爬取结果列表
		allSummarySearch = append(allSummarySearch, crawlResList...)
		allCrawlResList = append(allCrawlResList, crawlResList...)

		// 第三阶段：评估爬取结果，判断是否足够回答 topic
		answer, err := ds.stepSummarizeCrawlRes(ctx, crawlResList, topic, allSummarySearch)
		if err != nil {
			ds.Logger.Errorf("第 %d/%d 轮评估爬取结果失败: %v", epoch+1, ds.MaxEpochs, err)
			continue
		}

		// 一轮耗时
		duration := time.Since(startTime)
		ds.Logger.Infof("第 %d/%d 轮搜索耗时：%v", epoch+1, ds.MaxEpochs, duration)

		// 评估反思信息足够了就退出
		if strings.Contains(strings.ToLower(answer), "yes") {
			break
		}
	}

	// 第四阶段：生成最终总结
	summaryText, err := ds.stepFinalSummary(ctx, topic, allSummarySearch)
	if err != nil {
		return "", fmt.Errorf("生成最终总结失败: %v", err)
	}

	// 保存结果
	err = utils.SaveDeepsearchData(topic, allHaveQuery, allSummarySearch, summaryText, actualEpochs, ds.ProjectRoot, allCrawlResList, ds.Logger, mode)
	if err != nil {
		ds.Logger.Errorf("保存深度搜索数据失败: %v", err)
		return "", fmt.Errorf("保存深度搜索数据失败: %v", err)
	}

	ds.Logger.Infof("总共进行了 %d 轮深度搜索！", actualEpochs)
	ds.Logger.Infof("topic: %s", topic)
	ds.Logger.Info("================deepsearch 结束================")

	return summaryText, nil
}

// stepFormulateQuery 第一步：生成搜索查询
func (ds *DeepSearch) stepFormulateQuery(ctx context.Context, topic string, allHaveQuery []string, allSummarySearch []string, epoch int) ([]string, error) {
	ds.Logger.Info("第一步：生成搜索查询")

	// 使用工具函数生成查询
	haveQuery, err := utils.FormulateQuery(ctx, topic, allHaveQuery, allSummarySearch, ds.Logger, 5)
	if err != nil {
		return nil, fmt.Errorf("生成查询失败: %v", err)
	}

	// 如果为第一轮把原始 topic 加入去搜索
	if epoch == 0 && len(haveQuery) > 0 {
		haveQuery = append(haveQuery, topic)
	}

	ds.Logger.Infof("生成的查询列表: %v", haveQuery)
	return haveQuery, nil
}

// stepSearchAndCrawl 第二步：执行搜索和爬取
func (ds *DeepSearch) stepSearchAndCrawl(ctx context.Context, topic string, haveQuery []string, allSummarySearch []string) ([]string, error) {
	ds.Logger.Info("第二步：执行搜索和爬取")

	// 创建搜索和爬取实例
	searchCrawl := NewSearchCrawl(ds.Logger)

	// 调用 main_search.go 中的 Run 运行搜索和爬取，传入 topic（string） haveQuery（list）
	crawlResList, err := searchCrawl.Run(ctx, topic, haveQuery, allSummarySearch)
	if err != nil {
		return nil, fmt.Errorf("搜索和爬取失败: %v", err)
	}

	return crawlResList, nil
}

// stepSummarizeCrawlRes 第二步.5：总结爬取结果并判断是否满足需求
func (ds *DeepSearch) stepSummarizeCrawlRes(ctx context.Context, crawlResList []string, topic string, allSummarySearch []string) (string, error) {
	ds.Logger.Info("第二步.5：总结爬取结果并判断是否满足需求")

	// 使用工具函数总结爬取结果
	answer, _, err := utils.SummarizeCrawlRes(ctx, crawlResList, topic, allSummarySearch, ds.Logger)
	if err != nil {
		return "", fmt.Errorf("总结爬取结果失败: %v", err)
	}

	ds.Logger.Infof("评估结果: %v", answer)
	return answer, nil
}

// stepFinalSummary 第三步：生成最终总结
func (ds *DeepSearch) stepFinalSummary(ctx context.Context, topic string, summarySearch []string) (string, error) {
	ds.Logger.Info("第三步：生成最终总结")

	// 使用工具函数生成最终总结
	summaryText, err := utils.FinalSummary(ctx, topic, summarySearch, ds.Logger)
	if err != nil {
		return "", fmt.Errorf("生成最终总结失败: %v", err)
	}

	return summaryText, nil
}

// Cancel 取消深度搜索
func (ds *DeepSearch) Cancel() {
	ds.CancelMu.Lock()
	defer ds.CancelMu.Unlock()

	if ds.CancelFunc != nil {
		ds.CancelFunc()
		ds.Logger.Info("深度搜索已取消")
	}
}

// setCancelFunc 设置取消函数
func (ds *DeepSearch) setCancelFunc(cancel context.CancelFunc) {
	ds.CancelMu.Lock()
	defer ds.CancelMu.Unlock()

	ds.CancelFunc = cancel
}

// clearCancelFunc 清除取消函数
func (ds *DeepSearch) clearCancelFunc() {
	ds.CancelMu.Lock()
	defer ds.CancelMu.Unlock()

	ds.CancelFunc = nil
}
