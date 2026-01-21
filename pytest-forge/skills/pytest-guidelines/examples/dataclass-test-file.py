"""
Complete Dataclass Test File Example

This file demonstrates pytest guidelines for testing dataclass classes, including:
- Proper test structure for dataclass verification
- Using is_dataclass() helper function
- Testing dataclass methods
- Naming conventions
- Mock usage with dataclass instances
- Testing mutability and default values
- 100% coverage

Source File: transcript_segment.py
Test File: test_transcript_segment.py
"""

# =============================================================================
# SOURCE FILE (transcript_segment.py)
# =============================================================================
"""
from dataclasses import dataclass, field


@dataclass
class TranscriptSegment:
    speaker: str
    text: str
    chunk: int
    start: float
    end: float
    confidence: float = 1.0
    tags: list[str] = field(default_factory=list)

    def duration(self) -> float:
        return self.end - self.start

    def is_confident(self, threshold: float = 0.8) -> bool:
        return self.confidence >= threshold

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def format_time_range(self) -> str:
        return f"{self.start:.2f}s - {self.end:.2f}s"

    def word_count(self) -> int:
        return len(self.text.split())

    def is_long_segment(self, min_words: int = 50) -> bool:
        return self.word_count() >= min_words
"""

# =============================================================================
# TEST FILE (test_transcript_segment.py)
# =============================================================================
from unittest.mock import patch

import pytest
from transcript_segment import TranscriptSegment

# Note: is_dataclass is automatically available from conftest.py
# See examples/conftest.py for the helper function definition


# =============================================================================
# TEST FUNCTIONS
# =============================================================================

def test_class():
    """Verify TranscriptSegment is a dataclass with correct fields."""
    tested = TranscriptSegment
    fields = {
        "speaker": "str",
        "text": "str",
        "chunk": "int",
        "start": "float",
        "end": "float",
        "confidence": "float",
        "tags": "list[str]",
    }
    assert is_dataclass(tested, fields)


# Test: __init__ with required fields only
def test___init____required_only():
    """Test TranscriptSegment initialization with required fields only"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Hello world",
        chunk=1,
        start=0.0,
        end=2.5
    )

    exp_speaker = "Alice"
    exp_text = "Hello world"
    exp_chunk = 1
    exp_start = 0.0
    exp_end = 2.5
    exp_confidence = 1.0  # Default value
    exp_tags = []  # Default value

    assert tested.speaker == exp_speaker
    assert tested.text == exp_text
    assert tested.chunk == exp_chunk
    assert tested.start == exp_start
    assert tested.end == exp_end
    assert tested.confidence == exp_confidence
    assert tested.tags == exp_tags


def test___init____with_optional_fields():
    """Test TranscriptSegment initialization with optional fields"""
    tested = TranscriptSegment(
        speaker="Bob",
        text="Test message",
        chunk=2,
        start=2.5,
        end=5.0,
        confidence=0.95,
        tags=["important"]
    )

    exp_speaker = "Bob"
    exp_text = "Test message"
    exp_chunk = 2
    exp_start = 2.5
    exp_end = 5.0
    exp_confidence = 0.95
    exp_tags = ["important"]

    assert tested.speaker == exp_speaker
    assert tested.text == exp_text
    assert tested.chunk == exp_chunk
    assert tested.start == exp_start
    assert tested.end == exp_end
    assert tested.confidence == exp_confidence
    assert tested.tags == exp_tags


# Test: duration
def test_duration():
    """Test duration calculation"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=1.0,
        end=3.5
    )

    result = tested.duration()

    expected = 2.5
    assert result == expected


@pytest.mark.parametrize(("start", "end", "expected"), [
    pytest.param(0.0, 2.5, 2.5, id="simple"),
    pytest.param(1.5, 6.0, 4.5, id="mid_range"),
    pytest.param(10.0, 10.1, 0.1, id="short"),
])
def test_duration__parametrized(start, end, expected):
    """Test duration with multiple scenarios"""
    tested = TranscriptSegment(
        speaker="Test",
        text="Test",
        chunk=1,
        start=start,
        end=end
    )

    result = tested.duration()

    assert result == expected


# Test: is_confident
def test_is_confident__above_default_threshold():
    """Test is_confident returns True when confidence is above default threshold"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0,
        confidence=0.9
    )

    result = tested.is_confident()

    expected = True
    assert result is expected


def test_is_confident__below_default_threshold():
    """Test is_confident returns False when confidence is below default threshold"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0,
        confidence=0.7
    )

    result = tested.is_confident()

    expected = False
    assert result is expected


def test_is_confident__custom_threshold():
    """Test is_confident with custom threshold"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0,
        confidence=0.85
    )

    result = tested.is_confident(threshold=0.9)

    expected = False
    assert result is expected


@pytest.mark.parametrize(("confidence", "threshold", "expected"), [
    pytest.param(0.9, 0.8, True, id="above_threshold"),
    pytest.param(0.8, 0.8, True, id="equal_threshold"),
    pytest.param(0.7, 0.8, False, id="below_threshold"),
    pytest.param(1.0, 0.9, True, id="perfect_confidence"),
])
def test_is_confident__parametrized(confidence, threshold, expected):
    """Test is_confident with multiple scenarios"""
    tested = TranscriptSegment(
        speaker="Test",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0,
        confidence=confidence
    )

    result = tested.is_confident(threshold=threshold)

    assert result is expected


# Test: add_tag
def test_add_tag__to_empty():
    """Test adding tag to empty tags list"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0
    )

    tested.add_tag("urgent")

    exp_tags = ["urgent"]
    assert tested.tags == exp_tags


def test_add_tag__to_existing():
    """Test adding tag to existing tags"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0,
        tags=["important"]
    )

    tested.add_tag("urgent")

    exp_tags = ["important", "urgent"]
    assert tested.tags == exp_tags


def test_add_tag__duplicate():
    """Test adding duplicate tag does not create duplicate"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=0.0,
        end=1.0,
        tags=["urgent"]
    )

    tested.add_tag("urgent")

    exp_tags = ["urgent"]
    assert tested.tags == exp_tags


# Test: format_time_range
def test_format_time_range():
    """Test formatting time range"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Test",
        chunk=1,
        start=1.5,
        end=3.75
    )

    result = tested.format_time_range()

    expected = "1.50s - 3.75s"
    assert result == expected


@pytest.mark.parametrize(("start", "end", "expected"), [
    pytest.param(0.0, 2.5, "0.00s - 2.50s", id="from_zero"),
    pytest.param(1.234, 5.678, "1.23s - 5.68s", id="rounded"),
    pytest.param(10.0, 15.0, "10.00s - 15.00s", id="whole_numbers"),
])
def test_format_time_range__parametrized(start, end, expected):
    """Test format_time_range with multiple scenarios"""
    tested = TranscriptSegment(
        speaker="Test",
        text="Test",
        chunk=1,
        start=start,
        end=end
    )

    result = tested.format_time_range()

    assert result == expected


# Test: word_count
def test_word_count__single_word():
    """Test word count for single word"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Hello",
        chunk=1,
        start=0.0,
        end=1.0
    )

    result = tested.word_count()

    expected = 1
    assert result == expected


def test_word_count__multiple_words():
    """Test word count for multiple words"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Hello world from Alice",
        chunk=1,
        start=0.0,
        end=2.0
    )

    result = tested.word_count()

    expected = 4
    assert result == expected


@pytest.mark.parametrize(("text", "expected"), [
    pytest.param("Hello", 1, id="single_word"),
    pytest.param("Hello world", 2, id="two_words"),
    pytest.param("One two three four five", 5, id="five_words"),
    pytest.param("", 1, id="empty_string"),  # split() returns ['']
])
def test_word_count__parametrized(text, expected):
    """Test word_count with multiple scenarios"""
    tested = TranscriptSegment(
        speaker="Test",
        text=text,
        chunk=1,
        start=0.0,
        end=1.0
    )

    result = tested.word_count()

    assert result == expected


# Test: is_long_segment
def test_is_long_segment__above_default():
    """Test is_long_segment returns True when word count is above default threshold"""
    tested = TranscriptSegment(
        speaker="Alice",
        text=" ".join(["word"] * 55),
        chunk=1,
        start=0.0,
        end=10.0
    )

    with patch.object(tested, 'word_count') as mock_word_count:
        mock_word_count.side_effect = [55]
        result = tested.is_long_segment()

    expected = True
    assert result is expected

    exp_calls = [call()]
    assert mock_word_count.mock_calls == exp_calls


def test_is_long_segment__below_default():
    """Test is_long_segment returns False when word count is below default threshold"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Short text",
        chunk=1,
        start=0.0,
        end=1.0
    )

    with patch.object(tested, 'word_count') as mock_word_count:
        mock_word_count.side_effect = [2]
        result = tested.is_long_segment()

    expected = False
    assert result is expected

    exp_calls = [call()]
    assert mock_word_count.mock_calls == exp_calls


def test_is_long_segment__custom_threshold():
    """Test is_long_segment with custom threshold"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Some text here",
        chunk=1,
        start=0.0,
        end=1.0
    )

    with patch.object(tested, 'word_count') as mock_word_count:
        mock_word_count.side_effect = [3]
        result = tested.is_long_segment(min_words=5)

    expected = False
    assert result is expected

    exp_calls = [call()]
    assert mock_word_count.mock_calls == exp_calls


# Test: Dataclass mutability
def test_mutability():
    """Test that dataclass fields can be modified"""
    tested = TranscriptSegment(
        speaker="Alice",
        text="Original",
        chunk=1,
        start=0.0,
        end=1.0
    )

    # Modify fields
    tested.text = "Modified"
    tested.confidence = 0.5

    exp_text = "Modified"
    exp_confidence = 0.5

    assert tested.text == exp_text
    assert tested.confidence == exp_confidence


# =============================================================================
# KEY TAKEAWAYS FOR DATACLASS TESTING
# =============================================================================
"""
1. FIRST TEST - DATACLASS STRUCTURE:
   - MANDATORY: First test must be test_class()
   - Assigns the CLASS itself to 'tested' variable (not an instance)
   - Defines 'fields' dictionary with field names and type STRINGS
   - Uses is_dataclass() helper function to verify structure
   - Example: tested = TranscriptSegment (the class, not TranscriptSegment(...))
   - IMPORTANT: Type values are STRINGS like "str", "int", "float", "list[str]"

2. is_dataclass() HELPER:
   - Define once in tests/conftest.py (automatically available to all tests)
   - No need to import - pytest makes conftest.py functions globally available
   - Verifies: @dataclass decorator, correct fields, field types
   - More comprehensive than checking __dataclass_fields__ manually

3. CREATING TEST INSTANCES:
   - Use keyword arguments for clarity: TranscriptSegment(speaker="Alice", text="Test", ...)
   - Don't use positional args: TranscriptSegment("Alice", "Test", ...)
   - Makes tests more readable and maintainable

4. TESTING DEFAULT VALUES:
   - Test initialization with only required fields (verify defaults are set)
   - Test initialization with optional fields (verify overrides work)
   - Example: test___init____required_only() vs test___init____with_optional_fields()

5. TESTING MUTABILITY:
   - Unlike NamedTuples, dataclasses are MUTABLE by default
   - Test that fields can be modified directly
   - Test methods that modify fields in-place (like add_tag)
   - Verify modifications persist

6. FIELD ACCESS:
   - Access fields directly: tested.speaker, tested.text
   - Dataclasses provide attribute access like regular classes
   - No special unpacking like NamedTuples

7. NAMING CONVENTIONS:
   - Test naming: test_method_name or test_method_name__case
   - Variables: tested, result, expected, exp_*
   - Same conventions as regular class testing

8. ASSERTIONS:
   - Use 'is' for boolean singletons: assert result is True
   - Use '==' for other comparisons: assert result == "value"
   - Multiple expected values: exp_speaker, exp_text, exp_confidence

9. PARAMETRIZATION:
   - Use @pytest.mark.parametrize for multiple scenarios
   - CRITICAL: First parameter must be TUPLE: ("start", "end", "expected")
   - Use pytest.param() with descriptive id parameter

10. TEST ORDERING:
    - First test: test_class() (dataclass structure verification)
    - Then: tests in same order as methods appear in source
    - __init__ tests, duration, is_confident, add_tag, format_time_range, word_count, is_long_segment

11. REAL INSTANCES vs MOCKS:
    - Dataclasses are data containers with methods - use real instances
    - Only mock external dependencies or internal methods when testing other methods
    - Example: test_is_long_segment mocks word_count() to avoid duplication
    - Easy to create, provides type safety

12. MOCKING INTERNAL METHODS:
    - When testing method A that calls method B on the same class, mock B
    - Use patch.object(tested, 'method_name') for instance method mocking
    - This avoids test duplication and tests only the target method's logic
    - Example: is_long_segment() mocks word_count()

13. DEFAULT_FACTORY FIELDS:
    - Fields like list/dict use field(default_factory=list)
    - Test that each instance gets its own mutable default
    - Don't test implementation details of dataclasses itself

14. TYPE STRINGS FORMAT:
    - Field types in is_dataclass() are STRINGS
    - Simple types: "str", "int", "float", "bool"
    - Generic types: "list[str]", "dict[str, int]", "Optional[str]"
    - Match exactly as they appear in the class definition

15. CONSISTENCY:
    - Follow same patterns as regular class testing
    - Mock verification rules apply if methods use external dependencies
    - Same variable naming, assertion style, parametrization approach
"""
