#!/usr/bin/env python3
"""
Script to compare total response times across different pipeline evaluation files.
Usage: python scripts/compare_pipeline_times.py [--dir OUTPUT_DIR] [--files FILE1 FILE2 ...]
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple


def load_evaluation_file(filepath: Path) -> Dict:
    """Load a JSON evaluation file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_total_time(data: Dict) -> Tuple[float, int, float]:
    """
    Calculate total time from evaluation results.
    Returns: (total_time_ms, query_count, avg_time_ms)
    """
    results = data.get('results', [])
    total_time = 0.0
    count = 0
    
    for result in results:
        metadata = result.get('metadata', {})
        time_ms = metadata.get('total_time_ms', 0)
        if time_ms:
            total_time += time_ms
            count += 1
    
    avg_time = total_time / count if count > 0 else 0
    return total_time, count, avg_time


def format_time(ms: float) -> str:
    """Format milliseconds to a human-readable string."""
    if ms >= 1000:
        return f"{ms/1000:.2f}s"
    return f"{ms:.2f}ms"


def compare_pipelines(files: List[Path]) -> None:
    """Compare total times across multiple pipeline files."""
    results = []
    
    for filepath in files:
        try:
            data = load_evaluation_file(filepath)
            pipeline_name = data.get('pipeline', filepath.stem)
            total_time, query_count, avg_time = calculate_total_time(data)
            
            results.append({
                'file': filepath.name,
                'pipeline': pipeline_name,
                'total_time_ms': total_time,
                'query_count': query_count,
                'avg_time_ms': avg_time
            })
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
    
    if not results:
        print("No valid evaluation files found.")
        return
    
    # Sort by total time
    results.sort(key=lambda x: x['total_time_ms'])
    
    # Print comparison table
    print("\n" + "=" * 80)
    print("PIPELINE TIME COMPARISON")
    print("=" * 80)
    print(f"{'File':<50} {'Pipeline':<12} {'Queries':<8} {'Total Time':<12} {'Avg Time':<10}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['file']:<50} {r['pipeline']:<12} {r['query_count']:<8} "
              f"{format_time(r['total_time_ms']):<12} {format_time(r['avg_time_ms']):<10}")
    
    print("-" * 80)
    
    # Summary statistics
    if len(results) > 1:
        fastest = results[0]
        slowest = results[-1]
        speedup = slowest['total_time_ms'] / fastest['total_time_ms'] if fastest['total_time_ms'] > 0 else 0
        
        print(f"\n📊 Summary:")
        print(f"   Fastest: {fastest['file']} ({format_time(fastest['total_time_ms'])})")
        print(f"   Slowest: {slowest['file']} ({format_time(slowest['total_time_ms'])})")
        print(f"   Speedup: {speedup:.2f}x faster")
    
    print()


def find_latest_files_by_pipeline(output_dir: Path, pipeline_types: List[str] = None) -> List[Path]:
    """Find the latest evaluation file for each pipeline type."""
    if pipeline_types is None:
        pipeline_types = ['naive', 'pipeline', 'ragas']
    
    latest_files = []
    
    for ptype in pipeline_types:
        # Find files matching the pipeline type
        pattern = f"{ptype}_evaluation_*.json"
        matching_files = list(output_dir.glob(pattern))
        
        if matching_files:
            # Sort by modification time and get the latest
            latest = max(matching_files, key=lambda p: p.stat().st_mtime)
            latest_files.append(latest)
    
    return latest_files


def main():
    parser = argparse.ArgumentParser(description='Compare pipeline evaluation times')
    parser.add_argument('--dir', '-d', type=str, 
                        default='tests/output',
                        help='Directory containing evaluation files')
    parser.add_argument('--files', '-f', nargs='+', type=str,
                        help='Specific files to compare')
    parser.add_argument('--pattern', '-p', type=str,
                        help='Glob pattern to match files (e.g., "*_20251227_*.json")')
    parser.add_argument('--pipelines', nargs='+', type=str,
                        default=['naive', 'pipeline', 'ragas'],
                        help='Pipeline types to compare')
    
    args = parser.parse_args()
    
    # Determine base directory
    script_dir = Path(__file__).parent.parent
    output_dir = script_dir / args.dir
    
    if not output_dir.exists():
        print(f"Error: Directory {output_dir} does not exist")
        return
    
    # Get files to compare
    if args.files:
        files = [output_dir / f if not Path(f).is_absolute() else Path(f) for f in args.files]
    elif args.pattern:
        files = list(output_dir.glob(args.pattern))
    else:
        files = find_latest_files_by_pipeline(output_dir, args.pipelines)
    
    if not files:
        print("No evaluation files found to compare.")
        return
    
    print(f"\n📁 Comparing {len(files)} evaluation file(s) from: {output_dir}")
    compare_pipelines(files)


if __name__ == '__main__':
    main()
