#!/usr/bin/env python3
"""
Obsidian Vault Maintenance System
A comprehensive CLI tool for maintaining and organizing Obsidian vaults.

Features:
- Health checks and issue detection
- Orphaned file identification  
- Broken link detection and repair suggestions
- Tag analysis and cleanup recommendations
- Organization suggestions based on content patterns
- Comprehensive reporting (terminal, markdown, JSON)
"""

import os
import re
import sys
import json
import argparse
import datetime
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple, Optional
import difflib


class Colors:
    """ANSI color codes for terminal output"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


class VaultAnalyzer:
    """Main vault analysis engine"""
    
    def __init__(self, vault_path: Path):
        self.vault_path = Path(vault_path).resolve()
        self.files = {}  # filename -> full_path
        self.content_cache = {}  # path -> content
        self.links = defaultdict(set)  # file -> set of links it contains
        self.backlinks = defaultdict(set)  # file -> set of files linking to it
        self.tags = defaultdict(set)  # tag -> set of files containing it
        self.frontmatter = {}  # file -> frontmatter dict
        
    def scan_vault(self) -> Dict:
        """Comprehensive vault scan"""
        print(f"{Colors.BLUE}🔍 Scanning vault: {self.vault_path}{Colors.RESET}")
        
        self._collect_files()
        self._analyze_content()
        self._build_link_graph()
        self._extract_tags()
        self._parse_frontmatter()
        
        stats = self._calculate_stats()
        print(f"{Colors.GREEN}✓ Scan complete: {stats['total_files']} files, {stats['total_links']} links, {stats['unique_tags']} tags{Colors.RESET}")
        
        return stats
    
    def _collect_files(self):
        """Collect all markdown files in the vault"""
        for file_path in self.vault_path.rglob("*.md"):
            if self._should_include_file(file_path):
                key = file_path.stem
                self.files[key] = file_path
                
    def _should_include_file(self, file_path: Path) -> bool:
        """Determine if a file should be included in analysis"""
        # Skip common system/template files
        skip_patterns = [
            r'\.obsidian/',
            r'templates?/',
            r'\.git/',
            r'node_modules/',
            r'\.trash/',
        ]
        
        path_str = str(file_path.relative_to(self.vault_path))
        return not any(re.search(pattern, path_str, re.IGNORECASE) for pattern in skip_patterns)
    
    def _analyze_content(self):
        """Read and cache file content"""
        for filename, file_path in self.files.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.content_cache[file_path] = content
            except (UnicodeDecodeError, PermissionError) as e:
                print(f"{Colors.YELLOW}⚠️  Cannot read {file_path}: {e}{Colors.RESET}")
                self.content_cache[file_path] = ""
    
    def _build_link_graph(self):
        """Extract internal links and build link graph"""
        link_patterns = [
            r'\[\[([^\]|]+)(?:\|[^\]]*)?\]\]',  # [[link]] or [[link|alias]]
            r'\[([^\]]+)\]\(([^)]+\.md)\)',      # [text](file.md)
        ]
        
        for file_path, content in self.content_cache.items():
            filename = file_path.stem
            
            for pattern in link_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, tuple):
                        # Handle tuple matches from second pattern
                        link_target = match[1].replace('.md', '') if match[1].endswith('.md') else match[0]
                    else:
                        # Handle string matches from first pattern
                        link_target = match
                    
                    # Clean up link target
                    link_target = link_target.split('#')[0]  # Remove anchors
                    link_target = link_target.strip()
                    
                    if link_target:
                        self.links[filename].add(link_target)
                        self.backlinks[link_target].add(filename)
    
    def _extract_tags(self):
        """Extract hashtags from content"""
        tag_pattern = r'#([a-zA-Z0-9/_-]+)'
        
        for file_path, content in self.content_cache.items():
            filename = file_path.stem
            matches = re.findall(tag_pattern, content)
            
            for tag in matches:
                # Skip common false positives
                if not re.match(r'^(h[1-6]|[0-9]+)$', tag):
                    self.tags[tag].add(filename)
    
    def _parse_frontmatter(self):
        """Parse YAML frontmatter"""
        frontmatter_pattern = r'^---\n(.*?)\n---'
        
        for file_path, content in self.content_cache.items():
            filename = file_path.stem
            match = re.match(frontmatter_pattern, content, re.DOTALL)
            
            if match:
                # Simple YAML parsing (basic key: value pairs)
                fm_content = match.group(1)
                fm_dict = {}
                
                for line in fm_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        fm_dict[key] = value
                
                self.frontmatter[filename] = fm_dict
    
    def _calculate_stats(self) -> Dict:
        """Calculate vault statistics"""
        total_size = sum(
            file_path.stat().st_size 
            for file_path in self.files.values()
        )
        
        total_words = sum(
            len(content.split()) 
            for content in self.content_cache.values()
        )
        
        return {
            'total_files': len(self.files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_words': total_words,
            'total_links': sum(len(links) for links in self.links.values()),
            'unique_tags': len(self.tags),
            'files_with_frontmatter': len(self.frontmatter),
        }
    
    def find_orphaned_files(self) -> List[str]:
        """Find files with no incoming links"""
        orphans = []
        
        # Common files that shouldn't be considered orphaned
        system_files = {'index', 'readme', 'home', 'start', 'dashboard', 'toc'}
        
        for filename in self.files.keys():
            if filename.lower() not in system_files and len(self.backlinks[filename]) == 0:
                orphans.append(filename)
        
        return sorted(orphans)
    
    def find_broken_links(self) -> List[Tuple[str, str, str]]:
        """Find links pointing to non-existent files"""
        broken = []
        
        for source_file, targets in self.links.items():
            for target in targets:
                if target not in self.files:
                    # Try to find similar files for suggestions
                    suggestions = difflib.get_close_matches(
                        target, 
                        self.files.keys(), 
                        n=3, 
                        cutoff=0.6
                    )
                    suggestion = suggestions[0] if suggestions else "No suggestions"
                    broken.append((source_file, target, suggestion))
        
        return sorted(broken)
    
    def analyze_tags(self) -> Dict:
        """Analyze tag usage patterns"""
        tag_counts = {tag: len(files) for tag, files in self.tags.items()}
        
        # Find similar tags that might be duplicates
        similar_tags = []
        tag_list = list(self.tags.keys())
        
        for i, tag1 in enumerate(tag_list):
            for j, tag2 in enumerate(tag_list[i+1:], i+1):
                similarity = difflib.SequenceMatcher(None, tag1, tag2).ratio()
                if similarity > 0.8 and similarity < 1.0:
                    similar_tags.append((tag1, tag2, similarity))
        
        return {
            'tag_counts': sorted(tag_counts.items(), key=lambda x: x[1], reverse=True),
            'rare_tags': [(tag, count) for tag, count in tag_counts.items() if count == 1],
            'popular_tags': [(tag, count) for tag, count in tag_counts.items() if count >= 5],
            'similar_tags': sorted(similar_tags, key=lambda x: x[2], reverse=True),
        }
    
    def suggest_organization(self) -> Dict:
        """Suggest organizational improvements"""
        suggestions = {
            'date_based': self._find_date_based_files(),
            'topic_clusters': self._find_topic_clusters(), 
            'flat_structure': self._find_flat_structure_issues(),
        }
        
        return suggestions
    
    def _find_date_based_files(self) -> List[str]:
        """Find files that might benefit from date-based organization"""
        date_pattern = r'\d{4}-\d{2}-\d{2}'
        date_files = []
        
        for filename in self.files.keys():
            if re.search(date_pattern, filename):
                date_files.append(filename)
        
        return sorted(date_files)
    
    def _find_topic_clusters(self) -> List[Tuple[str, List[str]]]:
        """Find potential topic-based clusters using tags"""
        clusters = []
        
        for tag, files in self.tags.items():
            if len(files) >= 3:  # Clusters with at least 3 files
                clusters.append((tag, sorted(list(files))))
        
        return sorted(clusters, key=lambda x: len(x[1]), reverse=True)
    
    def _find_flat_structure_issues(self) -> List[str]:
        """Find files in root that might benefit from folders"""
        root_files = []
        
        for filename, file_path in self.files.items():
            # Check if file is directly in vault root (not in a subfolder)
            if len(file_path.relative_to(self.vault_path).parts) == 1:
                root_files.append(filename)
        
        return sorted(root_files)


class ReportGenerator:
    """Generate reports in different formats"""
    
    def __init__(self, analyzer: VaultAnalyzer):
        self.analyzer = analyzer
    
    def generate_terminal_report(self, analysis_results: Dict):
        """Generate colored terminal report"""
        print(f"\n{Colors.BOLD}📊 VAULT HEALTH REPORT{Colors.RESET}")
        print("=" * 50)
        
        # Statistics
        stats = analysis_results['stats']
        print(f"\n{Colors.CYAN}📈 Statistics:{Colors.RESET}")
        print(f"  Files: {stats['total_files']}")
        print(f"  Size: {stats['total_size_mb']} MB")
        print(f"  Words: {stats['total_words']:,}")
        print(f"  Links: {stats['total_links']}")
        print(f"  Tags: {stats['unique_tags']}")
        print(f"  Frontmatter: {stats['files_with_frontmatter']} files")
        
        # Orphaned files
        orphans = analysis_results['orphans']
        print(f"\n{Colors.YELLOW}🏝️  Orphaned Files ({len(orphans)}):{Colors.RESET}")
        if orphans:
            for orphan in orphans[:10]:  # Show first 10
                print(f"  • {orphan}")
            if len(orphans) > 10:
                print(f"  ... and {len(orphans) - 10} more")
        else:
            print("  ✓ No orphaned files found!")
        
        # Broken links
        broken = analysis_results['broken_links']
        print(f"\n{Colors.RED}🔗 Broken Links ({len(broken)}):{Colors.RESET}")
        if broken:
            for source, target, suggestion in broken[:10]:  # Show first 10
                print(f"  • {source} → {target}")
                if suggestion != "No suggestions":
                    print(f"    💡 Try: {suggestion}")
            if len(broken) > 10:
                print(f"  ... and {len(broken) - 10} more")
        else:
            print("  ✓ No broken links found!")
        
        # Tag analysis
        tag_analysis = analysis_results['tag_analysis']
        print(f"\n{Colors.MAGENTA}🏷️  Tag Analysis:{Colors.RESET}")
        print(f"  Popular tags: {len(tag_analysis['popular_tags'])}")
        print(f"  Rare tags: {len(tag_analysis['rare_tags'])}")
        print(f"  Similar tags: {len(tag_analysis['similar_tags'])}")
        
        if tag_analysis['similar_tags']:
            print(f"\n{Colors.YELLOW}  🔄 Similar tags (potential duplicates):{Colors.RESET}")
            for tag1, tag2, similarity in tag_analysis['similar_tags'][:5]:
                print(f"    • {tag1} ≈ {tag2} ({similarity:.1%})")
    
    def generate_markdown_report(self, analysis_results: Dict) -> str:
        """Generate markdown report"""
        report = []
        report.append("# Obsidian Vault Health Report")
        report.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Statistics
        stats = analysis_results['stats']
        report.append("## 📈 Statistics")
        report.append("")
        report.append(f"- **Files:** {stats['total_files']}")
        report.append(f"- **Size:** {stats['total_size_mb']} MB")
        report.append(f"- **Words:** {stats['total_words']:,}")
        report.append(f"- **Internal Links:** {stats['total_links']}")
        report.append(f"- **Unique Tags:** {stats['unique_tags']}")
        report.append(f"- **Files with Properties:** {stats['files_with_frontmatter']}")
        report.append("")
        
        # Issues
        orphans = analysis_results['orphans']
        report.append(f"## 🏝️ Orphaned Files ({len(orphans)})")
        report.append("")
        if orphans:
            report.append("Files with no incoming links:")
            report.append("")
            for orphan in orphans:
                report.append(f"- {orphan}")
        else:
            report.append("✅ No orphaned files found!")
        report.append("")
        
        # Broken links
        broken = analysis_results['broken_links']
        report.append(f"## 🔗 Broken Links ({len(broken)})")
        report.append("")
        if broken:
            report.append("Links pointing to non-existent files:")
            report.append("")
            for source, target, suggestion in broken:
                report.append(f"- **{source}** → `{target}`")
                if suggestion != "No suggestions":
                    report.append(f"  - 💡 Suggestion: `{suggestion}`")
        else:
            report.append("✅ No broken links found!")
        report.append("")
        
        # Tags
        tag_analysis = analysis_results['tag_analysis']
        report.append("## 🏷️ Tag Analysis")
        report.append("")
        
        if tag_analysis['popular_tags']:
            report.append("### Popular Tags (5+ uses)")
            report.append("")
            for tag, count in tag_analysis['popular_tags'][:10]:
                report.append(f"- #{tag} ({count} files)")
            report.append("")
        
        if tag_analysis['similar_tags']:
            report.append("### Similar Tags (Potential Duplicates)")
            report.append("")
            for tag1, tag2, similarity in tag_analysis['similar_tags']:
                report.append(f"- #{tag1} ≈ #{tag2} ({similarity:.1%})")
            report.append("")
        
        return "\n".join(report)
    
    def generate_json_report(self, analysis_results: Dict) -> str:
        """Generate JSON report for programmatic use"""
        # Convert sets to lists for JSON serialization
        json_safe = {}
        for key, value in analysis_results.items():
            if isinstance(value, dict):
                json_safe[key] = {k: list(v) if isinstance(v, set) else v for k, v in value.items()}
            elif isinstance(value, list):
                json_safe[key] = value
            else:
                json_safe[key] = value
        
        json_safe['generated_at'] = datetime.datetime.now().isoformat()
        
        return json.dumps(json_safe, indent=2, ensure_ascii=False)


class MaintenanceActions:
    """Handles maintenance actions like fixing links and organizing files"""
    
    def __init__(self, analyzer: VaultAnalyzer):
        self.analyzer = analyzer
    
    def fix_broken_links(self, interactive=True, dry_run=False) -> int:
        """Fix broken links with user confirmation"""
        broken_links = self.analyzer.find_broken_links()
        
        if not broken_links:
            print(f"{Colors.GREEN}✓ No broken links found!{Colors.RESET}")
            return 0
        
        print(f"\n{Colors.YELLOW}🔧 Found {len(broken_links)} broken links{Colors.RESET}")
        
        fixed_count = 0
        for source_file, broken_target, suggestion in broken_links:
            source_path = self.analyzer.files[source_file]
            
            print(f"\n{Colors.CYAN}📝 {source_file}{Colors.RESET}")
            print(f"  Broken link: [[{broken_target}]]")
            
            if suggestion != "No suggestions":
                print(f"  {Colors.GREEN}💡 Suggestion: [[{suggestion}]]{Colors.RESET}")
                
                if interactive:
                    choice = input("  Apply fix? (y/n/s=skip all): ").lower().strip()
                    if choice == 's':
                        break
                    elif choice != 'y':
                        continue
                
                if not dry_run:
                    # Read file content
                    content = self.analyzer.content_cache[source_path]
                    
                    # Replace the broken link
                    old_link = f"[[{broken_target}]]"
                    new_link = f"[[{suggestion}]]"
                    updated_content = content.replace(old_link, new_link)
                    
                    # Write back to file
                    try:
                        with open(source_path, 'w', encoding='utf-8') as f:
                            f.write(updated_content)
                        print(f"  {Colors.GREEN}✓ Fixed: {old_link} → {new_link}{Colors.RESET}")
                        fixed_count += 1
                    except Exception as e:
                        print(f"  {Colors.RED}❌ Failed to fix: {e}{Colors.RESET}")
                else:
                    print(f"  {Colors.BLUE}🔍 Would fix: [[{broken_target}]] → [[{suggestion}]]{Colors.RESET}")
                    fixed_count += 1
            else:
                print(f"  {Colors.RED}❌ No suggestions available{Colors.RESET}")
        
        if dry_run:
            print(f"\n{Colors.BLUE}🔍 Dry run: Would fix {fixed_count} links{Colors.RESET}")
        else:
            print(f"\n{Colors.GREEN}✓ Fixed {fixed_count} broken links{Colors.RESET}")
        
        return fixed_count
    
    def merge_similar_tags(self, threshold=0.8, interactive=True, dry_run=False) -> int:
        """Merge similar tags"""
        tag_analysis = self.analyzer.analyze_tags()
        similar_tags = [
            (tag1, tag2, sim) for tag1, tag2, sim in tag_analysis['similar_tags']
            if sim >= threshold
        ]
        
        if not similar_tags:
            print(f"{Colors.GREEN}✓ No similar tags found (threshold: {threshold}){Colors.RESET}")
            return 0
        
        print(f"\n{Colors.YELLOW}🏷️  Found {len(similar_tags)} similar tag pairs{Colors.RESET}")
        
        merged_count = 0
        for tag1, tag2, similarity in similar_tags:
            files1 = self.analyzer.tags[tag1]
            files2 = self.analyzer.tags[tag2]
            
            print(f"\n{Colors.CYAN}Tags: #{tag1} ({len(files1)} files) ≈ #{tag2} ({len(files2)} files) [{similarity:.1%}]{Colors.RESET}")
            
            if interactive:
                print(f"  Which tag to keep?")
                print(f"  1. #{tag1}")
                print(f"  2. #{tag2}")
                choice = input("  Choice (1/2/s=skip): ").strip()
                
                if choice == 's':
                    continue
                elif choice == '1':
                    keep_tag, merge_tag = tag1, tag2
                elif choice == '2':
                    keep_tag, merge_tag = tag2, tag1
                else:
                    continue
            else:
                # Auto-choose the more popular tag
                keep_tag, merge_tag = (tag1, tag2) if len(files1) >= len(files2) else (tag2, tag1)
            
            if not dry_run:
                # Replace the tag in all files
                merge_files = self.analyzer.tags[merge_tag]
                for filename in merge_files:
                    file_path = self.analyzer.files[filename]
                    content = self.analyzer.content_cache[file_path]
                    
                    # Replace #merge_tag with #keep_tag
                    updated_content = re.sub(
                        rf'#\b{re.escape(merge_tag)}\b',
                        f'#{keep_tag}',
                        content
                    )
                    
                    if updated_content != content:
                        try:
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                        except Exception as e:
                            print(f"  {Colors.RED}❌ Failed to update {filename}: {e}{Colors.RESET}")
                            continue
                
                print(f"  {Colors.GREEN}✓ Merged #{merge_tag} → #{keep_tag}{Colors.RESET}")
                merged_count += 1
            else:
                print(f"  {Colors.BLUE}🔍 Would merge #{merge_tag} → #{keep_tag}{Colors.RESET}")
                merged_count += 1
        
        if dry_run:
            print(f"\n{Colors.BLUE}🔍 Dry run: Would merge {merged_count} tag pairs{Colors.RESET}")
        else:
            print(f"\n{Colors.GREEN}✓ Merged {merged_count} similar tags{Colors.RESET}")
        
        return merged_count


def main():
    parser = argparse.ArgumentParser(description="Obsidian Vault Maintenance System")
    parser.add_argument('--vault', '-v', default='.', help='Path to Obsidian vault (default: current directory)')
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Scan command (default)
    scan_parser = subparsers.add_parser('scan', help='Analyze vault health (default)')
    scan_parser.add_argument('--format', choices=['terminal', 'markdown', 'json'], default='terminal', help='Report format')
    scan_parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    scan_parser.add_argument('--focus', choices=['orphans', 'links', 'tags'], help='Focus on specific issues')
    
    # Fix command
    fix_parser = subparsers.add_parser('fix', help='Fix issues interactively')
    fix_parser.add_argument('--interactive', action='store_true', default=True, help='Confirm each fix')
    fix_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    fix_parser.add_argument('--links', action='store_true', help='Fix broken links only')
    
    # Tags command
    tags_parser = subparsers.add_parser('tags', help='Tag management operations')
    tags_parser.add_argument('--merge-similar', action='store_true', help='Merge similar tags')
    tags_parser.add_argument('--threshold', type=float, default=0.8, help='Similarity threshold for merging')
    tags_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Properties command
    props_parser = subparsers.add_parser('properties', help='Frontmatter property operations')
    props_parser.add_argument('--standardize', action='store_true', help='Standardize property names')
    props_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Organize command
    org_parser = subparsers.add_parser('organize', help='File organization suggestions')
    org_parser.add_argument('--by', choices=['date', 'topic'], help='Organization method')
    org_parser.add_argument('--dry-run', action='store_true', help='Show what would be done')
    
    # Report command
    report_parser = subparsers.add_parser('report', help='Generate detailed reports')
    report_parser.add_argument('--format', choices=['terminal', 'markdown', 'json'], default='terminal')
    report_parser.add_argument('--output', '-o', help='Output file')
    report_parser.add_argument('--save-to', help='Save report to specific file')
    
    args = parser.parse_args()
    
    # Default to scan if no command specified
    if not args.command:
        args.command = 'scan'
        args.format = 'terminal'
        args.output = None
        args.focus = None
    
    args = parser.parse_args()
    
    # Default to scan if no command specified
    if not args.command:
        args.command = 'scan'
        if not hasattr(args, 'format'):
            args.format = 'terminal'
        if not hasattr(args, 'output'):
            args.output = None
        if not hasattr(args, 'focus'):
            args.focus = None
    
    # Validate vault path
    vault_path = Path(args.vault).resolve()
    if not vault_path.exists():
        print(f"{Colors.RED}❌ Vault path does not exist: {vault_path}{Colors.RESET}")
        sys.exit(1)
    
    if not vault_path.is_dir():
        print(f"{Colors.RED}❌ Vault path is not a directory: {vault_path}{Colors.RESET}")
        sys.exit(1)
    
    try:
        # Initialize analyzer
        analyzer = VaultAnalyzer(vault_path)
        
        # Initialize maintenance actions
        maintenance = MaintenanceActions(analyzer)
        
        # Perform analysis for most commands
        if args.command in ['scan', 'fix', 'tags', 'report', 'organize']:
            print(f"{Colors.BLUE}🚀 Starting vault analysis...{Colors.RESET}")
            stats = analyzer.scan_vault()
            
            # Gather analysis results
            analysis_results = {
                'stats': stats,
                'orphans': analyzer.find_orphaned_files(),
                'broken_links': analyzer.find_broken_links(),
                'tag_analysis': analyzer.analyze_tags(),
                'organization_suggestions': analyzer.suggest_organization(),
            }
        
        # Handle different commands
        if args.command == 'scan' or args.command == 'report':
            # Generate report
            reporter = ReportGenerator(analyzer)
            
            format_type = args.format if hasattr(args, 'format') else 'terminal'
            output_file = args.output if hasattr(args, 'output') else None
            
            if hasattr(args, 'save_to') and args.save_to:
                output_file = args.save_to
            
            if format_type == 'terminal':
                reporter.generate_terminal_report(analysis_results)
            elif format_type == 'markdown':
                content = reporter.generate_markdown_report(analysis_results)
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"{Colors.GREEN}✓ Report saved to: {output_file}{Colors.RESET}")
                else:
                    print(content)
            elif format_type == 'json':
                content = reporter.generate_json_report(analysis_results)
                if output_file:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"{Colors.GREEN}✓ Report saved to: {output_file}{Colors.RESET}")
                else:
                    print(content)
            
            # Summary for scan command
            if args.command == 'scan':
                total_issues = len(analysis_results['orphans']) + len(analysis_results['broken_links'])
                if total_issues > 0:
                    print(f"\n{Colors.YELLOW}⚠️  Found {total_issues} issues that could use attention{Colors.RESET}")
                    print(f"{Colors.CYAN}💡 Use 'vault-maintenance fix' to repair broken links{Colors.RESET}")
                    print(f"{Colors.CYAN}💡 Use 'vault-maintenance tags --merge-similar' for tag cleanup{Colors.RESET}")
                else:
                    print(f"\n{Colors.GREEN}🎉 Vault looks healthy! No major issues found{Colors.RESET}")
        
        elif args.command == 'fix':
            dry_run = getattr(args, 'dry_run', False)
            interactive = getattr(args, 'interactive', True)
            
            if getattr(args, 'links', False) or not any([getattr(args, 'links', False)]):
                # Fix broken links (default fix action)
                fixed_count = maintenance.fix_broken_links(interactive=interactive, dry_run=dry_run)
                
                if fixed_count == 0 and not dry_run:
                    print(f"{Colors.GREEN}🎉 No broken links found to fix!{Colors.RESET}")
        
        elif args.command == 'tags':
            if getattr(args, 'merge_similar', False):
                threshold = getattr(args, 'threshold', 0.8)
                dry_run = getattr(args, 'dry_run', False)
                
                merged_count = maintenance.merge_similar_tags(
                    threshold=threshold,
                    interactive=True,
                    dry_run=dry_run
                )
                
                if merged_count == 0 and not dry_run:
                    print(f"{Colors.GREEN}🎉 No similar tags found to merge!{Colors.RESET}")
            else:
                # Show tag analysis by default
                reporter = ReportGenerator(analyzer)
                tag_analysis = analysis_results['tag_analysis']
                
                print(f"\n{Colors.BOLD}🏷️  TAG ANALYSIS{Colors.RESET}")
                print("=" * 30)
                
                print(f"\n{Colors.CYAN}Popular tags (5+ uses):{Colors.RESET}")
                for tag, count in tag_analysis['popular_tags'][:10]:
                    print(f"  #{tag}: {count} files")
                
                print(f"\n{Colors.YELLOW}Similar tags:{Colors.RESET}")
                for tag1, tag2, similarity in tag_analysis['similar_tags'][:10]:
                    print(f"  #{tag1} ≈ #{tag2} ({similarity:.1%})")
                
                if tag_analysis['similar_tags']:
                    print(f"\n{Colors.CYAN}💡 Run with --merge-similar to merge duplicate tags{Colors.RESET}")
        
        elif args.command == 'organize':
            org_suggestions = analysis_results['organization_suggestions']
            
            print(f"\n{Colors.BOLD}📁 ORGANIZATION SUGGESTIONS{Colors.RESET}")
            print("=" * 40)
            
            if getattr(args, 'by', None) == 'date' or not getattr(args, 'by', None):
                date_files = org_suggestions['date_based']
                if date_files:
                    print(f"\n{Colors.CYAN}📅 Date-based files ({len(date_files)}):{Colors.RESET}")
                    for filename in date_files[:10]:
                        print(f"  • {filename}")
                    if len(date_files) > 10:
                        print(f"  ... and {len(date_files) - 10} more")
                    print(f"\n{Colors.BLUE}💡 Consider organizing these by year/month folders{Colors.RESET}")
            
            if getattr(args, 'by', None) == 'topic' or not getattr(args, 'by', None):
                topic_clusters = org_suggestions['topic_clusters']
                if topic_clusters:
                    print(f"\n{Colors.MAGENTA}🏷️  Topic clusters:{Colors.RESET}")
                    for tag, files in topic_clusters[:5]:
                        print(f"  #{tag} ({len(files)} files):")
                        for filename in files[:3]:
                            print(f"    • {filename}")
                        if len(files) > 3:
                            print(f"    ... and {len(files) - 3} more")
                    print(f"\n{Colors.BLUE}💡 Consider creating folders for major topics{Colors.RESET}")
        
        elif args.command == 'properties':
            print(f"\n{Colors.BOLD}📋 PROPERTY ANALYSIS{Colors.RESET}")
            print("=" * 30)
            
            fm_files = len(analyzer.frontmatter)
            total_files = len(analyzer.files)
            
            print(f"Files with properties: {fm_files}/{total_files} ({fm_files/total_files*100:.1f}%)")
            
            if analyzer.frontmatter:
                # Analyze property usage
                all_props = defaultdict(int)
                for props in analyzer.frontmatter.values():
                    for prop in props.keys():
                        all_props[prop] += 1
                
                print(f"\n{Colors.CYAN}Common properties:{Colors.RESET}")
                for prop, count in sorted(all_props.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"  {prop}: {count} files")
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⏹️  Analysis interrupted{Colors.RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error: {e}{Colors.RESET}")
        if '--debug' in sys.argv:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()