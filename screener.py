import os
import yfinance as yf
import pandas as pd
import numpy as np
import requests
from io import StringIO
from concurrent.futures import ThreadPoolExecutor
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders

# === CONFIGURATION ===
BATCH_SIZE = 500
MIN_VOLUME = 100_000
MIN_PRICE = 1
MAX_PRICE = 30
MIN_ATR = 0.1
MAX_WORKERS = 10
CSV_FILENAME = "csv_results/daily_results.csv"

# credentials from environment variables
EMAIL_SENDER = os.environ.get("EMAIL_SENDER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
EMAIL_RECEIVER = os.environ.get("EMAIL_RECEIVER")

if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER]):
    raise EnvironmentError("EMAIL_SENDER, EMAIL_PASSWORD, and EMAIL_RECEIVER must be set as environment variables")

# === FETCH TICKERS ===
def get_most_active_stocks():
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?count=100&scrIds=most_actives"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    data = response.json()
    return [item['symbol'] for item in data['finance']['result'][0]['quotes']]

# === ATR CALCULATION ===
def calculate_atr(hist, period=14):
    high_low = hist['High'] - hist['Low']
    high_close = np.abs(hist['High'] - hist['Close'].shift(1))
    low_close = np.abs(hist['Low'] - hist['Close'].shift(1))
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = ranges.max(axis=1)
    atr = true_range.rolling(window=period).mean().iloc[-1]
    return round(atr, 2)

# === VWAP CALCULATION ===
def calculate_vwap(hist):
    vwap = (hist['Close'] * hist['Volume']).cumsum() / hist['Volume'].cumsum()
    return vwap

# === PROCESS SINGLE TICKER ===
def process_ticker(ticker):
    try:
        print(f"🔎 Checking {ticker}...")
        stock = yf.Ticker(ticker)
        hist = stock.history(period="21d", interval="1d")
        if hist.empty or len(hist) < 14 or hist['Close'].isnull().all():
            print(f"❌ Skipping {ticker}: no recent data.")
            return None
        current_price = hist['Close'].iloc[-1]
        volume = hist['Volume'].iloc[-1]
        atr = calculate_atr(hist)
        try:
            info = stock.info or {}
        except Exception:
            print(f"⚠️ Info fetch failed for {ticker}")
            info = {}
        if (MIN_PRICE <= current_price <= MAX_PRICE) and (volume >= MIN_VOLUME) and (atr >= MIN_ATR):
            today = hist.iloc[-1]
            yesterday = hist.iloc[-2]
            price_action = (today['Close'] - today['Open']) / today['Open'] * 100
            volatility = (today['High'] - today['Low']) / today['Open'] * 100
            delta = hist['Close'].diff()
            gain = np.where(delta > 0, delta, 0)
            loss = np.where(delta < 0, -delta, 0)
            avg_gain = pd.Series(gain).rolling(window=14).mean()
            avg_loss = pd.Series(loss).rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            rsi_value = rsi.iloc[-1] if not rsi.isna().iloc[-1] else None
            vwap_today = calculate_vwap(hist).iloc[-1]
            vwap_deviation = (today['Close'] - vwap_today) / vwap_today * 100
            gap = (today['Open'] - yesterday['Close']) / yesterday['Close'] * 100
            avg_volume = hist['Volume'].mean()
            volume_surge = today['Volume'] / avg_volume * 100
            print(f"✅ Passed: {ticker} | Price: {current_price}, Vol: {volume}, ATR: {atr}")
            return {
                'Ticker': ticker,
                'Current Price': round(current_price, 2),
                'Volume': int(volume),
                'ATR': atr,
                'Price Action %': round(price_action, 2),
                'Volatility %': round(volatility, 2),
                'RSI 14': round(rsi_value, 2) if rsi_value else None,
                'VWAP Deviation %': round(vwap_deviation, 2),
                'Gap %': round(gap, 2),
                'Volume Surge %': round(volume_surge, 2),
                '52W High': info.get('fiftyTwoWeekHigh'),
                '52W Low': info.get('fiftyTwoWeekLow'),
                'Sector': info.get('sector'),
                'News Link': f"https://finance.yahoo.com/quote/{ticker}/news"
            }
        else:
            print(f"⚠️ Filtered out: {ticker} | Price: {current_price}, Vol: {volume}, ATR: {atr}")
            return None
    except Exception as e:
        print(f"⚠️ Error with {ticker}: {e}")
        return None

# === SCREENING FUNCTION ===
def screen_stocks(ticker_batch):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = list(executor.map(process_ticker, ticker_batch))
    return pd.DataFrame([res for res in results if res is not None])

# === EMAIL FUNCTION ===
def send_email_with_csv(to_email, subject, body, file_path):
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    with open(file_path, "rb") as attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename={file_path}')
        msg.attach(part)
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)
        print("📧 Email sent successfully.")
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication Error: {e}")
        print("Please check your EMAIL_PASSWORD (use Gmail App Password).")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# === MAIN FUNCTION ===
def main():
    print("🚀 Starting NASDAQ stock screener...")
    tickers = get_most_active_stocks()
    all_results = pd.DataFrame()
    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i:i + BATCH_SIZE]
        batch_result = screen_stocks(batch)
        all_results = pd.concat([all_results, batch_result], ignore_index=True)
    os.makedirs(os.path.dirname(CSV_FILENAME), exist_ok=True)
    all_results.to_csv(CSV_FILENAME, index=False)
    print(f"✅ Screener complete. {len(all_results)} stocks saved to {CSV_FILENAME}.")
    send_email_with_csv(
        to_email=EMAIL_RECEIVER,
        subject="📊 Daily Stock Screener csv_results",
        body="Attached is your daily NASDAQ stock screening report.",
        file_path=CSV_FILENAME
    )

if __name__ == "__main__":
    main()
