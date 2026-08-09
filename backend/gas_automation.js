/**
 * Chartora.in — Google Apps Script Master Automation Backend
 * Connects Stripe Webhooks -> Google Sheets CRM -> Gmail Onboarding -> Telegram Access Bot
 */

const SHEET_ID = 'YOUR_GOOGLE_SHEETS_ID';
const TELEGRAM_BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN';
const PRO_TELEGRAM_CHAT_ID = '-100XXXXXXX'; // Pro Channel ID
const CORE_TELEGRAM_CHAT_ID = '-100YYYYYYY'; // Core Channel ID

/**
 * HTTP POST Webhook Handler (Stripe Webhook Listener)
 */
function doPost(e) {
  try {
    const event = JSON.parse(e.postData.contents);
    const eventType = event.type;
    const session = event.data.object;

    if (eventType === 'checkout.session.completed') {
      handleNewSubscription(session);
    } else if (eventType === 'customer.subscription.deleted') {
      handleSubscriptionCancellation(session);
    }

    return ContentService.createTextOutput(JSON.stringify({ status: 'success' }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({ status: 'error', message: err.toString() }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Handles New Successful Subscription
 */
function handleNewSubscription(session) {
  const customerEmail = session.customer_details.email;
  const customerName = session.customer_details.name || 'Trader';
  const planId = session.amount_total === 3999 ? 'PRO' : 'CORE';
  const targetChannel = planId === 'PRO' ? PRO_TELEGRAM_CHAT_ID : CORE_TELEGRAM_CHAT_ID;

  // 1. Generate Telegram One-Time Invite Link
  const inviteLink = createTelegramInviteLink(targetChannel, customerEmail);

  // 2. Record Customer in Google Sheets CRM
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Customers');
  sheet.appendRow([
    new Date(),
    customerName,
    customerEmail,
    planId,
    'ACTIVE',
    session.subscription,
    inviteLink
  ]);

  // 3. Send Onboarding Email via Gmail
  sendWelcomeEmail(customerEmail, customerName, planId, inviteLink);
}

/**
 * Creates Single-Use Expiring Telegram Invite Link
 */
function createTelegramInviteLink(chatId, identifier) {
  const url = `https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/createChatInviteLink`;
  const payload = {
    chat_id: chatId,
    name: `Invite for ${identifier}`,
    member_limit: 1,
    expire_date: Math.floor(Date.now() / 1000) + (86400 * 3) // Expires in 3 days
  };

  const options = {
    method: 'post',
    contentType: 'application/json',
    payload: JSON.stringify(payload),
    muteHttpExceptions: true
  };

  const res = UrlFetchApp.fetch(url, options);
  const json = JSON.parse(res.getContentText());
  return json.ok ? json.result.invite_link : 'https://t.me/ChartoraSupportBot';
}

/**
 * Sends Automated Welcome & Onboarding Email
 */
function sendWelcomeEmail(email, name, plan, inviteLink) {
  const subject = `Welcome to Chartora ${plan} — Your Market Intelligence Access`;
  const body = `
Hi ${name},

Thank you for subscribing to Chartora ${plan}!

Here is your official onboarding checklist to get started:

1. JOIN TELEGRAM CHANNEL:
Click your single-use private invite link to join your setup alert channel:
${inviteLink}

2. YOUR 30-DAY TRADER ONBOARDING:
Over the next 4 weeks, you will receive our strategy breakdowns, EMA 9/21 pullback guides, and position sizing templates directly in your inbox.

3. TRANSPARENT SIGNAL JOURNAL:
You can track all generated setup records and before/after screenshots at:
https://chartora.in/#transparency

Important Disclaimer:
All setup alerts are for educational technical analysis purposes only. You independently decide all trade entries, position sizing, and risk parameters.

Welcome aboard,
The Chartora Team
Your markets. Our scanners. Your decision.
  `;

  GmailApp.sendEmail(email, subject, body);
}

/**
 * Handles Subscription Cancellation (Revokes Access)
 */
function handleSubscriptionCancellation(session) {
  const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName('Customers');
  const data = sheet.getDataRange().getValues();
  const subId = session.id;

  for (let i = 1; i < data.length; i++) {
    if (data[i][5] === subId) {
      sheet.getRange(i + 1, 5).setValue('CANCELLED');
      break;
    }
  }
}
