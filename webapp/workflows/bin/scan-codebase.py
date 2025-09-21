#!/usr/bin/env python3
"""
Codebase Environment Variable Scanner

Scans the webapp codebase for environment variable usage and compares with 
the golden environment file to identify missing or unused variables.

Usage:
    uv run python workflows/bin/scan-codebase.py                     # Full scan and comparison
    uv run python workflows/bin/scan-codebase.py --unused            # Find unused variables
    uv run python workflows/bin/scan-codebase.py --missing           # Find undefined variables  
    uv run python workflows/bin/scan-codebase.py --report            # Generate detailed report
"""

import argparse
import ast
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class EnvVarUsage:
    """Represents usage of an environment variable in code."""
    var_name: str
    file_path: str
    line_number: int
    context: str  # The line of code where it's used
    usage_type: str  # 'env', 'os.environ', 'settings', 'feature_flag'


@dataclass
class ScanResult:
    """Result of scanning the codebase."""
    found_variables: Set[str]
    usage_details: List[EnvVarUsage]
    files_scanned: int
    lines_scanned: int


@dataclass
class ComparisonReport:
    """Comparison between code usage and golden file."""
    used_in_code: Set[str]
    defined_in_golden: Set[str]
    missing_definitions: Set[str]  # Used in code but not in golden
    unused_definitions: Set[str]   # Defined in golden but not used
    properly_defined: Set[str]     # Used and defined


class CodebaseScanner:
    """Scans Python files for environment variable usage."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.webapp_dir = self.project_root.parent  # Go up to scan the actual webapp
        self.golden_file = self.project_root / "envs" / "env.gold"
        
        # Patterns to search for environment variables
        self.env_patterns = [
            # env.list('VARIABLE_NAME'), env.bool('VARIABLE_NAME'), etc.
            re.compile(r"env\.(?:str|list|bool|int|float|json|url|path|db_url|cache_url|email_url|search_url|queue_url)\s*\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]"),
            re.compile(r"env\s*\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]"),
            
            # os.environ.get('VARIABLE_NAME') or os.environ['VARIABLE_NAME']
            re.compile(r"os\.environ\.(?:get|__getitem__)\s*\(\s*['\"]([A-Z_][A-Z0-9_]*)['\"]"),
            
            # settings.VARIABLE_NAME
            re.compile(r"settings\.([A-Z_][A-Z0-9_]*)(?!\s*=)"),
            
            # FEATURE_FLAGS['FLAG_NAME'] or FEATURE_FLAGS.get('FLAG_NAME')
            re.compile(r"FEATURE_FLAGS\s*(?:\[|\.get\()\s*['\"]([A-Z_][A-Z0-9_]*)['\"]"),
            
            # Direct feature flag access: USE_GCS_STORAGE, LOKI_ENABLED, etc.
            re.compile(r"\\b(USE_[A-Z_]+|[A-Z_]+_ENABLED|[A-Z_]+_LOGGING)\\b"),
        ]
    
    def scan_python_files(self, directory: Path = None) -> ScanResult:
        """Scan all Python files for environment variable usage."""
        if directory is None:
            directory = self.webapp_dir
            
        found_variables = set()
        usage_details = []
        files_scanned = 0
        lines_scanned = 0
        
        # Find all Python files
        python_files = list(directory.rglob("*.py"))
        
        # Filter out virtual environments, migrations, and cache directories
        python_files = [
            f for f in python_files
            if not any(part in f.parts for part in [
                '.venv', 'venv', '__pycache__', '.git', 
                'migrations', 'node_modules', 'backups'
            ])
        ]
        
        for file_path in python_files:
            try:
                file_vars, file_usage, file_lines = self._scan_file(file_path)
                found_variables.update(file_vars)
                usage_details.extend(file_usage)
                files_scanned += 1
                lines_scanned += file_lines
                
            except Exception as e:
                print(f"Warning: Could not scan {file_path}: {e}")
        
        return ScanResult(
            found_variables=found_variables,
            usage_details=usage_details,
            files_scanned=files_scanned,
            lines_scanned=lines_scanned
        )
    
    def _scan_file(self, file_path: Path) -> Tuple[Set[str], List[EnvVarUsage], int]:
        """Scan a single Python file for environment variables."""
        found_vars = set()
        usage_details = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        for line_num, line in enumerate(lines, 1):
            line_vars = self._extract_env_vars_from_line(line, file_path, line_num)
            for usage in line_vars:
                found_vars.add(usage.var_name)
                usage_details.append(usage)
        
        return found_vars, usage_details, len(lines)
    
    def _extract_env_vars_from_line(self, line: str, file_path: Path, line_num: int) -> List[EnvVarUsage]:
        """Extract environment variables from a single line of code."""
        usages = []
        
        # Skip comments and strings that are likely not code
        stripped_line = line.strip()
        if stripped_line.startswith('#'):
            return usages
        
        # Check each pattern
        for pattern in self.env_patterns:
            matches = pattern.findall(line)
            for match in matches:
                # Determine usage type based on pattern
                usage_type = self._determine_usage_type(line, match)
                
                usages.append(EnvVarUsage(
                    var_name=match,
                    file_path=str(file_path.relative_to(self.webapp_dir)),
                    line_number=line_num,
                    context=line.strip(),
                    usage_type=usage_type
                ))
        
        return usages
    
    def _determine_usage_type(self, line: str, var_name: str) -> str:
        """Determine how the environment variable is being used."""
        if f"env('{var_name}'" in line or f'env("{var_name}"' in line:
            return 'env'
        elif 'os.environ' in line:
            return 'os.environ'
        elif f'settings.{var_name}' in line:
            return 'settings'
        elif 'FEATURE_FLAGS' in line:
            return 'feature_flag'
        else:
            return 'direct'
    
    def load_golden_variables(self) -> Set[str]:
        """Load variable names from the golden environment file."""
        if not self.golden_file.exists():
            print(f"Warning: Golden file not found: {self.golden_file}")
            return set()
        
        variables = set()
        
        with open(self.golden_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        var_name = line.split('=', 1)[0].strip()
                        if var_name and var_name.isidentifier():
                            variables.add(var_name)
                    except ValueError:
                        continue
        
        return variables
    
    def compare_with_golden(self, scan_result: ScanResult) -> ComparisonReport:
        """Compare scan results with golden environment file."""
        used_in_code = scan_result.found_variables
        defined_in_golden = self.load_golden_variables()
        
        missing_definitions = used_in_code - defined_in_golden
        unused_definitions = defined_in_golden - used_in_code
        properly_defined = used_in_code & defined_in_golden
        
        return ComparisonReport(
            used_in_code=used_in_code,
            defined_in_golden=defined_in_golden,
            missing_definitions=missing_definitions,
            unused_definitions=unused_definitions,
            properly_defined=properly_defined
        )
    
    def generate_usage_report(self, scan_result: ScanResult, comparison: ComparisonReport) -> str:
        """Generate a detailed usage report."""
        report = []
        
        report.append("=" * 80)
        report.append("ENVIRONMENT VARIABLE USAGE REPORT")
        report.append("=" * 80)
        report.append(f"Files scanned: {scan_result.files_scanned}")
        report.append(f"Lines scanned: {scan_result.lines_scanned}")
        report.append(f"Variables found: {len(scan_result.found_variables)}")
        report.append("")
        
        # Summary statistics
        report.append("SUMMARY:")
        report.append(f"  ✅ Properly defined: {len(comparison.properly_defined)}")
        report.append(f"  ❌ Missing definitions: {len(comparison.missing_definitions)}")
        report.append(f"  ⚠️  Unused definitions: {len(comparison.unused_definitions)}")
        report.append("")
        
        # Missing definitions (critical)
        if comparison.missing_definitions:
            report.append("❌ MISSING DEFINITIONS (used in code but not in env.gold):")
            report.append("-" * 60)
            for var_name in sorted(comparison.missing_definitions):
                report.append(f"  {var_name}")
                
                # Show where it's used
                usages = [u for u in scan_result.usage_details if u.var_name == var_name]
                for usage in usages[:3]:  # Show first 3 usages
                    report.append(f"    📍 {usage.file_path}:{usage.line_number} ({usage.usage_type})")
                    report.append(f"       {usage.context}")
                
                if len(usages) > 3:
                    report.append(f"    ... and {len(usages) - 3} more usages")
                report.append("")
        
        # Unused definitions (warning)
        if comparison.unused_definitions:
            report.append("⚠️  UNUSED DEFINITIONS (in env.gold but not used in code):")
            report.append("-" * 60)
            for var_name in sorted(comparison.unused_definitions):
                report.append(f"  {var_name}")
            report.append("")
        
        # Usage by type
        usage_by_type = {}
        for usage in scan_result.usage_details:
            if usage.usage_type not in usage_by_type:
                usage_by_type[usage.usage_type] = []
            usage_by_type[usage.usage_type].append(usage)
        
        report.append("USAGE BY TYPE:")
        report.append("-" * 40)
        for usage_type, usages in sorted(usage_by_type.items()):
            unique_vars = set(u.var_name for u in usages)
            report.append(f"  {usage_type}: {len(unique_vars)} variables, {len(usages)} usages")
        report.append("")
        
        # File-by-file breakdown
        usage_by_file = {}
        for usage in scan_result.usage_details:
            if usage.file_path not in usage_by_file:
                usage_by_file[usage.file_path] = []
            usage_by_file[usage.file_path].append(usage)
        
        report.append("USAGE BY FILE:")
        report.append("-" * 40)
        for file_path in sorted(usage_by_file.keys()):
            usages = usage_by_file[file_path]
            unique_vars = set(u.var_name for u in usages)
            report.append(f"  {file_path}: {len(unique_vars)} variables, {len(usages)} usages")
        
        return "\\n".join(report)
    
    def print_missing_variables(self, comparison: ComparisonReport, scan_result: ScanResult):
        """Print missing variables in a concise format."""
        if not comparison.missing_definitions:
            print("✅ All environment variables used in code are defined in env.gold")
            return
        
        print(f"❌ MISSING DEFINITIONS ({len(comparison.missing_definitions)} variables):")
        print("=" * 60)
        print("These variables are used in code but not defined in env.gold:")
        print("")
        
        for var_name in sorted(comparison.missing_definitions):
            print(f"🔍 {var_name}")
            
            # Show usage locations
            usages = [u for u in scan_result.usage_details if u.var_name == var_name]
            for usage in usages[:2]:  # Show first 2 usages
                print(f"   📍 {usage.file_path}:{usage.line_number}")
                print(f"      {usage.context}")
            
            if len(usages) > 2:
                print(f"   ... and {len(usages) - 2} more usages")
            print("")
        
        print("💡 ACTION REQUIRED:")
        print("   1. Add these variables to workflows/envs/env.gold")
        print("   2. Run: uv run python workflows/bin/sync-env-files.py local qa prod")
        print("   3. Update environment-specific values as needed")
    
    def print_unused_variables(self, comparison: ComparisonReport):
        """Print unused variables in a concise format."""
        if not comparison.unused_definitions:
            print("✅ All variables in env.gold are used in the codebase")
            return
        
        print(f"⚠️  UNUSED DEFINITIONS ({len(comparison.unused_definitions)} variables):")
        print("=" * 60)
        print("These variables are defined in env.gold but not used in code:")
        print("")
        
        for var_name in sorted(comparison.unused_definitions):
            print(f"❓ {var_name}")
        
        print("")
        print("💡 CONSIDER:")
        print("   - Remove unused variables from env.gold if they're truly not needed")
        print("   - Or verify if they should be used but are missing from code")


def main():
    """Main function to handle command line arguments and run scan."""
    parser = argparse.ArgumentParser(
        description="Scan codebase for environment variable usage",
        epilog="""
Examples:
  uv run python workflows/bin/scan-codebase.py                     # Full scan and comparison
  uv run python workflows/bin/scan-codebase.py --unused            # Show unused variables
  uv run python workflows/bin/scan-codebase.py --missing           # Show missing variables
  uv run python workflows/bin/scan-codebase.py --report            # Generate detailed report
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--unused',
        action='store_true',
        help='Show variables defined in env.gold but not used in code'
    )
    
    parser.add_argument(
        '--missing',
        action='store_true',
        help='Show variables used in code but not defined in env.gold'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed usage report'
    )
    
    parser.add_argument(
        '--directory',
        type=Path,
        help='Directory to scan (default: current webapp directory)'
    )
    
    args = parser.parse_args()
    
    scanner = CodebaseScanner()
    
    print("🔍 Scanning codebase for environment variable usage...")
    if args.directory:
        print(f"📁 Directory: {args.directory}")
    
    # Perform scan
    scan_result = scanner.scan_python_files(args.directory)
    comparison = scanner.compare_with_golden(scan_result)
    
    # Display results based on arguments
    if args.unused:
        scanner.print_unused_variables(comparison)
    elif args.missing:
        scanner.print_missing_variables(comparison, scan_result)
    elif args.report:
        report = scanner.generate_usage_report(scan_result, comparison)
        print(report)
    else:
        # Default: show summary and critical issues
        print(f"\\n📊 SCAN RESULTS:")
        print(f"  Files scanned: {scan_result.files_scanned}")
        print(f"  Variables found: {len(scan_result.found_variables)}")
        print(f"  ✅ Properly defined: {len(comparison.properly_defined)}")
        print(f"  ❌ Missing definitions: {len(comparison.missing_definitions)}")
        print(f"  ⚠️  Unused definitions: {len(comparison.unused_definitions)}")
        
        if comparison.missing_definitions:
            print("\\n" + "=" * 60)
            scanner.print_missing_variables(comparison, scan_result)
        
        if comparison.unused_definitions:
            print("\\n" + "=" * 60)
            scanner.print_unused_variables(comparison)
        
        if not comparison.missing_definitions and not comparison.unused_definitions:
            print("\\n🎉 Perfect! All environment variables are properly defined and used.")


if __name__ == "__main__":
    main()