"""DL-07-T1: repeat the real-catalogue search checks.
Run from Backend/ml-service with authorised read-only MongoDB access:
    python dl07_t1_live_check.py --live
LLM planning is disabled. No intentional database writes.
Results depend on the current catalogue and are limited to five per query.
"""

import argparse
from uuid import uuid4

from chatbots.agents import DiscountMateAgent
from chatbots.mcp_tools import product_search
from chatbots.services.product_repository import MongoProductRepository

DIRECT_CASES = [
    ("Freddo", None),
    ("Cadbury Freddo", None),
    ("Freddo", "Cadbury"),
    ("KitKat", None),
    ("KitKat", "Nestle"),
    ("Dairy Milk", "Cadbury"),
]

CHAT_CASES = [
    ("Find Freddo", "Matching products"),
    ("Find Cadbury Freddo", "Matching products"),
    ("Show me Dairy Milk", "Matching products"),
    ("Find cadbury freddo", "Matching products"),
    ("Find Nestle KitKat", "Matching products"),
    ("Find XYZ123", "No matches"),
    ("Show me Cadbury", "Relevant matches; review ambiguity"),
    ("Find Cadbury Dairy Milk", "Relevant matches; review relevance"),
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="Explicitly opt in to real database reads"
    )
    args = parser.parse_args()
    if not args.live:
        parser.error("Use --live only with approved read-only database access.")

    try:
        repo = MongoProductRepository()
        print("MongoDB connection OK.")
        print("=== Direct product search checks ===")
        for i, (name, brand) in enumerate(DIRECT_CASES, 1):
            matches = repo.search_products(product_name=name, brand=brand, limit=5)
            print(
                f"DB{i:02}: product_name={name!r}, brand={brand!r}, returned={len(matches)}"
            )

        agent = DiscountMateAgent(
            tool_registry={
                "search_products": lambda arguments: product_search.run(
                    arguments, repository=repo
                )
            },
            enable_llm_planning=False,
        )
        run_id = uuid4().hex
        errors = 0
        print("\n=== MateBot checks (LLM planning disabled) ===")
        for i, (message, expected) in enumerate(CHAT_CASES, 1):
            response = agent.chat(
                {"session_id": f"dl07-live-{run_id}-{i}", "message": message}
            )
            products = (response.data or {}).get("products", [])
            print(f"\nLIVE{i:02}: {message}")
            print("Expected (proposed):", expected)
            print("Success:", response.success)
            print("Action:", response.action)
            for call in response.tool_calls:
                print("Arguments:", call.arguments)
            print("Needs clarification:", response.needs_clarification)
            print("Products returned:", len(products))
            if not response.success or response.action != "search_products":
                errors += 1
        print(f"\nWorkflow errors: {errors}/{len(CHAT_CASES)}")
        print(
            "Review relevance and expected behaviour manually; counts alone are not acceptance criteria."
        )
        return int(errors > 0)
    except Exception as exc:
        # Avoid echoing connection strings or full connection errors.
        print("Test stopped:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
