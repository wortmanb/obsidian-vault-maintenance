#!/usr/bin/env python3
"""
Test suite for Obsidian Vault Maintenance System
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from vault_maintenance import VaultAnalyzer, ReportGenerator, MaintenanceActions


def create_test_vault():
    """Create a test vault with known issues"""
    test_dir = tempfile.mkdtemp(prefix="test_vault_")
    test_vault = Path(test_dir)
    
    # Create some test files with content
    files = {
        'index.md': """# Index Page
Welcome to the test vault.

Links to [[Valid File]] and [[Broken Link]].

Tags: #test #documentation
""",
        'valid_file.md': """# Valid File
This file exists and is linked from index.

Another link to [[Another File]].

Tags: #test #valid
""",
        'another_file.md': """# Another File
This file is linked from Valid File.

Tags: #test #another
""",
        'orphaned.md': """# Orphaned File
This file has no incoming links.

Tags: #orphan #lonely
""",
        'duplicate_tag.md': """# File with Similar Tags
This file has similar tags to test duplicates.

Tags: #test #tst #testing
""",
        'frontmatter.md': """---
title: "Frontmatter Test"
author: "Test Author"
date: 2026-02-23
tags: [frontmatter, yaml]
---

# Frontmatter Test
This file has YAML frontmatter.
""",
        'date_file_2024-01-15.md': """# Date-based File
This file follows date naming convention.

Tags: #dated #2024
""",
    }
    
    for filename, content in files.items():
        file_path = test_vault / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    return test_vault


def test_vault_analyzer():
    """Test the main VaultAnalyzer functionality"""
    test_vault = create_test_vault()
    
    try:
        print("🧪 Testing VaultAnalyzer...")
        
        # Initialize analyzer
        analyzer = VaultAnalyzer(test_vault)
        
        # Test scanning
        stats = analyzer.scan_vault()
        
        # Verify basic stats
        assert stats['total_files'] == 7, f"Expected 7 files, got {stats['total_files']}"
        assert stats['unique_tags'] > 0, "Should find some tags"
        assert stats['total_links'] > 0, "Should find some links"
        
        # Test orphan detection
        orphans = analyzer.find_orphaned_files()
        assert 'orphaned' in orphans, "Should detect orphaned.md as orphaned"
        assert 'index' not in orphans, "index.md should not be considered orphaned"
        
        # Test broken link detection
        broken_links = analyzer.find_broken_links()
        broken_targets = [link[1] for link in broken_links]
        assert 'Broken Link' in broken_targets, "Should detect 'Broken Link' as broken"
        
        # Test tag analysis
        tag_analysis = analyzer.analyze_tags()
        assert len(tag_analysis['similar_tags']) > 0, "Should find similar tags (test/tst/testing)"
        
        # Test frontmatter parsing
        assert 'frontmatter' in analyzer.frontmatter, "Should parse frontmatter from frontmatter.md"
        
        print("✅ VaultAnalyzer tests passed!")
        
    finally:
        # Cleanup
        shutil.rmtree(test_vault)


def test_report_generation():
    """Test report generation in different formats"""
    test_vault = create_test_vault()
    
    try:
        print("📊 Testing report generation...")
        
        analyzer = VaultAnalyzer(test_vault)
        stats = analyzer.scan_vault()
        
        analysis_results = {
            'stats': stats,
            'orphans': analyzer.find_orphaned_files(),
            'broken_links': analyzer.find_broken_links(),
            'tag_analysis': analyzer.analyze_tags(),
            'organization_suggestions': analyzer.suggest_organization(),
        }
        
        reporter = ReportGenerator(analyzer)
        
        # Test terminal report (just make sure it doesn't crash)
        print("  Testing terminal report...")
        reporter.generate_terminal_report(analysis_results)
        
        # Test markdown report
        print("  Testing markdown report...")
        markdown_content = reporter.generate_markdown_report(analysis_results)
        assert "# Obsidian Vault Health Report" in markdown_content
        assert "Statistics" in markdown_content
        
        # Test JSON report
        print("  Testing JSON report...")
        json_content = reporter.generate_json_report(analysis_results)
        assert '"total_files":' in json_content
        assert '"orphans":' in json_content
        
        print("✅ Report generation tests passed!")
        
    finally:
        shutil.rmtree(test_vault)


def test_maintenance_actions():
    """Test maintenance and repair actions"""
    test_vault = create_test_vault()
    
    try:
        print("🔧 Testing maintenance actions...")
        
        analyzer = VaultAnalyzer(test_vault)
        analyzer.scan_vault()
        
        maintenance = MaintenanceActions(analyzer)
        
        # Test broken link fixing (dry run)
        print("  Testing broken link fixes (dry run)...")
        fixed_count = maintenance.fix_broken_links(interactive=False, dry_run=True)
        assert fixed_count >= 0, "Should return non-negative fix count"
        
        # Test tag merging (dry run)
        print("  Testing tag merging (dry run)...")
        merged_count = maintenance.merge_similar_tags(
            threshold=0.7, 
            interactive=False, 
            dry_run=True
        )
        assert merged_count >= 0, "Should return non-negative merge count"
        
        print("✅ Maintenance action tests passed!")
        
    finally:
        shutil.rmtree(test_vault)


def test_cli_interface():
    """Test the CLI interface"""
    test_vault = create_test_vault()
    
    try:
        print("⌨️  Testing CLI interface...")
        
        # Test basic scan command
        exit_code = os.system(f'python3 vault_maintenance.py --vault "{test_vault}" scan > /dev/null 2>&1')
        assert exit_code == 0, "Basic scan command should succeed"
        
        # Test JSON output
        exit_code = os.system(f'python3 vault_maintenance.py --vault "{test_vault}" scan --format json > /dev/null 2>&1')
        assert exit_code == 0, "JSON format should work"
        
        # Test tags command
        exit_code = os.system(f'python3 vault_maintenance.py --vault "{test_vault}" tags > /dev/null 2>&1')
        assert exit_code == 0, "Tags command should work"
        
        print("✅ CLI interface tests passed!")
        
    finally:
        shutil.rmtree(test_vault)


def run_all_tests():
    """Run the complete test suite"""
    print("🚀 Running Obsidian Vault Maintenance test suite...\n")
    
    try:
        test_vault_analyzer()
        test_report_generation()
        test_maintenance_actions()
        test_cli_interface()
        
        print(f"\n🎉 All tests passed! Vault maintenance system is ready to use.")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)