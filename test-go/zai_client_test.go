package main

import (
	"testing"
)

func TestProcessQuotaLimit(t *testing.T) {
	// Test with valid data
	data := map[string]interface{}{
		"limits": []interface{}{
			map[string]interface{}{
				"type":       "TOKENS_LIMIT",
				"percentage": float64(25),
			},
			map[string]interface{}{
				"type":         "TIME_LIMIT",
				"percentage":   float64(10),
				"currentValue": float64(5),
				"usage":        float64(100),
				"usageDetails": []interface{}{
					map[string]interface{}{
						"modelCode": "search-prime",
						"usage":     float64(3),
					},
					map[string]interface{}{
						"modelCode": "web-reader",
						"usage":     float64(2),
					},
				},
			},
		},
	}

	result := ProcessQuotaLimit(data)

	if len(result.Limits) != 2 {
		t.Errorf("Expected 2 limits, got %d", len(result.Limits))
	}

	// Check token limit transformation
	if result.Limits[0].Type != "Token usage(5 Hour)" {
		t.Errorf("Expected 'Token usage(5 Hour)', got '%s'", result.Limits[0].Type)
	}

	// Check MCP limit transformation
	if result.Limits[1].Type != "MCP usage(1 Month)" {
		t.Errorf("Expected 'MCP usage(1 Month)', got '%s'", result.Limits[1].Type)
	}
}

func TestFormatGLMQuota(t *testing.T) {
	processedData := ProcessedZAILimit{
		Limits: []ProcessedLimit{
			{
				Type:       "Token usage(5 Hour)",
				Percentage: 25,
			},
			{
				Type:         "MCP usage(1 Month)",
				Percentage:   10,
				CurrentUsage: 5,
				Total:        100,
				UsageDetails: []ZAIUsageDetail{
					{ModelCode: "search-prime", Usage: 3},
					{ModelCode: "web-reader", Usage: 2},
					{ModelCode: "zread", Usage: 5}, // Should be excluded
				},
			},
		},
	}

	result := FormatGLMQuota(processedData)

	if len(result.Models) != 4 { // glm + mcp-monthly + search-prime + web-reader (zread excluded)
		t.Errorf("Expected 4 models, got %d", len(result.Models))
	}

	// Check GLM token quota (100 - 25 = 75)
	glmModel := result.Models[0]
	if glmModel.Name != "glm" || glmModel.Percentage != 75 {
		t.Errorf("Expected glm model with 75%%, got %s with %d%%", glmModel.Name, glmModel.Percentage)
	}

	// Check that zread is excluded
	for _, model := range result.Models {
		if model.Name == "glm-coding-plan-zread" {
			t.Error("zread should be excluded from models")
		}
	}
}

func TestGetBaseDomain(t *testing.T) {
	tests := []struct {
		baseURL  string
		platform string
		domain   string
		hasError bool
	}{
		{
			baseURL:  "https://api.z.ai/api/anthropic",
			platform: "ZAI",
			domain:   "https://api.z.ai",
			hasError: false,
		},
		{
			baseURL:  "https://open.bigmodel.cn/api/anthropic",
			platform: "ZHIPU",
			domain:   "https://open.bigmodel.cn",
			hasError: false,
		},
		{
			baseURL:  "https://invalid.com/api",
			platform: "",
			domain:   "",
			hasError: true,
		},
	}

	for _, test := range tests {
		platform, domain, err := GetBaseDomain(test.baseURL)

		if test.hasError {
			if err == nil {
				t.Errorf("Expected error for %s, got none", test.baseURL)
			}
		} else {
			if err != nil {
				t.Errorf("Unexpected error for %s: %v", test.baseURL, err)
			}
			if platform != test.platform {
				t.Errorf("Expected platform %s, got %s", test.platform, platform)
			}
			if domain != test.domain {
				t.Errorf("Expected domain %s, got %s", test.domain, domain)
			}
		}
	}
}
