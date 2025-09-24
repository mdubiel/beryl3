#!/usr/bin/env python3
"""
Environment Comparison Script

Compare environment configurations between QA and Production to ensure consistency
while highlighting expected differences.

Usage:
    uv run python workflows/bin/compare-envs.py qa prod              # Compare QA vs PROD
    uv run python workflows/bin/compare-envs.py --report             # Generate detailed report
    uv run python workflows/bin/compare-envs.py --matrix             # Show comparison matrix
"""

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class EnvDifference:
    """Represents a difference between environments."""
    var_name: str
    env1_value: str
    env2_value: str
    is_expected: bool
    reason: str


@dataclass
class ComparisonMatrix:
    """Result of comparing two environments."""
    env1_name: str
    env2_name: str
    identical: Dict[str, str]           # Variables with same values
    different: List[EnvDifference]      # Variables with different values
    env1_only: Dict[str, str]          # Variables only in env1
    env2_only: Dict[str, str]          # Variables only in env2
    expected_differences: List[EnvDifference]    # Expected differences
    unexpected_differences: List[EnvDifference]  # Unexpected differences


class EnvironmentComparison:
    """Compares environment configurations."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.envs_dir = self.project_root / "envs"
        
        # Define expected differences between environments
        self.expected_different_patterns = {
            # Domain and URL differences
            'SITE_DOMAIN': 'Different domains for each environment',
            'ALLOWED_HOSTS': 'Environment-specific host configurations', 
            'CSRF_TRUSTED_ORIGINS': 'Environment-specific trusted origins',
            'DEFAULT_FROM_EMAIL': 'Environment-specific email addresses',
            
            # Google Cloud differences
            'GCS_BUCKET_NAME': 'Environment-specific storage buckets',
            'GCS_PROJECT_ID': 'Different Google Cloud projects',
            'GCS_CREDENTIALS_PATH': 'Environment-specific credential paths',
            
            # Database differences
            'PG_DB': 'Environment-specific database names',
            'PG_USER': 'Environment-specific database users',
            'PG_PASSWORD': 'Environment-specific database passwords',
            'PG_HOST': 'Environment-specific database hosts',
            
            # Email differences
            'EMAIL_HOST_PASSWORD': 'Environment-specific API keys',
            
            # Environment identification
            'ENVIRONMENT': 'Environment name identifier',
            'DEPLOYMENT_ENVIRONMENT': 'Deployment environment identifier',
            'SITE_NAME': 'Environment-specific site names',
            
            # Monitoring differences
            
            # External URLs
            'EXTERNAL_DB_URL': 'Environment-specific database admin URLs',
            'EXTERNAL_MONITORING_URL': 'Environment-specific monitoring URLs',
            
            # Static/Media URLs
            'STATIC_URL': 'Environment-specific static file URLs',
            'MEDIA_URL': 'Environment-specific media file URLs',
            
            # Performance tuning
            'POST_OFFICE_BATCH_SIZE': 'Environment-specific performance tuning',
            'POST_OFFICE_BATCH_TIMEOUT': 'Environment-specific timeout settings',
            'POST_OFFICE_MAX_RETRIES': 'Environment-specific retry policies',
            'POST_OFFICE_RETRY_INTERVAL': 'Environment-specific retry intervals',
        }
        
        # Variables that should typically be identical between environments
        self.should_be_identical = {
            'DEBUG',
            'DB_ENGINE', 
            'EMAIL_HOST',
            'EMAIL_PORT',
            'EMAIL_USE_TLS',
            'EMAIL_HOST_USER',
            'USE_GCS_STORAGE',
            'USE_INBUCKET',
            'LOKI_ENABLED',
            'USE_GOOGLE_CLOUD_LOGGING',
            'APPLICATION_ACTIVITY_LOGGING',
            'GCS_LOCATION',
            'INBUCKET_WEB_PORT',
            'INBUCKET_SMTP_PORT',
            'GOOGLE_CLOUD_LOGGING_RESOURCE_TYPE',
            'EXTERNAL_RESEND_URL',
            'SITE_ID',
        }
    
    def load_environment_file(self, env_name: str) -> Dict[str, str]:
        """Load an environment file."""
        env_file = self.envs_dir / f"{env_name}.env"
        variables = {}
        
        if not env_file.exists():
            print(f"Warning: Environment file not found: {env_file}")
            return variables
        
        with open(env_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    try:
                        name, value = line.split('=', 1)
                        variables[name.strip()] = value
                    except ValueError:
                        print(f"Warning: Could not parse line {line_num} in {env_file}: {line}")
                        
        return variables
    
    def compare_environments(self, env1_name: str, env2_name: str) -> ComparisonMatrix:
        """Compare two environments."""
        env1_vars = self.load_environment_file(env1_name)
        env2_vars = self.load_environment_file(env2_name)
        
        all_vars = set(env1_vars.keys()) | set(env2_vars.keys())
        
        identical = {}
        different = []
        env1_only = {}
        env2_only = {}
        
        for var_name in all_vars:
            env1_value = env1_vars.get(var_name, '<missing>')
            env2_value = env2_vars.get(var_name, '<missing>')
            
            if var_name in env1_vars and var_name in env2_vars:
                if env1_value == env2_value:
                    identical[var_name] = env1_value
                else:
                    is_expected = self._is_difference_expected(var_name, env1_value, env2_value)
                    reason = self.expected_different_patterns.get(var_name, 'Unexpected difference')
                    
                    different.append(EnvDifference(
                        var_name=var_name,
                        env1_value=env1_value,
                        env2_value=env2_value,
                        is_expected=is_expected,
                        reason=reason
                    ))
            elif var_name in env1_vars:
                env1_only[var_name] = env1_value
            else:
                env2_only[var_name] = env2_value
        
        # Categorize differences
        expected_differences = [d for d in different if d.is_expected]
        unexpected_differences = [d for d in different if not d.is_expected]
        
        return ComparisonMatrix(
            env1_name=env1_name,
            env2_name=env2_name,
            identical=identical,
            different=different,
            env1_only=env1_only,
            env2_only=env2_only,
            expected_differences=expected_differences,
            unexpected_differences=unexpected_differences
        )
    
    def _is_difference_expected(self, var_name: str, value1: str, value2: str) -> bool:
        """Determine if a difference between environments is expected."""
        # Check if this variable is in our expected differences list
        if var_name in self.expected_different_patterns:
            return True
        
        # Check if this variable should be identical
        if var_name in self.should_be_identical:
            return False
        
        # For variables not explicitly categorized, assume difference is expected
        # (This allows for environment-specific configurations we haven't categorized)
        return True
    
    def print_comparison_summary(self, matrix: ComparisonMatrix):
        """Print a summary of the comparison."""
        total_vars = (len(matrix.identical) + len(matrix.different) + 
                     len(matrix.env1_only) + len(matrix.env2_only))
        
        print(f"\\n{'='*70}")
        print(f"ENVIRONMENT COMPARISON: {matrix.env1_name.upper()} vs {matrix.env2_name.upper()}")
        print(f"{'='*70}")
        print(f"Total variables compared: {total_vars}")
        print(f"  ✅ Identical: {len(matrix.identical)}")
        print(f"  🔄 Different: {len(matrix.different)}")
        print(f"    └─ Expected: {len(matrix.expected_differences)}")
        print(f"    └─ Unexpected: {len(matrix.unexpected_differences)}")
        print(f"  📍 Only in {matrix.env1_name}: {len(matrix.env1_only)}")
        print(f"  📍 Only in {matrix.env2_name}: {len(matrix.env2_only)}")
        
        if matrix.unexpected_differences:
            print(f"\\n⚠️  UNEXPECTED DIFFERENCES ({len(matrix.unexpected_differences)}):")
            print("-" * 50)
            for diff in matrix.unexpected_differences:
                print(f"  🔍 {diff.var_name}")
                print(f"     {matrix.env1_name}: {diff.env1_value}")
                print(f"     {matrix.env2_name}: {diff.env2_value}")
                print()
        
        if matrix.env1_only or matrix.env2_only:
            print(f"\\n📍 ENVIRONMENT-SPECIFIC VARIABLES:")
            print("-" * 50)
            
            if matrix.env1_only:
                print(f"  Only in {matrix.env1_name}:")
                for var_name, value in matrix.env1_only.items():
                    print(f"    - {var_name}={value}")
                print()
            
            if matrix.env2_only:
                print(f"  Only in {matrix.env2_name}:")
                for var_name, value in matrix.env2_only.items():
                    print(f"    - {var_name}={value}")
    
    def print_detailed_report(self, matrix: ComparisonMatrix):
        """Print a detailed comparison report."""
        print(f"\\n{'='*80}")
        print(f"DETAILED ENVIRONMENT COMPARISON REPORT")
        print(f"{'='*80}")
        print(f"Environments: {matrix.env1_name.upper()} vs {matrix.env2_name.upper()}")
        print(f"Generated: {self._get_timestamp()}")
        print()
        
        # Expected differences
        if matrix.expected_differences:
            print(f"✅ EXPECTED DIFFERENCES ({len(matrix.expected_differences)}):")
            print("-" * 60)
            for diff in matrix.expected_differences:
                print(f"  📋 {diff.var_name}")
                print(f"     Reason: {diff.reason}")
                print(f"     {matrix.env1_name}: {diff.env1_value}")
                print(f"     {matrix.env2_name}: {diff.env2_value}")
                print()
        
        # Unexpected differences
        if matrix.unexpected_differences:
            print(f"⚠️  UNEXPECTED DIFFERENCES ({len(matrix.unexpected_differences)}):")
            print("-" * 60)
            for diff in matrix.unexpected_differences:
                print(f"  🚨 {diff.var_name}")
                print(f"     This variable should typically be identical between environments")
                print(f"     {matrix.env1_name}: {diff.env1_value}")
                print(f"     {matrix.env2_name}: {diff.env2_value}")
                print()
        
        # Identical variables (brief list)
        if matrix.identical:
            print(f"✅ IDENTICAL VARIABLES ({len(matrix.identical)}):")
            print("-" * 60)
            identical_names = sorted(matrix.identical.keys())
            for i in range(0, len(identical_names), 4):
                row = identical_names[i:i+4]
                print(f"  {', '.join(row)}")
            print()
        
        # Variables only in one environment
        if matrix.env1_only or matrix.env2_only:
            print(f"📍 ENVIRONMENT-SPECIFIC VARIABLES:")
            print("-" * 60)
            
            if matrix.env1_only:
                print(f"  Only in {matrix.env1_name.upper()}:")
                for var_name, value in sorted(matrix.env1_only.items()):
                    print(f"    {var_name}={value}")
                print()
            
            if matrix.env2_only:
                print(f"  Only in {matrix.env2_name.upper()}:")
                for var_name, value in sorted(matrix.env2_only.items()):
                    print(f"    {var_name}={value}")
        
        # Recommendations
        print(f"\\n💡 RECOMMENDATIONS:")
        print("-" * 60)
        
        if matrix.unexpected_differences:
            print("  1. Review unexpected differences - these may indicate configuration drift")
            print("  2. Verify if unexpected differences are intentional")
            print("  3. Update comparison patterns if differences are expected")
        
        if matrix.env1_only or matrix.env2_only:
            print("  4. Review environment-specific variables")
            print("  5. Ensure both environments have all required variables")
        
        if not matrix.unexpected_differences and not matrix.env1_only and not matrix.env2_only:
            print("  🎉 Environments are properly aligned!")
    
    def print_comparison_matrix(self, matrix: ComparisonMatrix):
        """Print a comparison matrix showing all variables side by side."""
        all_vars = set()
        all_vars.update(matrix.identical.keys())
        all_vars.update(d.var_name for d in matrix.different)
        all_vars.update(matrix.env1_only.keys())
        all_vars.update(matrix.env2_only.keys())
        
        print(f"\\n{'='*100}")
        print(f"COMPARISON MATRIX: {matrix.env1_name.upper()} vs {matrix.env2_name.upper()}")
        print(f"{'='*100}")
        
        # Header
        print(f"{'Variable':<30} {'Status':<12} {matrix.env1_name.upper():<25} {matrix.env2_name.upper():<25}")
        print("-" * 100)
        
        for var_name in sorted(all_vars):
            env1_value = matrix.identical.get(var_name, 
                         matrix.env1_only.get(var_name, 
                         next((d.env1_value for d in matrix.different if d.var_name == var_name), '<missing>')))
            
            env2_value = matrix.identical.get(var_name,
                         matrix.env2_only.get(var_name,
                         next((d.env2_value for d in matrix.different if d.var_name == var_name), '<missing>')))
            
            # Determine status
            if var_name in matrix.identical:
                status = "✅ SAME"
            elif var_name in matrix.env1_only:
                status = f"📍 {matrix.env1_name.upper()}"
            elif var_name in matrix.env2_only:
                status = f"📍 {matrix.env2_name.upper()}"
            else:
                diff = next(d for d in matrix.different if d.var_name == var_name)
                status = "✅ DIFF" if diff.is_expected else "⚠️ DIFF"
            
            # Truncate long values
            env1_display = env1_value[:20] + "..." if len(env1_value) > 23 else env1_value
            env2_display = env2_value[:20] + "..." if len(env2_value) > 23 else env2_value
            
            print(f"{var_name:<30} {status:<12} {env1_display:<25} {env2_display:<25}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for reports."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def main():
    """Main function to handle command line arguments and run comparison."""
    parser = argparse.ArgumentParser(
        description="Compare environment configurations",
        epilog="""
Examples:
  uv run python workflows/bin/compare-envs.py qa prod              # Compare QA vs PROD
  uv run python workflows/bin/compare-envs.py --report qa prod     # Detailed report
  uv run python workflows/bin/compare-envs.py --matrix qa prod     # Comparison matrix
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'environments',
        nargs='*',
        default=['qa', 'prod'],
        help='Two environments to compare (default: qa prod)'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed comparison report'
    )
    
    parser.add_argument(
        '--matrix',
        action='store_true',
        help='Show side-by-side comparison matrix'
    )
    
    args = parser.parse_args()
    
    if len(args.environments) != 2:
        print("Error: Please specify exactly two environments to compare")
        parser.print_help()
        sys.exit(1)
    
    env1, env2 = args.environments
    
    comparator = EnvironmentComparison()
    
    print(f"🔍 Comparing {env1.upper()} vs {env2.upper()} environments...")
    
    # Perform comparison
    matrix = comparator.compare_environments(env1, env2)
    
    # Display results based on arguments
    if args.matrix:
        comparator.print_comparison_matrix(matrix)
    elif args.report:
        comparator.print_detailed_report(matrix)
    else:
        comparator.print_comparison_summary(matrix)
    
    # Exit code based on unexpected differences
    if matrix.unexpected_differences:
        print(f"\\n⚠️  Warning: {len(matrix.unexpected_differences)} unexpected differences found")
        sys.exit(1)
    else:
        print(f"\\n✅ Environment comparison completed successfully")


if __name__ == "__main__":
    main()