from playwright.sync_api import sync_playwright

URL = "https://ar.indeed.com/jobs?q=Head+of+Product&l=Argentina"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(user_agent=USER_AGENT)
    page = context.new_page()
    page.goto(URL, timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    print("Título de la página:", page.title())

    with open("indeed_debug.html", "w", encoding="utf-8") as f:
        f.write(page.content())
    print("HTML completo guardado en indeed_debug.html")

    challenge = page.query_selector("#challenge-form")
    print("¿Tiene challenge-form (verificación)?", challenge is not None)

    cards = page.query_selector_all("div.job_seen_beacon")
    print(f"Cards con 'div.job_seen_beacon': {len(cards)}")
    if not cards:
        cards = page.query_selector_all("td.resultContent")
        print(f"Cards con 'td.resultContent': {len(cards)}")

    if cards:
        first = cards[0]
        print("--- HTML de la primera card (primeros 800 caracteres) ---")
        print(first.evaluate("el => el.outerHTML")[:800])
    else:
        print("No se encontró ninguna card con ninguno de los dos selectores.")

    browser.close()
