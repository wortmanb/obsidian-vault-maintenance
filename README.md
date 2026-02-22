# Obsidian Vault Maintenance System

Comprehensive CLI tool for maintaining and organizing Obsidian vaults with automated health checks, issue detection, and maintenance operations.

## Features

### 🔍 Vault Analysis
- **Comprehensive scanning** of vault structure and content
- **File statistics** (count, size, word count, recent activity)
- **Link analysis** (internal links, backlinks, broken links)
- **Tag analysis** (usage patterns, hierarchy, similar tags)
- **Property analysis** (frontmatter consistency, missing properties)
- **Content analysis** (duplicates, orphans, organization suggestions)

### 🔧 Automated Fixes
- **Broken link repair** with intelligent suggestions
- **Tag normalization** and similar tag merging
- **Property standardization** and missing property addition
- **Interactive and dry-run modes** for safe operation
- **Batch operations** with confirmation prompts

### 📊 Health Reports
- **Terminal output** with color-coded status indicators
- **Markdown reports** for documentation and sharing
- **JSON export** for programmatic integration
- **Detailed statistics** and actionable insights
- **Quick wins** identification for immediate improvements

### 📁 Organization Tools
- **File organization suggestions** by date, topic, or type
- **Flat structure detection** and folder recommendations
- **Tag-based organization** with automatic folder suggestions
- **Daily note detection** and Journal folder recommendations
- **Duplicate detection** with merge suggestions

## Installation

```bash
cd ~/git/obsidian-vault-maintenance
chmod +x vault_maintenance.py
ln -sf $(pwd)/vault_maintenance.py ~/bin/vault-maintenance
```

## Usage

### Quick Health Check
```bash
vault-maintenance scan
```

### Detailed Analysis with Report
```bash
vault-maintenance scan --format markdown --save-to vault-report.md
```

### Fix Issues Interactively
```bash
vault-maintenance fix --interactive
```

### Dry-run Fixes (Preview Only)
```bash
vault-maintenance fix --dry-run
```

### Tag Management
```bash
vault-maintenance tags --normalize --merge-similar
```

### Property Management
```bash
vault-maintenance properties --standardize --add-missing
```

### File Organization
```bash
vault-maintenance organize --suggest-only
vault-maintenance organize --by date
vault-maintenance organize --by topic
```

### JSON Export for Scripting
```bash
vault-maintenance scan --format json > vault-data.json
```

## Commands

### `scan` - Analyze Vault Structure
Performs comprehensive vault analysis and generates reports.

**Options:**
- `--format {terminal|markdown|json}` - Output format (default: terminal)
- `--save-to FILE` - Save report to file
- `--vault PATH` - Specify vault path (default: ~/vaults/Wrap Buddies Vault)

**Example:**
```bash
vault-maintenance scan --format markdown --save-to ~/vault-health-report.md
```

### `fix` - Repair Issues
Automatically fixes detected issues with safety controls.

**Options:**
- `--dry-run` - Show what would be fixed without making changes
- `--interactive` - Ask for confirmation before each fix
- `--vault PATH` - Specify vault path

**Example:**
```bash
vault-maintenance fix --interactive --dry-run
```

### `tags` - Tag Management
Manages tag normalization and cleanup operations.

**Options:**
- `--normalize` - Normalize tag formatting (case, spacing)
- `--merge-similar` - Merge tags with high similarity scores
- `--vault PATH` - Specify vault path

**Example:**
```bash
vault-maintenance tags --normalize --merge-similar
```

### `properties` - Property Management
Manages frontmatter properties across the vault.

**Options:**
- `--standardize` - Standardize property naming conventions
- `--add-missing` - Add common missing properties to files
- `--vault PATH` - Specify vault path

### `report` - Generate Maintenance Report
Generates comprehensive maintenance reports.

**Options:**
- `--save-to FILE` - Save report to file (default: print to stdout)
- `--vault PATH` - Specify vault path

### `organize` - File Organization
Provides file organization suggestions and operations.

**Options:**
- `--suggest-only` - Only show suggestions without moving files
- `--by {date|topic|type}` - Organization strategy
- `--vault PATH` - Specify vault path

**Example:**
```bash
vault-maintenance organize --suggest-only
vault-maintenance organize --by date
```

## Configuration

### Default Vault Path
Default: `~/vaults/Wrap Buddies Vault`

Override with `--vault PATH` or set environment variable:
```bash
export OBSIDIAN_VAULT_PATH="~/my-vault"
```

### Ignored Folders
The following folders are automatically excluded from analysis:
- `.obsidian` (Obsidian metadata)
- `.trash` (Obsidian trash)
- `.git` (Git repository)
- `node_modules` (Node.js dependencies)
- `__pycache__` (Python cache)

### Supported File Types
- `.md` - Markdown files (primary)
- `.txt` - Text files  
- `.canvas` - Obsidian canvas files

## Analysis Features

### Orphan Detection
Identifies files with no incoming links that might be forgotten or need better linking.

**Exclusions:**
- Index files (index, readme, home)
- Files with special naming patterns

### Broken Link Detection
Finds links pointing to non-existent files with intelligent repair suggestions.

**Features:**
- **Fuzzy matching** for similar filenames
- **Case-insensitive matching** for common typos
- **Extension handling** (links with/without .md)
- **Multiple suggestion ranking** by similarity score

### Tag Analysis
Comprehensive tag usage analysis and cleanup suggestions.

**Features:**
- **Usage frequency** statistics
- **Similar tag detection** (80%+ similarity)
- **Tag hierarchy analysis** (slash-separated tags)
- **Rare tag identification** (single-use tags)
- **Tag normalization** suggestions

### Property Analysis
Frontmatter property consistency and standardization.

**Features:**
- **Property usage statistics** across files
- **Similar property detection** (typos, variations)
- **Missing property identification** (common properties)
- **Value consistency analysis** within properties

### Duplicate Detection
Identifies potential duplicate content by title similarity.

**Features:**
- **Normalized title matching** (case, punctuation insensitive)
- **Size and modification date comparison**
- **Grouped duplicate display** with file details

### Organization Suggestions
Intelligent file organization recommendations.

**Strategies:**
- **Date-based:** Groups daily notes and dated files
- **Topic-based:** Groups by tag frequency (3+ files per tag)
- **Type-based:** Groups by file type and content patterns
- **Flat structure detection:** Warns about too many root files

## Output Formats

### Terminal (Default)
Color-coded terminal output with visual indicators:
- 🟢 Green: Healthy/successful items
- 🟡 Yellow: Warnings and suggestions  
- 🔴 Red: Errors and issues
- 🔵 Blue: Informational items
- **Bold**: Section headers and important items

### Markdown
Well-formatted Markdown reports suitable for:
- Documentation and sharing
- Integration with other Obsidian notes
- Version control and tracking changes
- Team collaboration and reviews

### JSON
Structured data export for:
- Programmatic integration
- Custom analysis scripts
- Data processing pipelines
- Integration with other tools

## Safety Features

### Dry-run Mode
Preview all changes before applying:
```bash
vault-maintenance fix --dry-run
```

### Interactive Mode
Confirm each change individually:
```bash
vault-maintenance fix --interactive
```

### Non-destructive Operations
- Analysis operations never modify files
- All fixes create backups before changes
- Graceful error handling prevents data loss
- Comprehensive logging of all operations

## Integration Examples

### Daily Maintenance Script
```bash
#!/bin/bash
# Daily vault maintenance
vault-maintenance scan --format markdown --save-to ~/vault-reports/$(date +%Y-%m-%d).md
vault-maintenance fix --dry-run > ~/vault-reports/suggested-fixes-$(date +%Y-%m-%d).txt
```

### Weekly Cleanup
```bash
#!/bin/bash
# Weekly comprehensive maintenance
vault-maintenance scan
vault-maintenance tags --normalize
vault-maintenance properties --add-missing --interactive
vault-maintenance organize --suggest-only
```

### CI/CD Integration
```bash
#!/bin/bash
# Automated vault health checks
vault-maintenance scan --format json > vault-health.json

# Check for issues
if vault-maintenance scan --format json | jq -e '.broken_links | length > 0'; then
  echo "❌ Broken links detected"
  exit 1
fi

echo "✅ Vault health check passed"
```

## Use Cases

### Personal Knowledge Management
- **Daily maintenance** with automated health checks
- **Weekly organization** with tag and property cleanup
- **Monthly reviews** with comprehensive reporting
- **Continuous improvement** with trend analysis

### Team Collaboration
- **Shared vault maintenance** with consistent standards
- **Onboarding support** with organization guidance
- **Quality assurance** with automated checks
- **Documentation standards** with property enforcement

### Content Creation Workflows
- **Writing process optimization** with link health
- **Research organization** with tag-based grouping
- **Publication preparation** with duplicate detection
- **Archive maintenance** with orphan identification

## Requirements

- **Python 3.8+** (no external dependencies)
- **Obsidian vault** with standard markdown files
- **Read/write access** to vault directory
- **Terminal with color support** (optional, but recommended)

## Technical Details

### Performance
- **Parallel processing** for large vaults (1000+ files)
- **Memory efficient** streaming for content analysis
- **Incremental scanning** with modification time checks
- **Optimized algorithms** for link and tag analysis

### File Handling
- **UTF-8 encoding** support with fallback handling
- **Cross-platform** path handling (Windows/Mac/Linux)
- **Symlink awareness** with recursive loop prevention
- **Large file handling** with size and timeout limits

### Error Handling
- **Graceful degradation** when files are inaccessible
- **Comprehensive logging** with detailed error context
- **Recovery suggestions** for common issues
- **Safe failure modes** that preserve data integrity

## Contributing

### Development Setup
```bash
cd ~/git/obsidian-vault-maintenance
python3 -m venv venv
source venv/bin/activate
pip install -e .
```

### Testing
```bash
python3 -m pytest tests/
python3 vault_maintenance.py scan --vault test-vault
```

### Code Style
- **PEP 8** compliance
- **Type hints** for all functions
- **Comprehensive docstrings** 
- **Error handling** for all operations

## License

MIT License - feel free to use, modify, and distribute.

## Version History

- **v1.0** (Build #22): Initial release with comprehensive vault analysis and maintenance features
  - Complete vault scanning and health analysis
  - Broken link detection and repair
  - Tag analysis and organization
  - Property management and standardization  
  - File organization suggestions
  - Multi-format reporting (terminal/markdown/json)
  - Interactive and dry-run safety modes