#!/usr/bin/env python3
"""
Unit Tests for Phonetic Analysis Functions
Comprehensive testing of core phonetic algorithms
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from rhyme_core.phonetics import parse_pron, rhyme_tail, k_keys, extract_stress

class TestParsePron:
    """Test pronunciation parsing functionality"""
    
    def test_parse_pron_basic(self):
        """Test basic pronunciation parsing"""
        phones = parse_pron("D AH1 B AH0 L")
        expected = ["D", "AH1", "B", "AH0", "L"]
        assert phones == expected
    
    def test_parse_pron_with_spaces(self):
        """Test parsing with extra spaces"""
        phones = parse_pron("  D  AH1  B  AH0  L  ")
        expected = ["D", "AH1", "B", "AH0", "L"]
        assert phones == expected
    
    def test_parse_pron_empty(self):
        """Test parsing empty string"""
        phones = parse_pron("")
        assert phones == []
    
    def test_parse_pron_single_phone(self):
        """Test parsing single phoneme"""
        phones = parse_pron("AH1")
        assert phones == ["AH1"]

class TestRhymeTail:
    """Test rhyme tail extraction functionality"""
    
    def test_rhyme_tail_basic(self):
        """Test basic rhyme tail extraction"""
        phones = ["D", "AH1", "B", "AH0", "L"]
        vowel, coda = rhyme_tail(phones)
        assert vowel == "AH"
        assert coda == ("B", "AH0", "L")
    
    def test_rhyme_tail_stressed_vowel(self):
        """Test rhyme tail with stressed vowel"""
        phones = ["T", "AH1", "B", "AH0", "L"]
        vowel, coda = rhyme_tail(phones)
        assert vowel == "AH"
        assert coda == ("B", "AH0", "L")
    
    def test_rhyme_tail_no_stress(self):
        """Test rhyme tail with no stressed vowels"""
        phones = ["D", "AH0", "B", "AH0", "L"]
        vowel, coda = rhyme_tail(phones)
        assert vowel == "AH"
        assert coda == ("B", "AH0", "L")
    
    def test_rhyme_tail_multiple_stressed(self):
        """Test rhyme tail with multiple stressed vowels"""
        phones = ["D", "AH1", "B", "AH1", "L"]
        vowel, coda = rhyme_tail(phones)
        assert vowel == "AH"
        assert coda == ("B", "AH1", "L")
    
    def test_rhyme_tail_no_vowels(self):
        """Test rhyme tail with no vowels"""
        phones = ["D", "B", "L"]
        vowel, coda = rhyme_tail(phones)
        assert vowel == ""
        assert coda == ()
    
    def test_rhyme_tail_empty(self):
        """Test rhyme tail with empty input"""
        phones = []
        vowel, coda = rhyme_tail(phones)
        assert vowel == ""
        assert coda == ()

class TestKKeys:
    """Test K-key generation functionality"""
    
    def test_k_keys_basic(self):
        """Test basic K-key generation"""
        phones = ["D", "AH1", "B", "AH0", "L"]
        k1, k2, k3 = k_keys(phones)
        
        assert k1 == "AH"
        assert k2 == "AH|B AH0 L"
        assert k3 == "AH1|B AH0 L"
    
    def test_k_keys_no_coda(self):
        """Test K-key generation with no coda"""
        phones = ["AH1"]
        k1, k2, k3 = k_keys(phones)
        
        assert k1 == "AH"
        assert k2 == "AH|"
        assert k3 == "AH1|"
    
    def test_k_keys_complex(self):
        """Test K-key generation with complex coda"""
        phones = ["S", "T", "AH1", "R", "AH0", "N", "G"]
        k1, k2, k3 = k_keys(phones)
        
        assert k1 == "AH"
        assert k2 == "AH|R AH0 N G"
        assert k3 == "AH1|R AH0 N G"
    
    def test_k_keys_different_stress(self):
        """Test K-key generation with different stress patterns"""
        # Test with stress on first vowel
        phones1 = ["T", "AH1", "B", "AH0", "L"]
        k1_1, k2_1, k3_1 = k_keys(phones1)
        
        # Test with stress on second vowel
        phones2 = ["T", "AH0", "B", "AH1", "L"]
        k1_2, k2_2, k3_2 = k_keys(phones2)
        
        # K1 and K2 should be the same (stress-agnostic)
        assert k1_1 == k1_2 == "AH"
        assert k2_1 == k2_2 == "AH|B AH0 L"
        
        # K3 should be different (stress-preserved)
        assert k3_1 == "AH1|B AH0 L"
        assert k3_2 == "AH0|B AH1 L"

class TestExtractStress:
    """Test stress pattern extraction functionality"""
    
    def test_extract_stress_basic(self):
        """Test basic stress extraction"""
        phones = ["D", "AH1", "B", "AH0", "L"]
        stress = extract_stress(phones)
        assert stress == "1-0"
    
    def test_extract_stress_single_syllable(self):
        """Test stress extraction for single syllable"""
        phones = ["AH1"]
        stress = extract_stress(phones)
        assert stress == "1"
    
    def test_extract_stress_no_stress(self):
        """Test stress extraction with no stressed vowels"""
        phones = ["D", "AH0", "B", "AH0", "L"]
        stress = extract_stress(phones)
        assert stress == "0-0"
    
    def test_extract_stress_multiple_stressed(self):
        """Test stress extraction with multiple stressed vowels"""
        phones = ["D", "AH1", "B", "AH1", "L"]
        stress = extract_stress(phones)
        assert stress == "1-1"
    
    def test_extract_stress_complex(self):
        """Test stress extraction with complex pattern"""
        phones = ["S", "T", "AH1", "R", "AH0", "N", "G"]
        stress = extract_stress(phones)
        assert stress == "1-0"

class TestPhoneticIntegration:
    """Integration tests for phonetic functions"""
    
    def test_double_word_analysis(self):
        """Test complete phonetic analysis for 'double'"""
        phones = parse_pron("D AH1 B AH0 L")
        vowel, coda = rhyme_tail(phones)
        k1, k2, k3 = k_keys(phones)
        stress = extract_stress(phones)
        
        # Verify all components
        assert vowel == "AH"
        assert coda == ("B", "AH0", "L")
        assert k1 == "AH"
        assert k2 == "AH|B AH0 L"
        assert k3 == "AH1|B AH0 L"
        assert stress == "1-0"
    
    def test_trouble_word_analysis(self):
        """Test complete phonetic analysis for 'trouble'"""
        phones = parse_pron("T R AH1 B AH0 L")
        vowel, coda = rhyme_tail(phones)
        k1, k2, k3 = k_keys(phones)
        stress = extract_stress(phones)
        
        # Verify all components
        assert vowel == "AH"
        assert coda == ("B", "AH0", "L")
        assert k1 == "AH"
        assert k2 == "AH|B AH0 L"
        assert k3 == "AH1|B AH0 L"
        assert stress == "1-0"
    
    def test_rhyme_matching(self):
        """Test that 'double' and 'trouble' have matching K2 keys"""
        double_phones = parse_pron("D AH1 B AH0 L")
        trouble_phones = parse_pron("T R AH1 B AH0 L")
        
        _, double_k2, _ = k_keys(double_phones)
        _, trouble_k2, _ = k_keys(trouble_phones)
        
        # They should have the same K2 key (perfect rhyme by ear)
        assert double_k2 == trouble_k2 == "AH|B AH0 L"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])


