#!/usr/bin/env python3
"""
Convert figmaapi.txt HTML to structured JSON for easier parsing.

This script processes the complex HTML file and converts it into a clean,
structured format that's much easier to extract content from.
"""

import json
import re
from pathlib import Path
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional

def clean_text(text: str) -> str:
    """Clean and normalize text content"""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Fix punctuation spacing
    text = re.sub(r'\s*\.\s*', '. ', text)
    text = re.sub(r'\s*,\s*', ', ', text)
    text = re.sub(r'\s*:\s*', ': ', text)
    
    return text.strip()

def extract_code_examples(element: Tag) -> List[Dict]:
    """Extract code examples and API calls"""
    code_examples = []
    
    # Look for code blocks
    code_blocks = element.find_all(['pre', 'code'])
    for code in code_blocks:
        code_text = code.get_text().strip()
        if len(code_text) > 10:
            code_examples.append({
                "type": "code_block",
                "content": code_text,
                "language": "bash" if code_text.startswith("curl") else "json"
            })
    
    # Look for API endpoints
    endpoint_patterns = element.find_all(string=re.compile(r'(GET|POST|PUT|DELETE)\s+/'))
    for pattern in endpoint_patterns:
        if isinstance(pattern, str):
            code_examples.append({
                "type": "api_endpoint",
                "content": pattern.strip(),
                "language": "http"
            })
    
    return code_examples

def extract_tables(element: Tag) -> List[Dict]:
    """Extract structured table data"""
    tables = []
    
    for table in element.find_all('table'):
        table_data = {
            "headers": [],
            "rows": []
        }
        
        # Extract headers
        header_row = table.find('thead')
        if header_row:
            headers = header_row.find_all(['th', 'td'])
            table_data["headers"] = [clean_text(h.get_text()) for h in headers]
        
        # Extract rows
        body = table.find('tbody') or table
        for row in body.find_all('tr'):
            cells = row.find_all(['td', 'th'])
            if cells:
                row_data = [clean_text(cell.get_text()) for cell in cells]
                if row_data and any(row_data):  # Skip empty rows
                    table_data["rows"].append(row_data)
        
        if table_data["headers"] or table_data["rows"]:
            tables.append(table_data)
    
    return tables

def extract_section_content(section_element: Tag, section_id: str) -> Dict:
    """Extract comprehensive content from a section"""
    
    # Extract title
    title = ""
    title_selectors = [
        f'#{section_id} .sectionHeader',
        '.sectionHeader',
        '.subsectionHeader', 
        'h1', 'h2', 'h3'
    ]
    
    for selector in title_selectors:
        title_elem = section_element.select_one(selector)
        if title_elem:
            title = clean_text(title_elem.get_text())
            break
    
    if not title:
        title = section_id.replace('-', ' ').replace('_', ' ').title()
    
    # Remove unwanted elements before text extraction
    content_copy = BeautifulSoup(str(section_element), 'html.parser')
    
    # Remove UI elements, scripts, styles
    for unwanted in content_copy.find_all([
        'script', 'style', 'nav', 'header', 'footer', 'button', 'input',
        'div[class*="personalToken"]', 'div[class*="explorerInput"]'
    ]):
        unwanted.decompose()
    
    # Extract different types of content
    code_examples = extract_code_examples(content_copy)
    tables = extract_tables(content_copy)
    
    # Extract main text content (after removing code blocks and tables)
    for elem in content_copy.find_all(['pre', 'code', 'table']):
        elem.decompose()
    
    main_text = clean_text(content_copy.get_text(separator=' '))
    
    # Extract subsections
    subsections = []
    subsection_headers = content_copy.find_all(class_=re.compile(r'subsectionHeader|subsubsectionHeader'))
    for header in subsection_headers:
        subsection_title = clean_text(header.get_text())
        if subsection_title:
            # Find content until next subsection
            subsection_content = ""
            for sibling in header.find_next_siblings():
                if sibling.get('class') and any('subsectionHeader' in str(cls) for cls in sibling.get('class')):
                    break
                subsection_content += " " + clean_text(sibling.get_text())
            
            if subsection_content.strip():
                subsections.append({
                    "title": subsection_title,
                    "content": clean_text(subsection_content)
                })
    
    return {
        "id": section_id,
        "title": title,
        "main_content": main_text,
        "subsections": subsections,
        "code_examples": code_examples,
        "tables": tables,
        "word_count": len(main_text.split())
    }

def main():
    """Convert HTML to structured JSON"""
    
    # File paths
    html_file = "/Users/aartemov/dev/resale-analyzer/figmaapi.txt"
    output_file = "/Users/aartemov/dev/resale-analyzer/figmaapi_structured.json"
    
    print(f"🔄 Converting {html_file} to structured JSON...")
    
    # Load HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"📄 Loaded HTML file ({len(html_content):,} characters)")
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Define sections to extract
    section_ids = [
        "intro", "authentication", "files", "comments", "users", 
        "version-history", "projects", "library-items", "webhooks_v2",
        "activity_logs", "discovery", "payments", "variables", 
        "dev-resources", "library-analytics", "errors", 
        "scim-api-guide", "changelog"
    ]
    
    # Extract sections
    extracted_sections = []
    found_sections = 0
    
    for section_id in section_ids:
        print(f"🔍 Processing section: {section_id}")
        
        # Find section element
        section_element = soup.find(id=section_id)
        if not section_element:
            # Try alternative approaches
            section_element = soup.find('div', class_=re.compile(r'section'), id=section_id)
        
        if section_element:
            try:
                section_data = extract_section_content(section_element, section_id)
                
                # Only include sections with meaningful content
                if section_data["word_count"] > 20:
                    extracted_sections.append(section_data)
                    found_sections += 1
                    print(f"✅ Extracted {section_data['word_count']} words from {section_id}")
                else:
                    print(f"⚠️  Skipped {section_id} - insufficient content")
            except Exception as e:
                print(f"❌ Error processing {section_id}: {e}")
        else:
            print(f"❌ Section not found: {section_id}")
    
    # Also extract any additional sections found in sidebar
    print("🔍 Looking for additional sections in sidebar...")
    sidebar_links = soup.find_all('a', href=re.compile(r'^#'))
    additional_sections = 0
    
    for link in sidebar_links:
        href = link.get('href', '').lstrip('#')
        if href and href not in section_ids:
            section_element = soup.find(id=href)
            if section_element:
                try:
                    section_data = extract_section_content(section_element, href)
                    if section_data["word_count"] > 20:
                        extracted_sections.append(section_data)
                        additional_sections += 1
                        print(f"✅ Found additional section: {href} ({section_data['word_count']} words)")
                except Exception as e:
                    print(f"❌ Error processing additional section {href}: {e}")
    
    # Create final structure
    structured_data = {
        "source": "Figma API Documentation",
        "extracted_at": "2025-07-24",
        "total_sections": len(extracted_sections),
        "total_words": sum(section["word_count"] for section in extracted_sections),
        "sections": extracted_sections
    }
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n📊 CONVERSION COMPLETE:")
    print(f"   📄 Output file: {output_file}")
    print(f"   📋 Sections extracted: {len(extracted_sections)}")
    print(f"   📝 Total words: {structured_data['total_words']:,}")
    print(f"   💾 File size: {Path(output_file).stat().st_size / 1024:.1f} KB")
    
    # Show section breakdown
    print(f"\n📊 SECTION BREAKDOWN:")
    for section in extracted_sections:
        print(f"   {section['id']}: {section['word_count']} words - {section['title']}")
    
    print(f"\n🎉 Ready for structured extraction!")

if __name__ == "__main__":
    main()