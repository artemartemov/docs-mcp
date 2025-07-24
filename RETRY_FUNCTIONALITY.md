# Failed URL Retry Functionality

## Overview

The documentation ingestion system now includes comprehensive retry functionality that automatically tracks failed URLs and allows you to re-process only the failed items from previous ingestion runs.

## How It Works

### 1. Automatic Failed URL Tracking

During ingestion, the system automatically:
- **Tracks all failed URLs** with detailed error messages
- **Saves failed URLs to JSON files** in the `logs/` directory
- **Provides retry instructions** at the end of each ingestion

### 2. Failed URL File Format

Failed URL files are saved as JSON with comprehensive metadata:

```json
{
  "framework": "swiftui",
  "source_name": "SwiftUI latest Official Docs",
  "base_url": "https://developer.apple.com/documentation/swiftui/",
  "timestamp": "2025-07-23T12:30:08.123456",
  "total_failed": 15,
  "failed_urls": {
    "https://developer.apple.com/documentation/swiftui/text": "Invalid or empty content extracted",
    "https://developer.apple.com/documentation/swiftui/button": "Error processing: TimeoutError",
    "...": "..."
  },
  "ingestion_stats": {
    "total_discovered": 78,
    "total_processed": 78,
    "successful_ingestions": 63,
    "failed_ingestions": 15,
    "success_rate": 80.8,
    "elapsed_time": 245.6
  }
}
```

## Usage Examples

### 1. Basic Retry Commands

#### Using Makefile (Recommended)

```bash
# List all available failed URL files
make list-failed-files

# Retry specific framework with automatic file detection
make retry-swiftui FAILED_FILE=logs/failed_urls_swiftui_20250723_123008.json

# Generic retry command
make retry SOURCE=figma FAILED_FILE=logs/failed_urls_figma_20250723_124501.json
```

#### Using Direct Script

```bash
# Retry failed URLs directly
./run_ingestion.sh --source swiftui --retry logs/failed_urls_swiftui_20250723_123008.json

# Retry in test mode (only first 10 failed URLs)
./run_ingestion.sh --source swiftui --retry logs/failed_urls_swiftui_20250723_123008.json --test
```

### 2. Complete Workflow Example

```bash
# 1. Initial ingestion (some URLs may fail)
make ingest-swiftui

# 2. Check the output for failed URLs
# Output will show:
# 🔄 RETRY INSTRUCTIONS:
#    Failed URLs have been saved to: logs/failed_urls_swiftui_20250723_123008.json
#    
#    To retry only the failed URLs, run:
#    ./run_ingestion.sh --source swiftui --retry logs/failed_urls_swiftui_20250723_123008.json

# 3. List available failed files
make list-failed-files

# 4. Retry the failed URLs
make retry-swiftui FAILED_FILE=logs/failed_urls_swiftui_20250723_123008.json

# 5. If some URLs still fail, they'll be saved to a new file for another retry
```

## Available Retry Commands

### Individual Framework Commands
- `make retry-python FAILED_FILE=<path>`
- `make retry-react FAILED_FILE=<path>`
- `make retry-swiftui FAILED_FILE=<path>`
- `make retry-tailwind FAILED_FILE=<path>`
- `make retry-figma FAILED_FILE=<path>`
- `make retry-fastapi FAILED_FILE=<path>`

### Generic Commands
- `make retry SOURCE=<framework> FAILED_FILE=<path>`
- `make list-failed-files`

### Command-Line Script
- `./run_ingestion.sh --source <framework> --retry <failed_file> [--test]`

## Benefits

### 1. **Efficiency**
- Only processes URLs that actually failed
- No need to re-process successful URLs
- Saves time and resources

### 2. **Reliability**
- Detailed error tracking for debugging
- Automatic file generation with timestamps
- Comprehensive retry statistics

### 3. **Flexibility**
- Test mode for limited retries
- Framework-specific retry commands
- Support for multiple retry attempts

### 4. **Monitoring**
- Clear retry instructions after each ingestion
- Detailed statistics and progress tracking
- Success/failure reporting for retry attempts

## Example Output

### After Initial Ingestion
```
📊 INGESTION PROGRESS:
   Discovered: 78
   Processed: 78
   Successful: 63 (80.8%)
   Failed: 15
   Skipped (existing): 0
   Elapsed: 245.6s

🔄 RETRY INSTRUCTIONS:
   Failed URLs have been saved to: logs/failed_urls_swiftui_20250723_123008.json
   
   To retry only the failed URLs, run:
   ./run_ingestion.sh --source swiftui --retry logs/failed_urls_swiftui_20250723_123008.json
   
   Or use make commands:
   make retry-swiftui FAILED_FILE=logs/failed_urls_swiftui_20250723_123008.json
```

### During Retry
```
🔄 Starting retry ingestion from: logs/failed_urls_swiftui_20250723_123008.json

📂 Loaded 15 failed URLs from: logs/failed_urls_swiftui_20250723_123008.json

📊 ORIGINAL INGESTION STATS:
   Framework: swiftui
   Total Processed: 78
   Failed: 15
   Success Rate: 80.8%
   Original Date: 2025-07-23T12:30:08.123456

🎯 Retrying 15 failed URLs for swiftui
```

### After Retry
```
🎯 RETRY INGESTION COMPLETED:
   URLs Attempted: 15
   Successful: 12
   Failed: 3
   Success Rate: 80.0%
   Total Time: 45.2s

🔄 RETRY INGESTION SUMMARY:
📚 SWIFTUI RETRY:
   URLs Attempted: 15
   Successful: 12 (80.0%)
   Still Failed: 3
   Time: 45.2s

💾 New failures saved to: logs/failed_urls_swiftui_20250723_134523.json
```

## File Management

### Failed URL Files Location
All failed URL files are stored in the `logs/` directory with the naming pattern:
```
logs/failed_urls_<framework>_<timestamp>.json
```

### Cleanup
Failed URL files are automatically managed by the log cleanup system:
```bash
# Clean old log files (keeps last 10)
make clean-logs
```

## Integration with Weekly Updates

The retry functionality integrates seamlessly with weekly updates:

```bash
# Weekly update with automatic retry capability
make weekly-update

# Any failures during weekly updates are automatically saved for retry
# Check logs/weekly_update_*.json for details
```

## Best Practices

1. **Monitor Initial Ingestion**: Always check for failed URLs after ingestion
2. **Retry Soon**: Retry failed URLs while the issues are fresh
3. **Use Test Mode**: Test retries with `--test` flag for large failure sets
4. **Check Error Messages**: Review error details in failed URL files for debugging
5. **Multiple Retries**: Some URLs may succeed on second or third attempts
6. **Resource Management**: Use retry functionality during off-peak hours for large sets

This retry functionality ensures that temporary network issues, timeouts, or other transient problems don't result in permanently missing documentation content.