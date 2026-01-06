"""
Test script for LLM-based table type detection in chunker
"""
import asyncio
from app.utils.chunker import MarkdownStructureChunker

# Sample markdown with different table types
TEST_MD_KEYPAIR = """
# Thông tin môn học

| Thông tin | Giá trị |
|-----------|---------|
| Tên môn học | Lập trình Python |
| Mã môn | IT001 |
| Số tín chỉ | 3 |
| Khoa | Công nghệ thông tin |
"""

TEST_MD_STANDARD = """
# Danh sách môn học

| STT | Mã môn | Tên môn | Số TC |
|-----|--------|---------|-------|
| 1 | IT001 | Lập trình Python | 3 |
| 2 | IT002 | Cơ sở dữ liệu | 4 |
| 3 | IT003 | Mạng máy tính | 3 |
"""

async def test_table_type_detection():
    chunker = MarkdownStructureChunker()
    
    print("=" * 60)
    print("TEST 1: KEYPAIR TABLE (using LLM)")
    print("=" * 60)
    result1 = await chunker.chunk_markdown(TEST_MD_KEYPAIR)
    
    for section in result1['sections']:
        if section.get('tables'):
            for table in section['tables']:
                print(f"Table Type: {table['table_type']}")
                print(f"Searchable Text:\n{table['searchable_text']}")
                print()
    
    print("=" * 60)
    print("TEST 2: STANDARD TABLE (using LLM)")
    print("=" * 60)
    result2 = await chunker.chunk_markdown(TEST_MD_STANDARD)
    
    for section in result2['sections']:
        if section.get('tables'):
            for table in section['tables']:
                print(f"Table Type: {table['table_type']}")
                print(f"Searchable Text:\n{table['searchable_text']}")
                print()
    
    print("=" * 60)
    print("TEST 3: KEYPAIR TABLE (using sync heuristics only)")
    print("=" * 60)
    sections = await chunker.parse_sections(TEST_MD_KEYPAIR, use_llm=False)
    for section in sections:
        if section.get('tables'):
            for table in section['tables']:
                print(f"Table Type: {table['table_type']}")
                print(f"Searchable Text:\n{table['searchable_text']}")
                print()

if __name__ == "__main__":
    asyncio.run(test_table_type_detection())
