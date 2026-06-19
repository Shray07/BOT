#!/usr/bin/env python3
"""
Schengen Visa Appointment Monitor for UK/London - ACCURATE VERSION
Properly detects real slot availability with earliest dates
Alert Email: susha6458@gmail.com
"""

import time
import json
import smtplib
import logging
import os
import sys
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Tuple, Optional

# Optional: For browser automation
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# ==================== CONFIGURATION ====================

EMAIL_SENDER = "drr.up.20.riders@gmail.com"
EMAIL_PASSWORD = "gvyq rlah ywcq bohu"
EMAIL_RECIPIENT = "susha6458@gmail.com"

CHECK_INTERVAL = 600  # 10 minutes
PAGE_TIMEOUT = 30
MAX_RETRIES = 2
LOG_FILE = "visa_monitor.log"
DATA_FILE = "visa_status.json"

# ==================== CONSULATE DATA ====================

CONSULATES: Dict[str, Dict] = {
    "Sweden": {
        "url": "https://visa.vfsglobal.com/gbr/en/swe/book-an-appointment",
        "provider": "VFS Global",
        "type": "vfs",
    },
    "Portugal": {
        "url": "https://visa.vfsglobal.com/gbr/en/prt/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Latvia": {
        "url": "https://visa.vfsglobal.com/gbr/en/lva/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Greece": {
        "url": "https://uk-gr-services.gvcworld.eu/login/GB/en?lang=en_US",
        "provider": "GVC World",
        "type": "gvc",
    },
    "Finland": {
        "url": "https://visa.vfsglobal.com/gbr/en/fin",
        "provider": "VFS Global",
        "type": "vfs",
    },
    "Iceland": {
        "url": "https://visa.vfsglobal.com/gbr/en/isl/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Lithuania": {
        "url": "https://visa.vfsglobal.com/gbr/en/ltu/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Slovenia": {
        "url": "https://visa.vfsglobal.com/gbr/en/svn",
        "provider": "VFS Global",
        "type": "vfs",
    },
    "Hungary": {
        "url": "https://visa.vfsglobal.com/gbr/en/hun/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Austria": {
        "url": "https://visa.vfsglobal.com/gbr/en/aut/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Croatia": {
        "url": "https://visa.vfsglobal.com/gbr/en/hrv/book-an-appointment",
        "provider": "VFS Global",
        "type": "vfs",
    },
    "Netherlands": {
        "url": "https://visa.vfsglobal.com/gbr/en/nld/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Italy": {
        "url": "https://visa.vfsglobal.com/gbr/en/ita/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Czech Republic": {
        "url": "https://visa.vfsglobal.com/gbr/en/cze/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "Malta": {
        "url": "https://visa.vfsglobal.com/gbr/en/mlt/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
    "France": {
        "url": "https://fr.tlscontact.com/gb/LON/index.php",
        "provider": "TLScontact",
        "type": "tls",
    },
    "Germany": {
        "url": "https://visa-de.tlscontact.com/visa/gb",
        "provider": "TLScontact",
        "type": "tls",
    },
    "Switzerland": {
        "url": "https://visa.vfsglobal.com/gbr/en/che/login",
        "provider": "VFS Global",
        "type": "vfs_login",
    },
}

# ==================== SETUP LOGGING ====================

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ==================== EMAIL FUNCTIONS ====================

def send_email_alert(subject: str, body: str, is_html: bool = False) -> bool:
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECIPIENT
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())
        logger.info("Email alert sent to " + EMAIL_RECIPIENT)
        return True
    except Exception as e:
        logger.error("Failed to send email: " + str(e))
        return False

def send_slot_found_email(country: str, url: str, provider: str, earliest_date: str, total_slots: int = 0, slot_details: str = ""):
    subject = "VISA SLOT FOUND: " + country + " - London"

    slot_info = ""
    if earliest_date:
        slot_info = "<p><strong>Earliest Available Date:</strong> " + earliest_date + "</p>"
    if total_slots > 0:
        slot_info += "<p><strong>Total Available Slots:</strong> " + str(total_slots) + "</p>"
    if slot_details:
        slot_info += "<p><strong>Details:</strong> " + slot_details + "</p>"

    html_body = """
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 2px solid #28a745; border-radius: 10px;">
            <h1 style="color: #28a745; text-align: center;">APPOINTMENT SLOT AVAILABLE!</h1>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <h2 style="margin-top: 0; color: #495057;">Country: """ + country + """</h2>
                <p><strong>Provider:</strong> """ + provider + """</p>
                <p><strong>Location:</strong> London, United Kingdom</p>
                <p><strong>Found at:</strong> """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                """ + slot_info + """
            </div>
            <div style="text-align: center; margin: 30px 0;">
                <a href=""" + url + """ style="background: #28a745; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">
                    BOOK NOW
                </a>
            </div>
            <div style="background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p style="margin: 0;"><strong>Act Fast!</strong> Slots disappear quickly. Open the link immediately.</p>
            </div>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #dee2e6;">
            <p style="font-size: 12px; color: #6c757d; text-align: center;">
                This alert was sent by your Schengen Visa Monitor Bot.<br>
                Monitoring 18 consulates from London, UK.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email_alert(subject, html_body, is_html=True)

def send_daily_summary(status_data: Dict):
    subject = "Daily Visa Monitor Summary - " + datetime.now().strftime('%Y-%m-%d')
    available = [(k, v) for k, v in status_data.items() if v.get('has_slots')]
    checked = [k for k, v in status_data.items() if v.get('checked')]
    errors = [k for k, v in status_data.items() if v.get('error')]

    body = "DAILY VISA MONITOR SUMMARY\n"
    body += "=" * 50 + "\n"
    body += "Date: " + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + "\n\n"

    body += "AVAILABLE SLOTS (" + str(len(available)) + "):\n"
    if available:
        for country, data in available:
            date_info = " - Earliest: " + data.get('earliest_date', 'Unknown') if data.get('earliest_date') else ""
            body += "  * " + country + date_info + "\n"
    else:
        body += "  None found\n"

    body += "\nCONSULATES CHECKED (" + str(len(checked)) + "/18):\n"
    for c in checked:
        body += "  OK " + c + "\n"

    body += "\nERRORS (" + str(len(errors)) + "):\n"
    if errors:
        for c in errors:
            body += "  * " + c + ": " + status_data[c]['error'] + "\n"
    else:
        body += "  None\n"

    body += "\n---\nBot is running. Next check in " + str(CHECK_INTERVAL // 60) + " minutes."
    send_email_alert(subject, body)

# ==================== ACCURATE SLOT DETECTION ====================

def parse_vfs_page(content: str, text: str) -> Tuple[bool, Optional[str], int, str]:
    """
    Parse VFS Global page for accurate slot detection.
    Returns: (has_slots, earliest_date, slot_count, details)
    """
    text_lower = text.lower()
    content_lower = content.lower()
    combined = text_lower + " " + content_lower

    # VFS Global: Check for "no appointment slots" message
    no_slot_patterns = [
        "we are sorry but no appointment slots are currently available",
        "no appointment slots are currently available",
        "no slots available",
        "fully booked",
        "no available appointments"
    ]

    for pattern in no_slot_patterns:
        if pattern in combined:
            return False, None, 0, "No appointment slots currently available"

    # VFS Global: Check for "Earliest Available Slot: DD/MM/YYYY"
    earliest_match = re.search(r'earliest available slot\s*[:\-]?\s*(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}|\d{4}-\d{2}-\d{2})', combined)
    if earliest_match:
        date_str = earliest_match.group(1)
        return True, date_str, 1, "Earliest available slot: " + date_str

    # Also check for other date formats
    date_patterns = [
        r'available\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})',
        r'next available\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})',
        r'slot available\s*[:\-]?\s*(\d{2}/\d{2}/\d{4})',
    ]
    for pattern in date_patterns:
        match = re.search(pattern, combined)
        if match:
            return True, match.group(1), 1, "Slot available on: " + match.group(1)

    # If we see "appointment" but no clear no-slot message, be conservative
    if "appointment" in combined and "available" in combined:
        # Check if it's just a login page or booking page without actual dates
        if "login" in combined or "sign in" in combined:
            return False, None, 0, "Login page - cannot determine slot availability"
        if "book an appointment" in combined and not earliest_match:
            return False, None, 0, "Booking page - no specific dates found"

    return False, None, 0, "Could not determine slot status"

def parse_gvc_page(content: str, text: str) -> Tuple[bool, Optional[str], int, str]:
    """
    Parse GVC World (Greece) page for accurate slot detection.
    Looks for calendar with selectable (green) slots.
    """
    text_lower = text.lower()
    content_lower = content.lower()
    combined = text_lower + " " + content_lower

    # Check for "Available appointments" section
    if "available appointments" in combined:
        # Check if there are actual time slots listed
        # Look for time patterns like 08:30, 09:00, etc.
        time_slots = re.findall(r'\b(\d{2}:\d{2})\b', text)

        if time_slots and len(time_slots) > 2:
            # Check if the page shows a selected date
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', text)
            date_str = date_match.group(1) if date_match else "See calendar"
            return True, date_str, len(time_slots), str(len(time_slots)) + " time slots available"
        else:
            return False, None, 0, "Available appointments section but no selectable time slots"

    # Check for "Booked appointments" or no availability
    if "booked appointments" in combined and "available appointments" not in combined:
        return False, None, 0, "No available appointments - only booked shown"

    # Check for calendar without available slots
    if "please select time slot" in combined and "available appointments" not in combined:
        return False, None, 0, "Calendar shown but no available time slots"

    return False, None, 0, "Could not determine slot status"

def parse_tls_page(content: str, text: str) -> Tuple[bool, Optional[str], int, str]:
    """
    Parse TLScontact page (France, Germany) for slot detection.
    """
    text_lower = text.lower()
    content_lower = content.lower()
    combined = text_lower + " " + content_lower

    # TLScontact specific patterns
    no_slot_patterns = [
        "no appointment available",
        "pas de rendez-vous disponible",
        "kein termin verfugbar",
        "fully booked",
        "no slots"
    ]

    for pattern in no_slot_patterns:
        if pattern in combined:
            return False, None, 0, "No appointments available"

    # Check for available dates
    date_match = re.search(r'(\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4})', text)
    if date_match and ("available" in combined or "appointment" in combined):
        return True, date_match.group(1), 1, "Appointment available"

    return False, None, 0, "Could not determine slot status"

def check_with_playwright(url: str, country: str, config: Dict) -> Tuple[bool, Optional[str], int, str]:
    if not PLAYWRIGHT_AVAILABLE:
        return False, None, 0, "Playwright not installed"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = context.new_page()
            page.goto(url, wait_until='networkidle', timeout=PAGE_TIMEOUT * 1000)
            time.sleep(5)  # Wait longer for JS to load

            content = page.content()
            text = page.inner_text('body')
            browser.close()

            portal_type = config.get('type', 'vfs')

            if portal_type == 'gvc':
                return parse_gvc_page(content, text)
            elif portal_type == 'tls':
                return parse_tls_page(content, text)
            else:
                return parse_vfs_page(content, text)

    except Exception as e:
        return False, None, 0, "Error: " + str(e)

def check_with_selenium(url: str, country: str, config: Dict) -> Tuple[bool, Optional[str], int, str]:
    if not SELENIUM_AVAILABLE:
        return False, None, 0, "Selenium not installed"

    driver = None
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(PAGE_TIMEOUT)
        driver.get(url)
        time.sleep(5)

        content = driver.page_source
        text = driver.find_element(By.TAG_NAME, 'body').text

        portal_type = config.get('type', 'vfs')

        if portal_type == 'gvc':
            result = parse_gvc_page(content, text)
        elif portal_type == 'tls':
            result = parse_tls_page(content, text)
        else:
            result = parse_vfs_page(content, text)

        driver.quit()
        return result

    except Exception as e:
        if driver:
            driver.quit()
        return False, None, 0, "Error: " + str(e)

def check_website(url: str, country: str, config: Dict) -> Tuple[bool, Optional[str], int, str]:
    for attempt in range(MAX_RETRIES):
        if PLAYWRIGHT_AVAILABLE:
            result = check_with_playwright(url, country, config)
            if not result[3].startswith("Error") and not result[3].startswith("Playwright"):
                return result

        if SELENIUM_AVAILABLE:
            result = check_with_selenium(url, country, config)
            if not result[3].startswith("Error") and not result[3].startswith("Selenium"):
                return result

        time.sleep(2)

    return False, None, 0, "No browser automation available"

# ==================== MAIN MONITORING LOOP ====================

def load_previous_status() -> Dict:
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def save_status(status: Dict):
    with open(DATA_FILE, 'w') as f:
        json.dump(status, f, indent=2)

def run_check() -> Dict:
    previous = load_previous_status()
    current = {}
    alerts_sent = []

    logger.info("=" * 60)
    logger.info("Starting check cycle at " + datetime.now().strftime('%H:%M:%S'))
    logger.info("=" * 60)

    for country, config in CONSULATES.items():
        logger.info("Checking " + country + " (" + config['provider'] + ")...")

        has_slots, earliest_date, slot_count, message = check_website(config['url'], country, config)

        current[country] = {
            'checked': True,
            'has_slots': has_slots,
            'earliest_date': earliest_date,
            'slot_count': slot_count,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'url': config['url'],
            'provider': config['provider']
        }

        if has_slots:
            logger.info("  SLOT FOUND! " + message)

            # Only alert if this is a NEW finding (different from previous)
            prev = previous.get(country, {})
            prev_date = prev.get('earliest_date')

            if earliest_date != prev_date or not prev.get('has_slots', False):
                send_slot_found_email(country, config['url'], config['provider'], 
                                      earliest_date or "", slot_count, message)
                alerts_sent.append(country)
                current[country]['alert_sent'] = True
        else:
            logger.info("  No slots: " + message)

        time.sleep(3)

    save_status(current)

    slots_found = sum(1 for v in current.values() if v['has_slots'])
    logger.info("=" * 60)
    logger.info("Check complete. Slots found: " + str(slots_found) + "/18")
    if alerts_sent:
        logger.info("New alerts sent for: " + ", ".join(alerts_sent))
    logger.info("=" * 60)

    return current

def main():
    logger.info("Schengen Visa Monitor Bot Started")
    logger.info("Alerts will be sent to: " + EMAIL_RECIPIENT)
    logger.info("Check interval: " + str(CHECK_INTERVAL // 60) + " minutes")
    logger.info("Playwright: " + ("Yes" if PLAYWRIGHT_AVAILABLE else "No"))
    logger.info("Selenium: " + ("Yes" if SELENIUM_AVAILABLE else "No"))

    if not PLAYWRIGHT_AVAILABLE and not SELENIUM_AVAILABLE:
        logger.warning("No browser automation installed! Please install dependencies.")
        print("\nTo install Playwright (recommended):")
        print("  /opt/anaconda3/bin/python3 -m pip install playwright")
        print("  /opt/anaconda3/bin/python3 -m playwright install chromium")
        return

    send_email_alert(
        "Visa Monitor Bot Started",
        "Your Schengen visa monitor is now running!\n\nMonitoring 18 consulates in London.\nCheck interval: " + str(CHECK_INTERVAL // 60) + " minutes.\n\nYou will receive an email immediately when any slot opens up."
    )

    check_count = 0
    last_summary = None

    try:
        while True:
            check_count += 1
            status = run_check()

            now = datetime.now()
            if last_summary != now.date():
                send_daily_summary(status)
                last_summary = now.date()

            logger.info("Sleeping for " + str(CHECK_INTERVAL // 60) + " minutes... (Check #" + str(check_count) + ")")
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        send_email_alert("Visa Monitor Stopped", "The visa monitor bot was stopped manually.")
    except Exception as e:
        logger.error("Fatal error: " + str(e))
        send_email_alert("Visa Monitor CRASHED", "Error: " + str(e) + "\n\nPlease restart the bot.")

if __name__ == "__main__":
    main()
