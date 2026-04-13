#!/bin/bash
#
# Market price simulator: applies random ±1% price fluctuations to assets
#
# Usage:
#   scripts/simulate_market.sh              # all seeded assets, all markets
#   scripts/simulate_market.sh BR           # all seeded assets in BR market
#   scripts/simulate_market.sh PETR4 VALE3  # specific symbols repeatedly

set -e

BACKEND_CMD="${DJANGO_SETTINGS_MODULE:+python manage.py}"

# Set Django settings if not already set
if [ -z "$DJANGO_SETTINGS_MODULE" ]; then
    export DJANGO_SETTINGS_MODULE=config.settings
fi

# Parse arguments to determine symbol source and options
MARKET_FILTER=""
EXPLICIT_SYMBOLS=""
ENABLE_TRENDS=false

# Check for --trends flag
if [[ "$*" == *"--trends"* ]]; then
    ENABLE_TRENDS=true
    # Remove --trends from arguments
    set -- "${@/--trends/}"
fi

if [ $# -eq 0 ]; then
    # No args: discover all seeded assets across all markets
    echo "Discovering all seeded assets..."
    EXPLICIT_SYMBOLS=""
elif [ $# -eq 1 ] && [[ "$1" =~ ^(BR|US|UK|EU)$ ]]; then
    # Single market code: discover seeded assets in that market
    MARKET_FILTER="$1"
    echo "Discovering seeded assets in market: $MARKET_FILTER"
    EXPLICIT_SYMBOLS=""
else
    # Multiple args or single non-market arg: treat as explicit symbols
    EXPLICIT_SYMBOLS="$@"
    echo "Using explicit symbols: $EXPLICIT_SYMBOLS"
fi

if [ "$ENABLE_TRENDS" = true ]; then
    echo "Trends enabled: each asset will have a persistent directional bias"
fi

# Helper: get latest price for a symbol from database
get_current_price() {
    local symbol=$1
    python manage.py shell <<EOF 2>&1 | grep -E "^[0-9]+\.[0-9]{2}$"
from markets.models import Asset, AssetQuote
from django.core.cache import cache
try:
    asset = Asset.objects.get(display_symbol='$symbol')
    # Try cache first
    cached = cache.get(f'price:{asset.id}')
    if cached:
        price_str = cached.get('price', '')
        # Format to 2 decimal places
        if price_str:
            print(f"{float(price_str):.2f}")
    else:
        # Fallback to latest quote
        quote = AssetQuote.objects.filter(asset=asset).latest('as_of')
        print(f"{float(quote.price):.2f}")
except Exception as e:
    # If no price found, return empty (will be skipped)
    pass
EOF
}

# Helper: build list of symbols to simulate
build_symbol_list() {
    if [ -n "$EXPLICIT_SYMBOLS" ]; then
        # User provided explicit symbols
        echo "$EXPLICIT_SYMBOLS"
    else
        # Query database for seeded assets
        python manage.py shell <<EOF 2>&1 | grep -E "^[A-Z0-9]{1,10}$"
from markets.models import Asset
query = Asset.objects.filter(is_seeded=True)
if '$MARKET_FILTER':
    query = query.filter(market='$MARKET_FILTER')
symbols = query.values_list('display_symbol', flat=True).order_by('display_symbol')
for symbol in symbols:
    print(symbol)
EOF
    fi
}

# Helper: apply realistic price fluctuation (normal distribution, mostly small changes)
apply_fluctuation() {
    local price=$1
    local trend=$2
    # Use awk for realistic fluctuation: normal distribution centered at 0, stddev ~0.003 (±0.3% typical)
    # This gives mostly small changes (cents) with occasional larger moves, matching real market behavior
    awk -v p="$price" -v t="$trend" 'BEGIN {
        srand()
        # Box-Muller transform for normal distribution
        u1 = rand()
        u2 = rand()
        z = sqrt(-2 * log(u1)) * cos(2 * 3.14159265 * u2)
        # Scale to realistic fluctuation: stddev 0.3%, plus optional trend
        multiplier = 1.0 + (z * 0.003) + t
        new_price = p * multiplier
        printf "%.2f\n", new_price
    }'
}

# Helper: sleep based on symbol count (realistic throttling)
calculate_sleep() {
    local symbol_count=$1
    # Bash version: max(1, 60 / symbol_count)
    # 1 symbol = 60 seconds, 60 symbols = 1 second per symbol
    if [ "$symbol_count" -le 1 ]; then
        echo "60"
    elif [ "$symbol_count" -le 60 ]; then
        # Simple integer division: 60 / symbol_count
        echo $((60 / symbol_count))
    else
        echo "1"
    fi
}

# Helper: generate or retrieve trend for a symbol
get_trend() {
    local symbol=$1
    if [ "$ENABLE_TRENDS" = false ]; then
        echo "0"
        return
    fi
    # Trends are generated once per symbol and cached in associative array
    # If not cached, generate a new one (-0.0015 to +0.0015 per update, ~±0.15% typical drift)
    if [ -z "${ASSET_TRENDS[$symbol]:-}" ]; then
        ASSET_TRENDS[$symbol]=$(awk 'BEGIN {
            srand('$(date +%s)' + 1234567 + index("'$symbol'", "A"))
            trend = (rand() - 0.5) * 0.003
            printf "%.6f\n", trend
        }')
    fi
    echo "${ASSET_TRENDS[$symbol]}"
}

# Declare associative array for per-asset trends
declare -A ASSET_TRENDS

# Main loop
iteration=0
while true; do
    iteration=$((iteration + 1))
    echo ""
    echo "=== Iteration $iteration at $(date '+%Y-%m-%d %H:%M:%S') ==="

    # Build fresh symbol list each iteration (in case assets are added/removed)
    symbols=$(build_symbol_list)
    symbol_array=($symbols)
    symbol_count=${#symbol_array[@]}

    if [ $symbol_count -eq 0 ]; then
        echo "No symbols to simulate. Retrying in 5 seconds..."
        sleep 5
        continue
    fi

    echo "Simulating $symbol_count symbol(s)"

    sleep_duration=$(calculate_sleep $symbol_count)

    # Process each symbol
    success_count=0
    for symbol in "${symbol_array[@]}"; do
        # Get current price
        current_price=$(get_current_price "$symbol")

        if [ -z "$current_price" ]; then
            echo "⚠ $symbol: no price available, skipping"
            continue
        fi

        # Get per-asset trend (0 if trends disabled)
        trend=$(get_trend "$symbol")

        # Apply fluctuation with trend
        new_price=$(apply_fluctuation "$current_price" "$trend")

        # Call simulate_price command
        if python manage.py simulate_price "$symbol" "$new_price" > /dev/null 2>&1; then
            echo "✓ $symbol: $current_price → $new_price"
            success_count=$((success_count + 1))
        else
            echo "✗ $symbol: failed to simulate"
        fi

        # Throttle between symbols for realistic market feel
        sleep "$sleep_duration"
    done

    echo "Completed: $success_count/$symbol_count symbols updated"
done
