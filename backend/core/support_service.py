#!/usr/bin/env python3
"""
CHARTORA — Customer Support & Inquiry Service
Handles:
- Customer Support Ticket submission and lifecycle tracking (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- Employee Portal assignment, internal notes, and customer communication
- Integration with general contact, career, and affiliate applications
"""

import time
import secrets
from typing import Dict, Any, List, Optional

class SupportService:
    def __init__(self, db_getter):
        self.get_db = db_getter

    def create_ticket(self, ticket_data: Dict[str, Any], user_id: Optional[int] = None) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        ticket_id = f"TICK-{int(time.time() * 1000) % 1000000:06d}"
        name = ticket_data.get("name", "Trader").strip()
        email = ticket_data.get("email", "").strip().lower()
        subject = ticket_data.get("subject", "General Inquiry").strip()
        message = ticket_data.get("message", "").strip()
        category = ticket_data.get("category", "GENERAL").upper()
        priority = ticket_data.get("priority", "NORMAL").upper()

        if not email or not message:
            conn.close()
            return {"success": False, "error": "Email and message required"}

        cursor.execute("""
            INSERT INTO support_tickets (ticket_id, user_id, name, email, subject, message, category, priority, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
        """, (ticket_id, user_id, name, email, subject, message, category, priority))

        conn.commit()
        conn.close()

        return {
            "success": True,
            "ticket_id": ticket_id,
            "message": "Your support ticket has been received. Our team will respond shortly."
        }

    def get_tickets(
        self,
        user_id: Optional[int] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        conn = self.get_db()
        cursor = conn.cursor()

        query = "SELECT * FROM support_tickets"
        params = []
        conds = []

        if user_id is not None:
            conds.append("user_id = ?")
            params.append(user_id)
        if status:
            conds.append("status = ?")
            params.append(status.upper())

        if conds:
            query += " WHERE " + " AND ".join(conds)

        query += " ORDER BY CASE priority WHEN 'URGENT' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'NORMAL' THEN 3 ELSE 4 END, created_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, tuple(params))
        tickets = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return tickets

    def update_ticket(
        self,
        ticket_id: str,
        updates: Dict[str, Any],
        employee_id: Optional[int] = None
    ) -> Dict[str, Any]:
        conn = self.get_db()
        cursor = conn.cursor()

        status = updates.get("status")
        notes = updates.get("response_notes")
        priority = updates.get("priority")
        assigned = updates.get("assigned_employee_id") or employee_id

        clauses = []
        params = []

        if status:
            clauses.append("status = ?")
            params.append(status.upper())
            if status.upper() == "RESOLVED":
                clauses.append("resolved_at = CURRENT_TIMESTAMP")
        if notes:
            clauses.append("response_notes = ?")
            params.append(notes.strip())
        if priority:
            clauses.append("priority = ?")
            params.append(priority.upper())
        if assigned:
            clauses.append("assigned_employee_id = ?")
            params.append(assigned)

        if not clauses:
            conn.close()
            return {"success": True, "message": "No changes requested"}

        clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.append(ticket_id)

        cursor.execute(f"UPDATE support_tickets SET {', '.join(clauses)} WHERE ticket_id = ?", tuple(params))
        updated = cursor.rowcount > 0
        conn.commit()
        conn.close()

        return {
            "success": updated,
            "ticket_id": ticket_id,
            "message": "Ticket updated successfully" if updated else "Ticket not found"
        }
