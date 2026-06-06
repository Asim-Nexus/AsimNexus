"""
Data Lake: Text Extractor
=========================
Extracts and normalizes text content from various document formats.

Supports:
- Plain text (.txt)
- HTML (.html, .htm)
- Markdown (.md)
- JSON (.json)
- XML (.xml)
- CSV (.csv)
"""

import csv
import html
import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("DataLake.TextExtractor")


@dataclass
class ExtractedContent:
    """Result of text extraction."""
    source_path: str
    content: str
    format: str
    title: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    sections: List[Dict[str, Any]] = field(default_factory=list)
    extraction_timestamp: str = ""
    
    def __post_init__(self):
        if not self.extraction_timestamp:
            self.extraction_timestamp = datetime.utcnow().isoformat()


class TextExtractor:
    """
    Extracts and normalizes text from various document formats.
    Auto-detects format from file extension.
    """
    
    SUPPORTED_FORMATS = {".txt", ".html", ".htm", ".md", ".json", ".xml", ".csv"}
    
    def extract(self, path: str, metadata: Dict[str, Any] = None) -> Optional[ExtractedContent]:
        """
        Extract text content from a file.
        
        Args:
            path: Path to the file
            metadata: Optional metadata to attach
            
        Returns:
            ExtractedContent, or None on failure
        """
        if not os.path.exists(path):
            logger.error(f"File not found: {path}")
            return None
        
        ext = Path(path).suffix.lower()
        if ext not in self.SUPPORTED_FORMATS:
            logger.warning(f"Unsupported format: {ext}")
            return None
        
        metadata = metadata or {}
        title = metadata.get("title", Path(path).stem)
        
        try:
            if ext == ".txt":
                return self._extract_txt(path, title, metadata)
            elif ext in (".html", ".htm"):
                return self._extract_html(path, title, metadata)
            elif ext == ".md":
                return self._extract_md(path, title, metadata)
            elif ext == ".json":
                return self._extract_json(path, title, metadata)
            elif ext == ".xml":
                return self._extract_xml(path, title, metadata)
            elif ext == ".csv":
                return self._extract_csv(path, title, metadata)
        except Exception as e:
            logger.error(f"Failed to extract {path}: {e}")
            return None
    
    def _extract_txt(self, path: str, title: str, metadata: Dict) -> ExtractedContent:
        """Extract from plain text."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        return ExtractedContent(
            source_path=path,
            content=content,
            format="txt",
            title=title,
            metadata={"format": "txt", **metadata},
        )
    
    def _extract_html(self, path: str, title: str, metadata: Dict) -> ExtractedContent:
        """Extract from HTML."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()
        
        # Remove scripts and styles
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Extract text
        text = re.sub(r'<[^>]+>', ' ', html_content)
        text = html.unescape(text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Try to extract title from HTML
        title_match = re.search(r'<title[^>]*>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = html.unescape(title_match.group(1).strip())
        
        return ExtractedContent(
            source_path=path,
            content=text,
            format="html",
            title=title,
            metadata={"format": "html", **metadata},
        )
    
    def _extract_md(self, path: str, title: str, metadata: Dict) -> ExtractedContent:
        """Extract from Markdown."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        
        # Try to extract title from first heading
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        
        # Extract sections from headings
        sections = []
        current_section = None
        for line in content.split("\n"):
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                if current_section:
                    sections.append(current_section)
                current_section = {
                    "level": len(heading_match.group(1)),
                    "title": heading_match.group(2).strip(),
                    "content": "",
                }
            elif current_section:
                current_section["content"] += line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        return ExtractedContent(
            source_path=path,
            content=content,
            format="md",
            title=title,
            metadata={"format": "markdown", **metadata},
            sections=sections,
        )
    
    def _extract_json(self, path: str, title: str, metadata: Dict) -> ExtractedContent:
        """Extract from JSON."""
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        
        content = json.dumps(data, indent=2, ensure_ascii=False)
        
        return ExtractedContent(
            source_path=path,
            content=content,
            format="json",
            title=title,
            metadata={"format": "json", "structured": True, **metadata},
        )
    
    def _extract_xml(self, path: str, title: str, metadata: Dict) -> ExtractedContent:
        """Extract from XML."""
        tree = ET.parse(path)
        root = tree.getroot()
        
        def _get_text(element) -> str:
            texts = [element.text or ""]
            for child in element:
                texts.append(_get_text(child))
                texts.append(child.tail or "")
            return " ".join(filter(None, texts))
        
        content = _get_text(root)
        content = re.sub(r'\s+', ' ', content).strip()
        
        return ExtractedContent(
            source_path=path,
            content=content,
            format="xml",
            title=title,
            metadata={"format": "xml", **metadata},
        )
    
    def _extract_csv(self, path: str, title: str, metadata: Dict) -> ExtractedContent:
        """Extract from CSV."""
        rows = []
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                rows.append(row)
        
        content = "\n".join([",".join(row) for row in rows])
        
        return ExtractedContent(
            source_path=path,
            content=content,
            format="csv",
            title=title,
            metadata={"format": "csv", "rows": len(rows), **metadata},
        )
    
    def extract_directory(self, directory: str, recursive: bool = True) -> List[ExtractedContent]:
        """Extract text from all supported files in a directory."""
        results = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in Path(directory).glob(pattern):
            if file_path.suffix.lower() in self.SUPPORTED_FORMATS:
                doc = self.extract(str(file_path))
                if doc:
                    results.append(doc)
        
        return results


# Singleton
text_extractor = TextExtractor()
