"""
Unit tests for MarkdownStructureChunker
Test chunking functionality and output to JSON files

Usage:
    # Test with specific markdown file and output to data/output/
    python tests/unit/test_chunker.py --path data/raw/program/CNTT.md
    
    # Test with syllabus file
    python tests/unit/test_chunker.py --path "data/raw/syllabus/IS207 - Phát triển ứng dụng Web (2022-Rubric).md"
"""
import sys
import json
import asyncio
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, '/Users/admin/Documents/School/backend-support')

from app.utils.chunker import MarkdownStructureChunker


async def test_chunker_async(input_path: Path, output_dir: Path = None):
    """
    Test chunker with a markdown file and optionally save output (async version)
    
    Args:
        input_path: Path to markdown file
        output_dir: Directory to save output JSON (optional)
    """
    print(f"{'='*70}")
    print(f"Testing Chunker with: {input_path.name}")
    print(f"{'='*70}\n")
    
    # Check if file exists
    if not input_path.exists():
        print(f"❌ Error: File not found: {input_path}")
        return
    
    # Read markdown content
    print("📖 Reading markdown file...")
    with open(input_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    file_size = len(markdown_content)
    print(f"   File size: {file_size:,} characters\n")
    
    # Initialize chunker
    print("⚙️  Initializing MarkdownStructureChunker...")
    chunker = MarkdownStructureChunker()
    print(f"   Chunk size: {chunker.chunk_size}")
    print(f"   Chunk overlap: {chunker.chunk_overlap}\n")
    
    # Perform chunking (async with LLM table detection)
    print("🔧 Processing markdown (with LLM table detection)...")
    result = await chunker.chunk_markdown(
        text=markdown_content,
        metadata={'source': input_path.name}
    )
    
    sections = result['sections']
    chunks = result['chunks']
    
    # Display statistics
    print(f"✅ Chunking complete!")
    print(f"\n📊 Statistics:")
    print(f"   Total sections: {len(sections)}")
    print(f"   Total chunks: {len(chunks)}")
    
    # Analyze sections
    if sections:
        print(f"\n📑 Sections Analysis:")
        levels = {}
        for section in sections:
            level = section.get('level', 0)
            levels[level] = levels.get(level, 0) + 1
        
        for level in sorted(levels.keys()):
            print(f"   Level {level}: {levels[level]} sections")
        
        # Show sample sections
        print(f"\n   Sample sections (first 5):")
        for i, section in enumerate(sections[:5], 1):
            title = section['title']
            level = section['level']
            text_len = len(section['text'])
            has_tables = len(section.get('tables', []))
            print(f"   {i}. [H{level}] {title[:60]}... ({text_len} chars, {has_tables} tables)")
    
    # Analyze chunks
    if chunks:
        chunk_sizes = [len(chunk['text']) for chunk in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        min_size = min(chunk_sizes)
        max_size = max(chunk_sizes)
        
        print(f"\n📦 Chunks Analysis:")
        print(f"   Average size: {avg_size:.0f} chars")
        print(f"   Min size: {min_size} chars")
        print(f"   Max size: {max_size} chars")
        
        # Check for oversized chunks
        oversized = [i for i, size in enumerate(chunk_sizes, 1) if size > chunker.chunk_size]
        if oversized:
            print(f"   ⚠️  Oversized chunks (>{chunker.chunk_size}): {len(oversized)}")
            for idx in oversized[:5]:  # Show first 5
                print(f"      Chunk {idx}: {chunk_sizes[idx-1]} chars")
        else:
            print(f"   ✅ All chunks within size limit")
        
        # Show sample chunks
        print(f"\n   Sample chunks (first 3):")
        for i, chunk in enumerate(chunks[:3], 1):
            text_preview = chunk['text'][:100].replace('\n', ' ')
            text_len = len(chunk['text'])
            print(f"   {i}. {text_preview}... ({text_len} chars)")
    
    # Analyze tables
    total_tables = sum(len(section.get('tables', [])) for section in sections)
    if total_tables > 0:
        print(f"\n📊 Tables Analysis:")
        print(f"   Total tables found: {total_tables}")
        
        # Show sample tables
        tables_shown = 0
        for section in sections:
            tables = section.get('tables', [])
            if tables and tables_shown < 3:
                print(f"   In section: {section['title']}")
                for table in tables[:1]:  # Show first table
                    print(f"      - {table['num_rows']} rows x {table['num_columns']} cols")
                    if table['headers']:
                        headers_preview = ', '.join(table['headers'][:3])
                        print(f"      - Headers: {headers_preview}...")
                    tables_shown += 1
                    if tables_shown >= 3:
                        break
    
    # Save output if directory specified
    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate output filename
        output_filename = input_path.stem.lower().replace(' ', '_') + '.json'
        output_path = output_dir / output_filename
        
        print(f"\n💾 Saving output to: {output_path}")
        
        # Prepare output data (without embeddings)
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
        print(f"   ✅ Saved: {output_size:,} bytes")
        print(f"   📁 Location: {output_path.absolute()}")
    
    print(f"\n{'='*70}")
    print("✅ Test complete!")
    print(f"{'='*70}\n")


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Test MarkdownStructureChunker and output results to JSON',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test program file
  python tests/unit/test_chunker.py --path data/raw/program/CNTT.md
  
  # Test syllabus file
  python tests/unit/test_chunker.py --path "data/raw/syllabus/IS207 - Phát triển ứng dụng Web (2022-Rubric).md"
  
  # Specify custom output directory
  python tests/unit/test_chunker.py --path data/raw/program/KTMT.md --output data/output
        """
    )
    
    parser.add_argument(
        '--path',
        type=str,
        required=True,
        help='Path to markdown file to test'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/output',
        help='Output directory for JSON file (default: data/output)'
    )
    
    args = parser.parse_args()
    
    # Convert to Path objects
    input_path = Path(args.path)
    output_dir = Path(args.output) if args.output else None
    
    # Run test with asyncio
    asyncio.run(test_chunker_async(input_path, output_dir))


if __name__ == "__main__":
    main()
