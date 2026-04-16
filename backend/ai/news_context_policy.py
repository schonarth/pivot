BUCKET_ORDER = ("symbol", "company", "sector", "industry", "macro", "theme")

BUCKET_LIMITS = {
    "symbol": 2,
    "company": 2,
    "sector": 2,
    "industry": 2,
    "macro": 2,
    "theme": 2,
}

RAW_BUCKET_LIMITS = {
    "symbol": 8,
    "company": 8,
    "sector": 8,
    "industry": 8,
    "macro": 12,
    "theme": 12,
}

TOTAL_CONTEXT_LIMIT = 12

SOURCE_QUALITY = {
    "yahoo_finance": 3,
    "marketwatch": 2,
    "valor_economico": 2,
    "rss_feed": 1,
}

HEADLINE_STOPWORDS = {
    "a",
    "an",
    "and",
    "after",
    "as",
    "at",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "over",
    "the",
    "to",
    "with",
}

CORPORATE_SUFFIXES = {
    "ag",
    "co",
    "corp",
    "corporation",
    "inc",
    "ltd",
    "nv",
    "plc",
    "sa",
    "se",
    "spa",
    "s",
}

ASSET_METADATA_OVERRIDES = {}

THEME_RULES = (
    {
        "bucket": "macro",
        "name": "oil",
        "keywords": ("oil", "crude", "brent", "wti", "opec", "refinery"),
        "sector_names": ("Energy", "Basic Materials"),
        "industry_names": (),
    },
    {
        "bucket": "macro",
        "name": "rates",
        "keywords": ("rates", "yield", "fed", "inflation", "cpi", "interest rate"),
        "sector_names": ("Financial", "Real Estate", "Utilities"),
        "industry_names": (),
    },
    {
        "bucket": "macro",
        "name": "fx",
        "keywords": ("dollar", "fx", "currency", "forex", "exchange rate"),
        "sector_names": ("Financial", "Industrials", "Basic Materials", "Consumer Discretionary"),
        "industry_names": (),
    },
    {
        "bucket": "macro",
        "name": "growth",
        "keywords": ("gdp", "recession", "consumer spending", "labor market", "employment"),
        "sector_names": ("Consumer Discretionary", "Consumer Staples", "Financial"),
        "industry_names": (),
    },
    {
        "bucket": "theme",
        "name": "semiconductors",
        "keywords": ("chip", "chips", "semiconductor", "foundry", "gpu", "ai chip"),
        "sector_names": ("Technology", "Communication Services"),
        "industry_names": ("Semiconductors",),
    },
    {
        "bucket": "theme",
        "name": "banks",
        "keywords": ("loan", "credit", "deposit", "net interest margin", "bank"),
        "sector_names": ("Financial",),
        "industry_names": ("Banks",),
    },
    {
        "bucket": "theme",
        "name": "consumer",
        "keywords": ("retail", "spending", "sales", "demand", "shopping"),
        "sector_names": ("Consumer Discretionary", "Consumer Staples"),
        "industry_names": (),
    },
    {
        "bucket": "theme",
        "name": "industrial",
        "keywords": ("logistics", "manufacturing", "capex", "industrial", "orders"),
        "sector_names": ("Industrials",),
        "industry_names": (),
    },
)
