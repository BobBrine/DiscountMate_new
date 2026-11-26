# DL-07-T1: MateBot Search Investigation

| Field | Details |
| --- | --- |
| Project | DiscountMate, DataBytes, DL/AI stream |
| Task owner | Rotanak (Bob) Heng |
| Date | 26 November 2026 |
| Sprint / branch | Sprint 1, Week 4 / `DL-07-T1` |
| Status | Initial technical investigation complete, team agreement and integration checks pending |

## 1. Objective

Reproduce the reported brand and product search issue identified in the T2 handover, record expected and actual results for eight natural-language queries, and provide a repeatable testing baseline for DL-07-T2.

The investigation includes both synthetic product data and real MongoDB product data to determine whether the reported issue occurs in the existing DiscountMate catalogue.

No production fix is included in this task.

## 2. Background

The T2 handover identified an issue with MateBot's ability to handle combined brand and product names.

A product-only search may return matching products, while the same search with the brand included may return no results.

The existing product repository supports a separate brand argument. However, MateBot may pass the entire search phrase into the product name argument without separating the brand.

This investigation aims to reproduce and document that behaviour before implementation changes are made in DL-07-T2.

## 3. Synthetic Data Testing

### 3.1 Test Setup

The diagnostic script `dl07_t1_query_check.py` uses the existing `MongoProductRepository.search_products()` method to build search queries.

A mocked collection captures those queries, and the script simulates the relevant name and brand matching conditions against three synthetic records.

The chatbot checks use the actual `DiscountMateAgent` and product search tool with a fake repository and LLM planning disabled.

| Product code | Product name | Brand |
| --- | --- | --- |
| TEST001 | Freddo | Cadbury |
| TEST002 | Dairy Milk | Cadbury |
| TEST003 | KitKat | Nestle |

### 3.2 Reproduction Instructions

From the repository root, activate the configured Python environment, navigate to `Backend/ml-service`, and execute:

```powershell
python chatbots/evaluation/sample_agent_test.py
python dl07_t1_query_check.py
```

The existing chatbot smoke test passed.

The detailed synthetic testing output is recorded in `DL-07-T1-results.txt`.

### 3.3 Repository Query Checks

Expected results represent proposed user-facing requirements for the synthetic catalogue and have not yet been approved as formal acceptance criteria.

| ID | Product name input | Brand filter | Expected codes | Actual codes | Result |
| --- | --- | --- | --- | --- | --- |
| TC01 | Freddo | None | TEST001 | TEST001 | PASS |
| TC02 | Cadbury Freddo | None | TEST001 | None | FAIL |
| TC03 | Freddo | Cadbury | TEST001 | TEST001 | PASS |
| TC04 | freddo | None | TEST001 | TEST001 | PASS |
| TC05 | Freddo | Nestle | None | None | PASS |
| TC06 | XYZ123 | None | None | None | PASS |
| TC07 | Cadbury | None | TEST001, TEST002 | TEST001, TEST002 | PASS |
| TC08 | Cadbury Dairy Milk | None | TEST002 | None | FAIL |

**Result: 6/8 proposed requirements met.**

Combined brand and product phrases failed when the brand and product name were stored separately in the synthetic catalogue.

Providing a separate brand filter succeeded in TC03.

### 3.4 MateBot Workflow Checks

All eight messages selected the `search_products` action. All supplied `brand=None`.

| ID | User message | Extracted product name | Expected codes | Actual codes | Result |
| --- | --- | --- | --- | --- | --- |
| CHAT01 | Find Freddo | Freddo | TEST001 | TEST001 | PASS |
| CHAT02 | Find Cadbury Freddo | Cadbury Freddo | TEST001 | None | FAIL |
| CHAT03 | Show me Dairy Milk | Dairy Milk | TEST002 | TEST002 | PASS |
| CHAT04 | Find cadbury freddo | cadbury freddo | TEST001 | None | FAIL |
| CHAT05 | Find Nestle KitKat | Nestle KitKat | TEST003 | None | FAIL |
| CHAT06 | Find XYZ123 | XYZ123 | None | None | PASS |
| CHAT07 | Show me Cadbury | Cadbury | TEST001, TEST002 | TEST001, TEST002 | PASS |
| CHAT08 | Find Cadbury Dairy Milk | Cadbury Dairy Milk | TEST002 | None | FAIL |

**Result: 4/8 proposed requirements met, with 0 workflow execution errors.**

All four failed cases involved combined brand and product searches.

Every failed case returned:

`I could not find matching products.`

The unknown-product case returned the same message correctly for the synthetic catalogue.

The multiple-match case returned:

`I found these matching products: Freddo, Dairy Milk`

The `needs_clarification` field was `False`.

### 3.5 Synthetic Testing Conclusion

The synthetic testing successfully reproduced the search issue described in the T2 handover.

The results suggested that MateBot's heuristic planning path was not consistently separating the brand and product name before executing a product search.

However, real database verification was required to determine whether the same behaviour occurred with actual catalogue records.

## 4. Real MongoDB Verification

### 4.1 Test Setup

Real MongoDB testing was conducted on 26 November 2026 following the initial synthetic data investigation.

The existing local environment configuration successfully established a connection to the DiscountMate MongoDB database.

The following methods were used:

- Existing MongoDB chatbot tool smoke test.
- Direct calls to `MongoProductRepository.search_products()`.
- Existing `DiscountMateAgent` with the real product repository.
- Eight natural-language queries matching the original synthetic chatbot test cases.
- LLM planning disabled for repeatable testing.
- A maximum of five returned products per query.

No production code changes or intentional database modifications were made during testing.

Database credentials and connection strings are excluded from this report.

### 4.2 Existing MongoDB Smoke Test

The previous trimester's existing evaluation script was used to verify MongoDB connectivity and product search functionality.

```powershell
python chatbots/evaluation/mongo_tool_test.py --product-name "Freddo" --limit 5
```

The database connection succeeded, and five matching products were returned.

| Product name | Brand |
| --- | --- |
| Freddo Biscuits | Cadbury |
| Dairy Milk Freddo Party Cake Frozen Dessert | Cadbury |
| Dairy Milk Freddo Cupcakes 6 Pack | Cadbury |
| Dairy Milk Freddo Chocolate | Cadbury |
| Dairy Milk Freddo & Caramello Koala Chocolate Sharepack 18 Pieces | Cadbury |

The existing price comparison smoke test also completed successfully.

The returned pricing records contained historical dates. Price freshness and price comparison accuracy were not assessed as part of DL-07-T1.

### 4.3 Direct Product Search Results

The following checks were performed against the real product catalogue.

| ID | Product name | Brand filter | Expected | Actual | Assessment |
| --- | --- | --- | --- | --- | --- |
| DB01 | Freddo | None | Matching products | 5 products | PASS |
| DB02 | Cadbury Freddo | None | Matching products | 0 products | FAIL |
| DB03 | Freddo | Cadbury | Matching products | 5 products | PASS |
| DB04 | KitKat | None | Matching products | 5 products | PASS |
| DB05 | KitKat | Nestle | Matching products | 2 products | PASS |
| DB06 | Dairy Milk | Cadbury | Matching products | 5 products | PASS |

The first three checks were conducted using the existing MongoDB smoke test:

```powershell
python chatbots/evaluation/mongo_tool_test.py --product-name "Freddo" --limit 5

python chatbots/evaluation/mongo_tool_test.py --product-name "Cadbury Freddo" --limit 5

python chatbots/evaluation/mongo_tool_test.py --product-name "Freddo" --brand "Cadbury" --limit 5
```

The remaining checks were performed by calling the existing product repository directly.

The combined Cadbury Freddo search returned no products despite matching products being available when the brand and product name were provided separately.

This confirms that the issue reproduced using synthetic data also occurs with the real product catalogue.

### 4.4 Real MateBot Workflow Results

The existing MateBot agent was tested using the real MongoDB product repository rather than the fake repository used in the initial investigation.

LLM planning remained disabled to maintain consistency between the synthetic and real database tests.

| ID | User message | Expected | Actual | Assessment |
| --- | --- | --- | --- | --- |
| LIVE01 | Find Freddo | Matching products | 5 products | PASS |
| LIVE02 | Find Cadbury Freddo | Matching products | 0 products | FAIL |
| LIVE03 | Show me Dairy Milk | Matching products | 5 products | PASS |
| LIVE04 | Find cadbury freddo | Matching products | 0 products | FAIL |
| LIVE05 | Find Nestle KitKat | Matching products | 0 products | FAIL |
| LIVE06 | Find XYZ123 | No matches | 0 products | PASS |
| LIVE07 | Show me Cadbury | Relevant matches | 5 products, including a different brand | NEEDS REVIEW |
| LIVE08 | Find Cadbury Dairy Milk | Relevant matches | 1 product, potentially incomplete | NEEDS REVIEW |

### 4.5 Real Chatbot Testing Summary

- Passed proposed requirements: 3/8.
- Failed proposed requirements: 3/8.
- Require further review: 2/8.
- Workflow execution errors: 0/8.

All eight requests executed successfully and selected the `search_products` action.

However, successful workflow execution does not necessarily mean that the correct products were returned.

All eight queries supplied `brand=None`, including queries containing both a brand and product name.

All eight responses returned `needs_clarification=False`.

The assessments remain subject to team agreement on the expected search behaviour.

### 4.6 Comparison Between Synthetic and Real Data

| Query | Synthetic results | Real results |
| --- | --- | --- |
| Find Freddo | 1 product | 5 products |
| Find Cadbury Freddo | 0 products | 0 products |
| Show me Dairy Milk | 1 product | 5 products |
| Find cadbury freddo | 0 products | 0 products |
| Find Nestle KitKat | 0 products | 0 products |
| Find XYZ123 | 0 products | 0 products |
| Show me Cadbury | 2 products | 5 products |
| Find Cadbury Dairy Milk | 0 products | 1 product |

The number of returned products differs because the synthetic catalogue contains only three records, while the real catalogue contains a wider range of products.

Real search results were limited to a maximum of five returned products. These counts do not represent the total number of matching records in the database.

The main brand and product extraction issue remained consistent across both testing environments.

## 5. Findings and Root Cause Investigation

### 5.1 Combined Brand and Product Names

The heuristic planning path passes the entire combined brand and product phrase into `product_name`, leaving `brand` unset.

For example, the user enters:

`Find Cadbury Freddo`

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

Observed response:

- Action: `search_products`
- Products returned: 0
- Answer: `I could not find matching products.`
- Needs clarification: `False`

The repository builds a case-insensitive regular-expression search across individual fields, including:

- `product_name`
- `name`
- `item_name`
- `brand`

A separate brand condition is applied when a brand argument is provided.

When the complete combined phrase does not occur within an individual searchable field, the repository may fail to find products even when the brand and product name exist separately.

### 5.2 Separate Brand and Product Arguments

One possible approach for DL-07-T2 to investigate is separating the brand and product name before executing the search.

Example:

```json
{
  "product_name": "Freddo",
  "brand": "Cadbury",
  "pack_size": null,
  "category": null,
  "retailer": null,
  "limit": 5
}
```

The synthetic repository test returned the expected product using this approach.

The real MongoDB repository test returned five matching products using the same separation.

This demonstrates that the existing repository already supports separate brand filtering.

However, the proposed chatbot extraction improvement has not yet been implemented or tested.

### 5.3 Nestle KitKat Verification

The natural-language search `Find Nestle KitKat` returned no matching products.

Additional repository checks confirmed that Nestle KitKat products exist in the catalogue.

Searching for `KitKat` with `brand="Nestle"` returned two products:

- Kitkat Mini Pouch Chocolate Easter Bunny Share Pack.
- Kitkat Ice Cream 4 Pack.

This provides further evidence that the combined search failure was not caused by an absence of matching products in the catalogue.

### 5.4 Brand-Only and Ambiguous Searches

The query `Show me Cadbury` returned five products.

One returned product was Cadbury Mocha Coffee Sachets, which had Moccona recorded as its brand.

This occurred because the search can match the requested term against multiple individual fields, including the product name.

Whether this result is acceptable depends on whether a brand-only query is intended to return products mentioning the brand or only products with that specific brand value.

The current chatbot displayed matching products without requesting clarification.

The expected behaviour requires team agreement.

### 5.5 Catalogue Naming Differences

The query `Find Cadbury Dairy Milk` returned one product named `COCONUT ROUGH BUNNY`, with `CADBURY DAIRY MILK` recorded as its brand.

A direct repository search using `product_name="Dairy Milk"` and `brand="Cadbury"` returned five matching products.

This indicates that combined searches do not necessarily return zero results in every situation. Differences in catalogue naming and brand values may influence the search results.

The returned product's relevance and the desired handling of catalogue naming variations require further review.

## 6. Observed Application Contract

The tested Python chatbot workflow accepts a request containing:

- `session_id`
- `message`

For product searches, the chatbot selects the `search_products` action.

The observed search arguments include:

| Argument | Purpose |
| --- | --- |
| `product_name` | Product or search phrase extracted from the user's message |
| `brand` | Optional brand filter |
| `pack_size` | Optional product size filter |
| `category` | Optional product category filter |
| `retailer` | Optional retailer filter |
| `limit` | Maximum number of returned products |

The observed chatbot response exposes:

| Field | Purpose |
| --- | --- |
| `success` | Indicates whether the workflow executed successfully |
| `action` | Identifies the selected chatbot action |
| `answer` | Contains the response message |
| `tool_calls` | Contains the executed tool calls and their arguments |
| `needs_clarification` | Indicates whether additional information is requested |
| `data` | Contains structured results, including matching products |

Relevant source files:

- `chatbots/agents/langgraph_workflow.py`: Message interpretation and tool planning.
- `chatbots/mcp_tools/product_search.py`: Product search tool.
- `chatbots/services/product_repository.py`: Repository query generation and database access.
- `chatbots/config.py`: Database environment configuration.
- `chatbots/evaluation/mongo_tool_test.py`: Existing real MongoDB evaluation script.

This documents the observed Python agent and tool contract.

The full frontend HTTP API contract and compatibility with App Development's requirements have not yet been verified.

## 7. Overall Investigation Summary

| Testing activity | Result |
| --- | --- |
| Existing chatbot smoke test | Passed |
| Synthetic repository checks | 6/8 proposed requirements met |
| Synthetic MateBot checks | 4/8 proposed requirements met |
| Real MongoDB connection | Successful |
| Direct real database search checks | 5/6 proposed requirements met |
| Real MateBot workflow checks | 3 passed, 3 failed, 2 require review |
| Workflow execution errors | 0 in both chatbot test sets |
| Original reported search issue | Reproduced using synthetic and real data |
| Production code changes | None |

The investigation confirms that the reported combined brand and product search issue occurs in the existing MateBot heuristic workflow when using both synthetic and real product data.

Providing separate brand and product arguments allows the existing repository to retrieve products that were not found using the combined search phrase.

The findings provide a baseline for DL-07-T2 to investigate and improve brand and product extraction.

## 8. Limitations and Open Decisions

- The synthetic tests simulate only the relevant repository query conditions and do not reproduce all MongoDB functionality.
- Real database results represent the catalogue at the time of testing.
- Real search results were limited to five returned products per query.
- LLM-enabled planning has not been tested.
- Full frontend-to-backend integration has not been verified as part of the real database investigation.
- Price comparison accuracy and price freshness are outside the main scope of this investigation.
- PASS and FAIL labels represent proposed requirements rather than formally approved acceptance criteria.
- Expected response wording and clarification behaviour require team agreement.
- Confirm whether brand-only searches should include products mentioning the brand or only products with a matching brand field.
- Confirm how MateBot should respond when multiple products match a search.
- Confirm the expected no-match response.
- Confirm the app-facing API contract with App Development.
- Confirm with the stream lead whether additional integration or LLM-enabled verification is required before closing DL-07-T1.

## 9. Handover to DL-07-T2

The findings provide a documented starting point for Louis to investigate brand and product extraction and response handling.

Recommended areas for DL-07-T2:

1. Investigate how MateBot identifies brand and product names before executing searches.
2. Evaluate passing the brand and product name as separate search arguments.
3. Preserve existing successful product-only searches.
4. Preserve appropriate no-match responses.
5. Review brand-only and ambiguous search behaviour.
6. Consider differences in product and brand naming within the real catalogue.
7. Rerun the original synthetic and real database test cases after implementation changes.
8. Confirm compatibility with App Development's requirements.
9. Provide the updated implementation and test results for DL-07-T3 review and regression testing.

No production fix has been implemented as part of DL-07-T1.

## 10. Evidence and Contribution

### Existing Evidence

- `dl07_t1_query_check.py`: Repeatable synthetic diagnostic testing script developed with AI assistance.
- `DL-07-T1-results.txt`: Locally executed synthetic testing output, including expected and actual product codes and chatbot responses.
- `chatbots/evaluation/mongo_tool_test.py`: Existing evaluation script from the previous trimester, reused for real MongoDB testing.
- This investigation report: Consolidated documentation of the synthetic and real database testing results.

### Personal Contribution

- Reviewed the T2 handover and identified the existing MateBot search issue.
- Reviewed the relevant product repository and chatbot workflow.
- Prepared and executed eight synthetic repository checks.
- Prepared and executed eight synthetic MateBot workflow checks.
- Verified real MongoDB connectivity.
- Executed six direct real product search checks.
- Executed eight real MateBot workflow checks.
- Compared synthetic and real database results.
- Identified additional observations involving brand-only searches and catalogue naming.
- Communicated initial findings to the DL/AI stream.
- Uploaded the initial testing script, results and documentation to the `DL-07-T1` GitHub branch.
- Attended the Week 4 stakeholder meeting.
- Prepared the consolidated investigation report for review and handover.

AI assistance was used to prepare the diagnostic testing code and organise the investigation documentation. Testing commands were executed locally by the task owner, and the findings were based on the observed terminal output.

No production-code change is claimed.

## 11. Conclusion

The initial technical investigation for DL-07-T1 has been completed.

The brand and product search issue identified in the T2 handover was successfully reproduced using both synthetic product data and the real DiscountMate MongoDB catalogue.

The results indicate that the existing MateBot heuristic workflow can fail to find available products when combined brand and product names are passed as a single product name argument.

The existing repository successfully retrieves matching products when the brand and product name are supplied separately.

The investigation provides evidence and test cases for DL-07-T2 implementation and DL-07-T3 regression testing.

Final task closure remains subject to team agreement on expected search behaviour, application integration requirements and any additional verification required by the stream lead.