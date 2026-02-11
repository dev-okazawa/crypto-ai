from ai.src.market_cap import get_top_symbols

LIMITS = [20, 50, 100]

def main():
    coins = get_top_symbols(mode="all")

    target = []
    for c in coins:
        if c["status"] == "unsupported":
            target.append(c["symbol"])

    # 今回は Top20 まで
    scheduled = target[:20]

    with open("ai/data/scheduled_symbols.txt", "w") as f:
        for s in scheduled:
            f.write(s + "\n")

    print(f"Scheduled {len(scheduled)} symbols")

if __name__ == "__main__":
    main()
