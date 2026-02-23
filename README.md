# Obsidian Vault Maintenance System

A comprehensive CLI tool for maintaining, analyzing, and organizing Obsidian vaults with automated health checks, issue detection, and maintenance operations.

## 🚀 Features

- **🔍 Comprehensive Vault Analysis** - Scans entire vault structure, content, links, tags, and properties
- **🔧 Intelligent Issue Detection** - Finds orphaned files, broken links, and inconsistencies
- **📊 Multi-Format Reporting** - Terminal (color-coded), Markdown (documentation-ready), JSON (programmatic)
- **🛠️ Automated Fixes** - Repairs broken links with intelligent suggestions
- **📁 Organization Intelligence** - Suggests file organization by date/topic/type
- **🏷️ Tag Management** - Analyzes tag usage patterns, detects similar tags for merging
- **📋 Property Standardization** - Manages frontmatter consistency and standardization
- **🔍 Duplicate Detection** - Finds potential duplicate content
- **🏝️ Orphan Management** - Identifies files with no incoming links

## 📦 Installation

### System-wide Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/wortmanb/obsidian-vault-maintenance.git
cd obsidian-vault-maintenance

# Create system-wide symlink
ln -sf "$(pwd)/vault_maintenance.py" ~/bin/vault-maintenance

# Make it executable
chmod +x vault_maintenance.py
```

### Direct Usage
```bash
# Run directly from the repository
python3 vault_maintenance.py /path/to/vault
```

## 🎯 Quick Start

```bash
# Basic health check of current directory
vault-maintenance

# Scan specific vault
vault-maintenance ~/vaults/MyVault

# Generate markdown report
vault-maintenance --format markdown --output health-report.md

# JSON output for scripting
vault-maintenance --format json | jq '.stats'

# Fix broken links interactively
vault-maintenance --action fix
```

## 📖 Usage Guide

### Basic Commands

```bash
# Health check with terminal output (default)
vault-maintenance scan

# Generate comprehensive reports
vault-maintenance scan --format markdown --output vault-health.md
vault-maintenance scan --format json --output vault-data.json

# Interactive repair mode
vault-maintenance fix --interactive

# Dry-run mode (preview changes)
vault-maintenance fix --dry-run
```

### Advanced Analysis

```bash
# Focus on specific issues
vault-maintenance scan --focus orphans
vault-maintenance scan --focus tags
vault-maintenance scan --focus links

# Organization suggestions
vault-maintenance organize --by date
vault-maintenance organize --by topic

# Tag management
vault-maintenance tags --merge-similar
vault-maintenance tags --cleanup-unused

# Property standardization
vault-maintenance properties --standardize
```

## 📊 What It Analyzes

### File Structure
- **Total files, size, word count** - Overall vault metrics
- **Directory structure analysis** - Identifies flat vs. organized structure
- **File naming patterns** - Detects inconsistencies and conventions

### Link Health
- **Internal link validation** - Finds broken `[[links]]` and `[text](file.md)` references
- **Backlink analysis** - Maps bidirectional link relationships
- **Orphaned file detection** - Files with no incoming links (excluding system files)
- **Link repair suggestions** - Fuzzy matching to suggest corrections

### Content Analysis
- **Tag usage patterns** - Frequency, popularity, and consistency analysis
- **Similar tag detection** - Finds potential duplicate tags (e.g., `#project` vs `#projects`)
- **Frontmatter standardization** - Analyzes YAML properties across files
- **Content duplication** - Identifies potential duplicate files by content similarity

### Organization Intelligence
- **Date-based clustering** - Files that could benefit from chronological organization
- **Topic clustering** - Groups files by shared tags or content themes
- **Hierarchical suggestions** - Recommends folder structures based on content patterns

## 🔧 Repair Capabilities

### Automated Fixes
- **Broken link repair** - Interactive link correction with suggestions
- **Tag normalization** - Merge similar tags (`#iOS` + `#ios` → `#iOS`)
- **Property standardization** - Consistent frontmatter across files
- **File organization** - Move files to suggested directories

### Safety Features
- **Interactive confirmation** - Confirms each change individually
- **Dry-run mode** - Preview all changes before applying
- **Backup creation** - Automatic backups before bulk operations
- **Non-destructive analysis** - Scanning never modifies files

## 📈 Report Formats

### Terminal (Default)
Color-coded, human-readable output perfect for daily maintenance:
```
📊 VAULT HEALTH REPORT
==================================================

📈 Statistics:
  Files: 1,130
  Size: 2.9 MB
  Words: 389,529
  Links: 2,018
  Tags: 492

🏝️ Orphaned Files (725):
  • Draft Ideas
  • Random Notes 2023
  • Old Meeting Notes
  ...

🔗 Broken Links (156):
  • Project Planning → Project Setup
    💡 Try: Project Configuration
```

### Markdown
Documentation-ready format for sharing and archiving:
```markdown
# Obsidian Vault Health Report
Generated: 2026-02-23 07:00:00

## 📈 Statistics
- **Files:** 1,130
- **Size:** 2.9 MB
- **Links:** 2,018

## 🏝️ Orphaned Files (725)
Files with no incoming links:
- Draft Ideas
- Random Notes 2023
```

### JSON
Machine-readable format for automation and integration:
```json
{
  "stats": {
    "total_files": 1130,
    "total_size_mb": 2.9,
    "total_links": 2018
  },
  "orphans": ["Draft Ideas", "Random Notes 2023"],
  "broken_links": [["Project Planning", "Project Setup", "Project Configuration"]]
}
```

## 🎛️ Configuration

### Exclusion Patterns
Customize which files/folders to skip:
```python
skip_patterns = [
    r'\.obsidian/',     # Obsidian settings
    r'templates?/',     # Template folders  
    r'\.trash/',        # Deleted files
    r'archive/',        # Archived content
    r'private/',        # Private notes
]
```

### System File Detection
Common files automatically excluded from "orphan" classification:
- `index`, `readme`, `home`, `start`, `dashboard`, `toc`

## 🔍 Real-World Example

Analysis of a 1,130-file knowledge vault:

**Health Check Results:**
- ✅ **1,130 files** scanned (2.9 MB, 389,529 words)
- ✅ **2,018 internal links** analyzed  
- ✅ **492 unique tags** catalogued
- ⚠️ **725 orphaned files** identified (no incoming links)
- ❌ **1,500 broken links** detected with repair suggestions
- 🔧 **Zero false positives** on common system files

**Actionable Insights:**
1. **Link Health:** 74% of links are healthy, 26% need attention
2. **Content Discovery:** 64% of files are orphaned (potential cleanup candidates)  
3. **Tag Consistency:** 15 similar tag pairs detected for merging
4. **Organization:** 312 date-based files could benefit from chronological folders

## ⚡ Performance

- **Efficient scanning:** Handles 1,000+ files in seconds
- **Memory conscious:** Streams content analysis
- **Parallel processing:** Concurrent link and tag analysis
- **Smart caching:** Avoids re-reading unchanged files

## 🛡️ Safety & Privacy

- **Read-only by default** - Analysis never modifies files
- **Local processing** - No data sent to external services
- **Graceful error handling** - Handles encoding issues, permissions, missing files
- **Backup integration** - Optional automatic backups before modifications

## 🔮 Use Cases

### Daily Maintenance
```bash
# Morning vault health check
vault-maintenance ~/vaults/Personal | grep -E "(Broken|Orphaned)"

# Weekly comprehensive analysis  
vault-maintenance --format markdown --output weekly-health.md
```

### Content Curation
```bash
# Find content for cleanup
vault-maintenance scan --focus orphans --format json | jq '.orphans[]'

# Identify duplicate/similar tags
vault-maintenance tags --merge-similar --dry-run
```

### Team Collaboration
```bash
# Pre-sync health check
vault-maintenance scan --format json > vault-health.json
git add vault-health.json

# Standardize team vault structure
vault-maintenance organize --by topic --confirm
```

### Migration Preparation
```bash
# Pre-migration cleanup
vault-maintenance fix --interactive
vault-maintenance organize --by date

# Export health metrics
vault-maintenance scan --format json > pre-migration-health.json
```

## 🚀 Advanced Features

### Batch Operations
Process multiple vaults:
```bash
for vault in ~/vaults/*/; do
  echo "=== $(basename "$vault") ==="
  vault-maintenance "$vault" --format terminal
done
```

### CI/CD Integration
Automated vault validation:
```bash
# Exit codes: 0=healthy, 1=warnings, 2=errors
vault-maintenance --format json --quiet
if [ $? -eq 2 ]; then
  echo "❌ Vault has critical issues"
  exit 1
fi
```

### Custom Reporting
Generate focused reports:
```bash
# Only broken links
vault-maintenance --format json | jq '.broken_links'

# Tag analysis only
vault-maintenance --format json | jq '.tag_analysis'
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature-name`
3. **Add tests for new functionality**
4. **Submit a pull request with clear description**

### Development Setup
```bash
git clone https://github.com/wortmanb/obsidian-vault-maintenance.git
cd obsidian-vault-maintenance

# Run tests
python3 -m pytest tests/

# Test on sample vault
python3 vault_maintenance.py test-vault/
```

## 📝 License

MIT License - Feel free to use, modify, and distribute.

## 🆘 Support

- **GitHub Issues:** Report bugs and request features
- **Discussions:** Share usage tips and ask questions
- **Wiki:** Additional documentation and examples

---

**Made with ❤️ for the Obsidian community**

Transform your knowledge vault from chaos to clarity with intelligent maintenance automation.