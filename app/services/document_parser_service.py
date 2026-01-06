"""
Document Parser Service - Handles parsing PDF/DOCX files to Markdown
"""
import logging
import tempfile
import os
from typing import List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ParseResult:
    """Result of document parsing"""
    success: bool
    markdown: str
    filename: str
    pages: Optional[int] = None
    warnings: Optional[List[str]] = None
    error: Optional[str] = None


class DocumentParserService:
    """
    Service for parsing documents (PDF, DOCX) to Markdown
    
    Handles:
    - PDF to Markdown conversion (via pymupdf4llm)
    - DOCX to Markdown conversion (via pypandoc)
    - Grid table to pipe table conversion
    """
    
    SUPPORTED_PDF_EXTENSIONS = ['.pdf']
    SUPPORTED_DOCX_EXTENSIONS = ['.docx']
    
    def __init__(self):
        self._validate_dependencies()
    
    def _validate_dependencies(self):
        """Check if required dependencies are available"""
        try:
            import pymupdf
            import pymupdf4llm
            self._pdf_available = True
        except ImportError:
            self._pdf_available = False
            logger.warning("pymupdf4llm not available - PDF parsing disabled")
        
        try:
            import pypandoc
            self._docx_available = True
        except ImportError:
            self._docx_available = False
            logger.warning("pypandoc not available - DOCX parsing disabled")
    
    def _clean_encoding(self, text: str) -> str:
        """Clean up encoding issues in text"""
        return text.encode('utf-8', errors='surrogatepass').decode('utf-8', errors='ignore')
    
    def _clean_markdown_content(self, content: str) -> str:
        """
        Clean up markdown content by:
        1. Removing empty HTML comments (<!-- -->)
        2. Reducing excessive consecutive newlines to maximum 2
        """
        import re
        
        # Remove empty HTML comments
        content = re.sub(r'<!--\s*-->', '', content)
        
        # Reduce 3+ consecutive newlines to 2
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Clean up lines that are only whitespace
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.strip() == '':
                cleaned_lines.append('')
            else:
                cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Final pass to reduce consecutive empty lines
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        return content.strip()
    
    # =========================================================================
    # Grid Table to Pipe Table Conversion
    # =========================================================================
    
    def _convert_grid_table_to_pipe(self, table_lines: List[str]) -> List[str]:
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
        """
        import re
        
        if not table_lines:
            return []
        
        pipe_lines = []
        rows = []
        current_row = []
        
        for line in table_lines:
            stripped = line.strip()
            
            # Skip separator lines (lines with +, -, =, :)
            if re.match(r'^[\+\-\=\:]+$', stripped):
                if current_row:
                    rows.append(current_row)
                    current_row = []
                continue
            
            # Process cell lines (lines starting with |)
            if stripped.startswith('|') and stripped.endswith('|'):
                cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
                
                if not current_row:
                    current_row = cells
                else:
                    for i, cell in enumerate(cells):
                        if i < len(current_row) and cell:
                            current_row[i] += ' ' + cell
        
        if current_row:
            rows.append(current_row)
        
        if not rows:
            return []
        
        # Build pipe table
        if rows:
            header = rows[0]
            pipe_lines.append('| ' + ' | '.join(header) + ' |')
            separator = '| ' + ' | '.join(['---'] * len(header)) + ' |'
            pipe_lines.append(separator)
            
            for row in rows[1:]:
                while len(row) < len(header):
                    row.append('')
                pipe_lines.append('| ' + ' | '.join(row[:len(header)]) + ' |')
        
        return pipe_lines
    
    def _convert_simple_table_to_pipe(self, table_lines: List[str]) -> List[str]:
        """
        Convert pandoc simple table format to GFM pipe table.
        Handles multi-line cells with empty line separators between rows.
        
        Simple table example from pandoc:
          -------------------------------------------------------------------------------
           **Col1**  **Col2**                                               **Col3**
          ---------- ---------------------------------------------------- ----------------
              A      Line 1 of cell\\                                        X
                     Line 2 of cell
          
              B      Another cell content                                    Y
          -------------------------------------------------------------------------------
        """
        import re
        
        if not table_lines:
            return []
        
        # Find column boundaries from separator lines (lines with multiple dash segments)
        col_positions: List[tuple] = []
        
        for line in table_lines:
            # Look for inner separator (between header and body) - has multiple dash segments
            if re.match(r'^[\s\-]+$', line) and '-' in line:
                # Find start and end positions of each dash segment
                positions = []
                in_dash = False
                dash_start = 0
                for i, c in enumerate(line):
                    if c == '-' and not in_dash:
                        dash_start = i
                        in_dash = True
                    elif c != '-' and in_dash:
                        positions.append((dash_start, i))
                        in_dash = False
                # Handle dash at end of line
                if in_dash:
                    positions.append((dash_start, len(line)))
                
                # Keep the separator with most columns
                if len(positions) > len(col_positions):
                    col_positions = positions
        
        if not col_positions:
            # Fallback: split by 2+ spaces
            content_lines = [l for l in table_lines if l.strip() and not re.match(r'^[\s\-]+$', l.strip())]
            rows = []
            for line in content_lines:
                cells = re.split(r'\s{2,}', line.strip())
                cells = [c.strip() for c in cells if c.strip()]
                if cells:
                    rows.append(cells)
            if rows:
                pipe_lines = []
                header = rows[0]
                pipe_lines.append('| ' + ' | '.join(header) + ' |')
                pipe_lines.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
                for row in rows[1:]:
                    while len(row) < len(header):
                        row.append('')
                    pipe_lines.append('| ' + ' | '.join(row[:len(header)]) + ' |')
                return pipe_lines
            return []
        
        # Parse content into rows, handling multi-line cells
        # Empty lines between non-empty content lines indicate row boundaries
        rows: List[List[str]] = []
        current_row: Optional[List[str]] = None
        header_parsed = False
        
        for line in table_lines:
            stripped = line.strip()
            
            # Skip outer separator lines (start/end of table)
            if re.match(r'^[\s\-]+$', stripped):
                # Separator after header means we're done with header
                if current_row is not None and not header_parsed:
                    rows.append(current_row)
                    current_row = None
                    header_parsed = True
                elif current_row is not None:
                    rows.append(current_row)
                    current_row = None
                continue
            
            # Empty line after content = row complete
            if not stripped:
                if current_row is not None:
                    rows.append(current_row)
                    current_row = None
                continue
            
            # Extract cells based on column positions
            cells = []
            for start, end in col_positions:
                if start < len(line):
                    cell_text = line[start:min(end, len(line))].strip()
                else:
                    cell_text = ''
                cells.append(cell_text)
            
            # Check if this is a continuation (first column is empty/spaces only)
            first_col_start = col_positions[0][0]
            first_col_end = col_positions[0][1]
            first_col_content = line[first_col_start:min(first_col_end, len(line))].strip() if first_col_start < len(line) else ''
            is_continuation = current_row is not None and not first_col_content
            
            if is_continuation and current_row is not None:
                # Merge with current row - append to non-empty cells
                row = current_row  # Help type narrowing for the loop
                for i, cell in enumerate(cells):
                    if i < len(row) and cell:
                        if row[i]:
                            row[i] = row[i] + ' ' + cell
                        else:
                            row[i] = cell
            else:
                if current_row is not None:
                    rows.append(current_row)
                current_row = cells
        
        # Add last row if exists
        if current_row is not None:
            rows.append(current_row)
        
        if not rows:
            return []
        
        # Clean up cells - remove trailing backslashes and normalize whitespace
        cleaned_rows = []
        for row in rows:
            cleaned_row = []
            for cell in row:
                # Remove \\ which pandoc uses for line breaks
                cell = re.sub(r'\\+$', '', cell)
                cell = re.sub(r'\\{2,}', ' ', cell)
                cell = ' '.join(cell.split())  # Normalize whitespace
                cleaned_row.append(cell)
            cleaned_rows.append(cleaned_row)
        rows = cleaned_rows
        
        # Build pipe table
        pipe_lines = []
        header = rows[0]
        num_cols = len(header)
        
        pipe_lines.append('| ' + ' | '.join(header) + ' |')
        pipe_lines.append('| ' + ' | '.join(['---'] * num_cols) + ' |')
        
        for row in rows[1:]:
            while len(row) < num_cols:
                row.append('')
            pipe_lines.append('| ' + ' | '.join(row[:num_cols]) + ' |')
        
        return pipe_lines
    
    def _detect_and_convert_tables(self, content: str) -> str:
        """Detect and convert both grid tables and simple tables to GFM pipe tables."""
        import re
        
        lines = content.split('\n')
        converted_lines = []
        in_grid_table = False
        in_simple_table = False
        table_buffer = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Detect start of grid table (+---+ pattern)
            if re.match(r'^[\+\-\=\:]+[\+\-\=\:]+', stripped) and '+' in stripped and not in_grid_table and not in_simple_table:
                in_grid_table = True
                table_buffer = [line]
                i += 1
                continue
            
            # Detect start of simple table (line of only spaces and dashes, no +)
            if re.match(r'^[\s\-]+$', line) and '-' in line and '+' not in stripped and not in_grid_table and not in_simple_table:
                in_simple_table = True
                table_buffer = [line]
                i += 1
                continue
            
            # Process grid table
            if in_grid_table:
                if (stripped.startswith('|') or 
                    re.match(r'^[\+\-\=\:]+', stripped) or
                    not stripped):
                    table_buffer.append(line)
                    i += 1
                    
                    if (re.match(r'^[\+\-\=\:]+', stripped) and 
                        (i >= len(lines) or 
                         (not lines[i].strip().startswith('|') and 
                          not re.match(r'^[\+\-\=\:]+', lines[i].strip())))):
                        pipe_table = self._convert_grid_table_to_pipe(table_buffer)
                        converted_lines.extend(pipe_table)
                        converted_lines.append('')
                        in_grid_table = False
                        table_buffer = []
                    continue
                else:
                    pipe_table = self._convert_grid_table_to_pipe(table_buffer)
                    converted_lines.extend(pipe_table)
                    converted_lines.append('')
                    in_grid_table = False
                    table_buffer = []
            
            # Process simple table
            if in_simple_table:
                # Simple table ends with a line of dashes followed by non-table content
                is_separator = re.match(r'^[\s\-]+$', line) and '-' in line and '+' not in line
                
                table_buffer.append(line)
                i += 1
                
                # Check if this separator ends the table
                if is_separator:
                    # Look ahead to see if table ends
                    # Skip empty lines to find next non-empty line
                    look_ahead_idx = i
                    while look_ahead_idx < len(lines) and not lines[look_ahead_idx].strip():
                        look_ahead_idx += 1
                    
                    # Table ends if:
                    # 1. End of file, OR
                    # 2. Next non-empty line is NOT a table row (doesn't have leading spaces followed by content)
                    if look_ahead_idx >= len(lines):
                        # End of file
                        pipe_table = self._convert_simple_table_to_pipe(table_buffer)
                        converted_lines.extend(pipe_table)
                        converted_lines.append('')
                        in_simple_table = False
                        table_buffer = []
                    else:
                        next_content = lines[look_ahead_idx]
                        # Table row has indentation (starts with spaces) or is another separator
                        is_table_row = (re.match(r'^\s+\S', next_content) or 
                                       (re.match(r'^[\s\-]+$', next_content) and '-' in next_content))
                        if not is_table_row:
                            pipe_table = self._convert_simple_table_to_pipe(table_buffer)
                            converted_lines.extend(pipe_table)
                            converted_lines.append('')
                            in_simple_table = False
                            table_buffer = []
                continue
            
            # Normal line
            if not in_grid_table and not in_simple_table:
                converted_lines.append(line)
                i += 1
        
        # Handle remaining buffer
        if table_buffer:
            if in_grid_table:
                pipe_table = self._convert_grid_table_to_pipe(table_buffer)
            else:
                pipe_table = self._convert_simple_table_to_pipe(table_buffer)
            converted_lines.extend(pipe_table)
        
        return '\n'.join(converted_lines)
    
    # =========================================================================
    # PDF Parsing
    # =========================================================================
    
    async def parse_pdf(
        self,
        file_content: bytes,
        filename: str
    ) -> ParseResult:
        """Parse a PDF file and convert to Markdown"""
        if not self._pdf_available:
            return ParseResult(
                success=False,
                markdown="",
                filename=filename,
                error="PDF parsing not available - pymupdf4llm not installed"
            )
        
        import pymupdf
        import pymupdf4llm
        
        logger.info(f"Starting PDF parsing: {filename}")
        tmp_path = None
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            doc = pymupdf.open(tmp_path)
            num_pages = len(doc)
            
            md_content = pymupdf4llm.to_markdown(
                doc,
                hdr_info=False,
                write_images=False,
                page_chunks=False
            )
            
            doc.close()
            md_cleaned = self._clean_encoding(md_content)
            
            logger.info(f"Successfully parsed PDF '{filename}' ({num_pages} pages)")
            
            return ParseResult(
                success=True,
                markdown=md_cleaned,
                filename=filename,
                pages=num_pages
            )
            
        except Exception as e:
            logger.error(f"Failed to parse PDF '{filename}': {e}")
            return ParseResult(
                success=False,
                markdown="",
                filename=filename,
                error=str(e)
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass
    
    # =========================================================================
    # DOCX Parsing (using pypandoc)
    # =========================================================================
    
    async def parse_docx(
        self,
        file_content: bytes,
        filename: str
    ) -> ParseResult:
        """
        Parse a DOCX file and convert to Markdown using pypandoc
        
        Args:
            file_content: Raw bytes of the DOCX file
            filename: Original filename
            
        Returns:
            ParseResult with markdown content
        """
        if not self._docx_available:
            return ParseResult(
                success=False,
                markdown="",
                filename=filename,
                error="DOCX parsing not available - pypandoc not installed"
            )
        
        import pypandoc
        
        logger.info(f"Starting DOCX parsing: {filename}")
        tmp_path = None
        output_path = None
        
        try:
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
                tmp_file.write(file_content)
                tmp_path = tmp_file.name
            
            # Create temp output path
            output_path = tmp_path.replace('.docx', '.md')
            
            # Convert using pypandoc
            pypandoc.convert_file(
                tmp_path,
                'md',
                outputfile=output_path,
                extra_args=['--wrap=none']
            )
            
            # Read converted content
            with open(output_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Clean encoding
            md_cleaned = self._clean_encoding(md_content)
            
            # Convert grid tables to GFM pipe tables
            md_cleaned = self._detect_and_convert_tables(md_cleaned)
            
            # Clean up excessive newlines and empty HTML comments
            md_cleaned = self._clean_markdown_content(md_cleaned)
            
            logger.info(f"Successfully parsed DOCX '{filename}'")
            
            return ParseResult(
                success=True,
                markdown=md_cleaned,
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"Failed to parse DOCX '{filename}': {e}")
            return ParseResult(
                success=False,
                markdown="",
                filename=filename,
                error=str(e)
            )
        finally:
            # Clean up temp files
            for path in [tmp_path, output_path]:
                if path and os.path.exists(path):
                    try:
                        os.unlink(path)
                    except Exception:
                        pass
    
    def validate_file_extension(
        self,
        filename: str,
        file_type: str
    ) -> tuple[bool, Optional[str]]:
        """Validate file extension"""
        ext = os.path.splitext(filename.lower())[1]
        
        if file_type == 'pdf':
            if ext not in self.SUPPORTED_PDF_EXTENSIONS:
                return False, f"Only PDF files are accepted. Got: {ext}"
        elif file_type == 'docx':
            if ext not in self.SUPPORTED_DOCX_EXTENSIONS:
                return False, f"Only DOCX files are accepted. Got: {ext}"
        else:
            return False, f"Unknown file type: {file_type}"
        
        return True, None


# Global service instance
document_parser_service = DocumentParserService()
