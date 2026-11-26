# DL-07-T1 — MateBot search investigation

| Field | Details |
| --- | --- |
| Project | DiscountMate — DataBytes, DL/AI stream |
| Task owner | Rotanak (Bob) Heng |
| Date | 26 November 2026 |
| Sprint / branch | Sprint 1, Week 4 / `DL-07-T1` |
| Status | Initial investigation complete; team agreement and integration checks pending |

## 1. Objective

Reproduce the reported brand/product search issue, record expected and actual results for eight natural-language queries, and provide a repeatable baseline for DL-07-T2. No production fix is included in this task.

## 2. Test setup and reproduction

The diagnostic script `dl07_t1_query_check.py` uses the existing `MongoProductRepository.search_products()` method to build search queries. A mocked collection captures those queries, and the script simulates the relevant name and brand matching conditions against three synthetic records. The chatbot checks use the actual `DiscountMateAgent` and product-search tool with a fake repository and LLM planning disabled.

| Product code | Product name | Brand |
| --- | --- | --- |
| TEST001 | Freddo | Cadbury |
| TEST002 | Dairy Milk | Cadbury |
| TEST003 | KitKat | Nestle |

From the repository root, activate the configured Python environment, then run:

```powershell
cd Backend/ml-service
python chatbots/evaluation/sample_agent_test.py
python dl07_t1_query_check.py
```

The existing chatbot smoke test passed. The detailed diagnostic output is recorded in `DL-07-T1-results.txt`.

## 3. Repository query checks

Expected results are proposed user-facing requirements for this synthetic catalogue, not yet approved acceptance criteria. A dash means no matching product codes.

| ID | Product name input | Brand filter | Expected codes | Actual codes | Result |
| --- | --- | --- | --- | --- | --- |
| TC01 | Freddo | None | TEST001 | TEST001 | PASS |
| TC02 | Cadbury Freddo | None | TEST001 | — | FAIL |
| TC03 | Freddo | Cadbury | TEST001 | TEST001 | PASS |
| TC04 | freddo | None | TEST001 | TEST001 | PASS |
| TC05 | Freddo | Nestle | — | — | PASS |
| TC06 | XYZ123 | None | — | — | PASS |
| TC07 | Cadbury | None | TEST001, TEST002 | TEST001, TEST002 | PASS |
| TC08 | Cadbury Dairy Milk | None | TEST002 | — | FAIL |

**Result: 6/8 proposed requirements met.** Combined brand/product phrases fail when the brand and product name are stored separately in the fixture. Providing a separate brand filter succeeds in TC03.

## 4. MateBot workflow checks

All eight messages selected the `search_products` action. All supplied `brand=None`; the extracted product names are shown below.

| ID | User message | Extracted product name | Expected codes | Actual codes | Result |
| --- | --- | --- | --- | --- | --- |
| CHAT01 | Find Freddo | Freddo | TEST001 | TEST001 | PASS |
| CHAT02 | Find Cadbury Freddo | Cadbury Freddo | TEST001 | — | FAIL |
| CHAT03 | Show me Dairy Milk | Dairy Milk | TEST002 | TEST002 | PASS |
| CHAT04 | Find cadbury freddo | cadbury freddo | TEST001 | — | FAIL |
| CHAT05 | Find Nestle KitKat | Nestle KitKat | TEST003 | — | FAIL |
| CHAT06 | Find XYZ123 | XYZ123 | — | — | PASS |
| CHAT07 | Show me Cadbury | Cadbury | TEST001, TEST002 | TEST001, TEST002 | PASS |
| CHAT08 | Find Cadbury Dairy Milk | Cadbury Dairy Milk | TEST002 | — | FAIL |

**Result: 4/8 proposed requirements met; 0 workflow execution errors reported.** All four failed cases were combined brand/product searches. Every failed case returned `I could not find matching products.` The unknown-product case returned the same message correctly for this fixture. The multiple-match case returned `I found these matching products: Freddo, Dairy Milk` with `needs_clarification=False`.

## 5. Finding and observed input/output contract

The heuristic planning path passes the entire combined brand/product phrase into `product_name`, leaving `brand` unset. The repository builds a case-insensitive regular-expression search across individual fields (`product_name`, `name`, `item_name`, `brand`), with a separate brand condition when provided. A full phrase cannot match the synthetic record when its brand and name are stored separately.

Example: `Find Cadbury Freddo`.

Observed tool arguments:

```json
{
  "product_name": "Cadbury Freddo",
  "brand": null,
  "pack_size": null,
  "category": null,
  "retailer": null,
  "limit": 5
}
```

Observed response: `action=search_products`, no matching product codes, `answer="I could not find matching products."`, `needs_clarification=false`.

Proposed behaviour: find TEST001 for this fixture. One possible approach for T2 to evaluate is passing `product_name="Freddo"` and `brand="Cadbury"` separately. The repository-level TC03 supports that approach for the fixture; the full chatbot fix has not been implemented or tested.

Relevant source files:

- `chatbots/agents/langgraph_workflow.py` — message interpretation and tool planning.
- `chatbots/mcp_tools/product_search.py` — product-search tool.
- `chatbots/services/product_repository.py` — repository query generation.

This is the observed Python agent/tool contract, not a verified frontend HTTP API contract. The App Development team still needs to confirm its integration requirements.

## 6. Limitations and open decisions

- MongoDB catalogue access is outstanding. The tests use synthetic records and a partial simulation of query matching, not a real database. Actual catalogue fields, ranking, filters and production behaviour remain unverified.
- LLM-enabled planning, browser/frontend integration and price comparison are outside these executed tests.
- The PASS/FAIL labels compare observed product codes against proposed requirements, not approved acceptance criteria. Response wording and clarification are observed but not scored by the script.
- Confirm with App Development how combined searches, ambiguous matches and no-match responses should behave, and confirm the app-facing API contract.
- Arrange authorised catalogue access with Davina, or agree on approved test fixtures and record any remaining blockers.

## 7. Handover to DL-07-T2

Louis can rerun the diagnostic script as a baseline for extraction and response-handling changes. Prioritise the four failed chatbot cases; preserve the working product-only, unknown-product and multiple-match cases, subject to team agreement. After the fix, rerun both sets of tests and record the results for DL-07-T3 regression testing.

## 8. Evidence and contribution

- `dl07_t1_query_check.py`: repeatable diagnostic script (developed with AI assistance).
- `DL-07-T1-results.txt`: locally executed test output, including expected and actual product codes and chatbot responses.
- This report: summary of observed results and open decisions (drafted with AI assistance from the test output; review before sharing).
- Local execution and group progress update were completed on 26 November 2026. No production-code change is claimed.
