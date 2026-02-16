#!/usr/bin/env python3
import os
import sys
import pytest
import tempfile
import zipfile
from pathlib import Path

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from TMX.TMXParser import TMXParser
from TMDbApi.TMTranslationUnit import TMTranslationUnit


def create_minimal_tmx(content=None):
    """Create a minimal valid TMX file."""
    if content is None:
        content = """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z" changedate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Hello world</seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Hola mundo</seg>
</tuv>
</tu>
</body>
</tmx>"""
    return content


def create_tmx_with_metadata():
    """Create TMX file with metadata properties."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z" changedate="20090914T114332Z" tuid="test-123">
<prop type="tda-industry">Automotive Manufacturing</prop>
<prop type="tda-type">Instructions for Use</prop>
<prop type="tda-org">Pangeanic</prop>
<prop type="custom-prop">Custom Value</prop>
<tuv xml:lang="en-GB">
<prop type="tuv-prop">Source Metadata</prop>
<seg>Hello world</seg>
</tuv>
<tuv xml:lang="es-ES">
<prop type="tuv-prop">Target Metadata</prop>
<seg>Hola mundo</seg>
</tuv>
</tu>
</body>
</tmx>"""


def create_tmx_with_tags():
    """Create TMX file with XML tags in segments."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Hello <b>world</b></seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Hola <i>mundo</i></seg>
</tuv>
</tu>
</body>
</tmx>"""


def create_tmx_multiple_langs():
    """Create TMX file with multiple language pairs."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Hello</seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Hola</seg>
</tuv>
<tuv xml:lang="fr-FR">
<seg>Bonjour</seg>
</tuv>
</tu>
</body>
</tmx>"""


def create_tmx_with_lang_attr():
    """Create TMX file using lang attribute instead of xml:lang."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv lang="en-GB">
<seg>Hello world</seg>
</tuv>
<tuv lang="es-ES">
<seg>Hola mundo</seg>
</tuv>
</tu>
</body>
</tmx>"""


@pytest.mark.unit
class TestTMXParser:
    """Unit tests for TMXParser class."""

    @pytest.fixture
    def temp_tmx_file(self, tmp_path):
        """Create a temporary TMX file."""
        def _create(content):
            tmx_file = tmp_path / "test.tmx"
            tmx_file.write_text(content, encoding='utf-8')
            return str(tmx_file)
        return _create

    @pytest.fixture
    def temp_zip_file(self, tmp_path):
        """Create a temporary zip file with TMX."""
        def _create(content, filename="test.tmx"):
            zip_file = tmp_path / "test.zip"
            with zipfile.ZipFile(zip_file, 'w') as zf:
                zf.writestr(filename, content.encode('utf-8'))
            return str(zip_file)
        return _create

    def test_init_basic(self, temp_tmx_file):
        """Basic initialization."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path)
        assert parser.fname == tmx_path
        assert parser.domain is None
        assert parser.lang_pairs == []
        assert parser.username is None

    def test_init_with_domain(self, temp_tmx_file):
        """Initialization with domain."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path, domain="test-domain")
        assert parser.domain == "test-domain"

    def test_init_with_lang_pairs(self, temp_tmx_file):
        """Initialization with language pairs."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path, lang_pairs=[("en", "es")])
        assert parser.lang_pairs == [("en", "es")]

    def test_init_with_username(self, temp_tmx_file):
        """Initialization with username."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path, username="testuser")
        assert parser.username == "testuser"

    def test_parse_simple_tmx(self, temp_tmx_file):
        """Parse simple TMX file."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        assert segment.source_text == "Hello world"
        assert segment.target_text == "Hola mundo"
        assert segment.source_language == "en"
        assert segment.target_language == "es"

    def test_parse_tmx_from_zip(self, temp_zip_file):
        """Parse TMX file from zip archive."""
        zip_path = temp_zip_file(create_minimal_tmx())
        parser = TMXParser(zip_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        assert segment.source_text == "Hello world"
        assert segment.target_text == "Hola mundo"

    def test_parse_tmx_with_metadata(self, temp_tmx_file):
        """Parse TMX file with metadata."""
        tmx_path = temp_tmx_file(create_tmx_with_metadata())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        assert segment.industry == "Automotive Manufacturing"
        assert segment.type == "Instructions for Use"
        assert segment.organization == "Pangeanic"
        assert segment.tuid == "test-123"
        assert segment.metadata is not None
        assert segment.metadata.get("custom-prop") == "Custom Value"

    def test_parse_tmx_with_tuv_metadata(self, temp_tmx_file):
        """Parse TMX file with tuv-level metadata."""
        tmx_path = temp_tmx_file(create_tmx_with_metadata())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        assert segment.source_metadata is not None
        assert segment.target_metadata is not None
        assert segment.source_metadata.get("tuv-prop") == "Source Metadata"
        assert segment.target_metadata.get("tuv-prop") == "Target Metadata"

    def test_parse_tmx_with_tags(self, temp_tmx_file):
        """Parse TMX file with XML tags in segments."""
        tmx_path = temp_tmx_file(create_tmx_with_tags())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        # Tags should be processed by TMXmlTagPreprocessor
        assert "world" in segment.source_text
        assert "mundo" in segment.target_text

    def test_parse_tmx_with_domain(self, temp_tmx_file):
        """Parse TMX file with domain assignment."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path, domain="test-domain")
        segments = list(parser.parse())
        assert len(segments) == 1
        assert segments[0].domain == "test-domain"

    def test_parse_tmx_with_username(self, temp_tmx_file):
        """Parse TMX file with username assignment."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path, username="testuser")
        segments = list(parser.parse())
        assert len(segments) == 1
        assert segments[0].username == "testuser"

    def test_parse_tmx_file_name(self, temp_tmx_file):
        """Parse should extract file name."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        # file_name is stored as a string, not a list
        assert segments[0].file_name == "test.tmx"

    def test_parse_tmx_creation_date(self, temp_tmx_file):
        """Parse should extract creation date."""
        tmx_path = temp_tmx_file(create_tmx_with_metadata())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        assert segments[0].tm_creation_date == "20090914T114332Z"

    def test_parse_tmx_change_date(self, temp_tmx_file):
        """Parse should extract change date."""
        tmx_path = temp_tmx_file(create_tmx_with_metadata())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        assert segments[0].tm_change_date == "20090914T114332Z"

    def test_parse_tmx_lang_attr_fallback(self, temp_tmx_file):
        """Parse should handle lang attribute as fallback to xml:lang."""
        tmx_path = temp_tmx_file(create_tmx_with_lang_attr())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        assert segment.source_language == "en"
        assert segment.target_language == "es"

    def test_language_pairs_simple(self, temp_tmx_file):
        """Extract language pairs from simple TMX."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path)
        pairs = parser.language_pairs()
        assert len(pairs) == 1
        assert ("en", "es") in pairs

    def test_language_pairs_multiple(self, temp_tmx_file):
        """Extract language pairs from TMX with multiple languages."""
        tmx_path = temp_tmx_file(create_tmx_multiple_langs())
        parser = TMXParser(tmx_path)
        pairs = parser.language_pairs()
        # Should have en-es, en-fr pairs (or all combinations)
        assert len(pairs) >= 1
        assert any("en" in str(pair[0]) for pair in pairs)

    def test_parse_with_lang_pairs_filter(self, temp_tmx_file):
        """Parse should filter by specified language pairs."""
        tmx_path = temp_tmx_file(create_tmx_multiple_langs())
        parser = TMXParser(tmx_path, lang_pairs=[("en", "es")])
        segments = list(parser.parse())
        # Should only return en-es pairs
        for segment in segments:
            assert segment.source_language == "en"
            assert segment.target_language == "es"

    def test_parse_empty_segments_skipped(self, temp_tmx_file):
        """Empty segments should be skipped."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg></seg>
</tuv>
<tuv xml:lang="es-ES">
<seg></seg>
</tuv>
</tu>
</body>
</tmx>"""
        tmx_path = temp_tmx_file(content)
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        # Empty segments should be skipped
        assert len(segments) == 0

    def test_parse_multiple_tu_elements(self, temp_tmx_file):
        """Parse TMX with multiple tu elements."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>First</seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Primero</seg>
</tuv>
</tu>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Second</seg>
</tuv>
<tuv xml:lang="es-ES">
<seg>Segundo</seg>
</tuv>
</tu>
</body>
</tmx>"""
        tmx_path = temp_tmx_file(content)
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 2
        assert segments[0].source_text == "First"
        assert segments[1].source_text == "Second"

    def test_parse_zip_multiple_files(self, temp_zip_file, tmp_path):
        """Parse zip with multiple TMX files."""
        # Create zip with multiple files
        zip_path = tmp_path / "test.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("file1.tmx", create_minimal_tmx().encode('utf-8'))
            zf.writestr("file2.tmx", create_minimal_tmx().encode('utf-8'))
        
        parser = TMXParser(str(zip_path))
        segments = list(parser.parse())
        # Should parse both files
        assert len(segments) >= 2

    def test_parse_invalid_xml_handled(self, temp_tmx_file):
        """Invalid XML should be handled gracefully."""
        content = """<?xml version="1.0" encoding="UTF-8"?>
<tmx version="1.4">
<header creationtool="Test" creationtoolversion="1" segtype="sentence" 
        o-tmf="various" adminlang="en-US" srclang="en-GB" 
        datatype="PlainText" creationdate="20120216T102714Z" />
<body>
<tu creationdate="20090914T114332Z">
<tuv xml:lang="en-GB">
<seg>Hello</seg>
</tuv>
<!-- Invalid: missing closing tag -->
</body>
</tmx>"""
        tmx_path = temp_tmx_file(content)
        parser = TMXParser(tmx_path)
        # Should not raise exception, but may skip invalid parts
        segments = list(parser.parse())
        # May return 0 segments if XML is too malformed
        assert isinstance(segments, list)

    def test_get_lang_xml_namespace(self, temp_tmx_file):
        """_get_lang should handle xml:lang attribute."""
        tmx_path = temp_tmx_file(create_minimal_tmx())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        # Should successfully parse with xml:lang
        assert len(segments) == 1

    def test_get_lang_fallback(self, temp_tmx_file):
        """_get_lang should fallback to lang attribute."""
        tmx_path = temp_tmx_file(create_tmx_with_lang_attr())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        # Should successfully parse with lang fallback
        assert len(segments) == 1

    def test_parse_metadata_custom_props(self, temp_tmx_file):
        """Parse should include custom properties in metadata."""
        tmx_path = temp_tmx_file(create_tmx_with_metadata())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        assert segments[0].metadata is not None
        assert "custom-prop" in segments[0].metadata

    def test_parse_metadata_tda_props_separate(self, temp_tmx_file):
        """Parse should extract tda- props to separate fields."""
        tmx_path = temp_tmx_file(create_tmx_with_metadata())
        parser = TMXParser(tmx_path)
        segments = list(parser.parse())
        assert len(segments) == 1
        segment = segments[0]
        # tda- props should be in separate fields
        assert segment.industry == "Automotive Manufacturing"
        assert segment.type == "Instructions for Use"
        assert segment.organization == "Pangeanic"
        # And also in metadata
        assert segment.metadata is not None

