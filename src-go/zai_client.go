package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"
)

// ZAICache holds cached Z.ai API responses
type ZAICache struct {
	mu    sync.RWMutex
	cache map[string]CacheEntry
}

type CacheEntry struct {
	Data      interface{}
	ExpiresAt time.Time
}

var zaiCache = &ZAICache{
	cache: make(map[string]CacheEntry),
}

// ZAIQuotaLimit represents the quota limit response structure
type ZAIQuotaLimit struct {
	Limits []ZAILimit `json:"limits"`
}

type ZAILimit struct {
	Type         string           `json:"type"`
	Percentage   int              `json:"percentage"`
	CurrentUsage int              `json:"currentUsage,omitempty"`
	Total        int              `json:"usage,omitempty"`
	UsageDetails []ZAIUsageDetail `json:"usageDetails,omitempty"`
}

type ZAIUsageDetail struct {
	ModelCode string `json:"modelCode"`
	Usage     int    `json:"usage"`
}

// ProcessedZAILimit represents processed quota limit data
type ProcessedZAILimit struct {
	Limits []ProcessedLimit `json:"limits"`
}

type ProcessedLimit struct {
	Type         string           `json:"type"`
	Percentage   int              `json:"percentage"`
	CurrentUsage int              `json:"currentUsage,omitempty"`
	Total        int              `json:"usage,omitempty"`
	UsageDetails []ZAIUsageDetail `json:"usageDetails,omitempty"`
}

// QueryZAIEndpoint queries a Z.ai API endpoint with caching
func QueryZAIEndpoint(ctx context.Context, endpoint, authToken, queryParams string) (interface{}, error) {
	cacheKey := endpoint + queryParams

	// Check cache first
	zaiCache.mu.RLock()
	if entry, exists := zaiCache.cache[cacheKey]; exists && time.Now().Before(entry.ExpiresAt) {
		zaiCache.mu.RUnlock()
		fmt.Println("Returning cached z.ai data")
		return entry.Data, nil
	}
	zaiCache.mu.RUnlock()

	// Make HTTP request
	fullURL := endpoint + queryParams
	req, err := http.NewRequestWithContext(ctx, "GET", fullURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Authorization", authToken)
	req.Header.Set("Accept-Language", "en-US,en")
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to query Z.ai API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("Z.ai API error: status %d", resp.StatusCode)
	}

	var result map[string]interface{}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return nil, fmt.Errorf("failed to decode response: %w", err)
	}

	// Extract data field if present
	if data, exists := result["data"]; exists {
		result = data.(map[string]interface{})
	}

	// Cache the result
	config := LoadConfig()
	expiry := time.Now().Add(time.Duration(config.QueryDebounce) * time.Minute)
	zaiCache.mu.Lock()
	zaiCache.cache[cacheKey] = CacheEntry{
		Data:      result,
		ExpiresAt: expiry,
	}
	zaiCache.mu.Unlock()

	fmt.Printf("Cached z.ai data for %d minute(s)\n", config.QueryDebounce)
	return result, nil
}

// GetBaseDomain extracts platform and base domain from ANTHROPIC_BASE_URL
func GetBaseDomain(baseURL string) (string, string, error) {
	if strings.Contains(baseURL, "api.z.ai") {
		return "ZAI", "https://api.z.ai", nil
	}
	if strings.Contains(baseURL, "open.bigmodel.cn") || strings.Contains(baseURL, "dev.bigmodel.cn") {
		parsedURL, err := url.Parse(baseURL)
		if err != nil {
			return "", "", fmt.Errorf("failed to parse URL: %w", err)
		}
		return "ZHIPU", fmt.Sprintf("%s://%s", parsedURL.Scheme, parsedURL.Host), nil
	}
	return "", "", fmt.Errorf("unrecognized ANTHROPIC_BASE_URL: %s. Supported: https://api.z.ai/api/anthropic or https://open.bigmodel.cn/api/anthropic", baseURL)
}

// BuildTimeQueryParams builds query parameters for time-based endpoints
func BuildTimeQueryParams() string {
	now := time.Now().UTC()
	startDate := time.Date(now.Year(), now.Month(), now.Day()-1, now.Hour(), 0, 0, 0, time.UTC)
	endDate := time.Date(now.Year(), now.Month(), now.Day(), now.Hour(), 59, 59, 999999999, time.UTC)

	startTime := startDate.Format("2006-01-02 15:04:05")
	endTime := endDate.Format("2006-01-02 15:04:05")

	return fmt.Sprintf("?startTime=%s&endTime=%s", url.QueryEscape(startTime), url.QueryEscape(endTime))
}

// ProcessQuotaLimit processes quota limit data to transform type names
func ProcessQuotaLimit(data map[string]interface{}) ProcessedZAILimit {
	result := ProcessedZAILimit{}

	limits, exists := data["limits"]
	if !exists {
		return result
	}

	limitsArray, ok := limits.([]interface{})
	if !ok {
		return result
	}

	for _, item := range limitsArray {
		limitMap, ok := item.(map[string]interface{})
		if !ok {
			continue
		}

		limitType, _ := limitMap["type"].(string)
		percentage, _ := limitMap["percentage"].(float64)

		processedLimit := ProcessedLimit{
			Percentage: int(percentage),
		}

		switch limitType {
		case "TOKENS_LIMIT":
			processedLimit.Type = "Token usage(5 Hour)"
		case "TIME_LIMIT":
			processedLimit.Type = "MCP usage(1 Month)"
			if currentUsage, ok := limitMap["currentValue"].(float64); ok {
				processedLimit.CurrentUsage = int(currentUsage)
			}
			if total, ok := limitMap["usage"].(float64); ok {
				processedLimit.Total = int(total)
			}
			if usageDetails, ok := limitMap["usageDetails"].([]interface{}); ok {
				for _, detail := range usageDetails {
					if detailMap, ok := detail.(map[string]interface{}); ok {
						modelCode, _ := detailMap["modelCode"].(string)
						usage, _ := detailMap["usage"].(float64)
						processedLimit.UsageDetails = append(processedLimit.UsageDetails, ZAIUsageDetail{
							ModelCode: modelCode,
							Usage:     int(usage),
						})
					}
				}
			}
		default:
			processedLimit.Type = limitType
		}

		result.Limits = append(result.Limits, processedLimit)
	}

	return result
}

// FormatGLMQuota formats GLM quota limit data to match antigravity quota format
func FormatGLMQuota(quotaLimitData ProcessedZAILimit) FormattedQuota {
	models := []FormattedModel{}

	for _, limit := range quotaLimitData.Limits {
		switch limit.Type {
		case "Token usage(5 Hour)":
			// Token limit: show remaining percentage (100 - used)
			models = append(models, FormattedModel{
				Name:       "glm",
				Percentage: 100 - limit.Percentage,
			})
		case "MCP usage(1 Month)":
			// MCP limit: show remaining percentage
			models = append(models, FormattedModel{
				Name:       "glm-coding-plan-mcp-monthly",
				Percentage: 100 - limit.Percentage,
			})

			// Add individual tool usage details (excluding zread)
			for _, detail := range limit.UsageDetails {
				if detail.ModelCode == "zread" {
					continue
				}

				toolPercentage := 0
				if limit.Total > 0 {
					toolPercentage = int(float64(detail.Usage) / float64(limit.Total) * 100)
				}

				models = append(models, FormattedModel{
					Name:       fmt.Sprintf("glm-coding-plan-%s", detail.ModelCode),
					Percentage: 100 - toolPercentage,
				})
			}
		}
	}

	return FormattedQuota{
		Models:      models,
		LastUpdated: time.Now().Unix(),
		IsForbidden: false,
	}
}

// GetGLMQuota gets GLM quota data from Z.ai/ZHIPU API
func GetGLMQuota(ctx context.Context) (FormattedQuota, error) {
	baseURL := os.Getenv("ANTHROPIC_BASE_URL")
	authToken := os.Getenv("ANTHROPIC_AUTH_TOKEN")

	if authToken == "" {
		return FormattedQuota{}, fmt.Errorf("ANTHROPIC_AUTH_TOKEN environment variable is not set")
	}

	if baseURL == "" {
		return FormattedQuota{}, fmt.Errorf("ANTHROPIC_BASE_URL environment variable is not set. Set it to https://api.z.ai/api/anthropic or https://open.bigmodel.cn/api/anthropic")
	}

	// Get platform and base domain
	_, baseDomain, err := GetBaseDomain(baseURL)
	if err != nil {
		return FormattedQuota{}, err
	}

	// Query quota limit endpoint
	quotaLimitURL := baseDomain + "/api/monitor/usage/quota/limit"
	quotaLimitRaw, err := QueryZAIEndpoint(ctx, quotaLimitURL, authToken, "")
	if err != nil {
		return FormattedQuota{}, err
	}

	quotaLimitMap, ok := quotaLimitRaw.(map[string]interface{})
	if !ok {
		return FormattedQuota{}, fmt.Errorf("invalid quota limit response format")
	}

	quotaLimitProcessed := ProcessQuotaLimit(quotaLimitMap)

	// Format to match antigravity quota format
	return FormatGLMQuota(quotaLimitProcessed), nil
}
