"""Content cleaning utilities for scraped markdown."""

import re
from typing import Optional


def clean_markdown(content: str, max_chars: Optional[int] = None) -> str:
    """
    Remove noise from scraped markdown to reduce tokens and improve AI accuracy.

    Args:
        content: Raw markdown from scraper
        max_chars: Optional character limit after cleaning

    Returns:
        Cleaned markdown content
    """

    # ==========================================
    # PHASE 1: Remove structural noise
    # ==========================================

    # Remove image markdown
    # Example: "![Alt text](https://example.com/image.png)" → ""
    # Example: "![Logo](/images/logo.svg)" → ""
    content = re.sub(r'!\[.*?\]\(.*?\)', '', content)

    # Remove HTML comments
    # Example: "<!-- This is a comment -->" → ""
    # Example: "<!--[if IE]>...<![endif]-->" → ""
    content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)

    # Remove inline HTML tags (keep text content)
    # Example: "<div class='container'>Hello</div>" → "Hello"
    # Example: "<span style='color:red'>Warning</span>" → "Warning"
    # Example: "<br/>" → ""
    content = re.sub(r'<[^>]+>', '', content)

    # Convert links to just text [link text](url) → link text
    # Example: "[Click here](https://example.com)" → "Click here"
    # Example: "[Learn more](/about)" → "Learn more"
    content = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', content)

    # Remove standalone URLs
    # Example: "Visit https://example.com/page for more" → "Visit  for more"
    # Example: "http://api.example.com/v1" → ""
    content = re.sub(r'https?://\S+', '', content)

    # ==========================================
    # PHASE 2: Remove navigation/boilerplate
    # ==========================================

    # Common navigation patterns
    nav_patterns = [
        # Example: "Skip to main content" → ""
        r'Skip to (?:main )?content',

        # Example: "Back to top" → ""
        r'Back to top',

        # Example: "Primary Menu", "Footer Navigation" → ""
        r'(?:Primary|Main|Footer) (?:Menu|Navigation)',

        # Example: "Toggle navigation" → ""
        r'Toggle navigation',

        # Example: "Search", "Search for", "Search this site..." → ""
        r'Search\s*(?:for|this site)?\.{0,3}',

        # Example: "Menu", "Menu Close" → ""
        r'Menu\s*(?:Close)?',
    ]

    # Cookie/consent banners
    cookie_patterns = [
        # Example: "We use cookies to improve your experience. Accept Decline" → ""
        # Example: "This website uses cookies for analytics. Learn more" → ""
        r'(?:We use |This (?:site|website) uses )cookies.*?(?:Accept|Decline|Settings|Learn more)\.?',

        # Example: "Cookie Policy\nWe value your privacy..." → ""
        r'Cookie (?:Policy|Settings|Preferences).*?(?=\n\n|\Z)',

        # Example: "By continuing to use our site, you consent to cookies." → ""
        # Example: "By using this website you agree to our terms." → ""
        r'By (?:continuing|using) (?:this|our) (?:site|website).*?(?:consent|agree).*?\.?',
    ]

    # Legal/footer boilerplate
    legal_patterns = [
        # Example: "Privacy Policy - Updated 2024" → ""
        r'Privacy Policy.*?(?=\n\n|\Z)',

        # Example: "Terms of Service", "Terms and Conditions", "Terms of Use" → ""
        r'Terms (?:of Service|and Conditions|of Use).*?(?=\n\n|\Z)',

        # Example: "All rights reserved." → ""
        r'All rights reserved\.?',

        # Example: "© 2024 Company Inc." → ""
        # Example: "©2023 All rights reserved" → ""
        r'©\s*\d{4}.*?(?=\n|\Z)',

        # Example: "Copyright © 2024 Example Corp. All rights reserved." → ""
        # Example: "Copyright 2023 by Company" → ""
        r'Copyright\s+©?\s*\d{4}.*?(?=\n|\Z)',
    ]

    # Marketing/newsletter signup
    marketing_patterns = [
        # Example: "Subscribe to our newsletter for updates!" → ""
        r'Subscribe to (?:our )?(?:newsletter|updates).*?(?=\n\n|\Z)',

        # Example: "Sign up for our newsletter" → ""
        r'Sign up for (?:our )?(?:newsletter|updates).*?(?=\n\n|\Z)',

        # Example: "Get the latest news delivered to your inbox" → ""
        r'Get (?:the )?latest (?:news|updates).*?(?=\n\n|\Z)',

        # Example: "Follow us on Twitter, Facebook, and LinkedIn" → ""
        r'Follow us on.*?(?=\n\n|\Z)',

        # Example: "Share this on Facebook", "Share on Twitter" → ""
        r'Share (?:this|on).*?(?=\n\n|\Z)',
    ]

    # Social media links as text
    social_patterns = [
        # Example: "Facebook | Twitter | LinkedIn" → "  "
        # Example: "Facebook • Instagram • YouTube" → "  "
        r'(?:Facebook|Twitter|LinkedIn|Instagram|YouTube|TikTok)\s*(?:\||\•|\-)?',
    ]

    # Apply all pattern removals
    all_patterns = nav_patterns + cookie_patterns + legal_patterns + marketing_patterns + social_patterns
    for pattern in all_patterns:
        content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.DOTALL)

    # ==========================================
    # PHASE 3: Clean up whitespace
    # ==========================================

    # Remove lines that are just punctuation or single characters
    # Example: "|" → ""
    # Example: "•" → ""
    # Example: "→" → ""
    # Example: "---" (if short) → ""
    content = re.sub(r'^[\|\•\-\*\→\←\↑\↓\s]{1,5}$', '', content, flags=re.MULTILINE)

    # Remove repeated separators
    # Example: "-------------------" → ""
    # Example: "===================" → ""
    # Example: "___________________" → ""
    content = re.sub(r'[\-\—\=\_]{3,}', '', content)

    # Example: "********" → ""
    content = re.sub(r'\*{3,}', '', content)

    # Normalize whitespace - max 2 newlines (one blank line)
    # Example: "Hello\n\n\n\n\nWorld" → "Hello\n\nWorld"
    content = re.sub(r'\n{3,}', '\n\n', content)

    # Max 1 space between words
    # Example: "Hello     World" → "Hello World"
    content = re.sub(r' {2,}', ' ', content)

    # Convert tabs to single space
    # Example: "Column1\t\t\tColumn2" → "Column1 Column2"
    content = re.sub(r'\t+', ' ', content)

    # Remove empty lines with just spaces
    # Example: "   \n" → "\n"
    content = re.sub(r'^\s+$', '', content, flags=re.MULTILINE)

    # ==========================================
    # PHASE 4: Remove repetitive content
    # ==========================================

    # Remove duplicate lines (common in scraped nav where same link appears multiple times)
    # Example:
    #   "Home\nAbout\nContact\nHome\nAbout"
    #   → "Home\nAbout\nContact"
    lines = content.split('\n')
    seen = set()
    unique_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and stripped not in seen:
            seen.add(stripped)
            unique_lines.append(line)
        elif not stripped:  # Keep empty lines for paragraph breaks
            unique_lines.append(line)
    content = '\n'.join(unique_lines)

    # Final trim - remove leading/trailing whitespace
    content = content.strip()

    # Optional: Apply character limit
    if max_chars and len(content) > max_chars:
        content = content[:max_chars] + "\n\n[...content truncated...]"

    return content


def extract_key_sections(content: str) -> dict[str, str]:
    """
    Extract key business sections from cleaned content.
    Useful for structured analysis.

    Returns dict with keys: 'about', 'products', 'mission', 'team', 'contact'
    """
    sections = {}

    # Patterns to identify sections (case insensitive)
    section_patterns = {
        # Matches: "About Us", "About Company", "Who We Are", "Our Story"
        # Example: "## About Us\nWe are a leading..." → captures the section
        'about': r'(?:About\s+(?:Us|Company)|Who\s+We\s+Are|Our\s+Story).*?(?=\n#|\Z)',

        # Matches: "Products", "Services", "Solutions", "What We Do", "What We Offer"
        # Example: "# Our Products\n1. Product A..." → captures the section
        'products': r'(?:Products?|Services?|Solutions?|What\s+We\s+(?:Do|Offer)).*?(?=\n#|\Z)',

        # Matches: "Our Mission", "Mission"
        # Example: "## Our Mission\nTo transform..." → captures the section
        'mission': r'(?:Our\s+)?Mission.*?(?=\n#|\Z)',

        # Matches: "Our Team", "Leadership", "Management Team"
        # Example: "# Leadership\nJohn Doe, CEO..." → captures the section
        'team': r'(?:Our\s+)?(?:Team|Leadership|Management).*?(?=\n#|\Z)',

        # Matches: "Contact Us", "Contact", "Get in Touch"
        # Example: "## Contact Us\nEmail: info@..." → captures the section
        'contact': r'(?:Contact\s+(?:Us)?|Get\s+in\s+Touch).*?(?=\n#|\Z)',
    }

    for name, pattern in section_patterns.items():
        match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            sections[name] = match.group(0).strip()[:2000]  # Limit each section to 2000 chars

    return sections


def estimate_tokens(text: str) -> int:
    """
    Rough token estimate for English text.

    Rule of thumb: ~4 characters = 1 token (for English)
    This is approximate - actual tokenization varies by model.

    Example: "Hello world" (11 chars) → ~3 tokens
    Example: "Machine learning is great" (25 chars) → ~6 tokens
    """
    return len(text) // 4
