"""Browser session management for Thordata Scraping Browser.

This module provides a high-level wrapper around Playwright connected to
Thordata's Scraping Browser.
"""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

try:
    from playwright.async_api import Browser, Page, Playwright, async_playwright
except ImportError as e:
    raise ImportError(
        "Playwright is required for browser automation. "
        "Install it with: pip install thordata[browser]"
    ) from e

from ..async_client import AsyncThordataClient
from .exceptions import BrowserConnectionError, BrowserSessionError

logger = logging.getLogger(__name__)


class BrowserSession:
    """Domain-aware browser session wrapper for Thordata Scraping Browser."""

    def __init__(
        self,
        client: AsyncThordataClient,
        username: str | None = None,
        password: str | None = None,
    ) -> None:
        """Initialize browser session.

        Args:
            client: AsyncThordataClient instance
            username: Browser username (optional, can use env var)
            password: Browser password (optional, can use env var)
        """
        self._client = client
        self._username = username
        self._password = password
        self._playwright: Playwright | None = None
        self._browsers: dict[str, Browser] = {}
        self._pages: dict[str, Page] = {}
        self._current_domain: str = "default"
        # Console and network diagnostics cache
        self._console_messages: dict[str, list[dict[str, Any]]] = {}
        self._network_requests: dict[str, list[dict[str, Any]]] = {}
        self._max_console_messages = 10
        self._max_network_requests = 20

    @staticmethod
    def _get_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.hostname or "default"
        except Exception:
            return "default"

    async def _ensure_playwright(self) -> Playwright:
        """Ensure Playwright is started."""
        if self._playwright is None:
            self._playwright = await async_playwright().start()
        return self._playwright

    async def get_browser(self, domain: str = "default") -> Browser:
        """Get or create a browser instance for a given domain."""
        existing = self._browsers.get(domain)
        if existing and existing.is_connected():
            return existing

        # Clean up stale browser/page
        if existing is not None:
            logger.info("Browser for domain %s disconnected, recreating", domain)
            self._browsers.pop(domain, None)
            self._pages.pop(domain, None)

        playwright = await self._ensure_playwright()

        logger.info("Connecting to Thordata Scraping Browser for domain %s", domain)

        # Get browser credentials
        import os

        user = self._username or os.getenv("THORDATA_BROWSER_USERNAME")
        pwd = self._password or os.getenv("THORDATA_BROWSER_PASSWORD")

        if not user or not pwd:
            raise BrowserConnectionError(
                "Missing browser credentials. Set THORDATA_BROWSER_USERNAME and "
                "THORDATA_BROWSER_PASSWORD or pass them to BrowserSession."
            )

        # Retry logic with exponential backoff
        max_retries = 3
        last_error = None

        for attempt in range(max_retries):
            try:
                ws_url = self._client.get_browser_connection_url(
                    username=user, password=pwd
                )
                logger.debug(
                    "Attempt %d/%d: Connecting to %s...",
                    attempt + 1,
                    max_retries,
                    ws_url[:50],
                )
                browser = await playwright.chromium.connect_over_cdp(ws_url)
                logger.info("Successfully connected to browser for domain %s", domain)
                self._browsers[domain] = browser
                return browser
            except Exception as e:
                last_error = e
                logger.warning(
                    "Browser connection attempt %d/%d failed: %s",
                    attempt + 1,
                    max_retries,
                    e,
                )

                if attempt < max_retries - 1:
                    import asyncio

                    wait_time = 2**attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.info("Retrying in %d seconds...", wait_time)
                    await asyncio.sleep(wait_time)

        # If all retries failed, raise the last error
        raise BrowserConnectionError(
            f"Failed to connect to Thordata Scraping Browser after {max_retries} attempts. "
            f"Last error: {last_error}"
        ) from last_error

    async def get_page(self, url: str | None = None) -> Page:
        """Get or create a page for the current (or provided) domain."""
        if url:
            self._current_domain = self._get_domain(url)
        domain = self._current_domain

        existing = self._pages.get(domain)
        if existing and not existing.is_closed():
            return existing

        browser = await self.get_browser(domain)
        contexts = browser.contexts
        if not contexts:
            context = await browser.new_context()
        else:
            context = contexts[0]

        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()

        # Reset network tracking for this domain
        self._console_messages[domain] = []
        self._network_requests[domain] = []

        # Network request tracking
        async def on_request(request: Any) -> None:
            try:
                self._network_requests.setdefault(domain, [])
                import time

                self._network_requests[domain].append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "resourceType": getattr(request, "resource_type", None),
                        "timestamp": int(time.time() * 1000),
                    }
                )
                self._network_requests[domain] = self._network_requests[domain][
                    -self._max_network_requests :
                ]
            except Exception:
                pass

        async def on_response(response: Any) -> None:
            try:
                # Update last matching request with status
                req = response.request
                url = getattr(req, "url", None)
                if url and domain in self._network_requests:
                    for item in reversed(self._network_requests[domain]):
                        if item.get("url") == url and item.get("statusCode") is None:
                            item["statusCode"] = response.status
                            break
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        # Console message tracking
        async def on_console(msg: Any) -> None:
            try:
                self._console_messages.setdefault(domain, [])
                import time

                self._console_messages[domain].append(
                    {
                        "type": msg.type,
                        "message": msg.text,
                        "timestamp": int(time.time() * 1000),
                    }
                )
                self._console_messages[domain] = self._console_messages[domain][
                    -self._max_console_messages :
                ]
            except Exception:
                pass

        page.on("console", on_console)

        self._pages[domain] = page
        return page

    async def navigate(self, url: str, timeout: int = 120000) -> dict[str, Any]:
        """Navigate to a URL.

        Args:
            url: Target URL
            timeout: Navigation timeout in milliseconds

        Returns:
            Dictionary with url and title
        """
        page = await self.get_page(url)
        if page.url != url:
            await page.goto(url, timeout=timeout)
        title = await page.title()
        return {"url": page.url, "title": title}

    async def snapshot(
        self, filtered: bool = True, max_items: int = 80, include_dom: bool = False
    ) -> dict[str, Any]:
        """Capture an ARIA-like snapshot of the current page.

        Args:
            filtered: Whether to filter to interactive elements only
            max_items: Maximum number of elements to include
            include_dom: Whether to include dom_snapshot (DOM-based refs)

        Returns:
            Dictionary with url, title, aria_snapshot, and optionally dom_snapshot
        """
        page = await self.get_page()
        full_snapshot = await self._get_interactive_snapshot(page)

        if not filtered:
            result = {
                "url": page.url,
                "title": await page.title(),
                "aria_snapshot": full_snapshot,
            }
            if include_dom:
                dom_snapshot_raw = await self._capture_dom_snapshot(page)
                result["dom_snapshot"] = self._format_dom_elements(dom_snapshot_raw)
            return result

        # Filter and limit
        filtered_snapshot = self._filter_snapshot(full_snapshot)
        filtered_snapshot = self._limit_snapshot_items(
            filtered_snapshot, max_items=max_items
        )

        result = {
            "url": page.url,
            "title": await page.title(),
            "aria_snapshot": filtered_snapshot,
        }

        if include_dom:
            dom_snapshot_raw = await self._capture_dom_snapshot(page)
            result["dom_snapshot"] = self._format_dom_elements(dom_snapshot_raw)

        return result

    async def click_ref(
        self, ref: str, wait_for_navigation_ms: int | None = None
    ) -> dict[str, Any]:
        """Click an element by its ref ID.

        Args:
            ref: The ref ID from snapshot (e.g., "1" or "dom-1")
            wait_for_navigation_ms: Optional wait time in ms to detect navigation

        Returns:
            Dictionary with click result information
        """
        page = await self.get_page()
        url_before = page.url

        try:
            locator = page.locator(f'[data-fastmcp-ref="{ref}"]').first
            await locator.click(timeout=5000)

            # Check for navigation if requested
            did_navigate = False
            url_after = url_before
            if wait_for_navigation_ms and wait_for_navigation_ms > 0:
                import asyncio

                await asyncio.sleep(wait_for_navigation_ms / 1000)
                url_after = page.url
                did_navigate = url_after != url_before

            return {
                "message": "Successfully clicked element",
                "ref": ref,
                "url_before": url_before,
                "url_after": url_after,
                "did_navigate": did_navigate,
            }
        except Exception as e:
            raise BrowserSessionError(f"Failed to click element: {e}") from e

    async def type_ref(
        self, ref: str, text: str, submit: bool = False
    ) -> dict[str, Any]:
        """Type text into an element by its ref ID.

        Args:
            ref: The ref ID from snapshot
            text: Text to type
            submit: Whether to press Enter after typing

        Returns:
            Dictionary with type result information
        """
        page = await self.get_page()
        url_before = page.url

        try:
            locator = page.locator(f'[data-fastmcp-ref="{ref}"]').first
            await locator.fill(text)
            if submit:
                await locator.press("Enter")

            return {
                "message": "Typed into element" + (" and submitted" if submit else ""),
                "ref": ref,
                "url_before": url_before,
                "url_after": page.url,
            }
        except Exception as e:
            raise BrowserSessionError(f"Failed to type into element: {e}") from e

    async def screenshot_page(self, full_page: bool = False) -> bytes:
        """Take a screenshot of the current page.

        Args:
            full_page: Whether to capture full page or viewport only

        Returns:
            Screenshot as bytes (PNG format)
        """
        page = await self.get_page()
        return await page.screenshot(full_page=full_page)

    async def get_html(self, full_page: bool = False) -> str:
        """Get the HTML content of the current page.

        Args:
            full_page: Whether to get full page HTML or body only

        Returns:
            HTML content as string
        """
        page = await self.get_page()
        if full_page:
            return await page.content()
        else:
            try:
                return await page.evaluate("document.body.innerHTML")
            except Exception:
                return await page.content()

    async def scroll(self) -> dict[str, Any]:
        """Scroll to the bottom of the page.

        Returns:
            Dictionary with scroll result
        """
        page = await self.get_page()
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        return {"message": "Scrolled to bottom"}

    async def go_back(self) -> dict[str, Any]:
        """Navigate back in browser history.

        Returns:
            Dictionary with new URL
        """
        page = await self.get_page()
        await page.go_back()
        return {"url": page.url}

    def get_console_messages(
        self, n: int = 10, domain: str | None = None
    ) -> list[dict[str, Any]]:
        """Return recent console messages for the given domain.

        Args:
            n: Number of messages to return
            domain: Domain name (defaults to current domain)

        Returns:
            List of console message dictionaries
        """
        d = domain or self._current_domain
        items = self._console_messages.get(d, [])
        return items[-max(0, int(n)) :]

    def get_network_requests(
        self, n: int = 20, domain: str | None = None
    ) -> list[dict[str, Any]]:
        """Return recent network request summaries for the given domain.

        Args:
            n: Number of requests to return
            domain: Domain name (defaults to current domain)

        Returns:
            List of network request dictionaries
        """
        d = domain or self._current_domain
        items = self._network_requests.get(d, [])
        return items[-max(0, int(n)) :]

    def reset_page(self, domain: str | None = None) -> None:
        """Drop cached page for a domain so the next call recreates it.

        Args:
            domain: Domain name (defaults to current domain)
        """
        d = domain or self._current_domain
        self._pages.pop(d, None)
        self._console_messages.pop(d, None)
        self._network_requests.pop(d, None)

    async def _get_interactive_snapshot(self, page: Page) -> str:
        """Generate a text snapshot of interactive elements with refs."""
        script = """
        () => {
            function getSnapshot() {
                const lines = [];
                let refCounter = 0;

                function normalizeRole(tag, explicitRole) {
                    const role = (explicitRole || '').toLowerCase();
                    const t = (tag || '').toLowerCase();
                    if (role) return role;
                    if (t === 'a') return 'link';
                    if (t === 'button') return 'button';
                    if (t === 'input') return 'textbox';
                    if (t === 'select') return 'combobox';
                    if (t === 'textarea') return 'textbox';
                    return t;
                }

                function traverse(node) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        const tag = node.tagName.toLowerCase();
                        const interactiveTag = ['a', 'button', 'input', 'select', 'textarea'].includes(tag);
                        const role = normalizeRole(tag, node.getAttribute('role'));
                        const interactiveRole = ['button', 'link', 'textbox', 'searchbox', 'combobox', 'checkbox', 'radio', 'switch', 'tab', 'menuitem', 'option'].includes(role);

                        if (interactiveTag || interactiveRole) {
                            if (!node.dataset.fastmcpRef) {
                                node.dataset.fastmcpRef = (++refCounter).toString();
                            }
                            let name = node.innerText || node.getAttribute('aria-label') || '';
                            name = (name || '').replace(/\\s+/g, ' ').trim().substring(0, 80);

                            lines.push(`- ${role} "${name}" [ref=${node.dataset.fastmcpRef}]`);
                            if (node.href) {
                                lines.push(`  /url: "${node.href}"`);
                            }
                        }
                    }

                    node.childNodes.forEach(child => traverse(child));
                }

                traverse(document.body);
                return lines.join('\\n');
            }
            return getSnapshot();
        }
        """
        return await page.evaluate(script)

    @staticmethod
    def _filter_snapshot(snapshot_text: str) -> str:
        """Filter snapshot to interactive elements only."""
        import re

        lines = snapshot_text.split("\n")
        filtered = []
        i = 0
        while i < len(lines):
            line = lines[i]
            trimmed = line.strip()

            if not trimmed or not trimmed.startswith("-"):
                i += 1
                continue

            # Extract role
            role_match = re.match(r"^-\s+([a-zA-Z]+)", trimmed)
            if not role_match:
                i += 1
                continue

            role = role_match.group(1).lower()
            interactive_roles = {
                "button",
                "link",
                "textbox",
                "searchbox",
                "combobox",
                "checkbox",
                "radio",
                "switch",
                "tab",
                "menuitem",
                "option",
            }

            if role in interactive_roles:
                filtered.append(line)
                # Include next line if it's a URL
                if i + 1 < len(lines) and "/url:" in lines[i + 1]:
                    filtered.append(lines[i + 1])
                    i += 1

            i += 1

        return "\n".join(filtered)

    @staticmethod
    def _limit_snapshot_items(text: str, *, max_items: int) -> str:
        """Limit snapshot to the first N interactive element blocks."""
        if max_items <= 0:
            return ""
        if not text:
            return text

        lines = text.splitlines()
        out: list[str] = []
        items = 0
        for line in lines:
            if line.startswith("- ") or line.startswith("["):
                if items >= max_items:
                    break
                items += 1
            if items > 0:
                out.append(line)
        return "\n".join(out).strip()

    async def _capture_dom_snapshot(self, page: Page) -> list[dict[str, Any]]:
        """Capture a lightweight DOM snapshot of interactive elements."""
        script = """
        () => {
            const selectors = [
                'a[href]', 'button', 'input', 'select', 'textarea',
                '[role="button"]', '[role="link"]', '[role="checkbox"]',
                '[tabindex]:not([tabindex="-1"])'
            ];
            const elements = Array.from(document.querySelectorAll(selectors.join(',')));
            const results = [];
            let counter = 0;

            for (const el of elements) {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') {
                    continue;
                }

                if (!el.dataset.fastmcpRef) {
                    el.dataset.fastmcpRef = `dom-${++counter}`;
                }

                let name = el.innerText || el.getAttribute('aria-label') || el.getAttribute('title') || '';
                name = (name || '').replace(/\\s+/g, ' ').trim();

                results.push({
                    ref: el.dataset.fastmcpRef,
                    role: el.getAttribute('role') || el.tagName.toLowerCase(),
                    name,
                    url: el.href || ''
                });
            }
            return results;
        }
        """
        return await page.evaluate(script)

    @staticmethod
    def _format_dom_elements(dom_snapshot_raw: list[dict[str, Any]]) -> str:
        """Format DOM snapshot elements into a readable text representation."""
        lines = []
        for el in dom_snapshot_raw:
            ref = el.get("ref", "")
            role = el.get("role", "")
            name = el.get("name", "")
            url = el.get("url", "")
            lines.append(f'[{ref}] {role} "{name}"')
            if url:
                lines.append(f'  /url: "{url}"')
        return "\n".join(lines)

    async def close(self) -> None:
        """Cleanly close all pages, browsers, and Playwright."""
        import contextlib

        for page in list(self._pages.values()):
            with contextlib.suppress(Exception):
                await page.close()
        self._pages.clear()

        for browser in list(self._browsers.values()):
            with contextlib.suppress(Exception):
                await browser.close()
        self._browsers.clear()

        if self._playwright is not None:
            try:
                await self._playwright.stop()
            finally:
                self._playwright = None
