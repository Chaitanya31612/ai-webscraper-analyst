from dataclasses import dataclass, field


@dataclass
class AcceptRejectCriteria:
    """Define selection strategy for companies."""

    # ACCEPT if matches
    accept_industries: list[str] = field(default_factory=lambda: [
        "Technology", "Healthcare", "Financial Services", "Software"
    ])

    accept_product_keywords: list[str] = field(default_factory=lambda: [
        "SaaS", "platform", "cloud", "API", "analytics", "enterprise software"
    ])

    accept_company_sizes: list[str] = field(default_factory=lambda: [
        "SMB", "Enterprise", "Mid-market"
    ])

    # REJECT if matches (overrides accept)
    reject_product_keywords: list[str] = field(default_factory=lambda: [
        "gambling", "casino", "tobacco", "weapons", "adult content"
    ])

    reject_industries: list[str] = field(default_factory=lambda: [
        "Gambling", "Tobacco", "Adult Entertainment", "Weapons"
    ])

    # Requirements
    min_products_count: int = 1
    require_b2b: bool = False
    allowed_countries: list[str] = field(default_factory=list)  # Empty = all allowed