#!/usr/bin/env python3
"""
Obsidian Vault Maintenance System

Comprehensive CLI tool for maintaining Obsidian vaults:
- Orphan detection (files with no incoming links)  
- Broken link detection and repair
- Tag cleanup and normalization
- Property/frontmatter standardization
- File organization suggestions
- Duplicate content detection
- Health reports with actionable insights

Usage:
    vault-maintenance scan [--vault PATH] [--format json|markdown|terminal]
    vault-maintenance fix [--vault PATH] [--dry-run] [--interactive]
    vault-maintenance tags [--normalize] [--merge-similar]
    vault-maintenance properties [--standardize] [--add-missing]
    vault-maintenance report [--save-to FILE]
    vault-maintenance organize [--suggest-only] [--by date|topic|type]
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict, Counter
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional, Any
import difflib

# Configuration
DEFAULT_VAULT_PATH = Path.home() / "Wrap Buddies Vault"
SUPPORTED_EXTENSIONS = {'.md', '.txt', '.canvas'}
IGNORE_FOLDERS = {'.obsidian', '.trash', '.git', 'node_modules', '__pycache__'}
DATE_FORMATS = ['%Y-%m-%d', '%Y%m%d', '%B %d, %Y', '%d %B %Y']

# Color codes for terminal output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

class VaultAnalyzer:
    """Analyzes Obsidian vault structure and content."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.files: Dict[str, Dict] = {}
        self.links: Dict[str, Set[str]] = defaultdict(set)
        self.backlinks: Dict[str, Set[str]] = defaultdict(set)
        self.tags: Dict[str, Set[str]] = defaultdict(set)
        self.properties: Dict[str, Dict] = {}
        
    def scan_vault(self) -> Dict[str, Any]:
        """Comprehensive vault scan returning analysis results."""
        print(f"🔍 Scanning vault: {self.vault_path}")
        
        # Collect all files
        self._collect_files()
        
        # Analyze content
        for file_path, file_info in self.files.items():
            self._analyze_file(file_path, file_info)
            
        # Generate insights
        results = {
            'timestamp': datetime.now().isoformat(),
            'vault_path': str(self.vault_path),
            'summary': self._generate_summary(),
            'orphans': self._find_orphans(),
            'broken_links': self._find_broken_links(),
            'tag_analysis': self._analyze_tags(),
            'property_analysis': self._analyze_properties(),
            'duplicates': self._find_duplicates(),
            'organization_suggestions': self._suggest_organization()
        }
        
        return results
        
    def _collect_files(self):
        """Collect all supported files in the vault."""
        for root, dirs, files in os.walk(self.vault_path):
            # Skip ignored folders
            dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in SUPPORTED_EXTENSIONS:
                    rel_path = str(file_path.relative_to(self.vault_path))
                    
                    self.files[rel_path] = {
                        'name': file_path.stem,
                        'full_path': file_path,
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime),
                        'extension': file_path.suffix
                    }
                    
    def _analyze_file(self, rel_path: str, file_info: Dict):
        """Analyze individual file for links, tags, and properties."""
        try:
            content = file_info['full_path'].read_text(encoding='utf-8')
            file_info['content'] = content
            file_info['word_count'] = len(content.split())
            
            # Extract frontmatter properties
            properties = self._extract_frontmatter(content)
            if properties:
                self.properties[rel_path] = properties
                
            # Extract wikilinks [[link]]
            wikilinks = re.findall(r'\[\[([^\]]+)\]\]', content)
            for link in wikilinks:
                # Handle link with alias [[link|alias]]
                link_target = link.split('|')[0].strip()
                self.links[rel_path].add(link_target)
                self.backlinks[link_target].add(rel_path)
                
            # Extract markdown links [text](link)  
            md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            for text, link in md_links:
                if not link.startswith('http'):  # Internal links only
                    self.links[rel_path].add(link)
                    self.backlinks[link].add(rel_path)
                    
            # Extract tags #tag
            tags = re.findall(r'#([a-zA-Z0-9_/-]+)', content)
            for tag in tags:
                self.tags[tag].add(rel_path)
                
        except UnicodeDecodeError:
            file_info['error'] = 'Cannot read file (encoding issue)'
        except Exception as e:
            file_info['error'] = str(e)
            
    def _extract_frontmatter(self, content: str) -> Optional[Dict]:
        """Extract YAML frontmatter from file."""
        if not content.startswith('---'):
            return None
            
        try:
            end_marker = content.find('\n---\n', 3)
            if end_marker == -1:
                return None
                
            frontmatter = content[3:end_marker]
            
            # Simple YAML parsing (basic key: value pairs)
            properties = {}
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    properties[key.strip()] = value.strip()
                    
            return properties
        except Exception:
            return None
            
    def _generate_summary(self) -> Dict:
        """Generate vault summary statistics."""
        total_files = len(self.files)
        total_size = sum(f.get('size', 0) for f in self.files.values())
        total_words = sum(f.get('word_count', 0) for f in self.files.values())
        
        # File type distribution
        extensions = Counter(f['extension'] for f in self.files.values())
        
        # Recent activity (files modified in last 7 days)
        week_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        recent_files = sum(1 for f in self.files.values() 
                          if f.get('modified', datetime.min) >= week_ago)
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'total_words': total_words,
            'file_types': dict(extensions),
            'total_links': sum(len(links) for links in self.links.values()),
            'total_tags': len(self.tags),
            'files_with_properties': len(self.properties),
            'recent_files_7d': recent_files
        }
        
    def _find_orphans(self) -> List[Dict]:
        """Find files with no incoming links."""
        orphans = []
        
        for rel_path, file_info in self.files.items():
            # Skip index files and daily notes (common orphans by design)
            name = file_info['name'].lower()
            if any(skip in name for skip in ['index', 'readme', 'home']):
                continue
                
            # Check if any other file links to this one
            has_backlinks = False
            for link_target in [rel_path, file_info['name'], file_info['name'].replace(' ', '%20')]:
                if link_target in self.backlinks and self.backlinks[link_target]:
                    has_backlinks = True
                    break
                    
            if not has_backlinks:
                orphans.append({
                    'path': rel_path,
                    'name': file_info['name'],
                    'size': file_info['size'],
                    'modified': file_info['modified'].isoformat(),
                    'word_count': file_info.get('word_count', 0)
                })
                
        # Sort by modification date (newest first)
        orphans.sort(key=lambda x: x['modified'], reverse=True)
        return orphans
        
    def _find_broken_links(self) -> List[Dict]:
        """Find links that point to non-existent files."""
        broken = []
        
        for source_file, targets in self.links.items():
            for target in targets:
                # Try to resolve the target
                target_exists = False
                
                # Direct match
                if target in self.files:
                    target_exists = True
                else:
                    # Try with .md extension
                    if f"{target}.md" in self.files:
                        target_exists = True
                    else:
                        # Try fuzzy matching by name
                        for file_path, file_info in self.files.items():
                            if file_info['name'] == target or file_info['name'] == target.replace('%20', ' '):
                                target_exists = True
                                break
                                
                if not target_exists:
                    broken.append({
                        'source': source_file,
                        'target': target,
                        'suggestions': self._suggest_link_fixes(target)
                    })
                    
        return broken
        
    def _suggest_link_fixes(self, broken_target: str) -> List[str]:
        """Suggest possible fixes for broken links."""
        suggestions = []
        
        # Get all file names for fuzzy matching
        file_names = [info['name'] for info in self.files.values()]
        
        # Find close matches
        matches = difflib.get_close_matches(broken_target, file_names, n=3, cutoff=0.6)
        suggestions.extend(matches)
        
        # Try case-insensitive matching
        lower_target = broken_target.lower()
        for name in file_names:
            if name.lower() == lower_target and name not in suggestions:
                suggestions.append(name)
                
        return suggestions
        
    def _analyze_tags(self) -> Dict:
        """Analyze tag usage and suggest improvements."""
        tag_stats = {}
        
        for tag, files in self.tags.items():
            tag_stats[tag] = {
                'count': len(files),
                'files': list(files)
            }
            
        # Find similar tags that could be merged
        similar_pairs = []
        tag_list = list(self.tags.keys())
        for i, tag1 in enumerate(tag_list):
            for tag2 in tag_list[i+1:]:
                similarity = difflib.SequenceMatcher(None, tag1.lower(), tag2.lower()).ratio()
                if similarity > 0.8:  # 80% similarity
                    similar_pairs.append((tag1, tag2, similarity))
                    
        # Sort by frequency (most used first)
        sorted_tags = sorted(tag_stats.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            'total_tags': len(self.tags),
            'tag_usage': dict(sorted_tags[:20]),  # Top 20 tags
            'similar_tags': similar_pairs,
            'rare_tags': [tag for tag, info in tag_stats.items() if info['count'] == 1],
            'tag_hierarchy': self._analyze_tag_hierarchy()
        }
        
    def _analyze_tag_hierarchy(self) -> Dict:
        """Analyze tag hierarchy (tags with slashes)."""
        hierarchy = defaultdict(list)
        
        for tag in self.tags.keys():
            if '/' in tag:
                parts = tag.split('/')
                parent = parts[0]
                hierarchy[parent].append(tag)
                
        return dict(hierarchy)
        
    def _analyze_properties(self) -> Dict:
        """Analyze frontmatter properties."""
        if not self.properties:
            return {'total_files_with_properties': 0}
            
        # Property usage stats
        property_counts = defaultdict(int)
        property_values = defaultdict(set)
        
        for file_path, props in self.properties.items():
            for key, value in props.items():
                property_counts[key] += 1
                property_values[key].add(value)
                
        # Common properties
        common_props = dict(sorted(property_counts.items(), 
                                 key=lambda x: x[1], reverse=True))
        
        # Inconsistent property names (similar but different)
        similar_properties = []
        prop_list = list(property_counts.keys())
        for i, prop1 in enumerate(prop_list):
            for prop2 in prop_list[i+1:]:
                similarity = difflib.SequenceMatcher(None, prop1.lower(), prop2.lower()).ratio()
                if similarity > 0.8:
                    similar_properties.append((prop1, prop2, similarity))
                    
        return {
            'total_files_with_properties': len(self.properties),
            'property_usage': common_props,
            'property_values': {k: list(v) for k, v in property_values.items()},
            'similar_properties': similar_properties,
            'files_missing_common_properties': self._find_missing_properties()
        }
        
    def _find_missing_properties(self) -> List[Dict]:
        """Find files missing common properties."""
        # Define common properties that should be on most files
        common_props = ['tags', 'created', 'modified', 'type']
        missing = []
        
        for file_path, file_info in self.files.items():
            props = self.properties.get(file_path, {})
            missing_props = [prop for prop in common_props if prop not in props]
            
            if missing_props:
                missing.append({
                    'file': file_path,
                    'missing': missing_props
                })
                
        return missing
        
    def _find_duplicates(self) -> List[Dict]:
        """Find potential duplicate content."""
        # Group by similar titles
        title_groups = defaultdict(list)
        
        for file_path, file_info in self.files.items():
            # Normalize title for comparison
            normalized = re.sub(r'[^a-zA-Z0-9]', '', file_info['name'].lower())
            title_groups[normalized].append({
                'path': file_path,
                'name': file_info['name'],
                'size': file_info['size'],
                'modified': file_info['modified'].isoformat()
            })
            
        # Find groups with multiple files
        duplicates = []
        for normalized, files in title_groups.items():
            if len(files) > 1:
                duplicates.append({
                    'normalized_title': normalized,
                    'files': files,
                    'count': len(files)
                })
                
        return sorted(duplicates, key=lambda x: x['count'], reverse=True)
        
    def _suggest_organization(self) -> Dict:
        """Suggest file organization improvements."""
        suggestions = {
            'by_date': [],
            'by_topic': [],
            'by_type': [],
            'flat_structure_warning': []
        }
        
        # Analyze current structure
        depth_distribution = defaultdict(int)
        for file_path in self.files.keys():
            depth = len(Path(file_path).parts) - 1  # Subtract 1 for the file itself
            depth_distribution[depth] += 1
            
        # If too many files are in root, suggest organization
        root_files = depth_distribution.get(0, 0)
        if root_files > 10:
            suggestions['flat_structure_warning'] = {
                'files_in_root': root_files,
                'recommendation': 'Consider organizing files into folders'
            }
            
        # Suggest date-based organization for daily notes
        for file_path, file_info in self.files.items():
            if self._looks_like_date(file_info['name']):
                suggestions['by_date'].append(file_path)
                
        # Suggest topic-based organization by tag frequency
        tag_file_mapping = {}
        for tag, files in self.tags.items():
            if len(files) >= 3:  # Tags with 3+ files could be folders
                tag_file_mapping[tag] = list(files)
                
        suggestions['by_topic'] = tag_file_mapping
        
        return suggestions
        
    def _looks_like_date(self, filename: str) -> bool:
        """Check if filename looks like a date."""
        for date_format in DATE_FORMATS:
            try:
                datetime.strptime(filename, date_format)
                return True
            except ValueError:
                continue
        return bool(re.match(r'\d{4}-\d{2}-\d{2}', filename))

class VaultMaintenanceCLI:
    """CLI interface for vault maintenance operations."""
    
    def __init__(self):
        self.analyzer = None
        
    def main(self):
        """Main CLI entry point."""
        parser = argparse.ArgumentParser(
            description="Obsidian Vault Maintenance System",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=__doc__
        )
        
        parser.add_argument('--vault', type=Path, default=DEFAULT_VAULT_PATH,
                          help=f'Vault path (default: {DEFAULT_VAULT_PATH})')
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Scan command
        scan_parser = subparsers.add_parser('scan', help='Scan vault and analyze structure')
        scan_parser.add_argument('--format', choices=['json', 'markdown', 'terminal'], 
                               default='terminal', help='Output format')
        scan_parser.add_argument('--save-to', type=Path, help='Save report to file')
        
        # Fix command
        fix_parser = subparsers.add_parser('fix', help='Fix detected issues')
        fix_parser.add_argument('--dry-run', action='store_true', 
                              help='Show what would be fixed without making changes')
        fix_parser.add_argument('--interactive', action='store_true',
                              help='Ask for confirmation before each fix')
        
        # Tags command  
        tags_parser = subparsers.add_parser('tags', help='Tag management')
        tags_parser.add_argument('--normalize', action='store_true',
                               help='Normalize tag formatting')
        tags_parser.add_argument('--merge-similar', action='store_true',
                               help='Merge similar tags')
        
        # Properties command
        props_parser = subparsers.add_parser('properties', help='Property management')
        props_parser.add_argument('--standardize', action='store_true',
                                help='Standardize property names')
        props_parser.add_argument('--add-missing', action='store_true',
                                help='Add missing common properties')
        
        # Report command
        report_parser = subparsers.add_parser('report', help='Generate maintenance report')
        report_parser.add_argument('--save-to', type=Path, help='Save report to file')
        
        # Organize command
        organize_parser = subparsers.add_parser('organize', help='File organization')
        organize_parser.add_argument('--suggest-only', action='store_true',
                                   help='Only suggest organization, don\'t move files')
        organize_parser.add_argument('--by', choices=['date', 'topic', 'type'],
                                   help='Organization strategy')
        
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            return
            
        # Initialize analyzer
        if not args.vault.exists():
            print(f"{Colors.RED}Error: Vault path does not exist: {args.vault}{Colors.END}")
            sys.exit(1)
            
        self.analyzer = VaultAnalyzer(args.vault)
        
        # Execute command
        try:
            if args.command == 'scan':
                self.cmd_scan(args)
            elif args.command == 'fix':
                self.cmd_fix(args)
            elif args.command == 'tags':
                self.cmd_tags(args)
            elif args.command == 'properties':
                self.cmd_properties(args)
            elif args.command == 'report':
                self.cmd_report(args)
            elif args.command == 'organize':
                self.cmd_organize(args)
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.END}")
            sys.exit(1)
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.END}")
            sys.exit(1)
            
    def cmd_scan(self, args):
        """Scan vault command."""
        results = self.analyzer.scan_vault()
        
        if args.format == 'json':
            output = json.dumps(results, indent=2, default=str)
        elif args.format == 'markdown':
            output = self._format_markdown_report(results)
        else:
            output = self._format_terminal_report(results)
            
        if args.save_to:
            args.save_to.write_text(output)
            print(f"{Colors.GREEN}Report saved to {args.save_to}{Colors.END}")
        else:
            print(output)
            
    def cmd_fix(self, args):
        """Fix issues command."""
        results = self.analyzer.scan_vault()
        fixes_applied = 0
        
        print(f"{Colors.BLUE}🔧 Starting vault fixes...{Colors.END}")
        
        # Fix broken links
        if results['broken_links']:
            print(f"\n{Colors.YELLOW}📎 Fixing broken links...{Colors.END}")
            for link in results['broken_links']:
                if link['suggestions']:
                    suggested_fix = link['suggestions'][0]
                    
                    if args.interactive:
                        response = input(f"Replace '{link['target']}' with '{suggested_fix}' in {link['source']}? (y/n): ")
                        if response.lower() != 'y':
                            continue
                            
                    if not args.dry_run:
                        self._apply_link_fix(link['source'], link['target'], suggested_fix)
                        fixes_applied += 1
                        print(f"  ✓ Fixed: {link['source']} -> {suggested_fix}")
                    else:
                        print(f"  Would fix: {link['source']} -> {suggested_fix}")
                        
        print(f"\n{Colors.GREEN}✅ Fixes completed: {fixes_applied}{Colors.END}")
        
    def cmd_tags(self, args):
        """Tag management command.""" 
        results = self.analyzer.scan_vault()
        tag_analysis = results['tag_analysis']
        
        if args.normalize:
            print(f"{Colors.BLUE}🏷️  Normalizing tags...{Colors.END}")
            # Implementation for tag normalization
            
        if args.merge_similar:
            print(f"{Colors.BLUE}🔗 Merging similar tags...{Colors.END}")
            for tag1, tag2, similarity in tag_analysis.get('similar_tags', []):
                print(f"  Found similar: '{tag1}' and '{tag2}' ({similarity:.2%})")
                
    def cmd_properties(self, args):
        """Property management command."""
        results = self.analyzer.scan_vault()
        
        if args.standardize:
            print(f"{Colors.BLUE}📋 Standardizing properties...{Colors.END}")
            # Implementation for property standardization
            
        if args.add_missing:
            print(f"{Colors.BLUE}➕ Adding missing properties...{Colors.END}")
            # Implementation for adding missing properties
            
    def cmd_report(self, args):
        """Generate maintenance report."""
        results = self.analyzer.scan_vault()
        report = self._format_markdown_report(results)
        
        if args.save_to:
            args.save_to.write_text(report)
            print(f"{Colors.GREEN}Report saved to {args.save_to}{Colors.END}")
        else:
            print(report)
            
    def cmd_organize(self, args):
        """File organization command."""
        results = self.analyzer.scan_vault()
        suggestions = results['organization_suggestions']
        
        if args.suggest_only or not args.by:
            print(f"{Colors.BLUE}📁 Organization suggestions:{Colors.END}\n")
            
            if suggestions['flat_structure_warning']:
                warning = suggestions['flat_structure_warning']
                print(f"{Colors.YELLOW}⚠️  {warning['files_in_root']} files in root - {warning['recommendation']}{Colors.END}\n")
                
            if suggestions['by_date']:
                print(f"{Colors.CYAN}📅 Date-based files (could go in Journal/ folder):{Colors.END}")
                for file_path in suggestions['by_date'][:10]:  # Show first 10
                    print(f"  • {file_path}")
                if len(suggestions['by_date']) > 10:
                    print(f"  ... and {len(suggestions['by_date']) - 10} more")
                print()
                
            if suggestions['by_topic']:
                print(f"{Colors.CYAN}🏷️  Topic-based organization by tags:{Colors.END}")
                for tag, files in list(suggestions['by_topic'].items())[:5]:
                    print(f"  #{tag} ({len(files)} files)")
                    for file_path in files[:3]:
                        print(f"    • {file_path}")
                    if len(files) > 3:
                        print(f"    ... and {len(files) - 3} more")
                print()
        else:
            print(f"{Colors.BLUE}📁 Organizing files by {args.by}...{Colors.END}")
            # Implementation for actual file moving
            
    def _format_terminal_report(self, results: Dict) -> str:
        """Format results for terminal display."""
        output = []
        summary = results['summary']
        
        # Header
        output.append(f"{Colors.BOLD}{Colors.BLUE}📊 Obsidian Vault Health Report{Colors.END}")
        output.append(f"{Colors.CYAN}Vault: {results['vault_path']}{Colors.END}")
        output.append(f"{Colors.CYAN}Scanned: {results['timestamp']}{Colors.END}\n")
        
        # Summary
        output.append(f"{Colors.BOLD}📋 Summary{Colors.END}")
        output.append(f"  📄 Files: {summary['total_files']:,}")
        output.append(f"  💾 Size: {summary['total_size_mb']:,} MB")
        output.append(f"  📝 Words: {summary['total_words']:,}")
        output.append(f"  🔗 Links: {summary['total_links']:,}")
        output.append(f"  🏷️  Tags: {summary['total_tags']:,}")
        output.append(f"  📋 Files with properties: {summary['files_with_properties']:,}")
        output.append(f"  📅 Recent files (7d): {summary['recent_files_7d']:,}")
        output.append("")
        
        # Issues
        issues_count = len(results['orphans']) + len(results['broken_links'])
        if issues_count > 0:
            output.append(f"{Colors.BOLD}{Colors.YELLOW}⚠️  Issues Found ({issues_count}){Colors.END}")
            
            if results['orphans']:
                output.append(f"{Colors.YELLOW}  🔸 Orphaned files: {len(results['orphans'])}{Colors.END}")
                for orphan in results['orphans'][:5]:  # Show first 5
                    output.append(f"    • {orphan['name']} ({orphan['word_count']} words)")
                if len(results['orphans']) > 5:
                    output.append(f"    ... and {len(results['orphans']) - 5} more")
                    
            if results['broken_links']:
                output.append(f"{Colors.RED}  🔗 Broken links: {len(results['broken_links'])}{Colors.END}")
                for link in results['broken_links'][:5]:
                    suggestions = ", ".join(link['suggestions'][:2]) if link['suggestions'] else "none"
                    output.append(f"    • '{link['target']}' in {link['source']} (suggestions: {suggestions})")
                if len(results['broken_links']) > 5:
                    output.append(f"    ... and {len(results['broken_links']) - 5} more")
        else:
            output.append(f"{Colors.GREEN}✅ No issues found!{Colors.END}")
            
        output.append("")
        
        # Top tags
        tag_analysis = results['tag_analysis']
        if tag_analysis.get('tag_usage'):
            output.append(f"{Colors.BOLD}🏷️  Top Tags{Colors.END}")
            for tag, info in list(tag_analysis['tag_usage'].items())[:10]:
                output.append(f"  #{tag}: {info['count']} files")
            output.append("")
            
        # Quick wins
        output.append(f"{Colors.BOLD}💡 Quick Wins{Colors.END}")
        if results['duplicates']:
            output.append(f"  📑 Review {len(results['duplicates'])} potential duplicates")
        if tag_analysis.get('similar_tags'):
            output.append(f"  🔗 Merge {len(tag_analysis['similar_tags'])} similar tag pairs")
        if tag_analysis.get('rare_tags'):
            output.append(f"  🏷️  Review {len(tag_analysis['rare_tags'])} single-use tags")
            
        return "\n".join(output)
        
    def _format_markdown_report(self, results: Dict) -> str:
        """Format results as Markdown report."""
        output = []
        summary = results['summary']
        
        # Header
        output.append("# Obsidian Vault Health Report")
        output.append(f"**Vault:** `{results['vault_path']}`")
        output.append(f"**Generated:** {results['timestamp']}")
        output.append("")
        
        # Summary
        output.append("## 📊 Summary")
        output.append("")
        output.append("| Metric | Count |")
        output.append("|--------|-------|")
        output.append(f"| 📄 Files | {summary['total_files']:,} |")
        output.append(f"| 💾 Size | {summary['total_size_mb']:,} MB |")
        output.append(f"| 📝 Words | {summary['total_words']:,} |")
        output.append(f"| 🔗 Links | {summary['total_links']:,} |")
        output.append(f"| 🏷️ Tags | {summary['total_tags']:,} |")
        output.append(f"| 📋 Files with properties | {summary['files_with_properties']:,} |")
        output.append(f"| 📅 Recent files (7d) | {summary['recent_files_7d']:,} |")
        output.append("")
        
        # Issues
        issues_count = len(results['orphans']) + len(results['broken_links'])
        if issues_count > 0:
            output.append(f"## ⚠️ Issues ({issues_count})")
            output.append("")
            
            if results['orphans']:
                output.append(f"### 🔸 Orphaned Files ({len(results['orphans'])})")
                output.append("")
                output.append("Files with no incoming links:")
                output.append("")
                for orphan in results['orphans']:
                    output.append(f"- **{orphan['name']}** ({orphan['word_count']} words, modified {orphan['modified'][:10]})")
                output.append("")
                
            if results['broken_links']:
                output.append(f"### 🔗 Broken Links ({len(results['broken_links'])})")
                output.append("")
                for link in results['broken_links']:
                    output.append(f"- `{link['target']}` in **{link['source']}**")
                    if link['suggestions']:
                        output.append(f"  - Suggestions: {', '.join(link['suggestions'])}")
                output.append("")
        else:
            output.append("## ✅ No Issues")
            output.append("")
            output.append("Your vault is in great shape!")
            output.append("")
            
        # Top tags
        tag_analysis = results['tag_analysis']
        if tag_analysis.get('tag_usage'):
            output.append("## 🏷️ Tag Usage")
            output.append("")
            output.append("| Tag | Files |")
            output.append("|-----|-------|")
            for tag, info in list(tag_analysis['tag_usage'].items())[:15]:
                output.append(f"| #{tag} | {info['count']} |")
            output.append("")
            
        # Organization suggestions
        suggestions = results['organization_suggestions']
        if any(suggestions.values()):
            output.append("## 📁 Organization Suggestions")
            output.append("")
            
            if suggestions.get('flat_structure_warning'):
                warning = suggestions['flat_structure_warning']
                output.append(f"⚠️ **{warning['files_in_root']} files in root directory** - {warning['recommendation']}")
                output.append("")
                
            if suggestions.get('by_date'):
                output.append(f"### 📅 Date-based Files ({len(suggestions['by_date'])})")
                output.append("")
                output.append("These files could be organized in a `Journal/` folder:")
                output.append("")
                for file_path in suggestions['by_date']:
                    output.append(f"- {file_path}")
                output.append("")
                
        return "\n".join(output)
        
    def _apply_link_fix(self, source_file: str, old_target: str, new_target: str):
        """Apply a link fix to a file."""
        file_path = self.analyzer.vault_path / source_file
        content = file_path.read_text(encoding='utf-8')
        
        # Replace wikilinks
        content = content.replace(f"[[{old_target}]]", f"[[{new_target}]]")
        content = content.replace(f"[[{old_target}|", f"[[{new_target}|")
        
        file_path.write_text(content, encoding='utf-8')

if __name__ == "__main__":
    cli = VaultMaintenanceCLI()
    cli.main()