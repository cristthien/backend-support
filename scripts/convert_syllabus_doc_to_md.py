"""
Script để convert các file DOC và DOCX thành Markdown và lưu vào folder syllabus_modified.

Requirements:
- pypandoc: pip install pypandoc
- python-docx: pip install python-docx (optional, for better .doc support)

Note: For .doc files (old Word format), you have two options:
1. Install LibreOffice (recommended): brew install --cask libreoffice
2. Manually convert .doc to .docx files first

Usage:
    python scripts/convert_docs_to_md.py --input <input_folder> --output <output_folder>
    
    Hoặc sử dụng default paths:
    python scripts/convert_docs_to_md.py
"""

import os
import sys
import argparse
import re
from pathlib import Path
from typing import List, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    import pypandoc
except ImportError:
    logger.error("pypandoc chưa được cài đặt. Vui lòng chạy: pip install pypandoc")
    sys.exit(1)


def find_doc_files(input_folder: Path) -> List[Path]:
    """
    Tìm tất cả các file .doc và .docx trong folder.
    
    Args:
        input_folder: Thư mục chứa các file DOC/DOCX
        
    Returns:
        Danh sách các file path
    """
    doc_files = []
    
    # Tìm file .docx
    doc_files.extend(input_folder.glob("**/*.docx"))
    
    # Tìm file .doc
    doc_files.extend(input_folder.glob("**/*.doc"))
    
    # Filter out temporary files (bắt đầu với ~$)
    doc_files = [f for f in doc_files if not f.name.startswith("~$")]
    
    return sorted(doc_files)


def extract_course_info_from_table(lines: list, course_code: str) -> tuple:
    """
    Extract course name from the THÔNG TIN CHUNG table.
    
    Args:
        lines: All lines of the document
        course_code: Course code extracted from filename
        
    Returns:
        Tuple of (course_name_vi, course_name_en)
    """
    course_name_vi = None
    course_name_en = None
    
    # Look for the table rows with course name
    for i, line in enumerate(lines):
        # Look for "Tên môn học (tiếng Việt):" in table
        if re.search(r'Tên môn học.*tiếng Việt', line, re.IGNORECASE):
            # Check next few lines for the Vietnamese name
            for j in range(i, min(i + 5, len(lines))):
                # Look for text in ** markers or after |
                match = re.search(r'\|\s*\*\*(.+?)\*\*', lines[j])
                if match:
                    course_name_vi = match.group(1).strip()
                    break
        
        # Look for "Tên môn học (tiếng Anh):" in table
        if re.search(r'Tên môn học.*tiếng Anh', line, re.IGNORECASE):
            # Check next few lines for the English name
            for j in range(i, min(i + 5, len(lines))):
                match = re.search(r'\|\s*\*\*(.+?)\*\*', lines[j])
                if match:
                    course_name_en = match.group(1).strip()
                    break
        
        # Stop if we've passed the first table
        if course_name_vi and course_name_en:
            break
    
    return course_name_vi, course_name_en


def convert_grid_table_to_pipe(table_lines: List[str]) -> List[str]:
    """
    Convert grid table format to GFM pipe table format.
    
    Grid table example:
    +---+---+
    | A | B |
    +===+===+
    | 1 | 2 |
    +---+---+
    
    Converts to:
    | A | B |
    | --- | --- |
    | 1 | 2 |
    
    Args:
        table_lines: Lines of grid table
        
    Returns:
        Lines of pipe table
    """
    if not table_lines:
        return []
    
    pipe_lines = []
    rows = []
    current_row = []
    
    for line in table_lines:
        stripped = line.strip()
        
        # Skip separator lines (lines with +, -, =, :)
        if re.match(r'^[\+\-\=\:]+$', stripped):
            # If we have accumulated cells, this ends a row
            if current_row:
                rows.append(current_row)
                current_row = []
            continue
        
        # Process cell lines (lines starting with |)
        if stripped.startswith('|') and stripped.endswith('|'):
            # Extract cells between | delimiters
            cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
            
            if not current_row:
                # First line of this row
                current_row = cells
            else:
                # Multi-line cell content - append to current row
                for i, cell in enumerate(cells):
                    if i < len(current_row) and cell:
                        current_row[i] += ' ' + cell
    
    # Add last row if exists
    if current_row:
        rows.append(current_row)
    
    if not rows:
        return []
    
    # Build pipe table
    # First row is header
    if rows:
        header = rows[0]
        pipe_lines.append('| ' + ' | '.join(header) + ' |')
        
        # Separator line
        separator = '| ' + ' | '.join(['---'] * len(header)) + ' |'
        pipe_lines.append(separator)
        
        # Data rows
        for row in rows[1:]:
            # Pad row to match header length
            while len(row) < len(header):
                row.append('')
            pipe_lines.append('| ' + ' | '.join(row[:len(header)]) + ' |')
    
    return pipe_lines


def detect_and_convert_tables(content: str) -> str:
    """
    Detect grid tables in content and convert them to GFM pipe tables.
    
    Args:
        content: Markdown content with possible grid tables
        
    Returns:
        Content with grid tables converted to pipe tables
    """
    lines = content.split('\n')
    converted_lines = []
    in_grid_table = False
    table_buffer = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        
        # Detect start of grid table (line with +---+ pattern)
        if re.match(r'^[\+\-\=\:]+[\+\-\=\:]+', stripped) and not in_grid_table:
            in_grid_table = True
            table_buffer = [line]
            i += 1
            continue
        
        # Collect grid table lines
        if in_grid_table:
            # Check if still in table
            if (stripped.startswith('|') or 
                re.match(r'^[\+\-\=\:]+', stripped) or
                not stripped):  # Empty lines within table
                table_buffer.append(line)
                i += 1
                
                # Check if this is the last line of table
                # (ends with +---+ and next line doesn't start with | or +)
                if (re.match(r'^[\+\-\=\:]+', stripped) and 
                    (i >= len(lines) or 
                     (not lines[i].strip().startswith('|') and 
                      not re.match(r'^[\+\-\=\:]+', lines[i].strip())))):
                    # End of table - convert it
                    pipe_table = convert_grid_table_to_pipe(table_buffer)
                    converted_lines.extend(pipe_table)
                    converted_lines.append('')  # Add blank line after table
                    in_grid_table = False
                    table_buffer = []
                continue
            else:
                # Not a table line anymore - convert accumulated table
                pipe_table = convert_grid_table_to_pipe(table_buffer)
                converted_lines.extend(pipe_table)
                converted_lines.append('')
                in_grid_table = False
                table_buffer = []
                # Don't increment i, process this line normally
        
        # Normal line (not in grid table)
        if not in_grid_table:
            converted_lines.append(line)
            i += 1
    
    # Handle any remaining table buffer
    if table_buffer:
        pipe_table = convert_grid_table_to_pipe(table_buffer)
        converted_lines.extend(pipe_table)
    
    return '\n'.join(converted_lines)


def clean_markdown_content(content: str, filename: str) -> str:
    """
    Clean markdown content by:
    1. Converting grid tables to GFM pipe tables
    2. Extracting course code and name from filename or content
    3. Removing everything before first section heading
    4. Creating H1 with course code and name
    5. Converting numbered headings to H2
    6. Removing blockquote markers (>) from content
    
    Args:
        content: Original markdown content
        filename: Source filename (to extract course code)
        
    Returns:
        Cleaned markdown content
    """
    # First, convert grid tables to pipe tables
    content = detect_and_convert_tables(content)
    lines = content.split('\n')
    
    # Extract course code from filename
    # Format: "IS214 - QuanTriChuoiCungUng.md" -> "IS214"
    course_code = None
    course_name = None
    
    # Try to extract from filename first
    filename_match = re.match(r'^([A-Z]{2}\d{3})\s*-\s*(.+)\.md$', filename)
    if filename_match:
        course_code = filename_match.group(1)
    
    # Try to extract course name from THÔNG TIN CHUNG table
    course_name_vi, course_name_en = extract_course_info_from_table(lines, course_code)
    
    if course_name_vi:
        course_name = course_name_vi.upper()
    elif course_name_en:
        course_name = course_name_en.upper()
    
    # Fallback: Find course name from content with ** markers
    if not course_name and course_code:
        for i, line in enumerate(lines):
            # Look for pattern like "**IS214 -- NHẬP MÔN QUẢN TRỊ CHUỖI CUNG ỨNG**"
            pattern = rf'\*\*{course_code}\s*--\s*(.+?)\*\*'
            match = re.search(pattern, line)
            if match:
                course_name = match.group(1).strip()
                break
            
            # Stop searching when we hit the first section heading
            if re.match(r'^#{1,2}\s+', line.strip()) or re.match(r'^\d+\.\s+\*\*[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', line.strip()):
                break
    
    # Fallback: use filename if still no course name
    if not course_name and filename_match:
        # Convert filename to readable format
        raw_name = filename_match.group(2)
        # Try to separate camelCase or PascalCase
        course_name = re.sub(r'([a-z])([A-Z])', r'\1 \2', raw_name)
        course_name = course_name.upper()
    
    # Find the first content section (THÔNG TIN CHUNG or similar)
    first_content_idx = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Look for numbered heading like "1. **THÔNG TIN CHUNG**" or "## THÔNG TIN CHUNG" or "# THÔNG TIN CHUNG"
        if re.match(r'^#{1,2}\s+', stripped) or re.match(r'^\d+\.\s+\*\*[A-ZÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]', stripped):
            first_content_idx = i
            break
    
    if first_content_idx is None:
        logger.warning("No section heading found in %s, returning original content", filename)
        return content
    
    # Create new content
    cleaned_lines = []
    
    # Add H1 with course code and name
    if course_code and course_name:
        cleaned_lines.append(f"# {course_code} -- {course_name}")
        cleaned_lines.append("")
    elif course_code:
        cleaned_lines.append(f"# {course_code}")
        cleaned_lines.append("")
    
    # Track if we've added the H1 already to avoid duplicates
    h1_added = True if (course_code and (course_code or course_name)) else False
    
    # Process remaining lines
    for line in lines[first_content_idx:]:
        # Skip lines that should be removed
        if should_skip_line(line, course_code):
            continue
        
        # Remove blockquote markers (>) from the start of lines
        cleaned_line = re.sub(r'^>\s*', '', line)
        
        # Also remove > from inside table cells (e.g., "| > text |" -> "| text |")
        cleaned_line = re.sub(r'\|\s*>\s*', '| ', cleaned_line)
        
        # Convert numbered headings like "1. **THÔNG TIN CHUNG**" to "## THÔNG TIN CHUNG"
        # Also handle "(General information)" or similar English translations
        numbered_heading_match = re.match(r'^\d+\.\s+\*\*(.+?)\*\*(.*)$', cleaned_line.strip())
        if numbered_heading_match:
            heading_text = numbered_heading_match.group(1)
            rest = numbered_heading_match.group(2)  # Could contain "(English translation)"
            cleaned_line = f"## {heading_text}{rest}"
        
        # Convert "# HEADING (translation)" to "## HEADING"
        single_hash_match = re.match(r'^#\s+(.+?)(\s*\(.*\))?\s*$', cleaned_line.strip())
        if single_hash_match and not cleaned_line.strip().startswith('##'):
            heading_text = single_hash_match.group(1)
            # Only if it's not the first H1 we added
            if heading_text != f"{course_code} -- {course_name}" and heading_text != course_code:
                cleaned_line = f"## {heading_text}"
        
        cleaned_lines.append(cleaned_line)
    
    return '\n'.join(cleaned_lines)


def convert_doc_with_antiword(input_file: Path, output_file: Path) -> str:
    """
    Convert old binary .doc file using antiword command line tool.
    
    Args:
        input_file: Path to .doc file
        output_file: Path for output file
        
    Returns:
        Extracted markdown content
    """
    import subprocess
    import shutil
    
    # Check if antiword is available
    if not shutil.which('antiword'):
        raise RuntimeError(
            "antiword not found. Install with: brew install antiword\n"
            "Or manually convert .doc files to .docx in Microsoft Word"
        )
    
    try:
        logger.info(f"Converting {input_file.name} with antiword...")
        
        # Use antiword to extract text
        result = subprocess.run(
            ['antiword', str(input_file)],
            capture_output=True,
            text=True,
            check=True
        )
        
        text = result.stdout
        
        if not text or len(text.strip()) < 50:
            raise ValueError("Extracted text is too short or empty")
        
        # Write directly as markdown (plain text is valid markdown)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"✓ Converted {input_file.name} with antiword")
        return text
        
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"antiword failed: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to convert .doc file: {e}")


def should_skip_line(line: str, course_code: str) -> bool:
    """
    Check if a line should be skipped during cleaning.
    
    Args:
        line: Line to check
        course_code: Course code to identify duplicate headings
        
    Returns:
        True if line should be skipped
    """
    stripped = line.strip()
    
    # Skip "ĐỀ CƯƠNG MÔN HỌC" heading (with or without **)
    if re.search(r'^#{1,2}\s*\*{0,2}\s*ĐỀ CƯƠNG MÔN HỌC\s*\*{0,2}', stripped, re.IGNORECASE):
        return True
    
    # Skip duplicate course code headings (e.g., "**IS402 -- ĐIỆN TOÁN ĐÁM MÂY**" after H1)
    if course_code and re.search(rf'\*\*{course_code}\s*--\s*.+\*\*', stripped):
        return True
    
    return False


def convert_to_markdown(input_file: Path, output_file: Path) -> Tuple[bool, str]:
    """
    Convert file DOC/DOCX sang Markdown sử dụng pypandoc.
    
    Args:
        input_file: Đường dẫn file input (DOC/DOCX)
        output_file: Đường dẫn file output (MD)
        
    Returns:
        Tuple[success, message]
    """
    try:
        # Ensure output directory exists
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Converting {input_file.name} -> {output_file.name}")
        
        # Handle .doc files differently from .docx
        if input_file.suffix.lower() == '.doc':
            try:
                # Try antiword first (lightweight CLI tool)
                content = convert_doc_with_antiword(input_file, output_file)
            except Exception as e:
                logger.warning(f"Failed to convert .doc file: {e}")
                return False, f"✗ Skipped {input_file.name}: {str(e)}"
        else:
            # Convert .docx directly using pypandoc
            pypandoc.convert_file(
                str(input_file),
                'md',
                outputfile=str(output_file),
                extra_args=['--wrap=none', '--extract-media=.']
            )
            
            # Read the converted markdown content
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
        
        # Clean the markdown content
        cleaned_content = clean_markdown_content(content, output_file.name)
        
        # Write back the cleaned content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)
        
        logger.info("✓ Cleaned: %s", output_file.name)
        
        return True, f"✓ Converted successfully: {input_file.name}"
        
    except Exception as e:
        error_msg = f"✗ Error converting {input_file.name}: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def main():
    """Main function để convert tất cả file DOC/DOCX sang MD."""
    parser = argparse.ArgumentParser(
        description="Convert DOC/DOCX files to Markdown format"
    )
    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="data/raw/Syllabus",
        help="Input folder containing DOC/DOCX files (default: data/raw/Syllabus)"
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/raw/Syllabus-Modified",
        help="Output folder for MD files (default: data/raw/Syllabus-Modified)"
    )

    
    args = parser.parse_args()
    
    # Get absolute paths
    project_root = Path(__file__).parent.parent
    input_folder = project_root / args.input
    output_folder = project_root / args.output
    
    # Validate input folder
    if not input_folder.exists():
        logger.error(f"Input folder không tồn tại: {input_folder}")
        sys.exit(1)
    
    logger.info(f"Input folder: {input_folder}")
    logger.info(f"Output folder: {output_folder}")
    
    # Find all DOC/DOCX files
    doc_files = find_doc_files(input_folder)
    
    if not doc_files:
        logger.warning(f"Không tìm thấy file .doc hoặc .docx nào trong {input_folder}")
        return
    
    logger.info(f"Tìm thấy {len(doc_files)} file(s) để convert")
    
    # Convert each file
    results = []
    cleaned_count = 0
    for doc_file in doc_files:
        # Calculate relative path to maintain folder structure
        relative_path = doc_file.relative_to(input_folder)
        
        # Create output file path with .md extension
        output_file = output_folder / relative_path.with_suffix('.md')
        
        # Convert
        success, message = convert_to_markdown(doc_file, output_file)
        results.append((success, message))
        logger.info(message)
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SUMMARY")
    logger.info("="*60)
    
    successful = sum(1 for success, _ in results if success)
    failed = len(results) - successful
    
    logger.info(f"Total files: {len(results)}")
    logger.info(f"Successful: {successful}")
    logger.info(f"Failed: {failed}")
    
    if failed > 0:
        logger.warning("\nFailed conversions:")
        for success, message in results:
            if not success:
                logger.warning(f"  {message}")
    
    logger.info("="*60)


if __name__ == "__main__":
    main()
