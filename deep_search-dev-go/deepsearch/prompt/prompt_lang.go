package prompt

import (
	"text/template"
)

// PromptTemplates 包含所有提示词模板
var PromptTemplates = map[string]*template.Template{
	"formulate_query":   template.Must(template.New("formulate_query").Parse(FormulateQueryPrompt)),
	"related_url":      template.Must(template.New("related_url").Parse(RelatedUrlPrompt)),
	"summary_crawl_res": template.Must(template.New("summary_crawl_res").Parse(SummaryCrawlResPrompt)),
	"final_summary":    template.Must(template.New("final_summary").Parse(FinalSummaryPrompt)),
}

// GetPromptTemplate 获取指定名称的提示词模板
func GetPromptTemplate(name string) *template.Template {
	if tmpl, ok := PromptTemplates[name]; ok {
		return tmpl
	}
	return nil
}