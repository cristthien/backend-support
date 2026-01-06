"""
Simple document processing module with chunking and table extraction
"""
from typing import List, Dict, Optional, Literal
from enum import Enum
import re
import hashlib
import mistune
import asyncio
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class TableType(str, Enum):
    """Types of table structures"""
    KEYPAIR = "keypair"      # 2-column key-value table
    STANDARD = "standard"    # Multi-column table with headers


class MarkdownStructureChunker:
    """
    Complete markdown processor: chunks documents and extracts tables
    All-in-one solution for markdown document processing
    """

    def __init__(self, chunk_size: Optional[int] = None, chunk_overlap: Optional[int] = None):
        """
        Initialize the markdown structure chunker

        Args:
            chunk_size: Target size for chunks (soft limit), defaults to config value
            chunk_overlap: Overlap between chunks, defaults to config value
        """
        self.chunk_size = chunk_size if chunk_size is not None else settings.chunk_size
        self.chunk_overlap = chunk_overlap if chunk_overlap is not None else settings.chunk_overlap
        self.chunk_counter = 0
        
        # Initialize mistune parser with table plugin
        self.markdown_parser = mistune.create_markdown(
            plugins=['table'],
            renderer='ast'
        )
    
    @staticmethod
    def strip_markdown(text: str) -> str:
        """Remove markdown formatting from text"""
        # Remove bold/italic
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        # Remove links but keep text
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        # Remove inline code
        text = re.sub(r'`(.+?)`', r'\1', text)
        return text.strip()
    
    # ============================================================================
    # TABLE EXTRACTION METHODS
    # ============================================================================
    
    def _extract_tables_from_text(self, text: str) -> List[Dict]:
        """
        Extract all tables from markdown text
        
        Args:
            text: Markdown text containing tables
            
        Returns:
            List of table dictionaries with structure and searchable text
        """
        if not text or not text.strip():
            return []
        
        # Parse markdown to AST
        ast = self.markdown_parser(text)
        
        # Extract tables from AST
        tables = []
        self._extract_tables_from_ast(ast, tables)
        
        return tables
    
    async def extract_tables_with_llm(self, text: str) -> List[Dict]:
        """
        Extract all tables from markdown text using LLM for type detection
        
        This async method uses LLM to classify table types for more accurate
        searchable text generation.
        
        Args:
            text: Markdown text containing tables
            
        Returns:
            List of table dictionaries with structure and searchable text
        """
        if not text or not text.strip():
            return []
        
        # Parse markdown to AST
        ast = self.markdown_parser(text)
        
        # Extract raw table data from AST
        raw_tables = []
        self._extract_raw_tables_from_ast(ast, raw_tables)
        
        # Process each table with LLM detection
        tables = []
        for raw_table in raw_tables:
            processed = await self._process_table_node_async(raw_table)
            tables.append(processed)
        
        return tables
    
    def _extract_raw_tables_from_ast(self, node, tables: List[Dict]):
        """
        Extract raw table nodes from AST (without processing)
        
        Args:
            node: AST node (can be dict or list)
            tables: List to accumulate table nodes
        """
        if isinstance(node, list):
            for item in node:
                self._extract_raw_tables_from_ast(item, tables)
        elif isinstance(node, dict):
            if node.get('type') == 'table':
                tables.append(node)
            if 'children' in node:
                self._extract_raw_tables_from_ast(node['children'], tables)
    
    async def _process_table_node_async(self, table_node: Dict) -> Dict:
        """
        Process a table AST node with LLM-based type detection
        
        Args:
            table_node: Table node from mistune AST
            
        Returns:
            Dictionary with table structure, type, and searchable text
        """
        children = table_node.get('children', [])
        
        headers = []
        rows = []
        
        for child in children:
            child_type = child.get('type')
            
            if child_type == 'table_head':
                headers = self._extract_table_row(child)
            elif child_type == 'table_body':
                for row_node in child.get('children', []):
                    if row_node.get('type') == 'table_row':
                        row_data = self._extract_table_row(row_node)
                        rows.append(row_data)
        
        # Smart header detection
        if rows and self._is_header_empty_or_weak(headers):
            headers = rows[0]
            rows = rows[1:]
        if len(headers) > 2:
            table_type = TableType.STANDARD
        else:
            table_type = await self._detect_table_type_llm(headers, rows)
        searchable_text = self._build_searchable_text(headers, rows, table_type)
        
        return {
            'headers': headers,
            'rows': rows,
            'num_rows': len(rows),
            'num_columns': len(headers),
            'table_type': table_type.value,
            'searchable_text': searchable_text
        }
    
    def _extract_tables_from_ast(self, node, tables: List[Dict]):
        """
        Recursively extract tables from AST nodes
        
        Args:
            node: AST node (can be dict or list)
            tables: List to accumulate extracted tables
        """
        if isinstance(node, list):
            for item in node:
                self._extract_tables_from_ast(item, tables)
        elif isinstance(node, dict):
            node_type = node.get('type')
            
            if node_type == 'table':
                # Process table node
                table_data = self._process_table_node(node)
                tables.append(table_data)
            
            # Recursively process children
            if 'children' in node:
                self._extract_tables_from_ast(node['children'], tables)
    
    def _process_table_node(self, table_node: Dict) -> Dict:
        """
        Process a table AST node into structured data
        
        Args:
            table_node: Table node from mistune AST
            
        Returns:
            Dictionary with table structure, type, and searchable text
        """
        children = table_node.get('children', [])
        
        headers = []
        rows = []
        
        for child in children:
            child_type = child.get('type')
            
            if child_type == 'table_head':
                # Extract headers
                headers = self._extract_table_row(child)
            elif child_type == 'table_body':
                # Extract body rows
                for row_node in child.get('children', []):
                    if row_node.get('type') == 'table_row':
                        row_data = self._extract_table_row(row_node)
                        rows.append(row_data)
        
        # Smart header detection: if header is empty/meaningless, use first row as header
        if rows and self._is_header_empty_or_weak(headers):
            headers = rows[0]
            rows = rows[1:]  # Remove first row since it's now the header
        
        # Detect table type using heuristics
        table_type = self._detect_table_type_sync(headers, rows)
        
        # Build searchable text based on detected type
        searchable_text = self._build_searchable_text(headers, rows, table_type)
        
        # Create table dictionary
        table_dict = {
            'headers': headers,
            'rows': rows,
            'num_rows': len(rows),
            'num_columns': len(headers),
            'table_type': table_type.value,  # 'keypair' or 'standard'
            'searchable_text': searchable_text
        }
        
        return table_dict
    
    def _is_header_empty_or_weak(self, headers: List[str]) -> bool:
        """
        Check if header row is empty or contains weak/meaningless content
        
        Args:
            headers: List of header values
            
        Returns:
            True if header should be replaced with first data row
        """
        if not headers:
            return True
        
        # Count non-empty headers
        non_empty = [h for h in headers if h and h.strip()]
        
        # If less than half headers have content, it's weak
        if len(non_empty) < len(headers) / 2:
            return True
        
        # Check if all headers are very short or just symbols/numbers
        weak_patterns = [
            lambda h: len(h.strip()) <= 1,  # Single character
            lambda h: h.strip().isdigit(),   # Just numbers
            lambda h: not any(c.isalnum() for c in h),  # No alphanumeric
        ]
        
        weak_count = sum(
            1 for h in non_empty 
            if any(pattern(h) for pattern in weak_patterns)
        )
        
        # If more than half are weak, consider it weak header
        if weak_count > len(non_empty) / 2:
            return True
        
        return False
    
    def _extract_table_row(self, row_node: Dict) -> List[str]:
        """
        Extract cell values from a table row node
        
        Args:
            row_node: Table row node (table_head or table_row)
            
        Returns:
            List of cell text values
        """
        cells = []
        
        # Handle both table_head and table_row
        children = row_node.get('children', [])
        
        for cell_node in children:
            cell_type = cell_node.get('type')
            
            if cell_type in ['table_cell', 'table_head']:
                # Extract text from cell
                cell_text = self._extract_text_from_node(cell_node)
                cells.append(cell_text.strip())
        
        return cells
    
    def _extract_text_from_node(self, node) -> str:
        """
        Recursively extract all text content from a node
        
        Args:
            node: AST node
            
        Returns:
            Concatenated text content
        """
        if isinstance(node, str):
            return node
        
        if isinstance(node, dict):
            node_type = node.get('type')
            
            # Handle text nodes
            if node_type == 'text':
                return node.get('raw', '')
            
            # Handle inline code
            if node_type == 'codespan':
                return node.get('raw', '')
            
            # Handle links - extract text, ignore URL
            if node_type == 'link':
                children = node.get('children', [])
                return ''.join(self._extract_text_from_node(child) for child in children)
            
            # Handle emphasis, strong, etc.
            if 'children' in node:
                children = node.get('children', [])
                return ''.join(self._extract_text_from_node(child) for child in children)
            
            # Handle raw text
            if 'raw' in node:
                return node.get('raw', '')
        
        if isinstance(node, list):
            return ''.join(self._extract_text_from_node(item) for item in node)
        
        return ''
    
    def _detect_table_type_sync(self, headers: List[str], rows: List[List[str]]) -> TableType:
        """
        Detect table type using simple heuristics (sync fallback)
        
        Keypair indicators:
        - Exactly 2 columns
        - First column values look like labels (short, no numbers)
        - Second column values are varied/longer
        
        Args:
            headers: List of column headers
            rows: List of rows
            
        Returns:
            TableType enum value
        """
        num_cols = len(headers) if headers else (len(rows[0]) if rows else 0)
        
        # Not 2 columns -> definitely standard
        if num_cols != 2:
            return TableType.STANDARD
        
        # Check if first column looks like keys (labels)
        first_col_values = [row[0] for row in rows if row and len(row) >= 2]
        
        if not first_col_values:
            return TableType.STANDARD
        
        # Heuristics for keypair:
        # 1. First column values are shorter (avg < 30 chars)
        # 2. First column values don't contain numbers predominantly
        # 3. Headers might be empty or generic like "" or "Thông tin"
        
        avg_first_col_len = sum(len(v) for v in first_col_values) / len(first_col_values)
        
        # If first column is short and looks like labels
        if avg_first_col_len < 40:
            # Check if first column values look like field names
            label_patterns = [
                r'^[A-Za-zÀ-ỹ\s]+$',  # Only letters and spaces
                r'^[A-Za-zÀ-ỹ\s]+:?$',  # Letters with optional colon
            ]
            
            label_count = sum(
                1 for v in first_col_values 
                if any(re.match(p, v.strip()) for p in label_patterns)
            )
            
            # If more than 60% look like labels, it's keypair
            if label_count >= len(first_col_values) * 0.6:
                return TableType.KEYPAIR
        
        return TableType.STANDARD
    
    async def _detect_table_type_llm(self, headers: List[str], rows: List[List[str]]) -> TableType:
        """
        Detect table type using LLM (PRIMARY method)
        
        Falls back to heuristics if LLM fails.
        
        Args:
            headers: List of column headers
            rows: All rows of data
            
        Returns:
            TableType enum value
        """
        try:
            from app.clients.ollama import ollama_client
            
            # Build sample for LLM - show headers and first 2 rows max
            sample_rows = rows[:3] if len(rows) > 3 else rows # Lấy 3 dòng để dễ so sánh data type hơn
            sample_text = f"Headers: {headers}\nSample rows: {sample_rows}"

            prompt = f"""Analyze the structural semantics of the provided table snippet to classify it. 

            **Definitions:**
            1. **"keypair"**: A 2-column table representing a single entity's attributes. 
            - **Logic**: Column 1 contains distinct labels (keys), and Column 2 contains mixed data types (e.g., Row 1 is text, Row 2 is a date, Row 3 is currency).
            - The relationship is horizontal (Col 1 defines Col 2).
            
            2. **"standard"**: A list of multiple entities. 
            - **Logic**: Each column represents a specific variable/attribute. Data within the same column shows **vertical consistency** (e.g., Column 2 is ALWAYS a date across all rows).
            - The relationship is vertical (Row 1 and Row 2 are comparable items).

            **Input Data:**
            {sample_text}

            **Instruction:**
            - Check for vertical consistency in data types.
            - Check if Column 1 acts as a descriptive label for Column 2.
            - Respond with ONLY one word: "keypair" or "standard".
            """
                        
            response = await ollama_client.generate_answer(prompt)
            response_clean = response.strip().lower()
            
            if "keypair" in response_clean:
                return TableType.KEYPAIR
            else:
                return TableType.STANDARD
                
        except Exception as e:
            logger.warning(f"LLM table detection failed, falling back to heuristics: {e}")
            return self._detect_table_type_sync(headers, rows)
    
    def _build_searchable_text_keypair(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Build searchable text for keypair table (key: value format)
        
        Args:
            headers: List of column headers (usually ignored for keypair)
            rows: List of rows (each row is [key, value])
            
        Returns:
            Searchable text with "Key: Value" format per line
        """
        lines = []
        
        for row in rows:
            if not row or len(row) < 2:
                continue
            
            key = row[0].strip() if row[0] else ""
            value = row[1].strip() if row[1] else ""
            
            if key and value:
                # Remove trailing colon from key if exists
                key = key.rstrip(':')
                lines.append(f"{key}: {value}")
            elif key:
                lines.append(key)
            elif value:
                lines.append(value)
        
        return "\n".join(lines)
    
    def _build_searchable_text_standard(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Build searchable text for standard table (Header: Value format per column)
        
        Args:
            headers: List of column headers
            rows: List of rows (each row is a list of cell values)
            
        Returns:
            Searchable text with "Header1: Value1, Header2: Value2" format per row
        """
        if not headers and not rows:
            return ""
        
        lines = []
        
        # Add headers as context
        if headers:
            header_line = "Các cột: " + ", ".join([h for h in headers if h])
            lines.append(header_line)
        
        # Add each row
        for row in rows:
            if not row:
                continue
            
            # Pair headers with values
            if headers and len(headers) == len(row):
                row_parts = []
                for header, value in zip(headers, row):
                    if value:  # Only include non-empty values
                        row_parts.append(f"{header}: {value}")
                row_line = ", ".join(row_parts)
            else:
                # No headers or mismatch - just list values
                row_line = ", ".join([v for v in row if v])
            
            if row_line:
                lines.append(row_line)
        
        return "\n".join(lines)
    
    def _build_searchable_text(
        self, 
        headers: List[str], 
        rows: List[List[str]], 
        table_type: Optional[TableType] = None
    ) -> str:
        """
        Build searchable text representation of table based on its type
        
        Args:
            headers: List of column headers
            rows: List of rows (each row is a list of cell values)
            table_type: Optional pre-detected table type
            
        Returns:
            Searchable text representation
        """
        if not headers and not rows:
            return ""
        
        # Detect table type if not provided
        if table_type is None:
            table_type = self._detect_table_type_sync(headers, rows)
        
        # Build searchable text based on type
        if table_type == TableType.KEYPAIR:
            return self._build_searchable_text_keypair(headers, rows)
        else:
            return self._build_searchable_text_standard(headers, rows)
    
    def _get_table_summary(self, table: Dict) -> str:
        """
        Generate a human-readable summary of the table
        
        Args:
            table: Table dictionary
            
        Returns:
            Summary string like "Bảng 3 hàng x 4 cột"
        """
        num_rows = table.get('num_rows', 0)
        num_columns = table.get('num_columns', 0)
        
        summary = f"Bảng {num_rows} hàng x {num_columns} cột"
        
        # Add header info if available
        headers = table.get('headers', [])
        if headers:
            header_preview = ", ".join(headers[:3])  # First 3 headers
            if len(headers) > 3:
                header_preview += ", ..."
            summary += f". Các cột: {header_preview}"
        
        return summary
    
    def _remove_tables_from_text(self, text: str) -> str:
        """
        Remove markdown table syntax from text
        
        Args:
            text: Markdown text
            
        Returns:
            Text with tables removed
        """
        # Pattern to match markdown tables (lines starting with |)
        # Remove table rows and separator lines
        lines = text.split('\n')
        filtered_lines = []
        
        in_table = False
        for line in lines:
            stripped = line.strip()
            
            # Check if this is a table line (starts with | or is separator)
            if stripped.startswith('|') or self._is_table_separator(stripped):
                in_table = True
                continue
            else:
                # If we were in a table and now we're not, add a blank line
                if in_table:
                    filtered_lines.append('')
                    in_table = False
                
                filtered_lines.append(line)
        
        # Clean up multiple consecutive blank lines
        result = '\n'.join(filtered_lines)
        result = re.sub(r'\n{3,}', '\n\n', result)
        
        return result.strip()
    
    def _is_table_separator(self, line: str) -> bool:
        """
        Check if a line is a markdown table separator (e.g., |---|---|)
        
        Args:
            line: Line of text
            
        Returns:
            True if line is a table separator
        """
        # Table separator contains | and - and : characters
        if not line:
            return False
        
        # Remove whitespace
        stripped = line.strip()
        
        # Must start and contain |
        if not ('|' in stripped):
            return False
        
        # Remove | and whitespace, should only contain - and :
        cleaned = stripped.replace('|', '').replace(' ', '').replace('-', '').replace(':', '')
        
        return len(cleaned) == 0 and len(stripped) > 2
    
    # ============================================================================
    # CHUNKING METHODS
    # ============================================================================

    def _generate_chunk_id(self, content: str, hierarchy: List[str]) -> str:
        """Generate a unique chunk ID based on content and hierarchy"""
        self.chunk_counter += 1
        path = " > ".join(hierarchy)
        base = f"{path}_{self.chunk_counter}"
        return hashlib.md5(base.encode()).hexdigest()[:12]

    async def chunk_documents(self, documents: List[dict]) -> List[dict]:
        """
        Chunk multiple documents with structure preservation

        Args:
            documents: List of document dicts with 'text' and 'metadata'

        Returns:
            List of chunk dictionaries
        """
        all_chunks = []

        for doc in documents:
            doc_chunks = await self.chunk_markdown(
                doc['text'],
                doc.get('metadata', {})
            )
            all_chunks.extend(doc_chunks)

        return all_chunks

    async def chunk_markdown(self, text: str, metadata: dict = None) -> Dict[str, object]:
        """
        Parse markdown structure and create chunks with hierarchy
        
        Creates two types of retrieval units:
        1. Sections: Optimized for broad/general search with full hierarchy context
        2. Chunks: Detailed paragraph-level pieces for specific retrieval

        Args:
            text: Markdown text
            metadata: Document metadata

        Returns:
            {
                "sections": List[dict] - Hierarchical sections for broad retrieval,
                "chunks": List[dict] - Detailed chunks for specific retrieval
            }
        """
        if not text or not text.strip():
            return {
                "sections": [],
                "chunks": []
            }

        # Parse markdown into sections (async for LLM-based table detection)
        sections = await self.parse_sections(text)

        # Create optimized section mappings for broad/hierarchical search
        section_mappings = []
        for section in sections:
            section_mapping = self._create_section_mapping(section, metadata)
            section_mappings.append(section_mapping)

        # Create detailed chunks from section mappings (using searchable text)
        all_chunks = []
        for section_mapping in section_mappings:
            section_chunks = self._chunk_section_mapping(section_mapping, metadata)
            all_chunks.extend(section_chunks)
            
        return {
            "sections": section_mappings,
            "chunks": all_chunks
        }
    async def parse_sections(self, text: str, use_llm: bool = True) -> List[Dict]:
        """
        Parse markdown text into hierarchical sections
        
        Args:
            text: Markdown text to parse
            use_llm: If True, use LLM for table type detection with fallback to heuristics.
                     If False, use sync heuristics only.

        Returns:
            List of section dicts with heading, level, content, hierarchy, tables
        """
        lines = text.split('\n')
        sections = []
        current_section: Optional[Dict] = None
        heading_stack = []
        in_table = False

        for line in lines:
            stripped_line = line.strip()
            
            # Track if we're inside a table to avoid parsing table content as headings
            if stripped_line.startswith('|') or self._is_table_separator(stripped_line):
                in_table = True
                if current_section is not None:
                    section = current_section
                    if section['content']:
                        section['content'] += '\n' + line
                    else:
                        section['content'] = line
                continue
            elif in_table and not stripped_line:
                # Empty line might end table, but keep in_table=True for next line check
                in_table = False
                if current_section is not None:
                    section = current_section
                    if section['content']:
                        section['content'] += '\n' + line
                    else:
                        section['content'] = line
                continue
            
            # Only match headings if NOT in table
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line) if not in_table else None

            if heading_match:
                if current_section:
                    sections.append(current_section)

                level = len(heading_match.group(1))
                title = self.strip_markdown(heading_match.group(2).strip())

                heading_stack = [
                    (l, t) for l, t in heading_stack if l < level
                ]
                heading_stack.append((level, title))

                current_section = {
                    'level': level,
                    'title': title,
                    'content': '',
                    'hierarchy': [t for _, t in heading_stack]
                }
            else:
                if current_section is not None:
                    section = current_section
                    if section['content']:
                        section['content'] += '\n' + line
                    else:
                        section['content'] = line
                else:
                    if not sections or sections[-1]['level'] != 0:
                        sections.append({
                            'level': 0,
                            'title': 'Introduction',
                            'content': line + '\n',
                            'hierarchy': ['Introduction']
                        })
                    else:
                        sections[-1]['content'] += line + '\n'

        if current_section:
            sections.append(current_section)

        # Extract tables from each section and assign section IDs with parent tracking
        parent_stack = []  # Track parent sections by level
        
        for i, section in enumerate(sections):
            # Generate unique section ID
            section_id = self._generate_chunk_id(
                section['title'],
                section['hierarchy']
            )
            section['section_id'] = section_id
            
            # Determine parent section
            current_level = section['level']
            
            # Pop parents that are same level or deeper
            while parent_stack and parent_stack[-1]['level'] >= current_level:
                parent_stack.pop()
            
            # Set parent_section_id
            if parent_stack:
                section['parent_section_id'] = parent_stack[-1]['section_id']
            else:
                section['parent_section_id'] = None
            
            # Add current section to parent stack
            parent_stack.append({
                'section_id': section_id,
                'level': current_level
            })
            
            # Extract tables using LLM or sync method based on flag
            if use_llm:
                # Use LLM-based table extraction with automatic fallback
                section['tables'] = await self.extract_tables_with_llm(
                    section['content']
                )
            else:
                # Use sync heuristics only
                section['tables'] = self._extract_tables_from_text(
                    section['content']
                )

        return sections

    def _create_section_mapping(self, section: Dict, doc_metadata: dict = None) -> dict:
        """Create an optimized section mapping for broad/hierarchical retrieval"""
        section_id = section.get('section_id') or self._generate_chunk_id(section['title'], section['hierarchy'])
        hierarchy_path = " > ".join(section['hierarchy'])
        parent_section_id = section.get('parent_section_id')
        
        tables = section.get('tables', [])
        has_tables = len(tables) > 0
        
        content_text = section['content'].strip()
        
        if has_tables:
            clean_content = self._remove_tables_from_text(content_text)
            
            table_texts = []
            for i, table in enumerate(tables):
                summary = self._get_table_summary(table)
                table_searchable = table['searchable_text']
                table_texts.append(f"\n[Bảng {i+1}] {summary}\n{table_searchable}")
            
            searchable_text = f"[{hierarchy_path}]\n\n{clean_content}\n{''.join(table_texts)}"
        else:
            searchable_text = f"[{hierarchy_path}]\n\n{content_text}"
        
        # Clean metadata - only keep source, remove doc_type as it's added at top-level during ingestion
        clean_metadata = {k: v for k, v in (doc_metadata or {}).items() if k not in ['doc_type']}
        
        section_mapping = {
            'section_id': section_id,
            'parent_section_id': parent_section_id,
            'text': searchable_text,
            'title': section['title'],
            'hierarchy_path': hierarchy_path,
            'level': section['level'],
            'tables': tables,
            'metadata': {
                **clean_metadata,
                'type': 'section',
            }
        }
        
        return section_mapping

    def _chunk_section_mapping(self, section_mapping: Dict, doc_metadata: dict) -> List[dict]:
        """Chunk a section mapping's searchable text into retrievable pieces"""
        searchable_text = section_mapping['text'].strip()
        if not searchable_text:
            return []
        
        # If content fits in one chunk, return as-is
        if len(searchable_text) <= self.chunk_size:
            return [self._create_chunk(
                content=searchable_text,
                section_mapping=section_mapping,
                doc_metadata=doc_metadata,
                chunk_index=0
            )]
        
        # Split by chunk_size, trying to break at newlines when possible
        chunks = []
        start = 0
        
        while start < len(searchable_text):
            end = start + self.chunk_size
            
            # If we're not at the end of text, try to find a good break point
            if end < len(searchable_text):
                # Try to break at newline within last 20% of chunk
                search_start = max(start, end - int(self.chunk_size * 0.2))
                last_newline = searchable_text.rfind('\n', search_start, end)
                
                if last_newline > start:
                    end = last_newline + 1
            
            chunk_text = searchable_text[start:end].strip()
            
            if chunk_text:
                chunks.append(self._create_chunk(
                    content=chunk_text,
                    section_mapping=section_mapping,
                    doc_metadata=doc_metadata,
                    chunk_index=len(chunks)
                ))
            
            start = end

        return chunks if chunks else [self._create_chunk(
            content=searchable_text,
            section_mapping=section_mapping,
            doc_metadata=doc_metadata,
            chunk_index=0
        )]

    def _create_chunk(
        self,
        content: str,
        section_mapping: Dict,
        doc_metadata: dict,
        chunk_index: int
    ) -> dict:
        """Create a chunk dictionary from section mapping's searchable content"""
        section_id = section_mapping.get('section_id')
        parent_section_id = section_mapping.get('parent_section_id')
        hierarchy_path = section_mapping.get('hierarchy_path', '')
        
        # Generate chunk ID
        chunk_id = self._generate_chunk_id(content, [section_mapping.get('title', '')])

        # Create compact hierarchy context
        parts = hierarchy_path.split(' > ')
        if len(parts) <= 2:
            heading_context = hierarchy_path
        else:
            heading_context = f"{parts[0]} > ... > {parts[-1]}"

        # Check if content already starts with hierarchy path (first chunk of section)
        # to avoid duplicating the path prefix
        if content.startswith(f"[{hierarchy_path}]"):
            # Content already has the full path, just add compact context for readability
            full_content = f"[{heading_context}]\n\n{content[len(f'[{hierarchy_path}]'):].strip()}"
        elif content.startswith('['):
            # Content has some other bracket prefix, don't double-prefix
            full_content = content
        else:
            # Content doesn't have path, add compact context
            full_content = f"[{heading_context}]\n\n{content}"
        
        # Clean metadata - only keep source, remove doc_type as it's added at top-level during ingestion
        clean_metadata = {k: v for k, v in (doc_metadata or {}).items() if k not in ['doc_type']}
        
        chunk = {
            'chunk_id': chunk_id,
            'section_id': section_id,
            'text': full_content,
            'metadata': {
                **clean_metadata,
                'type': 'chunk',
                'parent_section_id': parent_section_id,
            }
        }

        return chunk

