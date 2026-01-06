"""
Batch test chunker for multiple markdown files
Process all files in a folder and output to data/output/

Usage:
    # Test all program files
    python tests/unit/test_chunker_batch.py --folder data/raw/program
    
    # Test all syllabus files
    python tests/unit/test_chunker_batch.py --folder data/raw/syllabus
    
    # Limit number of files
    python tests/unit/test_chunker_batch.py --folder data/raw/syllabus --max-files 5
"""
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, '/Users/admin/Documents/School/backend-support')

from app.utils.chunker import MarkdownStructureChunker


async def test_batch(folder_path: Path, output_dir: Path, max_files: int = None):
    """
    Batch test chunker with multiple markdown files
    
    Args:
        folder_path: Folder containing markdown files
        output_dir: Directory to save output JSON files
        max_files: Maximum number of files to process
    """
    print(f"{'='*70}")
    print(f"Batch Testing Chunker")
    print(f"{'='*70}")
    print(f"Input folder: {folder_path}")
    print(f"Output folder: {output_dir}")
    print(f"{'='*70}\n")
    
    # Find all markdown files
    markdown_files = sorted(folder_path.glob("*.md"))
    
    if not markdown_files:
        print(f"❌ No markdown files found in {folder_path}")
        return
    
    # Limit files if specified
    if max_files:
        markdown_files = markdown_files[:max_files]
        print(f"📝 Limited to first {max_files} files\n")
    
    print(f"📁 Found {len(markdown_files)} markdown files\n")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize chunker
    chunker = MarkdownStructureChunker()
    
    # Track statistics
    total_stats = {
        'files_processed': 0,
        'files_failed': 0,
        'total_sections': 0,
        'total_chunks': 0,
        'total_tables': 0,
        'total_input_size': 0,
        'total_output_size': 0,
        'start_time': datetime.now()
    }
    
    results = []
    
    # Process each file
    for idx, input_path in enumerate(markdown_files, 1):
        print(f"[{idx}/{len(markdown_files)}] Processing: {input_path.name}")
        
        try:
            # Read markdown
            with open(input_path, 'r', encoding='utf-8') as f:
                markdown_content = f.read()
            
            file_size = len(markdown_content)
            total_stats['total_input_size'] += file_size
            
            # Chunk markdown (async with LLM table detection)
            result = await chunker.chunk_markdown(
                text=markdown_content,
                metadata={'source': input_path.name}
            )
            
            sections = result['sections']
            chunks = result['chunks']
            total_tables = sum(len(s.get('tables', [])) for s in sections)
            
            # Update statistics
            total_stats['files_processed'] += 1
            total_stats['total_sections'] += len(sections)
            total_stats['total_chunks'] += len(chunks)
            total_stats['total_tables'] += total_tables
            
            # Generate output filename
            output_filename = input_path.stem.lower().replace(' ', '_').replace('(', '').replace(')', '') + '.json'
            output_path = output_dir / output_filename
            
            # Prepare output data
            output_data = {
                'metadata': {
                    'source_file': input_path.name,
                    'source_path': str(input_path),
                    'file_size': file_size,
                    'total_sections': len(sections),
                    'total_chunks': len(chunks),
                    'total_tables': total_tables,
                },
                'sections': sections,
                'chunks': chunks
            }
            
            # Save to JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            output_size = output_path.stat().st_size
            total_stats['total_output_size'] += output_size
            
            # Store result
            results.append({
                'file': input_path.name,
                'output': output_filename,
                'sections': len(sections),
                'chunks': len(chunks),
                'tables': total_tables,
                'input_size': file_size,
                'output_size': output_size
            })
            
            print(f"   ✅ {len(sections)} sections, {len(chunks)} chunks, {total_tables} tables")
            print(f"   💾 Saved to: {output_filename} ({output_size:,} bytes)\n")
            
        except Exception as e:
            total_stats['files_failed'] += 1
            print(f"   ❌ Error: {e}\n")
            import traceback
            traceback.print_exc()
    
    # Calculate summary
    total_stats['end_time'] = datetime.now()
    duration = (total_stats['end_time'] - total_stats['start_time']).total_seconds()
    
    # Print summary
    print(f"\n{'='*70}")
    print("📊 BATCH PROCESSING SUMMARY")
    print(f"{'='*70}")
    print(f"Files processed: {total_stats['files_processed']}/{len(markdown_files)}")
    print(f"Files failed: {total_stats['files_failed']}")
    print(f"Total sections: {total_stats['total_sections']:,}")
    print(f"Total chunks: {total_stats['total_chunks']:,}")
    print(f"Total tables: {total_stats['total_tables']:,}")
    print(f"Total input size: {total_stats['total_input_size']:,} bytes ({total_stats['total_input_size']/1024:.1f} KB)")
    print(f"Total output size: {total_stats['total_output_size']:,} bytes ({total_stats['total_output_size']/1024:.1f} KB)")
    print(f"Processing time: {duration:.2f} seconds")
    print(f"{'='*70}")
    
    # Print detailed results table
    if results:
        print(f"\n{'='*70}")
        print("📋 DETAILED RESULTS")
        print(f"{'='*70}")
        print(f"{'File':<40} {'Sections':<10} {'Chunks':<10} {'Tables':<10}")
        print(f"{'-'*70}")
        for r in results:
            print(f"{r['file'][:39]:<40} {r['sections']:<10} {r['chunks']:<10} {r['tables']:<10}")
        print(f"{'='*70}\n")
    
    # Save summary
    summary_path = output_dir / '_batch_summary.json'
    summary_data = {
        'timestamp': datetime.now().isoformat(),
        'input_folder': str(folder_path),
        'output_folder': str(output_dir),
        'statistics': {
            'files_processed': total_stats['files_processed'],
            'files_failed': total_stats['files_failed'],
            'total_sections': total_stats['total_sections'],
            'total_chunks': total_stats['total_chunks'],
            'total_tables': total_stats['total_tables'],
            'total_input_size': total_stats['total_input_size'],
            'total_output_size': total_stats['total_output_size'],
            'duration_seconds': duration
        },
        'results': results
    }
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)
    
    print(f"📄 Summary saved to: {summary_path}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Batch test MarkdownStructureChunker on multiple files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test all program files
  python tests/unit/test_chunker_batch.py --folder data/raw/program
  
  # Test all syllabus files
  python tests/unit/test_chunker_batch.py --folder data/raw/syllabus
  
  # Test with custom output directory
  python tests/unit/test_chunker_batch.py --folder data/raw/syllabus --output data/test_output
  
  # Limit to 5 files
  python tests/unit/test_chunker_batch.py --folder data/raw/syllabus --max-files 5
        """
    )
    
    parser.add_argument(
        '--folder',
        type=str,
        required=True,
        help='Folder containing markdown files to test'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/output',
        help='Output directory for JSON files (default: data/output)'
    )
    
    parser.add_argument(
        '--max-files',
        type=int,
        default=None,
        help='Maximum number of files to process'
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    folder_path = Path(args.folder)
    output_dir = Path(args.output)
    
    # Check if folder exists
    if not folder_path.exists():
        print(f"❌ Error: Folder not found: {folder_path}")
        return
    
    # Run batch test with asyncio
    asyncio.run(test_batch(folder_path, output_dir, args.max_files))


if __name__ == "__main__":
    main()
