"""DL-07-T1: offline product-search investigation.
Run from Backend/ml-service: python dl07_t1_query_check.py
All products are synthetic. No MongoDB or external LLM calls are made.
"""

from unittest.mock import MagicMock

from chatbots.agents import DiscountMateAgent
from chatbots.mcp_tools import product_search
from chatbots.services.product_repository import MongoProductRepository


# Synthetic catalogue: brand and product name are stored separately.
products = [
    {
        "product_code": "TEST001",
        "product_id": "TEST001",
        "product_name": "Freddo",
        "brand": "Cadbury",
    },
    {
        "product_code": "TEST002",
        "product_id": "TEST002",
        "product_name": "Dairy Milk",
        "brand": "Cadbury",
    },
    {
        "product_code": "TEST003",
        "product_id": "TEST003",
        "product_name": "KitKat",
        "brand": "Nestle",
    },
]


def find_matches(name, brand=None):
    # Skip the real MongoDB connection and capture the repository's query.
    repo = object.__new__(MongoProductRepository)
    repo.products_col = MagicMock()
    repo.products_col.find.return_value.limit.return_value = []
    repo.search_products(name, brand=brand)
    query = repo.products_col.find.call_args.args[0]

    # Simulate ONLY the query conditions relevant to our synthetic catalogue.
    # This does not implement MongoDB, ranking, category or pack-size filtering.
    matches = []
    for product in products:
        name_match = any(
            regex.search(str(product.get(field, "")))
            for condition in query["$or"]
            for field, regex in condition.items()
        )
        brand_match = (
            bool(query["brand"].search(product["brand"])) if "brand" in query else True
        )
        if product.get("product_code") is not None and name_match and brand_match:
            matches.append(product.copy())
    return matches


def product_codes(matches):
    return sorted(product["product_code"] for product in matches)


def print_results(expected, matches):
    actual = product_codes(matches)
    passed = sorted(expected) == actual
    print("Expected product codes:", expected)
    print("Actual product codes:  ", actual)
    for product in matches:
        print(f"  - {product['brand']} {product['product_name']}")
    print("Proposed requirement:", "PASS" if passed else "FAIL")
    return passed


def run_repository_tests():
    # Expected results describe proposed user-facing behaviour, not the bug.
    cases = [
        ("TC01 - Product only", "Freddo", None, ["TEST001"]),
        ("TC02 - Combined phrase", "Cadbury Freddo", None, ["TEST001"]),
        ("TC03 - Separate brand", "Freddo", "Cadbury", ["TEST001"]),
        ("TC04 - Lowercase", "freddo", None, ["TEST001"]),
        ("TC05 - Wrong brand", "Freddo", "Nestle", []),
        ("TC06 - Unknown product", "XYZ123", None, []),
        ("TC07 - Ambiguous search", "Cadbury", None, ["TEST001", "TEST002"]),
        ("TC08 - Another combined phrase", "Cadbury Dairy Milk", None, ["TEST002"]),
    ]
    print("\n=== Repository query checks (simulated matching) ===")
    passed = 0
    for label, name, brand, expected in cases:
        print(f"\n{label}")
        print(f"Input: product_name={name!r}, brand={brand!r}")
        matches = find_matches(name, brand)
        passed += print_results(expected, matches)
    print(f"\nRepository requirements met: {passed}/{len(cases)}")


class FakeProductRepository:
    """Adapter that lets the real chatbot tool search our synthetic data."""

    def search_products(self, **kwargs):
        if kwargs.get("pack_size") or kwargs.get("category"):
            raise NotImplementedError("Pack size and category are outside this test.")
        return find_matches(kwargs["product_name"], kwargs.get("brand"))[
            : kwargs.get("limit", 10)
        ]


def run_chatbot_tests():
    repo = FakeProductRepository()
    # Use real agent and tool, but disable LLM planning for repeatable tests.
    agent = DiscountMateAgent(
        tool_registry={
            "search_products": lambda arguments: product_search.run(
                arguments, repository=repo
            )
        },
        enable_llm_planning=False,
    )
    cases = [
        ("Find Freddo", ["TEST001"]),
        ("Find Cadbury Freddo", ["TEST001"]),
        ("Show me Dairy Milk", ["TEST002"]),
        ("Find cadbury freddo", ["TEST001"]),
        ("Find Nestle KitKat", ["TEST003"]),
        ("Find XYZ123", []),
        ("Show me Cadbury", ["TEST001", "TEST002"]),
        ("Find Cadbury Dairy Milk", ["TEST002"]),
    ]
    print("\n=== MateBot workflow checks (LLM planning disabled) ===")
    passed = 0
    errors = 0
    for i, (message, expected) in enumerate(cases, start=1):
        print(f"\nCHAT{i:02}: {message}")
        response = agent.chat(
            {
                "session_id": f"dl07-t1-{i}",
                "message": message,
            }
        )
        print("Action:", response.action)
        for call in response.tool_calls:
            print("Arguments:", call.arguments)
        print("Answer:", response.answer)
        print("Needs clarification:", response.needs_clarification)
        if not response.success or response.action != "search_products":
            print("ERROR: Search workflow did not complete successfully.")
            print("Error:", response.error)
            errors += 1
            continue
        matches = (response.data or {}).get("products", [])
        passed += print_results(expected, matches)
    print(f"\nChatbot search requirements met: {passed}/{len(cases)}")
    print(f"Workflow errors: {errors}")
    print("Response wording and ambiguity handling still need team agreement.")


if __name__ == "__main__":
    run_repository_tests()
    run_chatbot_tests()
    print("\nInvestigation complete. Failures are recorded, not fixed.")
    print("Real MongoDB and LLM-enabled behaviour remain unverified.")
