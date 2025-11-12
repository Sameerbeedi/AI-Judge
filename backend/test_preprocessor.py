"""
Test Script for Argument Preprocessing
Demonstrates all preprocessing features
"""

import asyncio
from argument_preprocessor import (
    ArgumentPreprocessor, 
    ArgumentParser, 
    ArgumentFormat,
    FileValidator
)
from fastapi import UploadFile
import io

# Create sample arguments in different formats

# 1. Numbered format
numbered_argument = """
PLAINTIFF'S ARGUMENT - BREACH OF CONTRACT CASE

1. CLEAR CONTRACTUAL OBLIGATIONS:
The contract explicitly stated that the defendant would deliver a fully functional ERP system with the following modules.

2. MATERIAL BREACH BY DEFENDANT:
The defendant failed to deliver the complete system by the agreed deadline.

3. FINANCIAL DAMAGES:
Due to the defendant's breach, the plaintiff suffered significant damages totaling ₹41,50,000.

4. GOOD FAITH EFFORTS BY PLAINTIFF:
We demonstrated good faith throughout the entire process.

5. DEFENDANT'S NEGLIGENCE:
Evidence shows the defendant assigned junior developers without adequate supervision.
"""

# 2. Lettered format
lettered_argument = """
DEFENDANT'S RESPONSE

a) Plaintiff Failed to Provide Requirements:
The plaintiff repeatedly changed requirements without proper documentation.

b) Technical Challenges Were Unforeseen:
We encountered technical limitations that were not apparent during initial assessment.

c) Extension Requests Were Denied:
Our requests for timeline extensions were unreasonably denied.

d) Partial Payment Withheld:
The plaintiff withheld payments which impacted our ability to allocate resources.
"""

# 3. Bullet point format
bullet_argument = """
KEY ARGUMENTS FOR THE DEFENSE

- The contract terms were ambiguous and subject to interpretation
- Plaintiff provided incomplete specifications leading to delays
- Force majeure events affected project timeline
- Multiple change requests altered the project scope significantly
- Payment delays caused resource allocation issues
"""

# 4. Roman numerals format
roman_argument = """
COUNTERARGUMENTS

I. Contractual Interpretation:
The contract must be read in its entirety considering all clauses.

II. Mutual Mistakes:
Both parties made assumptions that proved incorrect.

III. Substantial Performance:
The defendant substantially performed under the contract.

IV. Mitigation of Damages:
The plaintiff failed to mitigate their damages.
"""


async def test_format_detection():
    """Test automatic format detection"""
    print("=" * 60)
    print("TEST 1: Format Detection")
    print("=" * 60)
    
    parser = ArgumentParser()
    
    formats_to_test = {
        "Numbered": numbered_argument,
        "Lettered": lettered_argument,
        "Bullet": bullet_argument,
        "Roman": roman_argument
    }
    
    for name, text in formats_to_test.items():
        detected = parser.detect_format(text)
        print(f"\n{name} format detected as: {detected.value}")
        
        # Extract points
        points = parser.extract_points(text, detected)
        print(f"  Points found: {len(points)}")
        for i, point in enumerate(points[:2], 1):  # Show first 2
            print(f"    {i}. [{point['index']}] {point['content'][:60]}...")


async def test_file_validation():
    """Test file validation"""
    print("\n" + "=" * 60)
    print("TEST 2: File Validation")
    print("=" * 60)
    
    validator = FileValidator()
    
    # Test valid extensions
    valid_files = ["argument.txt", "brief.pdf", "case.docx", "evidence.doc"]
    invalid_files = ["image.jpg", "data.xlsx", "script.py"]
    
    print("\nValid file extensions:")
    for filename in valid_files:
        is_valid = validator.validate_extension(filename)
        print(f"  {filename}: {'✓ Valid' if is_valid else '✗ Invalid'}")
    
    print("\nInvalid file extensions:")
    for filename in invalid_files:
        is_valid = validator.validate_extension(filename)
        print(f"  {filename}: {'✓ Valid' if is_valid else '✗ Invalid'}")


async def test_argument_sequencing():
    """Test argument sequencing and ordering"""
    print("\n" + "=" * 60)
    print("TEST 3: Argument Sequencing")
    print("=" * 60)
    
    from argument_preprocessor import ArgumentSequencer
    
    sequencer = ArgumentSequencer()
    
    # Simulate alternating arguments
    arguments = [
        {'side': 'A', 'order': 1, 'text': 'Opening argument for plaintiff'},
        {'side': 'B', 'order': 2, 'text': 'Defense response'},
        {'side': 'A', 'order': 3, 'text': 'Plaintiff rebuttal'},
        {'side': 'B', 'order': 4, 'text': 'Defense counter-argument'},
        {'side': 'A', 'order': 5, 'text': 'Final plaintiff argument'},
    ]
    
    result = sequencer.process_argument_sequence(arguments)
    
    print(f"\nTotal rounds: {result['total_rounds']}")
    print(f"Is balanced: {result['is_balanced']}")
    print(f"Side A arguments: {len(result['side_a'])}")
    print(f"Side B arguments: {len(result['side_b'])}")
    
    print("\nArgument sequence:")
    for i, arg in enumerate(arguments, 1):
        print(f"  {i}. Side {arg['side']}: {arg['text'][:50]}...")
    
    # Test imbalanced arguments
    print("\n\nTesting imbalanced arguments:")
    is_valid, msg = sequencer.validate_argument_balance(5, 3, max_difference=1)
    print(f"  5 vs 3 arguments: {'✓ Valid' if is_valid else '✗ Invalid'}")
    if msg:
        print(f"  Message: {msg}")


async def test_text_cleaning():
    """Test text cleaning and normalization"""
    print("\n" + "=" * 60)
    print("TEST 4: Text Cleaning")
    print("=" * 60)
    
    parser = ArgumentParser()
    
    # Messy text with extra spaces, special characters
    messy_text = """
    This    text   has    multiple     spaces.
    
    
    It also has   excessive    line breaks.
    
    And some special characters: \x00\x1f that should be removed.
    """
    
    cleaned = parser.clean_text(messy_text)
    
    print("\nOriginal text:")
    print(repr(messy_text[:100]))
    print("\nCleaned text:")
    print(repr(cleaned[:100]))


async def test_point_extraction():
    """Test extracting structured points from arguments"""
    print("\n" + "=" * 60)
    print("TEST 5: Point Extraction")
    print("=" * 60)
    
    parser = ArgumentParser()
    
    # Extract from numbered format
    points = parser.extract_points(numbered_argument, ArgumentFormat.NUMBERED)
    
    print(f"\nExtracted {len(points)} points from numbered argument:")
    for point in points:
        print(f"\n  Point {point['index']}:")
        print(f"    {point['content'][:100]}...")


async def test_complete_preprocessing():
    """Test complete preprocessing pipeline"""
    print("\n" + "=" * 60)
    print("TEST 6: Complete Preprocessing Pipeline")
    print("=" * 60)
    
    preprocessor = ArgumentPreprocessor()
    
    # Create mock UploadFile
    class MockUploadFile:
        def __init__(self, content, filename):
            self.content = content
            self.filename = filename
            self.position = 0
        
        async def read(self):
            return self.content.encode('utf-8')
        
        async def seek(self, position):
            self.position = position
    
    # Test with numbered argument
    mock_file = MockUploadFile(numbered_argument, "plaintiff_argument.txt")
    
    try:
        result = await preprocessor.process_file(mock_file)
        
        print("\nPreprocessing Results:")
        print(f"  Filename: {result['filename']}")
        print(f"  Format detected: {result['format']}")
        print(f"  Word count: {result['metadata']['word_count']}")
        print(f"  Character count: {result['metadata']['char_count']}")
        print(f"  Points extracted: {result['metadata']['point_count']}")
        print(f"  File size: {result['metadata']['file_size_kb']:.2f} KB")
        
        print("\n  First 3 points:")
        for i, point in enumerate(result['points'][:3], 1):
            print(f"    {i}. [{point['index']}] {point['content'][:60]}...")
    
    except Exception as e:
        print(f"  Error: {e}")


async def test_case_validation():
    """Test complete case validation"""
    print("\n" + "=" * 60)
    print("TEST 7: Case Validation")
    print("=" * 60)
    
    preprocessor = ArgumentPreprocessor()
    
    # Simulate processed data for both sides
    side_a_data = {
        'combined_text': numbered_argument,
        'all_points': [{'index': str(i), 'content': f'Point {i}'} for i in range(1, 6)],
        'summary': {
            'file_count': 1,
            'total_words': 150,
            'total_points': 5
        }
    }
    
    side_b_data = {
        'combined_text': lettered_argument,
        'all_points': [{'index': chr(97+i), 'content': f'Point {chr(97+i)}'} for i in range(4)],
        'summary': {
            'file_count': 1,
            'total_words': 120,
            'total_points': 4
        }
    }
    
    validation = preprocessor.validate_case_arguments(side_a_data, side_b_data)
    
    print("\nValidation Results:")
    print(f"  Is Valid: {validation['is_valid']}")
    print(f"\n  Issues: {validation['issues'] if validation['issues'] else 'None'}")
    print(f"  Warnings: {validation['warnings'] if validation['warnings'] else 'None'}")
    
    print("\n  Statistics:")
    print(f"    Side A: {validation['statistics']['side_a']['points']} points, "
          f"{validation['statistics']['side_a']['words']} words")
    print(f"    Side B: {validation['statistics']['side_b']['points']} points, "
          f"{validation['statistics']['side_b']['words']} words")


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ARGUMENT PREPROCESSING TEST SUITE" + " " * 14 + "║")
    print("╚" + "=" * 58 + "╝")
    
    await test_format_detection()
    await test_file_validation()
    await test_argument_sequencing()
    await test_text_cleaning()
    await test_point_extraction()
    await test_complete_preprocessing()
    await test_case_validation()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
