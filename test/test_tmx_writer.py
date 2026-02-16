#!/usr/bin/env python3
import os
import sys
import pytest
import tempfile
import zipfile
from pathlib import Path
from lxml import etree

script_path = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(script_path, "..", "src"))
sys.path.insert(0, script_path)

from TMX.TMXWriter import TMXIterWriter
from TMDbApi.TMTranslationUnit import TMTranslationUnit


@pytest.mark.unit
class TestTMXIterWriter:
    """Unit tests for TMXIterWriter class."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory."""
        return tmp_path

    @pytest.fixture
    def sample_segment(self):
        """Create a sample TMTranslationUnit."""
        return TMTranslationUnit({
            "source_text": "Hello world",
            "source_language": "en-GB",
            "target_text": "Hola mundo",
            "target_language": "es-ES",
            "file_name": ["test.tmx"]
        })

    def test_init(self, temp_dir):
        """Initialization should set up header and footer."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        assert writer.filename == filename
        assert writer.srclang == "en-GB"
        assert writer.header is not None
        assert writer.footer is not None
        assert '<body>' in writer.header
        assert '</body>' in writer.footer

    def test_write_iter_single_segment(self, temp_dir, sample_segment):
        """write_iter should yield data for single segment."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        def segment_generator():
            yield sample_segment
        
        # Collect all yielded data
        data_chunks = list(writer.write_iter(segment_generator()))
        assert len(data_chunks) > 0
        
        # Write to file
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close writer
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Verify zip file
        assert Path(filename).exists()
        with zipfile.ZipFile(filename, 'r') as zf:
            files = zf.namelist()
            assert "pangeatm.tmx" in files or len(files) > 0

    def test_write_iter_multiple_segments(self, temp_dir):
        """write_iter should handle multiple segments."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        segments = [
            TMTranslationUnit({
                "source_text": "First",
                "source_language": "en-GB",
                "target_text": "Primero",
                "target_language": "es-ES",
                "file_name": ["test.tmx"]
            }),
            TMTranslationUnit({
                "source_text": "Second",
                "source_language": "en-GB",
                "target_text": "Segundo",
                "target_language": "es-ES",
                "file_name": ["test.tmx"]
            })
        ]
        
        def segment_generator():
            for seg in segments:
                yield seg
        
        # Collect all yielded data
        data_chunks = list(writer.write_iter(segment_generator()))
        assert len(data_chunks) > 0
        
        # Write to file
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close writer
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Verify zip file
        assert Path(filename).exists()
        with zipfile.ZipFile(filename, 'r') as zf:
            tmx_content = zf.read("pangeatm.tmx").decode('utf-8')
            assert "First" in tmx_content
            assert "Second" in tmx_content

    def test_write_iter_custom_filename(self, temp_dir, sample_segment):
        """write_iter should use custom filename."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        def segment_generator():
            yield sample_segment
        
        data_chunks = list(writer.write_iter(segment_generator(), fname="custom.tmx"))
        
        # Write to file
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close writer
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Verify zip file
        with zipfile.ZipFile(filename, 'r') as zf:
            files = zf.namelist()
            assert "custom.tmx" in files

    def test_write_iter_header_footer(self, temp_dir, sample_segment):
        """write_iter should include header and footer."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        def segment_generator():
            yield sample_segment
        
        data_chunks = list(writer.write_iter(segment_generator()))
        
        # Write to file
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close writer
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Verify structure
        with zipfile.ZipFile(filename, 'r') as zf:
            tmx_content = zf.read("pangeatm.tmx").decode('utf-8')
            assert '<tmx' in tmx_content
            assert '<header' in tmx_content
            assert '<body>' in tmx_content
            assert '</body>' in tmx_content
            assert '</tmx>' in tmx_content

    def test_write_close(self, temp_dir, sample_segment):
        """write_close should finalize zip file."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        def segment_generator():
            yield sample_segment
        
        # Write iter
        data_chunks = list(writer.write_iter(segment_generator()))
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Should be valid zip
        assert Path(filename).exists()
        with zipfile.ZipFile(filename, 'r') as zf:
            # Should be able to read without errors
            files = zf.namelist()
            assert len(files) > 0

    def test_write_iter_encoding(self, temp_dir, sample_segment):
        """write_iter should use UTF-8 encoding."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        def segment_generator():
            yield sample_segment
        
        data_chunks = list(writer.write_iter(segment_generator()))
        
        # Write to file
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close writer
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Verify encoding
        with zipfile.ZipFile(filename, 'r') as zf:
            tmx_content = zf.read("pangeatm.tmx").decode('utf-8')
            assert isinstance(tmx_content, str)

    def test_write_iter_pretty_print(self, temp_dir, sample_segment):
        """write_iter should use pretty printing."""
        filename = str(temp_dir / "output.zip")
        writer = TMXIterWriter(filename, "en-GB")
        
        def segment_generator():
            yield sample_segment
        
        data_chunks = list(writer.write_iter(segment_generator()))
        
        # Write to file
        with open(filename, 'wb') as f:
            for chunk in data_chunks:
                f.write(chunk)
        
        # Close writer
        close_chunks = list(writer.write_close())
        with open(filename, 'ab') as f:
            for chunk in close_chunks:
                f.write(chunk)
        
        # Verify pretty print
        with zipfile.ZipFile(filename, 'r') as zf:
            tmx_content = zf.read("pangeatm.tmx").decode('utf-8')
            # Should have newlines for pretty print
            assert '\n' in tmx_content

