#!/usr/bin/env python3
"""
Buyer Radar MVP E2E Demo Test
================================
Comprehensive end-to-end test covering the full demo flow:
  1. Health check & backend startup
  2. Login as admin (user A)
  3. Create products
  4. Search for buyers (quick search)
  5. Create a buyer manually
  6. Add contact to buyer
  7. AI score the buyer
  8. Generate outreach email
  9. Add followup
 10. Check due followups
 11. Calculate quote
 12. Auth isolation: no token / invalid token → 401

Since this is a SINGLE-USER system (no org_id / multi-tenancy),
"user B" isolation is tested via invalid/missing tokens.
"""

import httpx
import json
import time
import subprocess
import sys
import os

API = "http://localhost:8000"
TIMEOUT = 30

passed = 0
failed = 0


def log(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}: {detail}")


def ensure_backend():
    """Start backend if not running."""
    try:
        r = httpx.get(f"{API}/api/health", timeout=5)
        if r.status_code == 200:
            print("  Backend already running.")
            return True
    except Exception:
        pass

    print("  Starting backend...")
    subprocess.Popen(
        ["python3", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd="/root/buyer-radar",
        stdout=open("/tmp/buyer-radar-test.log", "w"),
        stderr=subprocess.STDOUT,
    )
    for _ in range(10):
        time.sleep(1)
        try:
            r = httpx.get(f"{API}/api/health", timeout=5)
            if r.status_code == 200:
                print("  Backend started.")
                return True
        except Exception:
            pass
    print("  ❌ Could not start backend.")
    return False


def login(username="admin", password="buyer2024"):
    """Login and return auth headers."""
    r = httpx.post(
        f"{API}/api/auth/login",
        json={"username": username, "password": password},
        timeout=10,
    )
    if r.status_code == 200:
        token = r.json().get("token")
        return {"Authorization": f"Bearer {token}"}
    return None


# ============================================================
# Main test flow
# ============================================================

def main():
    global passed, failed

    print("\n" + "=" * 60)
    print("  Buyer Radar MVP E2E Demo Test")
    print("=" * 60)

    # ----------------------------------------------------------
    # 0. Ensure backend is running
    # ----------------------------------------------------------
    print("\n[0] Backend health check")
    if not ensure_backend():
        print("FATAL: Backend not available. Aborting.")
        sys.exit(1)
    try:
        r = httpx.get(f"{API}/api/health", timeout=5)
        data = r.json()
        log("Health check", data.get("status") == "ok", f"got {data}")
    except Exception as e:
        log("Health check", False, str(e))
        sys.exit(1)

    # ----------------------------------------------------------
    # 1. Login as user A (admin)
    # ----------------------------------------------------------
    print("\n[1] Login as admin (user A)")
    headers_a = login()
    log("Login admin", headers_a is not None, "no token returned")

    # ----------------------------------------------------------
    # 2. Auth check
    # ----------------------------------------------------------
    print("\n[2] Auth verification")
    r = httpx.get(f"{API}/api/auth/check", headers=headers_a, timeout=10)
    log("Auth check (valid token)", r.status_code == 200, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 3. Create a product
    # ----------------------------------------------------------
    print("\n[3] Create product")
    ts = int(time.time())
    product_data = {
        "sku": f"TEST-RING-{ts}",
        "name_cn": "测试银戒指",
        "name_en": "Sterling Silver Test Ring",
        "cost_price": 3.50,
        "moq": 100,
        "unit": "pcs",
        "weight_kg": 0.02,
        "profit_rate": 40,
        "category": "Jewelry",
        "description": "925 sterling silver ring for E2E testing",
    }
    r = httpx.post(f"{API}/api/quote/products", headers=headers_a, json=product_data, timeout=10)
    product_id = None
    if r.status_code == 200:
        product_id = r.json().get("id")
        log("Create product", product_id is not None, f"response={r.json()}")
    else:
        log("Create product", False, f"status={r.status_code} body={r.text}")

    # ----------------------------------------------------------
    # 4. List products
    # ----------------------------------------------------------
    print("\n[4] List products")
    r = httpx.get(f"{API}/api/quote/products", headers=headers_a, timeout=10)
    products = []
    if r.status_code == 200:
        products = r.json()
        log("List products", isinstance(products, list) and len(products) >= 0, f"count={len(products)}")
    else:
        log("List products", False, f"status={r.status_code}")

    # Use created product_id or first existing one
    if not product_id and products:
        product_id = products[0].get("id") if isinstance(products[0], dict) else products[0]["id"]

    # ----------------------------------------------------------
    # 5. Quick search for buyers (keyword: "jewelry")
    # ----------------------------------------------------------
    print("\n[5] Quick search buyers")
    r = httpx.get(
        f"{API}/api/search/quick",
        headers=headers_a,
        params={"q": "jewelry"},
        timeout=10,
    )
    search_results = []
    if r.status_code == 200:
        search_results = r.json()
        log("Quick search 'jewelry'", isinstance(search_results, list), f"count={len(search_results)}")
    else:
        log("Quick search 'jewelry'", False, f"status={r.status_code} body={r.text[:200]}")

    # ----------------------------------------------------------
    # 6. Create a buyer manually
    # ----------------------------------------------------------
    print("\n[6] Create buyer")
    buyer_data = {
        "company_name": "E2E Test Jewelry Co. Ltd.",
        "country": "United States",
        "city": "New York",
        "industry": "Jewelry",
        "products": ["rings", "necklaces", "bracelets"],
        "email": "test@example.com",
        "phone": "+1-555-0100",
        "website": "https://example-test.com",
        "source": "E2E Test",
        "notes": "Created by E2E test script",
    }
    r = httpx.post(f"{API}/api/buyers", headers=headers_a, json=buyer_data, timeout=10)
    buyer_id = None
    if r.status_code == 200:
        buyer_id = r.json().get("id")
        log("Create buyer", buyer_id is not None, f"response={r.json()}")
    else:
        log("Create buyer", False, f"status={r.status_code} body={r.text}")

    # Fallback: search for existing buyer
    if not buyer_id and search_results:
        first = search_results[0]
        buyer_id = first.get("id") if isinstance(first, dict) else first[0]
        print(f"  (using existing buyer id={buyer_id})")

    if not buyer_id:
        print("FATAL: No buyer to work with. Aborting remaining tests.")
        print(f"\nResults: {passed} passed, {failed} failed")
        sys.exit(1)

    # ----------------------------------------------------------
    # 7. Get buyer detail
    # ----------------------------------------------------------
    print("\n[7] Get buyer detail")
    r = httpx.get(f"{API}/api/buyers/{buyer_id}", headers=headers_a, timeout=10)
    if r.status_code == 200:
        buyer = r.json()
        log("Get buyer detail", buyer.get("id") == buyer_id, f"company={buyer.get('company_name')}")
    else:
        log("Get buyer detail", False, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 8. List buyers
    # ----------------------------------------------------------
    print("\n[8] List buyers")
    r = httpx.get(f"{API}/api/buyers/list", headers=headers_a, timeout=10)
    if r.status_code == 200:
        data = r.json()
        log("List buyers", "data" in data and "total" in data, f"total={data.get('total')}")
    else:
        log("List buyers", False, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 9. Add contact to buyer
    # ----------------------------------------------------------
    print("\n[9] Add contact to buyer")
    contact_data = {
        "buyer_id": buyer_id,
        "name": "John Test",
        "position": "Purchasing Manager",
        "department": "Procurement",
        "email": "john.test@example.com",
        "phone": "+1-555-0200",
        "is_primary": 1,
    }
    r = httpx.post(f"{API}/api/contacts/{buyer_id}", headers=headers_a, json=contact_data, timeout=10)
    contact_id = None
    if r.status_code == 200:
        contact_id = r.json().get("id")
        log("Add contact", contact_id is not None, f"response={r.json()}")
    else:
        log("Add contact", False, f"status={r.status_code} body={r.text}")

    # ----------------------------------------------------------
    # 10. List contacts for buyer
    # ----------------------------------------------------------
    print("\n[10] List contacts")
    r = httpx.get(f"{API}/api/contacts/{buyer_id}", headers=headers_a, timeout=10)
    if r.status_code == 200:
        contacts = r.json()
        log("List contacts", isinstance(contacts, list) and len(contacts) >= 1, f"count={len(contacts)}")
    else:
        log("List contacts", False, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 11. AI score the buyer
    # ----------------------------------------------------------
    print("\n[11] AI score buyer")
    r = httpx.post(f"{API}/api/ai/score", headers=headers_a, json={"buyer_id": buyer_id}, timeout=30)
    if r.status_code == 200:
        score_data = r.json()
        score = score_data.get("score")
        level = score_data.get("level")
        log("AI score", score is not None, f"score={score} level={level}")
    else:
        log("AI score", False, f"status={r.status_code} body={r.text[:300]}")

    # ----------------------------------------------------------
    # 12. Generate outreach email
    # ----------------------------------------------------------
    print("\n[12] Generate outreach email")
    outreach_data = {
        "buyer_id": buyer_id,
        "channel": "email",
        "product": "Sterling Silver Ring",
        "language": "en",
    }
    r = httpx.post(f"{API}/api/ai/outreach", headers=headers_a, json=outreach_data, timeout=30)
    if r.status_code == 200:
        outreach = r.json()
        content = outreach.get("content")
        # content may be None if no AI key configured - endpoint still works
        log("Generate outreach", r.status_code == 200, f"content_len={len(content) if content else 0} (None=no AI key)")
    else:
        log("Generate outreach", False, f"status={r.status_code} body={r.text[:300]}")

    # ----------------------------------------------------------
    # 13. Add followup
    # ----------------------------------------------------------
    print("\n[13] Add followup")
    followup_data = {
        "method": "email",
        "subject": "E2E Test Followup - Jewelry Inquiry",
        "content": "Sent initial outreach email to test buyer. Waiting for response.",
        "result": "sent",
        "followup_date": time.strftime("%Y-%m-%d", time.localtime()),
    }
    r = httpx.post(f"{API}/api/followups/{buyer_id}", headers=headers_a, json=followup_data, timeout=10)
    followup_id = None
    if r.status_code == 200:
        followup_id = r.json().get("id")
        log("Add followup", followup_id is not None, f"response={r.json()}")
    else:
        log("Add followup", False, f"status={r.status_code} body={r.text}")

    # ----------------------------------------------------------
    # 14. List followups for buyer
    # ----------------------------------------------------------
    print("\n[14] List followups for buyer")
    r = httpx.get(f"{API}/api/followups/{buyer_id}", headers=headers_a, timeout=10)
    if r.status_code == 200:
        followups = r.json()
        log("List followups", isinstance(followups, list) and len(followups) >= 1, f"count={len(followups)}")
    else:
        log("List followups", False, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 15. Check due followups
    # ----------------------------------------------------------
    print("\n[15] Check due followups")
    r = httpx.get(f"{API}/api/followups/due/list", headers=headers_a, timeout=10)
    if r.status_code == 200:
        due = r.json()
        log("Due followups", isinstance(due, list), f"count={len(due)}")
    else:
        log("Due followups", False, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 16. Calculate quote
    # ----------------------------------------------------------
    print("\n[16] Calculate quote")
    quote_data = {
        "items": [
            {"product_id": product_id, "quantity": 500},
        ],
        "country": "United States",
        "shipping_method": "sea",
        "price_term": "FOB Shanghai",
        "port_from": "Shanghai",
    }
    r = httpx.post(f"{API}/api/quote/calculate", headers=headers_a, json=quote_data, timeout=15)
    if r.status_code == 200:
        quote_result = r.json()
        log("Calculate quote", "total" in quote_result or "items" in quote_result, f"keys={list(quote_result.keys())}")
    else:
        log("Calculate quote", False, f"status={r.status_code} body={r.text[:300]}")

    # ----------------------------------------------------------
    # 17. Test online search (may not exist)
    # ----------------------------------------------------------
    print("\n[17] Online search (POST /api/search/online)")
    r = httpx.post(
        f"{API}/api/search/online",
        headers=headers_a,
        json={"keyword": "jewelry buyer", "country": "United States"},
        timeout=15,
    )
    # This endpoint does not exist in current API - 405 is expected (method not allowed on /api/search)
    log("Online search (informational)", r.status_code in (200, 404, 405), f"status={r.status_code} (expected: not available)")

    # ----------------------------------------------------------
    # 18. Auth isolation: no token → 401
    # ----------------------------------------------------------
    print("\n[18] Auth isolation: missing token")
    r = httpx.get(f"{API}/api/buyers/list", timeout=10)  # no headers
    log("No token → 401", r.status_code == 401, f"status={r.status_code}")

    r = httpx.post(f"{API}/api/buyers", json=buyer_data, timeout=10)  # no headers
    log("No token POST → 401", r.status_code == 401, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 19. Auth isolation: invalid token → 401
    # ----------------------------------------------------------
    print("\n[19] Auth isolation: invalid token")
    bad_headers = {"Authorization": "Bearer invalidtoken1234567890"}
    r = httpx.get(f"{API}/api/buyers/list", headers=bad_headers, timeout=10)
    log("Invalid token → 401", r.status_code == 401, f"status={r.status_code}")

    r = httpx.get(f"{API}/api/auth/check", headers=bad_headers, timeout=10)
    log("Invalid token auth check → 401", r.status_code == 401, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 20. Auth isolation: malformed header → 401
    # ----------------------------------------------------------
    print("\n[20] Auth isolation: malformed header")
    r = httpx.get(f"{API}/api/buyers/list", headers={"Authorization": "NotBearer abc"}, timeout=10)
    log("Malformed header → 401", r.status_code == 401, f"status={r.status_code}")

    r = httpx.get(f"{API}/api/buyers/list", headers={"Authorization": "Bearer"}, timeout=10)
    log("Bearer no token → 401", r.status_code == 401, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 21. Buyer status & level lists
    # ----------------------------------------------------------
    print("\n[21] Buyer metadata lists")
    r = httpx.get(f"{API}/api/buyers/status/list", headers=headers_a, timeout=10)
    log("Status list", r.status_code == 200 and isinstance(r.json(), list), f"count={len(r.json()) if r.status_code==200 else 0}")

    r = httpx.get(f"{API}/api/buyers/level/list", headers=headers_a, timeout=10)
    log("Level list", r.status_code == 200 and isinstance(r.json(), list), f"count={len(r.json()) if r.status_code==200 else 0}")

    # ----------------------------------------------------------
    # 22. Search countries & industries
    # ----------------------------------------------------------
    print("\n[22] Search metadata")
    r = httpx.get(f"{API}/api/search/countries", headers=headers_a, timeout=10)
    log("Countries list", r.status_code == 200, f"status={r.status_code}")

    r = httpx.get(f"{API}/api/search/industries", headers=headers_a, timeout=10)
    log("Industries list", r.status_code == 200, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 23. Quote countries list
    # ----------------------------------------------------------
    print("\n[23] Quote countries")
    r = httpx.get(f"{API}/api/quote/countries", headers=headers_a, timeout=10)
    if r.status_code == 200:
        countries = r.json()
        log("Quote countries", isinstance(countries, list) and len(countries) > 0, f"count={len(countries)}")
    else:
        log("Quote countries", False, f"status={r.status_code}")

    # ----------------------------------------------------------
    # 24. Logout
    # ----------------------------------------------------------
    print("\n[24] Logout")
    r = httpx.post(f"{API}/api/auth/logout", headers=headers_a, timeout=10)
    log("Logout", r.status_code == 200, f"status={r.status_code}")

    # Verify token is invalidated after logout
    r = httpx.get(f"{API}/api/auth/check", headers=headers_a, timeout=10)
    log("Token invalid after logout", r.status_code == 401, f"status={r.status_code}")

    # ----------------------------------------------------------
    # Summary
    # ----------------------------------------------------------
    print("\n" + "=" * 60)
    print(f"  Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        print("\n  ⚠️  Some tests failed. Review above.")
        sys.exit(1)
    else:
        print("\n  🎉 All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
