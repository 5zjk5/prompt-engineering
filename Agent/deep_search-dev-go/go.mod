module deepsearch

go 1.22

require (
	github.com/joho/godotenv v1.5.1
	github.com/playwright-community/playwright-go v0.5200.1
	github.com/sashabaranov/go-openai v1.20.0
)

require (
	github.com/deckarep/golang-set/v2 v2.8.0 // indirect
	github.com/go-jose/go-jose/v3 v3.0.4 // indirect
	github.com/go-stack/stack v1.8.1 // indirect
)

// 确保本地包能够被正确导入
replace deepsearch => ./
