package logs

import (
	"fmt"
	"log"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"
)

// LogLevel 定义日志级别类型
type LogLevel int

const (
	DEBUG LogLevel = iota
	INFO
	WARNING
	ERROR
	CRITICAL
)

// Logger 结构体封装了日志功能
type Logger struct {
	consoleLogger *log.Logger
	fileLogger    *log.Logger
	printLevel    LogLevel
	logfileLevel  LogLevel
}

// defineLogLevel 创建独立的 logger，支持记录模块、函数、行号
func DefineLogLevel(projectRoot, topic, printLevel, logfileLevel string) (*Logger, string) {
	// 清理主题中的非法字符
	reg := regexp.MustCompile(`[\/\\:\*\?"<>\|]`)
	topic = reg.ReplaceAllString(topic, "_")

	// 获取当前时间
	now := time.Now()
	dateDir := now.Format("2006-01-02")

	// 确保topic长度不超过30个字符
	var logName string
	if len(topic) > 30 {
		logName = topic[:30] + "_" + now.Format("15_04_05") + ".log"
	} else {
		logName = topic + "_" + now.Format("15_04_05") + ".log"
	}

	// 创建日志目录
	logDir := filepath.Join(projectRoot, "logs", "logs", dateDir)
	err := os.MkdirAll(logDir, 0755)
	if err != nil {
		log.Fatalf("Failed to create log directory: %v", err)
	}

	// 打开日志文件
	file, err := os.OpenFile(filepath.Join(logDir, logName), os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
	if err != nil {
		log.Fatalf("Failed to open log file: %v", err)
	}

	// 解析日志级别
	pLevel := parseLogLevel(printLevel)
	lLevel := parseLogLevel(logfileLevel)

	// 返回自定义 Logger 结构体
	return &Logger{
		consoleLogger: log.New(os.Stderr, "", 0), // 不使用默认格式，我们自己格式化
		fileLogger:    log.New(file, "", 0),      // 不使用默认格式，我们自己格式化
		printLevel:    pLevel,
		logfileLevel:  lLevel,
	}, logName
}

// parseLogLevel 将字符串转换为日志级别
func parseLogLevel(level string) LogLevel {
	switch strings.ToUpper(level) {
	case "DEBUG":
		return DEBUG
	case "INFO":
		return INFO
	case "WARNING", "WARN":
		return WARNING
	case "ERROR":
		return ERROR
	case "CRITICAL", "FATAL":
		return CRITICAL
	default:
		return INFO
	}
}

// formatMessage 格式化日志消息，不添加级别信息（在logInternal中统一添加）
func (l *Logger) formatMessage(format string, v ...interface{}) string {
	if format == "" {
		return fmt.Sprint(v...)
	}
	return fmt.Sprintf(format, v...)
}

// shouldLog 检查是否应该记录日志
func (l *Logger) shouldLog(level LogLevel) bool {
	return level >= l.printLevel || level >= l.logfileLevel
}

// getCallerInfo 获取调用者信息，包括文件名、函数名和行号
func (l *Logger) getCallerInfo(skip int) (file, function string, line int) {
	pc, file, line, ok := runtime.Caller(skip)
	if !ok {
		return "unknown", "unknown", 0
	}

	// 获取函数名
	function = runtime.FuncForPC(pc).Name()

	// 提取文件名，去掉路径
	file = filepath.Base(file)

	return file, function, line
}

// logInternal 内部日志记录方法
func (l *Logger) logInternal(level LogLevel, levelStr string, format string, v ...interface{}) {
	if !l.shouldLog(level) {
		return
	}

	// 获取调用者信息，跳过3层以获取实际调用者
	file, function, line := l.getCallerInfo(3)

	// 格式化函数名，去掉包路径
	funcParts := strings.Split(function, ".")
	if len(funcParts) > 1 {
		function = funcParts[len(funcParts)-1]
	}

	// 格式化消息
	message := l.formatMessage(format, v...)

	// 添加调用者信息，类似Python的日志格式
	// 格式: 时间 [级别] 文件名:函数名:行号 - 消息
	now := time.Now().Format("2006/01/02 15:04:05")
	callerInfo := fmt.Sprintf("%s:%s:%d", file, function, line)
	fullMessage := fmt.Sprintf("%s [%s] %s - %s", now, levelStr, callerInfo, message)

	if level >= l.printLevel {
		l.consoleLogger.Output(2, fullMessage)
	}

	if level >= l.logfileLevel {
		l.fileLogger.Output(2, fullMessage)
	}
}

// Infof 记录信息级别的日志
func (l *Logger) Infof(format string, v ...interface{}) {
	l.logInternal(INFO, "INFO", format, v...)
}

// Warningf 记录警告级别的日志
func (l *Logger) Warningf(format string, v ...interface{}) {
	l.logInternal(WARNING, "WARNING", format, v...)
}

// Errorf 记录错误级别的日志
func (l *Logger) Errorf(format string, v ...interface{}) {
	l.logInternal(ERROR, "ERROR", format, v...)
}

// Debugf 记录调试级别的日志
func (l *Logger) Debugf(format string, v ...interface{}) {
	l.logInternal(DEBUG, "DEBUG", format, v...)
}

// Criticalf 记录严重错误级别的日志
func (l *Logger) Criticalf(format string, v ...interface{}) {
	l.logInternal(CRITICAL, "CRITICAL", format, v...)
}

// Info 记录信息级别的日志
func (l *Logger) Info(v ...interface{}) {
	l.logInternal(INFO, "INFO", "", v...)
}

// Warning 记录警告级别的日志
func (l *Logger) Warning(v ...interface{}) {
	l.logInternal(WARNING, "WARNING", "", v...)
}

// Error 记录错误级别的日志
func (l *Logger) Error(v ...interface{}) {
	l.logInternal(ERROR, "ERROR", "", v...)
}

// Debug 记录调试级别的日志
func (l *Logger) Debug(v ...interface{}) {
	l.logInternal(DEBUG, "DEBUG", "", v...)
}

// Critical 记录严重错误级别的日志
func (l *Logger) Critical(v ...interface{}) {
	l.logInternal(CRITICAL, "CRITICAL", "", v...)
}

// Exception 记录异常信息，类似Python的logger.exception
func (l *Logger) Exception(v ...interface{}) {
	l.logInternal(ERROR, "ERROR", "", v...)
}
